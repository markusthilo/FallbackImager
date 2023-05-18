#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-17'
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