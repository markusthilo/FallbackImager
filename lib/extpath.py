#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path, WindowsPath, PosixPath
from unicodedata import normalize
from string import ascii_letters, digits

__utf__ = 'utf-16-le', 'utf-16-be', 'utf-16', 'utf-8'

class ExtPath:
	'''Add some methods to pathlib´s Path Class'''

	@staticmethod
	def path(arg):
		'''Generate Path object'''
		if isinstance(arg, str):
			return Path(arg.strip('"'))
		else:
			return Path(arg)

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
		path = Path(path)
		path.mkdir(exist_ok=True)
		return path

	@staticmethod
	def get_size(path):
		'''Get size'''
		if not path:
			path = Path.cwd()
		if path.is_dir():
			return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())
		if path.is_file():
			return path.stat().st_size

	@staticmethod
	def mkfname(string):
		'''Eleminate chars that do not work in filenames'''
		string = normalize('NFKD', string).encode('ASCII', errors='ignore').decode('utf-8', errors='ignore').replace('/', '_')
		return ''.join(char for char in string if char in f'-_{ascii_letters}{digits}')

	@staticmethod
	def normalize_str(string):
		'''Normalize path given as string for better comparison'''
		string = normalize('NFD', string).encode(errors='ignore').decode('utf-8', errors='ignore').strip('\t\n\\/')
		string = string.replace('\n', ' ').replace('\t', ' ').replace('\r', '')
		string = string.replace(b'\xe2\x86\xb2'.decode(), '')
		string = string.replace(b'\x00\x00\x00\x00'.decode(), '.')
		return string

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
		'''Recursivly give all sub-paths'''
		for path in root.rglob('*'):
			if path.is_file():
				tp = 'File'
			elif path.is_dir():
				tp = 'Dir'
			else:
				tp = None
			yield path, path.relative_to(root), tp

	@staticmethod
	def quantitiy(root):
		'''Get quantitiy of all items'''
		return len(list(root.rglob('*')))

	@staticmethod
	def read_utf_head(path, after=0):
		'''Read first lines of TSV/text file while checking UTF encoding'''
		lines = list()
		for codec in __utf__:
			try:
				with path.open('r', encoding=codec) as fh:
					for cnt, line in enumerate(fh):
						lines.append(line.strip())
						if cnt == after:
							break
					if after == 0:
						return codec, lines[0]
					return codec, lines
			except UnicodeError:
				continue

	@staticmethod
	def readable_size(size):
		'''Genereate readable size string'''
		try:
			size = int(size)
		except (TypeError, ValueError):
			return 'undetected'
		strings = list()
		for base in (
			{'PiB': 2**50, 'TiB': 2**40, 'GiB': 2**30, 'MiB': 2**20, 'kiB': 2**10},
			{'PB': 10**15, 'TB': 10**12, 'GB': 10**9, 'MB': 10**6, 'kB': 10**3}
		):
			for u, b in base.items():
				rnd = round(size/b, 2)
				if rnd >= 1:
					break
			if rnd >= 10:
				rnd = round(rnd, 1)
			if rnd >= 100:
				rnd = round(rnd)
			strings.append(f'{rnd} {u}')
		return ' / '.join(strings)

	@staticmethod
	def readable_bin(path, offset=0, lines=64, bytes_per_line=16):
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

	def __init__(self, root, echo=print):
		'''Get quantitiy of files under root'''
		self.echo = echo
		self.quantitiy = ExtPath.quantitiy(root)
		self.counter = 0
		self.percent = 0
		self.factor = 100/self.quantitiy

	def inc(self):
		'''Check and display message'''
		self.counter += 1
		percent = int(self.factor*self.counter)
		if percent > self.percent:
			self.percent = percent
			self.echo(f'{self.percent}%, processing file/dir {self.counter} of {self.quantitiy}')
