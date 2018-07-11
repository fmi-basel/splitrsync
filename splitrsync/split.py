# Copyright (C) 2018 Friedrich Miescher Institute for Biomedical Research

from copy import deepcopy
from .item_list import dump_list, read_list_process_line
from .item_list import directory_symbol
from . import default_buffer_size

import io
import re

_min_corrected_size = 4096
spacer_re = re.compile(b'\s+')

def _static_vars(**kwargs):
	def decorate(func):
		for k in kwargs:
			setattr(func, k, kwargs[k])
		return func
	return decorate

def _find_smaller(size):
	smaller = 0
	for i in range(len(size)):
		#print('i = %d, smaller = %d: %d, %d' % (i, smaller, size[i], size[smaller]))
		if size[i] < size[smaller]:
			smaller = i
	return smaller

@_static_vars(next_index = 0)
def split_rr(**kwargs):
	n = kwargs['n']
	ret = split_rr.next_index
	split_rr.next_index = (split_rr.next_index + 1) % n
	return ret

@_static_vars(smaller = 0, sizes = [])
def split_size(**kwargs):
	n = kwargs['n']
	try:
		size = int(kwargs['size'], 10)
	except ValueError as e:
		raise RuntimeError('Invalid integer found for size while processing input file: %s' % str(e))
	if split_size.sizes == []:
		split_size.sizes = [0] * n
	ret = split_size.smaller
	corrected_size = size if size >= _min_corrected_size else _min_corrected_size
	split_size.sizes[split_size.smaller] += corrected_size
	split_size.smaller = _find_smaller(split_size.sizes)
	return ret

# default split function
default_split_list = split_rr

def _process_item(raw_line, split_fd_list, split_func, dir_list):
	try:
		is_dir, size, path = raw_line.split(b' ', 2)
	except ValueError:
		# TODO requires some further enhancement to be cough later
		raise ValueError('Input file list contains malformed line: %s' % repr(raw_line))
	if is_dir == directory_symbol:
		dir_list.write(path + b'\0')
	else:
		index = split_func(n = len(split_fd_list), size = size)
		split_fd_list[index].write(path + b'\0')
	return

def read_split_dump(file_list_path, sep, n, split_func, tmpdir, name = 'list-%s'):
	split_list_files = []
	split_fd_list = []
	dir_list_path = tmpdir + '/' + name % 'dir'
	dir_list = open(dir_list_path, 'wb')
	for i in range(n):
		next_file = tmpdir + '/' + name % str(i)
		split_list_files.append(next_file)
		split_fd_list.append(open(next_file, 'wb', buffering = default_buffer_size))
	read_list_process_line(file_list_path, sep, _process_item, (split_fd_list, split_func, dir_list))
	for fd in split_fd_list:
		fd.close()
	dir_list.close()
	return split_list_files, dir_list_path

def dump_split_list(item_split_list, name = 'list-%d', path = None):
	dir_path = path
	if path is None:
		dir_path = mkdtemp(suffix='.tmp', prefix='splitrsync_')
	file_list = []
	for i in range(len(item_split_list)):
		next_file = dir_path + '/' + name % i
		file_list.append(next_file)
		dump_list(item_split_list[i], next_file)
	return (dir_path, file_list)
