#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'ZipImager'
__author__ = 'Markus Thilo'
__version__ = '0.4.1_2024-04-15'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Using the Python library zipfile this module generates an ZIP archive from a source file structure.
'''

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from argparse import ArgumentParser
from lib.extpath import ExtPath, Progressor
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.hashes import FileHashes

class ZipImager:
	'''Imager using ZipFile'''

	def __init__(self):
		'''Create object'''
		self.available = True

	def create(self, root, filename=None, outdir=None, echo=print, log=None):
		'''Build zip file'''
		self.root_path = Path(root)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		self.echo = echo
		if log:
			self.log = log
		else:
			self.log = Logger(filename=self.filename, outdir=self.outdir,
				head='zipimager.ZipImager', echo=echo)
		self.echo('Creating Zip file')
		self.image_path = ExtPath.child(f'{self.filename}.zip', parent=self.outdir)
		self.tsv_path = ExtPath.child(f'{self.filename}.tsv', parent=self.outdir)
		file_cnt = 0
		dir_cnt = 0
		other_cnt = 0
		file_error_cnt = 0
		dir_error_cnt = 0
		progress = Progressor(self.root_path, echo=self.echo)
		with (
			ZipFile(self.image_path, 'w', ZIP_DEFLATED) as zf,
			self.tsv_path.open('w', encoding='utf-8') as tsv_fh
		):
			print('Path\tType\tCopied', file=tsv_fh)
			for path, relative, tp in ExtPath.walk(self.root_path):
				if tp == 'File':
					try:
						zf.write(path, relative)
						print(f'"{relative}"\tFile\tyes', file=tsv_fh)
						file_cnt += 1
					except:
						print(f'"{relative}"\tFile\tno', file=tsv_fh)
						file_error_cnt += 1
				elif tp == 'Dir':
					try:
						zf.mkdir(f'{relative}')
						print(f'"{relative}"\tDir\tyes', file=tsv_fh)
						dir_cnt += 1
					except:
						print(f'"{relative}"\tDir\tno', file=tsv_fh)
						dir_error_cnt += 1
				else:
					print(f'"{relative}"\tOther\tno', file=tsv_fh)
					other_cnt += 1
				progress.inc()
		msg = f'Created {self.image_path.name} '
		msg += f'(Files: {file_cnt} / Directories: {dir_cnt} / Other: {other_cnt})'
		self.log.info(msg, echo=True)
		msg = ''
		if file_error_cnt > 0:
			msg += f'{file_error_cnt} missing file(s)'
		if dir_error_cnt > 0:
			if msg:
				msg += ' and '
			msg += f'{dir_error_cnt} missing dir(s)'
		if msg:
			self.log.warning(msg)
		self.log.info('Calculating hashes', echo=True)
		self.log.info(f'\n--- Image hashes ---\n{FileHashes(self.image_path)}', echo=True)

class ZipImagerCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self):
		'''Define CLI using argparser'''
		super().__init__(description=__description__.strip(), prog=__app_name__.lower())
		self.add_argument('-f', '--filename', type=str, required=True,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('root', nargs=1, type=ExtPath.path,
			help='Source root', metavar='DIRECTORY'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.root = args.root[0]
		self.filename = args.filename
		self.outdir = args.outdir

	def run(self, echo=print):
		'''Run the imager'''
		imager = ZipImager()
		imager.create(self.root,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo
		)
		imager.log.close()

if __name__ == '__main__':	# start here if called as application
	app = ZipImagerCli()
	app.parse()
	app.run()
