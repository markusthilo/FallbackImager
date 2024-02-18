#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'AxChecker'
__author__ = 'Markus Thilo'
__version__ = '0.4.0_2024-02-18'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
As Magnet's AXIOM has proven to be unreliable in the past, this module compares the files in an AXIOM Case.mfdb to a file list (CSV/TSV e.g. created with X-Ways) or a local file structure. Only one partition of the case file can be compared at a time.

Hits are files, that are represented in the artifacts. Obviously this tool can only support to find missing files. You will (nearly) never have the identical file lists. In detail AxChecker takes the file paths of the AXIOM case and tries to subtract normalized paths from the list or file system.
'''

from pathlib import Path
from argparse import ArgumentParser
from os import name as __os_name__
from lib.extpath import ExtPath, Progressor
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.mfdbreader import MfdbReader
from lib.tsvreader import TsvReader

class AxChecker:
	'''Compare AXIOM case file / SQlite data base with paths'''

	def __init__(self):
		'''Create Object'''
		self.available = True

	def open(self, mfdb, echo=print):
		'''Open database'''
		self.mfdb = MfdbReader(mfdb)
		self.mfdb_path = Path(mfdb)
		self.echo = echo

	def list_partitions(self):
		'''List the partitions'''
		for n, partition_id in enumerate(self.mfdb.get_partition_ids(), start=1):
			self.echo(f'{n}: {self.mfdb.paths[partition_id]}')

	def check(self,
			filename = None,
			outdir = None,
			diff = None,
			partition = None,
			column = None,
			nohead = False,
			log = None
		):
		'''Check AXIOM case file'''
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		if diff:
			self.diff_path = Path(diff)
		else:
			self.diff_path = None
		if partition:
			try:
				self.partition = int(partition)
			except ValueError:
				self.partition = partition
		else:
			self.partition = None
		self.column = column
		self.nohead = nohead
		if log:
			self.log = log
		else:
			self.log = Logger(filename=self.filename, outdir=self.outdir, 
				head='axchecker.AxChecker', echo=self.echo)
		self.log.info(f'Reading {self.mfdb_path.name}', echo=True)
		partition_ids = self.mfdb.get_partition_ids()
		file_ids = self.mfdb.get_file_ids()
		hit_ids = self.mfdb.get_hit_ids()
		self.log.info(
			f'Case contains {len(partition_ids)} partitions, {len(file_ids)} file paths and {len(hit_ids)} hits',
			echo = True
		)
		if self.partition:
			partition_name = self.mfdb.get_partition_name(self.partition)
			if not partition_name:
				self.log.error('Unable to find given partition')
			self.log.info(f'Grepping file paths of partition {partition_name}', echo=True)
			paths = [path for path in self.mfdb.grep_partition(partition_name)]
			if not paths:
				self.log.error('Empty or not existing partition')
			msg = f'of partition {partition_name} '
		else:
			paths = [self.mfdb.paths[source_id] for source_id in file_ids]
			msg = ''
		self.log.info(f'Writing {len(paths)} paths {msg}to file', echo=True)
		with ExtPath.child(f'{self.filename}_files.txt', parent=self.outdir
			).open(mode='w', encoding='utf-8') as fh:
			for path in paths:
				print(path, file=fh)
		no_hit_ids = set(file_ids) - set(hit_ids)
		if no_hit_ids:
			self.log.info(f'{len(no_hit_ids)} file(s) is/are not represented in hits', echo=True)
			with ExtPath.child(f'{self.filename}_not_in_hits.txt', parent=self.outdir
			).open(mode='w', encoding='utf-8') as fh:
				for source_id in no_hit_ids:
					print(self.mfdb.paths[source_id], file=fh)
		if not self.diff_path:	# end here if nothing to compare is given
			self.log.info('Done', echo=True)
			return
		if not self.partition:
			raise ValueError('Missing partition to compare')
		self.log.info(f'Comparing AXIOM partition {partition_name} to {self.diff_path.name}', echo=True)
		part_name_len = len(partition_name)
		short_paths = {ExtPath.normalize_str(path[part_name_len:]) for path in paths}
		missing_cnt = 0
		if self.diff_path.is_dir():	# compare to dir
			progress = Progressor(self.diff_path, echo=self.echo)
			if __os_name__ == 'nt':
				normalize = ExtPath.normalize_win
			else:
				normalize = ExtPath.normalize_posix
			with ExtPath.child(f'{self.filename}_missing_files.txt', parent=self.outdir
				).open(mode='w', encoding='utf-8') as fh:
				for absolut_path, relative_path, tp in ExtPath.walk(self.diff_path):
					progress.inc()
					if tp == 'f' and not normalize(relative_path) in short_paths:
						print(relative_path, file=fh)
						missing_cnt += 1
		elif self.diff_path.is_file:	# compare to file
			tsv = TsvReader(self.diff_path, column=self.column, nohead=self.nohead)
			if tsv.column < 0:
				self.log.error('Column out of range/undetected')
			with ExtPath.child(f'{self.filename}_missing_files.txt', parent=self.outdir
				).open(mode='w', encoding='utf-8') as fh:
				if not self.nohead:
					print(tsv.head, file=fh)
				if self.echo == print:
					echo = lambda msg: print(f'\r{msg}', end='')
				else:
					echo = lambda msg: self.echo(msg, overwrite=True)
				echo(1)
				for tsv_cnt, (tsv_path, line) in enumerate(tsv.read_lines()):
					if not ExtPath.normalize_str(tsv_path) in short_paths:
						print(line, file=fh)
						missing_cnt += 1
					if tsv_cnt % 10000 == 0:
						echo(tsv_cnt)
			echo('')
			if tsv.errors:
				self.log.warning(
					f'Found unprocessable line(s) in {diff_path.name}:\n'+
					'\n'.join(tsv.errors)
				)
		else:
			self.log.error(f'Unable to read/open {diff_path.name}')
		if missing_cnt > 0:
			self.log.info(f'Found {missing_cnt} missing file path(s) in AXIOM case file',
				echo=True)

class AxCheckerCli(ArgumentParser):
	'''CLI, also used for GUI of FallbackImager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-c', '--column', type=str,
			help='Column with path to compare', metavar='INTEGER|STRING'
		)
		self.add_argument('-d', '--diff', type=ExtPath.path,
			help='Path to file or directory to compare with', metavar='FILE|DIRECTORY'
		)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-l', '--list', default=False, action='store_true',
			help='List images and partitions (ignores all other arguments)'
		)
		self.add_argument('-n', '--nohead', default=False, action='store_true',
			help='TSV file has no head line with names of columns (e.g. "Full path" etc.)'
		)
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write log and CSV list(s)', metavar='DIRECTORY'
		)
		self.add_argument('-p', '--partition', type=str,
			help='Partiton to compare (partition name or number in AXIOM case)', metavar='STRING/INT'
		)
		self.add_argument('mfdb', nargs=1, type=ExtPath.path,
			help='AXIOM Case (.mfdb) / SQLite data base file', metavar='FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.mfdb = args.mfdb[0]
		self.column = args.column
		self.diff = args.diff
		self.filename = args.filename
		self.list = args.list
		self.nohead = args.nohead
		self.outdir = args.outdir
		self.partition = args.partition

	def run(self, echo=print):
		'''Run AxChecker'''
		axchecker = AxChecker(self.mfdb, echo=echo)
		if self.list:
			axchecker.list_partitions()
			return
		axchecker.check(
			filename = self.filename,
			outdir = self.outdir,
			diff = self.diff,
			column = self.column,
			nohead = self.nohead,
			partition = self.partition
		)
		axchecker.log.close()

if __name__ == '__main__':	# start here if called as application
	app = AxCheckerCli()
	app.parse()
	app.run()
