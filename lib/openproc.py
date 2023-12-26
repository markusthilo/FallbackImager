#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import name as __os_name__
from subprocess import Popen, PIPE, STDOUT
if __os_name__ == 'nt':
	from subprocess import STARTUPINFO, STARTF_USESHOWWINDOW

class OpenProc(Popen):
	'''Use Popen the way it is needed here'''

	def __init__(self, cmd):
		'''Launch process'''
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
			super().__init__(cmd, stdout=PIPE, stderr=STDOUT)

	def echo_output(self, log):
		'''Echo stdout'''
		stack = list()
		for line in self.stdout:
			if line:
				stack.append(line.strip())
				log.echo(stack[-1])
			if len(stack) > 10:
				stack.pop(0)
		self.wait()
		if stack:
			log.info('\n'.join(stack))