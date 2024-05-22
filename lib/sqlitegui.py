#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from .guilabeling import SQLiteLabels
from .guielements import NotebookFrame, GridLabel, FilenameSelector
from .guielements import GridSeparator, OutDirSelector, FileSelector
from .guielements import StringRadiobuttons, StringSelector, GridLabel
from .guielements import AddJobButton, Error
#from .guielements import FilenameSelector, StringSelector, GridButton
#from .guielements import FileSelector, LeftButton, RightButton
#from .guielements import GridBlank, VerticalRadiobuttons
#from .sqliteutils import SQLiteReader

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
			('Execute', 'Alternative', 'DumpSchema', 'DumpContent')
		)
		self.sql_file = FileSelector(
			frame,
			self.root.settings.init_stringvar('SQLFile'),
			self.EXECUTE_SQL_FILE,
			self.SELECT_SQL_FILE,
			filetype = ('SQL', '*.sql'),
			tip = self.TIP_SQL_FILE,
		)
		GridLabel(frame, self.ALTERNATIVE, column=2)
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
		AddJobButton(frame, 'AxChecker', self._add_job)
		self.root.child_win_active = False

	def _list_schema(self):
		'''Show database schema'''
		if self.root.child_win_active:
			return
		sqlite_db = self.sqlite_db.get()
		if not sqlite_db:
			Error(self.FIRST_CHOOSE_DB)
			return
		try:
			reader = SQLiteReader(Path(sqlite_db))
		except Exception as e:
			Error(repr(e))
			return
		self.child_window = ChildWindow(self.root, self.root.SCHEMA)
		frame = ExpandedFrame(elf.child_window)
		self.tree = Tree(frame)
		for table_name, column_names in reader.list_tables():
			table = self.tree.insert('', 'end', text=table_name, iid=f'{table_name}\t')
			for column_name in column_names:
				self.tree.insert(table, 'end', text=column_name, iid=f'{table_name}\t{column_name}')

		frame = ExpandedFrame(self.child_window)
		LeftButton(frame, self.SELECT, self._get_selected)
		RightButton(frame, self.QUIT, self.child_window.destroy)

	def _get_selected(self):
		'''Get the selected root'''
		self.root.settings.section = self.CMD
		try:
			table_name, column_name = self.tree.focus().split('\t')
		except ValueError:
			pass
		else:
			self.root.settings.raw(self.root.TABLE).set(table_name)
			self.root.settings.raw(self.root.COLUMN).set(column_name)
		self.child_window.destroy()

	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		db = self.root.settings.get(self.root.SQLITE_DB)
		outdir = self.root.settings.get(self.root.OUTDIR) 
		filename = self.root.settings.get(self.root.FILENAME)
		to_do = self.root.settings.get(self.root.TO_DO)
		sql_file = self.root.settings.get(self.root.SQL_FILE)
		table = self.root.settings.get(self.root.TABLE)
		column = self.root.settings.get(self.root.COLUMN)
		if not db:
			if to_do == self.root.EXECUTE_SQL or to_do == self.root.ALTERNATIVE:
				db = Path(outdir)/f'{filename}.db'
			else:
				showerror(
					title = self.root.MISSING_ENTRIES,
					message = self.root.SQLITE_DB_REQUIRED
				)
				return
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
		cmd = self.root.settings.section.lower()
		cmd += f' --{self.root.OUTDIR.lower()} "{outdir}"'
		cmd += f' --{self.root.FILENAME.lower()} "{filename}"'
		if to_do == self.root.EXECUTE_SQL or to_do == self.root.ALTERNATIVE:
			if not sql_file:
				showerror(
					title = self.root.MISSING_ENTRIES,
					message = self.root.SQL_FILE_REQUIRED
				)
				return
			if to_do == self.root.EXECUTE_SQL:
				cmd += f' --execute "{sql_file}"'
			else:
				cmd += f' --read "{sql_file}"'
		elif to_do == self.root.DUMP_SCHEMA:
			cmd += f' --schema'
		else:
			if table:
				cmd += f' --table "{table}"'
			if column:
				cmd += f' --column "{column}"'
		cmd += f' "{db}"'
		self.root.append_job(cmd)
