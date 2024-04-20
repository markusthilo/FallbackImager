#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from lib.guielements import ExpandedLabel, ExpandedScrolledText, Checker, VerticalButtons
from lib.guielements import ExpandedFrame, GridSeparator, GridLabel, DirSelector
from lib.guielements import FilenameSelector, StringSelector, StringRadiobuttons
from lib.guielements import FileSelector, GridButton, GridBlank
from lib.timestamp import TimeStamp

class HashedCopyGui:
	'''Notebook page'''

	CMD = 'HashedCopy'

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		self.sources = ExpandedScrolledText(root, frame, root.JOB_HEIGHT)
		frame = ExpandedFrame(root, frame)
		root.row = 0

		GridButton(root, parent, text, command, column=1, columnspan=1)
		GridButton(root, parent, text, command, column=1, columnspan=1)

		GridLabel(root, frame, root.DESTINATION)
		DirSelector(root, frame, root.DESTINATION,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		GridLabel(root, frame, root.LOGGING)
		self.filename_str = FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
		DirSelector(root, frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR)

		#VerticalButtons(root, frame, root.COMPRESSION, (root.MAX, root.FAST, root.NONE), root.NONE)

		GridSeparator(root, frame)
		GridBlank(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job,
			column=0, columnspan=3)
		self.root = root

	def _select_verify_file(self):
		'''Select verify file'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.TO_DO).set(self.root.VERIFY_FILE)

	def _gen_name(self):
		'''Generate a name for the image'''
		if not self.name_str.string.get():
			self.name_str.string.set(Path(self.source_dir.source_str.get()).name)
	
	def _gen_description(self):
		'''Generate a description for the image'''
		if not self.descr_str.string.get():
			descr = TimeStamp.now(no_ms=True)
			source = self.source_dir.source_str.get()
			if source:
				descr += f', {Path(source).name}'
			self.descr_str.string.set(descr)

	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		source = self.root.settings.get(self.root.SOURCE)
		outdir = self.root.settings.get(self.root.OUTDIR)
		filename = self.root.settings.get(self.root.FILENAME)
		compression = self.root.settings.get(self.root.COMPRESSION)
		cmd = self.root.settings.section.lower()
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
		cmd += f' --{self.root.OUTDIR.lower()} "{outdir}"'
		cmd += f' --{self.root.FILENAME.lower()} "{filename}"'
		name = self.root.settings.get(self.root.IMAGE_NAME)
		if name:
			cmd += f' --name "{name}"'
		description = self.root.settings.get(self.root.IMAGE_DESCRIPTION)
		if description:
			cmd += f' --description "{description}"'
		if compression:
			cmd += f' --compress "{compression.lower()}"'
		if self.root.settings.get(self.root.COPY_EXE) == '1':
			cmd += ' --exe'
		cmd += f' "{source}"'
		self.root.append_job(cmd)