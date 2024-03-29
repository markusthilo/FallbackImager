#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'MkIsoImager'
__author__ = 'Markus Thilo'
__version__ = '0.3.0_2023-12-25'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This tool generates an ISO file (UDF file system) using mkisofs. It will log files that cannot be handled properly.
'''

from sys import executable as __executable__
from os import name as __os_name__
from pathlib import Path
from argparse import ArgumentParser
from lib.openproc import OpenProc
from lib.extpath import ExtPath
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.hashes import FileHashes
from isoverify import IsoVerify

__executable__ = Path(__executable__)
__file__ = Path(__file__)
if __executable__.stem.lower() == __file__.stem.lower():
	__parent_path__ = __executable__.parent
else:
	__parent_path__ = __file__.parent

class MkIsoImager:
	'''MAKEISOFS via subprocess (mkisofs -udf -o $image -V %label $source)'''

	def __init__(self):
		'''Generate object to use mkisofs'''
		if __os_name__ == 'nt':
			for self.mkisofs_path in (
				__parent_path__/'bin/mkisofs.exe',
				__parent_path__/'mkisofs.exe'
			):
				if self.mkisofs_path.is_file():
					break
		else:
			for self.mkisofs_path in (
				Path('/usr/bin/mkisofs'),
				Path('/usr/local/bin/mkisofs'),
				__parent_path__/'bin/mkisofs',
				__parent_path__/'mkisofs'
			):
				if self.mkisofs_path.is_file():
					break
		if not self.mkisofs_path.is_file():
			if __os_name__ == 'nt':
				raise RuntimeError('Uanbale to locate mkisofs.exe')
			raise RuntimeError('Uanbale to locate mkisofs')

	def create(self, root,
			filename = None,
			outdir = None,
			log = None,
			echo = print
		):
		'''Create image'''
		self.root_path = Path(root)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		self.image_path = ExtPath.child(f'{self.filename}.iso', parent=self.outdir)
		if log:
			self.log = log
		else:
			self.log = Logger(self.filename, outdir=self.outdir, head='mkisoimager.MkIsoImager', echo=echo)
		cmd = [f'{self.mkisofs_path}',
			'-udf',
			'-o', f'{self.image_path}',
			f'{self.root_path}'
		]
		self.log.info(f'> {" ".join(cmd)}', echo=True)
		proc = OpenProc(cmd)
		proc.echo_output(self.log)
		if not self.image_path.is_file():
			self.log.error(f'Could not create image file {self.image_path}')
		self.log.info(f'\n--- Image hashes ---\n{FileHashes(self.image_path)}', echo=True)

class MkIsoImagerCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, prog=__app_name__.lower(), **kwargs)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('root', nargs=1, type=ExtPath.path,
			help='Source', metavar='DIRECTORY'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.root = args.root[0]
		self.filename = args.filename
		self.outdir = args.outdir

	def run(self, echo=print):
		'''Run the imager'''
		imager = MkIsoImager()
		imager.create(self.root,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo
		)
		ver = IsoVerify()
		ver.read_udf(imager.image_path,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo,
			log = imager.log
		)
		ver.compare(self.root)
		imager.log.close()

if __name__ == '__main__':	# start here if called as application
	app = MkIsoImagerCli()
	app.parse()
	app.run()
