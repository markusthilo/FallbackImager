#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'AxChecker'
__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-23'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Verify AXIOM case files
'''

from pathlib import Path
from argparse import ArgumentParser
from sqlite3 import connect as SqliteConnect
from re import compile as regcompile
from tkinter.messagebox import showerror
from lib.extpath import ExtPath
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.greplists import GrepLists
from lib.guielements import SourceDirSelector, Checker
from lib.guielements import ExpandedFrame, GridSeparator, GridLabel, DirSelector
from lib.guielements import FilenameSelector, StringSelector, StringRadiobuttons
from lib.guielements import FileSelector, GridButton

class SQLiteReader:
	'''Read SQLite files'''

	def __init__(self, sqlite_path):
		'Open database'
		self.db = SqliteConnect(sqlite_path)
		self.cursor = self.db.cursor()
		
	def fetch_table(self, table, fields=None , where=None):
		'''Fetch one table completely'''
		cmd = 'SELECT '
		if fields:
			if isinstance(fields, str):
				cmd += f'"{fields}"'
			else:
				cmd += ', '.join(f'"{field}"' for field in fields)
		else:
			sql_cmd += '*'
		cmd += f' FROM "{table}"'
		if where:
			cmd += f' WHERE "{where[0]}"='
			cmd += f"'{where[1]}'"
		for row in self.cursor.execute(f'{cmd};'):
			yield row

	def close(self):
		'Close SQLite database'
		self.db.close()

class AxChecker:
	'''Compare AXIOM case file / SQlite data base with paths'''

	def __init__(self, mfdb, diff,
			filename = None,
			outdir = None,
			difftype = 'none',
			drop = GrepLists.false,
			log = None,
			echo = print
		):
		'''Definitions'''
		self.mfdb_path = Path(mfdb)
		self.diff_path = Path(diff)
		self.diff_type = None
		if self.diff_path.is_file():
			if pathtype == 'plain':
				self.diff_type = 'Plain text'
			elif difftype == 'tsv':
				self.diff_type = 'TSV'
		elif self.diff_path.is_dir and difftype == 'plain':
			self.diff_type = 'File system'
		if not self.diff_type:
			raise NotImplementedError(f'{path} with {difftype}')
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		self.echo = echo
		if log:
			self.log = log
		else:
			self.log = Logger(filename=self.filename, outdir=self.outdir, 
				head=f'axchecker.AxChecker, diff tipe: {self.diff_type}', echo=echo)

	def run(self):
		'''Compare content if image to source'''
		self.log.info(f'Reading {self.mfdb_path.name}', echo=True)
		db = SQLiteReader(self.mfdb_path)
		source_evidence = {source_id: source_evidence_number
			for source_id, source_evidence_number in db.fetch_table(
				'source_evidence',
				fields = ('source_id', 'source_evidence_number')
			)
		}
		source_partitions = dict()
		ids_to_drop = set()
		reg_evidence = regcompile('\.[^.]*$')
		reg_partition = regcompile(' ([0-9]+) ')
		for source_id, root_source_id, source_friendly_value in db.fetch_table(
				'source',
				fields = ('source_id', 'root_source_id', 'source_friendly_value'),
				where = ('source_type', 'Partition')
			):
			evidence = reg_evidence.sub('', source_evidence[root_source_id], 1)
			match = reg_partition.search(source_friendly_value)
			if match:
				partition = match.groups()[0]
				print('match:', match)
			else:
				partition = ''
			print(source_id, source_evidence[root_source_id], root_source_id, source_friendly_value)
			print(f'>{evidence} - {partition}<')
		#root_source_id: source_friendly_value
		
		
		
		
		
		
		#for source_id, source_path in db.fetch_table('source_path',
		#	fields=('source_id', 'source_path')):
		#	print(source_id, source_path)
		#	if source_path.startswith(

		#hit_location_sources = {row[0]
		#	for row in db.fetch_table('hit_location', fields='source_id')}


		#print(source_evidence)
		#print(source_partitions)
		#print(source_paths)
		#print(hit_location_sources)
		'''
		image = set()
		with ExtPath.child(f'{self.filename}_content.txt',
			parent=self.outdir).open(mode='w') as fh:
			for line in proc.readlines_stdout():
				if line and line[0] == '\\':
					print(line, file=fh)
					image.add(line.strip('\\'))
		if len(image) > 0:
			self.log.finished(proc, echo=True)
		else:
			self.log.finished(proc, error=': No or empty image\n')
		missing_file_cnt = 0
		missing_dir_cnt = 0
		missing_else_cnt = 0
		with ExtPath.child(f'{self.filename}_missing.txt',
			parent=self.outdir).open(mode='w') as fh:
			for path in ExtPath.walk(self.root_path):
				short = str(path.relative_to(self.root_path)).strip("\\")
				if short in image:
					continue
				if path.is_file():
					print(f'', file=fh)
					missing_file_cnt += 1
				elif path.is_dir():
					print(f'', file=fh)
					missing_dir_cnt += 1
				else:
					print(f'', file=fh)
					missing_else_cnt += 1
		missing_all_cnt = missing_file_cnt + missing_dir_cnt + missing_else_cnt
		msg = 'Verification:'
		if missing_all_cnt == 0:
			msg += f' no missing files or directories in {self.image_path.name}'
			self.log.info(msg, echo=True)
		else:
			msg += f'\nMissing content {missing_all_cnt} / {missing_file_cnt}'
			msg += f' / {missing_dir_cnt} / {missing_else_cnt}'
			msg += ' (all/files/dirs/other)\n'
			msg += f'Check {self.filename}_missing.txt if relevant content is missing!'
			self.log.warning(msg)
		'''

class AxCheckerCli(ArgumentParser):
	'''CLI, also used for GUI of FallbackImager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-b', '--blacklist', type=Path,
			help='Blacklist (textfile with one regex per line)', metavar='FILE'
		)
		self.add_argument('-d', '--diff', type=Path, required=True,
			help='Path to file or directory to compare with', metavar='FILE|DIRECTORY'
		)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write generated missing files', metavar='DIRECTORY'
		)
		self.add_argument('-t', '--difftype', type=str, default='plain',
			choices=['plain', 'tsv'],
			help='Type of comparison method or type of path to compare', metavar='STRING'
		)
		self.add_argument('-w', '--whitelist', type=Path,
			help='Whitelist (if given, blacklist is ignored)', metavar='FILE'
		)
		self.add_argument('mfdb', nargs=1, type=Path,
			help='AXIOM Case (.mfdb) / SQLite data base file', metavar='FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.mfdb = args.mfdb[0]
		self.blacklist = args.blacklist
		self.diff = args.diff
		self.filename = args.filename
		self.outdir = args.outdir
		self.difftype = args.difftype
		self.whitelist = args.whitelist

	def run(self, echo=print):
		'''Run AxChecker'''
		drop = GrepLists(
			blacklist = self.blacklist,
			whitelist = self.whitelist, 
			echo = echo
		).get_method()
		AxChecker(self.mfdb, self.diff,
			filename = self.filename,
			outdir = self.outdir,
			difftype = self.difftype,
			drop = drop,
			echo = echo,
		).run()

class AxCheckerGui:
	'''Notebook page'''

	CMD = __app_name__
	DESCRIPTION = __description__

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		self.frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(self.frame, text=f' {self.CMD} ')
		root.row = 0
		self.source_dir = SourceDirSelector(root, self.frame)
		GridLabel(root, self.frame, root.DESTINATION, columnspan=2)
		self.filename_str = FilenameSelector(root, self.frame, root.FILENAME, root.FILENAME)
		DirSelector(root, self.frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		self.name_str = StringSelector(root, self.frame, root.IMAGE_NAME, root.IMAGE_NAME,
			command=self._gen_name)
		self.descr_str = StringSelector(root, self.frame, root.IMAGE_DESCRIPTION, root.IMAGE_DESCRIPTION,
			command=self._gen_description)
		GridSeparator(root, self.frame)
		GridLabel(root, self.frame, root.TO_DO, columnspan=3)
		StringRadiobuttons(root, self.frame, root.TO_DO,
			(root.CREATE_AND_VERIFY, root.VERIFY_FILE), root.CREATE_AND_VERIFY)
		GridLabel(root, self.frame, root.CREATE_AND_VERIFY, column=1, columnspan=2)
		FileSelector(root, self.frame,
			root.VERIFY_FILE, root.VERIFY_FILE, root.SELECT_VERIFY_FILE)
		GridSeparator(root, self.frame)
		Checker(root, self.frame, root.COPY_EXE, root.COPY_EXE, columnspan=2)
		GridSeparator(root, self.frame)
		GridButton(root, self.frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job, columnspan=3)
		self.root = root

	def _gen_name(self):
		'''Generate a name for the image'''
		if not self.name_str.string.get():
			self.name_str.string.set(Path(self.source_dir.source_str.get()).name)
	
	def _gen_description(self):
		'''Generate a description for the image'''
		if not self.descr_str.string.get():
			descr = TimeStamp.now(no_ms=True)
			source = self.source_dir.source_str.get()
			if source:
				descr += f', {Path(source).name}'
			self.descr_str.string.set(descr)

	def _error(self):
		'''Show error for missing entries'''
		showerror(
			title = self.root.MISSING_ENTRIES,
			message = self.root.SOURCED_DEST_REQUIRED
		)

	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		source = self.root.settings.get(self.root.SOURCE)
		outdir = self.root.settings.get(self.root.OUTDIR)
		filename = self.root.settings.get(self.root.FILENAME)
		to_do = self.root.settings.get(self.root.TO_DO)
		image = self.root.settings.get(self.root.VERIFY_FILE)
		cmd = self.root.settings.section.lower()
		if to_do == self.root.VERIFY_FILE:
			if not image:
				self._error()
				return
			cmd += f' --verify --{self.root.PATH.lower()} {image}'
			if not filename:
				filename = image.stem
			if not outdir and image:
				outdir = image.parent
		if not source or not outdir or not filename:
			self._error()
			return
		cmd += f' --{self.root.OUTDIR.lower()} "{outdir}"'
		cmd += f' --{self.root.FILENAME.lower()} "{filename}"'
		name = self.root.settings.get(self.root.IMAGE_NAME)
		if name:
			cmd += f' --name "{name}"'
		description = self.root.settings.get(self.root.IMAGE_DESCRIPTION)
		if description:
			cmd += f' --description "{description}"'
		if self.root.settings.get(self.root.COPY_EXE) == '1':
			cmd += ' --exe'
		cmd += f' "{source}"'
		self.root.append_job(cmd)

if __name__ == '__main__':	# start here if called as application
	app = AxCheckerCli()
	app.parse()
	app.run()
