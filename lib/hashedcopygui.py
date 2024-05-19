#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter.messagebox import showerror
from tkinter.filedialog import askopenfilenames, askdirectory
from lib.guielements import ExpandedScrolledText, FilenameSelector
from lib.guielements import ExpandedFrame, GridSeparator, GridLabel, DirSelector
from lib.guielements import GridButton, GridBlank

class HashedCopyGui:
	'''Notebook page'''

	MODULE = 'HashedCopy'

	def __init__(self, root):
		'''Notebook page'''
		self.root = root
		frame = NotebookFrame(self)
		self.sources = ExpandedScrolledText(root, frame, root.JOB_HEIGHT)
		frame = ExpandedFrame(root, frame)

		GridButton(root, frame, root.ADD_SRC_FILES, self._add_files,
			column=0, columnspan=2, incrow=False)
		GridButton(root, frame, root.ADD_SRC_DIR, self._add_dir, column=2)
		GridLabel(root, frame, root.DESTINATION)
		DirSelector(root, frame, root.DESTINATION,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		GridLabel(root, frame, root.LOGGING)
		FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
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
		outdir = self.root.settings.get(self.root.OUTDIR)
		filename = self.root.settings.get(self.root.FILENAME)
		destination = self.root.settings.get(self.root.DESTINATION)
		cmd = self.root.settings.section.lower()
		if not outdir or not destination:
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
		cmd += f' --{self.root.DESTINATION.lower()} "{destination}"'
		while True:
			line = self.sources.get('1.0', '2.0').strip()
			if not line:
				break
			self.sources.delete('1.0', '2.0')
			cmd += f' "{line}"'
		self.root.append_job(cmd)
