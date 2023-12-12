#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'WipeR'
__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-12-12'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This is a wipe tool designed for SSDs and HDDs. There is also the possibility to overwrite files but without erasing file system metadata.

By default only unwiped blocks (or SSD pages) are overwritten though it is possible to force the overwriting of every block or even use a two pass wipe (1st pass writes random values). Instead of zeros you can choose to overwrite with a given byte value.

Whe the target is a physical drive, you can create a partition where (after a successful wipe) the log is copied into. A custom head for this log can be defined in a text file (wipe-head.txt by default).

Be aware that this module is extremely dangerous as it is designed to erase data!
'''

from sys import executable as __executable__
from time import sleep
from subprocess import Popen, PIPE
from pathlib import Path
from functools import partial
from argparse import ArgumentParser
from tkinter import StringVar
from tkinter.ttk import Frame, Radiobutton, Button, Checkbutton
from tkinter.messagebox import askyesno, showerror
from tkinter.filedialog import askopenfilenames
from tkinter.scrolledtext import ScrolledText
from lib.timestamp import TimeStamp
from lib.extpath import ExtPath
from lib.logger import Logger
from lib.linutils import LinUtils
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
for __zd_path__ in (
		__parent_path__/'zd',
		__parent_path__/'bin'/'zd',
		Path('/usr/bin/zd'),
		Path('/usr/local/bin/zd')
	):
	if __zd_path__.is_file():
		break
else:
	raise FileNotFoundError('Unable to locate zd')

class WipeR:
	'''Frontend and Python wrapper for zd'''

	MIN_BLOCKSIZE = 512
	STD_BLOCKSIZE = 4096
	MAX_BLOCKSIZE = 32768

	def __init__(self, targets,
			verify = False,
			allbytes = False,
			extra = False,
			value = False,
			blocksize = None,
			maxbadblocks = None,
			maxretries = None,
			log = None,
			outdir = None,
			echo = print
		):
		self.echo = echo
		if len(targets) == 0:
			raise FileNotFoundError('Missing drive or file(s) to wipe')
		if verify and allbytes and extra:
			raise RuntimeError(f'Too many arguments - you can perform normal wipe, all bytes, extra/2-pass or just verify')
		if blocksize and (
				blocksize % self.MIN_BLOCKSIZE != 0 or blocksize < self.MIN_BLOCKSIZE or blocksize > self.MAX_BLOCKSIZE
			):
				raise ValueError(f'Block size has to be n * {MIN_BLOCKSIZE}, >={MIN_BLOCKSIZE} and <={MAX_BLOCKSIZE}')
		if value:
			try:
				int(value, 16)
			except ValueError:
				raise ValueError('Byte to overwrite with (-f/--value) has to be a hex value')
			if int(value, 16) < 0 or int(value, 16) > 0xff:
				raise ValueError('Byte to overwrite (-f/--value) has to be inbetween 00 and ff')
		self.outdir = ExtPath.mkdir(outdir)
		if log:
			self.log = log
		else:
			self.log = Logger(
				filename = f'{TimeStamp.now(path_comp=True, no_ms=True)}_wipe-log.txt',
				outdir = self.outdir, 
				head = 'wiper.WipeR',
				echo = self.echo
			)
		if Path(targets[0]).is_block_device():
			if len(targets) != 1:
				raise RuntimeError('Only one physical drive at a time')
		cmd = [f'{__zd_path__}']
		if blocksize:
			cmd.extend(['-b',  blocksize])
		if value:
			cmd.extend(['-f', value])
		if maxbadblocks:
			cmd.extend(['-m', maxbadblocks])
		if maxretries:
			cmd.extend(['-r', maxretries])
		if verify:
			cmd.append('-v')
		elif allbytes:
			cmd.append('-a')
		elif extra:
			cmd.append('-x')
		if self.echo == print:
			echo = lambda msg: print(f'\r{msg}', end='')
		else:
			echo = lambda msg: self.echo(f'\n{msg}', overwrite=True)
		self.zd_error = False

		return

		for target in targets:
			self.echo()
			proc = Popen(cmd + [target], stdout=PIPE, stderr=PIPE, text=True)
			for line in proc.stdout:
				msg = line.strip()
				if msg:
					if msg.startswith('...'):
						echo(msg)
					else:
						self.log.info(msg)
						self.echo(f'\n{msg}')
			if stderr := proc.stderr.read():
				self.log.warning(stderr)
				self.zd_error = True

	def mkfs(self, target,
			fs = 'ntfs',
			loghead = None,
			mbr = False,
			name = None
		):
		'''Generate partition and file system'''
		if loghead:
			loghead = Path(loghead)
		else:
			loghead = __parent_path__/'wipe-head.txt'
		if not name:
			name = 'Volume'
		stdout, stderr = LinUtils.init_dev(target, mbr=mbr, fs=fs)
		if stderr:
			self.log.warning(stderr, echo=True)
		for retry in range(10):
			sleep(1)
			stdout, stderr = LinUtils.lsblk(target)
			try:
				partition = stdout[1]['path']
				break
			except IndexError:
				if retry < 9:
					continue
				self.log.error('Could not create new partition')
		stdout, stderr = LinUtils.mkfs(partition, fs=fs, label=name)
		if stderr:
			self.log.warning(stderr, echo=True)
		mnt = ExtPath.mkdir(self.outdir/'mnt')
		stdout, stderr = LinUtils.mount(partition, mnt)
		if stderr:
			self.log.error(stderr)
		self.log.close()
		log_path = mnt/'wipe-log.txt'
		try:
			head = loghead.read_text()
		except FileNotFoundError:
			head = ''
		with log_path.open('w') as fh:
			fh.write(head + self.log.path.read_text())
		stdout, stderr = LinUtils.umount(mnt)
		if stderr:
			raise RuntimeError(stderr)
		mnt.rmdir()

class WipeRCli(ArgumentParser):
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
			help='Create partition [fat32/exfat/ntfs] after wiping a physical drive',
			metavar='STRING'
		)
		self.add_argument('-f', '--value', type=str,
			help='Byte to overwrite with as hex (00 - ff)',
			metavar='HEX_BYTE'
		)
		self.add_argument('-g', '--loghead', type=Path,
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
		self.add_argument('targets', nargs='*', type=str,
			help='Target blockdevice or file(s) (/dev/sdc)', metavar='BLOCKDEVICE/FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.targets = args.targets
		self.allbytes = args.allbytes
		self.blocksize = args.blocksize
		self.create = args.create
		self.loghead = args.loghead
		self.maxbadblocks = args.maxbadblocks
		self.maxretries = args.maxretries
		self.mbr = args.mbr
		self.name = args.name
		self.outdir = args.outdir
		self.value = args.value
		self.verify = args.verify
		self.extra = args.extra

	def run(self, echo=print):
		'''Run zd'''
		if self.verify and (self.create or self.extra or self.mbr or self.driveletter or self.name):
			raise RuntimeError(f'Arguments incompatible with --verify/-v')
		wiper = WipeR(self.targets,
			allbytes = self.allbytes,
			blocksize = self.blocksize,
			maxbadblocks = self.maxbadblocks,
			maxretries = self.maxretries,
			outdir = self.outdir,
			value = self.value,
			verify = self.verify,
			extra = self.extra,
			echo = echo
		)
		if self.create:
			#if not wiper.physicaldrive:
			#	wiper.log.error('Unable to create a oartition after wiping file(s)')
			if wiper.zd_error:
				wiper.log.error('Wipe process terminated with errors, no partition will be created')
			wiper.mkfs(self.targets[0],
				fs = self.create,
				loghead = self.loghead,
				mbr = self.mbr,
				name = self.name
			)
		wiper.log.close()

class WipeRGui:
	'''Notebook page'''

	CMD = __app_name__
	DESCRIPTION = __description__
	DEF_BLOCKSIZE = 4096
	BLOCKSIZES = (512, 1024, 2048, 4096, 8192, 16384, 32768)
	DEF_VALUE = '0x00'
	DEF_MAXBADBLOCKS = '200'
	DEF_MAXRETRIES = '200'
	TABLES = ('GPT', 'MBR')
	DEF_TABLE = 'GPT'
	FS = ('NTFS', 'exFAT', 'FAT32')
	DEF_FS = 'NTFS'

	def __init__(self, root):
		'''Notebook page'''
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
			(root.NORMAL_WIPE, root.ALL_BYTES, root.EXTRA_PASS, root.VERIFY), root.NORMAL_WIPE)
		GridLabel(root, frame, root.NORMAL_WIPE, column=1)
		GridLabel(root, frame, root.ALL_BYTES, column=1)
		GridLabel(root, frame, root.EXTRA_PASS, column=1)
		GridLabel(root, frame, root.VERIFY, column=1)
		''''
		root.row -= 4
		GridIntMenu(root, frame, root.BLOCKSIZE, root.BLOCKSIZE, self.BLOCKSIZES,
			default=self.DEF_BLOCKSIZE, column=3)
		root.row -= 1
		GridStringMenu(root, frame, root.PARTITION_TABLE, root.PARTITION_TABLE,
			([root.DO_NOT_CREATE] + list(self.TABLES)), default=self.DEF_TABLE, column=4)
		root.row -= 1
		GridStringMenu(root, frame, root.FILE_SYSTEM, root.FILE_SYSTEM,
			([root.DO_NOT_CREATE] + list(self.FS)), default=self.DEF_FS, column=6)
		root.row -= 1
		GridStringMenu(root, frame, root.DRIVE_LETTER, root.DRIVE_LETTER,
			([root.NEXT_AVAILABLE] + self.get_free_letters()),
			default=root.NEXT_AVAILABLE, column=8)
		root.row += 1
		StringSelector(root, frame, root.VALUE, root.VALUE, default=self.DEF_VALUE,
			width=root.SMALL_FIELD_WIDTH, column=3)
		root.row -= 1
		StringSelector(root, frame, root.VOLUME_NAME, root.VOLUME_NAME,
			default=root.DEFAULT_VOLUME_NAME, width=root.SMALL_FIELD_WIDTH, column=6, columnspan=2)
		StringSelector(root, frame, root.MAXBADBLOCKS, root.MAXBADBLOCKS, default=self.DEF_MAXBADBLOCKS,
			width=root.SMALL_FIELD_WIDTH, column=3)
		root.row -= 1
		StringSelector(root, frame, root.MAXRETRIES, root.MAXRETRIES, default=self.DEF_MAXRETRIES,
			width=root.SMALL_FIELD_WIDTH, column=6, columnspan=2)
		GridSeparator(root, frame)
		GridLabel(root, frame, root.CONFIGURATION)
		FileSelector(root, frame, root.LOG_HEAD, root.LOG_HEAD, root.SELECT_TEXT_FILE,
			default=__parent_path__/'hdzero_log_head.txt',
			command=self._notepad_log_head, columnspan=8)
		FileSelector(root, frame, root.EXE, root.EXE, root.SELECT_EXE,
			filetype=(root.EXE, '*.exe'), default=__zd_exe_path__, columnspan=8)
		'''
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
		for drive_id, drive_info in WinUtils().list_drives():
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
		zd_exe = self.root.settings.get(self.root.EXE)
		if zd_exe:
			cmd += f' --zd "{zd_exe}"'
		to_do = self.root.settings.get(self.root.TO_DO)
		if to_do == self.root.ALL_BYTES:
			cmd += f' --allbytes'
		elif to_do == self.root.EXTRA_PASS:
			cmd += f' --extra'
		elif to_do == self.root.VERIFY:
			cmd += f' --verify'
		blocksize = self.root.settings.get(self.root.BLOCKSIZE)
		cmd += f' --blocksize {blocksize}'
		value = self.root.settings.get(self.root.VALUE)
		if value:
			try:
				int(value, 16)
			except ValueError:
				showerror(
					title = self.root.WRONG_ENTRY,
					message = self.root.NEED_HEX
				)
				return
			if int(value, 16) < 0 or int(value, 16) > 0xff:
				showerror(
					title = self.root.WRONG_ENTRY,
					message = self.root.BYTE_RANGE
				)
				return
			cmd += f' --value {value}'
		maxbadblocks = self.root.settings.get(self.root.MAXBADBLOCKS)
		if maxbadblocks:
			try:
				int(maxbadblocks)
			except ValueError:
				showerror(
					title = self.root.WRONG_ENTRY,
					message = f'{self.root.NEED_INT} "{self.root.MAXBADBLOCKS}"'
				)
				return
			cmd += f' --maxbadblocks {maxbadblocks}'
		maxretries = self.root.settings.get(self.root.MAXRETRIES)
		if maxretries:
			try:
				int(maxretries)
			except ValueError:
				showerror(
					title = self.root.WRONG_ENTRY,
					message = f'{self.root.NEED_INT} "{self.root.MAXRETRIES}"'
				)
				return
			cmd += f' --maxretries {maxretries}'
		partition_table = self.root.settings.get(self.root.PARTITION_TABLE)
		file_system = self.root.settings.get(self.root.FILE_SYSTEM)
		if (
			target_is_pd
			and to_do != self.root.VERIFY
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
				and askyesno(
					title = self.root.DRIVE_LETTER_TAKEN,
					message = self.root.USE_IT_ANYWAY
				)
			):
				cmd += f' --driveletter {drive_letter}'
			log_head = self.root.settings.get(self.root.LOG_HEAD)
			if log_head:
				cmd += f' --loghead "{log_head}"'
		if self.is_physical_drive(target):
			cmd += f' {target}'
		else:
			for target in self.filenames:
				cmd += f' "{target}"'
		self.root.append_job(cmd)

if __name__ == '__main__':	# start here if called as application
	app = WipeRCli()
	app.parse()
	app.run()
