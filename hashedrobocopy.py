#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'HashedRoboCopy'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2025-02-13'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Use RoboCopy and buld hashes of the source.
'''

from os import environ
from pathlib import Path
from argparse import ArgumentParser
from lib.pathutils import PathUtils
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.hashes import HashThread
from lib.winutils import RoboCopy

class HashedRoboCopy:
	'''Tool to copy files and verify the outcome using hashes'''

	def __init__(self, echo=print):
		'''Create object'''
		self.robocopy_path = Path(environ['SYSTEMDRIVE'])/'\\Windows\\system32\\Robocopy.exe'
		if self.robocopy_path.is_file():
			self.available = True
			self.echo = echo
		else:
			self.available = False

	def copy(self, sources, destination=None, filename=None, outdir=None, hashes=['md5'], log=None):
		'''Copy multiple sources'''
		self.filename = TimeStamp.now_or(filename)
		self.outdir = PathUtils.mkdir(outdir)
		self.tsv_path = self.outdir / f'{self.filename}_files.tsv'
		self.log = log if log else Logger(
			filename=self.filename, outdir=self.outdir, head='hashedrobocopy.HashedRoboCopy', echo=self.echo)
		self.warnings = 0
		src_files = set()
		src_dirs = set()
		for source in sources:
			abs_path = Path(source).absolute()
			if abs_path.is_file():
				src_files.add(abs_path)
			elif abs_path.is_dir():
				src_dirs.add(abs_path)
			elif abs_path.exists():
				self.log.warning(f'Source {abs_path} is neither a file nor a directory')
			else:
				self.log.error(f'Source {abs_path} does not exist')
		if destination:
			self.destination = Path(destination).absolute()
			if self.destination.exists() and not self.destination.is_dir():
				self.log.error('Destination {self.destination} exits and is not a directory')
		else:
			if not hashes:
				self.log.error('No destination specified and no hashes to calculate')
			self.destination = None
		self.dirs = list(src_dirs)
		self.files = [(path, path.relative_to(path.parent), path.stat().st_size) for path in src_files]
		for dir_path in src_dirs:
			for path in dir_path.rglob('*'):
				if path.is_file():
					self.files.append((path, path.relative_to(dir_path.parent), path.stat().st_size))
				elif path.is_dir():
					self.dirs.append(path)
				else:
					self.log.warning(f'{path} is neither a file nor a directory and will be ignored')
		self.hash_algs = hashes
		if self.hash_algs:
			hash_thread = HashThread((tpl[0] for tpl in self.files), algorithms=self.hash_algs)
			hash_thread.start()
		if self.destination:
			for src_dir in self.dirs:
				self.log.info(f'Using Robocopy.exe to copy {src_dir} to {self.destination}', echo=True)
				robocopy = RoboCopy(src_dir, self.destination / src_dir.name, '/e')
				self._log_robocopy(robocopy.wait(echo=self.echo))
			for src_file in self.files:
				self.log.info(f'Using Robocopy.exe to copy {src_file} to {self.destination}', echo=True)
				robocopy = RoboCopy(src_file.parent, self.destination, src_file.name)
				self._log_robocopy(robocopy.wait(echo=self.echo))

		head = 'Source\tType/File Size'
		if self.hash_algs:
			self.hashes = hash_thread.wait(echo=self.echo)
			head += f'\t{"\t".join(self.hash_algs)}'
		with self.tsv_path.open('w', encoding='utf-8') as fh:
			print(head, file=fh)
			cols2add = '\t-' * len(self.hash_algs)
			for path in self.dirs:
				print(f'{path}\tdirectory{cols2add}', file=fh)
			for (abs_path, rel_path, size), hashes in zip(self.files, self.hashes):
				line = f'{path}\t{size}'
				for hash in hashes:
					line += f'\t{hash}'
				print(line, file=fh)
		if self.destination:
			for path, size in files2hash.items():
				dst_path = self.destination / path.relative_to(src_dir)
				print(dst_path)
				dst_size = dst_path.stat().st_size
				if dst_size != size:
					self.log.warning(f'File size of {dst_path} differs from source {path} ({dst_size} / {size})')
			self.log.info(f'Done, paths are listed in {self.tsv_path}', echo=True)
		if self.warnings:
			self.log.warning(f'{self.warnings} warning(s) were thrown, check {self.log.path}')
		else:
			self.log.info('Finished without errors', echo=True)

	def _log_robocopy(self, returncode):
		'''Log robocopy returncode'''
		if returncode > 3:
			self.log.warning(f'Robocopy.exe gave returncode {returncode}')
			self.warnings += 1
		else:
			self.log.info(f'Robocopy.exe finished with returncode {returncode}', echo=True)

class HashedRoboCopyCli(ArgumentParser):
	'''CLI for the copy tool'''

	def __init__(self, echo=print):
		'''Define CLI using argparser'''
		super().__init__(description=__description__.strip(), prog=__app_name__.lower())
		self.add_argument('-a', '--algorithms', type=str,
			help='Algorithms to hash seperated by colon (e.g. "md5,sha256", no hashing: "none", default: "md5")', metavar='STRING'
		)
		self.add_argument('-d', '--destination', type=Path,
			help='Destination root (hash only if not given)', metavar='DIRECTORY'
		)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generate for log and file list (without extension)', metavar='STRING'
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
		if args.algorithms:
			if args.algorithms.lower() == 'none':
				self.algorithms = None
			else:
				self.algorithms = [alg.strip() for alg in args.algorithms.split(',')]
		else:
			self.algorithms = ['md5']
		self.destination = args.destination
		self.filename = args.filename
		self.outdir = args.outdir

	def run(self):
		'''Run the tool'''
		hrc = HashedRoboCopy(echo=self.echo)
		hrc.copy(self.sources,
			destination = self.destination,
			filename = self.filename,
			outdir = self.outdir,
			hashes = self.algorithms
		)
		hrc.log.close()

if __name__ == '__main__':	# start here if called as application
	app = HashedRoboCopyCli()
	app.parse()
	app.run()
