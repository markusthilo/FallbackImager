#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .extpath import ExtPath
from .timestamp import TimeStamp

class Logger:
	'''Simple logging'''

	PROC_FINISHED = 'Process finished successfully'
	PROC_ERROR = 'Process ended unsuccessfully'

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

	def info(self, *args, echo=False):
		'''Print info to log'''
		print(TimeStamp.now(), 'INFO', *args, file=self._fh)
		if echo and args:
			self.echo(*args)

	def warning(self, *args, string=None, echo=True):
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

	def error(self, *args, string=None, exception=True):
		'''Print error to log'''
		print(TimeStamp.now(), 'ERROR', *args, file=self._fh)
		self.echo('ERROR', *args)
		if string:
			print(file=self._fh)
			self.write(string)
			self.echo()
			self.echo(string)
		if exception:
			self._fh.close()
			raise RuntimeError(self.PROC_ERROR)

	def finished(self, proc, info='', error='', echo=True, exception=True):
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
			if echo and proc.stdout_str:
				self.echo(proc.stdout_str)
			self.info(self.PROC_FINISHED, info, echo=echo)

	def close(self):
		'''Close logfile'''
		self._fh.close()
