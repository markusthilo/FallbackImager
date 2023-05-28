#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from tkinter.ttk import Frame, LabelFrame, Notebook, Separator, Button
from tkinter.ttk import Label, Entry, Radiobutton, Checkbutton
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import showerror
from .timestamp import TimeStamp

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
	def __init__(self, root, parent, text, command, column=0, columnspan=1):
		super().__init__(parent, text=text, command=command)
		self.grid(row=root.row, column=column, columnspan=columnspan, sticky='w', padx=root.PAD)
		root.row += 1

class GridSeparator:
	'''|-------|'''
	def __init__(self, root, parent, column=0, columnspan=3):
		Separator(parent).grid(row=root.row, column=column, columnspan=columnspan,
			sticky='w', padx=root.PAD)
		root.row += 1

class GridLabel:
	'''| Label |'''
	def __init__(self, root, parent, text, column=0, columnspan=1):
		Label(parent, text=text).grid(row=root.row, column=column, columnspan=columnspan,
			sticky='w', padx=root.PAD)
		root.row += 1

class StringField(Button):
	'''Button + Entry to enter string'''
	def __init__(self, root, parent, key, text, command, column=1):
		self.string = root.settings.init_stringvar(key)
		super().__init__(parent, text=text, command=command)
		self.grid(row=root.row, column=column, sticky='e', padx=root.PAD)
		Entry(parent, textvariable=self.string, width=root.ENTRY_WIDTH).grid(
			row=root.row, column=column+1, sticky='w', padx=root.PAD)
		root.row += 1

class StringRadiobuttons:
	'''| Rabiobutton | | | |'''
	def __init__(self, root, parent, key, buttons, default, column=0):
		self.variable = root.settings.init_stringvar(key, default=default)
		for row, value in enumerate(buttons):
			Radiobutton(parent, variable=self.variable, value=value).grid(
				row=root.row+row, column=column, sticky='w', padx=root.PAD)

class SourceDirSelector(Button):
	'''Select source'''
	def __init__(self, root, parent, column=1, columnspan=1):
		self.source_str = root.settings.init_stringvar(root.SOURCE)
		
		GridSeparator(root, parent)
		GridLabel(root, parent, root.SOURCE, column=column, columnspan=columnspan)
		super().__init__(parent, text=root.SOURCE, command=self._select)
		self.grid(row=root.row, column=column, sticky='w', padx=root.PAD)
		Entry(parent, textvariable=self.source_str, width=root.ENTRY_WIDTH).grid(
			row=root.row, column=column+1, columnspan=columnspan, sticky='w', padx=root.PAD)
		root.row += 1
		GridSeparator(root, parent)
		self.root = root
	def _select(self):
		new_dir = askdirectory(title=self.root.ASK_SOURCE)
		if new_dir:
			self.source_str.set(new_dir)

class StringSelector(Button):
	'''String for names, descriptions etc.'''
	def __init__(self, root, parent, key, text, command=None, column=1, columnspan=1):
		self.string = root.settings.init_stringvar(key)
		super().__init__(parent, text=text, command=command)
		self.grid(row=root.row, column=column, sticky='w', padx=root.PAD)
		Entry(parent, textvariable=self.string, width=root.ENTRY_WIDTH).grid(
			row=root.row, column=column+1, columnspan=columnspan, sticky='w', padx=root.PAD)
		root.row += 1

class Checker(Checkbutton):
	'''Checkbox'''
	def __init__(self, root, parent, key, text, column=0, columnspan=1):
		self.int_var = root.settings.init_stringvar(key)
		super().__init__(parent, variable=self.int_var)
		self.grid(row=root.row, column=column, sticky='w', padx=root.PAD)
		GridLabel(root, parent, text, column=column+1, columnspan=columnspan)

