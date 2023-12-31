#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import name as __os_name__
from subprocess import Popen, PIPE, STDOUT
if __os_name__ == 'nt':
	from subprocess import STARTUPINFO, STARTF_USESHOWWINDOW

class OpenProc(Popen):
	'''Use Popen the way it is needed here'''

	def __init__(self, cmd, stderr=True, log=None):
		'''Launch process'''
		self.log = log
		if self.log:
			self.log.info(f'Executing {" ".join(cmd)}')
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

	def echo_output(self, echo=print):
		'''Echo stdout'''
		if self.log:
			stack = list()
			for line in self.stdout:
				if line:
					stack.append(line.strip())
					self.log.echo(stack[-1])
				if len(stack) > 10:
					stack.pop(0)
			if stack:
				self.log.info('\n'.join(stack))
		else:
			for line in self.stdout:
				if line:
					echo(line.strip())
