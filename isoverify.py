#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-14'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Comparing ISO with UDF to file structure'

from pathlib import Path
from pycdlib import PyCdlib
from argparse import ArgumentParser
from lib.greplists import GrepLists
from lib.extpath import ExtPath
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.hashes import FileHashes

class IsoReader(PyCdlib):
	'''Use PyCdlib to get UDF from ISO'''

	def __init__(self, path):
		'''Open ISO image'''
		self.path = path
		super().__init__()
		self.open(self.path)

	def get_udf(self):
		'''Get UDF fyle system structure, files and dirs'''
		self.udf_paths = list()
		self.udf_dirs_cnt = 0
		self.udf_files_cnt = 0
		for root, dirs, files in self.walk(udf_path='/'):
			for name in dirs:
				self.udf_paths.append('/'+f'{root}/{name}'.strip('/')+'/')
				self.udf_dirs_cnt += 1
			for name in files:
				self.udf_paths.append('/'+f'{root}/{name}'.strip('/'))
				self.udf_files_cnt += 1
		self.udf_paths.sort()
		return self.udf_paths

class FsReader:
	'''Get the mounted/local file system'''

	def __init__(self, root):
		'''Define root'''
		self.root_path = Path(root)

	def get_posix(self):
		'''Get file structure recursivly'''
		self.posix_paths = list()
		self.file_cnt = 0
		self.dir_cnt = 0
		self.else_cnt = 0
		for path, posix, tp in ExtPath.walk_posix(self.root_path):
			if tp == 'file':
				self.posix_paths.append(posix)
				self.file_cnt += 1
			elif tp == 'dir':
				self.posix_paths.append(posix)
				self.dir_cnt += 1
			else:
				self.posix_paths.append('$'+posix)
				self.else_cnt += 1
		self.posix_paths.sort()
		return self.posix_paths

class CompareIsoFs:
	'''Compare image to source'''

	def __init__(self, root, image, drop=GrepLists.false):
		'''Compare image to source file structure by Posix paths'''
		self.root_path = Path(root)
		self.source = FsReader(self.root_path)
		self.source_posix = self.source.get_posix()
		self.image_path = Path(image)
		self.image = IsoReader(self.image_path)
		self.image_posix = self.image.get_udf()
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
 
	def __init__(self, root,
		imagepath = None,
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
		if imagepath:
			self.image_path = Path(imagepath)
		else:
			self.image_path = ExtPath.child(f'{self.filename}.iso', parent=self.outdir)
		self.echo = echo
		if log:
			self.log = log
		else:
			self.log = Logger(filename=self.filename, outdir=self.outdir, 
				head=f'isoverify.IsoVerify')

	def posix_verify(self):
		'''Verify by Posix paths'''
		diff = CompareIsoFs(self.root_path, self.image_path, drop=self.drop)
		with ExtPath.child(f'{self.filename}_source.txt', parent=self.outdir).open('w') as fh:
			fh.write('\n'.join(diff.source_posix))
		with ExtPath.child(f'{self.filename}_image.txt', parent=self.outdir).open('w') as fh:
			fh.write('\n'.join(diff.image_posix))
		if self.drop != GrepLists.false:
			with ExtPath.child(f'{self.filename}_dropped.txt', parent=self.outdir).open('w') as fh:
				fh.write('\n'.join(diff.dropped_posix))
		with ExtPath.child(f'{self.filename}_missing.txt', parent=self.outdir).open('w') as fh:
			fh.write('\n'.join(diff.missing_posix))
		msg = f'Verification:\nSource {self.root_path.name}:'
		msg += f' {diff.source.file_cnt+diff.source.dir_cnt+diff.source.else_cnt}'
		msg += f' / {diff.source.file_cnt} / {diff.source.dir_cnt} / {diff.source.else_cnt}'
		msg += ' (all/files/dirs/other)\n'
		msg += f'Image {self.image_path.name}:'
		msg += f' {diff.image.udf_files_cnt+diff.image.udf_dirs_cnt} /'
		msg += f' {diff.image.udf_files_cnt} / {diff.image.udf_dirs_cnt} (all/files/dirs)\n'
		msg += f'\nImage hashes\n{FileHashes(self.image_path)}\n\n'
		if len(diff.dropped_posix) > 0:
			msg += f'{len(diff.dropped_posix)} UDF entries'
			msg += ' were ignored in verification (blacklist/whitelist)\n\n'
		if len(diff.missing_posix) == 0:
			msg += f'No missing files or directories in UDF structure of {self.image_path.name}'
			self.log.info(msg, echo=True)
		else:
			msg += f'Files might be lost, check {self.filename}_missing.txt'
			self.log.warning(msg)

class IsoVerifyCli(ArgumentParser):
	'''CLI for IsoVerify'''

	def __init__(self,description=__description__, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(**kwargs)
		self.add_argument('-b', '--blacklist', type=Path,
			help='Blacklist (textfile with one regex per line)', metavar='FILE'
		)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('-p', '--imagepath', type=Path,
			help='Image path', metavar='FILE'
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
		self.imagepath = args.imagepath
		self.whitelist = args.whitelist

	def run(self, echo=print):
		'''Run the verification'''
		drop = GrepLists(
			blacklist = self.blacklist,
			whitelist = self.whitelist, 
			echo = echo
		).get_method()
		image = IsoVerify(self.root,
			imagepath = self.imagepath,
			filename = self.filename,
			outdir = self.outdir,
			drop = drop,
			echo = echo,
		)
		image.posix_verify()
		image.log.close()

if __name__ == '__main__':	# start here if called as application
	app = IsoVerifyCli()
	app.parse()
	app.run()
