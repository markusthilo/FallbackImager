#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'HdZero'
__author__ = 'Markus Thilo'
__version__ = '0.0.8_2023-06-15'
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
from functools import partial
from subprocess import Popen, PIPE, STDOUT, STARTUPINFO, STARTF_USESHOWWINDOW, TimeoutExpired
from threading import Thread
from argparse import ArgumentParser
from tkinter import StringVar
from tkinter.ttk import Frame, Radiobutton, Button, Checkbutton
from tkinter.messagebox import showerror
from tkinter.filedialog import askopenfilenames
from tkinter.scrolledtext import ScrolledText
from lib.extpath import ExtPath, FilesPercent
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.mfdbreader import MfdbReader
from lib.tsvreader import TsvReader
from lib.guielements import SourceDirSelector, Checker, LeftLabel, GridIntMenu
from lib.guielements import ChildWindow, SelectTsvColumn, FilesSelector
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

	WINCMD_TIMEOUT = 30
	WINCMD_RETRIES = 10
	WINCMD_DELAY = 1

	def __init__(self, zerod=None):
		'''Generate Windows tools'''
		if zerod:
			self.zerod_path = Path(zerod)
		elif __zerod_exe_path__:
			self.zerod_path = __zerod_exe_path__
		else:
			raise FileNotFoundError('Unable to locate zerod.exe')
		self.conn = WMI()
		self.cmd_startupinfo = STARTUPINFO()
		self.cmd_startupinfo.dwFlags |= STARTF_USESHOWWINDOW
		self.process_id = GetCurrentProcessId()
		self.tmpscriptpath = __parent_path__/f'_script_{self.process_id}.tmp'
		self.this_drive = self.zerod_path.drive

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

	def create_partition(self, drive_id, label='Volume', letter=None, mbr=False, fs='ntfs'):
		'Create partition using diskpart'
		try:
			drive_no = drive_id[17:]
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
			writelog = None,
			mount = None,
			name = 'Volume',
			task = 'normal',
			verbose = False,
			mbr = False,
			echo = print,
			log = None
		):
		super().__init__()
		not_admin = not IsUserAnAdmin()
		if task != 'list':
			if len(targets) < 1:
				raise ValueError('No target to wipe was given')
			if str(targets[0]).startswith('\\\\.\\PHYSICALDRIVE'):
				if len(targets) > 1:
					raise ValueError('Only one physical drive at a time')
				if blocksize % self.MIN_BLOCKSIZE != 0:
					raise ValueError(f'{target} is a block device and needs block size n*512 bytes')
				self.wipe_drive = True
			else:
				self.wipe_drive = False
		if not_admin and ( task == 'list' or self.wipe_drive):
			raise RuntimeError('Admin rights required to access block devices')
		if blocksize <= 0 or blocksize > self.MAX_BLOCKSIZE:
			raise ValueError(f'Block size out of range (max. {self.MAX_BLOCKSIZE} bytes)')
		self.targets = targets
		self.blocksize = blocksize
		self.create = create
		self.ff = ff
		self.mount = mount
		self.task = task
		self.verbose = verbose
		self.mbr = mbr
		self.echo = echo
		if log:
			self.log = log
			self.writelog = None
		elif writelog:
			self.log = Logger(filename=f'_log_{self.process_id}.log', outdir=__parent_path__,
				head='hdzero.HdZero', echo=echo)
			if writelog:
				self.writelog = Path(writelog)
		else:
			self.log = None
			self.writelog = None

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
		for target in self.targets:
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
						self.log.info(msg, echo=True)
					else:
						self.echo(msg)
			error = proc.stderr.read()
			if error:
				if self.log:
					self.log.warning(error)
				else:
					self.echo(error)
		if self.wipe_drive:
			return self.create_partition(self.targets[0],
				label = self.name,
				letter = self.mount,
				mbr = self.mbr,
				fs = self.create
			)

	def write_logfile(self, letter):
		'''Write log to new volume'''
		self.log_path = Path(f'{letter}:\\hdzero-log.txt')
		with self.log_path.open('w') as fh:
			fh.write(self.writelog.read_text() + self.log.path.read_text())

