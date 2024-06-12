#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'HashedCopy'
__author__ = 'Markus Thilo'
__version__ = '0.5.2_2024-06-12'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Safe copy with log and hashes.
'''

from argparse import ArgumentParser
from hashlib import md5, sha256
from time import time, sleep
from lib.extpath import ExtPath, Progressor
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

	def __init__(self):
		'''Create object'''
		self.available = True

	def cp(self, sources, destination, filename=None, outdir=None, echo=print, log=None):
		'''Copy multiple sources'''
		self.dst_root_path = ExtPath.path(destination)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		self.echo = echo
		self.tsv_path = ExtPath.child(f'{self.filename}_files.tsv', parent=self.outdir)
		if log:
			self.log = log
		else:
			self.log = Logger(filename=self.filename, outdir=self.outdir,
				head='hashedcopy.HashedCopy', echo=echo)
		if self.dst_root_path.exists():
			if not self.dst_root_path.is_dir():
				self.log.error('Destination is not a directory')
		else:
			self.dst_root_path.mkdir()
		files = set()
		self.echo('Reading source and creating destination directories')
		for source in sources:
			source_path = ExtPath.path(source)
			if source_path.is_dir():
				source_path.mkdir(parents=True, exist_ok=True)
				for abs_path, rel_path, tp in ExtPath.walk(source_path):
					if tp == 'Dir':
						(self.dst_root_path/source_path.name/rel_path).mkdir(parents=True, exist_ok=True)
					else:
						files.add((abs_path, self.dst_root_path/source_path.name/rel_path))
			else:
				files.add((source_path, self.dst_root_path/source_path.name))
		self.echo('Copying files')
		hashed_files = list()
		progress = Progressor(len(files), echo=self.echo)
		start_time = time()
		for src_path, dst_path in files: 
			src_hashes = CopyFile(src_path, dst_path)
			hashed_files.append((src_path, dst_path, src_hashes))
			progress.inc()
		sync()
		sleep_time = start_time + self.MIN_COPY_SEC - time()
		if sleep_time > 0:
			echo(f'Waiting...')
			sleep(sleep_time)
		error_cnt = 0
		with self.tsv_path.open('w', encoding='utf-8') as fh:
			print('Source_File\tDestination_File\tSource_MD5\tDestination_MD5\tSource_SHA256\tDestination_SHA256\tSuccess', file=fh)
			for src_path, dst_path, src_hashes in hashed_files:
				dst_hashes = FileHashes(dst_path)
				line = f'{src_path}\t{dst_path}\t{src_hashes.md5}\t{dst_hashes.md5}\t{src_hashes.sha256}\t{dst_hashes.sha256}\t'
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

	def __init__(self):
		'''Define CLI using argparser'''
		super().__init__(description=__description__.strip(), prog=__app_name__.lower())
		self.add_argument('-d', '--destination', type=ExtPath.path, required=True,
			help='Destination root (required)', metavar='DIRECTORY'
		)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write log and file list (default: current)', metavar='DIRECTORY'
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
		copy.cp(self.sources, self.destination,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo
		)
		copy.log.close()

if __name__ == '__main__':	# start here if called as application
	app = HashedCopyCli()
	app.parse()
	app.run()
