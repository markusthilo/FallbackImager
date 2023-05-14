#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-14'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Read source/local file structure'

from pathlib import Path
from lib.extpath import ExtPath

class FsReader:
	'''Get the mounted/local file system'''

	def __init__(self, root):
		'''Define root'''
		self.root_path = Path(root)

	def get_posix(self):
		'''Get file structure recursivly'''
		self.posix_paths = list()
		self.file_cnt = 0
		self.dir_cnt = 0
		self.else_cnt = 0
		for path, posix, tp in ExtPath.walk_posix(self.root_path):
			if tp == 'file':
				self.posix_paths.append(posix)
				self.file_cnt += 1
			elif tp == 'dir':
				self.posix_paths.append(posix)
				self.dir_cnt += 1
			else:
				self.posix_paths.append('$'+posix)
				self.else_cnt += 1
		self.posix_paths.sort()
		return self.posix_paths
