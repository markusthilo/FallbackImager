#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from functools import partial
from idlelib.tooltip import Hovertip
from tkinter import Toplevel, StringVar
from tkinter.ttk import Frame, LabelFrame, Notebook, Separator, Button, Treeview
from tkinter.ttk import Label, Entry, Radiobutton, Checkbutton, OptionMenu, Scrollbar
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilename, askopenfilenames, askdirectory
from tkinter.messagebox import showerror
from .guilabeling import BasicLabels
from .timestamp import TimeStamp
from .extpath import ExtPath

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
	def __init__(self, root, parent, text, command, tip=None):
		super().__init__(parent, text=text, command=command, width=root.BUTTON_WIDTH)
		self.pack(padx=root.PAD, side='left')
		if tip:
			Hovertip(self, tip)

class RightButton(Button):
	'''|--- Button |'''
	def __init__(self, root, parent, text, command, tip=None):
		super().__init__(parent, text=text, command=command, width=root.BUTTON_WIDTH)
		self.pack(padx=root.PAD, side='right')
		if tip:
			Hovertip(self, tip)

class GridButton(Button):
	'''| | Button | | |'''
	def __init__(self, root, parent, text, command, column=1, columnspan=1, incrow=True, tip=None):
		super().__init__(parent, text=text, command=command, width=root.BUTTON_WIDTH)
		self.grid(row=root.row, column=column, columnspan=columnspan, sticky='w', padx=root.PAD)
		if incrow:
			root.row += 1
		if tip:
			Hovertip(self, tip)

class AddJobButton(GridButton):
	'''| [Add job] | | |'''
	def __init__(self, root, parent, name, command, column=0, columnspan=255):
		super().__init__(root, parent, f'{BasicLabels.ADD_JOB} {name}', command,
			column=column, columnspan=columnspan, tip=BasicLabels.TIP_ADD_JOB)

class GridSeparator:
	'''|-------|'''
	def __init__(self, root, parent, column=0, columnspan=255, incrow=True):
		Separator(parent).grid(row=root.row, column=column, columnspan=columnspan,
			sticky='w', padx=root.PAD, pady=root.PAD)
		if incrow:
			root.row += 1

class GridLabel:
	'''| Label |'''
	def __init__(self, root, parent, text, column=0, columnspan=255, incrow=True):
		Label(parent, text=text).grid(row=root.row, column=column, columnspan=columnspan,
			sticky='w', padx=root.PAD)
		if incrow:
			root.row += 1

class GridBlank:
	'''| |'''
	def __init__(self, root, parent, width=2, column=0, incrow=True):
		Label(parent, width=width).grid(row=root.row, column=column, padx=root.PAD)
		if incrow:
			root.row += 1

class GridStringMenu(OptionMenu):
	'''| | OptionMenu | | |'''
	def __init__(self, root, parent, key, text, values,
		default=None, column=1, columnspan=2, incrow=True, tip=None, section=None):
		self._variable = root.settings.init_stringvar(key, section=section, default=default)
		Label(parent, text=text, width=len(text)+1).grid(sticky='e', row=root.row, column=column, padx=(root.PAD, 0))
		super().__init__(parent, self._variable, self._variable.get(), *values)
		self.grid(sticky='w', row=root.row, column=column+1, columnspan=columnspan-1, padx=(0,root.PAD))
		if incrow:
			root.row += 1
		if tip:
			Hovertip(self, tip)
	def get(self):
		return self._variable.get()

class GridIntMenu(OptionMenu):
	'''| | OptionMenu | | |'''
	def __init__(self, root, parent, key, text, values,
		default=None, column=1, columnspan=2, incrow=True, tip=None, section=None):
		self._variable = root.settings.init_intvar(key, section=section, default=default)
		Label(parent, text=f'{text}	').grid(sticky='e', row=root.row, column=column)
		super().__init__(parent, self._variable, self._variable.get(), *values)
		self.grid(sticky='w', row=root.row, column=column+1, columnspan=columnspan-1)
		if incrow:
			root.row += 1
		if tip:
			Hovertip(self, tip)
	def get(self):
		return self._variable.get()

class Checker(Checkbutton):
	'''Checkbox'''
	def __init__(self, root, parent, key, text, default=False, column=0, columnspan=2, tip=None, section=None):
		self._variable = root.settings.init_boolvar(key, section=section, default=default)
		super().__init__(parent, variable=self._variable)
		self.grid(row=root.row, column=column)
		GridLabel(root, parent, text, column=column+1, columnspan=columnspan-1)
		if tip:
			Hovertip(self, tip)
	def get(self):
		return self._variable.get()

class StringRadiobuttons:
	'''| Rabiobutton | | | |'''
	def __init__(self, root, parent, key, buttons, default, column=0, section=None):
		self._variable = root.settings.init_stringvar(key, section=section, default=default)
		for row, value in enumerate(buttons, root.row):
			button = Radiobutton(parent, variable=self._variable, value=value)
			button.grid(row=row, column=column, sticky='w', padx=root.PAD)
			Hovertip(button, BasicLabels.TIP_RADIO_BUTTONS)
	def get():
		return self._variable.get()

