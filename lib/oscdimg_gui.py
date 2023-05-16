#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-17'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'GUI plugin for Oscdimg'

from lib.guielements import ExpandedFrame, GridSeparator, GridLabel
from lib.guielements import DirSelector, FileSelector, FilenameSelector
from lib.guielements import LeftLabel, StringRadiobuttons, GridButton

class OscdimgGui:
	'''GUI plugin for Oscdimg'''

	CMD = 'oscdimager'

	def __init__(self, root):
		'''Notebook page'''
		self.settings = root.settings
		self.settings.init_section(self.CMD)
		self.frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(self.frame, text=self.CMD)
		GridSeparator(root, self.frame, 0)
		GridLabel(root, self.frame, 'Source:', 1, columnspan=2)
		DirSelector(root, self.frame, 'source',
			'Directory', 'Select source directory', 2)
		GridSeparator(root, self.frame, 3)
		GridLabel(root, self.frame, 'Destination:', 4, columnspan=2)
		FilenameSelector(root, self.frame, 'filename', 'Filename',
			'Select file to use name', 5)
		DirSelector(root, self.frame, 'outdir',
			'Directory', 'Select destination directory', 6)
		GridSeparator(root, self.frame, 7)
		GridLabel(root, self.frame, 'Do not verify:', 8, columnspan=2)
		StringRadiobuttons(root, self.frame, 'pathfilter',
			(('none', 9), ('blacklist', 10), ('whitelist', 11)), 'none')
		GridLabel(root, self.frame, 'Check if all source paths are in image', 9, column=1, columnspan=2)
		FileSelector(root, self.frame, 'blacklist', 'Blacklist', 'Select blacklist', 10)
		FileSelector(root, self.frame, 'whitelist', 'Whitelist', 'Select whitelist', 11)
		GridSeparator(root, self.frame, 12)
		GridButton(root, self.frame, 'Add imaging to ISO', self._add_job, 13)
		self.root = root
	
	def _add_job(self):
		'''Generate command line'''
		self.settings.section = 'oscimg'
		root = self.settings.get('root')
		outdir = self.settings.get('outdir')
		filename = self.settings.get('filename')
		blacklist = self.settings.get('blacklist')
		whitelist = self.settings.get('whitelist')
		if not rootdir or not destdir or not destfname:
			showerror(
				title = f'{self.app_name}/{self.settings.section}',
				message = 'Source, destination directory and destination filename (without extension) are requiered'
			)
			return
		cmd = self.settings.section
		use_list = self.settings.get('use_list')
		if use_list == 'blacklist':
			blacklist = self.settings.get('blacklist')
			if blacklist:
				cmd += f' -b {blacklist}'
		elif use_list == 'whitelist':
			whitelist = self.settings.get('whitelist')
			if whitelist:
				cmd += f' -w {whitelist}'
		if self.settings.get('image_type') == 'joliet':
			cmd += ' -j'
		cmd += f' -o {destdir} -f {destfname} {rootdir}\n'
		self.jobs.insert(END, f'{cmd}')
		self.jobs.yview(END)
