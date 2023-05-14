#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-14'
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
from isoverify import IsoVerify

class Iso(PyCdlib):
	'''Adjustments to PyCdlib'''

	def __init__(self, path):
		'''Use UDF or Joliet from PyCdlib'''
		super().__init__()
		self.path = path
		self.new(udf='2.60')
		self._facade = self.get_udf_facade()

	def udf_add_directory(self, posix):
		'''Add directory to image'''
		self._facade.add_directory(udf_path=posix)

	def udf_add_file(self, path, posix):
		'''Add file to image'''
		self._facade.add_file(path, udf_path=posix)

	def close(self):
		'''Write and close'''
		super().write(self.path)
		super().close()

class PyCdlibImager:
	'''Imager using PyCdlib, max. file size is 4 GB!!!'''

	def __init__(self, root,
		drop = GrepLists.false,
		filename = None,
		outdir = None,
		echo = print
	):
		'''Prepare to write image file'''
		self.echo = echo
		self.root_path = Path(root)
		self.drop = drop
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		self.image_path = ExtPath.child(f'{self.filename}.iso', parent=self.outdir)
		self.log = Logger(filename=self.filename, outdir=self.outdir,
			head='pycdlibimager.PyCdlibImager')
		self.image = Iso(self.image_path)

	def create_iso(self):
		'''Fill image'''
		self.dropped_cnt = 0
		self.unidentified_posix = list()
		for path, posix, tp in ExtPath.walk_posix(self.root_path):
			if self.drop(posix):
				self.dropped_cnt += 1
			elif tp == 'file':
				self.image.udf_add_file(path, posix)
			elif tp == 'dir':
				self.image.udf_add_directory(posix)
			else:
				self.unidentified_posix.append('$'+posix)
		self.log.info(f'Writing image {self.image_path.name}', echo=True)
		try:
			self.image.close()
		except Exception:
			self.log.error('Could not create image')
		else:
			msg = f'Image {self.image_path} was created'
		
		
			self.log.info(msg, echo=True)

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

	def run(self, echo=print):
		'''Run the imager'''
		drop = GrepLists(
			blacklist = self.blacklist,
			whitelist = self.whitelist, 
			echo = echo
		).get_method()
		image = PyCdlibImager(self.root,
			filename = self.filename,
			outdir = self.outdir,
			drop = drop,
			echo = echo
		)
		image.create_iso()
		IsoVerify(self.root,
			imagepath = image.image_path,
			drop = drop,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo,
			log = image.log
		).posix_verify()
		image.log.close()

if __name__ == '__main__':	# start here if called as application
	app = PyCdlibCli(description=__description__)
	app.parse()
	app.run()
