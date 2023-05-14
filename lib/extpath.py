#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-14'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Add some methods to pathlib´s Path Class'

from pathlib import Path, PurePosixPath
from platform import system

class ExtPath:
	'''Add some methods to pathlib´s Path Class'''

	@staticmethod
	def child(name, parent=None):
		'''Generate full path'''
		if not name and not parent:
			return Path.cwd()
		if parent:
			parent = Path(parent)
		else:
			parent = Path.cwd()
		if name:
			return parent/name
		else:
			return parent

	@staticmethod
	def mkdir(path):
		'''Create directory or just give full dorectory path if exists'''
		if not path:
			return Path.cwd()
		path.mkdir(exist_ok=True)
		return path

	@staticmethod
	def walk(root):
		'''Recursivly give all sub-paths'''
		return root.rglob('*')

	@staticmethod
	def walk_posix(root):
		'''Recursivly check all sub-paths for files or dirs and give posix'''
		for path in ExtPath.walk(root):
			posix = f'/{path.relative_to(root).as_posix()}'
			if path.is_file():
				yield path, posix, 'file'
			elif path.is_dir():
				yield path, posix + '/', 'dir'
			else:
				yield path, posix, None
