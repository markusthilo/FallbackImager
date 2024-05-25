#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from idlelib.tooltip import Hovertip
from tkinter import Toplevel
from tkinter.ttk import Frame, LabelFrame, Notebook, Separator, Button, Treeview
from tkinter.ttk import Label, Entry, Radiobutton, Checkbutton, OptionMenu, Scrollbar
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import showerror
from .guilabeling import BasicLabels
from .guiconfig import GuiConfig
from .timestamp import TimeStamp

class Error:
	'''Show error'''
	def __init__(self, message):
		showerror(title=BasicLabels.ERROR, message=message)

class MissingEntry:
	'''Show error for missing entry'''
	def __init__(self, message):
		showerror(title=BasicLabels.MISSING_ENTRY, message=message)

class ExpandedFrame(Frame):
	'''|<- Frame ->|'''
	def __init__(self, parent):
		super().__init__(parent)
		self.pack(fill='both', padx=GuiConfig.PAD, pady=GuiConfig.PAD, expand=True)
		self.row = 0

class ExpandedNotebook(Notebook):
	'''|<- Notebook ->|'''
	def __init__(self, parent):
		super().__init__(parent)
		self.pack(fill='both', padx=GuiConfig.PAD, pady=GuiConfig.PAD, expand=True)

class ExpandedLabelFrame(LabelFrame):
	'''|<- LabelFrame ->|'''
	def __init__(self, parent, text):
		super().__init__(parent, text=text)
		self.pack(fill='both', padx=GuiConfig.PAD, expand=True)

class ExpandedSeparator:
	'''|<--------->|'''
	def __init__(self, parent):
		Separator(parent).pack(fill='both', padx=GuiConfig.PAD, expand=True)

class ExpandedLabel:
	'''|<- Label ->|'''
	def __init__(self, parent, text):
		Label(parent, text=text).pack(
			fill='both', padx=GuiConfig.PAD, expand=True)

class LeftLabel:
	'''| Label --->|'''
	def __init__(self, parent, text):
		Label(parent, text=text).pack(padx=GuiConfig.PAD, side='left')

class ExpandedScrolledText(ScrolledText):
	'''|<- ScrolledText ->|'''
	def __init__(self, parent, height):
		super().__init__(parent,
			padx = GuiConfig.PAD,
			pady = GuiConfig.PAD,
			width = -1,
			height = height
		)
		self.pack(fill='both', padx=GuiConfig.PAD, expand=True)

class LeftButton(Button):
	'''| Button ---|'''
	def __init__(self, parent, text, command, tip=None):
		super().__init__(parent, text=text, command=command, width=GuiConfig.BUTTON_WIDTH)
		self.pack(padx=GuiConfig.PAD, side='left')
		if tip:
			Hovertip(self, tip)

class RightButton(Button):
	'''|--- Button |'''
	def __init__(self, parent, text, command, tip=None):
		super().__init__(parent, text=text, command=command, width=GuiConfig.BUTTON_WIDTH)
		self.pack(padx=GuiConfig.PAD, side='right')
		if tip:
			Hovertip(self, tip)

class GridButton(Button):
	'''| | Button | | |'''
	def __init__(self, parent, text, command, column=1, columnspan=1, incrow=True, tip=None):
		super().__init__(parent, text=text, command=command, width=GuiConfig.BUTTON_WIDTH)
		self.grid(row=parent.row, column=column, columnspan=columnspan, sticky='w', padx=GuiConfig.PAD)
		if incrow:
			parent.row += 1
		if tip:
			Hovertip(self, tip)

class GridSeparator:
	'''|-------|'''
	def __init__(self, parent, column=0, columnspan=255, incrow=True):
		Separator(parent).grid(row=parent.row, column=column, columnspan=columnspan,
			sticky='w', padx=GuiConfig.PAD, pady=GuiConfig.PAD)
		if incrow:
			parent.row += 1

class GridLabel:
	'''| Label |'''
	def __init__(self, parent, text, column=0, columnspan=255, incrow=True):
		Label(parent, text=text).grid(row=parent.row, column=column, columnspan=columnspan,
			sticky='w', padx=GuiConfig.PAD)
		if incrow:
			parent.row += 1

class GridBlank:
	'''| |'''
	def __init__(self, parent, width=2, column=0, incrow=True):
		Label(parent, width=width).grid(row=parent.row, column=column, padx=GuiConfig.PAD)
		if incrow:
			parent.row += 1

