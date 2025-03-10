#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from tkinter import StringVar
from tkinter.ttk import Entry
from .guilabeling import SQLiteLabels
from .guielements import NotebookFrame, GridLabel, FilenameSelector, ExpandedFrame, GridButton
from .guielements import GridSeparator, OutDirSelector, FileSelector, ExpandedTree
from .guielements import StringRadiobuttons, StringSelector, GridLabel, LeftButton
from .guielements import AddJobButton, Error, ChildWindow, MissingEntry, RightButton
from .guiconfig import GuiConfig
from .sqliteutils import SQLiteReader

class SQLiteGui(SQLiteLabels):
	'''Notebook page for SQLite'''

	MODULE = 'SQLite'

	def __init__(self, root):
		'''Notebook page'''
		self.root = root
		frame = NotebookFrame(self)
		GridLabel(frame, 'SQLite')
		self.sqlite_db = FileSelector(
			frame,
			self.root.settings.init_stringvar('DBFile'),
			self.SQLITE_DB,
			self.SELECT_DB,
			filetype = ('SQLITE DB', '*.db'),
			tip = self.TIP_SQLITE_DB,
		)
		GridSeparator(frame)
		GridLabel(frame, self.DESTINATION)
		self.outdir = OutDirSelector(frame, self.root.settings.init_stringvar('OutDir'))
		self.filename = FilenameSelector(frame, '{now}_sqlite',
			self.root.settings.init_stringvar('Filename'))
		GridSeparator(frame)
		GridLabel(frame, self.TASK)
		self.task = StringRadiobuttons(
			frame,
			self.root.settings.init_stringvar('Task', default='Execute'),
			('Execute', 'Read', 'DumpSchema', 'DumpContent')
		)
		self.sql_file = FileSelector(
			frame,
			self.root.settings.init_stringvar('SQLFile'),
			self.EXECUTE_SQL_FILE,
			self.SELECT_SQL_FILE,
			filetype = ('SQL', '*.sql'),
			tip = self.TIP_SQL_FILE,
		)
		GridLabel(frame, self.ALTERNATIVE, column=1)
		GridLabel(frame, self.DUMP_SCHEMA, column=1)
		GridLabel(frame, self.DUMP_CONTENT, column=1)
		self.select_buttton = GridButton(
			frame,
			self.SELECT,
			self._list_schema,
			column = 1,
			incrow = False,
			tip = self.TIP_SELECT
		)
		self.table = StringVar()
		self.column = StringVar()
		GridLabel(frame, self.TABLE, column=2, columnspan=1, incrow=False)
		Entry(frame, textvariable=self.table, width=GuiConfig.MAX_ENTRY_WIDTH).grid(
			row=frame.row, column=3, sticky='w', padx=frame.padding)
		GridLabel(frame, self.COLUMN, column=4, columnspan=1, incrow=False)
		Entry(frame, textvariable=self.column, width=GuiConfig.MAX_ENTRY_WIDTH).grid(
			row=frame.row, column=5, sticky='w', padx=frame.padding)
		frame.row += 1
		'''
		self.table = StringSelector(
			frame,
			self.root.settings.init_stringvar('Table'),
			self.TABLE,
			command = self._list_schema,
			tip = self.TIP_TABLE
		)
		self.column = StringSelector(
			frame,
			self.root.settings.init_stringvar('Column'),
			self.COLUMN,
			command = self._list_schema,
			tip = self.TIP_COLUMN
		)
		'''
		AddJobButton(frame, 'SQLite', self._add_job)
		self.root.child_win_active = False

	def _list_schema(self):
		'''Show database schema'''
		sqlite_db = self.sqlite_db.get()
		if not sqlite_db:
			Error(self.FIRST_CHOOSE_DB)
			return
		try:
			reader = SQLiteReader(Path(sqlite_db))
		except Exception as e:
			Error(repr(e))
			return
		self.child_window = ChildWindow(self.root, self.SCHEMA, button=self.select_buttton)
		frame = ExpandedFrame(self.child_window)
		self.tree = ExpandedTree(frame, GuiConfig.TREE_WIDTH, GuiConfig.TREE_HEIGHT,
			text=sqlite_db, doubleclick=self._double_click)
		for table_name, column_names in reader.list_tables():
			table = self.tree.insert('', 'end', text=table_name, iid=f'{table_name}\t')
			for column_name in column_names:
				self.tree.insert(table, 'end', text=column_name, iid=f'{table_name}\t{column_name}')
		frame = ExpandedFrame(self.child_window)
		LeftButton(frame, self.SELECT, self._get_selected)
		RightButton(frame, self.QUIT, self.child_window.quit)

	def _double_click(self, dummy_event):
		'''Get selected root'''
		
		self._get_selected()

	def _get_selected(self):
		'''Get the selected root'''
		try:
			table, column = self.tree.focus().split('\t')
		except ValueError:
			pass
		else:
			self.table.set(table)
			self.column.set(column)
		self.child_window.quit()

	def _add_job(self):
		'''Generate command line'''
		sqlite_db = self.sqlite_db.get()
		outdir = self.outdir.get()
		filename = self.filename.get()
		task = self.task.get()
		sql_file = self.sql_file.get()
		table = self.table.get()
		column = self.column.get()
		if not sqlite_db:
			if task == 'Execute' or task == 'Read':
				sqlite_db = Path(outdir)/f'{filename}.db'
			else:
				MissingEntry(self.SQLITE_DB_REQUIRED)
				return
		if not outdir:
			MissingEntry(self.DEST_DIR_REQUIRED)
			return
		if not sql_file and ( task == 'Execute' or task == 'Read' ):
			MissingEntry(self.SQL_FILE_REQUIRED)
			return
		cmd = f'sqlite --outdir "{outdir}"'
		if filename:
			cmd += f' --filename "{filename}"'
		if task == 'Execute':
			cmd += f' --execute "{sql_file}"'
		elif task == 'Read':
			cmd += f' --read "{sql_file}"'
		elif task == 'DumpSchema':
			cmd += f' --schema'
		else:
			if table:
				cmd += f' --table "{table}"'
				if column:
					cmd += f' --column "{column}"'
		cmd += f' "{sqlite_db}"'
		self.root.append_job(cmd)
