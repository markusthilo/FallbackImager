#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path, WindowsPath
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
	def sum_files(root):
		'''Get sum of all files'''
		return sum(path.is_file() for path in ExtPath.walk(root))

	@staticmethod
	def walk_normalized_files(root):
		'''Recursivly give all files in sub-paths as Path and string'''
		if isinstance(root, WindowsPath):
			slash = '\\'
		else:
			slash = '/'
		for path in ExtPath.walk(root):
			if path.is_file():
				relative = f'{path.relative_to(root)}'
				yield slash+relative, relative.replace('\\', '/').strip('/')

	@staticmethod
	def walk_posix(root):
		'''Recursivly find all sub-paths for files or dirs and give posix'''
		for path in ExtPath.walk(root):
			posix = f'/{path.relative_to(root).as_posix()}'
			if path.is_file():
				yield path, posix, 'file'
			elif path.is_dir():
				yield path, posix + '/', 'dir'
			else:
				yield path, posix, None

class FilesPercent:
	'''Show progress when going through file structure'''

	def __init__(self, root, echo=print):
		'''Get quantitiy of files under root'''
		self.echo = echo
		self.all_files = ExtPath.sum_files(root)
		self.counter = 0
		self.percent = 0
		self.factor = 100/self.all_files

	def inc(self):
		'''Check and display message'''
		self.counter += 1
		percent = int(self.factor*self.counter)
		if percent > self.percent:
			self.percent = percent
			self.echo(f'{self.percent}%, processing file {self.counter} of {self.all_files}')
