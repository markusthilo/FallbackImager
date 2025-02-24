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
		try:
			self.padding = parent.padding
		except AttributeError:
			self.padding = parent.root.padding
		super().__init__(parent)
		self.pack(fill='x', padx=self.padding, pady=self.padding, expand=True)
		self.row = 0

class ExpandedNotebook(Notebook):
	'''|<- Notebook ->|'''
	def __init__(self, parent):
		self.font_family = parent.font_family
		self.font_size = parent.font_size
		self.padding = parent.padding
		super().__init__(parent)
		self.pack(fill='both', padx=self.padding, pady=self.padding, expand=True)

class ExpandedLabelFrame(LabelFrame):
	'''|<- LabelFrame ->|'''
	def __init__(self, parent, text):
		super().__init__(parent, text=text)
		self.pack(fill='x', padx=parent.padding, expand=True)

class ExpandedSeparator:
	'''|<--------->|'''
	def __init__(self, parent):
		Separator(parent).pack(fill='x', padx=parent.padding, expand=True)

class ExpandedLabel:
	'''|<- Label ->|'''
	def __init__(self, parent, text):
		Label(parent, text=text).pack(
			fill='x', padx=parent.padding, expand=True)

class LeftLabel:
	'''| Label --->|'''
	def __init__(self, parent, text):
		Label(parent, text=text).pack(padx=parent.padding, side='left')

class ExpandedScrolledText(ScrolledText):
	'''|<- ScrolledText ->|'''
	def __init__(self, parent, height, width=-1):
		super().__init__(parent,
			font = (parent.font_family, parent.font_size),
			padx = parent.padding,
			pady = parent.padding,
			width = width,
			height = height
		)
		self.pack(fill='both', padx=parent.padding, expand=True)

class LeftButton(Button):
	'''| Button ---|'''
	def __init__(self, parent, text, command, tip=None):
		super().__init__(parent, text=text, command=command, width=GuiConfig.BUTTON_WIDTH)
		self.pack(padx=parent.padding, side='left')
		if tip:
			Hovertip(self, tip)

class RightButton(Button):
	'''|--- Button |'''
	def __init__(self, parent, text, command, tip=None):
		super().__init__(parent, text=text, command=command, width=GuiConfig.BUTTON_WIDTH)
		self.pack(padx=parent.padding, side='right')
		if tip:
			Hovertip(self, tip)

class ExpandedTree(Treeview):
	'''Treeview with vertical scroll bar'''
	def __init__(self, parent, width, height,
		selectmode = 'browse',
		text = None,
		columns = None,
		doubleclick = None,
	):
		if text:
			show = None
		else:
			show = 'tree'
		if columns:
			column_names = list(columns.keys())
		else:
			column_names = None
		frame = ExpandedFrame(parent)
		super().__init__(frame, selectmode=selectmode, height=height, columns=column_names, show=show)
		self.column('#0', width=width)
		if text:
			self.heading('#0', text=text.upper())
		if columns:
			for col_text, col_width in columns.items():
				self.heading(col_text, text=col_text.upper())
				self.column(col_text, width=col_width)
		if doubleclick:
			self.bind('<Double-1>', doubleclick)
		self.pack(side='left', expand=True)
		vsb = Scrollbar(frame, orient='vertical', command=self.yview)
		vsb.pack(side='right', fill='y')
		self.configure(yscrollcommand=vsb.set)

class GridFrame(Frame):
	'''| Frame |'''
	def __init__(self, parent, column=0, columnspan=1, incrow=True):
		super().__init__(parent)
		self.grid(row=parent.row, column=column, columnspan=columnspan,
			padx=parent.padding, pady=parent.padding, sticky='e')
		if incrow:
			parent.row += 1

class GridButton(Button):
	'''| | Button | | |'''
	def __init__(self, parent, text, command, width=GuiConfig.BUTTON_WIDTH,
		column=1, columnspan=1, sticky='w', incrow=True, tip=None):
		super().__init__(parent, text=text, command=command, width=width)
		self.grid(row=parent.row, column=column, columnspan=columnspan, sticky=sticky,
			padx=parent.padding, pady=parent.padding)
		if incrow:
			parent.row += 1
		if tip:
			Hovertip(self, tip)

