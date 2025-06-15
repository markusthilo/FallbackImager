#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import StringVar
from tkinter.ttk import Button
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilenames
from functools import partial
from .guilabeling import WipeLabels
from .guiconfig import GuiConfig
from .diskselectgui import DiskSelectGui
from .guielements import MissingEntry, ChildWindow, GridMenu
from .guielements import ExpandedFrame, GridSeparator, GridLabel
from .guielements import DirSelector, OutDirSelector, NotebookFrame
from .guielements import StringSelector, StringRadiobuttons
from .guielements import FileSelector, LeftButton, RightButton, AddJobButton
from .linutils import LinUtils
from .stringutils import StringUtils

class SelectTargetWindow(DiskSelectGui, WipeLabels):
	'''Gui to slect target to wipe'''

	def __init__(self, root, button):
		'''Window to select disk'''
		DiskSelectGui.__init__(self, root, self.SELECT_DRIVE_TO_WIPE, button, physical=True)

	def _main_frame(self):
		'''Main frame'''
		self.main_frame = ExpandedFrame(self)
		self.lsblk(self.main_frame)
		frame = ExpandedFrame(self.main_frame)
		LeftButton(frame, self.SELECT, self._select, tip=self.TIP_SELECT_TARGET)
		LeftButton(frame, self.REFRESH, self._refresh, tip=self.TIP_REFRESH_DEVS)
		LeftButton(frame, self.SELECT_FILES_TO_WIPE, self._select_files, tip=self.TIP_FILES_TO_WIPE)
		RightButton(frame, self.QUIT, self.quit)

	def _select_files(self):
		'''Choose file(s) to wipe'''
		self.quit()
		filenames = [f'"{filename}"' for filename in askopenfilenames(title=self.SELECT_FILES_TO_WIPE)]
		if filenames:
			self.button.set(' '.join(filenames))
		else:
			self.button.set('')

