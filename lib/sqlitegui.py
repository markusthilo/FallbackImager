#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from tkinter.scrolledtext import ScrolledText
from tkinter.messagebox import showerror
from lib.guielements import SourceDirSelector, Checker, LeftLabel
from lib.guielements import ChildWindow, SelectTsvColumn
from lib.guielements import ExpandedFrame, GridSeparator, GridLabel, DirSelector
from lib.guielements import FilenameSelector, StringSelector, StringRadiobuttons
from lib.guielements import FileSelector, GridButton, LeftButton, RightButton
from lib.guielements import GridBlank, StringRadiobuttonsFrame
from sqlite import SQLite

class SQLiteGui:
	'''Notebook page for SQLite'''

	CMD = 'SQLite'

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		GridSeparator(root, frame)
		GridLabel(root, frame, root.DATABASE)
		FileSelector(root, frame, root.SQLITE_DB, root.SQLITE_DB,
			f'{root.SELECT_DB} ({root.SELECT_DB})',
			filetype=(root.SQLITE_DB, '*.db'))
		GridSeparator(root, frame)
		GridLabel(root, frame, root.DESTINATION)
		self.filename_str = FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
		DirSelector(root, frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		GridSeparator(root, frame)
		GridLabel(root, frame, root.TO_DO)
		StringRadiobuttonsFrame(root, frame, root.TO_DO,
			(root.EXECUTE_SQL, root.ALTERNATIVE, root.DUMP_SCHEMA, root.DUMP_CONTENT),
			root.EXECUTE_SQL)
		FileSelector(root, frame, root.SQL_FILE, root.SQL_FILE,
			f'{root.SELECT_SQL_FILE} ({root.SELECT_SQL_FILE})',
			filetype=(root.SQL_FILE, '*.sql'))
		StringSelector(root, frame, root.TABLE, root.TABLE, command=self._list_schema)
		StringSelector(root, frame, root.COLUMN, root.COLUMN, command=self._list_schema)
		GridSeparator(root, frame)
		GridBlank(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}',
			self._add_job, column=0, columnspan=3)
		root.child_win_active = False
		self.root = root

	def _list_schema(self):
		'''Show database schema'''
		if self.root.child_win_active:
			return
		self.root.settings.section = self.CMD
		db = self.root.settings.get(self.root.SQLITE_DB)
		if not db:
			showerror(
				title = self.root.SQLITE_DB,
				message = self.root.FIRST_CHOOSE_DB
			)
			return
		try:
			schema = SQLite(Path(db)).get_schema()
		except Exception as e:
			showerror(title=self.root.ERROR, message=repr(e))
			return
		window = ChildWindow(self.root, self.root.SCHEMA)
		text = ScrolledText(window, width=self.root.ENTRY_WIDTH, height=4*self.root.INFO_HEIGHT)
		text.pack(fill='both', expand=True)
		text.bind('<Key>', lambda dummy: 'break')
		text.insert('end', schema)
		text.configure(state='disabled')
		frame = ExpandedFrame(self.root, window)
		RightButton(self.root, frame, self.root.QUIT, window.destroy)

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
				cmd += f' --column "{table}"'
			if column:
				cmd += f' --column "{column}"'
		cmd += f' "{db}"'
		self.root.append_job(cmd)
