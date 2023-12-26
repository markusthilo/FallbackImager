#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lib.extpath import ExtPath
from lib.timestamp import TimeStamp

class Logger:
	'''Simple logging'''

	def __init__(self, filename=None, outdir=None, head='Start task', echo=print):
		'''Open/create directory to write logs'''
		self.outdir = ExtPath.mkdir(outdir)
		self.path = ExtPath.child(f'{filename}_log.txt', parent=self.outdir)
		self._fh = self.path.open(mode='w')
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
		if string:
			print(file=self._fh)
			self.write(string)
			if echo:
				self.echo()
				self.echo(string)

	def error(self, *args, exception='Unspecified error occured'):
		'''Print error to log'''
		print(TimeStamp.now(), 'ERROR', *args, file=self._fh)
		self.echo('ERROR', *args)
		if exception:
			self._fh.close()
			raise RuntimeError(exception)

	def close(self):
		'''Close logfile'''
		self._fh.close()
