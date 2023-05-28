#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from re import compile as regcompile

class RegList:
	'''List of regular expressions'''

	def __init__(self, path):
		'''Read file and build list with '''
		if isinstance(path, Path):
			with path.open() as textfile:
				self.regs = [regcompile(line.strip()) for line in textfile]
		else:
			self.regs = None

	def is_match(self, string):
		'''True if one regular expression matches'''
		if self.regs:
			for reg in self.regs:
				if reg.search(string):
					return True
		return False
