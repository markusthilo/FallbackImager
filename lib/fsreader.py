#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from lib.extpath import ExtPath

class FsReader:
	'''Get the mounted/local file system'''

	def __init__(self, root):
		'''Define root'''
		self.root_path = Path(root)

	def get_posix(self):
		'''Get file structure recursivly'''
		self.file_cnt = 0
		self.dir_cnt = 0
		self.else_cnt = 0
		for path, posix, tp in ExtPath.walk_posix(self.root_path):
			if tp == 'file':
				self.file_cnt += 1
				yield posix
			elif tp == 'dir':
				self.dir_cnt += 1
				yield posix
			else:
				self.else_cnt += 1
				yield f'${posix}'
