#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-12'
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
from lib.hashes import FileHashes

class Iso(PyCdlib):
	'''Adjustments to PyCdlib'''

	def __init__(self, path, spec='udf'):
		'''Use UDF or Joliet from PyCdlib'''
		super().__init__()
		self.path = path
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
	'''Imager using PyCdlib, max. file size is 4 GB!!!'''

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
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		self.image_path = ExtPath.child(f'{self.filename}.iso', parent=self.outdir)
		self.filters = GrepLists(blacklist=blacklist, whitelist=whitelist, echo=echo)
		self.content_path = ExtPath.child(f'{filename}_content.txt', parent=outdir)
		self.dropped_path = ExtPath.child(f'{filename}_dropped.txt', parent=outdir)
		self.skipped_path = ExtPath.child(f'{filename}_skipped.txt', parent=outdir)
		self.log = Logger(filename=self.filename, outdir=self.outdir,
			head=f'pycdlibimager.PyCdlibImager, specification: {spec}')
		self.image = Iso(self.image_path, spec=spec)

	def create(self):
		'''Fill image'''
		content_fh = self.content_path.open(mode='w')
		dropped_fh = self.dropped_path.open(mode='w')
		dropped_cnt = 0
		if self.filters.are_active:
			skipped_fh = self.skipped_path.dropped_path.open(mode='w')
		for full_path in ExtPath.walk(self.root_path):
			img_path_str = '/' + str(full_path.relative_to(self.root_path)).replace('\\', '/')
			if self.filters.to_store(full_path):
				if full_path.is_dir():
					try:
						self.image.append_directory(img_path_str)
					except Exception as ex:
						print(img_path_str, file=dropped_fh)
						dropped_cnt += 1
					else:
						print(img_path_str, file=content_fh)
				elif full_path.is_file():
					try:
						self.image.append_file(full_path, img_path_str)
					except Exception as ex:
						print(img_path_str, file=dropped_fh)
						dropped_cnt += 1
					else:
						print(img_path_str, file=content_fh)
				else:
					print(img_path_str, file=dropped_fh)
					dropped_cnt += 1
			else:
				print(img_path_str, file=skipped_fh)
		self.log.info('Writing image', echo=True)
		try:
			self.image.close()
		except Exception as ex:
			self.log.error('Could not create image')
		content_fh.close()
		dropped_fh.close()
		if self.filters.are_active:
			skipped_fh.close()
		self.log.info(f'Done\n--- Image hashes ---\n{FileHashes(self.image_path)}\n', echo=True)
		if dropped_cnt == 0:
			self.log.info('Successfully created image', echo=True)
		else:
			self.log.warning(f'{dropped_cnt} items were dropped: {self.dropped_path.name}')
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
