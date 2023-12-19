#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lib.guielements import ExpandedFrame, SourceDirSelector, GridSeparator, GridLabel
from lib.guielements import FilenameSelector, DirSelector, FileSelector
from lib.guielements import StringRadiobuttons, GridButton, GridBlank
from isoverify import IsoVerify

class IsoVerifyGui:
	'''Notebook page'''
	CMD = 'IsoVerify'

	def __init__(self, root):
		'''Notebook page'''
		IsoVerify()
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		SourceDirSelector(root, frame)
		GridLabel(root, frame, root.ISO_IMAGE)
		FileSelector(root, frame,
			root.IMAGE, root.IMAGE, root.SELECT_IMAGE, filetype=('ISO files', '*.iso'))
		GridSeparator(root, frame)
		GridLabel(root, frame, root.DESTINATION)
		FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
		DirSelector(root, frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		GridSeparator(root, frame)
		GridLabel(root, frame, root.SKIP_PATH_CHECK)
		StringRadiobuttons(root, frame, root.REGEXFILTER,
			(root.NO_FILTER, root.BLACKLIST, root.WHITELIST), root.NO_FILTER)
		GridLabel(root, frame, root.CHECK_ALL_PATHS, column=2)
		FileSelector(root, frame,
			root.BLACKLIST, root.BLACKLIST, root.SELECT_BLACKLIST, command=self._select_blacklist)
		FileSelector(root, frame,
			root.WHITELIST, root.WHITELIST, root.SELECT_WHITELIST, command=self._select_whitelist)
		GridSeparator(root, frame)
		GridBlank(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job,
			column=0, columnspan=3)
		self.root = root

	def _select_blacklist(self):
		'''Select blacklist'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.REGEXFILTER).set(self.root.BLACKLIST)

	def _select_whitelist(self):
		'''Select whitelist'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.REGEXFILTER).set(self.root.WHITELIST)

	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		source = self.root.settings.get(self.root.SOURCE)
		image = self.root.settings.get(self.root.IMAGE)
		outdir = self.root.settings.get(self.root.OUTDIR)
		filename = self.root.settings.get(self.root.FILENAME)
		blacklist = self.root.settings.get(self.root.BLACKLIST)
		whitelist = self.root.settings.get(self.root.WHITELIST)
		if not source:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.SOURCE_REQUIRED
			)
			return
		if not image:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.ISO_REQUIRED
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
		cmd += f' --image "{image}"'
		path_filter = self.root.settings.get(self.root.REGEXFILTER)
		if path_filter == self.root.BLACKLIST:
			blacklist = self.root.settings.get(self.root.BLACKLIST)
			if blacklist:
				cmd += f' --{self.root.BLACKLIST.lower()} "{blacklist}"'
		elif path_filter == self.root.WHITELIST:
			whitelist = self.root.settings.get(self.root.WHITELIST)
			if whitelist:
				cmd += f' --{self.root.WHITELIST.lower()} "{whitelist}"'
		cmd += f' "{source}"'
		self.root.append_job(cmd)
