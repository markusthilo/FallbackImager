#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-11'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Generate ISO from logical file structure'

from pathlib import Path
from pycdlib import PyCdlib
from argparse import ArgumentParser
from lib.greplists import GrepLists
from lib.extpath import ExtPath
from lib.timestamp import TimeStamp
from lib.logger import Logger

class Iso(PyCdlib):
	'''ISO Image'''

	def __init__(self, path, spec='udf'):
		'''Use UDF or Joliet from PyCdlib'''
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
			raise NotImplementedError(spec)

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
		super().write(self.path)
		super().close()

class PyCdlibImager:
	'''Image Generator for files / logical content'''

	def __init__(self, root,
		filename = None,
		outdir = None,
		blacklist = None,
		whitelist = None,
		spec = 'udf',
		echo = print
	):
		'''Prepare to write image file'''
		self.echo = echo
		self.root_path = Path(root)
		self.image_path = ExtPath.child(f'{filename}.iso', parent=outdir)
		self.log = Logger(filename=filename, outdir=outdir)
		self.grep = GrepLists(blacklist=blacklist, whitelist=whitelist, echo=echo)
		self.image = Iso(self.image_path, spec=spec)
		self.echo(f'PyCdlib will write to image file {self.image_path} with specification >{spec}<')

	def create(self):
		'''Fill image'''
		for path in ExtPath.walk(self.root_path):
			print(path)

		'''
				#store_path = ExtPath.to_str(full_path, parent=self.root_path)
		self.echo(full_path)
		if full_path is self.root_path:
			print(store_path, file=self.directories_file)
			continue
		try:
			self.image.append_directory(store_path)
			print(store_path, file=self.directories_file)
		except Exception as ex:
			print(store_path, file=self.dropped_file)
			print(f'{TimeStamp.now()}\t{store_path}\t{ex}', file=self.errors_file)
		for full_path in self.root_path.rglob('*'):	# files
			if full_path.is_file():
				store_path = ExtPath.to_str(full_path, parent=self.root_path)
				self.echo(full_path)
				if self.grep.to_store(store_path):
					try:
						self.image.append_file(full_path, store_path)
						print(store_path, file=self.files_file)
					except Exception as ex:
						print(store_path, file=self.dropped_file)
						print(f'{TimeStamp.now()}\t{store_path}\t{ex}', file=self.errors_file)
				else:
					print(store_path, file=self.excluded_file)

		self.image.close()
		
		'''
		self.log.close()

class PyCdlibCli(ArgumentParser):
	'''CLI for the imager'''

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

	def run(self, echo=print):
		'''Run the imager'''
		image = PyCdlibImager(self.root,
			blacklist = self.blacklist,
			filename = self.filename,
			outdir = self.outdir,
			whitelist = self.whitelist,
			spec = self.spec,
			echo = echo,
		)
		image.create()

if __name__ == '__main__':	# start here if called as application
	app = PyCdlibCli(description=__description__)
	app.parse()
	app.run()