class VerticalRadiobuttons:
	'''| Rabiobutton | Radiobutton | Radiobutton | ... |'''
	def __init__(self, root, parent, key, buttons, default, column=1, columnspan=255, incrow=True, section=None):
		frame = Frame(parent)
		frame.grid(row=root.row, column=column, columnspan=columnspan, sticky='w', padx=root.PAD)
		self._variable = root.settings.init_stringvar(key, section=section, default=default)
		for value in buttons:
			button = Radiobutton(frame, variable=self._variable, value=value, text=value)
			button.pack(side='left', padx=(root.PAD, 0))
			Hovertip(button, BasicLabels.TIP_RADIO_BUTTONS)
		if incrow:
			root.row += 1
	def get():
		return self._variable.get()

class StringSelector(Button):
	'''Button + Entry to select/write a string'''
	def __init__(self, root, parent, key, text, command=None, default=None, width=None,
		column=1, columnspan=255, incrow=True, tip=None, missing=None, section=None):
		self._variable = root.settings.init_stringvar(key, section=section, default=default)
		if not command:
			command = self._command
			self.default = default
		super().__init__(parent, text=text, command=command, width=root.BUTTON_WIDTH)
		self.grid(row=root.row, column=column, sticky='w', padx=root.PAD)
		if not width:
			width = root.ENTRY_WIDTH
		Entry(parent, textvariable=self._variable, width=width).grid(
			row=root.row, column=column+1, columnspan=columnspan-1, sticky='w', padx=root.PAD)
		if incrow:
			root.row += 1
		if tip:
			Hovertip(self, tip)
	def _command(self):
		if self._variable.get():
			return
		if self.default:
			self._variable.set(self.default)
	def get():
		string = self._variable.get()
		if string:
			return string
		if self.missing:
			showerror(title=BasicLabels.MISSING_ENTRY, message=self.missing)

class FilenameSelector(StringSelector):
	'''Button + Entry to select filename/base for output filenames'''	
	def __init__(self, root, parent, default):
		super().__init__(root, parent, 'filename', BasicLabels.FILENAME, command=self._command,
			tip=BasicLabels.TIP_FILENAME)
		self.default = default
	def _command(self):
		if self._variable.get():
			return
		self._variable.set(self.default.replace('{now}', TimeStamp.now(path_comp=True)))

class DirSelector(Button):
	'''Button + Entry to select a directory'''
	def __init__(self, root, parent, key, ask,
		default=None, command=None, column=1, columnspan=255, incrow=True, tip=None, missing=None, section=None):
		self._variable = root.settings.init_stringvar(key, section=section, default=default)
		super().__init__(parent, text=BasicLabels.DIRECTORY, command=self._select, width=root.BUTTON_WIDTH)
		self.grid(row=root.row, column=column, sticky='w', padx=root.PAD)
		Entry(parent, textvariable=self._variable, width=root.ENTRY_WIDTH).grid(
			row=root.row, column=column+1, columnspan=columnspan, sticky='w', padx=root.PAD)
		self.ask = ask
		self.command = command
		self.missing = missing
		if incrow:
			root.row += 1
		if tip:
			Hovertip(self, tip)
	def _select(self):
		new_dir = askdirectory(title=self.ask, mustexist=False)
		if new_dir:
			self._variable.set(new_dir)
		if self.command:
			self.command()
	def get():
		directory = self._variable.get()
		if directory:
			return directory
		if self.missing:
			showerror(title=BasicLabels.MISSING_ENTRY, message=self.missing)

class OutDirSelector(DirSelector):
	'''Select destination/output directory'''
	def __init__(self, root, parent, tip=None):
		if not tip:
			tip = BasicLabels.TIP_OUTDIR
		super().__init__(root, parent, 'outdir', BasicLabels.SELECT_OUTDIR,
			tip=tip, missing=BasicLabels.OUTDIR_REQUIRED)

class SourceDirSelector(DirSelector):
	'''Select source directory'''
	def __init__(self, root, parent, tip=None):
		if not tip:
			tip = BasicLabels.TIP_SOURCE
		super().__init__(root, parent, 'source', BasicLabels.SELECT_SOURCE,
			tip=tip, missing=BasicLabels.SOURCE_REQUIRED)

class FileSelector(Button):
	'''Select a file'''
	def __init__(self, root, parent, key, text, ask, command=None,
		filetype=('Text files', '*.txt'), default=None, initialdir=None,
		column=1, columnspan=255, incrow=True, tip=None, missing=None, section=None):
		self._variable = root.settings.init_stringvar(key, section=section, default=default)
		super().__init__(parent, text=text, command=self._select, width=root.BUTTON_WIDTH)
		self.grid(row=root.row, column=column, sticky='w', padx=root.PAD, pady=(root.PAD, 0))
		Entry(parent, textvariable=self._variable, width=root.ENTRY_WIDTH).grid(
			row=root.row, column=column+1, columnspan=columnspan-1, sticky='w', padx=root.PAD)
		self.ask = ask
		self.filetype = filetype
		self.initialdir = initialdir
		self.command = command
		if incrow:
			root.row += 1
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
	def get():
		filename = self._variable.get()
		if filename:
			return filename
		if self.missing:
			showerror(title=BasicLabels.MISSING_ENTRY, message=self.missing)

