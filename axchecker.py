#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'AxChecker'
__author__ = 'Markus Thilo'
__version__ = '0.4.1_2024-02-26'
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

	def list_roots(self, max_depth):
		'''List the potential root paths to compare'''
		try:
			max_depth = int(max_depth)
		except ValueError:
			max_depth = 2
		for source_id, source_type, source_path in self.mfdb.read_roots(max_depth=max_depth):
			self.echo(f'{source_id}: {source_path} ({source_type})')

	def _set_output(self, filename, outdir, log):
		'''Set output dir, filename and log'''
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		if log:
			self.log = log
		else:
			self.log = Logger(filename=self.filename, outdir=self.outdir, 
				head='axchecker.AxChecker', echo=self.echo)

	def check(self, filename=None, outdir=None, log=None):
		'''
			1.) Read table source from AXIOM case file and write to TSV
			2.) Look for files not represented in hits and write to TSV
		'''
		self._set_output(filename, outdir, log)
		self.log.info(f'Reading {self.mfdb_path.name}', echo=True)
		with ExtPath.child(f'{self.filename}_paths.tsv', parent=self.outdir
				).open(mode='w', encoding='utf-8') as fh:
				print('source_id\tsource_type\tsource_path', file=fh)
				for source_id, source_type, source_path in self.mfdb.read_paths():
					print(f'{source_id}\t{source_type}\t"{source_path}"', file=fh)
		self.log.info(f'AXIOM case contains {len(self.mfdb.paths)} paths, {len(self.mfdb.file_ids)} are files', echo=True)
		no_hit_ids = self.mfdb.file_ids - self.mfdb.get_hit_ids()
		if no_hit_ids:
			self.log.info(f'{len(no_hit_ids)} file(s) is/are not represented in hits', echo=True)
			with ExtPath.child(f'{self.filename}_not_in_hits.tsv', parent=self.outdir
			).open(mode='w', encoding='utf-8') as fh:
				for source_id in no_hit_ids:
					source_type, source_path = self.mfdb.paths[source_id]
					print(f'{source_id}\t{source_type}\t"{source_path}"', file=fh)

	def compare(self, root_id, diff,
			column = None,
			nohead = False,
			filename = None,
			outdir = None,
			log = None
		):
		'''Compare to CSV/TSV path list or existing file structure'''
		self._set_output(filename, outdir, log)
		self.diff_path = Path(diff)
		self.log.info(f'Reading {self.mfdb_path.name}', echo=True)
		axiom_file_paths = self.mfdb.file_paths(root_id)
		self.log.info(f'Comparing {self.mfdb.paths[root_id][1]} recursivly to {self.diff_path.name}', echo=True)
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

					print(absolut_path, relative_path, tp)

					if tp == 'File' and not normalize(relative_path) in axiom_file_paths:
						print(relative_path, file=fh)
						missing_cnt += 1
		elif self.diff_path.is_file:	# compare to file
			if column:
				self.column = column
			else:
				self.column = 1
			self.nohead = nohead
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
					if not ExtPath.normalize_str(tsv_path) in axiom_file_paths:
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
		self.add_argument('-l', '--list', type=str,
			help='List potential root IDs and paths by given max. path depth (!INTEGER = default)',
			metavar='INTEGER'
		)
		self.add_argument('-n', '--nohead', default=False, action='store_true',
			help='TSV file has no head line with names of columns (e.g. "Full path" etc.)'
		)
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write log and CSV list(s)', metavar='DIRECTORY'
		)
		self.add_argument('-r', '--root', type=int,
			help='ID of root path to list or to compare', metavar='INTEGER'
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
		self.root = args.root

	def run(self, echo=print):
		'''Run AxChecker'''
		axchecker = AxChecker()
		axchecker.open(self.mfdb, echo=echo)
		if self.list:
			axchecker.list_roots(self.list)
			return
		if self.diff:
			axchecker.compare(self.root, self.diff,
				column = self.column,
				nohead = self.nohead,
				filename = self.filename,
				outdir = self.outdir
			)
		else:
			axchecker.check(filename=self.filename, outdir=self.outdir)
		axchecker.log.info('All done', echo= True)
		axchecker.log.close()

if __name__ == '__main__':	# start here if called as application
	app = AxCheckerCli()
	app.parse()
	app.run()
