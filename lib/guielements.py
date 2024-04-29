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
	def __init__(self, root, parent, text, command):
		super().__init__(parent, text=text, command=command, width=root.BUTTON_WIDTH)
		self.pack(padx=root.PAD, side='left')

class RightButton(Button):
	'''|--- Button |'''
	def __init__(self, root, parent, text, command):
		super().__init__(parent, text=text, command=command, width=root.BUTTON_WIDTH)
		self.pack(padx=root.PAD, side='right')

class GridButton(Button):
	'''| | Button | | |'''
	def __init__(self, root, parent, text, command, column=1, columnspan=1, incrow=True):
		super().__init__(parent, text=text, command=command, width=root.BUTTON_WIDTH)
		self.grid(row=root.row, column=column, columnspan=columnspan, sticky='w', padx=root.PAD)
		if incrow:
			root.row += 1

class GridSeparator:
	'''|-------|'''
	def __init__(self, root, parent, column=0, columnspan=255, incrow=True):
		Separator(parent).grid(row=root.row, column=column, columnspan=columnspan,
			sticky='w', padx=root.PAD, pady=root.PAD)
		if incrow:
			root.row += 1

class GridIntMenu(OptionMenu):
	'''| | OptionMenu | | |'''
	def __init__(self, root, parent, key, text, values,
		default=None, column=1, columnspan=2, incrow=True):
		self.variable = root.settings.init_intvar(key, default=default)
		Label(parent, text=f'{text}	').grid(sticky='e', row=root.row, column=column)
		super().__init__(parent, self.variable, self.variable.get(), *values)
		self.grid(sticky='w', row=root.row, column=column+1, columnspan=columnspan-1)
		if incrow:
			root.row += 1

class GridStringMenu(OptionMenu):
	'''| | OptionMenu | | |'''
	def __init__(self, root, parent, key, text, values,
		default=None, column=1, columnspan=2, incrow=True):
		self.variable = root.settings.init_stringvar(key, default=default)
		Label(parent, text=text, width=len(text)+1).grid(sticky='e', row=root.row, column=column, padx=(root.PAD, 0))
		super().__init__(parent, self.variable, self.variable.get(), *values)
		self.grid(sticky='w', row=root.row, column=column+1, columnspan=columnspan-1, padx=(0,root.PAD))
		if incrow:
			root.row += 1

class Checker(Checkbutton):
	'''Checkbox'''
	def __init__(self, root, parent, key, text, column=0, columnspan=2):
		self.bool_var = root.settings.init_boolvar(key)
		super().__init__(parent, variable=self.bool_var)
		self.grid(row=root.row, column=column)
		GridLabel(root, parent, text, column=column+1, columnspan=columnspan-1)

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

class StringField(Button):
	'''Button + Entry to enter string'''
	def __init__(self, root, parent, key, text, command, column=1, columnspan=255, incrow=True):
		self.string = root.settings.init_stringvar(key)
		super().__init__(parent, text=text, command=command, width=root.BUTTON_WIDTH)
		self.grid(row=root.row, column=column, sticky='e', padx=root.PAD)
		Entry(parent, textvariable=self.string, width=root.ENTRY_WIDTH).grid(
			row=root.row, column=column+1, columnspan=columnspan-1, sticky='w', padx=root.PAD)
		if incrow:
			root.row += 1

class StringRadiobuttons:
	'''| Rabiobutton | | | |'''
	def __init__(self, root, parent, key, buttons, default, column=0):
		self.variable = root.settings.init_stringvar(key, default=default)
		for row, value in enumerate(buttons, root.row):
			Radiobutton(parent, variable=self.variable, value=value).grid(
				row=row, column=column, sticky='w', padx=root.PAD)

