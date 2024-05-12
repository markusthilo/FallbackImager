#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter.messagebox import showerror
from tkinter.ttk import Button
from tkinter.scrolledtext import ScrolledText
from functools import partial
from .guilabeling import WipeLabels
from .guiconfig import GuiConfig
from .guielements import MissingEntry, ChildWindow, Checker, GridMenu
from .guielements import ExpandedFrame, GridSeparator, GridLabel
from .guielements import DirSelector, OutDirSelector, NotebookFrame
from .guielements import FilenameSelector, StringSelector, StringRadiobuttons
from .guielements import FileSelector, LeftButton, RightButton, AddJobButton
from .linutils import LinUtils
from .stringutils import StringUtils

class WipeRGui(WipeLabels):
	'''Notebook page for WipeR'''

	MODULE = 'WipeR'
	DEF_BLOCKSIZE = 4096
	BLOCKSIZES = (512, 1024, 2048, 4096, 8192, 16384, 32768)
	DEF_MAXBADBLOCKS = '200'
	DEF_MAXRETRIES = '200'
	TABLES = (WipeLabels.NONE, 'GPT', 'MBR')
	DEF_TABLE = 'GPT'
	FS = ('NTFS', 'exFAT', 'FAT32', 'Ext4')
	DEF_FS = 'NTFS'

	def __init__(self, root):
		'''Notebook page'''
		self.root = root
		self.default_wlh_path = root.parent_path/'wipe-log-head.txt'
		frame = NotebookFrame(self)
		GridLabel(frame, self.WIPE)
		self.target = StringSelector(
			frame,
			self.root.settings.init_stringvar('Target'),
			self.TARGET,
			command=self._select_target,
			tip=self.TIP_TARGET
		)	
		self.target.set('')
		GridSeparator(frame)
		GridLabel(frame, self.LOGGING)
		self.outdir = OutDirSelector(frame, self.root.settings.init_stringvar('OutDir'))
		GridSeparator(frame)
		GridLabel(frame, self.MOUNTPOINT)
		self.mountpoint = DirSelector(
			frame,
			self.root.settings.init_stringvar('MountPoint'),
			self.SELECT_MOUNTPOINT,
			tip = self.TIP_MOUNTPOINT
		)
		GridSeparator(frame)
		GridLabel(frame, self.TASK)
		self.task = StringRadiobuttons(
			frame,
			self.root.settings.init_stringvar('Task', default='Normal'),
			('Normal', 'All', 'Extra', 'Verify')
		)
		GridLabel(frame, self.NORMAL_WIPE, column=1, columnspan=1, incrow=False)
		GridMenu(
			frame,
			self.root.settings.init_intvar('Blocksize', default=self.DEF_BLOCKSIZE),
			self.BLOCKSIZE,
			self.BLOCKSIZES,
			column = 2,
			incrow = False,
			tip = self.TIP_BLOCKSIZE
		)
		GridMenu(
			frame,
			self.root.settings.init_stringvar('PartitionTable', default=self.DEF_TABLE),
			self.PARTITION_TABLE,
			self.TABLES,
			column = 4,
			incrow = False,
			tip = self.TIP_PARTITION_TABLE
		)
		GridMenu(
			frame,
			self.root.settings.init_stringvar('FileSystem', default=self.DEF_FS),
			self.FILE_SYSTEM,
			self.FS,
			column = 6,
			incrow = False,
			tip = self.TIP_FILE_SYSTEM
		)
		self.part_name = StringSelector(
			frame,
			self.root.settings.init_stringvar('PartitionName'),
			self.PART_NAME,
			default = self.DEF_PART_NAME,
			width = GuiConfig.SMALL_FIELD_WIDTH,
			column = 8,
			columnspan = 2,
			tip = self.TIP_PART_NAME
		)
		GridLabel(frame, self.ALL_BYTES, column=1, columnspan=1, incrow=False)
		self.value = StringSelector(
			frame,
			self.root.settings.init_stringvar('Value', default='00'),
			self.VALUE,
			default = '00',
			width = GuiConfig.SMALL_FIELD_WIDTH,
			column = 3,
			tip = self.TIP_VALUE
		)
		GridLabel(frame, self.EXTRA_PASS, column=1, columnspan=1, incrow=False)
		self.max_bad_blocks = StringSelector(
			frame,
			self.root.settings.init_stringvar('MaxBadBlocks', default=self.DEF_MAXBADBLOCKS),
			self.MAXBADBLOCKS,
			default = self.DEF_MAXBADBLOCKS,
			width = GuiConfig.SMALL_FIELD_WIDTH,
			column = 3,
			incrow = False,
			tip = self.TIP_MAXBADBLOCKS
		)
		self.max_retries = StringSelector(
			frame,
			self.root.settings.init_stringvar('MaxRetries', default=self.DEF_MAXRETRIES),
			self.MAXRETRIES,
			default = self.DEF_MAXRETRIES,
			width = GuiConfig.SMALL_FIELD_WIDTH,
			column = 7,
			tip = self.TIP_MAXRETRIES
		)
		GridLabel(frame, self.VERIFY, column=1, columnspan=1, incrow=False)

		return

		GridSeparator(root, frame)
		GridLabel(root, frame, root.CONFIGURATION)
		FileSelector(root, frame, root.LOG_HEAD, root.LOG_HEAD, root.SELECT_TEXT_FILE,
			default=self.default_wlh_path,
			command=self._default_head, columnspan=8)
		GridSeparator(root, frame)
		GridBlank(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}',
			self._add_job, column=0, columnspan=3)
		root.child_win_active = False
		self.filenames = None

	def _default_head(self):
		'''Set default log header'''
		self.root.settings.section = self.CMD
		if self.root.settings.get(self.root.LOG_HEAD):
			return
		self.root.settings.raw(self.root.LOG_HEAD).set(self.default_wlh_path)

	def _select_target(self):
		'''Select drive to wipe'''
		if self.root.child_win_active:
			return
		self.target_window = ChildWindow(self.root, self.root.SELECT)
		self.root.settings.section = self.CMD
		frame = ExpandedFrame(self.root, self.target_window)
		self.root.row = 0
		GridLabel(self.root, frame, self.root.SELECT_SOURCE)
		for diskpath, diskinfo in LinUtils.diskinfo().items():
			infotext = f'Disk size: {StringUtils.join(diskinfo["disk"], delimiter=", ")}'
			for partition, info in diskinfo['partitions'].items():
				infotext += f'\n- {partition}: {StringUtils.join(info, delimiter=", ")}'
			Button(frame, text=diskpath, command=partial(self._put_drive, diskpath), width=self.root.BUTTON_WIDTH).grid(
				row=self.root.row, column=0, sticky='nw', padx=self.root.PAD)
			text = ScrolledText(frame, width=self.root.ENTRY_WIDTH,
				height=min(len(f'{(infotext)}'.split('\n')), self.root.MAX_ENTRY_HEIGHT ))
			text.grid(row=self.root.row, column=1)
			text.bind('<Key>', lambda dummy: 'break')
			text.insert('end', infotext)
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
		if not target and not self.filenames:
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
		cmd += f' --outdir "{outdir}"'
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
		if ( to_do != self.root.VERIFY
			and partition_table != self.root.DO_NOT_CREATE
			and file_system != self.root.DO_NOT_CREATE
		):
			if partition_table != self.TABLES[0]:
				cmd += f' --mbr'
			cmd += f' --create {file_system}'
			volume_name = self.root.settings.get(self.root.VOLUME_NAME)
			if volume_name:
				cmd += f' --name "{volume_name}"'
			log_head = self.root.settings.get(self.root.LOG_HEAD)
			if log_head:
				cmd += f' --loghead "{log_head}"'
		if target:
			cmd += f' {target}'
		else:
			for filename in self.filenames:
				cmd += f' "{filename}"'
		self.root.append_job(cmd)