class GridSeparator:
	'''|-------|'''
	def __init__(self, parent, column=0, columnspan=255, incrow=True):
		Separator(parent).grid(row=parent.row, column=column, columnspan=columnspan,
			sticky='w', padx=parent.padding, pady=parent.padding)
		if incrow:
			parent.row += 1

class GridLabel(Label):
	'''| Label |'''
	def __init__(self, parent, text, column=0, columnspan=255, incrow=True):
		super().__init__(parent, text=text)
		self.grid(row=parent.row, column=column, columnspan=columnspan, sticky='w', padx=parent.padding)
		if incrow:
			parent.row += 1

class GridBlank:
	'''| |'''
	def __init__(self, parent, width=2, column=0, incrow=True):
		Label(parent, width=width).grid(row=parent.row, column=column, padx=parent.padding)
		if incrow:
			parent.row += 1

class GridScrolledText(ScrolledText):
	'''| ScrolledText |'''
	def __init__(self, parent, width, height,
		column = 0,
		columnspan = 255,
		ro = False,
		incrow = True
	):
		super().__init__(parent,
			font = (parent.font_family, parent.font_size),
			padx = parent.padding,
			pady = parent.padding,
			width = width,
			height = height
		)
		self.grid(row=parent.row, column=column, columnspan=columnspan,
			sticky='news', padx=parent.padding)
		if ro:
			self.bind('<Key>', lambda dummy: 'break')
			self.configure(state='disabled')
		if incrow:
			parent.row += 1

	#def echo(self, *msg, end=True, overwrite=False):

	def echo(self, *arg, end=None):
		'''Write message to info field (ScrolledText)'''
		msg = ' '.join(arg)
		self.info_text.configure(state='normal')
		if not self.info_newline:
			self.info_text.delete('end-2l', 'end-1l')
		self.info_text.insert('end', f'{msg}\n')
		self.info_text.configure(state='disabled')
		if self.info_newline:
			self.info_text.yview('end')
		self.info_newline = end != '\r'

		'''Append message in info box'''
		self.configure(state='normal')
		if overwrite:
			self.delete('end-2l', 'end')
			self.insert('end', '\n')
		self.insert('end', ' '.join(f'{string}' for string in msg) + '\n')
		self.configure(state='disabled')
		if end:
			self.yview('end')

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
		command=None, width=None, column=1, columnspan=2, incrow=True, tip=None):
		self._variable = variable
		Label(parent, text=f'{text}:').grid(sticky='e', row=parent.row, column=column, padx=parent.padding)
		super().__init__(parent, self._variable, self._variable.get(), *values, command=command)
		self.grid(sticky='w', row=parent.row, column=column+1, columnspan=columnspan-1, padx=parent.padding)
		#if command:
		#	self._variable.trace('w', command)
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
	def __init__(self, parent, variable, text, command=None, column=0, columnspan=2, incrow=True, tip=None):
		self._variable = variable
		super().__init__(parent, variable=self._variable, command=command)
		self.grid(row=parent.row, column=column)
		GridLabel(parent, text, column=column+1, columnspan=columnspan-1, incrow=incrow)
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
			button.grid(row=row, column=column, sticky='w', padx=parent.padding)
			Hovertip(button, BasicLabels.TIP_RADIO_BUTTONS)
	def set(self, value):
		self._variable.set(value=value)
	def get(self):
		return self._variable.get()

class VerticalRadiobuttons:
	'''| Rabiobutton | Radiobutton | Radiobutton | ... |'''
	def __init__(self, parent, variable, buttons, column=1, columnspan=255, incrow=True):
		frame = Frame(parent)
		frame.grid(row=parent.row, column=column, columnspan=columnspan, sticky='w', padx=parent.padding)
		self._variable = variable
		for value in buttons:
			button = Radiobutton(frame, variable=self._variable, value=value, text=value)
			button.pack(side='left', padx=(parent.padding, 0))
			Hovertip(button, BasicLabels.TIP_RADIO_BUTTONS)
		if incrow:
			parent.row += 1
	def set(self, value):
		self._variable.set(value=value)
	def get(self):
		return self._variable.get()

