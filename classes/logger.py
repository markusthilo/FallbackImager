#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime

class Logger:
	'''Handle logging'''

	def __init__(self, path, kill=None):
		'''Open/create config file'''
		self._files = [path.open('w')]
		self._kill = kill

	def add(self, path):
		self._files.append(path.open('w'))

	def close(self, instance=0):
		'''Close config file(s)'''
		if instance:
			self._files.pop(instance)
		else:
			for f in self._files:
				f.close()

	def _now(self):
		return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f %Z')

	def write(self, entry):
		'''Write entry to log file'''
		entry = f'{self._now()} {entry}'
		for f in self._files:
			print(entry, flush=True, file=f)

	def exception(self, ex):
		'''Write exception to log file'''
		self.write(f'{type(ex)}: {ex}')

	def check_kill_signal(self):
		'''Check if kill signal is set'''
		if self._kill and self._kill.is_set():
			self.write('Aborted due to user interaction')
			self.close()
			return True
		return False