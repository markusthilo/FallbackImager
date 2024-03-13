#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from functools import partial
from tkinter.messagebox import showerror
from tkinter import Button, Label
from tkinter.ttk import Frame, Treeview
from lib.guielements import SourceDirSelector, Checker, LeftLabel
from lib.guielements import ChildWindow, SelectTsvColumn, GridBlank, ScrollFrame
from lib.guielements import ExpandedFrame, GridSeparator, GridLabel, DirSelector
from lib.guielements import FilenameSelector, StringSelector, StringRadiobuttons
from lib.guielements import FileSelector, GridButton, LeftButton, RightButton
from lib.mfdbreader import MfdbReader

class AxCheckerGui:
	'''Notebook page for AxChecker'''

	CMD = 'AxChecker'

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		GridSeparator(root, frame)
		GridLabel(root, frame, root.AXIOM, columnspan=3)
		FileSelector(root, frame, root.CASE_FILE, root.CASE_FILE,
			f'{root.OPEN_CASE_FILE} ({root.AXIOM_CASE_FILE})',
			filetype=(root.CASE_FILE, root.AXIOM_CASE_FILE))
		StringSelector(root, frame, root.ROOT, root.ROOT,
			command=self._select_root)	
		GridSeparator(root, frame)
		GridLabel(root, frame, root.DESTINATION, columnspan=2)
		self.filename_str = FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
		DirSelector(root, frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		GridSeparator(root, frame)
		GridLabel(root, frame, root.VERIFY_FILE, columnspan=2)
		StringRadiobuttons(root, frame, root.VERIFY_FILE,
			(root.DO_NOT_COMPARE, root.FILE_STRUCTURE, root.TSV), root.DO_NOT_COMPARE)
		GridLabel(root, frame, root.DO_NOT_COMPARE, column=1, columnspan=2)
		DirSelector(root, frame, root.FILE_STRUCTURE, root.FILE_STRUCTURE, root.SELECT_FILE_STRUCTURE,
			command=self._select_file_structure)
		FileSelector(root, frame, root.TSV, root.TSV, root.SELECT_TSV,
			filetype=('CSV', '*.csv'), command=self._select_tsv_file)
		StringSelector(root, frame, root.COLUMN, root.COLUMN, command=self._select_column)
		Checker(root, frame, root.TSV_NO_HEAD, root.TSV_NO_HEAD, column=1)
		GridSeparator(root, frame)
		GridBlank(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}',
			self._add_job, column=0, columnspan=3)
		root.child_win_active = False
		self.root = root

	def _select_root(self):
		'''Select partition in the AXIOM case'''
		if self.root.child_win_active:
			return
		self.root.settings.section = self.CMD
		mfdb = self.root.settings.get(self.root.CASE_FILE)
		if not mfdb:
			showerror(
				title = self.root.CASE_FILE,
				message = self.root.FIRST_CHOOSE_CASE
			)
			return
		mfdbreader = MfdbReader(mfdb)
		self.source_ids = list()
		self.source_paths = list()
		self.source_types = list()
		for source_id, source_type, source_path in mfdbreader.read_roots(max_depth=2):
			self.source_ids.append(source_id)
			self.source_paths.append(source_path)
			self.source_types.append(source_type)
		if not self.source_ids:
			showerror(
				title = self.root.CASE_FILE,
				message = self.root.UNABLE_DETECT_PATHS
			)
			return
		self.child_window = ChildWindow(self.root, self.root.SELECT_PARTITION)
		self.child_window.geometry(f'{self.root.STD_PIXEL_WIDTH}x{self.root.STD_PIXEL_HEIGHT}')
		self.child_window.resizable(True, True)
		frame = ScrollFrame(self.root, self.child_window)
		#Label(frame, bg='#ff0000').pack(fill='both', expand=True)
		#treeview = Treeview(frame)
		for row, path in enumerate(self.source_paths):
		#	treeview.insert("", 'end', text=f'{path}')
			Button(frame, text=f'{path}', bd=0, command=partial(self._get_root, row)).grid(sticky='w', row=row, column=0)
			Label(frame, text=':').grid(row=row, column=1)
			Button(frame, text=f'{self.source_types[row]}', bd=0, command=partial(self._get_root, row)).grid(sticky='w', row=row, column=2)
		#treeview.pack(fill='both', expand=True)
		frame = Frame(self.child_window)
		frame.pack(fill='x', padx=self.root.PAD, pady=self.root.PAD, expand=True)


		#frame = ExpandedFrame(self.root, self.child_window)
		#LeftButton(self.root, frame, self.root.SELECT, self._get_partition)
		RightButton(self.root, frame, self.root.QUIT, self.child_window.destroy)

	def _get_root(self, row):
		'''Get the selected root'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.ROOT).set(self.source_ids[row])
		self.child_window.destroy()

	def _select_file_structure(self):
		'''Select file structure to compare'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.VERIFY_FILE).set(self.root.FILE_STRUCTURE)

	def _select_tsv_file(self):
		'''Select TSV file to compare'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.VERIFY_FILE).set(self.root.TSV)

	def _select_column(self):
		'''Select column in TSV file to compare'''
		SelectTsvColumn(self.root, self.CMD)

	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		mfdb = self.root.settings.get(self.root.CASE_FILE)
		partition = self.root.settings.get(self.root.PARTITION)
		if not mfdb:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.CASE_REQUIRED
			)
			return
		outdir = self.root.settings.get(self.root.OUTDIR) 
		filename = self.root.settings.get(self.root.FILENAME)
		if not outdir:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.DEST_DIR_REQUIRED
			)
			return
		if not filename:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.DEST_FN_REQUIRED
			)
			return
		verify = self.root.settings.get(self.root.VERIFY_FILE)
		if not partition and verify != self.root.DO_NOT_COMPARE:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.PARTITION_REQUIRED
			)
			return
		file_structure = self.root.settings.get(self.root.FILE_STRUCTURE)
		tsv = self.root.settings.get(self.root.TSV)
		column = self.root.settings.get(self.root.COLUMN)
		cmd = self.root.settings.section.lower()
		cmd += f' --partition "{partition}"'
		cmd += f' --{self.root.OUTDIR.lower()} "{outdir}"'
		cmd += f' --{self.root.FILENAME.lower()} "{filename}"'
		if verify == self.root.FILE_STRUCTURE:
			if not file_structure:
				showerror(
					title = self.root.MISSING_ENTRIES,
					message = self.root.ROOT_DIR_REQUIRED
				)
				return
			cmd += f' --diff "{file_structure}"'
		elif verify == self.root.TSV:
			if not tsv or not column:
				showerror(
					title = self.root.MISSING_ENTRIES,
					message = self.root.TSV_AND_COL_REQUIRED
					)
				return
			cmd += f' --diff "{tsv}" --column {column}'
			if self.root.settings.get(self.root.TSV_NO_HEAD) == '1':
				cmd += ' --nohead'
		cmd += f' "{mfdb}"'
		self.root.append_job(cmd)