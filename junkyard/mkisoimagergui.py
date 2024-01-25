#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from tkinter.messagebox import showerror
from lib.guielements import ExpandedFrame, SourceDirSelector, GridLabel, FilenameSelector
from lib.guielements import GridSeparator, DirSelector, StringSelector, FileSelector
from lib.guielements import GridButton, GridBlank
from mkisoimager import MkIsoImager

class MkIsoImagerGui:
	'''Notebook page for MkIsoImager'''

	CMD = 'MkIsoImager'

	def __init__(self, root):
		'''Notebook page'''
		self.mkisoimager = MkIsoImager()
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		SourceDirSelector(root, frame)
		GridLabel(root, frame, root.DESTINATION)
		FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
		DirSelector(root, frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		self.name_str = StringSelector(root, frame, root.IMAGE_NAME, root.IMAGE_NAME,
			command=self._gen_name)
		GridSeparator(root, frame)
		GridBlank(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job,
			column=0, columnspan=3)
		self.root = root
	
	def _gen_name(self):
		'''Generate a name for the image'''
		self.root.settings.section = self.CMD
		if not self.name_str.string.get() and self.root.settings.get(self.root.SOURCE):
			self.name_str.string.set(
				self.mkisoimager.labelize(Path(self.root.settings.get(self.root.SOURCE)).stem))
	
	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		source = self.root.settings.get(self.root.SOURCE)
		outdir = self.root.settings.get(self.root.OUTDIR)
		filename = self.root.settings.get(self.root.FILENAME)
		name = self.root.settings.get(self.root.IMAGE_NAME)
		mkisofs = self.root.settings.get(self.root.MKISOFS)
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
		if mkisofs and Path(mkisofs) != __mkisofs_path__:
			cmd += f' --mkisofs "{mkisofs}"'
		cmd += f' --{self.root.OUTDIR.lower()} "{outdir}"'
		cmd += f' --{self.root.FILENAME.lower()} "{filename}"'
		if name:
			cmd += f' --{self.root.IMAGE_NAME.lower()} "{name}"'
		cmd += f' "{source}"'
		self.root.append_job(cmd)
