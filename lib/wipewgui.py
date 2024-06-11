#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import StringVar
from tkinter.filedialog import askopenfilenames
from tkinter.ttk import Button
from tkinter.scrolledtext import ScrolledText
from functools import partial
from .guiconfig import GuiConfig
from .guilabeling import WipeLabels
from .guielements import NotebookFrame, GridLabel, StringSelector, GridSeparator, MissingEntry
from .guielements import OutDirSelector, GridMenu, StringRadiobuttons, FileSelector
from .guielements import AddJobButton, ChildWindow, ExpandedFrame, LeftButton, RightButton
from .winutils import WinUtils

class WipeWGui(WipeLabels):
	'''Notebook page for WipeW'''

	MODULE = 'WipeW'
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
		self.target_type = None
		GridSeparator(frame)
		GridLabel(frame, self.LOGGING)
		self.outdir = OutDirSelector(frame, self.root.settings.init_stringvar('OutDir'))
		GridSeparator(frame)
		GridLabel(frame, self.NEW_PARTITION)
		self.new_letter = GridMenu(
			frame,
			StringVar(value=self.NEXT_AVAILABLE),
			self.ASSIGN_DRIVE_LETTER,
			([self.NEXT_AVAILABLE] + WinUtils.get_free_letters()),
			tip = self.TIP_NEW_DRIVE_LETTER
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
		AddJobButton(frame, 'WipeW', self._add_job)
		self.root.child_win_active = False

	def _notepad_log_head(self):
		'''Edit log header file with Notepad'''
		proc = Popen(['notepad', self.root.settings.get(self.root.LOG_HEAD, section=self.CMD)])
		proc.wait()

	def _select_target(self):
		'''Select drive to wipe'''
		if self.root.child_win_active:
			return
		self.target_window = ChildWindow(self.root, self.SELECT)
		frame = ExpandedFrame(self.target_window)
		GridLabel(frame, self.SELECT_DRIVE_TO_WIPE)
		for drive_id, drive_info in WinUtils().list_drives():
			Button(frame, text=drive_id, command=partial(self._put_drive, drive_id)).grid(
				row=frame.row, column=0, sticky='nw', padx=GuiConfig.PAD)
			text = ScrolledText(frame, width=GuiConfig.ENTRY_WIDTH,
				height=min(len(drive_info.split('\n')), GuiConfig.MAX_ENTRY_HEIGHT ))
			text.grid(row=frame.row, column=1)
			text.bind('<Key>', lambda dummy: 'break')
			text.insert('end', f'{drive_id} - {drive_info}')
			text.configure(state='disabled')
			frame.row += 1
		frame = ExpandedFrame(self.target_window)
		LeftButton(frame, self.REFRESH, self._refresh_target_window)
		frame = ExpandedFrame(self.target_window)
		GridSeparator(frame)
		frame = ExpandedFrame(self.target_window)
		LeftButton(frame, self.SELECT_FILES_TO_WIPE, self._select_files)
		RightButton(frame, self.QUIT, self.target_window.destroy)

	def _refresh_target_window(self):
		'''Destroy and reopen Target Window'''
		self.target_window.destroy()
		self._select_target()

	def _put_drive(self, drive_id):
		'''Put drive id to target string'''
		self.target_window.destroy()
		self.target.set(drive_id)
		self.target_type = 'drive'

	def _select_files(self):
		'''Choose file(s) to wipe'''
		self.target_window.destroy()
		self.filenames = askopenfilenames(title=self.SELECT_FILES)
		if self.filenames:
			plus = len(self.filenames) -1
			target = self.filenames[0]
			if plus > 0:
				if plus == 1:
					target += f' + {plus} {self.FILE}'
				else:
					target += f' + {plus} {self.FILES}'
			self.target.set(target)
			self.target_type = 'files'
		else:
			self.target_type = None

	def _add_job(self):
		'''Generate command line'''
		target = self.target.get()
		outdir = self.outdir.get()
		new_letter = self.new_letter.get()
		task = self.task.get()
		blocksize = self.blocksize.get()
		part_table = self.part_table.get()
		filesystem = self.filesystem.get()
		part_name = self.part_name.get()
		value = self.value.get()
		max_bad_blocks = self.max_bad_blocks.get()
		max_retries = self.max_retries.get()
		log_head = self.log_head.get()
		if not target or not self.target_type:
			MissingEntry(self.TARGET_REQUIRED)
			return
		if not outdir:
			MissingEntry(self.OUTDIR_REQUIRED)
			return
		cmd = f'wipew --outdir "{outdir}"'
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
		if self.target_type == 'files' and self.filenames:
			for filename in self.filenames:
				cmd += f' "{filename}"'
		else:
			if filesystem != '-' and part_table != '-':
				if part_table == 'mbr':
					cmd += f' --mbr'
				cmd += f' --create {filesystem}'
				if part_name:
					cmd += f' --name "{part_name}"'
				if log_head:
					cmd += f' --loghead "{log_head}"'
				if new_letter != self.NEXT_AVAILABLE:
					cmd += f' --driveletter {new_letter}'
			cmd += f' "\\\\.\\{target.strip("\\.").upper()}"'
		self.root.append_job(cmd)
