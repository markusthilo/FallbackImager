#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from tkinter.messagebox import showerror
from lib.guielements import SourceDirSelector, Checker, VerticalButtons
from lib.guielements import ExpandedFrame, GridSeparator, GridLabel, DirSelector
from lib.guielements import FilenameSelector, StringSelector, GridButton, GridBlank
from lib.timestamp import TimeStamp

class DismImagerGui:
	'''Notebook page'''

	CMD = 'DismImager'

	def __init__(self, root):
		'''Notebook page'''
		sekf,root = root
		frame = NotebookFrame(self.root, 'DismImager')
		self.source = SourceDirSelector(frame, self.root.settings.init_stringvar('Source'))
		self.outdir = OutDirSelector(frame, self.root.settings.init_stringvar('OutDir'))
		self.filename = FilenameSelector(frame, '{now}_dismimager',
			self.root.settings.init_stringvar('Filename'))
		self.name = StringSelector(
			frame,
			self.root.settings.init_stringvar('Name'),
			self.NAME,
			command = self._gen_name,
			tip = self.TIP_NAME
		)
		self.name = StringSelector(
			frame,
			self.root.settings.init_stringvar('Description'),
			self.DESCRIPTION,
			command = self._gen_description,
			tip = self.TIP_DESCRIPTION
		)
		self.compression = VerticalRadiobuttons(
			frame,
			self.root.settings.init_boolvar('Compression'),
			('none', 'fast', 'max'),
			'none'
		)
		GridSeparator(frame)
		self.copy_exe = Checker(
			frame,
			self.root.settings.init_boolvar('CopyExe'),
			self.COPY_EXE,
			columnspan = 2,
			tip = self.TIP_COPY_EXE
		)
		AddJobButton(frame, 'DismImager', self._add_job)
		self.root.child_win_active = False

	def _gen_name(self):
		'''Generate a name for the image'''
		if not self.name.get():
			self.name.set(Path(self.source.get()).name)
	
	def _gen_description(self):
		'''Generate a description for the image'''
		if not self.description.get():
			descr = TimeStamp.now(no_ms=True)
			source = self.source.get()
			if source:
				descr += f', {Path(source).name}'
			self.description.set(descr)

	def _add_job(self):
		'''Generate command line'''
		source = self.source.get()
		outdir = self.outdir.get()
		filename = self.filename.get()
		name = self.name.get()
		description = self.description.get()
		compression = self.compression.get()
		copy_exe = self.copy_exe.get()
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