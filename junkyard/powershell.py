#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-11-23'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Interface for PowerShell commands'

from subprocess import Popen, PIPE
from os import environ

class PowerShell(Popen):
	'''Powershell via subprocess'''

	def __init__(self, cmd):
		'''Init subprocess without showing a terminal window'''
		self.cmd_str = '>'
		for arg in cmd:
			self.cmd_str += f' {arg}'
		print(self.cmd_str)
		super().__init__(
			['powershell', '-Command'] + cmd,
			stdout = PIPE,
			stderr = PIPE,
			encoding = 'utf-8',
			errors = 'ignore',
			universal_newlines = True
		)

	def _read_stderr(self):
		'''Read stderr ro string and print error'''
		self.stderr_str = self.stderr.read().strip()
		if self.stderr_str:
			print(self.stderr_str)

	def read_all(self):
		'''Get full stdout and stderr as string'''
		self.stdout_str = self.stdout.read().strip()
		self._read_stderr()

	def readlines_stdout(self):
		'''Read stdout line by line''' 
		for line in self.stdout:
			line = line.strip()
			if line:
				yield line
		self.stdout_str = None
		self._read_stderr()

	def get_stdout_decoded(self, delimiter=':'):
		'''Give  stdout decoded to dict'''
		decoded = dict()
		for line in self.readlines_stdout():
			try:
				key, value = line.split(delimiter, 1)
			except ValueError:
				continue
			key = key.strip()
			value = value.strip()
			if key in decoded:
				decoded[key].append(value)
			else:
				decoded[key] = [value]
		return decoded