class StringSelector(Button):
	'''Button + Entry to select/write a string'''
	def __init__(self, parent, variable, text, command=None, default=None, width=None, show='',
		column=1, columnspan=255, incrow=True, tip=None):
		self._variable = variable
		if not command:
			command = self._command
			self.default = default
		super().__init__(parent, text=text, command=command, width=GuiConfig.BUTTON_WIDTH)
		self.grid(row=parent.row, column=column, sticky='w', padx=parent.padding)
		if not width:
			width = GuiConfig.ENTRY_WIDTH
		Entry(parent, textvariable=self._variable, show=show, width=width).grid(
			row=parent.row, column=column+1, columnspan=columnspan-1, sticky='w', padx=parent.padding)
		if incrow:
			parent.row += 1
		if tip:
			Hovertip(self, tip)
	def _command(self):
		if self._variable.get():
			return
		if self.default:
			self._variable.set(value=self.default.replace('{now}', TimeStamp.now(path_comp=True)))
	def set(self, value):
		self._variable.set(value=value)
	def get(self):
		return self._variable.get()

class FilenameSelector(StringSelector):
	'''Button + Entry to select filename/base for output filenames'''	
	def __init__(self, parent, default, variable):
		super().__init__(parent, variable, BasicLabels.FILENAME, default=default,
			tip=BasicLabels.TIP_FILENAME)

class DirSelector(Button):
	'''Button + Entry to select a directory'''
	def __init__(self, parent, variable, text, ask,
		initialdir=None,
		command=None,
		column=1,
		columnspan=255,
		incrow=True,
		tip=None,
		mustexist=False
	):
		self._variable = variable
		super().__init__(parent, text=text, command=self._select, width=GuiConfig.BUTTON_WIDTH)
		self.grid(row=parent.row, column=column, sticky='w', padx=parent.padding)
		Entry(parent, textvariable=self._variable, width=GuiConfig.ENTRY_WIDTH).grid(
			row=parent.row, column=column+1, columnspan=columnspan, sticky='w', padx=parent.padding)
		self.ask = ask
		self.command = command
		self.initialdir = initialdir
		self.mustexist = mustexist
		if incrow:
			parent.row += 1
		if tip:
			Hovertip(self, tip)
	def _select(self):
		new_dir = askdirectory(title=self.ask, initialdir=self.initialdir, mustexist=self.mustexist)
		if new_dir:
			self._variable.set(value=new_dir)
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
			tip=tip)#, missing=BasicLabels.OUTDIR_REQUIRED)

class SourceDirSelector(DirSelector):
	'''Select source directory'''
	def __init__(self, parent, variable, tip=None):
		super().__init__(parent, variable, BasicLabels.SOURCE, BasicLabels.SELECT_SOURCE,
			tip=tip)#, missing=BasicLabels.SOURCE_REQUIRED)

class FileSelector(Button):
	'''Select a file'''
	def __init__(self, parent, variable, text, ask, command=None,
		filetype=('Text files', '*.txt'), initialdir=None,
		column=1, columnspan=255, incrow=True, tip=None):
		self._variable = variable
		super().__init__(parent, text=text, command=self._select, width=GuiConfig.BUTTON_WIDTH)
		self.grid(row=parent.row, column=column, sticky='w', padx=parent.padding, pady=(parent.padding, 0))
		Entry(parent, textvariable=self._variable, width=GuiConfig.ENTRY_WIDTH).grid(
			row=parent.row, column=column+1, columnspan=columnspan-1, sticky='w', padx=parent.padding)
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
			self._variable.set(value=new_filename)
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

class ChildWindow(Toplevel):
	'''Child window to main application window'''

	def __init__(self, root, title,
		resizable = False,
		button = None,
		destroy = None
	):
		'''Open child window'''
		self.root = root
		self.font_family = root.font_family
		self.font_size = root.font_size
		self.padding = root.padding
		self.button = button
		if self.button:
			button.configure(state='disabled')
		super().__init__(self.root)
		self.title(title)
		self.resizable(resizable, resizable)
		self.iconphoto(True, self.root.appicon)
		if destroy:
			self.protocol('WM_DELETE_WINDOW', destroy)
		else:
			self.protocol('WM_DELETE_WINDOW', self.quit)
		self.root.child_win_active = True
		self.row = 0
		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)

	def set_minsize(self):
		self.update()
		self.minsize(self.winfo_width(), self.winfo_height())

	def quit(self):
		'''Destroy the child window'''
		try:
			self.root.block_child
			self.root.block_child = False
		except AttributeError:
			pass
		if self.button:
			self.button.configure(state='normal')
		super().destroy()
