#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from. guilabeling import EwfCheckerLabels
from .guielements import NotebookFrame, FileSelector, GridSeparator
from .guielements import GridLabel, OutDirSelector, FilenameSelector
from .guielements import AddJobButton
#from lib.guielements import ExpandedFrame, GridSeparator, GridLabel
#from lib.guielements import FilenameSelector, DirSelector, FileSelector
#from lib.guielements import GridButton, GridBlank
#from ewfchecker import EwfChecker

class EwfCheckerGui(EwfCheckerLabels):
	'''GUI for EwfChecker'''

	MODULE = 'EwfChecker'

	def __init__(self, root):
		'''Notebook page'''
		self.root = root
		frame = NotebookFrame(self)
		self.image = FileSelector(
			frame,
			self.root.settings.init_stringvar('Image'),
			self.IMAGE,
			self.SELECT_IMAGE,
			filetype=('EWF/E01', '*.e01'),
			tip = self.SELECT_IMAGE
		)
		GridSeparator(frame)
		GridLabel(frame, self.DESTINATION)
		self.outdir = OutDirSelector(
			frame,
			self.root.settings.init_stringvar('OutDir'),
			tip = self.TIP_OUTDIR
		)
		self.image = FilenameSelector(
			frame,
			'{now}_ewfverify',
			self.root.settings.init_stringvar('Filename')
		)
		AddJobButton(frame, 'EwfVerify', self._add_job)

	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		image = self.root.settings.get(self.root.IMAGE)
		outdir = self.root.settings.get(self.root.OUTDIR)
		filename = self.root.settings.get(self.root.FILENAME)
		if not image:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.IMAGE_REQUIRED
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
		cmd += f' --{self.root.OUTDIR.lower()} "{outdir}"'
		cmd += f' --{self.root.FILENAME.lower()} "{filename}"'
		cmd += f' "{image}"'
		self.root.append_job(cmd)
