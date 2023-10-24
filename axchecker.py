#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'AxChecker'
__author__ = 'Markus Thilo'
__version__ = '0.2.2_2023-10-22'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Verify AXIOM case files
Output directory and filename (base for the generetad files, do extension) are required.
-l/--list lists the partitions contained in the AXIOM case file.
To compare to a file structure, give the partition with -p/--partition,
e.g. "Test-SD.E01 - Entire Disk (exFAT, 1,86 GB) Test-SD".
When a text file is given by -d/--diff, the tool handles the content as a file list
and tries to compare it to the given AXIOM partition from "Case.mfdb".
-c/--column has to point to the paths if the text file is in TSV format,
e.g. "Full path" for TSV file generated with X-Ways (German: "Vollpfad").
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
from lib.guielements import SourceDirSelector, Checker, LeftLabel
from lib.guielements import ChildWindow, SelectTsvColumn, GridBlank
from lib.guielements import ExpandedFrame, GridSeparator, GridLabel, DirSelector
from lib.guielements import FilenameSelector, StringSelector, StringRadiobuttons
from lib.guielements import FileSelector, GridButton, LeftButton, RightButton

class AxChecker:
	'''Compare AXIOM case file / SQlite data base with paths'''

	def __init__(self, mfdb,
			filename = None,
			outdir = None,
			diff = None,
			partition = None,
			column = None,
			nohead = False,
			log = None,
			echo = print
		):
		'''Definitions'''
		self.mfdb_path = Path(mfdb)
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
		self.log = log

	def list_partitions(self):
		'''List the partitions'''
		self.mfdb = MfdbReader(self.mfdb_path)
		for n, partition in enumerate(self.mfdb.partitions.values(), start=1):
			self.echo(f'{n}: {partition}')

	def check(self):
		'''Check AXIOM case file'''
		if not self.log:
			self.log = Logger(filename=self.filename, outdir=self.outdir, 
				head='axchecker.AxChecker', echo=self.echo)
		self.log.info(f'Reading {self.mfdb_path.name}', echo=True)
		self.mfdb = MfdbReader(self.mfdb_path)
		self.all_partitions = list(self.mfdb.partitions.values())
		msg = f'AXIOM case contains {len(self.all_partitions)} partitions,'
		msg += f' {len(self.mfdb.files)} file paths and {len(self.mfdb.hits)} hits'
		self.log.info(msg, echo=True)
		if self.partition:
			if isinstance(self.partition, int):
				try:
					self.partition = self.all_partitions[self.partition-1]
				except IndexError:
					self.log.error(f'Only {len(self.all_partitions)} partition(s) in AXIOM case file')
			elif not self.partition in self.all_partitions:
				self.log.error(f'Unable to find partiton "{self.partition}" in AXIOM case file')
			self.log.info('Dropping file paths in unselected partitions', echo=True)
			self.mfdb.files = self.mfdb.get_files_of_partition(self.partition)
			self.log.info('Checking files of {self.partition}', echo=True)
		else:
			self.log.info('Writing partitions', echo=True)
			with ExtPath.child(f'{self.filename}_partitions.txt', parent=self.outdir
				).open(mode='w', encoding='utf-8') as fh:
				for partition in self.all_partitions:
					print(partition, file=fh)
		msg = f'Writing {len(self.mfdb.files)} file paths of '
		if self.partition:
			msg += f'partition {self.partition}'
		else:
			msg += 'entire case file'
		self.log.info(msg, echo=True)
		with ExtPath.child(f'{self.filename}_files.txt', parent=self.outdir
			).open(mode='w', encoding='utf-8') as fh:
			for source_path in self.mfdb.files.values():
				print(source_path, file=fh)
		no_hit_files = self.mfdb.get_no_hit_files()
		if no_hit_files:
			msg = f'{len(no_hit_files)} file(s) is/are not represented in hits,'
			msg += ' writing list'
			self.log.info(msg, echo=True)
			with ExtPath.child(f'{self.filename}_not_in_hits.txt', parent=self.outdir
			).open(mode='w', encoding='utf-8') as fh:
				for source_path in no_hit_files.values():
					print(source_path, file=fh)
		if not self.diff_path:	# end here if nothing to compare is given
			self.log.info('Done', echo=True)
			return
		if not self.partition:
			if len(self.all_partitions) == 1:
				self.partition = self.all_partitions[0]
			else:
				self.log.error('Misssing partition to compare')
		self.log.info(
			f'Comparing AXIOM partition {self.partition} to {self.diff_path.name}',
			echo=True)
		len_partition = len(self.partition)
		files_short_paths = {source_path[len_partition:]
			for source_path in self.mfdb.files.values()
		}
		missing_cnt = 0
		if self.diff_path.is_dir():	# compare to dir
			progress = FilesPercent(self.diff_path, echo=self.echo)
			with ExtPath.child(f'{self.filename}_missing_files.txt', parent=self.outdir
				).open(mode='w', encoding='utf-8') as fh:
				for absolut_path, relative_path in ExtPath.walk_files(self.diff_path):
					progress.inc()
					path = ExtPath.windowize(relative_path)
					if not path in files_short_paths:
						print(absolut_path, file=fh)
						missing_cnt += 1
		elif self.diff_path.is_file:	# compare to file
			tsv = TsvReader(self.diff_path, column=self.column, nohead=self.nohead)
			if tsv.column < 0:
				self.log.error('Column out of range/undetected')
			self.echo(f'Processing {self.diff_path}')
			with ExtPath.child(f'{self.filename}_missing_files.txt', parent=self.outdir
				).open(mode='w', encoding='utf-8') as fh:
				if not self.nohead:
					print(tsv.head, file=fh)
				for full_path, line in tsv.read_lines():
					path = ExtPath.normalize(full_path)
					if not path in files_short_paths:
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
		self.add_argument('-d', '--diff', type=Path,
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
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write log and CSV list(s)', metavar='DIRECTORY'
		)
		self.add_argument('-p', '--partition', type=str,
			help='Image and partiton to compare (--diff DIRECTORY)', metavar='STRING'
		)
		self.add_argument('mfdb', nargs=1, type=Path,
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
		axchecker = AxChecker(self.mfdb,
			filename = self.filename,
			outdir = self.outdir,
			diff = self.diff,
			column = self.column,
			nohead = self.nohead,
			partition = self.partition,
			echo = echo,
		)
		if self.list:
			axchecker.list_partitions()
			return
		axchecker.check()
		axchecker.log.close()

class AxCheckerGui:
	'''Notebook page'''

	CMD = __app_name__
	DESCRIPTION = __description__

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		GridSeparator(root, frame)
		GridLabel(root, frame, root.AXIOM, columnspan=3)
		FileSelector(root, frame, root.CASE_FILE, root.CASE_FILE,
			f'{root.OPEN_CASE_FILE} ({root.AXIOM_CASE_FILE})',
			filetype=(root.CASE_FILE, root.AXIOM_CASE_FILE))
		StringSelector(root, frame, root.PARTITION, root.PARTITION,
			command=self._select_partition)	
		GridSeparator(root, frame)
		GridLabel(root, frame, root.DESTINATION, columnspan=2)
		self.filename_str = FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
		DirSelector(root, frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		GridSeparator(root, frame)
		GridLabel(root, frame, root.VERIFY_FILE, columnspan=2)
		StringRadiobuttons(root, frame, root.VERIFY_FILE,
			(root.DO_NOT_COMPARE, root.FILE_STRUCTURE, root.TSV), root.DO_NOT_COMPARE)
		GridLabel(root, frame, root.DO_NOT_COMPARE, column=1, columnspan=2)
		DirSelector(root, frame, root.FILE_STRUCTURE, root.FILE_STRUCTURE, root.SELECT_FILE_STRUCTURE,
			command=self._select_file_structure)
		FileSelector(root, frame, root.TSV, root.TSV, root.SELECT_TSV,
			command=self._select_tsv_file)
		StringSelector(root, frame, root.COLUMN, root.COLUMN, command=self._select_column)
		Checker(root, frame, root.TSV_NO_HEAD, root.TSV_NO_HEAD, column=1)
		GridSeparator(root, frame)
		GridBlank(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}',
			self._add_job, column=0, columnspan=3)
		root.child_win_active = False
		self.root = root

	def _select_partition(self):
		'''Select partition in the AXIOM case'''
		if self.root.child_win_active:
			return
		self.root.settings.section = self.CMD
		mfdb = self.root.settings.get(self.root.CASE_FILE)
		if not mfdb:
			showerror(
				title = self.root.CASE_FILE,
				message = self.root.FIRST_CHOOSE_CASE
			)
			return
		mfdb = MfdbReader(Path(mfdb))
		if not mfdb.partitions:
			showerror(
				title = self.root.CASE_FILE,
				message = self.root.UNABLE_DETECT_PARTITIONS
			)
			return
		if len(mfdb.partitions) == 1:
			self.root.settings.raw(self.root.PARTITION).set(list(mfdb.partitions.values())[0])
			return
		self.partition_window = ChildWindow(self.root, self.root.SELECT_PARTITION)
		self._selected_part = StringVar()
		for partition in mfdb.partitions.values():
			frame = ExpandedFrame(self.root, self.partition_window)
			Radiobutton(frame, variable=self._selected_part, value=partition).pack(
				side='left', padx=self.root.PAD)
			LeftLabel(self.root, frame, partition)
		frame = ExpandedFrame(self.root, self.partition_window)
		LeftButton(self.root, frame, self.root.SELECT, self._get_partition)
		RightButton(self.root, frame, self.root.QUIT, self.partition_window.destroy)

	def _get_partition(self):
		'''Get the selected partition'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.PARTITION).set(self._selected_part.get())
		self.partition_window.destroy()

	def _select_file_structure(self):
		'''Select file structure to compare'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.VERIFY_FILE).set(self.root.FILE_STRUCTURE)

	def _select_tsv_file(self):
		'''Select TSV file to compare'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.VERIFY_FILE).set(self.root.TSV)

	def _select_column(self):
		'''Select column in TSV file to compare'''
		SelectTsvColumn(self.root, self.CMD)

	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		mfdb = self.root.settings.get(self.root.CASE_FILE)
		partition = self.root.settings.get(self.root.PARTITION)
		if not mfdb:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.CASE_REQUIRED
			)
			return
		outdir = self.root.settings.get(self.root.OUTDIR) 
		filename = self.root.settings.get(self.root.FILENAME)
		if not outdir:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.DEST_DIR_REQUIRED
			)
			return
		if not filename:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.DEST_FN_REQUIRED
			)
			return
		verify = self.root.settings.get(self.root.VERIFY_FILE)
		if not partition and verify != self.root.DO_NOT_COMPARE:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.PARTITION_REQUIRED
			)
			return
		file_structure = self.root.settings.get(self.root.FILE_STRUCTURE)
		tsv = self.root.settings.get(self.root.TSV)
		column = self.root.settings.get(self.root.COLUMN)
		cmd = self.root.settings.section.lower()
		cmd += f' --partition "{partition}"'
		cmd += f' --{self.root.OUTDIR.lower()} "{outdir}"'
		cmd += f' --{self.root.FILENAME.lower()} "{filename}"'
		if verify == self.root.FILE_STRUCTURE:
			if not file_structure:
				showerror(
					title = self.root.MISSING_ENTRIES,
					message = self.root.ROOT_DIR_REQUIRED
				)
				return
			cmd += f' --diff "{file_structure}"'
		elif verify == self.root.TSV:
			if not tsv or not column:
				showerror(
					title = self.root.MISSING_ENTRIES,
					message = self.root.TSV_AND_COL_REQUIRED
					)
				return
			cmd += f' --diff "{tsv}" --column {column}'
			if self.root.settings.get(self.root.TSV_NO_HEAD) == '1':
				cmd += ' --nohead'
		cmd += f' "{mfdb}"'
		self.root.append_job(cmd)

if __name__ == '__main__':	# start here if called as application
	app = AxCheckerCli()
	app.parse()
	app.run()