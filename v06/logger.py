#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .pathutils import PathUtils
from .timestamp import TimeStamp

class Logger:
	'''Simple logging'''

	def __init__(self, filename=None, outdir=None, head='Start task', echo=print):
		'''Open/create directory to write logs'''
		self.path = PathUtils.mkdir(outdir).joinpath(
			f'{filename}_log.txt' if filename else f'{TimeStamp.now(path_comp=True)}_log.txt')
		self._fh = self.path.open(mode='w', buffering=1)
		self.info(head)
		self.echo = echo

	def write(self, string):
		'''Write string to log as it is'''
		self._fh.write(string)

	def write_ln(self, *args, echo=False):
		'''Write/print one line to log'''
		print(*args, file=self._fh)
		if echo and args:
			self.echo(*args)

	def info(self, *args, echo=False):
		'''Print info to log'''
		print(TimeStamp.now(), 'INFO', *args, file=self._fh)
		if echo and args:
			self.echo(*args)

	def warning(self, *args, echo=True):
		'''Print warning to log'''
		print(TimeStamp.now(), 'WARNING', *args, file=self._fh)
		if echo:
			self.echo('WARNING', *args)

	def error(self, *args, exception=True):
		'''Print error to log'''
		if args:
			print(TimeStamp.now(), 'ERROR', *args, file=self._fh)
			self.echo('ERROR', *args)
		if isinstance(exception, str):
			print(TimeStamp.now(), 'FATAL ERROR', exception, file=self._fh)
			self._fh.close()
			raise RuntimeError(exception)
		if exception:
			self._fh.close()
			raise RuntimeError('Unspecified fatal error')

	def close(self):
		'''Close logfile'''
		self._fh.close()
