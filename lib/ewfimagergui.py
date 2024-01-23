#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter.messagebox import showerror
from tkinter.ttk import Button
from tkinter import Text
from functools import partial
from os import getlogin
from lib.timestamp import TimeStamp
from lib.guielements import SourceDirSelector, Checker, LeftLabel, GridIntMenu, GridStringMenu
from lib.guielements import ChildWindow, SelectTsvColumn, FilesSelector, ExpandedLabelFrame
from lib.guielements import ExpandedFrame, GridSeparator, GridLabel, DirSelector
from lib.guielements import FilenameSelector, StringSelector, StringRadiobuttons
from lib.guielements import FileSelector, GridButton, LeftButton, RightButton, GridBlank
from lib.linutils import LinUtils
from lib.stringutils import StringUtils

class EwfImagerGui:
	'''Notebook page for EwfImager'''

	CMD = 'EwfImager'
	MEDIA_TYPES = ['fixed', 'removable', 'optical']

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		GridSeparator(root, frame)
		GridLabel(root, frame, root.SOURCE)
		StringSelector(root, frame, root.SOURCE, root.SOURCE,
			command=self._select_source, columnspan=4)
		root.settings.raw(root.SOURCE).set('')
		GridSeparator(root, frame)
		GridLabel(root, frame, root.DESTINATION)
		DirSelector(root, frame, root.OUTDIR, root.DIRECTORY, root.SELECT_DEST_DIR, columnspan=4)
		StringSelector(root, frame, root.CASE_NO, root.CASE_NO,
			command=self._set_ts_case_no, columnspan=4)
		StringSelector(root, frame, root.EVIDENCE_NO, root.EVIDENCE_NO,
			command=self._set_def_evidence_no, columnspan=4)
		StringSelector(root, frame, root.DESCRIPTION, root.DESCRIPTION,
			command=self._set_def_description, columnspan=4)
		StringSelector(root, frame, root.EXAMINER_NAME, root.EXAMINER_NAME,
			command=self._set_def_examiner_name, columnspan=4)
		notes = [f'Notes {index}' for index in ('A', 'B', 'C')]
		StringRadiobuttons(root, frame, root.NOTES, notes, notes[0])
		for choice in notes:
			StringSelector(root, frame, choice, choice, command=partial(self._select_notes, choice), columnspan=4)
		StringSelector(root, frame, root.SEGMENT_SIZE, root.SEGMENT_SIZE, default=root.AUTO, command=self._set_auto,
			width=root.SMALL_FIELD_WIDTH, columnspan=4)
		root.row -= 1
		GridStringMenu(root, frame, root.MEDIA_TYPE, root.MEDIA_TYPE,
				 self.MEDIA_TYPES, default=self.MEDIA_TYPES[0], column=2)
		GridSeparator(root, frame)
		GridBlank(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job,
			column=0, columnspan=3)
		self.root = root

	def _select_source(self):
		'''Select source'''
		if self.root.child_win_active:
			return
		self.source_window = ChildWindow(self.root, self.root.SELECT)
		self.root.settings.section = self.CMD
		frame = ExpandedFrame(self.root, self.source_window)
		self.root.row = 0
		GridLabel(self.root, frame, self.root.SELECT_SOURCE)
		for diskpath, diskinfo in LinUtils.diskinfo().items():
			Button(frame, text=diskpath, width=self.root.BUTTON_WIDTH,
				command=partial(self._put_source, diskpath)).grid(
				row=self.root.row, column=0, sticky='nw', padx=self.root.PAD)
			text = Text(frame, width=self.root.ENTRY_WIDTH, height=1)
			text.grid(row=self.root.row, column=1)
			text.insert('end', f'Disk: {StringUtils.join(diskinfo["disk"], delimiter=", ")}')
			text.configure(state='disabled')
			self.root.row += 1
			for partition, info in diskinfo['partitions'].items():
				Button(frame, text=partition, width=self.root.BUTTON_WIDTH,
					command=partial(self._put_source, partition)).grid(
					row=self.root.row, column=0, sticky='nw', padx=self.root.PAD)
				text = Text(frame, width=self.root.ENTRY_WIDTH, height=1)
				text.grid(row=self.root.row, column=1)
				text.insert('end', f'Partition: {StringUtils.join(info, delimiter=", ")}')
				text.configure(state='disabled')
				self.root.row += 1
		frame = ExpandedFrame(self.root, self.source_window)
		LeftButton(self.root, frame, self.root.REFRESH, self._refresh_source_window)
		frame = ExpandedFrame(self.root, self.source_window)
		GridSeparator(self.root, frame)
		frame = ExpandedFrame(self.root, self.source_window)
		RightButton(self.root, frame, self.root.QUIT, self.source_window.destroy)

	def _refresh_source_window(self):
		'''Destroy and reopen Target Window'''
		self.source_window.destroy()
		self._select_source()

	def _put_source(self, dev):
		'''Put drive id to sourcestring'''
		self.source_window.destroy()
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.SOURCE).set(dev)

	def _set_ts_case_no(self):
		self.root.settings.section = self.CMD
		if self.root.settings.get(self.root.CASE_NO):
			return
		self.root.settings.raw(self.root.CASE_NO).set(TimeStamp.now(path_comp=True))

	def _set_def_evidence_no(self):
		self.root.settings.section = self.CMD
		if self.root.settings.get(self.root.EVIDENCE_NO):
			return
		self.root.settings.raw(self.root.EVIDENCE_NO).set(self.root.DEF_EVIDENCE_NO)

	def _set_def_description(self):
		self.root.settings.section = self.CMD
		if self.root.settings.get(self.root.DESCRIPTION):
			return
		self.root.settings.raw(self.root.DESCRIPTION).set(self.root.DEF_DESCRIPTION)

	def _set_def_examiner_name(self):
		self.root.settings.section = self.CMD
		if self.root.settings.get(self.root.EXAMINER_NAME):
			return
		self.root.settings.raw(self.root.EXAMINER_NAME).set(getlogin().upper())

	def _select_notes(self, choice):
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.NOTES).set(choice)

	def _set_auto(self):
		self.root.settings.section = self.CMD
		if self.root.settings.get(self.root.SEGMENT_SIZE):
			return
		self.root.settings.raw(self.root.SEGMENT_SIZE).set(self.root.AUTO)

	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		source = self.root.settings.get(self.root.SOURCE)
		outdir = self.root.settings.get(self.root.OUTDIR)
		filename = self.root.settings.get(self.root.FILENAME)
		name = self.root.settings.get(self.root.IMAGE_NAME)
		oscdimg_exe = self.root.settings.get(self.root.OSCDIMG_EXE)
		if not source:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.SOURCE_REQUIRED
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
		if oscdimg_exe and Path(oscdimg_exe) != __oscdimg_exe_path__:
			cmd += f' --exe "{oscdimg_exe}"'
		cmd += f' --{self.root.OUTDIR.lower()} "{outdir}"'
		cmd += f' --{self.root.FILENAME.lower()} "{filename}"'
		if name:
			cmd += f' --{self.root.IMAGE_NAME.lower()} "{name}"'
		cmd += f' "{source}"'
		self.root.append_job(cmd)
