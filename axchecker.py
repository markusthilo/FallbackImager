#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'AxChecker'
__author__ = 'Markus Thilo'
__version__ = '0.5.2_2024-06-10'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
As Magnet's AXIOM has proven to be unreliable in the past, this module compares the files in
an AXIOM Case.mfdb to a file list (CSV/TSV e.g. created with X-Ways) or a local file structure.
Only one partition or subtree of the case file can be compared at a time.
Hits are files, that are represented in the artifacts.
This tool might help to find missing files. Be aware that you will (nearly) never have full accordance.
'''

from argparse import ArgumentParser
from os import name as __os_name__
from lib.extpath import ExtPath, Progressor
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.sqliteutils import SQLiteReader

class MfdbReader(SQLiteReader):
	'''Extend SqliteReader for AXIOM data base'''

	def _read_source(self):
		'''Read table source'''
		for source_id, parent_source_id, source_type, source_friendly_value in self.fetch_table('source',
			columns=('source_id', 'parent_source_id', 'source_type', 'source_friendly_value')):
			source_id = int(source_id)
			try:
				parent_source_id = int(parent_source_id)
			except TypeError:
				parent_source_id = None
			yield source_id, parent_source_id, source_type, source_friendly_value

	def _read_paths(self):
		'''Read table source_path'''
		for source_id, source_path in self.fetch_table('source_path',
			columns=('source_id', 'source_path')):
			yield int(source_id), source_path

	def get_types(self):
		'''Read table source and get types'''
		self.types = {int(source_id): source_type
			for source_id, source_type
			in self.fetch_table('source', columns=('source_id', 'source_type'))
		}

	def read_roots(self, max_depth=2):
		'''Read potential root paths to compare'''
		self.get_types()
		for source_id, source_path in self._read_paths():
			source_type = self.types[source_id]
			if source_type != 'File' and source_path.count('\\') < max_depth:
				yield source_id, source_type, source_path

	def read_paths(self):
		'''Read table source_path and get source_type from table source'''
		self.get_types()
		self.paths = dict()
		self.file_ids = set()	# ids of files to compare with hits
		for source_id, source_path in self._read_paths():
			source_type = self.types[source_id]
			self.paths[source_id] = (source_type, source_path)
			if self.types[source_id] == 'File':
				self.file_ids.add(source_id)
			yield source_id, source_type, source_path

	def get_hit_ids(self):
		'''Get hit ids'''
		self.hit_ids = {source_id
			for source_id
			in self.fetch_table('hit_location', column='hit_location_id')}
		return self.hit_ids

	def get_paths(self):
		'''Get paths as dict'''
		self.get_types()
		self.paths = { source_id: (self.types[source_id], source_path)
			for source_id, source_path in self._read_paths()
		}

	def walk(self, root_id):
		'''Recursivly get sub-paths'''
		self.get_paths()
		root_path = f'{self.paths[root_id][1]}\\'
		root_len = len(root_path)
		for source_id, (source_type, source_path) in self.paths.items():
			if source_path.startswith(root_path):
				yield source_id, source_type, source_path[root_len:]

	def get_relative_paths(self, root_id):
		'''Get relative paths under given root'''
		return {ExtPath.normalize(relative_path)
			for source_id, source_type, relative_path in self.walk(root_id)
		}

	def tree(self):
		'''Read table source and give possible roots'''
		for source_id, parent_source_id, source_type, source_friendly_value in self._read_source():
			if source_type != 'File':
				yield source_id, parent_source_id, source_type, source_friendly_value

class AxChecker:
	'''Compare AXIOM case file / SQlite data base with paths'''

	def __init__(self):
		'''Create Object'''
		self.available = True

	def open(self, mfdb, echo=print):
		'''Open database'''
		self.mfdb = MfdbReader(mfdb)
		self.mfdb_path = ExtPath.path(mfdb)
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
		self.filename = TimeStamp.now_or(filename, base='axchecker')
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
			nohead = False,
			encoding = None,
			filename = None,
			outdir = None,
			log = None
		):
		'''Compare to CSV/TSV path list or existing file structure'''
		self._set_output(filename, outdir, log)
		if not root_id:
			self.log.error('Missing root ID to compare')
		diff_path = ExtPath.path(diff)
		self.log.info(f'Reading {self.mfdb_path.name}', echo=True)
		axiom_paths = self.mfdb.get_relative_paths(root_id)
		self.log.info(f'Comparing {self.mfdb.paths[root_id][1]} recursivly to {diff_path.name}', echo=True)
		missing_cnt = 0
		if diff_path.is_dir():	# compare to dir
			progress = Progressor(diff_path, echo=self.echo)
			if __os_name__ == 'nt':
				normalize = ExtPath.normalize_win
			else:
				normalize = ExtPath.normalize_posix
			with ExtPath.child(f'{self.filename}_missing_files.txt', parent=self.outdir
				).open(mode='w', encoding='utf-8') as fh:
				for absolut_path, relative_path, tp in ExtPath.walk(diff_path):
					progress.inc()
					if tp == 'File' and not normalize(relative_path) in axiom_paths:
						print(relative_path, file=fh)
						missing_cnt += 1
		elif diff_path.is_file:	# compare to file
			if not encoding:
				if __os_name__ == 'nt':
					encoding = 'utf_16_le'
				else:
					encoding = 'utf-8'
				encoding = self.default_encoding()
			tsv = diff_path.read_bytes().decode(encoding, errors='ignore').split('\n')
			with ExtPath.child(f'{self.filename}_missing_files.txt', parent=self.outdir
				).open(mode='w', encoding=encoding) as fh:
				if not nohead:
					print(tsv.pop(0).strip(), file=fh)
				if self.echo == print:
					echo = lambda msg: print(f'\r{msg}', end='')
				else:
					echo = lambda msg: self.echo(msg, overwrite=True)
				echo(1)
				for tsv_cnt, line in enumerate(tsv):
					path = ExtPath.normalize(line.split('\t', 1)[0])
					if not path in axiom_paths:
						print(line.strip(), file=fh)
						missing_cnt += 1
					if tsv_cnt % 10000 == 0:
						echo(tsv_cnt)
			echo('')
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
		self.add_argument('-d', '--diff', type=ExtPath.path,
			help='Path to file or directory to compare with', metavar='FILE|DIRECTORY'
		)
		self.add_argument('-e', '--encoding', type=str,
			help='Encoding of the file given by --diff (default is utf_16_le on Win, utf-8 on other systems)',
			metavar='STRING'
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
			help='ID of root path to compare', metavar='INTEGER'
		)
		self.add_argument('mfdb', nargs=1, type=ExtPath.path,
			help='AXIOM Case (.mfdb) / SQLite data base file', metavar='FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.mfdb = args.mfdb[0]
		self.diff = args.diff
		self.encoding = args.encoding
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
				encoding = self.encoding,
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
