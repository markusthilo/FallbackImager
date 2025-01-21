#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'HashedCopy'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2025-01-21'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Safe copy with log and hashes.
'''

from pathlib import Path
from threading import Thread
from time import sleep
from argparse import ArgumentParser
from lib.pathutils import PathUtils, Progressor
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.hashes import HashThread
from lib.winutils import RoboWalk, RoboCopy

class HashedRoboCopy:
	'''Tool to copy files and verify the outcome using hashes'''

	def __init__(self, echo=print):
		'''Create object'''
		self.available = True
		self.echo = echo

	def copy(self, sources, destination, filename=None, outdir=None, hashes=None, compare=False, processes=None, log=None):
		'''Copy multiple sources'''
		self.filename = TimeStamp.now_or(filename)
		self.outdir = PathUtils.mkdir(outdir)
		self.tsv_path = self.outdir / f'{self.filename}_files.tsv'
		self.log = log if log else Logger(
			filename=self.filename, outdir=self.outdir, head='hashedrobocopy.HashedRoboCopy', echo=self.echo)
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

		'''
		if self.source.name:
			self.destination = self.destination.joinpath(self.source.name)
		else:
			splitted = f'{self.source}'.split(':')
			if len(splitted) > 1:
				self.destination = self.destination.joinpath(splitted[0])
			else:
				splitted = f'{self.source}'.split('\\')
				if len(splitted) > 1:
					self.destination = self.destination.joinpath(splitted[-2])
				else:
					self.destination = self.destination.joinpath(filename)
		'''

		self.destination = Path(destination).resolve()
		if self.destination.exists() and not self.destination.is_dir():
			self.log.error('Destination {self.destination} exits and is not a directory')
		files2hash = set()
		quantity = len(self.src_files)
		for src_dir in self.src_dirs:
			robowalk = RoboWalk(src_dir)
			files2hash.update(robowalk.files)
			quantity += len(robowalk.files)
		files2hash.update(self.src_files)
		hash_thread = HashThread(files2hash, algorithms=hashes, processes=processes)
		hash_thread.start()
		for src_file in self.src_files:
			self.log.info(f'Using Robocopy.exe to copy {src_file} to {self.destination}', echo=True)
			robocopy = RoboCopy(src_file.parent, self.destination, src_file.name, '/fp', '/ns', '/ndl',
				echo=self.echo)
			robocopy.wait()
		for src_dir in self.src_dirs:
			self.log.info(f'Using Robocopy.exe to copy {src_dir} to {self.destination}', echo=True)
			robocopy = RoboCopy(src_dir, self.destination / src_dir.name, '/e', '/fp', '/ns', '/ndl',
				echo=self.echo, start=)
			robocopy.wait()
		if hash_thread.is_alive():
			index = 0
			self.echo('Calculating hashes')
			while hash_thread.is_alive():
				self.echo('-\\|/'[index], end='\r')
				sleep(.25)
				index = (index + 1) % 4
		

		hash_thread.join()
		print(hash_thread.hashes)
		exit()

		robocopy = RoboCopy(self.source, self.destination, '/e', '/fp', '/ns', '/nc', '/ndl')
		for line in robocopy.run():
			self._print_line(line)
		returncode = robocopy.wait()
		if returncode == 1:
			self.log.info('Finished copy process successfully, Robocopy.exe returncode: 1', echo=True)
		else:
			self.log.warning(f'Robocopy.exe failed with returncode: {returncode}')




		with self.tsv_path.open('w', encoding='utf-8') as fh:
			print(f'Source\tRelative_Path\tType\t{"\t".join(self._hashe_algs)}', file=fh)
			cols2add = '\t-' * len(self._hashe_algs)
			for absolut, relative in self.src_tree.get_relative_dirs().items():
				print(f'{absolut}\t{relative}\tdir{cols2add}', file=fh)
			for absolut, relative in self.src_tree.get_relative_files().items():
				hashes = [self.hashes[alg][absolut] for alg in self._hashe_algs]
				print(f'{absolut}\t{relative}\tfile{"\t".join(hashes)}', file=fh)
		self.log.info(f'Done, file hashes are listed in {self.tsv_path}', echo=True)

class HashedRoboCopyCli(ArgumentParser):
	'''CLI for the copy tool'''

	def __init__(self, echo=print):
		'''Define CLI using argparser'''
		super().__init__(description=__description__.strip(), prog=__app_name__.lower())
		self.add_argument('-a', '--algorithms', type=str,
			help='Algorithms to hash seperated by colon (e.g. "md5,sha256", no hashing: "none", default: "md5")', metavar='STRING'
		)
		self.add_argument('-c', '--compare', action='store_true',
			help='Hash files at destination and check if mathing to source (use 1st given algorithm)'
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
		self.compare = args.compare
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
		self.processes = args.processes

	def run(self):
		'''Run the tool'''
		hrc = HashedRoboCopy(echo=self.echo)
		hrc.copy(self.sources, self.destination,
			filename = self.filename,
			outdir = self.outdir,
			hashes = self.algorithms,
			compare = self.compare,
			processes = self.processes
		)
		hrc.log.close()

if __name__ == '__main__':	# start here if called as application
	app = HashedRoboCopyCli()
	app.parse()
	app.run()
