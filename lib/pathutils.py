#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path, WindowsPath, PosixPath
from unicodedata import normalize
from string import ascii_letters, digits

__utf__ = 'utf-16-le', 'utf-16-be', 'utf-16', 'utf-8'

class PathUtils:
	'''Additional abilities for pathlib'''

	@staticmethod
	def mkdir(path):
		'''Create directory or just give full dorectory path if exists'''
		if not path:
			return Path.cwd()
		path = Path(path)
		path.mkdir(parents=True, exist_ok=True)
		return path

	@staticmethod
	def get_size(path):
		'''Get size'''
		if not path:
			path = Path.cwd()
		if path.is_dir():
			return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
		if path.is_file():
			return path.stat().st_size

	@staticmethod
	def mkfname(string):
		'''Eleminate chars that do not work in filenames'''
		string = normalize('NFKD', string).encode('ASCII', errors='ignore').decode('utf-8', errors='ignore').replace('/', '_')
		return ''.join(char for char in string if char in f'-_{ascii_letters}{digits}')

	@staticmethod
	def normalize(string):
		'''Normalize path given as string for better comparison'''
		return normalize('NFKD', string).strip('\\/').encode(errors='surrogateescape').decode(errors='surrogateescape')

	@staticmethod
	def normalize_posix(path):
		'''Normalize Posix path for better comparison'''
		return f'{path}'.strip('\t\n/').replace('\n', ' ').replace('\t', ' ').replace('\r', '').replace('/', '\\')

	@staticmethod
	def normalize_win(path):
		'''Normalize Windows path for better comparison'''
		return f'{path}'.strip('\t\n\\').replace('\n', ' ').replace('\t', ' ').replace('\r', '')

	@staticmethod
	def walk(root):
		'''Walk but give path, relative path and type'''
		for path in root.rglob('*'):
			if path.is_file():
				tp = 'file'
			elif path.is_dir():
				tp = 'dir'
			else:
				tp = None
			yield path, path.relative_to(root), tp

	@staticmethod
	def parented_walk(root):
		'''Walk but give path, parent, name and type'''
		for path in root.rglob('*'):
			if path.is_dir():
				tp = 'dir'
			elif path.is_file():
				tp = 'file'
			else:
				tp = None
			yield path, path.parent, path.name, tp

	@staticmethod
	def quantitiy(root):
		'''Get quantitiy of all items'''
		return len(list(root.rglob('*')))

	@staticmethod
	def read_utf_head(path, lines_in=10, lines_out=1):
		'''Read first lines of TSV/text file while checking UTF encoding'''
		lines = list()
		last = max(lines_in, lines_out) - 1
		for codec in __utf__:
			try:
				with path.open('r', encoding=codec) as fh:
					for cnt, line in enumerate(fh):
						lines.append(line.strip())
						if cnt == last:
							break
					if lines_out == 1:
						return codec, lines[0]
					return codec, lines[:lines_out]
			except UnicodeError:
				continue
		raise RuntimeError('Unable to detect UTF codec')

	@staticmethod
	def read_bin(path, offset=0, lines=64, bytes_per_line=16):
		'''Genereate string from binary file'''
		string = ''
		with path.open('rb') as fh:
			for line_offset in range(offset, offset+lines):
				string += f'{line_offset:016x} '
				line = fh.read(bytes_per_line)
				chars = ''
				for byte in line:
					string += f'{byte:02x} '
					if 31 < byte < 127:
						chars += chr(byte)
					else:
						chars += '.'
				string += f'{chars}\n'
		return string

class Progressor:
	'''Show progress when going through file structure'''

	def __init__(self, root_or_quant, echo=print, item='file/dir'):
		'''Get quantitiy of files under root or give quantitiy as int'''
		self.echo = echo
		self.item = item
		if isinstance(root_or_quant, int):
			self.quantitiy = root_or_quant
		else:
			self.quantitiy = Path.quantitiy(root_or_quant)
		self.counter = 0
		self.percent = 0
		self.factor = 100/self.quantitiy

	def inc(self):
		'''Check and display message'''
		self.counter += 1
		percent = int(self.factor*self.counter)
		if percent > self.percent:
			self.percent = percent
			self.echo(f'{self.percent}%, processing {self.item} {self.counter} of {self.quantitiy}')
