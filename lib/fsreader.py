#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from lib.extpath import ExtPath

class FsReader:
	'''Get the mounted/local file system'''

	def __init__(self, root):
		'''Get file structure recursivly'''
		self.root_path = Path(root)
		self.files_posix = []
		self.files_path = []
		self.dirs_posix = []
		self.dirs_path = []
		self.others_posix = []
		self.others_path = []
		for path, posix, tp in ExtPath.walk_posix(self.root_path):
			if tp == 'file':
				self.files_posix.append(posix)
				self.files_path.append(path)
			elif tp == 'dir':
				self.dirs_posix.append(posix)
				self.dirs_path.append(path)
			else:
				self.others_posix.append(posix)
				self.others_path.append(path)
