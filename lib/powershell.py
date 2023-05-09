#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-09'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Release'
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
		self.stdout_str = self.stdout.read().strip()
		self.stderr_str = self.stderr.read().strip()
		print(self.stdout_str)
		if self.stderr_str:
			print(self.stderr_str)

	def get_stdout_decoded(self, delimiter=':'):
		'''Give  stdout decoded to dict'''
		decoded = dict()
		for line in self.stdout_str.split('\n'):
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
