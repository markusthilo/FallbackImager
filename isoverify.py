#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'IsoVerify'
__author__ = 'Markus Thilo'
__version__ = '0.2.2_2023-11-20'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Compare ISO image (UDF) to file structure
'''

from pathlib import Path
from pycdlib import PyCdlib
from argparse import ArgumentParser
from tkinter.messagebox import showerror
from lib.greplists import GrepLists
from lib.extpath import ExtPath, FilesPercent
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.hashes import FileHashes
from lib.fsreader import FsReader
from lib.guielements import ExpandedFrame, SourceDirSelector, GridSeparator, GridLabel
from lib.guielements import FilenameSelector, DirSelector, FileSelector
from lib.guielements import StringRadiobuttons, GridButton, GridBlank

class IsoReader(PyCdlib):
	'''Use PyCdlib to get UDF from ISO'''

	def __init__(self, path):
		'''Get UDF fyle system structure, files and dirs'''
		self.path = path
		super().__init__()
		self.open(self.path)
		self.files_posix = set()
		self.dirs_posix = set()
		for root, dirs, files in self.walk(udf_path='/'):
			for name in dirs:
				self.dirs_posix.add('/'+f'{root}/{name}'.strip('/')+'/')
			for name in files:
				self.files_posix.add('/'+f'{root}/{name}'.strip('/'))
		self.close()

class CompareIsoFs:
	'''Compare ISO/UDF to file structure'''

	def __init__(self, root, image, drop=GrepLists.false, echo=print):
		'''Compare image to source file structure by Posix paths'''
		self.root_path = Path(root)
		echo(f'Getting structure of {self.root_path}')
		self.source = FsReader(self.root_path)
		self.source_posix = self.source.get_posix()
		self.image_path = Path(image)
		echo(f'Reading UDF from {self.image_path}')
		self.image = IsoReader(self.image_path)
		self.image_posix = self.image.get_udf()
		self.image.close()
		echo('Comparing file paths')
		self.delta_posix = list(set(self.source_posix)-set(self.image_posix))
		self.delta_posix.sort()
		self.dropped_posix = list()
		self.missing_posix = list()
		for posix in self.delta_posix:
			if drop(posix):
				self.dropped_posix.append(posix)
			else:
				self.missing_posix.append(posix)

class IsoVerify:
	'''Verification'''
 
	def __init__(self, root,
		imagepath = None,
		drop = GrepLists.false,
		filename = None,
		outdir = None,
		echo = print,
		log = None,
	):
		'''Set paths, logs etc.'''
		self.root_path = Path(root)
		self.drop = drop
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		if imagepath:
			self.image_path = Path(imagepath)
		else:
			self.image_path = ExtPath.child(f'{self.filename}.iso', parent=self.outdir)
		self.echo = echo
		if log:
			self.log = log
		else:
			self.log = Logger(filename=self.filename, outdir=self.outdir, 
				head=f'isoverify.IsoVerify', echo=echo)

	def posix_verify(self):
		'''Verify by Posix paths'''
		self.log.info(f'Reading UDF file system from {self.image_path}', echo=True)
		iso = IsoReader(self.image_path)
		with ExtPath.child(f'{self.filename}_content.txt', parent=self.outdir).open('w') as fh:
			fh.write('\n'.join(sorted(list(iso.dirs_posix|iso.files_posix))))
		self.log.info(
			f'ISO/UDF contains {len(iso.dirs_posix)} directories and {len(iso.files_posix)} files', echo=True)
		self.log.info(f'Getting structure of {self.root_path.name}', echo=True)
		source = FsReader(self.root_path)
		if self.drop == GrepLists.false:
			delta_posix = set(source.get_posix())
		else:
			delta_posix = {posix for posix in source.get_posix() if not self.drop(posix)}
		delta_posix -= iso.dirs_posix
		delta_posix -= iso.files_posix
		msg = f'Source {self.root_path.name}:'
		msg += f' {source.file_cnt+source.dir_cnt+source.else_cnt}'
		msg += f' / {source.file_cnt} / {source.dir_cnt} / {source.else_cnt}'
		msg += ' (all/files/dirs/other)'
		self.log.info(msg, echo=True)
		if delta_posix:
			with ExtPath.child(f'{self.filename}_missing.txt', parent=self.outdir).open('w') as fh:
				fh.write('\n'.join(sorted(list(delta_posix))))
			self.log.warning(f'{len(delta_posix)} paths are missing in ISO')

class IsoVerifyCli(ArgumentParser):
	'''CLI for IsoVerify'''

	def __init__(self,description=__description__, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(**kwargs)
		self.add_argument('-b', '--blacklist', type=ExtPath.path,
			help='Blacklist (textfile with one regex per line)', metavar='FILE'
		)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-i', '--image', type=ExtPath.path,
			help='Image path', metavar='FILE'
		)
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('-w', '--whitelist', type=ExtPath.path,
			help='Whitelist (if given, blacklist is ignored)', metavar='FILE'
		)
		self.add_argument('root', nargs=1, type=ExtPath.path,
			help='Source root', metavar='DIRECTORY'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.root = args.root[0]
		self.blacklist = args.blacklist
		self.filename = args.filename
		self.outdir = args.outdir
		self.imagepath = args.image
		self.whitelist = args.whitelist

	def run(self, echo=print):
		'''Run the verification'''
		if self.blacklist and self.whitelist:
			raise ValueError('Unable to wirk with blacklist and whitelist at the same time')
		drop = GrepLists(blacklist=self.blacklist, whitelist=self.whitelist).get_method()
		image = IsoVerify(self.root,
			imagepath = self.imagepath,
			filename = self.filename,
			outdir = self.outdir,
			drop = drop,
			echo = echo
		)
		image.posix_verify()
		image.log.close()

class IsoVerifyGui:
	'''Notebook page'''
	CMD = __app_name__
	DESCRIPTION = __description__

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		SourceDirSelector(root, frame)
		GridLabel(root, frame, root.ISO_IMAGE)
		FileSelector(root, frame,
			root.IMAGE, root.IMAGE, root.SELECT_IMAGE, filetype=('ISO files', '*.iso'))
		GridSeparator(root, frame)
		GridLabel(root, frame, root.DESTINATION)
		FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
		DirSelector(root, frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		GridSeparator(root, frame)
		GridLabel(root, frame, root.SKIP_PATH_CHECK)
		StringRadiobuttons(root, frame, root.REGEXFILTER,
			(root.NO_FILTER, root.BLACKLIST, root.WHITELIST), root.NO_FILTER)
		GridLabel(root, frame, root.CHECK_ALL_PATHS, column=2)
		FileSelector(root, frame,
			root.BLACKLIST, root.BLACKLIST, root.SELECT_BLACKLIST, command=self._select_blacklist)
		FileSelector(root, frame,
			root.WHITELIST, root.WHITELIST, root.SELECT_WHITELIST, command=self._select_whitelist)
		GridSeparator(root, frame)
		GridBlank(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job,
			column=0, columnspan=3)
		self.root = root

	def _select_blacklist(self):
		'''Select blacklist'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.REGEXFILTER).set(self.root.BLACKLIST)

	def _select_whitelist(self):
		'''Select whitelist'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.REGEXFILTER).set(self.root.WHITELIST)

	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		source = self.root.settings.get(self.root.SOURCE)
		image = self.root.settings.get(self.root.IMAGE)
		outdir = self.root.settings.get(self.root.OUTDIR)
		filename = self.root.settings.get(self.root.FILENAME)
		blacklist = self.root.settings.get(self.root.BLACKLIST)
		whitelist = self.root.settings.get(self.root.WHITELIST)
		if not source:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.SOURCE_REQUIRED
			)
			return
		if not image:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.ISO_REQUIRED
			)
			return
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
		cmd = self.root.settings.section.lower()
		cmd += f' --{self.root.OUTDIR.lower()} "{outdir}"'
		cmd += f' --{self.root.FILENAME.lower()} "{filename}"'
		cmd += f' --imagepath "{image}"'
		path_filter = self.root.settings.get(self.root.REGEXFILTER)
		if path_filter == self.root.BLACKLIST:
			blacklist = self.root.settings.get(self.root.BLACKLIST)
			if blacklist:
				cmd += f' --{self.root.BLACKLIST.lower()} "{blacklist}"'
		elif path_filter == self.root.WHITELIST:
			whitelist = self.root.settings.get(self.root.WHITELIST)
			if whitelist:
				cmd += f' --{self.root.WHITELIST.lower()} "{whitelist}"'
		cmd += f' "{source}"'
		self.root.append_job(cmd)

if __name__ == '__main__':	# start here if called as application
	app = IsoVerifyCli()
	app.parse()
	app.run()
