#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'AxChecker'
__author__ = 'Markus Thilo'
__version__ = '0.2.3_2024-01-23'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
As Magnet's AXIOM has proven to be unreliable in the past, this module compares the files in an AXIOM Case.mfdb to a file list (CSV/TSV e.g. created with X-Ways) or a local file structure. Only one partition of the case file can be compared at a time.

Hits are files, that are represented in the artifacts. Obviously this tool can only support to find missing files. You will (nearly) never have the identical file lists. In detail AxChecker takes the file paths of the AXIOM case and tries to subtract normalized paths from the list or file system.
'''

from pathlib import Path
from argparse import ArgumentParser
from tkinter import StringVar
from tkinter.ttk import Radiobutton, Button, Checkbutton
from tkinter.messagebox import showerror
from tkinter.scrolledtext import ScrolledText
from lib.extpath import ExtPath, FilesPercent
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.mfdbreader import MfdbReader
from lib.tsvreader import TsvReader

class AxChecker:
	'''Compare AXIOM case file / SQlite data base with paths'''

	def __init__(self):
		'''Create Object'''
		pass

	def list_partitions(self, mfdb, echo=print):
		'''List the partitions'''
		for n, partition_id in enumerate(MfdbReader().get_partition_ids(mfdb), start=1):
			self.echo(f'{n}: {self.mfdb.paths[partition_id]}')

	def check(self, mfdb,
			filename = None,
			outdir = None,
			diff = None,
			partition = None,
			column = None,
			nohead = False,
			log = None,
			echo = print
		):
		'''Check AXIOM case file'''
		self.mfdb_path = Path(mfdb)
		self.mfdb = MfdbReader(self.mfdb_path)
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
		self.echo = echo
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
		self.log.info(f'Comparing AXIOM partition {partition_name} to {self.diff_path.name}', echo=True)
		short_paths = {path[len(partition_name):] for path in paths}
		missing_cnt = 0
		if self.diff_path.is_dir():	# compare to dir
			progress = FilesPercent(self.diff_path, echo=self.echo)
			with ExtPath.child(f'{self.filename}_missing_files.txt', parent=self.outdir
				).open(mode='w', encoding='utf-8') as fh:
				for absolut_path, relative_path in ExtPath.walk_files(self.diff_path):
					progress.inc()
					path = ExtPath.windowize(relative_path)
					if not path in short_paths:
						print(absolut_path, file=fh)
						missing_cnt += 1
		elif self.diff_path.is_file:	# compare to file
			tsv = TsvReader(self.diff_path, column=self.column, nohead=self.nohead)
			if tsv.column < 0:
				self.log.error('Column out of range/undetected')
			with ExtPath.child(f'{self.filename}_missing_files.txt', parent=self.outdir
				).open(mode='w', encoding='utf-8') as fh:
				if not self.nohead:
					print(tsv.head, file=fh)
				for full_path, line in tsv.read_lines():
					if not ExtPath.normalize(full_path) in short_paths:
						print(line, file=fh)
						missing_cnt += 1
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
			help='Image and partiton to compare (--diff DIRECTORY)', metavar='STRING'
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
		if self.list:
			AxChecker().list_partitions(self.mfdb, echo=echo)
			return
		axchecker = AxChecker()
		axchecker.check(self.mfdb,
			filename = self.filename,
			outdir = self.outdir,
			diff = self.diff,
			column = self.column,
			nohead = self.nohead,
			partition = self.partition,
			echo = echo,
		)
		axchecker.log.close()

if __name__ == '__main__':	# start here if called as application
	app = AxCheckerCli()
	app.parse()
	app.run()
