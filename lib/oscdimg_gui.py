#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-17'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'GUI plugin for Oscdimg'

from .guielements import ExpandedFrame, GridSeparator, GridLabel
from .guielements import DirSelector, FileSelector, FilenameSelector
from .guielements import LeftLabel, StringRadiobuttons, GridButton, Error

class OscdimgGui:
	'''GUI plugin for Oscdimg'''

	CMD = 'OscdImager'

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		self.frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(self.frame, text=self.CMD)
		GridSeparator(root, self.frame, 0)
		GridLabel(root, self.frame, root.SOURCE, 1, columnspan=2)
		DirSelector(root, self.frame, root.SOURCE,
			root.DIRECTORY, root.SELECT_ROOT, 2)
		GridSeparator(root, self.frame, 3)
		GridLabel(root, self.frame, root.DESTINATION, 4, columnspan=2)
		FilenameSelector(root, self.frame, root.FILENAME, root.FILENAME,
			root.SELECT_FILENAME, 5)
		DirSelector(root, self.frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR, 6)
		GridSeparator(root, self.frame, 7)
		GridLabel(root, self.frame, root.SKIP_PATH_CHECK, 8, columnspan=3)
		StringRadiobuttons(root, self.frame, root.PATHFILTER,
			((f'{None}', 9), (root.BLACKLIST, 10), (root.WHITELIST, 11)), f'{None}')
		GridLabel(root, self.frame, root.CHECK_ALL_PATHS, 9, column=1, columnspan=2)
		FileSelector(root, self.frame,
			root.BLACKLIST, root.BLACKLIST,root.SELECT_BLACKLIST, 10)
		FileSelector(root, self.frame,
			root.WHITELIST, root.WHITELIST, root.SELECT_WHITELIST, 11)
		GridSeparator(root, self.frame, 12)
		GridButton(root, self.frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job, 13)
		self.root = root
	
	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		source = self.root.settings.get(self.root.SOURCE)
		outdir = self.root.settings.get(self.root.OUTDIR)
		filename = self.root.settings.get(self.root.FILENAME)
		blacklist = self.root.settings.get(self.root.BLACKLIST)
		whitelist = self.root.settings.get(self.root.WHITELIST)
		if not source or not outdir or not filename:
			Error.source_dest_required()
			return
		cmd = self.root.settings.section.lower()
		cmd += f' --{self.root.OUTDIR.lower()} {outdir}'
		cmd += f' --{self.root.FILENAME.lower()} {filename}'
		path_filter = self.root.settings.get(self.root.PATHFILTER)
		if path_filter == self.root.BLACKLIST:
			blacklist = self.root.settings.get(self.root.BLACKLIST)
			if blacklist:
				cmd += f' --{self.root.BLACKLIST.lower()} {blacklist}'
		elif path_filter == self.root.WHITELIST:
			whitelist = self.root.settings.get(self.root.WHITELIST)
			if whitelist:
				cmd += f' --{self.root.WHITELIST.lower()} {whitelist}'
		cmd += f' {source}'
		self.root.append_job(cmd)
