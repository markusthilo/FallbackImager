#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'IsoVerify'
__author__ = 'Markus Thilo'
__version__ = '0.3.0_2023-12-25'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This module is used by ISO generating modules to compare the UDF structure to the source file structure. Therefor it uses the pycdlib library. It can also be used to compare an existing image to a local file structure.

It is possible to skip paths using a whitelist or a blacklist. The patterns have to be given as regular expressions (Python/re syntax), one per line in a text file. Paths are handles in the POSIX format (no Windowish backslashes). When a local path matches to one line in the whitelist, the verification of this path is skipped. When a blicklist is given, the comparison is skipped if there is no match in the list of regular expressions. You can only use whitelist or blacklist at a time.
'''

from pathlib import Path
from pycdlib import PyCdlib
from argparse import ArgumentParser
from lib.extpath import ExtPath, FilesPercent
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.hashes import FileHashes
from lib.fsreader import FsReader

class IsoVerify:
	'''Verify UDF ISO image file'''

	def read_udf(self, iso, outdir=None, filename=None, echo=print, log=None):
		'''Read iso image'''
		self.iso_path = Path(iso)
		self.outdir = ExtPath.mkdir(outdir)
		if filename:
			self.filename = filename
		else:
			self.filename = TimeStamp.now_or(filename)
		self.echo = echo
		if log:
			self.log = log
		else:
			self.log = Logger(filename=self.filename, outdir=self.outdir, 
				head=f'isoverify.IsoVerify', echo=echo)
		self.log.info(f'Reading UDF file system from {self.iso_path}', echo=True)
		self.iso = PyCdlib()
		self.iso.open(self.iso_path)
		self.files_posix = ['/'+f'{root}/{file}'.strip('/')
			for root, dirs, files in self.iso.walk(udf_path='/')
			for file in files
		]
		self.iso.close()
		self.log.info(
			f'ISO/UDF contains {len(self.files_posix)} files', echo=True)
		with ExtPath.child(f'{self.filename}_files.txt', parent=self.outdir).open('w') as fh:
			fh.write('\n'.join(self.files_posix))

	def compare(self, root):
		'''Compare to local file system structure'''
		self.root_path = Path(root)
		self.log.info(f'Getting structure of {self.root_path.name}', echo=True)
		missing = [posix for path, posix, tp in ExtPath.walk_posix(root)
			if tp == 'file' and posix not in self.files_posix
		]
		if missing:
			with ExtPath.child(f'{self.filename}_missing.txt', parent=self.outdir).open('w') as fh:
				fh.write('\n'.join(missing))
			self.log.warning(f'{len(missing)} missing file(s) in ISO/UDF')

class IsoVerifyCli(ArgumentParser):
	'''CLI for IsoVerify'''

	def __init__(self):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, prog=__app_name__.lower())
		self.add_argument('-d', '--dir', type=ExtPath.path,
			help='Root directory to compare', metavar='DIRECTORY'
		)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('iso', nargs=1, type=ExtPath.path,
			help='ISO image file', metavar='FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.iso = args.iso[0]
		self.dir = args.dir
		self.filename = args.filename
		self.outdir = args.outdir

	def run(self, echo=print):
		'''Run the verification'''
		ver = IsoVerify()
		ver.read_udf(self.iso,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo
		)
		if self.dir:
			ver.compare(self.dir)
		ver.log.close()

if __name__ == '__main__':	# start here if called as application
	app = IsoVerifyCli()
	app.parse()
	app.run()
