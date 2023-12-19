#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'ZipImager'
__author__ = 'Markus Thilo'
__version__ = '0.3.0_2023-12-18'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Using the Python library zipfile this module generates an ZIP archive from a source file structure. By giving a file list (CSV/TSV) it is possible to select what to include. In addition you can use a whitelist (excludes files) or a blacklist (selects files).
'''

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from argparse import ArgumentParser
from lib.greplists import GrepLists
from lib.extpath import ExtPath, FilesPercent
from lib.tsvreader import TsvReader
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.hashes import FileHashes

class ZipImager:
	'''Imager using ZipFile'''

	def __init__(self):
		'''Create object'''
		pass

	def _write_flat(self, path, relative, zf, files_fh, dropped_fh, file_cnt, dropped_cnt):
		'''Write ZIP with flattened structure'''
		fname = ExtPath.flatten(relative)
		try:
			zf.write(path, fname)
			print(f'{relative}\t{fname}', file=files_fh)
			return file_cnt + 1, dropped_cnt
		except:
			print(f'{relative}\tdropped_by_zip', file=dropped_fh)
			return file_cnt, dropped_cnt + 1

	def _write_structure(self, path, relative, zf, files_fh, dropped_fh, file_cnt, dropped_cnt):
		'''Write ZIP reproducing the relative structure'''
		try:
			zf.write(path, relative)
			print(relative, file=files_fh)
			return file_cnt + 1, dropped_cnt
		except:
			print(f'{relative}\tdropped_by_zip', file=dropped_fh)
			return file_cnt, dropped_cnt + 1

	def create(self, root,
		flat = False,
		filelist = None,
		column = 1,
		nohead = False,
		drop = GrepLists.false,
		filename = None,
		outdir = None,
		echo = print,
		log = None
	):
		'''Create zip file'''
		self.echo = echo
		self.root_path = Path(root)
		self.flat = flat
		self.filelist = filelist
		self.column = column
		self.nohead = nohead
		self.drop = drop
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		self.image_path = ExtPath.child(f'{self.filename}.zip', parent=self.outdir)
		self.files_path = ExtPath.child(f'{self.filename}_files.txt', parent=self.outdir)
		self.dropped_path = ExtPath.child(f'{self.filename}_dropped.txt', parent=self.outdir)
		if log:
			self.log = log
		else:
			self.log = Logger(filename=self.filename, outdir=self.outdir,
				head='zipimager.ZipImager', echo=echo)
		self.echo('Creating Zip file')
		file_cnt = 0
		dropped_cnt = 0
		if self.filelist:
			tsv = TsvReader(Path(self.filelist), column=self.column, nohead=self.nohead)
			if tsv.column < 0:
				self.log.error('Column out of range/undetected')
			filelist = {ExtPath.to_posix(path) for path, line in tsv.read_lines() if path}
		progress = FilesPercent(self.root_path, echo=self.echo)
		with (
			ZipFile(self.image_path, 'w', ZIP_DEFLATED) as zf,
			self.files_path.open('w') as files_fh,
			self.dropped_path.open('w') as dropped_fh
		):
			if self.flat:
				write = self._write_flat
			else:
				write = self._write_structure
			for path, relative in ExtPath.walk_files(self.root_path):
				if self.filelist:
					posix = ExtPath.norm_to_posix(relative)
					if not posix in filelist:
						continue
					filelist.remove(posix)
				progress.inc()
				if self.drop(relative):
					print(f'{relative}\tdropped_by_regex', file=dropped_fh)
					dropped_cnt += 1
				else:
					file_cnt, dropped_cnt = write(path, relative, zf, files_fh, dropped_fh, file_cnt, dropped_cnt)
		self.log.info(f'Created {self.image_path.name} containing {file_cnt} file(s)', echo=True)
		if self.drop != GrepLists.false:
			self.log.info(f'Dropped {dropped_cnt} file(s) by given filter(s)')
		if self.filelist and len(filelist) > 0:
			path = ExtPath.child(f'{self.filename}_missing.txt', parent=self.outdir)
			with path.open('w') as fh:
				for posix in filelist:
					print(posix, file=fh)
			self.log.warning(f'{len(filelist)} file(s) from given list is/are missing, check {path.name}')
		self.log.info(f'\n--- Image hashes ---\n{FileHashes(self.image_path)}', echo=True)

class ZipImagerCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self):
		'''Define CLI using argparser'''
		super().__init__(description=__description__.strip(), prog=__app_name__.lower())
		self.add_argument('-b', '--blacklist', type=ExtPath.path,
			help='Blacklist (textfile with one regex per line)', metavar='FILE'
		)
		self.add_argument('-c', '--column', type=str,
			help='Column with path for -l/--filelist', metavar='INTEGER|STRING'
		)
		self.add_argument('-f', '--filename', type=str, required=True,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-n', '--nohead', default=False, action='store_true',
			help='TSV file has no head line with names of columns (e.g. "Full path" etc.)'
		)
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('-l', '--filelist', type=ExtPath.path,
			help='Copy only the files in the list', metavar='FILE'
		)
		self.add_argument('-t', '--flat', default=False, action='store_true',
			help='Generate a flat structure without folders'
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
		self.column = args.column
		self.filename = args.filename
		self.filelist = args.filelist
		self.flat = args.flat
		self.nohead = args.nohead
		self.outdir = args.outdir
		self.whitelist = args.whitelist

	def run(self, echo=print):
		'''Run the imager'''
		imager = ZipImager()
		imager.create(self.root,
			filename = self.filename,
			outdir = self.outdir,
			filelist = self.filelist,
			column = self.column,
			nohead = self.nohead,
			flat = self.flat,
			drop = GrepLists(blacklist=self.blacklist, whitelist=self.whitelist).get_method(),
			echo = echo
		)
		imager.log.close()

if __name__ == '__main__':	# start here if called as application
	app = ZipImagerCli()
	app.parse()
	app.run()
