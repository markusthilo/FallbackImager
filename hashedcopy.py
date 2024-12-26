#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'HashedCopy'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2024-12-26'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Safe copy with log and hashes.
'''

from pathlib import Path
from argparse import ArgumentParser
from hashlib import md5, sha256
from time import time, sleep
from lib.pathutils import PathUtils, Progressor
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.hashes import FileHashes, CopyFile
try:
	from os import sync as os_sync
	def sync(): os_sync()
except ImportError:
	def sync(): pass

class HashedCopy:
	'''Tool to copy files and verify the outcome using hashes'''

	MIN_COPY_SEC = 10

	def __init__(self, echo=print):
		'''Create object'''
		self.available = True
		self.echo = echo

	def cp(self, sources, destination, filename=None, outdir=None, log=None):
		'''Copy multiple sources'''
		self.dst_root_path = Path(destination)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = PathUtils.mkdir(outdir)
		self.tsv_path = self.outdir / f'{self.filename}_files.tsv'
		self.log = log if log else Logger(
			filename=self.filename, outdir=self.outdir, head='hashedcopy.HashedCopy', echo=self.echo)
		if self.dst_root_path.exists():
			if not self.dst_root_path.is_dir():
				self.log.error('Destination is not a directory')
		else:
			self.dst_root_path.mkdir()
		source_paths = sorted(list({Path(source) for source in sources}))
		files2cp = list()
		error_cnt = 0
		with self.tsv_path.open('w', encoding='utf-8') as fh:
			print('Source\tDestination\tType\tSource_MD5\tDestination_MD5\tSource_SHA256\tDestination_SHA256\tSuccess', file=fh)
			self.echo('Creating directories')
			for source_path in source_paths:
				root_dst_path = self.dst_root_path.joinpath(source_path)
				if source_path.is_dir():
					root_dst_path.mkdir(parents=True, exist_ok=True)
					print(f'{source_path}\t{root_dst_path}\tdir\t-\t-\t-\t-\tyes', file=fh)
					for abs_path, rel_path, tp in PathUtils.walk(source_path):
						dst_path = self.dst_root_path.joinpath(source_path.name, rel_path)
						if tp == 'dir':
							dst_path.mkdir(parents=True, exist_ok=True)
							print(f'{abs_path}\t{dst_path}\tdir\t-\t-\t-\t-\tyes', file=fh)
						elif tp == 'file':
							files2cp.append((abs_path, dst_path))
						else:
							print(f'{abs_path}\t{dst_path}\tother\t-\t-\t-\t-\tno', file=fh)
							error_cnt += 1
				elif source_path.is_file():
					files2cp.append((source_path, root_dst_path))
				else:
					print(f'{source_path}\t{root_dst_path}\tother\t-\t-\t-\t-\tno', file=fh)
					error_cnt += 1
			self.echo('Copying files')
			hashed_files = list()
			progress = Progressor(len(files2cp), echo=self.echo, item='file')
			for src_path, dst_path in files2cp:
				src_hashes = CopyFile(src_path, dst_path)
				hashed_files.append((src_path, dst_path, src_hashes))
				progress.inc()
			sync()
			for src_path, dst_path, src_hashes in hashed_files:
				dst_hashes = FileHashes(dst_path)
				line = f'{src_path}\t{dst_path}\tfile\t{src_hashes.md5}\t{dst_hashes.md5}\t{src_hashes.sha256}\t{dst_hashes.sha256}\t'
				if src_hashes.md5 == dst_hashes.md5 and src_hashes.sha256 == dst_hashes.sha256:
					line += 'yes'
				else:
					line += 'no'
					error_cnt += 1
				print(line, file=fh)
		self.log.info(f'Copied {len(hashed_files)-error_cnt} file(s), check {self.tsv_path}', echo=True)
		if error_cnt > 0:
			self.log.error(f'{error_cnt} missing file(s)')


class HashedCopyCli(ArgumentParser):
	'''CLI for the copy tool'''

	def __init__(self, echo=print):
		'''Define CLI using argparser'''
		super().__init__(description=__description__.strip(), prog=__app_name__.lower())
		self.add_argument('-d', '--destination', type=Path, required=True,
			help='Destination root (required)', metavar='DIRECTORY'
		)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write log and file list (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('sources', nargs='+', type=Path,
			help='Source files or directories to copy', metavar='FILE/DIRECTORY'
		)
		self.echo = echo

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.sources = args.sources
		self.destination = args.destination
		self.filename = args.filename
		self.outdir = args.outdir

	def run(self):
		'''Run the tool'''
		copy = HashedCopy(echo=self.echo)
		copy.cp(self.sources, self.destination,
			filename = self.filename,
			outdir = self.outdir
		)
		copy.log.close()

if __name__ == '__main__':	# start here if called as application
	app = HashedCopyCli()
	app.parse()
	app.run()
