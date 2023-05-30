#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'ZipImager'
__author__ = 'Markus Thilo'
__version__ = '0.0.3_2023-05-30'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Generate ZIP file from logical file structure
'''

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from argparse import ArgumentParser
from lib.greplists import GrepLists
from lib.extpath import ExtPath, FilesPercent
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.hashes import FileHashes
from lib.guielements import BasicFilterTab

class ZipImager:
	'''Imager using ZipFile'''

	def __init__(self, root,
		drop = GrepLists.false,
		filename = None,
		outdir = None,
		echo = print
	):
		'''Prepare to create zip file'''
		self.echo = echo
		self.root_path = Path(root)
		self.drop = drop
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		self.image_path = ExtPath.child(f'{self.filename}.zip', parent=self.outdir)
		self.files_path = ExtPath.child(f'{self.filename}_files.txt', parent=self.outdir)
		self.dropped_path = ExtPath.child(f'{self.filename}_dropped.txt', parent=self.outdir)
		self.log = Logger(filename=self.filename, outdir=self.outdir,
			head='zipimager.ZipImager', echo=echo)

	def create(self):
		'''Create zip file'''
		self.echo('Creating Zip file')
		file_cnt = 0
		dropped_cnt = 0
		progress = FilesPercent(self.root_path, echo=self.echo)
		with (
			ZipFile(self.image_path, 'w', ZIP_DEFLATED) as zf,
			self.files_path.open('w') as files_fh,
			self.dropped_path.open('w') as dropped_fh
		):
			for path in ExtPath.walk(self.root_path):
				if path.is_file():
					progress.inc()
					relative = path.relative_to(self.root_path)
					if self.drop(relative):
						print(relative, file=dropped_fh)
						dropped_cnt += 1
					else:
						zf.write(path, relative)
						print(relative, file=files_fh)
						file_cnt += 1
		self.log.info(f'Created {self.image_path.name} containing {file_cnt} file(s)', echo=True)
		if self.drop != GrepLists.false:
			self.log.info(f'Dropped {dropped_cnt} file(s) by given filter(s)')
		self.log.info(f'\n--- Image hashes ---\n{FileHashes(self.image_path)}', echo=True)

class ZipImagerCli(ArgumentParser):
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
		image = ZipImager(self.root,
			filename = self.filename,
			outdir = self.outdir,
			drop = GrepLists(
				blacklist = self.blacklist,
				whitelist = self.whitelist, 
				echo = echo
			).get_method(),
			echo = echo
		)
		image.create()
		image.log.close()

class ZipImagerGui(BasicFilterTab):
	'''Notebook page'''
	CMD = __app_name__
	DESCRIPTION = __description__
	def __init__(self, root):
		super().__init__(root)

if __name__ == '__main__':	# start here if called as application
	app = ZipImagerCli(description=__description__.strip())
	app.parse()
	app.run()
