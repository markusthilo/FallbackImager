#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from tkinter.filedialog import askopenfilenames, askdirectory
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
		GridButton(root, frame, root.ADD_SRC_FILES, self._add_files, column=0, columnspan=2)
		root.row -= 1
		GridButton(root, frame, root.ADD_SRC_DIR, self._add_dir, column=2)
		GridLabel(root, frame, root.DESTINATION)
		DirSelector(root, frame, root.DESTINATION,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		GridLabel(root, frame, root.LOGGING)
		self.filename_str = FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
		DirSelector(root, frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		GridSeparator(root, frame)
		GridBlank(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job,
			column=0, columnspan=3)
		self.root = root

	def _add_files(self):
		'''Add source file(s)'''
		filenames = askopenfilenames(title=self.root.ADD_SRC_FILES)
		if filenames:
			for filename in filenames:
				self.sources.insert('end', f'{filename}\n')

	def _add_dir(self):
		'''Add source directory'''
		dir = askdirectory(title=self.root.ADD_SRC_DIR)
		if dir:
			self.sources.insert('end', f'{dir}\n')
			self.sources.yview('end')

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


		'''
		last = self.jobs_text.get('end-2l', 'end').strip(';\n')
		if not last or cmd != last:
			self.jobs_text.insert('end', f'{cmd};\n')
			self.jobs_text.yview('end')

		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.TO_DO).set(self.root.VERIFY_FILE)
		'''

		self.root.append_job(cmd)