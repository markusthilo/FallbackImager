#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-10'
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
		cwd = Path.cwd()
		if not path:
			return cwd
		path.mkdir(exist_ok=True)
		return path

	@staticmethod
	def to_str(path, parent=None, prefix=None):
		'''Give Joliet or UDF compatible path as string'''
		if parent:
			path = path.relative_to(parent)
		string = f'{PurePosixPath(path)}'
		if prefix:
			return f'{prefix}{string}'
		return string

	@staticmethod
	def str_to_posix(string):
		'''Normalize backslashes to Posix conformity'''
		return string.replace('\\', '/')

	@staticmethod
	def walk(root_path):
		'''Recursivly give all sub-paths'''
		for path in root_path.rglob('*'):
			yield path

	@staticmethod
	def walk_win_str(root_path):
		'''Recursivly give all sub-paths as strings on Windows'''
		first_str = str(ExtPath.walk(root_path).relative_to(root_path))
		if len(first_str) > 1 and first_str[1] == ':':
			skip = 3
		elif first_str[0] == '\\':
			skip = 1
		else:
			skip = 0
		for path in ExtPath.walk(root_path):
			yield str(path.relative_to(root_path))[skip:]