class NotebookFrame(ExpandedFrame):
	'''To start a module'''
	def __init__(self, parent):
		parent.root.settings.this_section = parent.MODULE
		super().__init__(parent.root.notebook)
		parent.root.notebook.add(self, text=f' {parent.MODULE} ')
		GridSeparator(self)

class AddJobButton(GridButton):
	'''| [Add job] | | |'''
	def __init__(self, parent, module, command, column=0, columnspan=255):
		GridBlank(parent)
		GridSeparator(parent)
		super().__init__(parent, f'{BasicLabels.ADD_JOB} {module}', command,
			column=column, columnspan=columnspan, tip=BasicLabels.TIP_ADD_JOB)

class GridMenu(OptionMenu):
	'''| | OptionMenu | | |'''
	def __init__(self, parent, variable, text, values,
		width=None, column=1, columnspan=2, incrow=True, tip=None):
		self._variable = variable
		Label(parent, text=f'{text}:').grid(sticky='e', row=parent.row, column=column, padx=GuiConfig.PAD)
		super().__init__(parent, self._variable, self._variable.get(), *values)
		self.grid(sticky='w', row=parent.row, column=column+1, columnspan=columnspan-1, padx=GuiConfig.PAD)
		if not width:
			width = GuiConfig.MENU_WIDTH
		self.configure(width=width)
		if incrow:
			parent.row += 1
		if tip:
			Hovertip(self, tip)
	def set(self, value):
		self._variable.set(value=value)
	def get(self):
		return self._variable.get()

class Checker(Checkbutton):
	'''Checkbox'''
	def __init__(self, parent, variable, text, column=0, columnspan=2, tip=None):
		self._variable = variable
		super().__init__(parent, variable=self._variable)
		self.grid(row=parent.row, column=column)
		GridLabel(parent, text, column=column+1, columnspan=columnspan-1)
		if tip:
			Hovertip(self, tip)
	def set(self, value):
		self._variable.set(value=value)
	def get(self):
		return self._variable.get()

class StringRadiobuttons:
	'''| Rabiobutton | | | |'''
	def __init__(self, parent, variable, buttons, column=0):
		self._variable = variable
		for row, value in enumerate(buttons, parent.row):
			button = Radiobutton(parent, variable=self._variable, value=value)
			button.grid(row=row, column=column, sticky='w', padx=GuiConfig.PAD)
			Hovertip(button, BasicLabels.TIP_RADIO_BUTTONS)
	def set(self, value):
		self._variable.set(value=value)
	def get(self):
		return self._variable.get()

class VerticalRadiobuttons:
	'''| Rabiobutton | Radiobutton | Radiobutton | ... |'''
	def __init__(self, parent, variable, buttons, column=1, columnspan=255, incrow=True):
		frame = Frame(parent)
		frame.grid(row=parent.row, column=column, columnspan=columnspan, sticky='w', padx=GuiConfig.PAD)
		self._variable = variable
		for value in buttons:
			button = Radiobutton(frame, variable=self._variable, value=value, text=value)
			button.pack(side='left', padx=(GuiConfig.PAD, 0))
			Hovertip(button, BasicLabels.TIP_RADIO_BUTTONS)
		if incrow:
			parent.row += 1
	def set(self, value):
		self._variable.set(value=value)
	def get(self):
		return self._variable.get()

class StringSelector(Button):
	'''Button + Entry to select/write a string'''
	def __init__(self, parent, variable, text, command=None, default=None, width=None,
		column=1, columnspan=255, incrow=True, tip=None):
		self._variable = variable
		if not command:
			command = self._command
			self.default = default
		super().__init__(parent, text=text, command=command, width=GuiConfig.BUTTON_WIDTH)
		self.grid(row=parent.row, column=column, sticky='w', padx=GuiConfig.PAD)
		if not width:
			width = GuiConfig.ENTRY_WIDTH
		Entry(parent, textvariable=self._variable, width=width).grid(
			row=parent.row, column=column+1, columnspan=columnspan-1, sticky='w', padx=GuiConfig.PAD)
		if incrow:
			parent.row += 1
		if tip:
			Hovertip(self, tip)
	def _command(self):
		if self._variable.get():
			return
		if self.default:
			self._variable.set(self.default)
	def set(self, value):
		self._variable.set(value=value)
	def get(self):
		return self._variable.get()

class FilenameSelector(StringSelector):
	'''Button + Entry to select filename/base for output filenames'''	
	def __init__(self, parent, default, variable):
		super().__init__(parent, variable, BasicLabels.FILENAME, command=self._command,
			tip=BasicLabels.TIP_FILENAME)
		self.default = default
	def _command(self):
		if self._variable.get():
			return
		self._variable.set(self.default.replace('{now}', TimeStamp.now(path_comp=True)))

