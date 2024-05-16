#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter.ttk import Button
from tkinter import Text
from functools import partial
from os import getlogin, access, R_OK
from .guilabeling import EwfImagerLabels
from .guiconfig import GuiConfig
from .guielements import Checker, GridMenu, ChildWindow, NotebookFrame
from .guielements import ExpandedFrame, GridSeparator, GridLabel, OutDirSelector
from .guielements import StringSelector, StringRadiobuttons, AddJobButton
from .guielements import GridButton, LeftButton, RightButton, GridBlank
from .guielements import Error, MissingEntry
from .timestamp import TimeStamp
from .linutils import LinUtils
from .stringutils import StringUtils

class EwfImagerGui(EwfImagerLabels):
	'''Notebook page for EwfImager'''

	MODULE = 'EwfImager'
	DEF_SIZE = '40'

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
		self.case_no = StringSelector(
			frame,
			self.root.settings.init_stringvar('CaseNo'),
			self.CASE_NO,
			command = self._set_ts_case_no,
			tip = self.TIP_METADATA
		)
		self.evidence_no = StringSelector(
			frame,
			self.root.settings.init_stringvar('EvidenceNo'),
			self.EVIDENCE_NO,
			command = self._set_def_evidence_no,
			tip = self.TIP_METADATA
		)
		self.description = StringSelector(
			frame,
			self.root.settings.init_stringvar('Description'),
			self.DESCRIPTION,
			command = self._set_def_description,
			tip = self.TIP_METADATA
		)
		self.examiner_name = StringSelector(
			frame,
			self.root.settings.init_stringvar('ExaminerName'),
			self.EXAMINER_NAME,
			command = self._set_def_examiner_name,
			tip = self.TIP_METADATA
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
				command = partial(self._select_notes, index),
				tip = self.TIP_NOTE
			)
		self.segment_size = StringSelector(
			frame,
			self.root.settings.init_stringvar('SegmentSize', default=self.DEF_SIZE),
			self.SEGMENT_SIZE,
			width = GuiConfig.SMALL_FIELD_WIDTH,
			command = self._set_def_size,
			columnspan = 2,
			incrow = False,
			tip=self.TIP_SEGMENT_SIZE
		)
		self.compression = GridMenu(
			frame,
			self.root.settings.init_stringvar('Compression', default='fast'),
			self.COMPRESSION,
			('fast', 'best', 'none'),
			column = 3,
			incrow = False,
			tip = self.TIP_COMPRESSION
		)
		self.media_type = GridMenu(
			frame,
			self.root.settings.init_stringvar('MediaType', default='fixed'),
			self.MEDIA_TYPE,
			('auto', 'fixed', 'removable', 'optical'),
			column = 5,
			incrow = False,
			tip = self.TIP_METADATA
		)
		self.media_flag = GridMenu(
			frame,
			self.root.settings.init_stringvar('MediaFlag', default='physical'),
			self.MEDIA_FLAG,
			('auto', 'logical', 'physical'),
			column = 7,
			tip = self.TIP_METADATA
		)
		self.filename = StringSelector(
			frame,
			self.root.settings.init_stringvar('Filename'),
			self.FILENAME,
			command = self._set_filename,
			tip = self.TIP_FILENAME
		)
		AddJobButton(frame, 'AxChecker', self._add_job)
		self.root.child_win_active = False

	def _select_source(self):
		'''Select source'''
		if self.root.child_win_active:
			return
		self.source_window = ChildWindow(self.root, self.SELECT_SOURCE)
		frame = ExpandedFrame(self.source_window)
		for diskpath, diskinfo in LinUtils.diskinfo().items():
			Button(frame, text=diskpath, width=GuiConfig.BUTTON_WIDTH,
				command=partial(self._put_source, diskpath)).grid(
				row=frame.row, column=0, sticky='nw', padx=GuiConfig.PAD)
			text = Text(frame, width=GuiConfig.FILES_FIELD_WIDTH, height=1)
			text.grid(row=frame.row, column=1)
			text.insert('end', f'Disk: {StringUtils.join(diskinfo["disk"], delimiter=", ")}')
			text.configure(state='disabled')
			frame.row += 1
			for partition, info in diskinfo['partitions'].items():
				Button(frame, text=partition, width=GuiConfig.BUTTON_WIDTH,
					command=partial(self._put_source, partition)).grid(
					row=frame.row, column=0, sticky='nw', padx=GuiConfig.PAD)
				text = Text(frame, width=GuiConfig.FILES_FIELD_WIDTH, height=1)
				text.grid(row=frame.row, column=1)
				text.insert('end', f'Partition: {StringUtils.join(info, delimiter=", ")}')
				text.configure(state='disabled')
				frame.row += 1
		frame = ExpandedFrame(self.source_window)
		LeftButton(frame, self.REFRESH, self._refresh_source_window)
		RightButton(frame, self.QUIT, self.source_window.destroy)

	def _refresh_source_window(self):
		'''Destroy and reopen Target Window'''
		self.source_window.destroy()
		self._select_source()

	def _put_source(self, dev):
		'''Put drive id to sourcestring'''
		self.source_window.destroy()
		if access(dev, R_OK):
			self.source.set(dev)
		else:
			Error(self.ARE_YOU_ROOT)

	def _set_ts_case_no(self):
		if not self.case_no.get():
			self.case_no.set(TimeStamp.now(path_comp=True))

	def _set_def_evidence_no(self):
		if not self.evidence_no.get():
			self.evidence_no.set(self.DEF_EVIDENCE_NO)

	def _set_def_description(self):
		if not self.description.get():
			self.description.set(self.DEF_DESCRIPTION)

	def _set_def_examiner_name(self):
		if not self.examiner_name.get():
			self.examiner_name.set(getlogin().upper())

	def _select_notes(self, choice):
		self.notes_select.set(choice)

	def _set_def_size(self):
		if not self.segment_size.get():
			self.segment_size.set(self.DEF_SIZE)

	def _set_filename(self):
		self.filename.set('TEST')

	def _add_job(self):
		'''Generate command line'''

		#self.SOURCE_REQUIRED
		#self.CASE_NO_REQUIRED
		#self.EVIDENCE_NO_REQUIRED
		#self.DESCRIPTION_REQUIRED

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
