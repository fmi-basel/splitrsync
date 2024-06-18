# Copyright (C) 2020 Friedrich Miescher Institute for Biomedical Research

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

##############################################################################
#                                                                            #
# Author: Enrico Tagliavini          <enrico.tagliavini@fmi.ch>              #
#                                                                            #
##############################################################################

import errno
import os
import shutil

from concurrent.futures import ThreadPoolExecutor
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
	# our own filter must be added last or it will override the user provided one
	# TODO FIXME we must remove any file filter the user specified or we end up syncing files
	# in here
	# ACTUALLY remove the filters entirely form rsync_args and add your own. We have the
	# list file from --files-from anyway, but we might have recursive enabled in rsync
	# so we still want our own filter to exclude all files on get directories only
	# TODO remove original filters
	rsync_args = args + ['-f+ */', '-f- *']
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

def __print_rm_error(function, path, excinfo):
	excpt = excinfo[1]
	if hasattr(excpt, 'errno') and excpt.errno == errno.ENOENT:
		# we tried to remove a file that doesn't exist, all good
		return
	print('Error while removing %s: %s' % (path, str(excpt)))

# we remove only the files to avoid the different thread worker to fight each other unnecessarily removing directories
# recursively. Instead we save the directory list to be removed for later and we remove those later
# not doing so can also cause problems on some file systems such as NFS, which is not POSIX and might throw a 
# stale file error if multiple threads are trying to remove it in parallel
def __rm_worker(files_list):
	dir_list = []
	for file_path in files_list:
		try:
			os.unlink(file_path)
		except IsADirectoryError:
			# shutil.rmtree(file_path, False, __print_rm_error)
			dir_list.append(file_path)
		except OSError as e:
			if e.errno != errno.ENOENT:
				raise e
	return dir_list

batch_size = 1000
def __batch_rm_files(item, dest, executor, last = False):
	# if last == True we might not have another item, we just want to start processing the remaining items in the batch
	if item is not None:
		__batch_rm_files.next_batch.append(dest + b'/' + item)
	if len(__batch_rm_files.next_batch) >= batch_size or last:
		f = __submit2executor(__batch_rm_files.next_batch, executor)
		__batch_rm_files.next_batch = []
		__batch_rm_files.futures.append(f)
	return
# static variable initialization trick
__batch_rm_files.next_batch = []
__batch_rm_files.futures = []

def __submit2executor(item_list, executor):
	return executor.submit(__rm_worker, item_list)

# TODO add handlers for SIGINT / SIGTERM etc to shutdown the executor without waiting
def prm(n, delete_list, dest):
	print('Starting worker threads for removing leftover files')
	global executor
	with ThreadPoolExecutor(thread_name_prefix = 'rm_worker_') as executor:
		read_list_process_line(delete_list, b'\0', __batch_rm_files, (dest, executor))
		__batch_rm_files(None, None, executor, True)
		futures = __batch_rm_files.futures
		dir_list = []
		for f in futures:
			dir_list += f.result()
	
	dir_list.sort(reverse = True)
	print('Worker threads finished removing files, now removing the remaining %d folders' % len(dir_list))
	for dir_p in dir_list:
		# shutil.rmtree(dir_p, False, __print_rm_error)
		try:
			os.rmdir(dir_p)
		except OSError as e:
			if e.errno != errno.ENOENT:
				raise e
	return
