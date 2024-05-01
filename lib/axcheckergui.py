#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter.messagebox import showerror
from .guilabeling import AxCheckerLabels
from .guielements import ChildWindow, SelectTsvColumn, GridBlank, Checker, Tree
from .guielements import ExpandedFrame, GridSeparator, GridLabel, DirSelector
from .guielements import FilenameSelector, StringSelector, StringRadiobuttons
from .guielements import FileSelector, GridButton, LeftButton, RightButton, AddJobButton
from .mfdbreader import MfdbReader

class AxCheckerGui(AxCheckerLabels):
	'''Notebook page for AxChecker'''

	CMD = 'AxChecker'

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		GridSeparator(root, frame)
		GridLabel(root, frame, 'AXIOM')
		FileSelector(
			root,
			frame,
			'case_file',
			self.CASE_FILE,
			f'{self.OPEN_CASE_FILE} (Case.mfdb)',
			filetype = ('Case.mfdb', 'Case.mfdb'),
			tip = self.TIP_CASE_FILE
		)
		StringSelector(root, frame, 'root_id', self.ROOT,
			command=self._select_root, tip=self.TIP_ROOT)	
		GridSeparator(root, frame)
		GridLabel(root, frame, root.DESTINATION)
		DirSelector(root, frame, 'outdir', self.DIRECTORY,
			root.SELECT_DEST_DIR, tip=self.TIP_DIRECTORY)
		self.filename_str = FilenameSelector(root, frame, 'filename',
			self.FILENAME, tip=self.TIP_FILENAME)
		GridSeparator(root, frame)
		GridLabel(root, frame, self.TASK)
		StringRadiobuttons(root, frame, 'task', ('check', 'compare_dir', 'compare_tsv'), 'check')
		GridLabel(root, frame, self.CHECK, column=1)
		DirSelector(root, frame, 'comp_dir', self.DIRECTORY, self.SELECT_COMP_DIR,
			command=self._select_file_structure, tip=self.TIP_COMP_DIR)
		FileSelector(root, frame, 'tsv_file', self.TSV_FILE, self.SELECT_FILE,
			filetype=('Text/TSV', '*.txt'), command=self._select_tsv_file, tip=self.TIP_COMP_TSV)
		StringSelector(root, frame, 'tsv_column', self.COLUMN, command=self._select_column,
			tip=self.TIP_TSV_COLUMN)
		Checker(root, frame, 'tsv_no_head', self.TSV_NO_HEAD, columnspan=3, tip=self.TIP_TSV_NO_HEAD)
		GridSeparator(root, frame)
		GridBlank(root, frame)
		AddJobButton(root, frame, self.CMD, self._add_job)
		root.child_win_active = False
		self.root = root

	def _select_root(self):
		'''Select root to compare in the AXIOM case'''
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
		self.child_window = ChildWindow(self.root, self.root.SELECT_ROOT)
		self.child_window.resizable(0, 0)
		frame = ExpandedFrame(self.root, self.child_window)
		self.tree = Tree(self.root, frame)
		entries = dict()
		for source_id, parent_id, source_type, friendly_value in MfdbReader(mfdb).tree():
			if parent_id:
				try:
					parent = entries[parent_id]
				except KeyError:
					continue
				entries[source_id] = self.tree.insert(parent, 'end', text=friendly_value, iid=source_id)
			else:
				entries[source_id] = self.tree.insert('', 'end', text=friendly_value, iid=source_id)
			if source_type == 'Partition':
				self.tree.see(source_id)
		frame = ExpandedFrame(self.root, self.child_window)
		LeftButton(self.root, frame, self.root.SELECT, self._get_root)
		RightButton(self.root, frame, self.root.QUIT, self.child_window.destroy)

	def _get_root(self):
		'''Get the selected root'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.ROOT).set(self.tree.focus())
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
		root_id = self.root.settings.get(self.root.ROOT)
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
		try:
			int(root_id)
		except ValueError:
			root_id = None
		if verify != self.root.DO_NOT_COMPARE and not root_id:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.ID_REQUIRED
			)
			return
		file_structure = self.root.settings.get(self.root.FILE_STRUCTURE)
		tsv = self.root.settings.get(self.root.TSV)
		column = self.root.settings.get(self.root.COLUMN)
		cmd = self.root.settings.section.lower()
		cmd += f' --root {root_id}'
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