#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-05'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Generate ISO from a partition of an evidence item'

from pathlib import Path
from re import compile as regcompile
from pycdlib import PyCdlib
from argparse import ArgumentParser, FileType
from lib.extpath import ExtPath

class RegList:
	'''List of regular expressions to exclude paths'''

	def __init__(self, path):
		'''Read file and build list with '''
		if isinstance(path, Path):
			with path.open() as textfile:
				self.regs = [regcompile(line.strip()) for line in textfile]
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
	'''ISO Image'''

	def __init__(self, filename, parent=None, spec='udf'):
		'''Create image'''
		self.image_path = ExtPath.fullpath(f'{filename}.iso', parent)
		super().__init__()
		if spec.lower() == 'udf':
			self.new(udf='2.60')
			self._facade = self.get_udf_facade()
			self.append_directory = self._udf_add_directory
			self.append_file = self._udf_add_file
		elif spec.lower() == 'joliet':
			self.new(joliet=3)
			self._facade = self.get_joliet_facade()
			self.append_directory = self._joliet_add_directory
			self.append_file = self._joliet_add_file
		else:
			raise NotImplementedError(f'unknown specification {spec}')

	def _udf_add_directory(self, rel_path):
		'''Add directory to image'''
		self._facade.add_directory(udf_path=f'/{rel_path}')

	def _udf_add_file(self, full_path, rel_path):
		'''Add file to image'''
		self._facade.add_file(full_path, udf_path=f'/{rel_path}')

	def _joliet_add_directory(self, rel_path):
		'''Add directory to image'''
		self._facade.add_directory(joliet_path=f'/{rel_path}')

	def _joliet_add_file(self, full_path, rel_path):
		'''Add file to image'''
		self._facade.add_file(full_path, joliet_path=f'/{rel_path}')

	def close(self):
		'''Write and close'''
		super().write(self.image_path)
		super().close()

class FileImage:
	'''Image Generator for files / logical content'''

	def __init__(self, root,
		imager = ISO,
		spec = 'udf',
		filename = None,
		outdir = None,
		blacklist = None,
		whitelist = None,
		echo = print
	):
		'''Definitions'''
		self.echo = echo
		self.root_path = Path(root)
		if outdir:
			self.dir_path = Path(outdir)
			self.dir_path.mkdir(exist_ok=True)
		else:
			self.dir_path = Path.cwd()
		self.content_file = ExtPath.open_write(f'{filename}_content.txt', parent=self.dir_path)
		self.dropped_file = ExtPath.open_write(f'{filename}_dropped.txt', parent=self.dir_path)
		self.image = imager(filename, parent=self.dir_path, spec=spec)
		self.echo(f'Image file {self.image.image_path} with specification >{spec}<')
		self.blacklist = RegList(blacklist)
		self.whitelist = RegList(whitelist)
		if self.whitelist.regs:
			self.to_store = self._is_in_whitelist
			self.echo(f'Using whitelist {whitelist}')
		else:
			self.to_store = self._not_in_blacklist
			if self.blacklist.regs:
				self.echo(f'Using blacklist {blacklist}')

	def _not_in_blacklist(self, posix_str):
		'''Return True when path is blacklisted'''
		return not self.blacklist.is_match(posix_str.strip('/'))

	def _is_in_whitelist(self, posix_str):
		'''Return True when path is not in whitelist'''
		return self.whitelist.is_match(posix_str.strip('/'))

	def _log_content(self, rel_path):
		'''Add to file list'''
		print(rel_path, file=self.content_file)

	def _log_dropped(self, rel_path):
		'''Add to file list'''
		print(rel_path, file=self.dropped_file)

	def fill(self):
		'''Fill image'''
		for full_path in self.root_path.glob("**/"):	# directories
			store_path = ExtPath.path_to_str(full_path, parent=self.root_path)
			if full_path.is_dir() and not full_path is self.root_path:
				self.echo(full_path)
				self.image.append_directory(store_path)
				self._log_content(store_path)
			else:
				self._log_dropped(store_path)
		for full_path in self.root_path.rglob("*"):	# files
			store_path = ExtPath.path_to_str(full_path, parent=self.root_path)
			if not full_path.is_file():
				continue
			self.echo(full_path)
			if self.to_store(store_path):
				self.image.append_file(full_path, store_path)
				self._log_content(store_path)
			else:
				self._log_dropped(store_path)

	def close(self):
		'''Close image file and logs'''
		self.dropped_file.close()
		self.content_file.close()
		self.image.close()

class CLI(ArgumentParser):
	'''CLI for the imager'''

	@staticmethod
	def no_echo(*args, **kwargs):
		'''Dummy for silent mode'''
		pass

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(**kwargs)
		self.add_argument('-b', '--blacklist', type=Path,
			help='Blacklist (textfile with one regex per line)', metavar='FILE'
		)
		self.add_argument('-f', '--filename', type=str, required=True,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-j', '--joliet', default=False, action='store_true',
			help='Use Joliet file system instead of UDF'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('-v', '--verbose', default=False, action='store_true',
			help='Print infos to stdout'
		)
		self.add_argument('-w', '--whitelist', type=Path,
			help='Whitelist (if given, blacklist is ignored)', metavar='FILE'
		)
		self.add_argument('root', nargs=1, type=Path,
			help='Source root', metavar='DIRECTORY'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.root = args.root[0]
		self.blacklist = args.blacklist
		self.filename = args.filename
		self.outdir = args.outdir
		self.whitelist = args.whitelist
		if args.joliet:
			self.spec = 'joliet'
		else:
			self.spec = 'udf'
		self.verbose = args.verbose

	def run(self, echo=print):
		'''Run the imager'''
		if not self.verbose:
			echo = self.no_echo
		image = FileImage(self.root,
			blacklist = self.blacklist,
			filename = self.filename,
			outdir = self.outdir,
			whitelist = self.whitelist,
			spec = self.spec,
			echo = echo,
		)
		image.fill()
		image.close()

if __name__ == '__main__':	# start here if called as application
	app = CLI(description=__description__)
	app.parse()
	app.run()
