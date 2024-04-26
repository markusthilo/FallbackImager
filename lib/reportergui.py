#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter.messagebox import showerror
from tkinter.scrolledtext import ScrolledText
from lib.guielements import ExpandedFrame, GridSeparator, GridLabel
from lib.guielements import ChildWindow, FilenameSelector, DirSelector, FileSelector
from lib.guielements import GridButton, GridBlank, LeftButton, RightButton
from reporter import Reporter

class ReporterGui:
	'''Notebook page'''
	CMD = 'Reporter'

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		GridSeparator(root, frame)
		GridLabel(root, frame, root.SOURCE)
		FileSelector(root, frame,
			root.TEMPLATE, root.TEMPLATE, root.SELECT_TEMPLATE, filetype=('TXT', '*.txt'))
		FileSelector(root, frame,
			root.JSON_FILE, root.JSON_FILE, root.SELECT_JSON, filetype=('JSON', '*.json'))
		GridSeparator(root, frame)
		GridLabel(root, frame, root.DESTINATION)
		FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
		DirSelector(root, frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		GridSeparator(root, frame)
		GridBlank(root, frame)
		GridButton(root, frame, root.PARSE_NOW, self._parse)
		root.child_win_active = False
		self.root = root

	def _parse(self):
		'''Parse instantaniously and show in preview window'''
		if self.root.child_win_active:
			return
		self.root.settings.section = self.CMD
		template = self.root.settings.get(self.root.TEMPLATE)
		if not template:
			showerror(
				title = self.root.TEMPLATE,
				message = self.root.SOURCE_REQUIRED
			)
			return
		json = self.root.settings.get(self.root.JSON_FILE)
		if not json:
			showerror(
				title = self.root.JSON,
				message = self.root.SOURCE_REQUIRED
			)
			return
		outdir = self.root.settings.get(self.root.OUTDIR)
		filename = self.root.settings.get(self.root.FILENAME)
		self.preview_window = ChildWindow(self.root, self.root.PREVIEW)
		self.reporter = Reporter()
		self.text = ScrolledText(self.preview_window,
			width = self.root.ENTRY_WIDTH,
			height = 4*self.root.INFO_HEIGHT,
			wrap = 'word'
		)
		self.text.pack(fill='both', expand=True)
		self.text.insert('1.0', self.reporter.parse(json, template))
		if self.reporter.errors > 0:
			self.text.insert('end', f'\n\n### {self.root.PARSER_REPORTED} {self.reporter.errors} {self.root.ERRORS} ###')

		frame = ExpandedFrame(self.root, self.preview_window)
		if outdir or filename:
			LeftButton(self.root, frame, self.root.WRITE_TO_FILE, self._write)
		RightButton(self.root, frame, self.root.QUIT, self.preview_window.destroy)

	def _write(self):
		'''Write to file'''
		self.root.settings.section = self.CMD
		outdir = self.root.settings.get(self.root.OUTDIR)
		filename = self.root.settings.get(self.root.FILENAME)
		if outdir or filename:
			self.reporter.write(filename=filename, outdir=outdir)
		else:
			showerror(
				title = self.root.ERROR,
				message = self.root.SELECT_DEST_DIR
			)
		self.preview_window.destroy()
