#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter.messagebox import showerror
from tkinter.ttk import Label, Button
from tkinter import Text
from functools import partial
from os import getlogin, access, R_OK
from .guilabeling import EwfImagerLabels
from .guielements import Checker, GridMenu, ChildWindow, NotebookFrame
from .guielements import ExpandedFrame, GridSeparator, GridLabel, OutDirSelector
from .guielements import StringSelector, StringRadiobuttons
from .guielements import GridButton, LeftButton, RightButton, GridBlank
from .timestamp import TimeStamp
from .linutils import LinUtils
from .stringutils import StringUtils

class EwfImagerGui(EwfImagerLabels):
	'''Notebook page for EwfImager'''

	MODULE = 'EwfImager'
	MEDIA_TYPES = ['auto', 'fixed', 'removable', 'optical']
	MEDIA_FLAGS = ['auto', 'logical', 'physical']
	COMPRESSIONS = ['fast', 'best', 'none']

	def __init__(self, root):
		'''Notebook page'''
		self.root = root
		frame = NotebookFrame(self)
		GridLabel(frame, self.SOURCE)
		self.source = StringSelector(
			frame,
			self.root.settings.init_stringvar('Source'),
			self.SELECT,
			command = self._select_source,
			missing = self.SOURCE_REQUIRED,
			tip = self.TIP_SOURCE
		)
		self.set_ro = Checker(
			frame,
			self.root.settings.init_boolvar('SetReadOnly'),
			self.SETRO,
			tip = self.TIP_SETRO
		)
		GridSeparator(frame)
		GridLabel(frame, self.DESTINATION)
		self.outdir = OutDirSelector(
			frame,
			self.root.settings.init_stringvar('OutDir'),
			tip = self.TIP_IMAGE_LOGS
		)
		self.root_id = StringSelector(
			frame,
			self.root.settings.init_stringvar('CaseNo'),
			self.CASE_NO,
			command=self._set_ts_case_no,
			tip=self.TIP_METADATA
		)
		self.evidence_no = StringSelector(
			frame,
			self.root.settings.init_stringvar('EvidenceNo'),
			self.EVIDENCE_NO,
			command=self._set_def_evidence_no,
			tip=self.TIP_METADATA
		)
		self.description = StringSelector(
			frame,
			self.root.settings.init_stringvar('Description'),
			self.DESCRIPTION,
			command=self._set_def_description,
			tip=self.TIP_METADATA
		)
		self.examiner_name = StringSelector(
			frame,
			self.root.settings.init_stringvar('ExaminerName'),
			self.EXAMINER_NAME,
			command=self._set_def_examiner_name,
			tip=self.TIP_METADATA
		)
		self.notes_select = StringRadiobuttons(
			frame,
			self.root.settings.init_stringvar('Notes', default='A'),
			'ABC'
		)
		self.notes = dict()
		for index in 'ABC':
			self.notes[index] = StringSelector(
				frame,
				self.root.settings.init_stringvar(f'Note{index}'),
				f'{self.NOTES} {index}',
				command=partial(self._select_notes, index),
				tip=self.TIP_METADATA
			)

		self.segment_size = StringSelector(
			frame,
			self.root.settings.init_stringvar('SegmentSize', default='auto'),
			self.SEGMENT_SIZE,
			command=self.self._set_auto,
			tip=self.TIP_SEGMENT_SIZE
		)


		return

		StringSelector(root, frame, root.SEGMENT_SIZE, root.SEGMENT_SIZE, default=root.AUTO, command=self._set_auto,
			width=root.SMALL_FIELD_WIDTH, columnspan=2, incrow=False)
		Label(frame, width=4).grid(row=root.row, column=3)
		GridStringMenu(root, frame, root.COMPRESSION, root.COMPRESSION,
			self.COMPRESSIONS, default=self.COMPRESSIONS[0], column=4, incrow=False)
		Label(frame, width=4).grid(row=root.row, column=6)
		GridStringMenu(root, frame, root.MEDIA_TYPE, root.MEDIA_TYPE,
			self.MEDIA_TYPES, default=self.MEDIA_TYPES[0], column=7, incrow=False)
		Label(frame, width=4).grid(row=root.row, column=9)
		GridStringMenu(root, frame, root.MEDIA_FLAG, root.MEDIA_FLAG,
			self.MEDIA_FLAGS, default=self.MEDIA_FLAGS[0], column=10)
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
		if access(dev, R_OK):
			self.root.settings.section = self.CMD
			self.root.settings.raw(self.root.SOURCE).set(dev)
		else:
			showerror(
				title = self.root.UNABLE_ACCESS,
				message = self.root.ROOT_HELP
			)

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
		case_no = self.root.settings.get(self.root.CASE_NO)
		evidence_number = self.root.settings.get(self.root.EVIDENCE_NO)
		description = self.root.settings.get(self.root.DESCRIPTION)
		examiner_name = self.root.settings.get(self.root.EXAMINER_NAME)
		notes = self.root.settings.get(self.root.settings.get(self.root.NOTES))
		media_type = self.root.settings.get(self.root.MEDIA_TYPE)
		media_flag = self.root.settings.get(self.root.MEDIA_FLAG)
		compression = self.root.settings.get(self.root.COMPRESSION)
		setro = self.root.settings.get(self.root.SETRO)
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
		if not case_no or not evidence_number or not description or not examiner_name:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.IMAGE_DETAILS_REQUIRED
			)
			return
		cmd = self.root.settings.section.lower()
		cmd += f' --{self.root.OUTDIR.lower()} "{outdir}"'
		cmd += f' -C "{case_no}" -E "{evidence_number}" -D "{description}" -e "{examiner_name}"'
		if notes:
			cmd += f' -N "{notes}"'
		cmd += f' -c {compression}'
		if media_type != self.MEDIA_TYPES[0]:
			cmd += f' -m {media_type}'
		if media_flag != self.MEDIA_FLAGS[0]:
			cmd += f' -M {media_flag}'
		if setro:
			cmd += ' --setro'
		cmd += f' "{source}"'
		self.root.append_job(cmd)
