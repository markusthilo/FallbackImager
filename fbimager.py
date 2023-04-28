#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-04-28'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Generate ISO from a partition of an evidence item'

from pathlib import Path
from sys import executable
from re import compile as regcompile
from pycdlib import PyCdlib
from argparse import ArgumentParser, FileType

class ExtPath(Path):
	'''Add some methodes to pathlib's Path Class'''

	@staticmethod
	def app_path():
		'''Return path of Python script or executable binary if compiled'''
		scriptpath = Path(__file__)
		exepath =  Path(executable)
		if exepath.stem != scriptpath.stem:
			return scriptpath
		else:
			return exepath

	@staticmethod
	def open_read(path, default=None, encoding=None, errors=None, newline=None):
		'''Open file to read. Set default for configs etc.'''
		if path:
			path = Path(path)
		elif default:
			path = ExtPath.app_path().parent/default
		if path.is_file():
			return path.open(encoding=encoding, errors=errors, newline=newline)

	@staticmethod
	def path_to_write(filename, parent=Path.cwd()):
		'''Generate full path to write file'''
		if parent:
			parent = Path(parent)
		else:
			parent = Path.cwd()
		return parent/filename

	@staticmethod
	def open_write(filename, parent=None, encoding=None, errors=None, newline=None):
		'''Open file to write'''
		return ExtPath.path_to_write(filename, parent=parent).open(
			mode='w', encoding=encoding, errors=errors, newline=newline)

	@staticmethod
	def joliet(full, parent=None):
		'''Give Joliet compatible path as string'''
		if parent:
			return f'/{full.relative_to(parent)}'
		return f'/{full}'

class RegList:
	'''List of regular expressions to exclude paths'''

	def __init__(self, textfile):
		'''Read file and build list with '''
		if textfile:
			self.regs = [ regcompile(line.strip()) for line in textfile ]
			textfile.close()
		else:
			self.regs = None

	def is_match(self, string):
		'''True if one regular expression matches'''
		if self.regs:
			for reg in self.regs:
				if reg.search(string):
					return True
		return False

class ISO(PyCdlib):
	'''ISO Image, Joliet 3'''

	def __init__(self, image_path):
		'''Create image'''
		self.image_path = image_path
		super().__init__()
		self.new(joliet=3)
		self._joliet_facade = self.get_joliet_facade()

	def joliet_add_directory(self, rel_path):
		'''Add directory to image'''
		self._joliet_facade.add_directory(joliet_path=f'/{rel_path}')

	def joliet_add_file(self, full_path, rel_path):
		'''Add file to image'''
		self._joliet_facade.add_file(full_path, joliet_path=f'/{rel_path}')

	def close(self):
		'''Write and close'''
		super().write(self.image_path)
		super().close()

class Imager:
	'''Image Generator'''

	def __init__(self, root,
		blacklist = None,
		filename = None,
		outdir = None,
		whitelist = None
	):
		'''Definitions'''
		self.root_path = Path(root)
		self.blacklist = RegList(ExtPath.open_read(blacklist, default='blacklist.txt'))
		self.whitelist = RegList(ExtPath.open_read(whitelist, default='whitelist.txt'))
		if self.whitelist.regs:
			self.to_store = self.is_in_whitelist
		else:
			self.to_store = self.not_in_blacklist
		self.dir_path = Path(outdir)
		self.dir_path.mkdir(exist_ok=True)
		self.iso = ISO(ExtPath.path_to_write(f'{filename}.iso', parent=self.dir_path))
		self.content_file = ExtPath.open_write(f'{filename}_content.txt', parent=self.dir_path)
		self.dropped_file = ExtPath.open_write(f'{filename}_dropped.txt', parent=self.dir_path)

	def not_in_blacklist(self, joliet_str):
		'''Return True when path is blacklisted'''
		return not self.blacklist.is_match(joliet_str.strip('/'))

	def is_in_whitelist(self, posix_str):
		'''Return True when path is not in whitelist'''
		return self.whitelist.is_match(joliet_str.strip('/'))

	def content_add(self, rel_path):
		'''Add to file list'''
		print(rel_path, file=self.content_file)

	def dropped_add(self, rel_path):
		'''Add to file list'''
		print(rel_path, file=self.dropped_file)

	def mkiso(self):
		'''Generate one ISO image'''
		for full_path in self.root_path.glob("**/"):	# directories
			joliet_path = ExtPath.joliet(full_path, parent=self.root_path)
			if full_path.is_dir() and not full_path is self.root_path:
				self.iso.joliet_add_directory(joliet_path)
				self.content_add(joliet_path)
			else:
				self.dropped_add(joliet_path)
		for full_path in self.root_path.rglob("*"):	# files
			joliet_path = ExtPath.joliet(full_path, parent=self.root_path)
			if not full_path.is_file():
				continue
			if self.to_store(joliet_path):
				self.iso.joliet_add_file(full_path, joliet_path)
				self.content_add(joliet_path)
			else:
				self.dropped_add(joliet_path)
		self.dropped_file.close()
		self.content_file.close()
		self.iso.close()

if __name__ == '__main__':	# start here if called as application
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('-b', '--blacklist', type=Path,
		help='Blacklist (textfile with one regex per line)', metavar='FILE'
	)
	argparser.add_argument('-f', '--filename', type=str, required=True,
		help='Filename to generated (without extension)', metavar='STRING'
	)
	argparser.add_argument('-o', '--outdir', type=Path, required=True,
		help='Directory to write generated files (default: current)', metavar='DIRECTORY'
	)

	argparser.add_argument('-w', '--whitelist', type=Path,
		help='Whitelist (if set, blacklist is ignored)', metavar='FILE'
	)
	argparser.add_argument('root', nargs=1, type=Path,
		help='Source root', metavar='DIRECTORY'
	)
	args = argparser.parse_args()
	Imager(args.root[0],
		blacklist = args.blacklist,
		filename = args.filename,
		outdir = args.outdir,
		whitelist = args.whitelist
	).mkiso()
