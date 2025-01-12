#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'HashedCopy'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2025-01-12'
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
from lib.hashes import FileHashes
from lib.winutils import RoboWalk, RoboCopy

class HashedRoboCopy:
	'''Tool to copy files and verify the outcome using hashes'''

	def __init__(self, echo=print):
		'''Create object'''
		self.available = True
		self.echo = echo

	def _print_line(self, line):
		'''Print line'''
		if line.rstrip().endswith('%'):
			print(f'\r{line.strip()}  \r', end='')
		else:
			print(line)

	def _print_allive(self):
		'''Show that I am alive'''
		try:
			self._allive_i += 1
		except AttributeError:
			self._allive_i = 0
		if self._allive_i > 3:
			self._allive_i = 0
		print(f'\r{"-\\|/"[self._allive_i]}\r', end='')

	def _calc_hashes(self):
		'''Calculate hashes'''
		self.hashes = dict()
		for alg in self._hashe_algs:
			self.log.info(f'Calculating {alg} hashes')
			print(alg)
			self.hashes[alg] = FileHashes(self.src_tree.files, algorithm=alg).calculate()
		self.log.info('Finished calculating hashes')

	def cp(self, source, destination, filename=None, outdir=None, hashes=('md5',), log=None):
		'''Copy multiple sources'''
		self.filename = TimeStamp.now_or(filename)
		self.outdir = PathUtils.mkdir(outdir)
		self.tsv_path = self.outdir / f'{self.filename}_files.tsv'
		self.log = log if log else Logger(
			filename=self.filename, outdir=self.outdir, head='hashedrobocopy.HashedRoboCopy', echo=self.echo)
		self.source = Path(source).resolve()
		if not self.source.exists():
			self.log.error(f'Source {self.source} does not exist')
		self.destination = Path(destination).resolve()
		if not self.destination.is_dir():
			self.log.error('Destination {self.destination} is not a directory')
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
		if self.destination.exists():
			self.log.error('Destination {self.destination} already exits')
		self.src_tree = RoboWalk(self.source)
		self._hashe_algs = hashes
		hash_thread = Thread(target=self._calc_hashes)
		hash_thread.start()
		self.log.info(f'Using Robocopy.exe to copy {self.source} to {self.destination}', echo=True)
		robocopy = RoboCopy(self.source, self.destination, '/e', '/fp', '/ns', '/nc', '/ndl')
		for line in robocopy.run():
			self._print_line(line)
		returncode = robocopy.wait()
		if returncode == 1:
			self.log.info('Finished copy process successfully, Robocopy.exe returncode: 1', echo=True)
		else:
			self.log.warning(f'Robocopy.exe failed with returncode: {returncode}')
		if hash_thread.is_alive():
			self.echo('Calculating hashes')
			while hash_thread.is_alive():
				self._print_allive()
				sleep(.25)
			self.echo()
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
			help='Algorithms to hash seperated by colon (e.g. -a md5,sha256, default is md5)', metavar='STRING'
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
		self.add_argument('source', nargs=1, type=Path,
			help='Source files or directories to copy', metavar='FILE/DIRECTORY'
		)
		self.echo = echo

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.source = args.source[0]
		self.destination = args.destination
		self.filename = args.filename
		self.outdir = args.outdir

	def run(self):
		'''Run the tool'''
		copy = HashedRoboCopy(echo=self.echo)
		copy.cp(self.source, self.destination,
			filename = self.filename,
			outdir = self.outdir
		)
		copy.log.close()

if __name__ == '__main__':	# start here if called as application
	app = HashedRoboCopyCli()
	app.parse()
	app.run()
