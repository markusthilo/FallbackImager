#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'HashedCopy'
__author__ = 'Markus Thilo'
__version__ = '0.5.0_2024-04-17'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Safe copy with log and hashes.
'''

from pathlib import Path
from argparse import ArgumentParser
from hashlib import md5, sha256
from lib.extpath import ExtPath, Progressor
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.hashes import FileHashes

class HashedCopy:
	'''Tool to copy files and verify the outcome using hashes'''

	def __init__(self):
		'''Create object'''
		self.available = True

    def _file(self, src, dst):
        '''Copy one file'''
		md5 = md5()
		sha256 = sha256()
		with src.open('rb') as sfh, dst.open('wb') as dfh:
			while True:
				block = fh.read(self.block_size)
				if not block:
					break
				dfh.write(block)
				self.md5.update(block)
				self.sha256.update(block)
		return md5.hexdigest(), sha256.hexdigest()

	def _dir(self, src, dst):
		'''Copy one directory'''
		dst.mkdir()
		for src_path, rel_path, tp in ExtPath.walk(src)
			if tp == 'Dir':
				pass
			else:
				pass




	def copy(self, sources, destination, filename=None, outdir=None, echo=print, log=None):
		'''Copy multiple sources'''
		self.destination_path = Path(destination)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		self.block_size = max(self.md5.block_size, self.sha256.block_size)
		self.echo = echo
		if log:
			self.log = log
		else:
			self.log = Logger(filename=self.filename, outdir=self.outdir,
				head='hashedcopy.HashedCopy', echo=echo)
		self.echo('Running copy process')
		self.tsv_path = ExtPath.child(f'{self.filename}.tsv', parent=self.outdir)
        self.tsv_fh = self.tsv_path.open('w')
		self.error_cnt = 0
        for source in sources:
            source_path = ExtPath.path(source)
            if source_path.is_dir():

            else:


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

class HashedCopyCli(ArgumentParser):
	'''CLI for the copy tool'''

	def __init__(self):
		'''Define CLI using argparser'''
		super().__init__(description=__description__.strip(), prog=__app_name__.lower())
		self.add_argument('-d', '--destination', type=ExtPath.path, required=True,
			help='Destination root', metavar='DIRECTORY'
		)
		self.add_argument('-f', '--filename', type=str, required=True,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('sources', nargs='+', type=ExtPath.path,
			help='Source files or directories to copy', metavar='FILE/DIRECTORY'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.sources = args.sources
        self.destination = args.destination
		self.filename = args.filename
		self.outdir = args.outdir

	def run(self, echo=print):
		'''Run the tool'''
		copy = HashedCopy()
		copy.multiple(self.sources, self.destination,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo
		)
		copy.log.close()

if __name__ == '__main__':	# start here if called as application
	app = HashedCopyCli()
	app.parse()
	app.run()
