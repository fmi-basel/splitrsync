import os

from subprocess import Popen as popen
from tempfile import mkstemp
from threading import Thread

from .rsync import check_rsync_output
from .item_list import dump_list, generate_list
from .split import dump_split_list, split_list_size

join_timeout = 604800 # 1 week

class RsyncSplitList():
	
	def __init__(self, nproc, item_list, split = split_list_size):
		self.nproc = nproc
		self.split_list = split(item_list, 4)
		self.dir_list = [d for d in filter(lambda x: x.isdirectory(), item_list)]
		self.dump_dir = None
		self.split_file_list = None
		self.dir_list_path = None
		return
	
	def dump(self, name_prefix = 'rsync_list', path = None):
		if self.dump_dir is None:
			tmpdir, split_file_list = dump_split_list(self.split_list, name_prefix + '-%d', path)
			self.dir_list_path = tmpdir + '/' + name_prefix + '-dir'
			dump_list(self.dir_list, self.dir_list_path)
			self.dump_dir = tmpdir
			self.split_file_list = split_file_list
		return (self.dump_dir, self.split_file_list, self.dir_list_path)

def generate_split_list(rsync_opts, source, dest, nproc, split = split_list_size):
	return RsyncSplitList(nproc, generate_list(rsync_opts, source, dest), split)

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
	rsync_args.append('--files-from=%s' % list_file_path)
	rsync_args.append('--from0')
	rsync_args.append(source)
	rsync_args.append(dest)
	print('[Thread %d] starting rsync' % t_number)
	(out, err) = check_rsync_output(rsync_args)
	print('[Thread %d] rsync finished' % t_number)
	return

def prsync(args, split_list, source, dest):
	if '--delete' in args:
		raise ValueError('--delete option is forbidden during parallel rsync')
	print('Syncing directory tree')
	rsync_dir_tree(args, split_list, source, dest)
	print('Syncing directory tree finished')
	threads = []
	for i in range(split_list.nproc):
		threads.append(Thread(
				name = 'Working thread number %d' % i,
				target = __rsync_worker,
				args = (i, args, split_list.split_file_list[i], source, dest)
			))
	print('Starting %d worker threads for syncing')
	for t in threads:
		t.start()
	for t in threads:
		t.join(join_timeout)
	print('All threads terminated')
	return
