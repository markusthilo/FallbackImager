#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'AxChecker'
__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-26'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Verify AXIOM case files
'''

from pathlib import Path
from argparse import ArgumentParser
from tkinter.messagebox import showerror
from lib.extpath import ExtPath
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.mfdbreader import MfdbReader
from lib.guielements import SourceDirSelector, Checker
from lib.guielements import ExpandedFrame, GridSeparator, GridLabel, DirSelector
from lib.guielements import FilenameSelector, StringSelector, StringRadiobuttons
from lib.guielements import FileSelector, GridButton

class AxChecker:
	'''Compare AXIOM case file / SQlite data base with paths'''

	def __init__(self, mfdb,
			filename = None,
			outdir = None,
			log = None,
			echo = print
		):
		'''Definitions'''
		self.mfdb_path = Path(mfdb)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
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

	def check_mfdb(self):
		'''Load content AXIOM case data base'''
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

	def diff_mfdb(self, diff, diff_type, partition=None):
		'''Compare Axiom Case'''
		diff_path = Path(diff)
		not_file_cnt = 0
		not_hit_cnt = 0
		if diff_path.is_dir():
			if diff_type != 'fs':
				self.log.error(f'{diff_path} is not a directory/possible root path')
			if len(self.mfdb.partitions) > 1:
				if not self.partition:
					self.log.error('Misssing root path')
				for part_id, partition in self.mfdb.get_partitions():
					if partition == self.partiton:
						break
			else:
				part_id = list(self.mfdb.partitions)[0]
			self.log.info('Comparing files in AXIOM to {diff_path.name}', echo=True)
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
				for path, norm_path in ExtPath.walk_normalized_files(diff_path):
					if norm_path in normalized_file_paths:
						source_id = normalized_file_paths[norm_path]
						if not source_id in self.mfdb.hit_ids:
							print(self.mfdb.paths[source_id], file=not_hits_fh)
							not_hit_cnt += 1
					else:
						print(path, file=not_files_fh)
						not_file_cnt += 1
		elif diff_type == 'tsv':
			self.log.error('Not implemented in this version: compare to TSV')
		else:
			if diff_type == 'fs':
				self.log.error(f'{diff_path} is not a directory/possible root path')
			else:
				self.log.error(f'Unknown option >{diff_type}<')
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
		self.add_argument('-d', '--diff', type=Path,
			help='Path to file or directory to compare with', metavar='FILE|DIRECTORY'
		)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-l', '--list', default=False, action='store_true',
			help='List images and partitions (ignores all other arguments)'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write generated missing files', metavar='DIRECTORY'
		)
		self.add_argument('-p', '--partition', type=str,
			help='Image and partiton to compare (--diff DIRECTORY)', metavar='STRING'
		)
		self.add_argument('-t', '--difftype', type=str, default='fs',
			choices=['fs', 'tsv'],
			help='How to compare, default is >fs< for file structure', metavar='STRING'
		)
		self.add_argument('mfdb', nargs=1, type=Path,
			help='AXIOM Case (.mfdb) / SQLite data base file', metavar='FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.mfdb = args.mfdb[0]
		self.diff = args.diff
		self.filename = args.filename
		self.list = args.list
		self.outdir = args.outdir
		self.partition = args.partition
		self.difftype = args.difftype

	def run(self, echo=print):
		'''Run AxChecker'''
		axchecker = AxChecker(self.mfdb,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo,
		)
		if self.list:
			axchecker.list_mfdb()
			return
		axchecker.check_mfdb()
		if self.diff:
			axchecker.diff_mfdb(self.diff, self.difftype, partition=self.partition)
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
			(root.DO_NOT_COMPARE, root.FILE_STRUCTURE), root.DO_NOT_COMPARE)
		GridLabel(root, self.frame, root.DO_NOT_COMPARE, column=1, columnspan=2)
		DirSelector(root, self.frame,
			root.FILE_STRUCTURE, root.FILE_STRUCTURE, root.ASK_FILE_STRUCTURE)
		GridSeparator(root, self.frame)
		GridSeparator(root, self.frame)
		GridButton(root, self.frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job, columnspan=3)
		self.root = root

	def _select_partition(self):
		'''Select partition in the AXIOM case'''
		pass

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
