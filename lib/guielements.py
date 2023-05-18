#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-18'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'GUI elements'

from pathlib import Path
from tkinter.ttk import Frame, LabelFrame, Notebook, Separator, Button
from tkinter.ttk import Label, Entry, Radiobutton
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import showerror

class ExpandedFrame(Frame):
	'''|<- Frame ->|'''
	def __init__(self, root, parent):
		super().__init__(parent)
		self.pack(fill='both', padx=root.PAD, pady=root.PAD, expand=True)

class ExpandedNotebook(Notebook):
	'''|<- Notebook ->|'''
	def __init__(self, root):
		super().__init__(root)
		self.pack(fill='both', padx=root.PAD, pady=root.PAD, expand=True)

class ExpandedLabelFrame(LabelFrame):
	'''|<- LabelFrame ->|'''
	def __init__(self, root, parent, text):
		super().__init__(parent, text=text)
		self.pack(fill='both', padx=root.PAD, expand=True)

class ExpandedSeparator:
	'''|<--------->|'''
	def __init__(self, root, parent):
		Separator(parent).pack(fill='both', padx=root.PAD, expand=True)

class ExpandedLabel:
	'''|<- Label ->|'''
	def __init__(self, root, parent, text):
		Label(parent, text=text).pack(
			fill='both', padx=root.PAD, expand=True)

class LeftLabel:
	'''| Label --->|'''
	def __init__(self, root, parent, text):
		Label(parent, text=text).pack(padx=root.PAD, side='left')

class ExpandedScrolledText(ScrolledText):
	'''|<- ScrolledText ->|'''
	def __init__(self, root, parent, height):
		super().__init__(parent,
			padx = root.PAD,
			pady = root.PAD,
			width = -1,
			height = height
		)
		self.pack(fill='both', padx=root.PAD, expand=True)

class LeftButton(Button):
	'''| Button ---|'''
	def __init__(self, root, parent, text, command):
		super().__init__(parent, text=text, command=command)
		self.pack(padx=root.PAD, side='left')

class RightButton(Button):
	'''|--- Button |'''
	def __init__(self, root, parent, text, command):
		super().__init__(parent, text=text, command=command)
		self.pack(padx=root.PAD, side='right')

class GridButton(Button):
	'''| | Button | | |'''
	def __init__(self, root, parent, text, command, row, column=0, columnspan=3):
		super().__init__(parent, text=text, command=command)
		self.grid(row=row, column=column, columnspan=columnspan, sticky='w', padx=root.PAD)

class GridSeparator:
	'''|-------|'''
	def __init__(self, root, parent, row):
		Separator(parent).grid(row=row, column=0, columnspan=3,
			sticky='w', padx=root.PAD)

class GridLabel:
	'''| Label |'''
	def __init__(self, root, parent, text, row, column=0, columnspan=1):
		Label(parent, text=text).grid(row=row, column=column, columnspan=columnspan,
			sticky='w', padx=root.PAD)

class StringField(Button):
	'''Button + Entry to enter string'''
	def __init__(self, root, parent, key, text, command, row):
		root.settings.init_stringvar(key)
		super().__init__(parent, text=text, command=command)
		self.grid(row=row, column=1, sticky='e', padx=root.PAD)
		Entry(parent, textvariable=root.settings.raw(key), width=root.ENTRY_WIDTH).grid(
			row=row, column=2, sticky='w', padx=root.PAD)

class StringRadiobuttons:
	'''| Rabiobutton | | | |'''
	def __init__(self, root, parent, key, buttons, default):
		root.settings.init_stringvar(key, default=default)
		for value, row in buttons:
			Radiobutton(parent, variable=root.settings.raw(key), value=value).grid(
				row=row, column=0, sticky='w', padx=root.PAD)

class FileSelector(Button):
	'''Button to select file to read'''
	def __init__(self, root, parent, key, text, ask, row,
		filetype=('Text files', '*.txt'),):
		root.settings.init_stringvar(key)
		super().__init__(parent,
			text = text,
			command = lambda: root.settings.raw(key).set(
				askopenfilename(title=ask, filetypes=(filetype, ('All files', '*.*')))
			)
		)
		self.grid(row=row, column=1, sticky='w', padx=root.PAD, pady=(root.PAD, 0))
		Entry(parent, textvariable=root.settings.raw(key), width=root.ENTRY_WIDTH).grid(
			row=row, column=2, sticky='w', padx=root.PAD)

class FilenameSelector(Button):
	'''Button + Entry to enter string'''
	def __init__(self, root, parent, key, text, ask, row):
		root.settings.init_stringvar(key)
		super().__init__(parent, text=text, command=self._askfilename) 
		self.grid(row=row, column=1, sticky='w', padx=root.PAD)
		Entry(parent, textvariable=root.settings.raw(key), width=root.ENTRY_WIDTH).grid(
			row=row, column=2, sticky='w', padx=root.PAD)
		self.root = root
		self.key = key
		self.ask = ask
	def _askfilename(self):
		filename = askopenfilename(title=self.ask)
		if filename:
			self.root.settings.raw(self.key).set(Path(filename).stem)

class DirSelector(Button):
	'''Button + Entry to select directory'''
	def __init__(self, root, parent, key, text, ask, row):
		root.settings.init_stringvar(key)
		super().__init__(parent,
			text = text,
			command = lambda: root.settings.raw(key).set(
				askdirectory(
					title = ask,
					mustexist = False
				)
			)
		)
		self.grid(row=row, column=1, sticky='w', padx=root.PAD)
		Entry(parent, textvariable=root.settings.raw(key), width=root.ENTRY_WIDTH).grid(
			row=row, column=2, sticky='w', padx=root.PAD)

class Error:
	@staticmethod
	def source_dest_required():
		showerror(
			title = 'Missing entries',
			message = 'Source, destination directory and destination filename (without extension) are requiered'
		)

class BasicFilterTab:
	'''Basic ExpandedNotebook with blacklist and whitelist'''

	def __init__(self, root):
		'''Notebook page for an imager'''
		root.settings.init_section(self.CMD)
		self.frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(self.frame, text=f' {self.CMD} ')
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



