#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'AxChecker'
__author__ = 'Markus Thilo'
__version__ = '0.0.2_2023-05-28'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Verify AXIOM case files
'''

from pathlib import Path
from argparse import ArgumentParser
from tkinter import Toplevel, StringVar
from tkinter.ttk import Radiobutton
from tkinter.messagebox import showerror
from lib.extpath import ExtPath
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
			).open('w') for source_id, partition in self.mfdb.get_partition_fnames()
		}
		for source_id in source_ids:
			print(f'{self.mfdb.short_paths[source_id][1]}',
				file = fh_dict[self.mfdb.short_paths[source_id][0]]
			)
		for fh in fh_dict.values():
			fh.close()

	def	_split_line(self, line):
		'''Splite line from, TSV file to list; line: str'''
		return [key.strip() for key in line.split('\t')]

	def check(self):
		'''Check AXIOM case file'''
		if not self.log:
			self.log = Logger(filename=self.filename, outdir=self.outdir, 
				head='axchecker.AxChecker', echo=self.echo)
		self.log.info(f'Reading paths from {self.mfdb_path.name} and writing text files', echo=True)
		self.mfdb.fetch_paths()
		self.write_tsv_files(self.mfdb.file_ids, 'Files')
		self.write_tsv_files(self.mfdb.folder_ids, 'Folders')
		if self.mfdb.ignored_file_ids:
			self.log.info('All file paths are represented in hits/artifacts', echo=True)
		else:
			self.write_tsv_files(self.mfdb.ignored_file_ids, 'Ignored')
			self.log.warning('Found ignored file paths that are not in hits/artifacts')
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
		if self.diff_path.is_dir():
			normalized_file_paths = {self.mfdb.normalized_path(source_id): source_id
				for source_id in self.mfdb.file_ids
				if self.mfdb.short_paths[source_id][0] == part_id
			}
			with (
				ExtPath.child(f'{self.filename}_not_in_files.txt',
					parent=self.outdir).open('w') as not_files_fh,
				ExtPath.child(f'{self.filename}_not_in_artifacts.txt',
					parent=self.outdir).open('w') as not_hits_fh
			):
				for path, norm_path in ExtPath.walk_normalized_files(self.diff_path):
					if norm_path in normalized_file_paths:
						source_id = normalized_file_paths[norm_path]
						if not source_id in self.mfdb.hit_ids:
							print(self.mfdb.paths[source_id], file=not_hits_fh)
							not_hit_cnt += 1
					else:
						print(path, file=not_files_fh)
						not_file_cnt += 1
		elif self.diff_path.is_file:
			column = None
			for codec in 'utf-32', 'utf-16', 'utf-8':
				try:
					with self.diff_path.open('r', encoding=codec) as diff_fh:
						first = diff_fh.readline()
						break
				except UnicodeDecodeError:
					continue
			cols = first.split('\t')
			tsv_fields_len = len(cols)
			if tsv_fields_len == 1:
				column = 0
			else:
				try:
					column = int(self.column)-1
				except ValueError:
					if self.nohead:
						self.log.error('Unable to determin column with paths to compare')
					for column, col_str in enumerate(cols):
						if col_str == self.column:
							break
			if column < 0 or column >= tsv_fields_len:
				self.log.error('Column out of range')
			normalized_paths = {self.mfdb.normalized_path(source_id): source_id
				for source_id, path in self.mfdb.short_paths.items()
				if self.mfdb.short_paths[source_id][0] == part_id
			}
			with (
				ExtPath.child(f'{self.filename}_diff_paths.txt',
					parent=self.outdir).open('w') as diff_paths_fh,
				ExtPath.child(f'{self.filename}_diff_artifacts.txt',
					parent=self.outdir).open('w') as diff_hits_fh,
				self.diff_path.open('r', encoding=codec) as diff_fh
			):
				if not self.nohead:
					line = diff_fh.readline()
					diff_paths_fh.write(line)
					diff_hits_fh.write(line)
				for line in diff_fh:
					fields = self._split_line(line)
					if len(fields) < tsv_fields_len:
						fields.extend(self._split_line(next(self.tsv_file)))
					try:
						path = fields[column].replace('\\', '/').strip()
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
		self.frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(self.frame, text=f' {self.CMD} ')
		root.row = 0
		GridSeparator(root, self.frame)
		GridLabel(root, self.frame, root.AXIOM, columnspan=3)
		FileSelector(root, self.frame, root.CASE_FILE, root.CASE_FILE,
			f'{root.OPEN_CASE_FILE} ({root.AXIOM_CASE_FILE})',
			filetype=(root.CASE_FILE, root.AXIOM_CASE_FILE))
		StringSelector(root, self.frame, root.PARTITION, root.PARTITION,
			command=self._select_partition)		
		GridSeparator(root, self.frame)
		GridLabel(root, self.frame, root.DESTINATION, columnspan=2)
		self.filename_str = FilenameSelector(root, self.frame, root.FILENAME, root.FILENAME)
		DirSelector(root, self.frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		GridSeparator(root, self.frame)
		GridLabel(root, self.frame, root.VERIFY_FILE, columnspan=2)
		StringRadiobuttons(root, self.frame, root.VERIFY_FILE,
			(root.DO_NOT_COMPARE, root.FILE_STRUCTURE, root.TSV), root.DO_NOT_COMPARE)
		GridLabel(root, self.frame, root.DO_NOT_COMPARE, column=1, columnspan=2)
		DirSelector(root, self.frame, root.FILE_STRUCTURE, root.FILE_STRUCTURE, root.SELECT_FILE_STRUCTURE)
		FileSelector(root, self.frame, root.TSV, root.TSV, root.SELECT_TSV)
		StringSelector(root, self.frame, root.COLUMN, root.COLUMN)
		Checker(root, self.frame, root.TSV_NO_HEAD, root.TSV_NO_HEAD, column=1)
		GridSeparator(root, self.frame)
		GridButton(root, self.frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job, columnspan=3)
		self.root = root

	def _select_partition(self):
		'''Select partition in the AXIOM case'''
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
		self.window = Toplevel(self.root)
		self.window.title(self.root.SELECT_PARTITION)
		self.window.resizable(0, 0)
		self.window.iconbitmap(self.root.icon_path)
		self._selected_part = StringVar()
		for partition in mfdb.partitions.values():
			frame = ExpandedFrame(self.root, self.window)
			Radiobutton(frame, variable=self._selected_part, value=partition).pack(
				side='left', padx=self.root.PAD)
			LeftLabel(self.root, frame, partition)
		frame = ExpandedFrame(self.root, self.window)
		LeftButton(self.root, frame, self.root.SELECT, self._get_partition)
		RightButton(self.root, frame, self.root.QUIT, self.window.destroy)

	def _get_partition(self):
		'''Get the selected partition'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.PARTITION).set(self._selected_part.get())
		self.window.destroy()

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