class DirSelector(Button):
	'''Button + Entry to select a directory'''
	def __init__(self, parent, variable, text, ask,
		default=None, command=None, column=1, columnspan=255, incrow=True, tip=None, missing=None):
		self._variable = variable
		super().__init__(parent, text=text, command=self._select, width=GuiConfig.BUTTON_WIDTH)
		self.grid(row=parent.row, column=column, sticky='w', padx=GuiConfig.PAD)
		Entry(parent, textvariable=self._variable, width=GuiConfig.ENTRY_WIDTH).grid(
			row=parent.row, column=column+1, columnspan=columnspan, sticky='w', padx=GuiConfig.PAD)
		self.ask = ask
		self.command = command
		self.missing = missing
		if incrow:
			parent.row += 1
		if tip:
			Hovertip(self, tip)
	def _select(self):
		new_dir = askdirectory(title=self.ask, mustexist=False)
		if new_dir:
			self._variable.set(new_dir)
		if self.command:
			self.command()
	def set(self, value):
		self._variable.set(value=value)
	def get(self):
		return self._variable.get()

class OutDirSelector(DirSelector):
	'''Select destination/output directory'''
	def __init__(self, parent, variable, tip=None):
		if not tip:
			tip = BasicLabels.TIP_OUTDIR
		super().__init__(parent, variable, BasicLabels.DIRECTORY, BasicLabels.SELECT_OUTDIR,
			tip=tip, missing=BasicLabels.OUTDIR_REQUIRED)

class SourceDirSelector(DirSelector):
	'''Select source directory'''
	def __init__(self, parent, variable, tip=None):
		super().__init__(parent, variable, BasicLabels.SOURCE, BasicLabels.SELECT_SOURCE,
			tip=tip, missing=BasicLabels.SOURCE_REQUIRED)

class FileSelector(Button):
	'''Select a file'''
	def __init__(self, parent, variable, text, ask, command=None,
		filetype=('Text files', '*.txt'), initialdir=None,
		column=1, columnspan=255, incrow=True, tip=None):
		self._variable = variable
		super().__init__(parent, text=text, command=self._select, width=GuiConfig.BUTTON_WIDTH)
		self.grid(row=parent.row, column=column, sticky='w', padx=GuiConfig.PAD, pady=(GuiConfig.PAD, 0))
		Entry(parent, textvariable=self._variable, width=GuiConfig.ENTRY_WIDTH).grid(
			row=parent.row, column=column+1, columnspan=columnspan-1, sticky='w', padx=GuiConfig.PAD)
		self.ask = ask
		self.filetype = filetype
		self.initialdir = initialdir
		self.command = command
		if incrow:
			parent.row += 1
		if tip:
			Hovertip(self, tip)
	def _select(self):
		new_filename = askopenfilename(
			title = self.ask,
			filetypes = (self.filetype, ('All files', '*.*')),
			initialdir = self.initialdir
		)
		if new_filename:
			self._variable.set(new_filename)
		if self.command:
			self.command()
	def set(self, value):
		self._variable.set(value=value)
	def get(self):
		return self._variable.get()

class SourceFileSelector(FileSelector):
	'''Select source directory'''
	def __init__(self, parent, variable, tip=None):
		super().__init__(root, parent, variable, BasicLabels.SOURCE, BasicLabels.SELECT_SOURCE,
			tip=tip, missing=BasicLabels.SOURCE_REQUIRED)

class Tree(Treeview):
	'''Treeview with vertical scroll bar'''
	def __init__(self, parent, selectmode='browse', width=None, height=None):
		if not width:
			width = GuiConfig.TREE_WIDTH
		if not height:
			height = GuiConfig.TREE_HEIGHT
		super().__init__(parent, selectmode=selectmode, height=height, show='tree')
		self.column("#0", width=width)
		self.pack(side='left', expand=True)
		vsb = Scrollbar(parent, orient='vertical', command=self.yview)
		vsb.pack(side='right', fill='y')
		self.configure(yscrollcommand=vsb.set)

class ChildWindow(Toplevel):
	'''Child window to main application window'''

	def __init__(self, root, title):
		'''Open child window'''
		self.root = root
		super().__init__(self.root)
		self.title(title)
		self.resizable(0, 0)
		self.iconphoto(True, self.root.appicon)
		self.protocol('WM_DELETE_WINDOW', self.destroy)
		self.root.child_win_active = True

	def destroy(self):
		'''Destroy the child window'''
		self.root.child_win_active = False
		super().destroy()
