#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter.messagebox import showerror
from .guilabeling import AxCheckerLabels
from .guielements import ChildWindow, GridBlank, Checker, Tree
from .guielements import ExpandedFrame, GridSeparator, GridLabel
from .guielements import DirSelector, OutDirSelector, SelectTsvColumn
from .guielements import FilenameSelector, StringSelector, StringRadiobuttons
from .guielements import FileSelector, GridButton, LeftButton, RightButton, AddJobButton
from .mfdbreader import MfdbReader

class AxCheckerGui(AxCheckerLabels):
	'''Notebook page for AxChecker'''

	MODULE = 'AxChecker'

	def __init__(self, root):
		'''Notebook page'''
		self.root = root
		self.root.settings.this_section = self.MODULE
		frame = ExpandedFrame(self.root.notebook)
		self.root.notebook.add(frame, text=f' {self.MODULE} ')
		frame.row = 0
		GridSeparator(frame)
		GridLabel(frame, 'AXIOM')
		self.case_file = FileSelector(
			frame,
			self.root.settings.init_stringvar('CaseFile'),
			self.CASE_FILE,
			f'{self.OPEN_CASE_FILE} (Case.mfdb)',
			filetype = ('Case.mfdb', 'Case.mfdb'),
			tip = self.TIP_CASE_FILE,
			missing = self.FIRST_CHOOSE_CASE
		)
		self.root_id = StringSelector(
			frame,
			self.root.settings.init_stringvar('RootID'),
			self.ROOT,
			command=self._select_root,
			tip=self.TIP_ROOT
		)	
		GridSeparator(frame)
		GridLabel(frame, self.DESTINATION)
		self.outdir = OutDirSelector(frame, self.root.settings.init_stringvar('OutDir'))
		self.filename = FilenameSelector(frame, '{now}_' + self.MODULE.lower(),
			self.root.settings.init_stringvar('Filename'))
		GridSeparator(frame)
		GridLabel(frame, self.TASK)
		self.task = StringRadiobuttons(
			frame,
			self.root.settings.init_stringvar('Task'),
			('Check', 'CompareDir', 'CompareTSV'),
			'Check'
		)
		GridLabel(frame, self.CHECK, column=1)
		self.root_dir = DirSelector(
			frame,
			self.root.settings.init_stringvar('RootDir'),
			self.SELECT_COMP_DIR,
			command = self._select_file_structure,
			tip  =self.TIP_COMP_DIR
		)
		self.tsv_file = FileSelector(
			frame,
			self.root.settings.init_stringvar('File'),
			self.TSV_FILE,
			self.SELECT_FILE,
			filetype = ('Text/TSV', '*.txt'),
			command = self._select_tsv_file,
			tip = self.TIP_COMP_TSV
		)
		self.tsv_column = StringSelector(
			frame,
			self.root.settings.init_stringvar('Column'),
			self.COLUMN,
			command = self._select_column,
			tip = self.TIP_TSV_COLUMN
		)
		self.tsv_no_head = Checker(
			frame,
			self.root.settings.init_stringvar('NoHead'),
			self.TSV_NO_HEAD,
			columnspan = 3,
			tip = self.TIP_TSV_NO_HEAD
		)
		GridSeparator(frame)
		GridBlank(frame)
		AddJobButton(frame, self.MODULE, self._add_job)
		self.child_win_active = False

	def _select_root(self):
		'''Select root to compare in the AXIOM case'''
		if self.child_win_active:
			return
		mfdb = self.case_file.get()
		if not mfdb:
			showerror(
				title = self.CASE_FILE,
				message = self.FIRST_CHOOSE_CASE
			)
			return
		self.child_window = ChildWindow(self.root, self.SELECT_ROOT)
		self.child_window.resizable(0, 0)
		frame = ExpandedFrame(self.child_window)
		self.tree = Tree(frame)
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
		frame = ExpandedFrame(self.child_window)
		LeftButton(frame, self.SELECT, self._get_root)
		RightButton(frame, self.QUIT, self.child_window.destroy)

	def _get_root(self):
		'''Get the selected root'''
		self.root_id.set(self.tree.focus())
		self.child_window.destroy()

	def _select_file_structure(self):
		'''Select file structure to compare'''
		self.root.settings.section = self.CMD
		self.root.settings.raw('task').set('compare_dir')

	def _select_tsv_file(self):
		'''Select TSV file to compare'''
		self.root.settings.section = self.CMD
		self.root.settings.raw('task').set('compare_tsv')

	def _select_column(self):
		'''Select column in TSV file to compare'''
		SelectTsvColumn(self.root, self.CMD)

	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		mfdb = self.root.settings.get('case_file')
		if not mfdb:
			showerror(
				title = self.MISSING_ENTRY,
				message = self.CASE_REQUIRED
			)
			return
		outdir = self.root.settings.get('outdir')
		if not outdir:
			showerror(
				title = self.MISSING_ENTRY,
				message = self.DEST_DIR_REQUIRED
			)
			return
		filename = self.root.settings.get('filename')

		verify = self.root.settings.get(self.root.VERIFY_FILE)

		root_id = self.root.settings.get('root_id')

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