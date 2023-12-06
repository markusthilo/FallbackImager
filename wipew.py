#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'WipeW'
__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-12-06'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This is a wipe tool designed for SSDs and HDDs. There is also the possibility to overwrite files but without erasing file system metadata.

By default only unwiped blocks (or SSD pages) are overwritten though it is possible to force the overwriting of every block or even use a two pass wipe (1st pass writes random values). Instead of zeros you can choose to overwrite with ones.

Whe the target is a physical drive, you can create a partition where (after a successful wipe) the log is copied into. A custom head for this log can be defined in a text file (hdzero_log_head.txt by default).

Be aware that this module is extremely dangerous as it is designed to erase data! There will be no "Are you really really sure questions" as Windows users might be used to.
'''

from sys import executable as __executable__
from pathlib import Path
from functools import partial
from win32com.shell.shell import IsUserAnAdmin
from argparse import ArgumentParser
from tkinter import StringVar
from tkinter.ttk import Frame, Radiobutton, Button, Checkbutton
from tkinter.messagebox import askyesno, showerror
from tkinter.filedialog import askopenfilenames
from tkinter.scrolledtext import ScrolledText
from lib.timestamp import TimeStamp
from lib.extpath import ExtPath
from lib.logger import Logger
from lib.winutils import WinUtils
from lib.guielements import SourceDirSelector, Checker, LeftLabel, GridIntMenu, GridStringMenu
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
for __zd_exe_path__ in (
		__parent_path__/'zd-win.exe',
		__parent_path__/'bin'/'zd-win.exe',
	):
	if __zd_exe_path__.is_file():
		break
else:
	__zd_exe_path__ = None

class WipeW(WinUtils):
	'''Frontend and Python wrapper for zd-win.exe'''

	MIN_BLOCKSIZE = 512
	STD_BLOCKSIZE = 4096
	MAX_BLOCKSIZE = 32768

	def __init__(self,
			targets = None,
			verify = False,
			allbytes = False,
			extra = False,
			value = False,
			blocksize = None,
			maxbadblocks = None,
			maxretries = None,
			create = None,
			driveletter = None,
			listdrives = False,
			log = None,
			loghead = None,
			mbr = False,
			name = None,
			outdir = None,
			zd = None,
			echo = print
		):
		self.echo = echo
		if listdrives:
			if len(targets) > 0:
				raise RuntimeError('Giving targets makes no sense with --listdrives')
			super().__init__()
			self.echo_drives()
			return
		if len(targets) == 0:
			raise FileNotFoundError('Missing drive or file(s) to wipe')
		if verify and allbytes and extra:
			raise RuntimeError(f'Too many arguments - you can perform normal wipe, all bytes, extra/2-pass or just verify')
		if verify and (create or extra or mbr or driveletter or name):
			raise RuntimeError(f'Arguments incompatible with --verify/-v')
		if blocksize and (
				blocksize % self.MIN_BLOCKSIZE != 0 or blocksize < MIN_BLOCKSIZE or blocksize > MAX_BLOCKSIZE
			):
				raise ValueError(f'Block size has to be n * {MIN_BLOCKSIZE}, >={MIN_BLOCKSIZE} and <={MAX_BLOCKSIZE}')
		try:
			int(value, 16)
		except ValueError:
			raise ValueError('Byte to overwrite with (-f/--value) has to be a hex value')
		if int(value, 16) < 0 or int(value, 16) > 0xff:
			raise ValueError('Byte to overwrite (-f/--value) has to be inbetween 00 and ff')
		self.outdir = ExtPath.mkdir(outdir)
		if zd:
			self.zd_path = Path(zd)
		elif __zd_exe_path__:
			self.zd_path = __zd_exe_path__
		else:
			raise FileNotFoundError('Unable to locate zd-win.exe')
		super().__init__(self.outdir)
		not_admin = not IsUserAnAdmin()
		self.allbytes = allbytes
		self.blocksize = blocksize
		self.extra = extra
		self.verify = verify
		self.maxbadblocks = maxbadblocks
		self.maxretries = maxretries
		self.value = value
		if len(targets) == 1 and self.is_physical_drive(targets[0]):
			if not_admin:
				raise RuntimeError('Admin rights are required to access block devices')
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
		if create:
			if not self.physicaldrive:
				raise RuntimeError(f'{target} is not a block device')
			if name:
				self.name = name
			else:
				self.name = 'Volume'
			self.create = create.lower()
			if loghead:
				self.loghead = Path(loghead)
			self.driveletter = driveletter
			self.mbr = mbr
		else:
			self.create = None
			if driveletter or name or mbr:
				raise RuntimeError(f'Not going to create a partition - too many arguments')
		self.log = log

	def echo_drives(self):
		'''List drives and show infos'''
		for drive_id, drive_info in self.list_drives():
			self.echo(f'\n{drive_id} - {drive_info}')
		self.echo()

	def zd(self):
		'''Run zd-win.exe + write log to file'''
		if not self.log:
			self.log = Logger(
				filename = f'{TimeStamp.now(path_comp=True, no_ms=True)}_wipe-log.txt',
				outdir = self.outdir, 
				head = 'wipew.WipeW',
				echo = self.echo
			)
		cmd = f'{self.zd_path}'
		if self.blocksize:
			cmd += f' -b {self.blocksize}'
		if self.value:
			cmd += f' -f {self.value}'
		if self.maxbadblocks:
			cmd += f' -m {self.maxbadblocks}'
		if self.maxretries:
			cmd += f' -r {self.maxretries}'
		if self.verify:
			cmd += ' -v'
		elif self.allbytes:
			cmd += ' -a'
		elif self.extra:
			cmd += ' -x'
		if self.echo == print:
			echo = lambda msg: print(f'\r{msg}', end='')
		else:
			echo = lambda msg: self.echo(f'\n{msg}', overwrite=True)
		error = False
		for target in self.targets:
			self.echo()
			proc = self.cmd_launch(f'{cmd} ' + str(target).rstrip('\\'))
			for line in proc.stdout:
				msg = line.strip()
				if msg:
					if msg.startswith('...'):
						echo(msg)
					elif msg.startswith('Process took'):
						self.echo(f'\n{msg}')
						self.log.info(msg)
					else:
						self.log.info(msg, echo=True)
			if stderr := proc.stderr.read():
				self.log.warning(stderr)
				error = True
		if not self.create:
			self.log.close()
			return
		if error:
			self.log.warning(f'Could not create {self.create} file system')
			self.log.close()
			return
		if not self.driveletter:
			self.driveletter = self.get_free_letters()[0]
		letter = self.create_partition(self.targets[0],
			label = self.name,
			letter = self.driveletter,
			mbr = self.mbr,
			fs = self.create
		)
		self.log.close()
		if letter:
			log_path = Path(f'{letter}:\\wipe-log.txt')
			head = ''
			if self.loghead:
				try:
					head = self.loghead.read_text()
				except FileNotFoundError:
					pass
			with log_path.open('w') as fh:
				fh.write(head + self.log.path.read_text())

class WipeWCli(ArgumentParser):
	'''CLI, also used for GUI of FallbackImager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-a', '--allbytes', action='store_true',
			help='Write every byte/block (do not check before overwriting block)'
		)
		self.add_argument('-b', '--blocksize', type=int,
			help='Block size in bytes (=n*512, >=512, <= 32768,default is 4096)', metavar='INTEGER'
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
		self.add_argument('-f', '--value', type=str,
			help='Byte to overwrite with as hex (00 - ff)',
			metavar='HEX_BYTE'
		)
		self.add_argument('-g', '--loghead',
			default=__parent_path__/'hdzero_log_head.txt', type=Path,
			help='Use the given file as head when writing log to new drive',
			metavar='FILE'
		)
		self.add_argument('-l', '--listdrives', action='store_true',
			help='List physical drives (ignore all other arguments)'
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
		self.add_argument('-q', '--maxbadblocks', type=int,
			help='Abort after given number of bad blocks (default is 200)', metavar='INTEGER'
		)
		self.add_argument('-r', '--maxretries', type=int,
			help='Maximum of retries after read or write error (default is 200)',
			metavar='INTEGER'
		)
		self.add_argument('-v', '--verify', action='store_true',
			help='Verify, but do not wipe'
		)
		self.add_argument('-x', '--extra', action='store_true',
			help='Overwrite all bytes/blocks twice, write random bytes at 1st pass'
		)
		self.add_argument('-z', '--zd', type=Path, help='Path to zd-win.exe', metavar='FILE')
		self.add_argument('targets', nargs='*', type=str,
			help='Target drive or file(s) (e.g. \\.\\\\PHYSICALDRIVE1)', metavar='DRIVE/FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.targets = args.targets
		if len(self.targets) == 1 and self.targets[0].startswith('\\.PHYSICALDRIVE'):
			self.targets = [f'\\\\.\\{self.targets[0][2:]}']
		self.allbytes = args.allbytes
		self.blocksize = args.blocksize
		self.create = args.create
		self.driveletter = args.driveletter
		self.listdrives = args.listdrives
		self.loghead = args.loghead
		self.maxbadblocks = args.maxbadblocks
		self.maxretries = args.maxretries
		self.mbr = args.mbr
		self.name = args.name
		self.outdir = args.outdir
		self.value = args.value
		self.verify = args.verify
		self.extra = args.extra
		self.zd = args.zd

	def run(self, echo=print):
		'''Run HdZero'''
		wiper = WipeW(
			targets = self.targets,
			allbytes = self.allbytes,
			blocksize = self.blocksize,
			create = self.create,
			driveletter = self.driveletter,
			listdrives = self.listdrives,
			loghead = self.loghead,
			maxbadblocks = self.maxbadblocks,
			maxretries = self.maxretries,
			mbr = self.mbr,
			name = self.name,
			outdir = self.outdir,
			value = self.value,
			verify = self.verify,
			extra = self.extra,
			zd = self.zd,
			echo = echo
		)
		if not self.listdrives:
			wiper.zd()

class HdZeroGui(WinUtils):
	'''Notebook page'''

	CMD = __app_name__
	DESCRIPTION = __description__
	DEF_BLOCKSIZE = 4096
	BLOCKSIZES = (512, 1024, 2048, 4096, 8192, 16384, 32768,
		65536, 131072, 262144, 524288, 1048576)
	TABLES = ('GPT', 'MBR')
	DEF_TABLE = 'GPT'
	FS = ('NTFS', 'exFAT', 'FAT32')
	DEF_FS = 'NTFS'

	def __init__(self, root):
		'''Notebook page'''
		super().__init__(__parent_path__)
		self.hdzero = HdZero()
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		GridSeparator(root, frame)
		GridLabel(root, frame, root.WIPE)
		StringSelector(root, frame, root.TARGET, root.TARGET,
			command=self._select_target, columnspan=8)
		root.settings.raw(root.TARGET).set('')
		GridSeparator(root, frame)
		GridLabel(root, frame, root.LOGGING)
		DirSelector(root, frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR, columnspan=8)
		GridSeparator(root, frame)
		GridLabel(root, frame, root.TO_DO)
		StringRadiobuttons(root, frame, root.TO_DO,
			(root.NORMAL_WIPE, root.EVERY_BLOCK, root.EXTRA_PASS, root.VERIFY), root.NORMAL_WIPE)
		GridLabel(root, frame, root.NORMAL_WIPE, column=1)
		GridLabel(root, frame, root.EVERY_BLOCK, column=1)
		GridLabel(root, frame, root.EXTRA_PASS, column=1)
		GridLabel(root, frame, root.VERIFY, column=1)
		root.row -= 4
		GridIntMenu(root, frame, root.BLOCKSIZE, root.BLOCKSIZE, self.BLOCKSIZES,
			default=self.DEF_BLOCKSIZE, column=2)
		root.row -= 1
		GridStringMenu(root, frame, root.PARTITION_TABLE, root.PARTITION_TABLE,
			([root.DO_NOT_CREATE] + list(self.TABLES)), default=self.DEF_TABLE, column=4)
		root.row -= 1
		GridStringMenu(root, frame, root.FILE_SYSTEM, root.FILE_SYSTEM,
			([root.DO_NOT_CREATE] + list(self.FS)), default=self.DEF_FS, column=6)
		root.row -= 1
		GridStringMenu(root, frame, root.DRIVE_LETTER, root.DRIVE_LETTER,
			([root.NEXT_AVAILABLE] + self.hdzero.get_free_letters()),
			default=root.NEXT_AVAILABLE, column=8)
		root.row += 1
		Checker(root, frame, root.USE_FF, root.USE_FF, column=2)
		root.row -= 1
		StringSelector(root, frame, root.VOLUME_NAME, root.VOLUME_NAME,
			default=root.DEFAULT_VOLUME_NAME, width=root.VOLUME_NAME_WIDTH, column=6, columnspan=2)
		GridSeparator(root, frame)
		GridLabel(root, frame, root.CONFIGURATION)
		FileSelector(root, frame, root.LOG_HEAD, root.LOG_HEAD, root.SELECT_TEXT_FILE,
			default=__parent_path__/'hdzero_log_head.txt',
			command=self._notepad_log_head, columnspan=8)
		FileSelector(root, frame, root.ZEROD_EXE, root.ZEROD_EXE, root.SELECT_ZEROD_EXE,
			filetype=(root.ZEROD_EXE, 'zerod.exe'), default=__zerod_exe_path__, columnspan=8)
		GridSeparator(root, frame)
		GridBlank(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}',
			self._add_job, column=0, columnspan=3)
		root.child_win_active = False
		self.root = root
		self.filenames = None

	def _notepad_log_head(self):
		'''Edit log header file with Notepad'''
		proc = Popen(['notepad', self.root.settings.get(self.root.LOG_HEAD, section=self.CMD)])
		proc.wait()

	def _select_target(self):
		'''Select drive to wipe'''
		if self.root.child_win_active:
			return
		self.target_window = ChildWindow(self.root, self.root.SELECT)
		self.root.settings.section = self.CMD
		frame = ExpandedFrame(self.root, self.target_window)
		self.root.row = 0
		GridLabel(self.root, frame, self.root.SELECT_DRIVE)
		for drive_id, drive_info in self.hdzero.list_drives():
			Button(frame, text=drive_id, command=partial(self._put_drive, drive_id)).grid(
				row=self.root.row, column=0, sticky='nw', padx=self.root.PAD)
			text = ScrolledText(frame, width=self.root.ENTRY_WIDTH,
				height=min(len(drive_info.split('\n')), self.root.MAX_ENTRY_HEIGHT ))
			text.grid(row=self.root.row, column=1)
			text.bind('<Key>', lambda dummy: 'break')
			text.insert('end', f'{drive_id} - {drive_info}')
			text.configure(state='disabled')
			self.root.row += 1
		frame = ExpandedFrame(self.root, self.target_window)
		LeftButton(self.root, frame, self.root.REFRESH, self._refresh_target_window)
		frame = ExpandedFrame(self.root, self.target_window)
		GridSeparator(self.root, frame)
		frame = ExpandedFrame(self.root, self.target_window)
		LeftButton(self.root, frame, self.root.SELECT_FILES, self._select_files)
		RightButton(self.root, frame, self.root.QUIT, self.target_window.destroy)

	def _refresh_target_window(self):
		'''Destroy and reopen Target Window'''
		self.target_window.destroy()
		self._select_target()

	def _put_drive(self, drive_id):
		'''Put drive id to target string'''
		self.target_window.destroy()
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.TARGET).set(drive_id)
		self.filenames = None

	def _select_files(self):
		'''Choose file(s) to wipe'''
		self.target_window.destroy()
		self.filenames = askopenfilenames(title=self.root.SELECT_FILES)
		if self.filenames:
			plus = len(self.filenames) -1
			target = self.filenames[0]
			if plus > 0:
				if plus == 1:
					target += f' + {plus} {self.root.FILE}'
				else:
					target += f' + {plus} {self.root.FILES}'
			self.root.settings.raw(self.root.TARGET).set(target)

	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		target = self.root.settings.get(self.root.TARGET)
		target_is_pd = self.is_physical_drive(target)
		if not target or ( not target_is_pd and not self.filenames ):
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.TARGET_REQUIRED
			)
			self.filenames = None
			return
		outdir = self.root.settings.get(self.root.OUTDIR) 
		if not outdir:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.LOGDIR_REQUIRED
			)
			return
		cmd = self.root.settings.section.lower()
		cmd += f' --{self.root.OUTDIR.lower()} "{outdir}"'
		zerod_exe = self.root.settings.get(self.root.ZEROD_EXE)
		if zerod_exe:
			cmd += f' --zerod "{zerod_exe}"'
		log_head = self.root.settings.get(self.root.LOG_HEAD)
		if log_head:
			cmd += f' --loghead "{log_head}"'
		to_do = self.root.settings.get(self.root.TO_DO)
		if to_do == self.root.EVERY_BLOCK:
			cmd += f' --every'
		elif to_do == self.root.EXTRA_PASS:
			cmd += f' --extra'
		elif to_do == self.root.VERIFY:
			cmd += f' --verify'
		blocksize = self.root.settings.get(self.root.BLOCKSIZE)
		cmd += f' --blocksize {blocksize}'
		if self.root.settings.get(self.root.USE_FF):
			cmd += f' --ff'
		partition_table = self.root.settings.get(self.root.PARTITION_TABLE)
		file_system = self.root.settings.get(self.root.FILE_SYSTEM)
		if (
			target_is_pd
			and partition_table != self.root.DO_NOT_CREATE
			and file_system != self.root.DO_NOT_CREATE
		):
			if partition_table != self.TABLES[0]:
				cmd += f' --mbr'
			cmd += f' --create {file_system}'
			volume_name = self.root.settings.get(self.root.VOLUME_NAME)
			if volume_name:
				cmd += f' --name "{volume_name}"'
			drive_letter = self.root.settings.get(self.root.DRIVE_LETTER)
			if (
				drive_letter != self.root.NEXT_AVAILABLE
				and not self.hdzero.drive_letter_is_free(drive_letter)
				and askyesno(
					title = self.root.DRIVE_LETTER_TAKEN,
					message = self.root.USE_IT_ANYWAY
				)
			):
				cmd += f' --driveletter {drive_letter}'
		if self.is_physical_drive(target):
			cmd += f' {target}'
		else:
			for target in self.filenames:
				cmd += f' "{target}"'
		self.root.append_job(cmd)

if __name__ == '__main__':	# start here if called as application
	app = WipeWCli()
	app.parse()
	app.run()