# Copyright (C) 2018 Friedrich Miescher Institute for Biomedical Research

from subprocess import Popen as popen, PIPE, STDOUT, DEVNULL

import sys

rsync_cmd = b'rsync'
rsync_copts = []  # cannot put -q here, will silence the --itemize output

class RsyncError(Exception):
	# output is just the (guessed) relevant part for the error, not the whole
	def __init__(self, message, output = None):
		super(RsyncError, self).__init__(message)
		self.message = message
		self.output = output

	def __str__(self):
		out = self.message
		if self.output is not None and len(self.output) > 0:
			out += '\n\nRsync output / error:\n%s\n\n' % self.output
		return out

def check_rsync_output(args):
	try:
		#print('calling: rsync ' + ' '.join(args))
		rsync = popen(basic_rsync_cmd() + args, stdin=DEVNULL, stdout=PIPE, stderr=PIPE)
		(out, err) = rsync.communicate()
		rsync.wait()
	except (OSError,IOError) as e:
		raise RsyncError(str(e))
	out = out.decode()
	err = err.decode()
	if rsync.returncode != 0:
		raise RsyncError('rsync process terminated with returncode %d' % rsync.returncode, err)
	if err is not None and err != '':
		print('WARNING: rsync output found on standard error:', file=sys.stderr)
		for line in err.split('\n'):
			if line is None or line == '':
				continue
			print('rsync standard error: %s' % line, file=sys.stderr)
		print('', file=sys.stderr)
	return (out, err)

def basic_rsync_cmd():
	return [rsync_cmd] + rsync_copts
