#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from tkinter.scrolledtext import ScrolledText
from .timestamp import TimeStamp
from .guiconfig import GuiConfig
from .guilabeling import ReporterLabels
from .guielements import NotebookFrame, GridSeparator, GridLabel
from .guielements import OutDirSelector, StringSelector, GridBlank
from .guielements import FileSelector, GridButton, MissingEntry, ChildWindow
from .guielements import ExpandedFrame, LeftButton, RightButton
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
		self.filename = StringSelector(frame, self.root.settings.init_stringvar('Filename'), self.FILENAME,
			command=self._gen_filename, tip=self.TIP_FILENAME)
		GridBlank(frame)
		GridSeparator(frame)
		GridButton(frame, self.PARSE, self._parse, column=0, columnspan=2)
		self.root.child_win_active = False

	def _gen_filename(self):
		'''Generate default filename from JSON filename'''
		if self.filename.get():
			return
		json = self.json.get()
		if json:
			self.filename.set(Path(json).stem)
		else:
			self.filename.set(f'{TimeStamp.now(path_comp=True)}_report')

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
		self.text.pack(fill='both', padx=GuiConfig.PAD, pady=GuiConfig.PAD, expand=True)
		self.text.insert('1.0', self.reporter.parse(json, template))
		if self.reporter.errors > 0:
			self.text.insert('end', f'\n\n### {self.PARSER_REPORTED} {self.reporter.errors} {self.ERRORS} ###')
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
