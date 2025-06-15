#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from. guilabeling import BasicLabels
from .guielements import NotebookFrame, FileSelector, GridSeparator
from .guielements import GridLabel, OutDirSelector, FilenameSelector
from .guielements import AddJobButton, MissingEntry

class EwfCheckerGui(BasicLabels):
	'''GUI for EwfChecker'''

	MODULE = 'EwfChecker'

	def __init__(self, root):
		'''Notebook page'''
		self.root = root
		frame = NotebookFrame(self)
		GridLabel(frame, self.SOURCE)
		self.image = FileSelector(
			frame,
			self.root.settings.init_stringvar('Image'),
			self.IMAGE,
			self.SELECT_IMAGE,
			filetype=('EWF/E01', '*.E01'),
			tip = self.SELECT_IMAGE
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
			'{now}_ewfchecker',
			self.root.settings.init_stringvar('Filename')
		)
		AddJobButton(frame, 'EwfVerify', self._add_job)

	def _add_job(self):
		'''Generate command line'''
		image = self.image.get()
		outdir = self.outdir.get()
		filename = self.filename.get()
		if not image:
			MissingEntry(self.IMAGE_REQUIRED)
			return
		if not outdir:
			MissingEntry(self.OUTDIR_REQUIRED)
			return
		cmd = f'ewfchecker --outdir "{outdir}"'
		if filename:
			cmd += f' --filename "{filename}"'
		cmd += f' "{image}"'
		self.root.append_job(cmd)
