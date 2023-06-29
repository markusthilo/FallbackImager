#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'HdZero'
__author__ = 'Markus Thilo'
__version__ = '0.1.0_2023-06-29'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Erases disks while not touching empty blocks/pages.
The tool is also capable of overwriting files but slack and files system artefacts
will remain. It is designed to securely wipe HDDs/SSDs and generate a protocol.
'''

from sys import executable as __executable__
from pathlib import Path
from wmi import WMI
from win32api import GetCurrentProcessId, GetLogicalDriveStrings
from win32com.shell.shell import IsUserAnAdmin
from time import sleep
from functools import partial
from subprocess import Popen, PIPE, STDOUT, STARTUPINFO, STARTF_USESHOWWINDOW, TimeoutExpired
from threading import Thread
from argparse import ArgumentParser
from tkinter import StringVar
from tkinter.ttk import Frame, Radiobutton, Button, Checkbutton
from tkinter.messagebox import askyesno
from tkinter.filedialog import askopenfilenames
from tkinter.scrolledtext import ScrolledText
from lib.extpath import ExtPath, FilesPercent
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.mfdbreader import MfdbReader
from lib.tsvreader import TsvReader
from lib.guielements import SourceDirSelector, Checker, LeftLabel, GridIntMenu
from lib.guielements import ChildWindow, SelectTsvColumn, FilesSelector, ExpandedLabelFrame
from lib.guielements import ExpandedFrame, GridSeparator, GridLabel, DirSelector
from lib.guielements import FilenameSelector, StringSelector, StringRadiobuttons
from lib.guielements import FileSelector, GridButton, LeftButton, RightButton

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

class WinUtils:
	'Needed Windows functions'

	WINCMD_TIMEOUT = 60
	WINCMD_RETRIES = 20
	WINCMD_DELAY = 1

	def __init__(self):
		'''Generate Windows tools'''
		self.conn = WMI()
		self.cmd_startupinfo = STARTUPINFO()
		self.cmd_startupinfo.dwFlags |= STARTF_USESHOWWINDOW
		self.process_id = GetCurrentProcessId()
		self.tmpscriptpath = __parent_path__/f'_script_{self.process_id}.tmp'

	def cmd_launch(self, cmd):
		'''Start command line subprocess without showing a terminal window'''
		return Popen(
			cmd,
			shell = True,
			stdout = PIPE,
			stderr = PIPE,
			encoding = 'utf-8',
			errors = 'ignore',
			universal_newlines = True,
			startupinfo = self.cmd_startupinfo
		)

	def list_drives(self):
		'''List drive infos, partitions and logical drives'''
		disk2part = {(rel.Antecedent.DeviceID, rel.Dependent.DeviceID)
			for rel in self.conn.Win32_DiskDriveToDiskPartition()
		}
		part2logical = {(rel.Antecedent.DeviceID, rel.Dependent.DeviceID)
			for rel in self.conn.Win32_LogicalDiskToPartition()
		}
		disk2logical = { logical: disk
			for disk, part_disk in disk2part
			for part_log, logical in part2logical
			if part_disk == part_log
		}
		log_disks = dict()
		for log_disk in self.conn.Win32_LogicalDisk():
			info = f'\n- {log_disk.DeviceID} '
			if log_disk.VolumeName:
				info += f'{log_disk.VolumeName}, '
			if log_disk.FileSystem:
				info += f'{log_disk.FileSystem}, '
			info += f'{ExtPath.readable_size(log_disk.Size)}'
			log_disks[log_disk.DeviceID] = info
		drives = dict()
		for drive in self.conn.Win32_DiskDrive():
			drive_info = f'{drive.Caption.strip()}, {drive.InterfaceType}, '
			drive_info += f'{drive.MediaType}, {ExtPath.readable_size(drive.Size)}'
			drives[drive.DeviceID] = drive_info
		for drive_id, drive_info in sorted(drives.items()):
			drive_letters = list()
			for log_id, disk_id in disk2logical.items():
				if disk_id == drive_id:
					try:
						drive_info += log_disks[log_id]
						drive_letters.append(log_id)
					except KeyError:
						continue
			yield drive_id, drive_info, drive_letters

	def dismount_drives(self, driveletters):
		'Dismount Drives'
		for driveletter in driveletters:
			proc = self.cmd_launch(f'mountvol {driveletter} /p')
			try:
				proc.wait(timeout=self.WINCMD_TIMEOUT)
			except:
				pass
		stillmounted = driveletters
		for cnt in range(self.WINCMD_RETRIES):
			for driveletter in stillmounted:
				if not Path(driveletter).exists():
					stillmounted.remove(driveletter)
			if stillmounted == list():
				return
			sleep(self.WINCMD_DELAY)
		return stillmounted

	def run_diskpart(self, script):
		'Run diskpart script'
		self.tmpscriptpath.write_text(script)
		proc = self.cmd_launch(f'diskpart /s {self.tmpscriptpath}')
		try:
			proc.wait(timeout=self.WINCMD_TIMEOUT)
		except TimeoutExpired:
			pass
		try:
			self.tmpscriptpath.unlink()
		except:
			pass
		return

	def clean_table(self, driveid):
		'Clean partition table using diskpart'
		try:
			driveno = driveid[17:]
		except:
			return
		self.run_diskpart(f'''select disk {driveno}