class StringRadiobuttonsFrame:
	'''| Rabiobutton | Radiobutton | Radiobutton | ... |'''
	def __init__(self, root, parent, key, buttons, default, column=1, columnspan=255, incrow=True):
		frame = Frame(parent)
		frame.grid(row=root.row, column=column, columnspan=columnspan, sticky='w', padx=root.PAD)
		self.variable = root.settings.init_stringvar(key, default=default)
		for value in buttons:
			Radiobutton(frame, variable=self.variable, value=value).pack(
				side='left', padx=(root.PAD, 0))
			Label(frame, text=value).pack(side='left', padx=(0, 4*root.PAD))
		if incrow:
			root.row += 1

class VerticalButtons:
	'''---|Radiobutton|Radiobutton|Radiobutton|---'''
	def __init__(self, root, parent, key, buttons, default, column=1, columnspan=255, incrow=True):
		Label(parent, text=key).grid(row=root.row, column=column, columnspan=columnspan)
		frame = Frame(parent)
		frame.grid(row=root.row, column=column, columnspan=columnspan, sticky='w', padx=root.PAD)
		self.variable = root.settings.init_stringvar(key, default=default)
		for button in buttons:
			Radiobutton(frame, variable=self.variable, value=button, text=button).pack(
				side='right', padx=root.PAD)
		if incrow:
			root.row += 1

class SourceDirSelector(Button):
	'''Select source'''
	def __init__(self, root, parent, column=0, columnspan=255):
		self.source_str = root.settings.init_stringvar(root.SOURCE)
		GridSeparator(root, parent)
		GridLabel(root, parent, root.SOURCE, columnspan=columnspan+2)
		super().__init__(parent, text=root.DIRECTORY, command=self._select, width=root.BUTTON_WIDTH)
		self.grid(row=root.row, column=column+1, sticky='w', padx=root.PAD)
		Entry(parent, textvariable=self.source_str, width=root.ENTRY_WIDTH).grid(
			row=root.row, column=column+2, columnspan=columnspan, sticky='w', padx=root.PAD)
		root.row += 1
		GridSeparator(root, parent)
		self.root = root
	def _select(self):
		new_dir = askdirectory(title=self.root.ASK_SOURCE)
		if new_dir:
			self.source_str.set(new_dir)

class StringSelector(Button):
	'''String for names, descriptions etc.'''
	def __init__(self, root, parent, key, text, command=None,
		column=1, columnspan=255, width=None, default=None, incrow=True):
		self.string = root.settings.init_stringvar(key, default=default)
		if not command:
			command = self._command
		super().__init__(parent, text=text, command=command, width=root.BUTTON_WIDTH)
		self.grid(row=root.row, column=column, sticky='w', padx=root.PAD)
		if not width:
			width = root.ENTRY_WIDTH
		Entry(parent, textvariable=self.string, width=width).grid(
			row=root.row, column=column+1, columnspan=columnspan-1, sticky='w', padx=root.PAD)
		if incrow:
			root.row += 1
		self.default = default
	def _command(self):
		if self.string.get():
			return
		if self.default:
			self.string.set(self.default)

class FileSelector(Button):
	'''Button to select file to read'''
	def __init__(self, root, parent, key, text, ask, command=None,
		filetype=('Text files', '*.txt'), default=None, initialdir=None,
		column=1, columnspan=255, tip=None):
		self.file_str = root.settings.init_stringvar(key)
		if default:
			self.file_str.set(default)
		super().__init__(parent, text=text, command=self._select, width=root.BUTTON_WIDTH)
		self.grid(row=root.row, column=column, sticky='w', padx=root.PAD, pady=(root.PAD, 0))
		Entry(parent, textvariable=self.file_str, width=root.ENTRY_WIDTH).grid(
			row=root.row, column=column+1, columnspan=columnspan-1, sticky='w', padx=root.PAD)
		root.row += 1
		self.root = root
		self.ask = ask
		self.filetype = filetype
		self.initialdir = initialdir
		self.command = command
		if tip:
			Hovertip(self, tip)
	def _select(self):
		new_filename = askopenfilename(
			title = self.ask,
			filetypes = (self.filetype, ('All files', '*.*')),
			initialdir = self.initialdir
		)
		if new_filename:
			self.file_str.set(new_filename)
		if self.command:
			self.command()

