#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'HdZero'
__author__ = 'Markus Thilo'
__version__ = '0.0.8_2023-06-12'
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
from argparse import ArgumentParser
from tkinter import StringVar
from tkinter.ttk import Frame, Radiobutton, Button, Checkbutton
from tkinter.messagebox import showerror
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
			startupinfo = self.cmd_startupinfo,
			stdout = PIPE,
			stderr = PIPE,
			universal_newlines = True
		)

	def list_drives(self):
		'Use DiskDrive'
		drives = { drive.Index: drive for drive in self.conn.Win32_DiskDrive() }
		for i in sorted(drives.keys()):
			yield drives[i]

	def get_drive(self, diskindex):
		'Get DiskDrive to given DiskIndex'
		for drive in self.conn.Win32_DiskDrive():
			if drive.index == diskindex:
				return drive

	def get_partitions(self, diskindex):
		'Get Partition to given DiskIndex'
		for part in self.conn.Win32_LogicalDiskToPartition():
			if part.Antecedent.DiskIndex == diskindex:
				yield part

	def dismount_drives(self, driveletters):
		'Dismount Drives'
		for driveletter in driveletters:
			proc = self.cmd_launch(['mountvol', driveletter, '/p'])
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
		proc = self.cmd_launch(['diskpart', '/s', self.tmpscriptpath])
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

	def create_partition(self, driveid, label, letter=None, table='gpt', fs='ntfs'):
		'Create partition using diskpart'
		try:
			driveno = driveid[17:]
		except:
			return
		if not letter:
			usedletters = GetLogicalDriveStrings().split(':\\\x00')
			for char in range(ord('D'),ord('Z')+1):
				if not chr(char) in usedletters:
					pure_letter = chr(char)
					break
			else:
				return
			letter = pure_letter + ':'
		else:
			pure_letter = letter.strip(':')
		ret = self.run_diskpart(f'''select disk {driveno}
clean
convert {table}
create partition primary
format quick fs={fs} label={label}
assign letter={pure_letter}
''')
		for cnt in range(self.WINCMD_RETRIES):
			if Path(letter).exists():
				return letter
			sleep(self.WINCMD_DELAY)

class HdZero(WinUtils):
	'''Use zerod.exe'''

	MIN_BLOCKSIZE = 512
	MAX_BLOCKSIZE = 1048576

	def __init__(self, targets,
			blocksize = 4096,
			ff = False,
			writelog = None,
			task = 'normal',
			verbose = False,
			echo = print,
			log = None,
		):
		not_admin = not IsUserAnAdmin()
		bs_not_512n = blocksize % self.MIN_BLOCKSIZE != 0
		for target in targets:
			if target.is_block_device():
				if not_admin:
					raise RuntimeError(f'Admin rights required to access block device {target}')
				if bs_not_512n:
					raise ValueError(f'{target} is a block device and needs block size n*512 bytes')
		if blocksize <= 0 or blocksize > self.MAX_BLOCKSIZE:
			raise ValueError('Block size out of range (<={self.MAX_BLOCKSIZE})')
		super().__init__()
		self.targets = targets
		self.blocksize = blocksize
		self.ff = ff
		self.writelog = writelog
		self.task = task
		self.verbose = verbose
		self.echo = echo
		if log:
			self.log = log
			self.tmplogpath = None
		else:
			self.log = Logger(filename=f'_log_{self.process_id}.tmp', outdir=__parent_path__,
				head='hdzero.HdZero', echo=echo)
			self.tmplogpath = __parent_path__/f'_log_{self.process_id}.tmp'

	def zerod_get_size(self, target_path):
		'Use zerod.exe toget file or disk size'
		proc = self.cmd_launch([self.zerod_path, target_path, '/p'])
		proc.wait(timeout=self.WINCMD_TIMEOUT)
		try:
			return proc.stdout.read().split()[4]
		except:
			return

	def zerod_launch(self, target_path):
		'''Use zerod.exe to wipe file or drive'''
		cmd = [self.zerod_path, target_path]
		if self.task == 'print':
			return self.zerod_get_size(target_path)
		elif self.task == 'extra':
			cmd.append('/x')
		elif self.task == 'all':
			cmd.append('/a')
		elif self.task == 'check':
			cmd.append('/c')
		if self.ff:
			cmd.append('/f')
		if self.verbose:
			cmd.append('/v')
		self.echo(f'Running {cmd}')
		return self.cmd_launch(cmd)

	def run(self):
		'''Run zerod + write log to file'''
		if self.task == 'print':
			for target in self.targets:
				self.echo(f'{target}: {self.zerod_get_size(target)} bytes')
		else:
			for target in self.targets:
				proc = self.zerod_launch(target)
				for line in proc.stdout:
					self.echo(line.strip())

