#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from lib.guielements import SourceDirSelector, Checker, VerticalButtons
from lib.guielements import ExpandedFrame, GridSeparator, GridLabel, DirSelector
from lib.guielements import FilenameSelector, StringSelector, StringRadiobuttons
from lib.guielements import FileSelector, GridButton, GridBlank
from lib.dism import Dism
from lib.timestamp import TimeStamp

class DismImagerGui:
	'''Notebook page'''

	CMD = 'DismImager'

	def __init__(self, root):
		'''Notebook page'''
		stdout, stderr = Dism('').read_all()
		if stderr:
			raise RuntimeError(f'Unable tu run Dism\n{stout}\n{stderr}')
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		self.source_dir = SourceDirSelector(root, frame)
		GridLabel(root, frame, root.DESTINATION, columnspan=2)
		self.filename_str = FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
		DirSelector(root, frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		self.name_str = StringSelector(root, frame, root.IMAGE_NAME, root.IMAGE_NAME,
			command=self._gen_name)
		self.descr_str = StringSelector(root, frame, root.IMAGE_DESCRIPTION, root.IMAGE_DESCRIPTION,
			command=self._gen_description)
		VerticalButtons(root, frame, root.COMPRESSION, (root.MAX, root.FAST, root.NONE), root.NONE)
		GridSeparator(root, frame)
		GridLabel(root, frame, root.TO_DO)
		StringRadiobuttons(root, frame, root.TO_DO,
			(root.CREATE_AND_VERIFY, root.VERIFY_FILE), root.CREATE_AND_VERIFY)
		GridLabel(root, frame, root.CREATE_AND_VERIFY, column=1, columnspan=2)
		FileSelector(root, frame, root.VERIFY_FILE, root.VERIFY_FILE, root.SELECT_VERIFY_FILE,
			command=self._select_verify_file)
		Checker(root, frame, root.COPY_EXE, root.COPY_EXE, columnspan=2)
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
		to_do = self.root.settings.get(self.root.TO_DO)
		compression = self.root.settings.get(self.root.COMPRESSION)
		image = self.root.settings.get(self.root.VERIFY_FILE)
		cmd = self.root.settings.section.lower()
		if to_do == self.root.VERIFY_FILE:
			if not image:
				showerror(
					title = self.root.MISSING_ENTRIES,
					message = self.root.IMAGE_REQUIRED
				)
				return
			cmd += f' --verify --{self.root.PATH.lower()} {image}'
			if not filename:
				filename = Path(image).stem
			if not outdir and image:
				outdir = image.parent
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