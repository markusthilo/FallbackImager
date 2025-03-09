#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'ZipImager'
__author__ = 'Markus Thilo'
__version__ = '0.6.0_2025-03-07'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Using the Python library zipfile this module generates an ZIP archive from a source file structure.
'''

from zipfile import ZipFile, ZIP_DEFLATED
from argparse import ArgumentParser
from lib.pathutils import PathUtils, Progressor
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.hashes import FileHashes

class ZipImager:
	'''Imager using ZipFile'''

	def __init__(self, echo=print):
		'''Create object'''
		self.available = True
		self.echo = echo

	def create(self, root, filename=None, outdir=None, log=None):
		'''Build zip file'''
		self.root_path = Path(root)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = PathUtils.mkdir(outdir)
		self.log = log if log else Logger(
			filename=self.filename, outdir=self.outdir, head='zipimager.ZipImager', echo=self.echo)
		self.echo('Creating Zip file')
		self.image_path = self.outdir / f'{self.filename}.zip'
		self.tsv_path = self.outdir / f'{self.filename}.tsv'
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
				if tp == 'file':
					try:
						zf.write(path, relative)
						print(f'"{relative}"\tFile\tyes', file=tsv_fh)
						file_cnt += 1
					except:
						print(f'"{relative}"\tFile\tno', file=tsv_fh)
						file_error_cnt += 1
				elif tp == 'dir':
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

	def __init__(self, echo=print):
		'''Define CLI using argparser'''
		super().__init__(description=__description__.strip(), prog=__app_name__.lower())
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('root', nargs=1, type=Path,
			help='Source root', metavar='DIRECTORY'
		)
		self.echo = echo

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.root = args.root[0]
		self.filename = args.filename
		self.outdir = args.outdir

	def run(self):
		'''Run the imager'''
		imager = ZipImager(echo=self.echo)
		imager.create(self.root,
			filename = self.filename,
			outdir = self.outdir
		)
		imager.log.close()

if __name__ == '__main__':	# start here if called as application
	app = ZipImagerCli()
	app.parse()
	app.run()
