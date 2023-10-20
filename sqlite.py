#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'Sqlite'
__author__ = 'Markus Thilo'
__version__ = '0.2.2_2023-10-20'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Work with SQLite (e.g. for RDSv3 or SQL dump files)
'''

from pathlib import Path
from argparse import ArgumentParser
from tkinter.messagebox import showerror
from tkinter.scrolledtext import ScrolledText
from lib.extpath import ExtPath
from lib.sqliteutils import SQLiteExec, SQLiteReader, SQLDump
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.guielements import SourceDirSelector, Checker, LeftLabel
from lib.guielements import ChildWindow, SelectTsvColumn
from lib.guielements import ExpandedFrame, GridSeparator, GridLabel, DirSelector
from lib.guielements import FilenameSelector, StringSelector, StringRadiobuttons
from lib.guielements import FileSelector, GridButton, LeftButton, RightButton
from lib.guielements import GridBlank, StringRadiobuttonsFrame

class SQLite:
	'''The easy way to work with SQLite'''

	def __init__(self, db,
		filename = None,
		outdir = None,
		echo = print,
		log = None
	):
		'''Prepare to create zip file'''
		self.echo = echo
		self.db_path = Path(db)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		self.log = log

	def start_log(self):
		'''Start logging'''
		if not self.log:
			self.log = Logger(filename=self.filename, outdir=self.outdir,
				head='sqlite.SQLite', echo=self.echo)

	def trans_ex(self, sql_path, executor):
		'''Read statements from file, translate and execute'''
		sqldump = SQLDump(sql_path)
		for cmd_str, values in sqldump.translate_all():
			try:
				executor.cursor.execute(cmd_str, values)
			except Exception as ex:
				yield ex
			yield None

	def execute(self, sql_path, alternative=False):
		'''Execute statements from SQL file'''
		self.start_log()
		self.log.info('Executing statements from SQL file', echo=True)
		executor = SQLiteExec(self.db_path)
		executed_cnt = 0
		warning_cnt = 0
		if self.echo == print:
			echo = lambda msg: print(f'\r{msg}', end='')
		else:
			echo = lambda msg: self.echo(msg, overwrite=True)
		if alternative:
			gen_ex = self.trans_ex(sql_path, executor)
		else:
			gen_ex = executor.from_file(sql_path)
		echo(1)
		for warning in gen_ex:
			if warning:
				self.log.warning(warning, echo=False)
				warning_cnt += 1
				continue
			executed_cnt += 1
			if executed_cnt % 10000 == 0:
				echo(executed_cnt)
				if msg := executor.commit():
					self.log.warning(msg, echo=False)
					warning_cnt += 1
		echo('')
		if msg := executor.commit():
			self.log.warning(msg)
			warning_cnt += 1 
		executor.close()
		self.log.info(f'Applied {executed_cnt} statement(s) to {self.db_path}', echo=True)
		if warning_cnt > 0:
			self.log.warning(f'SQLite library threw {warning_cnt} exception(s)')
		self.log.close()

	def dump(self, table=None, column=None, sort=False, uniq=False):
		'''Dump to text file'''
		self.start_log()
		self.log.info('Dumping to text/CSV file')
		reader = SQLiteReader(self.db_path)
		if table:
			tables = (table,)
		else:
			tables = reader.get_tables()
		for table in tables:
			try:
				len_table = reader.count(table)
			except Exception as ex:
				self.log.error(ex)
			if len_table == 0:
				self.log.info(f'Skipping table {table} - no items', echo=True)
			else:
				if column:
					tp = reader.get_printable(table, column)
					if tp != '' and tp != '"':
						self.log.info(f'{column} of {table} contains {len_table} of type {tp}')
						continue
					if not column in reader.get_columns(table):
						self.log.info(f'Table {table} does not have {column}', echo=True)
						continue
					with ExtPath.child(f'{self.filename}_{table}_{column}.txt', parent=self.outdir
						).open(mode='w', encoding='utf-8') as fh:
						for row, in reader.fetch_table(table, columns=column):
							print(row, file=fh)
					continue
				columns = tuple(col for col in reader.get_columns(table))
				types = tuple(reader.get_printable(table, col) for col in columns)
				self.log.info(f'Creating file for table {table}', echo=True)
				with ExtPath.child(f'{self.filename}_{table}.csv', parent=self.outdir
					).open(mode='w', encoding='utf-8') as fh:
					print('\t'.join(columns), file=fh)
					for row in reader.fetch_table(table, columns=columns):
						line = list()
						for i, item in enumerate(row):
							if types[i] == '':
								line.append(f'{item}')
							elif types[i] == '"':
								line.append(f'"{item}"')
							else:
								line.append(types[i])
						print('\t'.join(line), file=fh)
		self.log.info('Done', echo=True)
		reader.close()
		self.log.close()

	def schema(self):
		'''Get database schema'''
		self.start_log()
		self.log.info('Write database schema to text/CSV file')
		reader = SQLiteReader(self.db_path)
		with ExtPath.child(f'{self.filename}_schema.txt', parent=self.outdir
			).open(mode='w', encoding='utf-8') as fh:
			print('table (rows):\tcolumns (type)\t...', file=fh)
			for table, columns in reader.list_tables():
				line = f'{table} ({reader.count(table)}):'
				for column in columns:
					if col_type := reader.get_type(table, column):
						line += f'\t{column} ({col_type})'
					else:
						line += f'\t{column}'
				print(line, file=fh)
		self.log.info('Done', echo=True)
		reader.close()
		self.log.close()

	def list_tables(self):
		'''Get tables with columns'''
		reader = SQLiteReader(self.db_path)
		for name, columns in reader.list_tables():
			yield name, columns

	def echo_schema(self):
		'''Get short version of database schema and print/echo'''
		for name, columns in self.list_tables():
			col_names = ', '.join(columns)
			self.echo(f'{name}: {col_names}')

class SQLiteCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(**kwargs)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-c', '--column', type=str,
			help='Column/field to dump'
		)
		self.add_argument('-l', '--list', default=False, action='store_true',
			help='List tables/schema, ignore other tasks', dest='echo_schema'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('-r', '--read', type=Path,
			help='Read dump file and fill SQLite DB (alternative method to -x)', metavar='FILE'
		)
		self.add_argument('-s', '--schema', default=False, action='store_true',
			help='Write schema of database as text/TSV file'
		)
		self.add_argument('-t', '--table', type=str,
			help='Dump table'
		)
		self.add_argument('-x', '--execute', type=Path,
			help='Execute SQL statements from file an apply to database', metavar='FILE'
		)
		self.add_argument('db', nargs=1, type=Path,
			help='Database file', metavar='FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.db = args.db[0]
		self.column = args.column
		self.echo_schema = args.echo_schema
		self.filename = args.filename
		self.outdir = args.outdir
		self.read = args.read
		self.schema = args.schema
		self.table = args.table
		self.execute = args.execute

	def run(self, echo=print):
		'''Run the imager'''
		sqlite = SQLite(self.db,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo
		)
		if self.echo_schema:
			sqlite.echo_schema()
		else:
			if self.execute:
				sql_path = self.execute
				sqlite.execute(sql_path)
			elif self.read:
				sql_path = self.read
				sqlite.execute(sql_path, alternative=True)
			elif self.schema:
				sqlite.schema()
			else:
				sqlite.dump(table=self.table, column=self.column)

class SQLiteGui:
	'''Notebook page'''
	CMD = __app_name__
	DESCRIPTION = __description__

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
		db = SQLite(Path(db), echo=lambda line: text.insert('end', f'{line}\n'))
		window = ChildWindow(self.root, self.root.SCHEMA)
		text = ScrolledText(window, width=self.root.ENTRY_WIDTH, height=4*self.root.INFO_HEIGHT)
		text.pack(fill='both', expand=True)
		text.bind('<Key>', lambda dummy: 'break')
		db.echo_schema()
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

if __name__ == '__main__':	# start here if called as application
	app = SQLiteCli(description=__description__.strip())
	app.parse()
	app.run()
