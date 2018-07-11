# Copyright (C) 2018 Friedrich Miescher Institute for Biomedical Research

import errno
import os

from queue import Queue, Empty
from subprocess import Popen as popen, DEVNULL
from tempfile import mkstemp
from threading import Thread, Event

from .rsync import check_rsync_output
from .item_list import read_list_process_line
from .split import read_split_dump, default_split_list

join_timeout = 2419200 # 1 month

class RsyncSplitList():
	
	def __init__(self, nproc, item_list_file, sep, tmpdir, split_func):
		self.nproc = nproc
		self.dir_list_path = None
		self.delete_list_path = None
		self.dump_dir = None
		self.item_list_file = item_list_file
		self.sep = sep
		self.split_file_list = None
		self.split_func = default_split_list
		self.tmpdir = tmpdir
		if split_func is not None:
			self.split_func = split_func

	def split_and_dump(self):
		# don't dump again if we already did
		if self.split_file_list is None:
			split_list_files, dir_list = read_split_dump(
					self.item_list_file,
					self.sep,
					self.nproc,
					self.split_func,
					self.tmpdir
			)
			self.split_file_list = split_list_files
			self.dir_list_path = dir_list
		return (self.split_file_list, self.dir_list_path)

def init_threads(n, target, args):
	threads = []
	for i in range(n):
		threads.append(Thread(
				name = 'Working thread number %d' % i,
				target = target,
				args = (i,) + args
			))
	return threads

def start_threads(threads):
	for t in threads:
		t.start()
	return

def join_threads(threads):
	for t in threads:
		try:
			t.join(join_timeout)
		# if we initialized the thread but it's not started yet
		# it will throw an exception we can safely ignore 
		except RuntimeError:
			pass
	return

def rsync_dir_tree(args, split_list, source, dest):
	if '--delete' in args:
		raise ValueError('--delete option is forbidden during parallel rsync')
	rsync_args = ['-f+ */', '-f- *'] + args
	rsync_args.append('--files-from=%s' % split_list.dir_list_path)
	rsync_args.append('--from0')
	#rsync_args.append('--dry-run')
	#rsync_args.append('--itemize-changes')
	rsync_args.append(source)
	rsync_args.append(dest)
	(out, err) = check_rsync_output(rsync_args)
	#print(out + '\n')
	#print(err)
	return

def __rsync_worker(t_number, args, list_file_path, source, dest):
	if '--delete' in args:
		raise ValueError('--delete option is forbidden during parallel rsync')
	rsync_args = args.copy()
	rsync_args.append('--files-from=%s' % list_file_path[t_number])
	rsync_args.append('--from0')
	rsync_args.append(source)
	rsync_args.append(dest)
	#print('[Thread %d] starting rsync' % t_number)
	(out, err) = check_rsync_output(rsync_args)
	#print('[Thread %d] rsync finished' % t_number)
	return

def prsync(args, split_list, source, dest):
	if '--delete' in args:
		raise ValueError('--delete option is forbidden during parallel rsync')
	print('Syncing directory tree. This is a single process task')
	rsync_dir_tree(args, split_list, source, dest)
	threads = init_threads(split_list.nproc, __rsync_worker, (args, split_list.split_file_list, source, dest))
	print('Starting %d worker processes for %s' % (len(threads), 'file syncing'))
	start_threads(threads)
	join_threads(threads)
	return

def __add2queue(item, dest, queue):
	queue.put(dest + b'/' + item)
	return

def __rm_worker(t_number, queue, finish_event, quit_event):
	while not (queue.empty() and finish_event.is_set()):
		if quit_event.is_set():
			break
		path = queue.get()
		# the queue is None terminated, if None is returned, just quit
		if path is None:
			break
		try:
			os.unlink(path)
		except IsADirectoryError:
			os.rmdir(path)
		except OSError as e:
			if e.errno != errno.ENOENT:
				raise e
	return

def prm(n, delete_list, dest):
	# our system should be able to roughly do 10000 files / sec in best cases
	# let's keep a queue of 1 second of work
	quit_event = Event()
	finish_event = Event()
	deleteme_queue = Queue(maxsize = 10000)
	threads = init_threads(n, __rm_worker, (deleteme_queue, finish_event, quit_event))
	print('Starting %d worker threads for %s' % (len(threads), 'removing leftover files'))
	start_threads(threads)
	read_list_process_line(delete_list, b'\0', __add2queue, (dest, deleteme_queue))
	finish_event.set()
	# let's terminate the list with None elements. At most each thread will read one None element
	# to check if execution should terminate, hence add n None elements to be sure each thread can read
	# one. To do a simple test, rsync something where nothing has to be deleted
	for j in range(n):
		deleteme_queue.put(None)
	join_threads(threads)
	return
