#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-11'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Logging'

from .extpath import ExtPath
from .timestamp import TimeStamp

class Logger:
	'''Simple logging'''

	PROC_ERROR = 'Process returned error'

	def __init__(self, filename=None, outdir=None, head='Start task', echo=print):
		'''Open/create directory to write logs'''
		self.path = ExtPath.child(f'{filename}_log.txt', parent=outdir)
		self._fh = self.path.open(mode='w')
		self.info(head)
		self.echo = echo

	def write(self, string):
		'''Write string to log as it is'''
		self._fh.write(string)

	def info(self, *args, echo=False):
		'''Print info to log'''
		print(TimeStamp.now(), 'INFO', *args, file=self._fh)
		if echo:
			echo(*args)

	def warning(self, *args, string=None, echo=True):
		'''Print warning to log'''
		print(TimeStamp.now(), 'WARNING', *args, file=self._fh)
		if string:
			self.write(string)
		print(file=self._fh)
		if echo:
			self.echo('WARNING', *args)

	def error(self, *args, string=None, no_exception=False):
		'''Print error to log'''
		print(TimeStamp.now(), 'ERROR', *args, file=self._fh)
		if string:
			self.write(string)
		print(file=self._fh)
		if echo:
			self.echo('ERROR', *args)
		if not no_exception:
			self._fh.close()
		raise RuntimeError(self.PROC_ERROR)

	def finished(self, proc, echo=True, no_exception=False):
		'''Handle finished process'''
		if proc.stdout_str:
			self.write(proc.stdout_str)
		if proc.stderr_str:
			self.error('Process returned error',
				string = proc.stderr_str,
				no_exception = no_exception
			)
		else:
			self.info('Process finished', echo=echo)

	def close(self):
		'''Close logfile'''
		self._fh.close()