class WipeRGui(WipeLabels):
	'''Notebook page for WipeR'''

	MODULE = 'WipeR'
	DEF_BLOCKSIZE = 4096
	BLOCKSIZES = (512, 1024, 2048, 4096, 8192, 16384, 32768)
	DEF_MAXBADBLOCKS = '200'
	DEF_MAXRETRIES = '200'
	TABLES = ('-', 'GPT', 'MBR')
	DEF_TABLE = 'GPT'
	FS = ('-', 'NTFS', 'exFAT', 'FAT32', 'Ext4')
	DEF_FS = 'NTFS'

	def __init__(self, root):
		'''Notebook page'''
		self.root = root
		self.default_wlh_path = root.parent_path/'wipe-log-head.txt'
		frame = NotebookFrame(self)
		GridLabel(frame, self.WIPE)
		self.target = StringSelector(
			frame,
			StringVar(value=self.TARGET_WARNING),
			self.TARGET,
			command=self._select_target,
			tip=self.TIP_TARGET
		)
		GridSeparator(frame)
		GridLabel(frame, self.LOGGING)
		self.outdir = OutDirSelector(frame, self.root.settings.init_stringvar('OutDir'))
		GridSeparator(frame)
		GridLabel(frame, self.MOUNTPOINT)
		self.mountpoint = DirSelector(
			frame,
			self.root.settings.init_stringvar('MountPoint'),
			self.DIRECTORY,
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
		self.max_bad_blocks = StringSelector(
			frame,
			self.root.settings.init_stringvar('MaxBadBlocks', default=self.DEF_MAXBADBLOCKS),
			self.MAXBADBLOCKS,
			default = self.DEF_MAXBADBLOCKS,
			width = GuiConfig.SMALL_FIELD_WIDTH,
			column = 2,
			columnspan = 2,
			incrow = False,
			tip = self.TIP_MAXBADBLOCKS
		)
		self.max_retries = StringSelector(
			frame,
			self.root.settings.init_stringvar('MaxRetries', default=self.DEF_MAXRETRIES),
			self.MAXRETRIES,
			default = self.DEF_MAXRETRIES,
			width = GuiConfig.SMALL_FIELD_WIDTH,
			column = 4,
			tip = self.TIP_MAXRETRIES
		)
		GridLabel(frame, self.ALL_BYTES, column=1, columnspan=1, incrow=False)
		self.value = StringSelector(
			frame,
			self.root.settings.init_stringvar('Value', default='00'),
			self.VALUE,
			default = '00',
			width = GuiConfig.SMALL_FIELD_WIDTH,
			column = 2,
			columnspan = 2,
			incrow = False,
			tip = self.TIP_VALUE
		)
		self.blocksize = GridMenu(
			frame,
			self.root.settings.init_intvar('Blocksize', default=self.DEF_BLOCKSIZE),
			self.BLOCKSIZE,
			self.BLOCKSIZES,
			column = 4,
			tip = self.TIP_BLOCKSIZE
		)
		GridLabel(frame, self.EXTRA_PASS, column=1, columnspan=1, incrow=False)
		self.part_name = StringSelector(
			frame,
			self.root.settings.init_stringvar('PartitionName'),
			self.PART_NAME,
			default = self.DEF_PART_NAME,
			width = GuiConfig.SMALL_FIELD_WIDTH,
			column = 2,
			columnspan = 2,
			incrow = False,
			tip = self.TIP_PART_NAME
		)
		self.part_table = GridMenu(
			frame,
			self.root.settings.init_stringvar('PartitionTable', default=self.DEF_TABLE),
			self.PARTITION_TABLE,
			self.TABLES,
			column = 4,
			tip = self.TIP_PARTITION_TABLE
		)
		GridLabel(frame, self.VERIFY, column=1, columnspan=1, incrow=False)
		self.filesystem = GridMenu(
			frame,
			self.root.settings.init_stringvar('FileSystem', default=self.DEF_FS),
			self.FILE_SYSTEM,
			self.FS,
			column = 4,
			tip = self.TIP_FILE_SYSTEM
		)
		GridSeparator(frame)
		GridLabel(frame, self.CONFIGURATION)
		self.log_head = FileSelector(
			frame,
			self.root.settings.init_stringvar('LogHead', default=self.default_wlh_path),
			self.LOG_HEAD,
			self.SELECT_TEXT_FILE,
			filetype = ('Text', '*.txt'),
			tip = self.TIP_LOG_HEAD
		)
		AddJobButton(frame, 'WipeR', self._add_job)

	def _select_target(self):
		'''Select drive to wipe'''
		self.select_target = SelectTargetWindow(self.root, self.target)

	def _add_job(self):
		'''Generate command line'''
		target = self.target.get()
		outdir = self.outdir.get()
		mountpoint = self.mountpoint.get()
		task = self.task.get()
		blocksize = self.blocksize.get()
		part_table = self.part_table.get()
		filesystem = self.filesystem.get()
		part_name = self.part_name.get()
		value = self.value.get()
		max_bad_blocks = self.max_bad_blocks.get()
		max_retries = self.max_retries.get()
		log_head = self.log_head.get()
		if not target or target.startswith(self.TARGET_WARNING):
			MissingEntry(self.TARGET_REQUIRED)
			return
		if not outdir:
			MissingEntry(self.OUTDIR_REQUIRED)
			return
		cmd = f'wiper --outdir "{outdir}"'
		if task == 'All':
			cmd += ' --allbytes'
		elif task == 'Extra':
			cmd += ' --extra'
		elif task == 'Verify':
			cmd += ' --verify'
		if blocksize:
			cmd += f' --blocksize {blocksize}'
		if value:
			try:
				int(value, 16)
			except ValueError:
				pass
			else:
				if int(value, 16) >= 0 or int(value, 16) <= 0xff:
					cmd += f' --value {value}'
		if max_bad_blocks:
			try:
				int(max_bad_blocks)
			except ValueError:
				pass
			else:
				cmd += f' --maxbadblocks {max_bad_blocks}'
		if max_retries:
			try:
				int(max_retries)
			except ValueError:
				pass
			else:
				cmd += f' --maxretries {max_retries}'
		if LinUtils.is_disk(target):
			if part_table != '-' and filesystem != '-' and task != 'Verify':
				if part_table == 'mbr':
					cmd += f' --mbr'
				cmd += f' --create {filesystem.lower()}'
				if part_name:
					cmd += f' --name "{part_name}"'
				if log_head:
					cmd += f' --loghead "{log_head}"'
				if mountpoint:
					cmd += f' --mount "{mountpoint}"'
		cmd += f' {target}'
		self.root.append_job(cmd)
