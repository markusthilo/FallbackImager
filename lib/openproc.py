#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import name as __os_name__
from subprocess import Popen, PIPE, STDOUT, DEVNULL
if __os_name__ == 'nt':
	from subprocess import STARTUPINFO, STARTF_USESHOWWINDOW

class OpenProc(Popen):
	'''Use Popen the way it is needed here'''

	def __init__(self, cmd, stderr=True, log=None):
		'''Launch process'''
		self.log = log
		if __os_name__ == 'nt':
			self.startupinfo = STARTUPINFO()
			self.startupinfo.dwFlags |= STARTF_USESHOWWINDOW
			super().__init__(cmd,
				stdout = PIPE,
				stderr = STDOUT,
				encoding = 'utf-8',
				errors = 'ignore',
				universal_newlines = True,
				startupinfo = self.startupinfo
			)
		else:
			if stderr:
				stderr = PIPE
			else:
				stderr = STDOUT
			super().__init__(cmd, stdout=PIPE, stderr=stderr, encoding='utf-8')

	def echo_output(self, echo=print, cnt=None, skip=0):
		'''Echo stdout, cnt: max. lines to log, skip: skip lines to log'''
		if self.log:
			stdout_cnt = 0
			stack = list()
			for line in self.stdout:
				if line:
					stdout_cnt += 1
					stripped = line.strip()
					self.log.echo(stripped)
					if stdout_cnt > skip:
						stack.append(stripped)
				if cnt and len(stack) > cnt:
					stack.pop(0)
			if stack:
				self.log.info('\n' + '\n'.join(stack))
		else:
			for line in self.stdout:
				if line:
					echo(line.strip())
