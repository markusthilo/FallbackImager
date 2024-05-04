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
			self.root.settings.init_stringvar('Task', default='Check'),
			('Check', 'CompareDir', 'CompareTSV')
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
			self.root.settings.init_boolvar('NoHead'),
			self.TSV_NO_HEAD,
			columnspan = 3,
			tip = self.TIP_TSV_NO_HEAD
		)
		GridSeparator(frame)
		GridBlank(frame)
		AddJobButton(frame, self.MODULE, self._add_job)
		self.root.child_win_active = False

	def _select_root(self):
		'''Select root to compare in the AXIOM case'''
		if self.root.child_win_active:
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
		self.task.set('CompareDir')

	def _select_tsv_file(self):
		'''Select TSV file to compare'''
		self.task.set('CompareTSV')

	def _select_column(self):
		'''Select column in TSV file to compare'''
		self.task.set('CompareTSV')
		SelectTsvColumn(self.root, self.tsv_column, self.tsv_file)

	def _add_job(self):
		'''Generate command line'''
		mfdb = self.case_file.get()
		outdir = self.outdir.get()
		filename = self.filename.get()
		task = self.task.get()
		if task != 'Check':
			root_id = self.root_id.get()
			try:
				int(root_id)
			except ValueError:
				showerror(
					title = self.MISSING_ENTRIES,
					message = self.ROOT_ID_REQUIRED
				)
				return
			if task == 'CompareDir':
				root_dir = self.root_dir.get()
				if not root_dir:
					showerror(
						title = self.MISSING_ENTRIES,
						message = self.ROOT_DIR_REQUIRED
					)
					return
			else:
				tsv_file = self.tsv_file.get()
				tsv_column = self.tsv_column.get()
				if not tsv_file or not tsv_column:
					showerror(
						title = self.MISSING_ENTRIES,
						message = self.TSV_AND_COL_REQUIRED
					)
					return
				tsv_no_head = self.tsv_no_head.get()
		cmd = f'axchecker --root "{root_id}" --outdir "{outdir}"'
		if filename:
			cmd += f' --filename "{filename}"'
		if task == 'CompareDir':
			cmd += f' --diff "{root_dir}"'
		elif task == 'CompareTSV':
			cmd += f' --diff "{tsv_file}" --column "{tsv_column}"'
			if tsv_no_head:
				cmd += ' --nohead'
		cmd += f' "{mfdb}"'
		self.root.append_job(cmd)