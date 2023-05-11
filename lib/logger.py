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

	PROC_FINISHED = 'Process finished'
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
			self.echo(*args)

	def warning(self, *args, string=None, echo=True):
		'''Print warning to log'''
		print(TimeStamp.now(), 'WARNING', *args, file=self._fh)
		if echo:
			self.echo('WARNING', *args)
		if string:
			self.write(string)
			if echo:
				self.echo(string)

	def error(self, *args, string=None, exception=True):
		'''Print error to log'''
		print(TimeStamp.now(), 'ERROR', *args, file=self._fh)
		self.echo('ERROR', *args)
		if string:
			self.write(string)
			self.echo(string)
		if exception:
			self._fh.close()
			raise RuntimeError(self.PROC_ERROR)

	def finished(self, proc, error='', echo=True, exception=True):
		'''Handle finished process'''
		if proc.stderr_str or error:
			if proc.stdout_str:
				self.write(proc.stdout_str)
				self.echo(proc.stdout_str)
			self.error(self.PROC_ERROR, error,
				string = proc.stderr_str,
				exception = exception
			)
		else:
			if proc.stdout_str:
				self.write(proc.stdout_str)
			if echo:
				self.echo(proc.stdout_str)
			self.info(self.PROC_FINISHED, echo=echo)

	def close(self):
		'''Close logfile'''
		self._fh.close()
