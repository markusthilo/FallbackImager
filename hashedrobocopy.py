#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'HashedRoboCopy'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2025-02-05'
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
from lib.winutils import RoboWalk, RoboCopy

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

	def copy(self, sources, destination, filename=None, outdir=None, hashes=['md5'], log=None):
		'''Copy multiple sources'''
		self.filename = TimeStamp.now_or(filename)
		self.outdir = PathUtils.mkdir(outdir)
		self.tsv_path = self.outdir / f'{self.filename}_files.tsv'
		self.log = log if log else Logger(
			filename=self.filename, outdir=self.outdir, head='hashedrobocopy.HashedRoboCopy', echo=self.echo)
		self.errors = 0
		self.src_files = set()
		self.src_dirs = set()
		for source in sources:
			if source.is_file():
				self.src_files.add(Path(source).resolve())
			elif source.is_dir():
				self.src_dirs.add(Path(source).resolve())
			elif source.exists():
				self.log.error(f'Source {source} is neither a file nor a directory')
			else:
				self.log.error(f'Source {source} does not exist')
		self.destination = Path(destination).resolve()
		if self.destination.exists() and not self.destination.is_dir():
			self.log.error('Destination {self.destination} exits and is not a directory')
		files2hash = self.src_files.copy()
		dirs2log = self.src_dirs.copy()
		quantity = len(self.src_files)
		for src_dir in self.src_dirs:
			robowalk = RoboWalk(src_dir)
			files2hash.update(robowalk.files)
			dirs2log.update(robowalk.dirs)
			quantity += len(robowalk.files)
		self.hash_algs = hashes
		if self.hash_algs:
			hash_thread = HashThread(files2hash, algorithms=self.hash_algs)
			hash_thread.start()
		start = 1
		for src_file in self.src_files:
			self.log.info(f'Using Robocopy.exe to copy {src_file} to {self.destination}', echo=True)
			robocopy = RoboCopy(src_file.parent, self.destination, src_file.name, '/fp', '/ns', '/ndl')
			self._log_robocopy(robocopy.wait(echo=self.echo, quantity=quantity, start=start))
			start = robocopy.counter + 1
		for src_dir in self.src_dirs:
			self.log.info(f'Using Robocopy.exe to copy {src_dir} to {self.destination}', echo=True)
			robocopy = RoboCopy(src_dir, self.destination / src_dir.name, '/e', '/fp', '/ns', '/ndl')
			self._log_robocopy(robocopy.wait(echo=self.echo, quantity=quantity, start=start))
			start = robocopy.counter + 1
		if self.hash_algs:
			self.hashes = hash_thread.wait(echo=self.echo)
		with self.tsv_path.open('w', encoding='utf-8') as fh:
			print(f'Source\tType\t{"\t".join(self.hash_algs)}', file=fh)
			cols2add = '\t-' * len(self.hash_algs)
			for path in dirs2log:
				print(f'{path}\tdir\t{cols2add}', file=fh)
			for path, hashes in self.hashes.items():
				print(f'{path}\tfile\t{"\t".join(hashes[alg] for alg in self.hash_algs)}', file=fh)
		self.log.info(f'Done, file hashes are listed in {self.tsv_path}', echo=True)
		if self.errors:
			self.log.warning(f'Robocopy.exe reported problems')
		else:
			self.log.info('Finished copy process without Errors', echo=True)

	def _log_robocopy(self, returncode):
		'''Log robocopy returncode'''
		if returncode > 5:
			self.log.warning(f'Robocopy.exe failed with returncode {returncode}')
			self.errors += 1
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
		self.add_argument('-d', '--destination', type=Path, required=True,
			help='Destination root (required)', metavar='DIRECTORY'
		)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write log and file list (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('-p', '--processes', type=int,
			help='Number of parallel processes to hash (default: CPU cores / 2)', metavar='INTEGER'
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
				self.algorithms = list()
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
		hrc.copy(self.sources, self.destination,
			filename = self.filename,
			outdir = self.outdir,
			hashes = self.algorithms
		)
		hrc.log.close()

if __name__ == '__main__':	# start here if called as application
	app = HashedRoboCopyCli()
	app.parse()
	app.run()
