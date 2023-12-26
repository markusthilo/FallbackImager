#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lib.guielements import ExpandedFrame, SourceDirSelector, GridLabel, FilenameSelector
from lib.guielements import GridSeparator, DirSelector, StringSelector, FileSelector
from lib.guielements import GridButton, GridBlank

class OscdImagerGui:
	'''Notebook page for OscdImager'''

	CMD = 'OscdImager'

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		SourceDirSelector(root, frame)
		GridLabel(root, frame, root.DESTINATION, columnspan=2)
		FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
		DirSelector(root, frame, root.OUTDIR, root.DIRECTORY, root.SELECT_DEST_DIR)
		GridSeparator(root, frame)
		GridBlank(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job,
			column=0, columnspan=3)
		self.root = root

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
