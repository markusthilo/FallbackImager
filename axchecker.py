#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'AxChecker'
__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-24'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Verify AXIOM case files
'''

from pathlib import Path, PurePath
from argparse import ArgumentParser
from re import compile as regcompile
from tkinter.messagebox import showerror
from lib.extpath import ExtPath
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.greplists import GrepLists
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
		if log:
			self.log = log
		else:
			self.log = Logger(filename=self.filename, outdir=self.outdir, 
				head='axchecker.AxChecker', echo=echo)

	def open_tsv(self, type_str):
		'''Open file handlers for one TSV file per partition'''
		reg = regcompile(' (\([^\)]*\) )|([ *.;:#"/\\\])')
		return {partition:
			ExtPath.child(
				f'{self.filename}_{type_str}_{reg.sub("_", partition)}.txt',
				parent = self.outdir
			).open('w') for partition in self.partitions.values()
		}

	def write_tsv(self, source_ids, fh_dict):
		'''Write TSV file by given iterable source_ids'''
		for source_id in source_ids:
			print(
				f'{source_id}\t{self.id_with_partition[source_id]}\t{self.short_paths[source_id]}',
				file = fh_dict[self.id_with_partition[source_id]]
			)

	def close_tsv(self, fh_dict):
		'''Close file handlers in dict (values)'''
		for fh in fh_dict.values():
			fh.close()

	def check_mfdb(self):
		'''Load content AXIOM case data base'''
		self.log.info(f'Reading {self.mfdb_path.name}', echo=True)
		db = MfdbReader(self.mfdb_path)
		'''
		db = SQLiteReader(self.mfdb_path)
		self.paths = {source_id: source_path
			for source_id, source_path in db.fetch_table('source_path',
				fields = ('source_id', 'source_path')
			)
		}
		self.images = {source_id: self.paths[source_id]
			for source_id in db.fetch_table('source',
				fields = 'source_id',
				where = ('source_type', 'Image')
			)
		}
		self.partitions = {source_id: self.paths[source_id]
			for source_id in db.fetch_table('source',
				fields = 'source_id',
				where = ('source_type', 'Partition')
			)
		}
		self.files = {source_id: self.paths[source_id]
			for source_id in db.fetch_table('source',
				fields = 'source_id',
				where = ('source_type', 'File')
			)
		}
		self.folders = {source_id: self.paths[source_id]
			for source_id in db.fetch_table('source',
				fields = 'source_id',
				where = ('source_type', 'Folder')
			)
		}
		self.hits = {source_id: self.paths[source_id]
			for source_id in db.fetch_table('hit_location',
				fields = 'source_id'
			)
		}
		self.log.info(f'Closing file handler for {self.mfdb_path.name}', echo=True)
		db.close()
		self.file_ids = set(self.files)
		self.folder_ids = set(self.folders)
		self.hit_ids = set(self.hits)
		self.id_with_partition = dict()
		self.short_paths = dict()
		self.ignored_file_ids = self.file_ids-self.hit_ids
		for part_path in self.partitions.values():
			part_len = len(part_path)
			for source_id, path in self.paths.items():
				if path.startswith(part_path):
					self.id_with_partition[source_id] = part_path
					self.short_paths[source_id] = path[part_len:]
		fh_dict = self.open_tsv('Files')
		self.write_tsv(self.file_ids, fh_dict)
		self.close_tsv(fh_dict)
		fh_dict = self.open_tsv('Folders')
		self.write_tsv(self.folder_ids, fh_dict)
		self.close_tsv(fh_dict)
		if self.ignored_file_ids:
			self.log.info('All falle paths represented in hits/artifacts', echo=True)
		else:
			fh_dict = self.open_tsv('Ignored')
			self.write(self.ignored_file_ids, fh_dict)
			self.close_tsv(fh_dict)
			self.log.warning('Ignored file paths that are not in hits/artifacts')

		
		
		self.file_ids = set(self.files)
		self.folder_ids = set(self.folders)
		self.hit_ids = set(self.hits)
		self.id_with_partition = dict()
		self.short_paths = dict()
		self.ignored_file_ids = self.file_ids-self.hit_ids
		for part_path in self.partitions.values():
			part_len = len(part_path)
			for source_id, path in self.paths.items():
				if path.startswith(part_path):
					self.id_with_partition[source_id] = part_path
					self.short_paths[source_id] = path[part_len:]
		fh_dict = self.open_tsv('Files')
		self.write_tsv(self.file_ids, fh_dict)
		self.close_tsv(fh_dict)
		fh_dict = self.open_tsv('Folders')
		self.write_tsv(self.folder_ids, fh_dict)
		self.close_tsv(fh_dict)
		if self.ignored_file_ids:
			self.log.info('All falle paths represented in hits/artifacts', echo=True)
		else:
			fh_dict = self.open_tsv('Ignored')
			self.write(self.ignored_file_ids, fh_dict)
			self.close_tsv(fh_dict)
			self.log.warning('Ignored file paths that are not in hits/artifacts')
		'''

	def diff_mfdb(self, diff, diff_type, drop = GrepLists.false):
		'''Compare Axiom Case'''
		diff_path = Path(diff)
		if diff_path.is_dir():
			if diff_type != 'fs':
				raise ValueError('A source file system is required for option >fs<')

			for path, file_str in ExtPath.walk_files(diff_path):
				print(path, file_str)
			
			
			
		elif diff_type == 'tsv':
			print('TSV diff to come...')
		else:
			raise NotImplementedError(f'Unknown option >{diff_type}<')

class AxCheckerCli(ArgumentParser):
	'''CLI, also used for GUI of FallbackImager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-b', '--blacklist', type=Path,
			help='Blacklist (textfile with one regex per line)', metavar='FILE'
		)
		self.add_argument('-d', '--diff', type=Path,
			help='Path to file or directory to compare with', metavar='FILE|DIRECTORY'
		)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write generated missing files', metavar='DIRECTORY'
		)
		
		self.add_argument('-t', '--difftype', type=str, default='fs',
			choices=['fs', 'tsv'],
			help='How to compare, default is >fs< for file structure', metavar='STRING'
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
		axchecker = AxChecker(self.mfdb,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo,
		)
		axchecker.check_mfdb()
		if self.diff:
			drop = GrepLists(
			blacklist = self.blacklist,
			whitelist = self.whitelist, 
			echo = echo
			).get_method()
			axchecker.diff_mfdb(self.diff, self.difftype,
				drop = GrepLists(
					blacklist = self.blacklist,
					whitelist = self.whitelist, 
					echo = echo
				).get_method()
			)
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
