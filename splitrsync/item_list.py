# Copyright (C) 2018 Friedrich Miescher Institute for Biomedical Research

import io
import re
import sys

from .rsync import check_rsync_output
from . import default_buffer_size

rsync_list_re = re.compile(r'^(?P<change>[\w.*<>+]+) +(?P<size>\d+) (?P<path>.*)$')
path_escape_re = re.compile(br'\\#(?P<oct>\d{3})')

file_symbol = b'F'
directory_symbol = b'D'
delete_symbol = b'RM'

sane_path_len = 4096

class RsyncItem():
	
	def __init__(self, change, size, path):
		self.change_raw = change
		self.size = int(size)
		self.path = path
	
	def isdelete(self):
		if self.change_raw == '*deleting':
			return True
		return False
	
	def isdirectory(self):
		if self.change_raw[1] == 'd':
			return True
		return False
	
	def isupdate(self):
		# the . could mean update in the attributes, we want them
		if self.change_raw[0] in ['*']:
			return False
		return True

def _rsync_esc2char(matchobj):
	return bytes([int(matchobj.group('oct'), 8)])

def generate_list(rsync_opts, source, dest, list_path, delete_path):
	with open(list_path, 'wb') as list_fd, open(delete_path, 'wb') as delete_fd:
		#rsync_args = deepcopy(rsync_opts)
		rsync_args = rsync_opts[:]
		rsync_args.append('--dry-run')
		rsync_args.append(r'--out-format=%i %l %n')
		# rsync_args.append(r'--8-bit-output') ## not really know what this does. Keep it as a note, it might be useful
		rsync_args.append(source)
		rsync_args.append(dest)

		(out, err) = check_rsync_output(rsync_args)
		#print('OUTPUT:\n%s\n\n\nERROR:\n%s\n' % (out, err))

		unknown_lines = []
		rsync_items = [] 
		for line in out.split('\n'):
			if line is None or line == '':
				continue
			m = rsync_list_re.search(line)
			if m is None:
				print('WARNING: unrecognized rsync output line: %s' % line, file=sys.stderr)
				unknown_lines.append(line)
				continue
			change = m.group('change').encode()
			size = m.group('size').encode()
			raw_path = m.group('path').encode()
			path = path_escape_re.sub(_rsync_esc2char, raw_path)
			if change == b'*deleting':
				delete_fd.write(path + b'\0')
			else:
				isdir = file_symbol
				if change[1] == b'd'[0]:  # a bit ugly
					isdir = directory_symbol
				list_fd.write(isdir + b' ' + size + b' ' + path + b'\0')
	return

def dump_list(item_list, path):
	with open(path, 'w') as f:
		for item in item_list:
			f.write('%s\0' % item.path)
	return

def read_list_process_line(list_path, sep, process_func, args):
	with open(list_path, 'rb', buffering = default_buffer_size) as list_fd:
		#list_fd = io.BufferedReader(fd, buffer_size = default_buffer_size)
		next_item = b''
		buf = list_fd.read(default_buffer_size)
		while len(buf) > 0:
			s = buf.split(sep)
			for i in range(len(s) - 1):
				next_item += s[i]
				process_func(next_item, *args)
				next_item = b''
			next_item = s[len(s) - 1]
			if len(next_item) > sane_path_len:
				# malformed files can go on forever here, if we keep reading without
				# finding a separator after reaching a maximum possible path length
				# just stop and abort
				raise RuntimeError(
						'Possible corrupt input file. Cannot find a end of line separator %s ' \
						'after %d characters. If you specified a list of files with --files-from ' \
						'you should use --from0 if you used \\0 as field separator, otherwise ' \
						'you should *not* use --from0. If you didn\'t specify a list of file ' \
						'with --files-from the temporary file internally created was likely corrupted' %
						(sep, sane_path_len)
					)
			buf = list_fd.read(default_buffer_size)
		# process last item in case the list doesn't end with the sep char
		if next_item != b'':
			process_func(*((next_item,) + args))
	return