class HdZeroCli(ArgumentParser):
	'''CLI, also used for GUI of FallbackImager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-b', '--blocksize', default=4096, type=int,
			help='Block size', metavar='INTEGER'
		)
		self.add_argument('-f', '--ff', default=False, action='store_true',
			help='Fill with binary ones / 0xFF instad of zeros'
		)
		self.add_argument('-l', '--log', default=Path('hdzerologhead.txt'), type=Path,
			help='Write log file using the given file as head', metavar='FILE'
		)
		self.add_argument('-t', '--task', type=str, default='normal',
			choices=['normal', 'all', 'extra', 'check', 'print'],
			help='Task to perform: normal, all, extra, check or print', metavar='STRING'
		)
		self.add_argument('-v', '--verbose', default=False, action='store_true',
			help='Verbose, print all warnings'
		)
		self.add_argument('targets', nargs='+', type=Path,
			help='AXIOM Case (.mfdb) / SQLite data base file', metavar='FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.targets = args.targets
		self.blocksize = args.blocksize
		self.ff = args.ff
		self.writelog = args.log
		self.task = args.task
		self.verbose = args.verbose

	def run(self, echo=print):
		'''Run AxChecker'''
		hdzero = HdZero(self.targets,
			blocksize = self.blocksize,
			ff = self.ff,
			writelog = self.writelog,
			task = self.task,
			verbose = self.verbose,
			echo = echo
		)
		hdzero.run()
		hdzero.log.close()

class HdZeroGui:
	'''Notebook page'''

	CMD = __app_name__
	DESCRIPTION = __description__
	DEF_BLOCKSIZE = 4096
	BLOCKSIZES = (512, 1024, 2048, 4096, 8192, 16384, 32768,
		65536, 131072, 262144, 524288, 1048576)

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		GridLabel(root, frame, root.WIPE_WARNING, columnspan=3)
		GridSeparator(root, frame)
		StringSelector(root, frame, root.DRIVE, root.DRIVE,
			command=self._select_drive)
		self.files_selector = FilesSelector(root, frame, root.FILES, root.FILES,
			root.ASK_FILES)
		StringRadiobuttons(root, frame, root.TO_DO,
			(root.NORMAL_WIPE, root.ALL_BLOCKS, root.EXTRA_PASS, root.CHECK),
			root.NORMAL_WIPE)
		GridLabel(root, frame, root.NORMAL_WIPE, column=1, columnspan=2)
		GridLabel(root, frame, root.ALL_BLOCKS, column=1, columnspan=2)
		GridLabel(root, frame, root.EXTRA_PASS, column=1, columnspan=2)
		GridLabel(root, frame, root.CHECK, column=1, columnspan=2)
		GridIntMenu(root, frame, root.BLOCKSIZE, root.BLOCKSIZE, self.BLOCKSIZES,
			default=self.DEF_BLOCKSIZE, column=1, columnspan=2)
		Checker(root, frame, root.USE_FF, root.USE_FF, column=1, columnspan=2)
		FileSelector(root, frame, root.LOG_HEAD, root.LOG_HEAD, root.SELECT_TEXT_FILE,
			command=None)
		GridSeparator(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job, columnspan=2)
		self.root = root

	def notepad_log_header(self):
		'Edit log header file with Notepad'
		proc = Popen(['notepad', self.log_header_path])
		proc.wait()

	def _select_drive(self):
		'''Select drive to wipe'''
		if self.root.child_win_active:
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
		self.partition_window = ChildWindow(self.root, self.root.SELECT_PARTITION)
		self._selected_part = StringVar()
		for source, partition in mfdb.partitions.values():
			partition_path = f'{source} - {partition}'
			frame = ExpandedFrame(self.root, self.partition_window)
			Radiobutton(frame, variable=self._selected_part, value=partition_path).pack(
				side='left', padx=self.root.PAD)
			LeftLabel(self.root, frame, partition_path)
		frame = ExpandedFrame(self.root, self.partition_window)
		LeftButton(self.root, frame, self.root.SELECT, self._get_partition)
		RightButton(self.root, frame, self.root.QUIT, self.partition_window.destroy)



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
		if not outdir or not filename:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.SOURCED_DEST_REQUIRED
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

class Gui:
	'GUI look and feel'

	PAD = 4
	BARLENGTH = 400
	WARNING_FG = 'red'
	WARNING_BG = 'white'
	
	SIZEBASE = (
		{ 'PiB': 2**50, 'TiB': 2**40, 'GiB': 2**30, 'MiB': 2**20, 'kiB': 2**10 },
		{ 'PB': 10**15, 'TB': 10**12, 'GB': 10**9, 'MB': 10**6, 'kB': 10**3 }
	)

	def __init__(self, debug=False):
		'Base Configuration'
		self.debug = debug
		if self.debug:
			print('DEBUG mode')
		self.__file_parentpath__ = Path(__file__).parent
		self.conf = Config(self.__file_parentpath__/'hdzero.conf')
		self.conf.read()
		WinUtils.__init__(self, self.__file_parentpath__)
		self.i_am_admin = self.is_user_an_admin()
		Logging.__init__(self, self.__file_parentpath__)
		self.app_info_str = self.conf['TEXT']['title'] + f' v{__version__}'
		Tk.__init__(self)
		self.title(self.app_info_str)
		self.app_icon = PhotoImage(file=self.__file_parentpath__/'icon.png')
		self.iconphoto(False, self.app_icon)
		self.resizable(False, False)
		self.protocol('WM_DELETE_WINDOW', self.quit_app)
		self.mainframe_user_opts = dict()
		self.working = False
		self.abort_work = False
		### MAIN FRAME ###
		frame = Frame(self)
		frame.pack(fill='both', expand=True)
		Label(
			frame,
			text = self.conf['TEXT']['head'],
			padding = self.PAD
		).pack(fill='both', expand=True, side='left')
		if not self.i_am_admin:
			frame = Frame(self)
			frame.pack(fill='both', expand=True)
			Label(
				frame,
				text = self.conf['TEXT']['notadmin'],
				foreground = self.WARNING_FG,
				background = self.WARNING_BG,
				padding=self.PAD
			).pack(fill='both', expand=True, side='left')
		### TARGET NOTBOOK ###
		notebook = Notebook(self)
		notebook.pack(padx=self.PAD, pady=self.PAD, expand=True)
		### DRIVES ###
		drives_nbf = Frame(notebook)
		drives_nbf.pack(fill='both', expand=True)
		notebook.add(drives_nbf, text=self.conf['TEXT']['drive'])
		self.drives_frame = Frame(drives_nbf, padding=self.PAD)
		self.drives_frame.pack(fill='both', expand=True)
		self.selected_target = StringVar()
		self.fill_drives_frame()
		### DISK OPTIONS FRAME ###
		frame = LabelFrame(drives_nbf, padding=self.PAD)
		frame.pack(padx=self.PAD, fill='both', expand=True)
		self.mainframe_user_opts['parttable'] = StringVar(value=self.conf['DEFAULT']['parttable'])
		Radiobutton(frame, variable=self.mainframe_user_opts['parttable'], value='None',
			text=self.conf['TEXT']['no_diskpart'], padding=(self.PAD, 0)).grid(row=0, column=0, sticky='w')
		Radiobutton(frame, variable=self.mainframe_user_opts['parttable'],
			value='gpt',
			text='GPT', padding=(self.PAD, 0)).grid(row=1, column=0, sticky='w')
		Radiobutton(frame, variable=self.mainframe_user_opts['parttable'],
			value='mbr',
			text='MBR', padding=(self.PAD, 0)).grid(row=2, column=0, sticky='w')
		self.mainframe_user_opts['fs'] = StringVar(value=self.conf['DEFAULT']['fs'])
		Radiobutton(frame, variable=self.mainframe_user_opts['fs'],
			value='ntfs', text='NTFS', padding=(self.PAD*4, 0)).grid(row=0, column=1, sticky='w')
		Radiobutton(frame, variable=self.mainframe_user_opts['fs'],
			value='exfat', text='exFAT', padding=(self.PAD*4, 0)).grid(row=1, column=1, sticky='w')
		Radiobutton(frame, variable=self.mainframe_user_opts['fs'],
			value='fat32', text='FAT32', padding=(self.PAD*4, 0)).grid(row=2, column=1, sticky='w')
		Label(frame, text=self.conf['TEXT']['volname']+':', padding=(self.PAD, 0)
			).grid(row=0, column=2, sticky='e')
		self.mainframe_user_opts['volname'] = StringVar(value=self.conf['DEFAULT']['volname'])
		Entry(frame, textvariable=self.mainframe_user_opts['volname']).grid(row=0, column=3, sticky='w')
		self.mainframe_user_opts['writelog'] = BooleanVar(value=self.conf['DEFAULT']['writelog'])
		Checkbutton(frame, text=self.conf['TEXT']['writelog'], variable=self.mainframe_user_opts['writelog'],
			onvalue=True, offvalue=False, padding=(self.PAD, 0)).grid(row=2, column=2, sticky='w')
		Button(frame, text=self.conf['TEXT']['editlog'],
			command=self.notepad_log_header).grid(row=2, column=3, sticky='w')
		### START / REFRESH DRIVE FRAME ###
		frame = Frame(drives_nbf, padding=self.PAD)
		frame.pack(fill='both', expand=True)
		self.start_drive_button = Button(
			frame,
			text = self.conf['TEXT']['start'],
			command = self.start_drive,
			state = DISABLED
		)
		self.start_drive_button.pack(side='left')
		Button(frame, text=self.conf['TEXT']['refresh'],
			command=self.refresh_drives_frame).pack(padx=self.PAD*4, side='left')
		### FILE(S) ###
		files_nbf = Frame(notebook)
		files_nbf.pack(fill='both', expand=True)
		notebook.add(files_nbf, text=self.conf['TEXT']['files'])
		frame = Frame(files_nbf)
		frame.pack(padx=self.PAD, pady=self.PAD, fill='both', expand=True)
		self.mainframe_user_opts['deletefiles'] = BooleanVar(value=self.conf['DEFAULT']['deletefiles'])
		Checkbutton(
			frame,
			text = self.conf['TEXT']['deletefiles'],
			variable = self.mainframe_user_opts['deletefiles'],
			onvalue = True,
			offvalue = False,
			padding = (self.PAD, 0)
		).pack(side='left')
		frame = Frame(files_nbf)
		frame.pack(padx=self.PAD, pady=self.PAD, fill='both', expand=True)
		self.start_files_button = Button(
			frame,
			text = self.conf['TEXT']['start'],
			command = self.start_files
		)
		self.start_files_button.pack(side='left')
		### OPTIONS FRAME ###
		frame = Frame(self, padding=self.PAD)
		frame.pack(fill='both', expand=True)
		frame = LabelFrame(frame, padding=(self.PAD*2, 0))
		frame.pack(fill='both', expand=True)
		self.mainframe_user_opts['job'] = StringVar(value=self.conf['DEFAULT']['job'])
		Radiobutton(frame, variable=self.mainframe_user_opts['job'], value='normal',
		text=self.conf['TEXT']['normal'], padding=(self.PAD, 0)).grid(row=0, column=0, sticky='w')
		Radiobutton(frame, variable=self.mainframe_user_opts['job'], value='extra',
		text=self.conf['TEXT']['extra'], padding=(self.PAD, 0)).grid(row=1, column=0, sticky='w')
		Radiobutton(frame, variable=self.mainframe_user_opts['job'], value='selective',
		text=self.conf['TEXT']['selective'], padding=(self.PAD, 0)).grid(row=2, column=0, sticky='w')
		Radiobutton(frame, variable=self.mainframe_user_opts['job'], value='check',
		text=self.conf['TEXT']['check'], padding=(self.PAD, 0)).grid(row=3, column=0, sticky='w')
		self.mainframe_user_opts['full_verify'] = BooleanVar(value=self.conf['DEFAULT']['full_verify'])
		Checkbutton(
			frame,
			text = self.conf['TEXT']['full_verify'],
			variable = self.mainframe_user_opts['full_verify'],
			onvalue = True,
			offvalue = False,
			padding = (self.PAD*4, 0)
		).grid(row=0, column=1, sticky='w')
		self.mainframe_user_opts['ff'] = BooleanVar(value=self.conf['DEFAULT']['ff'])
		Checkbutton(
			frame,
			text = self.conf['TEXT']['ff'],
			variable = self.mainframe_user_opts['ff'],
			onvalue = True,
			offvalue = False,
			padding = (self.PAD*4, 0)
		).grid(row=1, column=1, sticky='w')
		Label(frame, text=self.conf['TEXT']['blocksize']+':'#)#, padding=(self.PAD*4, 0)
			).grid(row=3, column=2, sticky='e')
		self.mainframe_user_opts['blocksize'] = StringVar(value=self.conf['DEFAULT']['blocksize'])
		OptionMenu(
			frame,
			self.mainframe_user_opts['blocksize'],
			self.conf['DEFAULT']['blocksize'],
			*self.BLOCKSIZES
		).grid(row=3, column=3, sticky='w')
		### BOTTOM ###
		frame = Frame(self, padding=self.PAD)
		frame.pack(fill='both', expand=True)
		self.mainframe_user_opts['askmore'] = BooleanVar(value=self.conf['DEFAULT']['askmore'])
		Checkbutton(
			frame,
			text = self.conf['TEXT']['askmore'],
			variable = self.mainframe_user_opts['askmore'],
			onvalue = True, offvalue = False
		).pack(padx=self.PAD, side='left')
		self.quit_button = Button(frame, text=self.conf['TEXT']['quit'], command=self.quit_app)
		self.quit_button.pack(side='right')

	def readable(self, size):
		'Genereate readable size string'
		try:
			size = int(size)
		except (TypeError, ValueError):
			return self.conf['TEXT']['undetected']
		strings = list()
		for base in self.SIZEBASE:
			for u, b in base.items():
				rnd = round(size/b, 2)
				if rnd >= 1:
					break
			if rnd >= 10:
				rnd = round(rnd,1)
			if rnd >= 100:
				rnd = round(rnd)
			strings.append(f'{rnd} {u}')
		return ' / '.join(strings)

	def list_to_string(self, strings):
		'One per line'
		if len(strings) <= 20:
			return ':\n' + '\n '.join(strings)
		else:
			return ':\n' + '\n '.join(strings[:20]) + f'\n... {len(strings)-20} ' + self.conf['TEXT']['more']

	def clear_frame(self, frame):
		'Destroy all widgets in frame'
		for child in frame.winfo_children():
			child.destroy()

	def decode_settings(self):
		'Decode settings and write as default to config file'
		self.options = { setting: tkvalue.get() for setting, tkvalue in self.mainframe_user_opts.items() } 
		for option, value in self.options.items():
			self.conf['DEFAULT'][option] = str(value)
		self.conf.write()

	def fill_drives_frame(self):
		'Drive section'
		Label(self.drives_frame, text=self.conf['TEXT']['mounted']).grid(row=0, column=1, sticky='w')
		Label(self.drives_frame, text=self.conf['TEXT']['details']).grid(row=0, column=2, sticky='w')
		row = 1
		for drive in self.list_drives():
			button = Radiobutton(
				self.drives_frame,
				text = f'{drive.index}',
				command = self.enable_start_drive_button,
				variable = self.selected_target,
				value = drive.index,
				padding=(self.PAD*2, 0)
			)
			button.grid(row=row, column=0, sticky='w')
			partitions = [ part.Dependent.DeviceID for part in self.get_partitions(drive.index) ]
			p_label = Label(self.drives_frame, text=', '.join(partitions))
			p_label.grid(row=row, column=1, sticky='w')
			Label(
				self.drives_frame,
				text = f'{drive.Caption}, {drive.MediaType} ({self.readable(self.zerod_get_size(drive.DeviceID))})'
			).grid(row=row, column=2, sticky='w')
			if self.i_am_admin:
				if self.this_drive in partitions or 'C:' in partitions:
					p_label.configure(foreground=self.WARNING_FG, background=self.WARNING_BG)
			else:
				button.configure(state=DISABLED)
			row += 1

	def refresh_drives_frame(self):
		self.decode_settings()
		self.clear_frame(self.drives_frame)
		self.start_drive_button.configure(state=DISABLED)
		self.selected_target.set(None)
		self.fill_drives_frame()

	def enable_start_drive_button(self):
		'When target has been selected'
		if not self.working:
			self.start_drive_button.configure(state=NORMAL)

	def quit_app(self):
		'Write config an quit'
		if self.debug:
			print('DEBUG: gui.working:', self.working)
		if self.working and not self.confirm(self.conf['TEXT']['abort'] + '?'):
			return
		self.destroy()

	def confirm(self, question):
		'Additional Confirmations'
		question += '\n\n'
		question += self.conf['TEXT']['areyoushure']
		if not askquestion(self.conf['TEXT']['warning_title'], question) == 'yes':
			return False
		if self.options['askmore'] and not (
			askquestion(self.conf['TEXT']['warning_title'], self.conf['TEXT']['areyoureallyshure']) == 'yes'
			and askquestion(self.conf['TEXT']['warning_title'], self.conf['TEXT']['areyoufngshure']) == 'yes'
		):
			return False
		return True

	def open_work_frame(self):
		'Open frame to show progress and iconify main frame'
		self.working = True
		self.quit_button.configure(state=DISABLED)
		self.start_drive_button.configure(state=DISABLED)
		self.start_files_button.configure(state=DISABLED)
		self.work_frame = Toplevel(self)
		self.work_frame.iconphoto(False, self.app_icon)
		self.work_frame.title(self.conf['TEXT']['title'])
		self.work_frame.resizable(False, False)
		self.work_frame.protocol('WM_DELETE_WINDOW', self.set_abort_work)
		frame = Frame(self.work_frame)
		frame.pack(fill='both', expand=True)
		self.head_info = StringVar()
		Label(frame, textvariable=self.head_info).pack(padx=self.PAD, pady=self.PAD)
		self.main_info = StringVar()
		Label(frame, textvariable=self.main_info).pack(padx=self.PAD, pady=self.PAD)
		self.progressbar = Progressbar(frame, mode='indeterminate', length=self.BARLENGTH)
		self.progressbar.pack(padx=self.PAD, pady=self.PAD, fill='both', expand=True)
		self.progressbar.start()
		self.progress_info = StringVar()
		Label(frame, textvariable=self.progress_info).pack(padx=self.PAD, pady=self.PAD)
		Button(
			frame,
			text = self.conf['TEXT']['abort'],
			command = self.set_abort_work
		).pack(padx=self.PAD, pady=self.PAD, side='right')

	def close_work_frame(self):
		'Close work frame and show main'
		self.working = False
		self.abort_work = False
		self.quit_button.configure(state=NORMAL)
		self.start_files_button.configure(state=NORMAL)
		self.work_frame.destroy()

	def set_abort_work(self):
		'Write config an quit'
		if self.confirm(self.conf['TEXT']['abort'] + '?'):
			self.abort_work = True

	def watch_zerod(self, files_of_str = ''):
		'Handle output of zerod'
		of_str = self.conf['TEXT']['of']
		bytes_str = self.conf['TEXT']['bytes']
		pass_of_str = ''
		for msg_raw in self.zerod_proc.stdout:
			msg_split = msg_raw.split()
			msg = msg_raw.strip()
			if self.debug:
				print("DEBUG: zerod:", msg)
			info = None
			if msg_split[0] == '...':
				progress_str = files_of_str + pass_of_str + ' '
				progress_str += f'{msg_split[1]} {of_str} {msg_split[3]} {bytes_str}'
				self.progress_info.set(progress_str)
				self.progressbar['value'] = 100 * float(msg_split[1]) / float(msg_split[3])
			elif msg_split[0] == 'Calculating':
				continue
			elif msg_split[0] == 'Pass':
				pass_of_str = self.conf['TEXT']['pass'] + f' {msg_split[1]} {of_str} {msg_split[3]}'
			elif msg_split[0] == 'Testing':
				self.main_info.set(self.conf['TEXT']['testing_blocksize'] + f' {msg_split[3]} {bytes_str}')
			elif msg_split[0] == 'Using':
				self.blocksize = msg_split[4]
				self.main_info.set(self.conf['TEXT']['using_blocksize'] + f' {self.blocksize} {bytes_str}')
			elif msg_split[0] == 'Verifying':
				pass_of_str = ''
				info = self.conf['TEXT']['verifying']
				self.main_info.set(info)
			elif msg_split[0] == 'Verified':
				info = self.conf['TEXT']['verified'] + f' {msg_split[1]} {bytes_str}'
				self.main_info.set(info)
			elif msg_split[0] == 'All':
				info = f'{msg_split[2]} {bytes_str} '
				if msg_split[4] == 'are':
					info += self.conf['TEXT']['are'] + f' {msg_split[5]}'
				else:
					info += self.conf['TEXT']['written']
				self.main_info.set(info)
			elif msg_split[0] == 'Warning:':
				info = msg
				self.main_info.set(info)
			else:
				info = msg
			if info and self.options['writelog']:
				self.append_log(info)
			if self.abort_work:
				return

	def start_drive(self):
		'Star work process'
		target = self.selected_target.get()
		if not target:
			return
		self.decode_settings()
		diskindex = int(target)
		drive = self.get_drive(diskindex)
		if drive == None:
			self.refresh_drives_frame()
			return
		driveletters = [ part.Dependent.DeviceID for part in self.get_partitions(diskindex) ]
		if self.debug:
			print('DEBUG: gui.options:', self.options)
		if self.options['job'] != 'check':
			question = self.conf['TEXT']['drivewarning']
			question += f'\n\n{drive.DeviceID}\n{drive.Caption}, {drive.MediaType}\n'
			question += self.readable(drive.Size) + '\n'
			mounted = ''
			for driveletter in driveletters:
				mounted += f'\n{driveletter}'
				if driveletter == self.this_drive or driveletter == 'C:':
					mounted += ' - ' + self.conf['TEXT']['danger']
			if mounted != '':
				question += self.conf['TEXT']['mounted'] + mounted
			else:
				question += self.conf['TEXT']['nomounted']
			if not self.confirm(question):
				self.refresh_drives_frame()
				return
			stillmounted = self.dismount_drives(driveletters)
			if stillmounted:
				warning = self.conf['TEXT']['not_dismount'] + ' '
				warning += ', '.join(stillmounted)
				warning += '\n\n' + self.conf['TEXT']['dismount_manually']
				showwarning(title=self.conf['TEXT']['warning_title'], message=warning)
				self.refresh_drives_frame()
				return
		if driveletters != list():
			self.driveletter = driveletters[0]
		else:
			self.driveletter = None
		if self.options['writelog']:
			self.start_log(
				f'{self.app_info_str}\n{drive.Caption}, {drive.MediaType}, {self.readable(drive.Size)}'
			)
		self.work_target = drive.DeviceID
		self.open_work_frame()
		Thread(target=self.drive_worker).start()

	def drive_worker(self):
		'Worker for drive'
		self.head_info.set(self.work_target)
		if self.options['job'] != 'check':
			self.main_info.set(self.conf['TEXT']['cleaning_table'])
			self.clean_table(self.work_target)
		if self.abort_work:
			self.close_work_frame()
			return
		self.progressbar.stop()
		self.progressbar.configure(mode='determinate')
		self.progressbar['value'] = 0
		self.zerod_proc = self.zerod_launch(
			self.work_target,
			blocksize = self.options['blocksize'],
			job = self.options['job'],
			writeff = self.options['ff'],
			verify = self.options['full_verify']
		)
		self.watch_zerod()
		if self.abort_work:
			self.zerod_proc.terminate()
			self.close_work_frame()
			return
		if self.zerod_proc.wait() != 0:
			showerror(
				self.conf['TEXT']['error'],
				self.conf['TEXT']['errorwhile'] + f' {self.work_target} \n\n {self.zerod_proc.stderr.read()}'
			)
			self.close_work_frame()
			return
		self.progress_info.set('')
		self.quit_button.configure(state=DISABLED)
		mounted = None
		if self.options['parttable'] != 'None':
			self.main_info.set(self.conf['TEXT']['creatingpartition'])
			self.progressbar.configure(mode="indeterminate")
			self.progressbar.start()
			mounted = self.create_partition(
				self.work_target,
				self.options['volname'],
				table = self.options['parttable'],
				fs = self.options['fs'],
				letter = self.driveletter
			)
			if mounted:
				info = self.conf['TEXT']['newpartition'] + f' {mounted}'
				self.main_info.set(info)
			else:
				showwarning(
					title = self.conf['TEXT']['warning_title'],
					message = self.conf['TEXT']['couldnotcreate']
				)
			self.progressbar.stop()
			self.progressbar.configure(mode='determinate')
		self.progressbar['value'] = 100
		self.main_info.set('')
		self.progress_info.set('')
		if self.options['writelog']:
			self.log_timestamp()
			logpath = None
			if mounted:
				logpath = Path(mounted)/'hdzero-log.txt'
			else:
				filename = asksaveasfilename(title=self.conf['TEXT']['write_log'], defaultextension='.txt')
				if filename:
					logpath = Path(filename)
			self.write_log(logpath)
		self.main_info.set(self.conf['TEXT']['all_done'])
		showinfo(message=self.conf['TEXT']['all_done'])
		self.close_work_frame()

	def start_files(self):
		'Wipe selected file or files - launch thread'
		if self.options['check']:
			self.work_target = askopenfilenames(
				title=self.conf['TEXT']['filestocheck'],
				initialdir=self.conf['DEFAULT']['initialdir']
			)
		else:
			self.work_target = askopenfilenames(
				title=self.conf['TEXT']['filestowipe'],
				initialdir=self.conf['DEFAULT']['initialdir']
			)
		if len(self.work_target) < 1:
			self.refresh_main()
			return
		if not self.options['check']:
			question = self.conf['TEXT']['filewarning']
			question += self.list_to_string(self.work_target)
			if not self.confirm(question):
				self.refresh_main()
				return
		self.conf['DEFAULT']['initialdir'] = str(Path(self.work_target[0]).parent)
		self.decode_settings()
		self.options['writelog'] = False
		self.open_work_frame()
		Thread(target=self.files_worker).start()

	def files_worker(self):
		'Worker for files'
		of_str = self.conf['TEXT']['of']
		files_of_str = ''
		qt_files = len(self.work_target)
		file_cnt = 0
		errors = list()
		self.progressbar.stop()
		self.progressbar.configure(mode='determinate')
		for file in self.work_target:
			self.head_info.set(file)
			self.zerod_proc = self.zerod_launch(
				file,
				blocksize = self.options['blocksize'],
				extra = self.options['extra'],
				writeff = self.options['ff'],
				verify = self.options['full_verify'],
				check = self.options['check']
			)
			if qt_files > 1:
				file_cnt += 1
				files_of_str = self.conf['TEXT']['file'] + f' {file_cnt} {of_str} {qt_files}, '
			self.watch_zerod(files_of_str=files_of_str)
			if self.abort_work:
				self.zerod_proc.terminate()
				self.close_work_frame()
			return
			if self.zerod_proc.wait() == 0:
				if self.options['deletefiles'] and not self.options['check']:
					self.main_info.set(self.conf['TEXT']['deleting_file'])
					try:
						Path(file).unlink()
					except:
						errors.append(file)
			else:
				errors.append(file)
		
		self.progressbar.stop()
		self.progressbar.configure(mode='determinate')
		
		if qt_files > 1:
			self.head_info.set(f'{qt_files} ' + self.conf['TEXT']['files'])
		else:
			self.head_info.set('1 ' + self.conf['TEXT']['file'])
		self.main_info.set('')
		self.progress_info.set('')
		if errors == list():
			showinfo(message=self.conf['TEXT']['all_done'])
		else:
			self.main_info.set(self.conf['TEXT']['errorwhile'])
			showerror(
				self.conf['TEXT']['error'],
				self.conf['TEXT']['errorwhile'] + self.list_to_string(errors)
			)
		self.close_work_frame()




if __name__ == '__main__':	# start here if called as application
	app = HdZeroCli()
	app.parse()
	app.run()