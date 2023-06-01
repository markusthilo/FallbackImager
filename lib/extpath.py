#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path, WindowsPath
from unicodedata import normalize

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
	def windowize(path):
		'''Replace slashes with backslashes'''
		if isinstance(path, PosixPath):
			return Path(str(path).replace('/', '\\'))
		return path

	@staticmethod
	def normalize(path):
		'''Normalize path for better comparison'''
		path = normalize('NFD', path).encode(errors='ignore').decode('utf-8', errors='ignore')
		path = path.rstrip('\\/ \t\n').replace(':', '/')
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
	def walk_files(root):
		'''Recursivly find all files'''
		if isinstance(root, WindowsPath):
			slash = '\\'
		else:
			slash = '/'
		for path in ExtPath.walk(root):
			yield f'{slash}{path.relative_to(root)}'

	@staticmethod
	def walk_posix(root):
		'''Recursivly find all sub-paths for files or dirs and give posix'''
		for path in ExtPath.walk(root):
			posix = f'/{path.relative_to(root).as_posix()}'
			if path.is_file():
				yield path, posix, 'file'
			elif path.is_dir():
				yield path, f'{posix}/', 'dir'
			else:
				yield path, posix, None

	@staticmethod
	def read_head(path, after=None):
		'''Read first line of TSV/text file while checking UTF encoding'''
		for codec in 'utf-16-le', 'utf-16-be', 'utf-16', 'utf-8':
			try:
				with path.open('r', encoding=codec) as fh:
					head = fh.readline().strip()
					if after and after > 0:
						head = [head]
						while after > 0:
							line = fh.readline()
							if not line:
								break
							head.append(line)
							after -= 1
					break
			except UnicodeDecodeError:
				continue
		return head, codec

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
