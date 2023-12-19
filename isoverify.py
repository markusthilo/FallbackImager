#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'IsoVerify'
__author__ = 'Markus Thilo'
__version__ = '0.3.0_2023-12-18'
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
from tkinter.messagebox import showerror
from lib.greplists import GrepLists
from lib.extpath import ExtPath, FilesPercent
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.hashes import FileHashes
from lib.fsreader import FsReader

class IsoReader(PyCdlib):
	'''Use PyCdlib to get UDF from ISO'''

	def __init__(self, path):
		'''Get UDF fyle system structure, files and dirs'''
		self.path = path
		super().__init__()
		
		print('DEBUG', self.path, type(self.path))
		
		self.open(self.path)
		self.files_posix = set()
		self.dirs_posix = set()
		for root, dirs, files in self.walk(udf_path='/'):
			for name in dirs:
				self.dirs_posix.add('/'+f'{root}/{name}'.strip('/')+'/')
			for name in files:
				self.files_posix.add('/'+f'{root}/{name}'.strip('/'))
		self.close()

class CompareIsoFs:
	'''Compare ISO/UDF to file structure'''

	def __init__(self, root, image, drop=GrepLists.false, echo=print):
		'''Compare image to source file structure by Posix paths'''
		self.root_path = Path(root)
		echo(f'Getting structure of {self.root_path}')
		self.source = FsReader(self.root_path)
		self.source_posix = self.source.get_posix()
		self.image_path = Path(image)
		echo(f'Reading UDF from {self.image_path}')
		self.image = IsoReader(self.image_path)
		self.image_posix = self.image.get_udf()
		self.image.close()
		echo('Comparing file paths')
		self.delta_posix = list(set(self.source_posix)-set(self.image_posix))
		self.delta_posix.sort()
		self.dropped_posix = list()
		self.missing_posix = list()
		for posix in self.delta_posix:
			if drop(posix):
				self.dropped_posix.append(posix)
			else:
				self.missing_posix.append(posix)

class IsoVerify:
	'''Verification'''
 
	def __init__(self):
		'''Generate object'''
		pass

	def verify(self, root,
		image = None,
		drop = GrepLists.false,
		filename = None,
		outdir = None,
		echo = print,
		log = None,
	):
		'''Set paths, logs etc.'''
		self.root_path = Path(root)
		self.drop = drop
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		if image:
			self.image_path = Path(image)
		else:
			self.image_path = ExtPath.child(f'{self.filename}.iso', parent=self.outdir)
		self.echo = echo
		if log:
			self.log = log
		else:
			self.log = Logger(filename=self.filename, outdir=self.outdir, 
				head=f'isoverify.IsoVerify', echo=echo)
		self.log.info(f'Reading UDF file system from {self.image_path}', echo=True)
		iso = IsoReader(self.image_path)
		with ExtPath.child(f'{self.filename}_content.txt', parent=self.outdir).open('w') as fh:
			fh.write('\n'.join(sorted(list(iso.dirs_posix|iso.files_posix))))
		self.log.info(
			f'ISO/UDF contains {len(iso.dirs_posix)} directories and {len(iso.files_posix)} files', echo=True)
		self.log.info(f'Getting structure of {self.root_path.name}', echo=True)
		source = FsReader(self.root_path)
		if self.drop == GrepLists.false:
			delta_posix = set(source.get_posix())
		else:
			delta_posix = {posix for posix in source.get_posix() if not self.drop(posix)}
		delta_posix -= iso.dirs_posix
		delta_posix -= iso.files_posix
		msg = f'Source {self.root_path.name}:'
		msg += f' {source.file_cnt+source.dir_cnt+source.else_cnt}'
		msg += f' / {source.file_cnt} / {source.dir_cnt} / {source.else_cnt}'
		msg += ' (all/files/dirs/other)'
		self.log.info(msg, echo=True)
		if delta_posix:
			with ExtPath.child(f'{self.filename}_missing.txt', parent=self.outdir).open('w') as fh:
				fh.write('\n'.join(sorted(list(delta_posix))))
			self.log.warning(f'{len(delta_posix)} paths are missing in ISO')

class IsoVerifyCli(ArgumentParser):
	'''CLI for IsoVerify'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, prog=__app_name__.lower(), **kwargs)
		self.add_argument('-b', '--blacklist', type=ExtPath.path,
			help='Blacklist (textfile with one regex per line)', metavar='FILE'
		)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-i', '--image', type=ExtPath.path,
			help='Image path', metavar='FILE'
		)
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('-w', '--whitelist', type=ExtPath.path,
			help='Whitelist (if given, blacklist is ignored)', metavar='FILE'
		)
		self.add_argument('root', nargs=1, type=ExtPath.path,
			help='Source root', metavar='DIRECTORY'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.root = args.root[0]
		self.blacklist = args.blacklist
		self.filename = args.filename
		self.outdir = args.outdir
		self.image = args.image
		self.whitelist = args.whitelist

	def run(self, echo=print):
		'''Run the verification'''
		if self.blacklist and self.whitelist:
			raise ValueError('Unable to wirk with blacklist and whitelist at the same time')
		drop = GrepLists(blacklist=self.blacklist, whitelist=self.whitelist).get_method()
		ver = IsoVerify()
		ver.verify(self.root,
			image = self.image,
			filename = self.filename,
			outdir = self.outdir,
			drop = drop,
			echo = echo
		)
		ver.log.close()

if __name__ == '__main__':	# start here if called as application
	app = IsoVerifyCli()
	app.parse()
	app.run()