clean
'''
		)

	def create_partition(self, drive_path, label='Volume', letter=None, mbr=False, fs='ntfs'):
		'''Create partition using diskpart'''
		try:
			drive_no = str(drive_path)[17:].rstrip('\\')
		except:
			return
		if not letter:
			used_letters = GetLogicalDriveStrings().split(':\\\x00')
			for char in range(ord('D'),ord('Z')+1):
				if not chr(char) in used_letters:
					letter = chr(char)
					break
			else:
				return
		if mbr:
			table = 'mbr'
		else:
			table = 'gpt'
		self.run_diskpart(f'''select disk {drive_no}
clean
convert {table}
create partition primary
format quick fs={fs} label={label}
assign letter={letter}
''')
		for cnt in range(self.WINCMD_RETRIES):
			sleep(self.WINCMD_DELAY)
			if Path(f'{letter}:').exists():
				return letter

class HdZero(WinUtils):
	'''Use zerod.exe'''

	MIN_BLOCKSIZE = 512
	MAX_BLOCKSIZE = 1048576

	def __init__(self, targets,
			blocksize = 4096,
			create = 'ntfs',
			ff = False,
			loghead = None,
			mount = None,
			name = 'Volume',
			task = 'normal',
			verbose = False,
			mbr = False,
			zerod = __zerod_exe_path__,
			echo = print,
		):
		super().__init__()
		if zerod:
			self.zerod_path = Path(zerod)
		elif __zerod_exe_path__:
			self.zerod_path = __zerod_exe_path__
		else:
			raise FileNotFoundError('Unable to locate zerod.exe')
		not_admin = not IsUserAnAdmin()
		self.verbose = verbose
		self.log = None
		self.echo = echo
		self.task = task
		if task == 'list':
			if not_admin:
				raise RuntimeError('Admin rights required to list block devices')
		else:
			if len(targets) < 1:
				raise ValueError('No target to wipe was given')
			if str(targets[0]).startswith('\\\\.\\PHYSICALDRIVE'):
				if not_admin:
					raise RuntimeError('Admin rights required to access block devices')
				if len(targets) > 1:
					raise ValueError('Only one physical drive at a time')
				if blocksize and blocksize % self.MIN_BLOCKSIZE != 0:
					raise ValueError(f'{target} is a block device and needs block size n*512 bytes')
				if create:
					self.create = create.lower()
					if create == 'none':
						self.create = None
					else:
						self.log = Logger(
							filename = f'_log_{self.process_id}.log',
							outdir = __parent_path__,
							echo = echo,
							head = f'''hdzero.HdZero

HDZero Version {__version__}
Author: Markus Thilo
This wipe tool is part of the FallbackImager Project:
https://github.com/markusthilo/FallbackImager
GNU General Public License Version 3

