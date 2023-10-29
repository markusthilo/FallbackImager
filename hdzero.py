#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'HdZero'
__author__ = 'Markus Thilo'
__version__ = '0.2.2_2023-10-29'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Wipe disk but not touching empty blocks/pages or overwrite all. The tool is also
capable of overwriting files but slack and files system artefacts will remain.
It is designed to securely wipe HDDs/SSDs and generate a log file.
'''

from sys import executable as __executable__
from pathlib import Path
from functools import partial
from win32com.shell.shell import IsUserAnAdmin
from argparse import ArgumentParser
from tkinter import StringVar
from tkinter.ttk import Frame, Radiobutton, Button, Checkbutton
from tkinter.messagebox import askyesno
from tkinter.filedialog import askopenfilenames
from tkinter.scrolledtext import ScrolledText
from lib.timestamp import TimeStamp
from lib.extpath import ExtPath
from lib.logger import Logger
from lib.winutils import WinUtils
from lib.guielements import SourceDirSelector, Checker, LeftLabel, GridIntMenu
from lib.guielements import ChildWindow, SelectTsvColumn, FilesSelector, ExpandedLabelFrame
from lib.guielements import ExpandedFrame, GridSeparator, GridLabel, DirSelector
from lib.guielements import FilenameSelector, StringSelector, StringRadiobuttons
from lib.guielements import FileSelector, GridButton, LeftButton, RightButton, GridBlank

__executable__ = Path(__executable__)
__file__ = Path(__file__)
if __executable__.stem.lower() == __file__.stem.lower():
	__parent_path__ = __executable__.parent
else:
	__parent_path__ = __file__.parent
for __zerod_exe_path__ in (
		__parent_path__/'zerod.exe',
		__parent_path__/'bin'/'zerod.exe',
	):
	if __zerod_exe_path__.is_file():
		break
else:
	__zerod_exe_path__ = None

class HdZero(WinUtils):
	'''Use zerod.exe'''

	MIN_BLOCKSIZE = 512
	MAX_BLOCKSIZE = 1048576

	def __init__(self, targets,
			ff = False,
			blocksize = None,
			create = None,
			driveletter = None,
			listdrives = False,
			log = None,
			loghead = None,
			every = False,
			mbr = False,
			name = None,
			outdir = None,
			verify = False,
			extra = False,
			zerod = None,
			echo = print
		):
		self.echo = echo
		if listdrives:
			super().__init__()
			self.echo_drives()
			return
		self.outdir = ExtPath.mkdir(outdir)
		super().__init__(self.outdir)
		if len(targets) == 0:
			raise FileNotFoundError('Missing drive or file(s) to wipe')
		if zerod:
			self.zerod_path = Path(zerod)
		elif __zerod_exe_path__:
			self.zerod_path = __zerod_exe_path__
		else:
			raise FileNotFoundError('Unable to locate zerod.exe')
		not_admin = not IsUserAnAdmin()
		self.ff = ff
		if len(targets) == 1 and str(targets[0]).startswith('\\\\.\\PHYSICALDRIVE'):
			if not_admin:
				raise RuntimeError('Admin rights are required to access block devices')
			if blocksize and blocksize % self.MIN_BLOCKSIZE != 0:
				raise ValueError(f'{target} is a block device and needs block size n*512 bytes')
			self.physicaldrive = True
			self.targets = targets
		else:
			if create or mbr or driveletter or name:
				raise RuntimeError(f'Arguments only for physical drives')
			self.targets = list()
			for target in targets:
				target_path = Path(target)
				if not target_path.is_file():
					raise FileNotFoundError(f'Cannot find file {target_path} to wipe')
				self.targets.append(target_path)
			self.physicaldrive = False
		if blocksize and (blocksize <= 0 or blocksize > self.MAX_BLOCKSIZE):
			raise ValueError(f'Block size out of range (max. {self.MAX_BLOCKSIZE} bytes)')
		if verify and (create or extra or mbr or driveletter or name):
			raise RuntimeError(f'Arguments incompatible to --verify/-v')
		if create:
			if not self.physicaldrive:
				raise RuntimeError(f'{target} is not a block device')
			if not name:
				raise RuntimeError(f'Missing name for new partition')
			self.create = create.lower()
			if loghead:
				self.loghead = Path(loghead)
			self.driveletter = driveletter
			self.mbr = mbr
			self.name = name
		else:
			self.create = None
			if driveletter or name or mbr:
				raise RuntimeError(f'Too many arguments')
		self.blocksize = blocksize
		self.every = every
		self.extra = extra
		self.verify = verify
		self.log = log

	def echo_drives(self):
		'''List drives and show infos'''
		for drive_id, drive_info, drive_letters in self.list_drives():
			self.echo(f'\n{drive_id} - {drive_info}')
		self.echo()

	def zerod(self):
		'''Run zerod + write log to file'''
		if not self.log:
			self.log = Logger(
				filename = f'{TimeStamp.now(path_comp=True, no_ms=True)}_hdzero',
				outdir = self.outdir, 
				head = 'hdzero.HdZero',
				echo = self.echo
			)
		zerod_str = f'{self.zerod_path}'
		if self.blocksize:
			opt_str = f' {self.blocksize}'
		else:
			opt_str = ''
		if self.verify:
			opt_str += ' /v'
		else:
			if self.extra:
				opt_str += ' /x'
			elif self.every:
				opt_str += ' /e'
		if self.ff:
			opt_str += ' /f'
		if self.echo == print:
			echo = lambda msg: print(f'\r{msg}', end='')
		else:
			echo = lambda msg: self.echo(msg, overwrite=True)
		error = False
		for target in self.targets:
			self.echo()
			cmd = f'{zerod_str} {target}{opt_str}'
			proc = self.cmd_launch(cmd)
			for line in proc.stdout:
				msg = line.strip()
				if msg.startswith('...'):
					echo(msg)
				else:
					self.log.info(msg, echo=True)
			if stderr := proc.stderr.read():
				self.log.warning(stderr)
				error = True
		if self.create and not error:
			letter = self.create_partition(self.targets[0],
				label = self.name,
				letter = self.driveletter,
				mbr = self.mbr,
				fs = self.create
			)
		else:
			letter = None
			self.log.warning(f'Could not create {self.create} file system')
		self.log.close()
		if letter:
			log_path = Path(f'{letter}:\\hdzero-log.txt')
			head = ''
			if self.loghead:
				try:
					head = self.loghead.read_text()
				except FileNotFoundError:
					pass
			with log_path.open('w') as fh:
				fh.write(head + self.log.path.read_text())

class HdZeroCli(ArgumentParser):
	'''CLI, also used for GUI of FallbackImager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-1', '--ff', action='store_true',
			help='Write binary ones (0xff bytes) instead of zeros'
		)
		self.add_argument('-b', '--blocksize', type=int,
			help='Block size', metavar='INTEGER'
		)
		self.add_argument('-c', '--create', type=str,
			choices=['ntfs', 'fat32', 'exfat', 'NTFS', 'FAT32', 'EXFAT', 'ExFAT', 'exFAT'],
			help='Create partition (when target is a physical drive)',
			metavar='STRING'
		)
		self.add_argument('-d', '--driveletter', type=str,
			help='Assign letter to drive (when target is a physical drive)',
			metavar='DRIVE LETTER'
		)
		self.add_argument('-e', '--every', action='store_true',
			help='Write every block (do not check before overwriting block)'
		)
		self.add_argument('-l', '--listdrives', action='store_true',
			help='List physical drives (ignore all other arguments)'
		)
		self.add_argument('-g', '--loghead',
			default=__parent_path__/'hdzero_log_head.txt', type=Path,
			help='Use the given file as head when writing log to new drive',
			metavar='FILE'
		)
		self.add_argument('-m', '--mbr', action='store_true',
			help='Use mbr instead of gpt Partition table (when target is a physical drive)'
		)
		self.add_argument('-n', '--name', type=str,
			help='Name/label of the new partition (when target is a physical drive)',
			metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write log', metavar='DIRECTORY'
		)
		self.add_argument('-v', '--verify', action='store_true',
			help='Verify for zeros (or 0xff with -f) but do not wipe'
		)
		self.add_argument('-x', '--extra', action='store_true',
			help='Overwrite/wipe all blocks twice, write random bytes at 1st pass (for HDDs)'
		)
		self.add_argument('-z', '--zerod', type=Path, help='Path to zerod.exe', metavar='FILE')
		self.add_argument('targets', nargs='*', type=str,
			help='Target drive or file(s) (e.g. \\.\\\\PHYSICALDRIVE1)', metavar='DRIVE/FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.targets = args.targets
		self.ff = args.ff
		self.blocksize = args.blocksize
		self.create = args.create
		self.driveletter = args.driveletter
		self.every = args.every
		self.listdrives = args.listdrives
		self.loghead = args.loghead
		self.mbr = args.mbr
		self.name = args.name
		self.outdir = args.outdir
		self.verify = args.verify
		self.extra = args.extra
		self.zerod = args.zerod

	def run(self, echo=print):
		'''Run HdZero'''
		hdzero = HdZero(self.targets,
			ff = self.ff,
			blocksize = self.blocksize,
			create = self.create,
			driveletter = self.driveletter,
			listdrives = self.listdrives,
			loghead = self.loghead,
			every = self.every,
			mbr = self.mbr,
			name = self.name,
			verify = self.verify,
			extra = self.extra,
			zerod = self.zerod,
			echo = echo
		)
		if not self.listdrives:
			hdzero.zerod()

class HdZeroGui(WinUtils):
	'''Notebook page'''

	CMD = __app_name__
	DESCRIPTION = __description__
	DEF_BLOCKSIZE = 4096
	BLOCKSIZES = (512, 1024, 2048, 4096, 8192, 16384, 32768,
		65536, 131072, 262144, 524288, 1048576)
	PARTITIONS = ('GPT', 'MBR', 'Do not create partition')
	FILESYSTEMS = ('NTFS', 'exFAT', 'FAT32')

	def __init__(self, root):
		'''Notebook page'''
		super().__init__(__parent_path__)
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		GridSeparator(root, frame)
		GridLabel(root, frame, root.WIPE)
		StringSelector(root, frame, root.TARGET, root.TARGET,
			command=self._select_target, columnspan=4)
		GridSeparator(root, frame)
		GridLabel(root, frame, root.LOGGING)
		self.filename_str = FilenameSelector(root, frame, root.FILENAME, root.FILENAME, columnspan=4)
		DirSelector(root, frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR, columnspan=4)
		GridSeparator(root, frame)
		GridLabel(root, frame, root.TO_DO)
		StringRadiobuttons(root, frame, root.TO_DO,
			(root.NORMAL_WIPE, root.ALL_BLOCKS, root.EXTRA_PASS, root.CHECK), root.NORMAL_WIPE)
		GridLabel(root, frame, root.NORMAL_WIPE, column=1)
		GridLabel(root, frame, root.ALL_BLOCKS, column=1)
		GridLabel(root, frame, root.EXTRA_PASS, column=1)
		GridLabel(root, frame, root.CHECK, column=1)
		GridSeparator(root, frame)
		GridLabel(root, frame, root.CONFIGURATION)
		root.row -= 1
		GridIntMenu(root, frame, root.BLOCKSIZE, root.BLOCKSIZE, self.BLOCKSIZES,
			default=self.DEF_BLOCKSIZE, column=2)
		root.row -= 1
		Checker(root, frame, root.USE_FF, root.USE_FF, column=4)
		FileSelector(root, frame, root.LOG_HEAD, root.LOG_HEAD, root.SELECT_TEXT_FILE,
			default=__parent_path__/'hdzero_log_head.txt',
			command=self.notepad_log_head, columnspan=4)
		FileSelector(root, frame, root.ZEROD_EXE, root.ZEROD_EXE, root.SELECT_ZEROD_EXE,
			filetype=(root.ZEROD_EXE, 'zerod.exe'), default=__zerod_exe_path__, columnspan=4)

		GridSeparator(root, frame)
		GridBlank(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}',
			self._add_job, column=0, columnspan=3)
		root.child_win_active = False
		self.root = root
		

	def notepad_log_head(self):
		'Edit log header file with Notepad'
		proc = Popen(['notepad', self.root.settings.get(self.root.LOG_HEAD, section=self.CMD)])
		proc.wait()

	def gen_drive_list_frame(self):
		'''Generate drame with list of available drives'''
		try:
			self.drive_list_inner_frame.destroy()
		except AttributeError:
			pass
		self.root.row = 0
		self.drive_list_inner_frame = Frame(self.drive_list_outer_frame)
		self.drive_list_inner_frame.pack()
		for drive_id, drive_info, drive_letters in self.list_drives():
			Button(self.drive_list_inner_frame,
				text = f'{drive_id}',
				command = partial(self._process_drive, drive_id, drive_letters)
			).grid(sticky='nw', row=self.root.row, column=0, padx=self.root.PAD, pady=self.root.PAD)
			text = ScrolledText(self.drive_list_inner_frame, height=self.root.JOB_HEIGHT)
			text.grid(row=self.root.row, column=1, padx=self.root.PAD, pady=self.root.PAD)
			text.bind('<Key>', lambda dummy: 'break')
			text.insert('end', drive_info)
			text.configure(state='disabled')
			self.root.row += 1

	def _set_default_name(self):
		'''Set the default partition name'''
		self.root.settings.section = self.CMD
		if not self.root.settings.get(self.root.PARTITION_NAME):
			self.root.settings.raw(self.root.PARTITION_NAME).set(self.root.DEFAULT_PARTITION_NAME)

	def _select_target(self):
		'''Select drive to wipe'''
		if self.root.child_win_active:
			return
		self.drive_window = ChildWindow(self.root, self.root.SELECT_DRIVE)
		self.root.settings.section = self.CMD
		self.drive_list_outer_frame = ExpandedFrame(self.root, self.drive_window)
		self.gen_drive_list_frame()
		frame = ExpandedLabelFrame(self.root, self.drive_window, self.root.CREATE)
		self.root.row = 0
		StringSelector(self.root, frame, self.root.PARTITION_NAME, self.root.PARTITION_NAME,
			width=self.root.PARTITION_NAME_WIDTH, command=self._set_default_name, column=0)
		self.root.row = 0
		GridLabel(self.root, frame, self.root.PARTITION_TABLE, column=2, columnspan=2)
		StringRadiobuttons(self.root, frame, self.root.PARTITION_TABLE, self.PARTITIONS,
			self.PARTITIONS[0], column=2)
		GridLabel(self.root, frame, self.PARTITIONS[0], column=3)
		GridLabel(self.root, frame, self.PARTITIONS[1], column=3)
		GridLabel(self.root, frame, self.PARTITIONS[2], column=3)
		self.root.row = 0
		GridLabel(self.root, frame, self.root.FILESYSTEM, column=4, columnspan=2)
		StringRadiobuttons(self.root, frame, self.root.FILESYSTEM, self.FILESYSTEMS,
			self.FILESYSTEMS[0], column=4)
		GridLabel(self.root, frame, self.FILESYSTEMS[0], column=5)
		GridLabel(self.root, frame, self.FILESYSTEMS[1], column=5)
		GridLabel(self.root, frame, self.FILESYSTEMS[2], column=5)
		frame = ExpandedFrame(self.root, self.drive_window)
		LeftButton(self.root, frame, self.root.REFRESH, self.gen_drive_list_frame)
		RightButton(self.root, frame, self.root.QUIT, self.drive_window.destroy)

	def _select_files(self):
		self.root.settings.write()
		return
		if self.root.child_win_active or self.root.start_disabled:
			return
		filenames = askopenfilenames(title=self.root.ASK_FILES)
		if not filenames:
			return
		if askyesno(title=f'{self.root.WIPE} {len(filenames)} {self.root.FILES}',
			message=self.root.AREYOUSURE):
			self.root.disable_start()
			hdzero = HdZero(filenames,
				task = self.root.settings.get(self.root.TO_DO),
				ff = self.root.settings.get(self.root.USE_FF),
				blocksize = self.root.settings.get(self.root.BLOCKSIZE),
				echo = self.root.append_info,
				zerod = self.root.settings.get(self.root.ZEROD_EXE)
			)

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
	app = HdZeroCli()
	app.parse()
	app.run()