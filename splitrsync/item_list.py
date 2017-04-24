import re
import sys

from .rsync import check_rsync_output

rsync_list_re = re.compile(r'^(?P<change>[\w.*<>+]+) +(?P<size>\d+) (?P<path>.*)$')
path_escape_re = re.compile(r'\\#(?P<oct>\d{3})')

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
	return chr(int(matchobj.group('oct'), 8))

def generate_list(rsync_opts, source, dest):
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
		change = m.group('change')
		size = m.group('size')
		raw_path = m.group('path')
		path = path_escape_re.sub(_rsync_esc2char, raw_path)
		#print('%s %s %s' % (change, size, path))
		rsync_items.append(RsyncItem(change, size, path))
	
	rsync_items.sort(key=(lambda x: x.size), reverse=True)
	return rsync_items

def dump_list(item_list, path):
	with open(path, 'w') as f:
		for item in item_list:
			f.write('%s\0' % item.path)
	return

#from stat import S_ISDIR
#def list_from_files(paths):
	#item_list = []
	#for f in paths:
		## WARNING might need to prepend the src for absolute path
		#with open(f, 'r') as list_fd:
			#for item in list_fd.read().split('\0'):
				#change = '>fc........'
				#if item is None or item == '':
					#continue
				#item_stat = os.stat(item)
				#if S_ISDIR(item_stat.st_mode):
					#change[1] = 'd'
				#item_list.append(RsyncItem(change, item_stat.st_size, f))
	#return item_list