'''
						)
						if loghead:
							self.loghead = Path(loghead)
				else:
					self.create = None
				self.wipe_drive = True
			else:
				self.wipe_drive = False
			if blocksize <= 0 or blocksize > self.MAX_BLOCKSIZE:
				raise ValueError(f'Block size out of range (max. {self.MAX_BLOCKSIZE} bytes)')
			self.targets = targets
			self.blocksize = blocksize
			self.ff = ff
			self.mount = mount
			self.name = name
			self.mbr = mbr

	def echo_drives(self):
		'''List drives and show infos'''
		for drive_id, drive_info, drive_letters in self.list_drives():
			self.echo(f'\n{drive_id} - {drive_info}')

	def zerod_launch(self, target_path):
		'''Use zerod.exe to wipe file or drive'''
		target = f'{target_path}'.rstrip('\\')
		cmd_str = f'{self.zerod_path} "{target}"'
		if self.task == 'extra':
			cmd_str += ' /x'
		elif self.task == 'all':
			cmd_str += ' /a'
		elif self.task == 'check':
			cmd_str += ' /c'
		if self.ff:
			cmd_str += ' /f'
		if self.verbose:
			cmd_str += ' /v'
		self.echo(f'Running {cmd_str}')
		return self.cmd_launch(cmd_str)

	def run(self):
		'''Run zerod + write log to file'''
		if self.task == 'list':
			self.echo_drives()
			return
		error = False
		for target in self.targets:
			self.echo()
			proc = self.zerod_launch(target)
			for line in proc.stdout:
				msg = line.strip()
				if msg.startswith('...'):
					if self.echo == print:
						print(f'\r{msg}', end='')
					else:
						self.echo(msg, overwrite=True)
				else:
					if self.log:
						self.log.write_ln(msg, echo=True)
					else:
						self.echo(msg)
			error = proc.stderr.read()
			if error:
				if self.log:
					self.log.warning(error)
				else:
					self.echo(error)
		if self.wipe_drive and not error:
			letter = self.create_partition(self.targets[0],
				label = self.name,
				letter = self.mount,
				mbr = self.mbr,
				fs = self.create
			)
			self.log.info('End of wipe process')
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
		if self.log:
			self.log.path.unlink()

class HdZeroCli(ArgumentParser):
	'''CLI, also used for GUI of FallbackImager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-b', '--blocksize', default=4096, type=int,
			help='Block size', metavar='INTEGER'
		)
		self.add_argument('-c', '--create', type=str,
			choices=['ntfs', 'fat32', 'exfat', 'none'], default='ntfs',
			help='Create partition (when target is a physical drive)', metavar='STRING'
		)
		self.add_argument('-f', '--ff', action='store_true',
			help='Fill with binary ones / 0xFF instad of zeros'
		)
		self.add_argument('-l', '--loghead',
			default=__parent_path__/'hdzero_log_head.txt', type=Path,
			help='Use the given file as head when writing log to new drive',
			metavar='FILE'
		)
		self.add_argument('-m', '--mount', type=str,
			help='Assign letter to wiped drive (when target is a physical drive)',
			metavar='DRIVE LETTER'
		)
		self.add_argument('-n', '--name', type=str, default='Volume',
			help='Name/label of the new partition (when target is a physical drive)',
			metavar='STRING'
		)
		self.add_argument('-t', '--task', type=str, default='normal',
			choices=['normal', 'all', 'extra', 'check', 'list'],
			help='Task to perform: normal, all, extra, check or list', metavar='STRING'
		)
		self.add_argument('-v', '--verbose', action='store_true',
			help='Verbose, print all warnings'
		)
		self.add_argument('-r', '--mbr', action='store_true',
			help='Use mbr instead of gpt Partition table (when target is a physical drive)'
		)
		self.add_argument('-z', '--zerod', type=Path, help='Path to zerod.exe', metavar='FILE')
		self.add_argument('targets', nargs='*', type=Path,
			help='AXIOM Case (.mfdb) / SQLite data base file', metavar='FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.targets = args.targets
		self.blocksize = args.blocksize
		self.create = args.create
		self.ff = args.ff
		self.loghead = args.loghead
		self.mount = args.mount
		self.name = args.name
		self.task = args.task
		self.verbose = args.verbose
		self.mbr = args.mbr
		self.zerod = args.zerod

	def run(self, echo=print):
		'''Run AxChecker'''
		HdZero(self.targets,
			blocksize = self.blocksize,
			create = self.create,
			ff = self.ff,
			loghead = self.loghead,
			mount = self.mount,
			name = self.name,
			task = self.task,
			verbose = self.verbose,
			mbr = self.mbr,
			echo = echo,
			zerod = self.zerod
		).run()

class Worker(Thread):
	'''Run HdZero as task'''

	def __init__(self, root, hdzero):
		'''Give GUI and HdZero to worker'''
		self.root = root
		self.hdzero = hdzero
		super().__init__()

	def run(self):
		'''Start the work'''
		self.hdzero.run()
		self.root.enable_start()

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
		super().__init__()
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		GridLabel(root, frame, root.WIPE, columnspan=2)
		GridSeparator(root, frame)
		Button(frame, text=root.DRIVE, command=self._select_drive).grid(
			row=root.row, column=1, sticky='w', padx=root.PAD)
		Button(frame, text=root.FILES, command=self._select_files).grid(
			row=root.row, column=2, sticky='w', padx=root.PAD)
		GridIntMenu(root, frame, root.BLOCKSIZE, root.BLOCKSIZE, self.BLOCKSIZES,
			default=self.DEF_BLOCKSIZE, column=3)
		StringRadiobuttons(root, frame, root.TO_DO,
			(root.NORMAL_WIPE, root.ALL_BLOCKS, root.EXTRA_PASS, root.CHECK),
			root.NORMAL_WIPE
		)
		GridLabel(root, frame, root.NORMAL_WIPE, column=1)
		GridLabel(root, frame, root.ALL_BLOCKS, column=1)
		GridLabel(root, frame, root.EXTRA_PASS, column=1)
		GridLabel(root, frame, root.CHECK, column=1)
		Checker(root, frame, root.USE_FF, root.USE_FF)
		FileSelector(root, frame, root.LOG_HEAD, root.LOG_HEAD, root.SELECT_TEXT_FILE,
			default=__parent_path__/'hdzero_log_head.txt',
			command=self.notepad_log_head, columnspan=3)
		FileSelector(root, frame, root.ZEROD_EXE, root.ZEROD_EXE, root.SELECT_ZEROD_EXE,
			filetype=(root.ZEROD_EXE, 'zerod.exe'), default=__zerod_exe_path__,columnspan=3)
		self.root = root
		self.root.child_win_active = False

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

	def _select_drive(self):
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

	def _process_drive(self, drive_id, drive_letters):
		'''Is run when dirive got selected'''
		self.root.settings.write()
		if self.root.start_disabled:
			return
		self.root.child_win_active = False
		self.drive_window.destroy()
		if askyesno(title=f'{self.root.WIPE} {drive_id}', message=self.root.AREYOUSURE):
			self.root.disable_start()
			if drive_letters:
				mount = drive_letters[0]
			else:
				mount = None
			self.root.settings.section = self.CMD
			if self.root.settings.get(self.root.PARTITION_TABLE) == 'GPT':
				create = self.root.settings.get(self.root.FILESYSTEM)
				mbr = False
			elif self.root.settings.get(self.root.PARTITION_TABLE) == 'MBR':
				create = self.root.settings.get(self.root.FILESYSTEM)
				mbr = True
			else:
				create = None
				mbr = False
			hdzero = HdZero([drive_id],
				task = self.root.settings.get(self.root.TO_DO),
				ff = self.root.settings.get(self.root.USE_FF),
				blocksize = self.root.settings.get(self.root.BLOCKSIZE),
				loghead = self.root.settings.get(self.root.LOG_HEAD),
				name = self.root.settings.get(self.root.PARTITION_NAME),
				mbr = mbr,
				create = create,
				mount = mount,
				echo = self.root.append_info,
				zerod = self.root.settings.get(self.root.ZEROD_EXE)
			)
			Worker(self.root, hdzero).start()

	def _select_files(self):
		self.root.settings.write()
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
			Worker(self.root, hdzero).start()

if __name__ == '__main__':	# start here if called as application
	app = HdZeroCli()
	app.parse()
	app.run()