#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter.ttk import Button
from tkinter import Text
from functools import partial
from os import getlogin, access, R_OK
from .guilabeling import EwfImagerLabels
from .guiconfig import GuiConfig
from .diskselectgui import DiskSelectGui
from .guielements import Checker, GridMenu, ChildWindow, NotebookFrame
from .guielements import ExpandedFrame, GridSeparator, GridLabel, OutDirSelector
from .guielements import StringSelector, StringRadiobuttons, AddJobButton
from .guielements import LeftButton, RightButton, Error, MissingEntry
from .timestamp import TimeStamp
from .linutils import LinUtils
from .stringutils import StringUtils

class EwfImagerGui(EwfImagerLabels):
	'''GUI for EwfImager'''

	MODULE = 'EwfImager'

	def __init__(self, root):
		'''Notebook page'''
		self.root = root
		frame = NotebookFrame(self)
		GridLabel(frame, self.SOURCE)
		self.source_var = self.root.settings.init_stringvar('Source')
		self.source = StringSelector(
			frame,
			self.source_var,
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
		GridLabel(frame, self.SETTINGS)
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
		GridSeparator(frame)
		GridLabel(frame, self.DESTINATION)
		self.outdir = OutDirSelector(
			frame,
			self.root.settings.init_stringvar('OutDir'),
			tip = self.TIP_OUTDIR
		)
		self.filename = StringSelector(
			frame,
			self.root.settings.init_stringvar('Filename'),
			self.FILENAME,
			command = self._set_filename,
			tip = self.TIP_FILENAME
		)
		AddJobButton(frame, self.MODULE, self._add_job)

	def _select_source(self):
		'''Select source to image'''
		DiskSelectGui(self.root, self.SELECT_TARGET, self.source_var)

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
		if not self.filename.get():
			case_no = self.case_no.get()
			evidence_number = self.evidence_no.get()
			description = self.description.get()
			if case_no and evidence_number and description:
				self.filename.set(f'{case_no}_{evidence_number}_{description}')
			else:
				MissingEntry(self.MISSING_METADATA)

	def _add_job(self):
		'''Generate command line'''
		source = self.source.get()
		setro = self.set_ro.get()
		outdir = self.outdir.get()
		case_no = self.case_no.get()
		evidence_number = self.evidence_no.get()
		description = self.description.get()
		examiner_name = self.examiner_name.get()
		notes = self.notes[self.notes_select.get()].get()
		compression = self.compression.get()
		media_type = self.media_type.get()
		media_flag = self.media_flag.get()
		segment_size = self.segment_size.get().replace(' ', '')
		filename = self.filename.get()
		if not access(source, R_OK):
			Error(self.ARE_YOU_ROOT)
			return
		if not source:
			MissingEntry(self.SOURCE_REQUIRED)
			return
		if not outdir:
			MissingEntry(self.OUTDIR_REQUIRED)
			return
		if not case_no or not evidence_number or not description:
			MissingEntry(self.METADATA_REQUIRED)
			return
		if segment_size:
			try:
				int(segment_size.replace(' ', '').rstrip('mMgGbB'))
			except ValueError:
				Error(self.UNDECODEABLE_SEGMENT_SIZE)
				return
		cmd = f'ewfimager --outdir "{outdir}" -C "{case_no}" -E "{evidence_number}"'
		cmd += f' -D "{description}" -S {segment_size}'
		if examiner_name:
			cmd += f' -e "{examiner_name}"'
		if notes:
			cmd += f' -N "{notes}"'
		cmd += f' -c {compression} -m {media_type} -M {media_flag}'
		if filename:
			cmd += f' --filename "{filename}"'
		if setro:
			cmd += ' --setro'
		cmd += f' "{source}"'
		self.root.append_job(cmd)