class FilesSelector(ScrolledText):
	'''ScrolledText to select files'''
	def __init__(self, root, parent, key, text, ask, command=None, width=None, height=None,
		filetypes=(('All files', '*.*'),), column=1, columnspan=255):
		if not width:
			width = root.FILES_FIELD_WIDTH
		if not height:
			height = root.INFO_HEIGHT
		self.button = Button(parent, text=text, command=self._select)
		self.button.grid(row=root.row, column=column, sticky='nw', padx=root.PAD, pady=root.PAD)
		super().__init__(parent,
			padx = root.PAD,
			pady = root.PAD,
			width = width,
			height = height
		)
		self.grid(row=root.row, column=column+1, columnspan=columnspan,
			sticky='nw', padx=root.PAD, pady=root.PAD)
		root.row += 1
		self.root = root
		self.ask = ask
		self.filetypes = filetypes
		self.command = command
	def _select(self):
		new_filenames = askopenfilenames(title=self.ask, filetypes=self.filetypes)
		if new_filenames:
			self.delete('1.0', 'end')
			self.insert('end', '\n'.join(new_filenames))
		if self.command:
			self.command()

class FilenameSelector(Button):
	'''Button + Entry to enter string'''	
	def __init__(self, root, parent, key, text, default=None, command=None, column=1, columnspan=255):
		self.string = root.settings.init_stringvar(key)
		self.default = default
		if not command:
			command = self._command
		super().__init__(parent, text=text, command=command, width=root.BUTTON_WIDTH) 
		self.grid(row=root.row, column=column, sticky='w', padx=root.PAD)
		Entry(parent, textvariable=self.string, width=root.ENTRY_WIDTH).grid(
			row=root.row, column=column+1, columnspan=columnspan, sticky='w', padx=root.PAD)
		root.row += 1
		self.command = command
	def _command(self):
		if self.string.get():
			return
		if self.default:
			self.string.set(self.default)
		else:
			self.string.set(TimeStamp.now(path_comp=True))
		if self.command:
			self.command()

class DirSelector(Button):
	'''Button + Entry to select directory'''
	def __init__(self, root, parent, key, text, ask, command=None, column=1, columnspan=255):
		self.dir_str = root.settings.init_stringvar(key)
		super().__init__(parent, text=text, command=self._select, width=root.BUTTON_WIDTH)
		self.grid(row=root.row, column=column, sticky='w', padx=root.PAD)
		Entry(parent, textvariable=self.dir_str, width=root.ENTRY_WIDTH).grid(
			row=root.row, column=column+1, columnspan=columnspan, sticky='w', padx=root.PAD)
		root.row += 1
		self.root = root
		self.ask = ask
		self.command = command
	def _select(self):
		new_dir = askdirectory(title=self.ask, mustexist=False)
		if new_dir:
			self.dir_str.set(new_dir)
		if self.command:
			self.command()

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

	def __init__(self, root, cmd):
		'''Open child window'''
		if root.child_win_active:
			return
		self.root = root
		self.cmd = cmd
		self.root.settings.section = self.cmd
		tsv = self.root.settings.get(self.root.TSV)
		if tsv:
			encoding, head = ExtPath.read_utf_head(Path(tsv), after=self.root.MAX_ROW_QUANT)
			try:
				columns = len(head[0].split('\t'))
			except IndexError:
				columns = 1
			if columns == 1:
				self.root.settings.raw(self.root.COLUMN).set('1')
				return
			if len(head) < 2:
				tsv = None
		if not tsv:
			showerror(
				title = self.root.TSV,
				message = self.root.FIRST_CHOOSE_TSV
			)
			return
		super().__init__(self.root, self.root.SELECT_COLUMN)
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
			variable = self.root.settings.raw(self.root.TSV_NO_HEAD)
		).pack(side='left', padx=self.root.PAD)
		RightButton(self.root, frame, self.root.QUIT, self.destroy)

	def _get_column(self, column):
		'''Get the selected column'''
		self.root.settings.section = self.cmd
		self.root.settings.raw(self.root.COLUMN).set(f'{column}')
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