class HdZeroCli(ArgumentParser):
	'''CLI, also used for GUI of FallbackImager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-b', '--blocksize', default=4096, type=int,
			help='Block size', metavar='INTEGER'
		)
		self.add_argument('-c', '--create', type=str, choices=['ntfs', 'fat32', 'exfat'],
			help='Create partition (when target is a physical drive)', metavar='STRING'
		)
		self.add_argument('-f', '--ff', default=False, action='store_true',
			help='Fill with binary ones / 0xFF instad of zeros'
		)
		self.add_argument('-l', '--log', default=Path('hdzerologhead.txt'), type=Path,
			help='Write log file using the given file as head (when target is a physical drive)',
			metavar='FILE'
		)
		self.add_argument('-m', '--mount', type=str,
			help='Assign letter to wiped drive (when target is a physical drive)',
			metavar='DRIVE LETTER'
		)
		self.add_argument('-n', '--name', type=str,
			help='Name/label of the new partition (when target is a physical drive)',
			metavar='STRING'
		)
		self.add_argument('-t', '--task', type=str, default='normal',
			choices=['normal', 'all', 'extra', 'check', 'list'],
			help='Task to perform: normal, all, extra, check or list', metavar='STRING'
		)
		self.add_argument('-v', '--verbose', default=False, action='store_true',
			help='Verbose, print all warnings'
		)
		self.add_argument('-r', '--mbr', default=False, action='store_true',
			help='Use mbr instead of gpt Partition table (when target is a physical drive)'
		)
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
		self.writelog = args.log
		self.mount = args.mount
		self.name = args.name
		self.task = args.task
		self.verbose = args.verbose
		self.mbr = args.mbr

	def run(self, echo=print):
		'''Run AxChecker'''
		hdzero = HdZero(self.targets,
			blocksize = self.blocksize,
			create = self.create,
			ff = self.ff,
			writelog = self.writelog,
			mount = self.mount,
			name = self.name,
			task = self.task,
			verbose = self.verbose,
			mbr = self.mbr,
			echo = echo
		)
		hdzero.run()
		hdzero.log.close()

class DriveWorker(Thread):
	'''Wipe drive'''

	def __init__(self, gui, drive_id, drive_letters):
		'''Give job list and info handler to Worker object'''
		super().__init__()
		self.gui = gui
		self.drive_id = drive_id
		self.drive_letters = drive_letters

	def run(self):
		'''Start the work'''
		self.gui.disable_start()
		echo = self.gui.append_info
		echo('drive_id:', self.drive_id)
		echo('drive_letters:', self.drive_letters)
		
		self.gui.enable_start()

class HdZeroGui(WinUtils):
	'''Notebook page'''

	CMD = __app_name__
	DESCRIPTION = __description__
	DEF_BLOCKSIZE = 4096
	BLOCKSIZES = (512, 1024, 2048, 4096, 8192, 16384, 32768,
		65536, 131072, 262144, 524288, 1048576)

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

	def _select_drive(self):
		'''Select drive to wipe'''
		if self.root.child_win_active:
			return
		self.drive_window = ChildWindow(self.root, self.root.SELECT_DRIVE)
		self.root.settings.section = self.CMD
		self.drive_list_outer_frame = ExpandedFrame(self.root, self.drive_window)
		self.gen_drive_list_frame()
		frame = ExpandedFrame(self.root, self.drive_window)
		LeftButton(self.root, frame, self.root.REFRESH, self.gen_drive_list_frame)
		RightButton(self.root, frame, self.root.QUIT, self.drive_window.destroy)

	def _process_drive(self, drive_id, drive_letters):
		'''Is run when dirive got selected'''
		self.log_head_path = self.root.settings.get(self.root.LOG_HEAD)
		self.zerod_path = self.root.settings.get(self.root.ZEROD_EXE)
		self.root.settings.write()
		self.worker = DriveWorker(self.root, drive_id, drive_letters)
		self.worker.start()
		self.drive_window.destroy()

	def _select_files(self):
		filenames = askopenfilenames(title=self.root.ASK_FILES)
		if filenames:
			print(filenames)
			self.zerod_path = self.root.settings.get(self.root.ZEROD_EXE)

if __name__ == '__main__':	# start here if called as application
	app = HdZeroCli()
	app.parse()
	app.run()