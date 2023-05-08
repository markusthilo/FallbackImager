#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-08'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Logging'

from pathlib import Path
from .extpath import ExtPath
from .timestamp import TimeStamp

class FileDirLogger:
	'''Log stored or dropped files and directories'''

	def __init__(self, filename=None, outdir=None):
		'''Open/create directory to write logs'''
		if outdir:
			self.dir_path = Path(outdir)
			self.dir_path.mkdir(exist_ok=True)
		else:
			self.dir_path = Path.cwd()
		if not filename:
			filename = TimeStamp.now()
		self.directories_file = ExtPath.open_write(f'{filename}_directories.txt', parent=self.dir_path)
		self.files_file = ExtPath.open_write(f'{filename}_files.txt', parent=self.dir_path)
		self.excluded_file = ExtPath.open_write(f'{filename}_excluded.txt', parent=self.dir_path)
		self.dropped_file = ExtPath.open_write(f'{filename}_dropped.txt', parent=self.dir_path)
		self.errors_file = ExtPath.open_write(f'{filename}_errors.txt', parent=self.dir_path)

	def close(self):
		'''Close logfiles'''
		self.errors_file.close()
		self.dropped_file.close()
		self.excluded_file.close()
		self.files_file.close()
		self.directories_file.close()