class FileSelector(Button):
	'''Button to select file to read'''
	def __init__(self, root, parent, key, text, ask,
		filetype=('Text files', '*.txt'), default=None, column=1, columnspan=1):
		self.file_str = root.settings.init_stringvar(key)
		if default:
			self.file_str.set(default)
		super().__init__(parent, text=text, command=self._select)
		self.grid(row=root.row, column=column, sticky='w', padx=root.PAD, pady=(root.PAD, 0))
		Entry(parent, textvariable=self.file_str, width=root.ENTRY_WIDTH).grid(
			row=root.row, column=2, sticky='w', padx=root.PAD)
		root.row += 1
		self.root = root
		self.ask = ask
		self.filetype = filetype
	def _select(self):
		new_filename = askopenfilename(title=self.ask, filetypes=(self.filetype, ('All files', '*.*')))
		if new_filename:
			self.file_str.set(new_filename)

class FilenameSelector(Button):
	'''Button + Entry to enter string'''	
	def __init__(self, root, parent, key, text, default=None, column=1, columnspan=1):
		self.string = root.settings.init_stringvar(key)
		self.default = default
		super().__init__(parent, text=text, command=self._command) 
		self.grid(row=root.row, column=column, columnspan=columnspan, sticky='w', padx=root.PAD)
		Entry(parent, textvariable=self.string, width=root.ENTRY_WIDTH).grid(
			row=root.row, column=column+1, sticky='w', padx=root.PAD)
		root.row += 1
	def _command(self):
		if self.string.get():
			return
		if self.default:
			self.string.set(self.default)
		else:
			self.string.set(TimeStamp.now(path_comp=True))

class DirSelector(Button):
	'''Button + Entry to select directory'''
	def __init__(self, root, parent, key, text, ask, column=1, columnspan=1):
		self.dir_str = root.settings.init_stringvar(key)
		super().__init__(parent, text=text, command=self._select)
		self.grid(row=root.row, column=column, columnspan=columnspan, sticky='w', padx=root.PAD)
		Entry(parent, textvariable=self.dir_str, width=root.ENTRY_WIDTH).grid(
			row=root.row, column=column+1, sticky='w', padx=root.PAD)
		root.row += 1
		self.root = root
		self.ask = ask
	def _select(self):
		new_dir = askdirectory(title=self.ask, mustexist=False)
		if new_dir:
			self.dir_str.set(new_dir)

class BasicTab:
	'''Basic ExpandedNotebook'''

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		SourceDirSelector(root, frame)
		GridLabel(root, frame, root.DESTINATION, columnspan=2)
		FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
		DirSelector(root, frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		GridSeparator(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job, columnspan=3)
		self.root = root
	
	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		source = self.root.settings.get(self.root.SOURCE)
		outdir = self.root.settings.get(self.root.OUTDIR)
		filename = self.root.settings.get(self.root.FILENAME)
		if not source or not outdir or not filename:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.SOURCED_DEST_REQUIRED
			)
			return
		cmd = self.root.settings.section.lower()
		cmd += f' --{self.root.OUTDIR.lower()} "{outdir}"'
		cmd += f' --{self.root.FILENAME.lower()} "{filename}"'
		cmd += f' "{source}"'
		self.root.append_job(cmd)

class BasicFilterTab:
	'''Basic ExpandedNotebook with blacklist and whitelist'''

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		SourceDirSelector(root, frame)
		GridLabel(root, frame, root.DESTINATION, columnspan=2)
		FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
		DirSelector(root, frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		GridSeparator(root, frame)
		GridLabel(root, frame, root.SKIP_PATH_CHECK, columnspan=3)
		StringRadiobuttons(root, frame, root.PATHFILTER,
			(f'{None}', root.BLACKLIST, root.WHITELIST), f'{None}')
		GridLabel(root, frame, root.CHECK_ALL_PATHS, column=1, columnspan=2)
		FileSelector(root, frame,
			root.BLACKLIST, root.BLACKLIST, root.SELECT_BLACKLIST)
		FileSelector(root, frame,
			root.WHITELIST, root.WHITELIST, root.SELECT_WHITELIST)
		GridSeparator(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job, columnspan=3)
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
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.SOURCED_DEST_REQUIRED
			)
			return
		cmd = self.root.settings.section.lower()
		cmd += f' --{self.root.OUTDIR.lower()} "{outdir}"'
		cmd += f' --{self.root.FILENAME.lower()} "{filename}"'
		path_filter = self.root.settings.get(self.root.PATHFILTER)
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
