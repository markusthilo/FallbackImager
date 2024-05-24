#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter.scrolledtext import ScrolledText
from .guiconfig import GuiConfig
from .guilabeling import ReporterLabels
from .guielements import NotebookFrame, GridSeparator, GridLabel
from .guielements import OutDirSelector, FilenameSelector, GridBlank
from .guielements import FileSelector, GridButton, MissingEntry
from .guielements import LeftButton, RightButton
from reporter import Reporter

class ReporterGui(ReporterLabels):
	'''Notebook page'''

	MODULE = 'Reporter'

	def __init__(self, root):
		'''Notebook page'''
		self.root = root
		frame = NotebookFrame(self)
		GridLabel(frame, self.SOURCE)
		self.template = FileSelector(
			frame,
			self.root.settings.init_stringvar('Template'),
			self.TEMPLATE,
			self.SELECT_TEMPLATE,
			filetype = ('TXT', '*.txt'),
			tip = self.TIP_TEMPLATE,
		)
		self.json = FileSelector(
			frame,
			self.root.settings.init_stringvar('Json'),
			self.JSON,
			self.SELECT_JSON,
			filetype = ('JSON', '*.json'),
			tip = self.TIP_JSON,
		)
		GridSeparator(frame)
		GridLabel(frame, self.DESTINATION)
		self.outdir = OutDirSelector(frame, self.root.settings.init_stringvar('OutDir'))
		self.filename = FilenameSelector(frame, '{now}_report',
			self.root.settings.init_stringvar('Filename'))
		GridBlank(frame)
		GridSeparator(frame)
		GridButton(frame, self.PARSE, self._parse, column=0, columnspan=2)
		self.root.child_win_active = False

	def _parse(self):
		'''Parse instantaniously and show in preview window'''
		if self.root.child_win_active:
			return
		template = self.template.get()
		if not template:
			MissingEntry(self.TEMPLATE_REQUIRED)
			return
		json = self.json.get()
		if not json:
			MissingEntry(self.JSON_REQUIRED)
			return
		self.preview_window = ChildWindow(self.root, self.PREVIEW)
		self.reporter = Reporter()
		self.text = ScrolledText(self.preview_window,
			width = GuiConfig.ENTRY_WIDTH,
			height = 4*GuiConfig.INFO_HEIGHT,
			wrap = 'word'
		)
		self.text.pack(fill='both', expand=True)
		self.text.insert('1.0', self.reporter.parse(json, template))
		if self.reporter.errors > 0:
			self.text.insert('end', f'\n\n### {self.root.PARSER_REPORTED} {self.reporter.errors} {self.root.ERRORS} ###')

		frame = ExpandedFrame(self.preview_window)
		if self.outdir.get():
			LeftButton(frame, self.WRITE_TO_FILE, self._write)
		RightButton(frame, self.QUIT, self.preview_window.destroy)

	def _write(self):
		'''Write to file'''
		outdir = self.outdir.get()
		filename = self.filename.get()
		if outdir:
			self.reporter.write(filename=filename, outdir=outdir)
		else:
			MissingEntry(self.OUTDIR_REQUIRED)
		self.preview_window.destroy()
