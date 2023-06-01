#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'AxChecker'
__author__ = 'Markus Thilo'
__version__ = '0.0.4_2023-06-1'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Verify AXIOM case files
'''

from pathlib import Path
from argparse import ArgumentParser
from functools import partial
from tkinter import Toplevel, StringVar
from tkinter.ttk import Radiobutton, Button, Checkbutton
from tkinter.messagebox import showerror
from tkinter.scrolledtext import ScrolledText
from lib.extpath import ExtPath, FilesPercent
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.mfdbreader import MfdbReader
from lib.guielements import SourceDirSelector, Checker, LeftLabel
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
		self.partition = partition
		self.column = column
		self.nohead = nohead
		self.echo = echo
		self.log = log
		self.mfdb = MfdbReader(self.mfdb_path)

	def list_mfdb(self):
		'''List the images and partitions'''
		for partition in self.mfdb.get_partitions():
			self.echo(partition[1])

	def write_tsv_files(self, source_ids, type_str):
		'''Write TSV file by given iterable source_ids'''
		fh_dict = {source_id:
			ExtPath.child(
				f'{self.filename}_{type_str}_{partition}.txt',
				parent = self.outdir
			).open('w', encoding='utf-8') for source_id, partition in self.mfdb.get_partition_fnames()
		}
		for source_id in source_ids:
			print(f'{self.mfdb.short_paths[source_id][1]}',
				file = fh_dict[self.mfdb.short_paths[source_id][0]]
			)
		for fh in fh_dict.values():
			fh.close()

	def	_split_line(self, line):
		'''Splite line from, TSV file to list; line: str'''
		return [key.rstrip('\n') for key in line.split('\t')]

	def check(self):
		'''Check AXIOM case file'''
		if not self.log:
			self.log = Logger(filename=self.filename, outdir=self.outdir, 
				head='axchecker.AxChecker', echo=self.echo)
		self.log.info(f'Reading paths from {self.mfdb_path.name} and writing text files', echo=True)
		self.mfdb.fetch_paths()
		self.write_tsv_files(self.mfdb.file_ids, 'Files')
		self.write_tsv_files(self.mfdb.folder_ids, 'Folders')
		self.log.info(
			f'AXIOM processed {len(self.mfdb.file_ids)} file(s) and  {len(self.mfdb.folder_ids)} folder(s)',
			echo = True
		)
		if self.mfdb.ignored_file_ids:
			self.log.info('All file paths are represented in hits/artifacts', echo=True)
		else:
			self.write_tsv_files(self.mfdb.ignored_file_ids, 'Ignored')
			self.log.warning(f'Found {len(self.mfdb.ignored_file_ids)} ignored file path(s) not in hits/artifacts')
		if not self.diff_path:
			return
		if not self.partition:
			if len(self.mfdb.partitions) == 1:
				self.partition = list(self.mfdb.partitions.values())[0][1]
			else:
				self.log.error('Misssing partition/root path')
		if len(self.mfdb.partitions) > 1:
			for part_id, partition in self.mfdb.get_partitions():
				if partition == self.partition:
					break
		else:
			part_id = list(self.mfdb.partitions)[0]
		self.log.info('Comparing files in AXIOM to {self.diff_path.name}', echo=True)
		not_file_cnt = 0
		not_hit_cnt = 0
		if self.diff_path.is_dir():	# compare to dir
			file_paths = {self.mfdb.short_paths[source_id][1]: source_id
				for source_id in self.mfdb.file_ids
				if self.mfdb.short_paths[source_id][0] == part_id
			}
			progress = FilesPercent(self.diff_path, echo=self.echo)
			with (
				ExtPath.child(f'{self.filename}_not_in_files.txt',
					parent=self.outdir).open('w') as not_files_fh,
				ExtPath.child(f'{self.filename}_not_in_artifacts.txt',
					parent=self.outdir).open('w') as not_hits_fh
			):
				for path, relative_path in ExtPath.walk_files(self.diff_path):
					progress.inc()
					if ExtPath.windowize(relative_path) in file_paths:
						source_id = file_paths[relative_path]
						if not source_id in self.mfdb.hit_ids:
							print(self.mfdb.paths[source_id], file=not_hits_fh)
							not_hit_cnt += 1
					else:
						print(path, file=not_files_fh)
						not_file_cnt += 1
		elif self.diff_path.is_file:	# compare to file
			column = None
			head, encoding = ExtPath.read_head(self.diff_path)
			cols = head.split('\t')
			tsv_fields_len = len(cols)
			if tsv_fields_len == 1:
				column = 0
			else:
				try:
					column = int(self.column)-1
				except (ValueError, TypeError):
					if self.nohead:
						self.log.error('Unable to determin column with paths to compare')
					for column, col_str in enumerate(cols):
						if col_str == self.column:
							break
			if column < 0 or column >= tsv_fields_len:
				self.log.error('Column out of range')
			normalized_paths = {ExtPath.normalize(self.mfdb.short_paths[source_id][1]): source_id
				for source_id, path in self.mfdb.short_paths.items()
				if self.mfdb.short_paths[source_id][0] == part_id
			}
			with (
				ExtPath.child(f'{self.filename}_diff_paths.txt',
					parent=self.outdir).open('w', encoding=encoding) as diff_paths_fh,
				ExtPath.child(f'{self.filename}_diff_artifacts.txt',
					parent=self.outdir).open('w', encoding=encoding) as diff_hits_fh,
				self.diff_path.open('r', encoding=encoding) as diff_fh
			):
				if not self.nohead:
					line = diff_fh.readline()
					diff_paths_fh.write(line)
					diff_hits_fh.write(line)
				for line in diff_fh:
					fields = self._split_line(line)
					if len(fields) < tsv_fields_len:
						line = line.rstrip('\n')
						fields = self._split_line(f'{line} {next(diff_fh)}')
					try:
						path = ExtPath.normalize(fields[column])
					except IndexError:
						self.log.error(f'Found unprocessable line in {diff_path.name}:\n{line}')
					if path in normalized_paths:
						source_id = normalized_paths[path]
						if source_id in self.mfdb.hit_ids:
							continue
						diff_hits_fh.write(line)
						not_hit_cnt += 1
					else:
						diff_paths_fh.write(line)
						not_file_cnt += 1
		else:
			self.log.error(f'Unable to read/open {diff_path.name}')
		if not_file_cnt == 0 and not_hit_cnt == 0:
			self.log.info(f'All {len(self.mfdb.file_ids)} file paths were found in the AXIOM artifacts')
		else:
			msg = 'Not every file path is represented in the AXIOM artifacts\n'
			msg += f'Completely missing in AXIOM: {not_file_cnt}\n'
			msg += f'Not represented in the artifacts but present in the case file: {not_hit_cnt}\n'
			self.log.warning(msg)

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
			help='Directory to write generated missing files', metavar='DIRECTORY'
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
			axchecker.list_mfdb()
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
		self.partition_window = None
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
		self.column_window = None
		Checker(root, frame, root.TSV_NO_HEAD, root.TSV_NO_HEAD, column=1)
		GridSeparator(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job, columnspan=3)
		self.root = root

	def _child_window(self, title):
		'''Open child window to root'''
		window = Toplevel(self.root)
		window.title(title)
		window.resizable(0, 0)
		window.iconbitmap(self.root.icon_path)
		return window

	def _select_partition(self):
		'''Select partition in the AXIOM case'''
		if self.partition_window:
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
			self.root.settings.raw(self.root.PARTITION).set(list(mfdb.partitions.values())[0][1])
			return
		self.partition_window = self._child_window(self.root.SELECT_PARTITION)
		self.partition_window.protocol('WM_DELETE_WINDOW', self._destroy_partition_window)
		self._selected_part = StringVar()
		for partition in mfdb.partitions.values():
			frame = ExpandedFrame(self.root, self.partition_window)
			Radiobutton(frame, variable=self._selected_part, value=partition).pack(
				side='left', padx=self.root.PAD)
			LeftLabel(self.root, frame, partition)
		frame = ExpandedFrame(self.root, self.partition_window)
		LeftButton(self.root, frame, self.root.SELECT, self._get_partition)
		RightButton(self.root, frame, self.root.QUIT, _destroy_partition_window)
		self.partition_window = None

	def _destroy_partition_window(self):
		'''Destroy the child window'''
		self.partition_window.destroy()
		self.partition_window = None

	def _get_partition(self):
		'''Get the selected partition'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.PARTITION).set(self._selected_part.get())
		self._destroy_partition_window()

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
		if self.column_window:
			return
		self.root.settings.section = self.CMD
		tsv = self.root.settings.get(self.root.TSV)
		if tsv:
			head, encoding = ExtPath.read_head(Path(tsv), after=self.root.MAX_ROW_QUANT-1)
			if len(head) < 2:
				tsv = None
		if not tsv:
			showerror(
				title = self.root.TSV,
				message = self.root.FIRST_CHOOSE_TSV
			)
			return
		self.root.settings.raw(self.root.VERIFY_FILE).set(self.root.TSV)
		if len(head[0].split('\t')) == 1:
			self.root.settings.raw(self.root.COLUMN).set('1')
			return
		self.column_window = self._child_window(self.root.SELECT_COLUMN)
		self.column_window.protocol('WM_DELETE_WINDOW', self._destroy_column_window)
		self._selected_column = StringVar()
		frame = ExpandedFrame(self.root, self.column_window)
		preview = {(row, column): entry
			for row, line in enumerate(head)
			for column, entry in enumerate(line.split('\t'))
		}
		entry_heights = [0]*self.root.MAX_ROW_QUANT
		for row in range(self.root.MAX_ROW_QUANT):
			for column in range(self.root.MAX_COLUMN_QUANT):
				try:
					entry_heights[row] = max(
						entry_heights[row],
						min(int(len(preview[row, column])/self.root.MAX_ENTRY_WIDTH)+1,
							self.root.MAX_ENTRY_HEIGHT)
					)
				except KeyError:
					break
		entry_widths = [self.root.MIN_ENTRY_WIDTH]*self.root.MAX_COLUMN_QUANT
		for column in range(self.root.MAX_COLUMN_QUANT):
			for row in range(self.root.MAX_ROW_QUANT):
				try:
					entry_widths[column] = max(
						entry_widths[column],
						min(len(preview[row, column]), self.root.MAX_ENTRY_WIDTH)
					)
				except KeyError:
					break
		for row, height in enumerate(entry_heights):
			for column, width in enumerate(entry_widths):
				try:
					entry = preview[row, column]
				except KeyError:
					break
				text = ScrolledText(frame, width=width, height=height)
				text.grid(row=row, column=column)
				text.bind('<Key>', lambda dummy: 'break')
				text.insert('end', preview[row, column])
				text.configure(state='disabled')
		print(row, column)
		row += 1
		for column in range(column):
			Button(frame,
				text = f'{column+1}',
				command = partial(self._get_column, column+1)
			).grid(row=row, column=column, padx=self.root.PAD, pady=self.root.PAD)
		frame = ExpandedFrame(self.root, self.column_window)
		Checkbutton(frame,
			text = self.root.TSV_NO_HEAD,
			variable = self.root.settings.raw(self.root.TSV_NO_HEAD)
		).pack(side='left', padx=self.root.PAD)
		RightButton(self.root, frame, self.root.QUIT, self._destroy_column_window)

	def _destroy_column_window(self):
		'''Destroy the child window'''
		self.column_window.destroy()
		self.column_window = None

	def _get_column(self, column):
		'''Get the selected column'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.COLUMN).set(f'{column}')
		self._destroy_column_window()

	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		mfdb = self.root.settings.get(self.root.CASE_FILE)
		partition = self.root.settings.get(self.root.PARTITION)
		if not mfdb or not partition:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.CASE_AND_PARTITION_REQUIRED
			)
			return
		outdir = self.root.settings.get(self.root.OUTDIR) 
		verify = self.root.settings.get(self.root.VERIFY_FILE)
		filename = self.root.settings.get(self.root.FILENAME)
		file_structure = self.root.settings.get(self.root.FILE_STRUCTURE)
		tsv = self.root.settings.get(self.root.TSV)
		column = self.root.settings.get(self.root.COLUMN)
		cmd = self.root.settings.section.lower()
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