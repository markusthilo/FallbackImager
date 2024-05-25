#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from .guilabeling import DismImagerLabels
from .guielements import NotebookFrame, SourceDirSelector, GridSeparator
from .guielements import GridLabel, OutDirSelector, FilenameSelector
from .guielements import StringSelector, VerticalRadiobuttons, Checker
from .guielements import AddJobButton, MissingEntry

class DismImagerGui(DismImagerLabels):
	'''Notebook page'''

	MODULE = 'DismImager'

	def __init__(self, root):
		'''Notebook page for DismImager'''
		self.root = root
		frame = NotebookFrame(self)
		GridLabel(frame, self.SOURCE)
		self.source = SourceDirSelector(
			frame,
			self.root.settings.init_stringvar('Source'),
			tip = self.TIP_SOURCE
		)
		GridSeparator(frame)
		GridLabel(frame, self.DESTINATION)
		self.outdir = OutDirSelector(
			frame,
			self.root.settings.init_stringvar('OutDir'),
			tip = self.TIP_OUTDIR
		)
		self.filename = FilenameSelector(
			frame,
			'{now}_dismimager',
			self.root.settings.init_stringvar('Filename')
		)
		self.name = StringSelector(
			frame,
			self.root.settings.init_stringvar('Name'),
			self.NAME,
			command = self._gen_name,
			tip = self.TIP_NAME
		)
		self.description = StringSelector(
			frame,
			self.root.settings.init_stringvar('Description'),
			self.DESCRIPTION,
			command = self._gen_description,
			tip = self.TIP_DESCRIPTION
		)
		GridLabel(frame, self.COMPRESSION, column=1, columnspan=1, incrow=False)
		self.compression = VerticalRadiobuttons(
			frame,
			self.root.settings.init_stringvar('Compression', default='none'),
			('none', 'fast', 'max'),
			column = 2
		)
		GridSeparator(frame)
		self.copy_exe = Checker(
			frame,
			self.root.settings.init_boolvar('CopyExe'),
			self.COPY_EXE,
			columnspan = 3,
			tip = self.TIP_COPY_EXE
		)
		AddJobButton(frame, 'DismImager', self._add_job)
		self.root.child_win_active = False

	def _gen_name(self):
		'''Generate a name for the image'''
		source = self.source.get()
		if source and not self.name.get():
			self.name.set(Path(source).name)
	
	def _gen_description(self):
		'''Generate a description for the image'''
		source = self.source.get()
		if source and not self.description.get():
			self.description.set(f'{self.IMAGE_OF} "{Path(source).name}"')

	def _add_job(self):
		'''Generate command line'''
		source = self.source.get()
		outdir = self.outdir.get()
		filename = self.filename.get()
		name = self.name.get()
		description = self.description.get()
		compression = self.compression.get()
		copy_exe = self.copy_exe.get()
		if not source:
			MissingEntry(self.SOURCE_REQUIRED)
			return
		if not outdir:
			MissingEntry(self.OUTDIR_REQUIRED)
			return
		cmd = f'dismimager --outdir "{outdir}"'
		if filename:
			cmd += f' --filename "{filename}"'
		if name:
			cmd += f' --name "{name}"'
		if description:
			cmd += f' --description "{description}"'
		if compression:
			cmd += f' --compress "{compression}"'
		if copy_exe:
			cmd += ' --exe'
		cmd += f' "{source}"'
		self.root.append_job(cmd)