class Tree(Treeview):
	'''Treeview with vertical scroll bar'''
	def __init__(self, root, parent, selectmode='browse', width=None, height=None):
		if not width:
			width = root.TREE_WIDTH
		if not height:
			height = root.TREE_HEIGHT
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
		super().__init__(root)
		self.title(title)
		self.resizable(0, 0)
		self.iconphoto(True, root.appicon)
		self.protocol('WM_DELETE_WINDOW', self.destroy)
		root.child_win_active = True
		self.root = root

	def destroy(self):
		'''Destroy the child window'''
		self.root.child_win_active = False
		super().destroy()

class SelectTsvColumn(ChildWindow):
	'''Window to select column of a TSV file'''

	def __init__(self, root, cmd, file='tsv_file', column='tsv_column', no_head = 'tsv_no_head'):
		'''Open child window for module=cmd'''
		if root.child_win_active:
			return
		self.root = root
		self.cmd = cmd
		self.file_key = file
		self.column_key = column
		self.no_head_key = no_head
		self.root.settings.section = self.cmd
		tsv = self.root.settings.get(self.file_key)
		if tsv:
			encoding, head = ExtPath.read_utf_head(Path(tsv), lines_out=self.root.MAX_ROW_QUANT)
			try:
				columns = len(head[0].split('\t'))
			except IndexError:
				columns = 1
			if columns == 1:
				self.root.settings.raw(self.column_key).set('1')
				return
			if len(head) < 2:
				tsv = None
		if not tsv:
			showerror(
				title = BasicLabels.MISSING_ENTRY,
				message = BasicLabels.FIRST_CHOOSE_TSV
			)
			return
		super().__init__(self.root, BasicLabels.SELECT_COLUMN)
		self._selected_column = StringVar()
		frame = ExpandedFrame(self.root, self)
		preview = {(row, column): entry
			for row, line in enumerate(head)
			for column, entry in enumerate(line.split('\t'))
		}
		entry_heights = [0]*self.root.MAX_ROW_QUANT
		for row in range(self.root.MAX_ROW_QUANT):
			for column in range(self.root.MAX_COLUMN_QUANT):
				try:
					entry_heights[row] = max(
						entry_heights[row],
						min(int(len(preview[row, column])/self.root.MAX_ENTRY_WIDTH)+1,
							self.root.MAX_ENTRY_HEIGHT)
					)
				except KeyError:
					break
		entry_widths = [self.root.MIN_ENTRY_WIDTH]*self.root.MAX_COLUMN_QUANT
		for column in range(self.root.MAX_COLUMN_QUANT):
			for row in range(self.root.MAX_ROW_QUANT):
				try:
					entry_widths[column] = max(
						entry_widths[column],
						min(len(preview[row, column]), self.root.MAX_ENTRY_WIDTH)
					)
				except KeyError:
					break
		for row, height in enumerate(entry_heights):
			for column, width in enumerate(entry_widths):
				try:
					entry = preview[row, column]
				except KeyError:
					break
				text = ScrolledText(frame, width=width, height=height)
				text.grid(row=row, column=column)
				text.bind('<Key>', lambda dummy: 'break')
				text.insert('end', preview[row, column])
				text.configure(state='disabled')
		if columns > self.root.MAX_COLUMN_QUANT:
			columns = self.root.MAX_COLUMN_QUANT
		row += 1
		for column in range(columns):
			Button(frame,
				text = f'{column+1}',
				command = partial(self._get_column, column+1)
			).grid(row=row, column=column, padx=self.root.PAD, pady=self.root.PAD)
		frame = ExpandedFrame(self.root, self)
		Checkbutton(frame,
			text = self.root.TSV_NO_HEAD,
			variable = self.root.settings.raw(self.no_head_key)
		).pack(side='left', padx=self.root.PAD)
		RightButton(self.root, frame, BasicLabels.QUIT, self.destroy)

	def _get_column(self, column):
		'''Get the selected column'''
		self.root.settings.section = self.cmd
		self.root.settings.raw(self.column_key).set(f'{column}')
		self.destroy()

class BasicTab:
	'''Basic notebook tab'''

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		SourceDirSelector(root, frame)
		GridLabel(root, frame, root.DESTINATION, columnspan=2)
		FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
		DirSelector(root, frame, root.OUTDIR, root.DIRECTORY, root.SELECT_DEST_DIR)
		GridSeparator(root, frame)
		GridBlank(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job,
			column=0, columnspan=3)
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
