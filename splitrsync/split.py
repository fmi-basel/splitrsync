from copy import deepcopy
from tempfile import mkdtemp
from .item_list import dump_list


_min_corrected_size = 4096
	
def split_list_rr(item_list, n):
	d = {}
	for i in range(n):
		d[i] = []
	i = 0
	for item in item_list:
		d[i].append(item)
		i += 1
		i %= n
	return d

def _find_smaller(size):
	smaller = 0
	for i in range(len(size)):
		#print('i = %d, smaller = %d: %d, %d' % (i, smaller, size[i], size[smaller]))
		if size[i] < size[smaller]:
			smaller = i
	return smaller

def split_list_size(item_list, n):
	d = {}
	size = [0] * n
	for i in range(n):
		d[i] = []
	smaller = 0
	for item in item_list:
		d[smaller].append(item)
		# adjust size to give a minimum wait to metadata only operations
		# this way they get distributed more evenly across different processes
		corrected_size = item.size if item.size >= _min_corrected_size else _min_corrected_size
		size[smaller] += corrected_size
		smaller = _find_smaller(size)
	return d

# default split function
split_list = split_list_size

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
