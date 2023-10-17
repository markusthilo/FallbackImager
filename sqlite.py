#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'Sqlite'
__author__ = 'Markus Thilo'
__version__ = '0.2.2_2023-10-17'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Work with SQLite (e.g. for RDSv3 or SQL dump files)
'''

from pathlib import Path
from argparse import ArgumentParser
from lib.extpath import ExtPath
from lib.sqliteutils import SQLiteExec, SQLiteReader, SQLDump
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.guielements import SourceDirSelector, Checker, LeftLabel
from lib.guielements import ChildWindow, SelectTsvColumn
from lib.guielements import ExpandedFrame, GridSeparator, GridLabel, DirSelector
from lib.guielements import FilenameSelector, StringSelector, StringRadiobuttons
from lib.guielements import FileSelector, GridButton, LeftButton, RightButton

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
			for table in reader.get_tables():
				line = f'{table} ({reader.count(table)}):\t'
				line += '\t'.join(f'{column} ({reader.get_type(table, column)})'
					for column in reader.get_columns(table)
				)
				print(line, file=fh)
		self.log.info('Done', echo=True)
		reader.close()
		self.log.close()

	def echo_schema(self):
		'''Get short version of database schema and print/echo'''
		reader = SQLiteReader(self.db_path)
		self.echo('Getting schema from database')
		for name, columns in reader.list_tables():
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
		#GridLabel(root, frame, root.SQLITE_DB, columnspan=3)
		FileSelector(root, frame, root.SQLITE_DB, root.SQLITE_DB,
			f'{root.SELECT_DB} ({root.SELECT_DB})',
			filetype=(root.SQLITE_DB, '*.db'))
		GridButton(root, frame, root.SCHEMA , self._list_schema, column=1)
		GridSeparator(root, frame)

		StringRadiobuttons(root, frame, root.TO_DO,
			(root.EXECUTE_SQL, root.ALTERNATIVE, root.DUMP_SCHEMA, root.DUMP_CONTENT),
			root.EXECUTE_SQL)
		GridLabel(root, frame, root.EXECUTE_SQL, column=1)
		GridLabel(root, frame, root.ALTERNATIVE, column=1)
		GridLabel(root, frame, root.DUMP_SCHEMA, column=1)
		GridLabel(root, frame, root.DUMP_CONTENT, column=1)
		'''

		FileSelector(root, frame, root.SQL_FILE, root.SQL_FILE,
			f'{root.SELECT_SQL_FILE} ({root.SELECT_SQL_FILE})',
			filetype=(root.SQL_FILE, '*.sql'))
		
		StringSelector(root, frame, root.TABLE, root.TABLE,
			command=self._select_partition)	
		
		GridLabel(root, frame, root.VERIFY_FILE, columnspan=2)
		StringRadiobuttons(root, frame, root.VERIFY_FILE,
			(root.DO_NOT_COMPARE, root.FILE_STRUCTURE, root.TSV), root.DO_NOT_COMPARE)
		GridLabel(root, frame, root.DO_NOT_COMPARE, column=1, columnspan=2)
		DirSelector(root, frame, root.FILE_STRUCTURE, root.FILE_STRUCTURE, root.SELECT_FILE_STRUCTURE,
			command=self._select_file_structure)
		FileSelector(root, frame, root.TSV, root.TSV, root.SELECT_TSV,
			command=self._select_tsv_file)
		StringSelector(root, frame, root.COLUMN, root.COLUMN, command=self._select_column)
		Checker(root, frame, root.TSV_NO_HEAD, root.TSV_NO_HEAD, column=1)
		'''
		GridSeparator(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job, columnspan=3)
		root.child_win_active = False
		self.root = root

	def _list_schema(self):
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
		mfdb = MfdbReader(Path(mfdb))
		if not mfdb.partitions:
			showerror(
				title = self.root.CASE_FILE,
				message = self.root.UNABLE_DETECT_PARTITIONS
			)
			return
		if len(mfdb.partitions) == 1:
			self.root.settings.raw(self.root.PARTITION).set(list(mfdb.partitions.values())[0])
			return
		self.partition_window = ChildWindow(self.root, self.root.SELECT_PARTITION)
		self._selected_part = StringVar()
		for partition in mfdb.partitions.values():
			frame = ExpandedFrame(self.root, self.partition_window)
			Radiobutton(frame, variable=self._selected_part, value=partition).pack(
				side='left', padx=self.root.PAD)
			LeftLabel(self.root, frame, partition)
		frame = ExpandedFrame(self.root, self.partition_window)
		LeftButton(self.root, frame, self.root.SELECT, self._get_partition)
		RightButton(self.root, frame, self.root.QUIT, self.partition_window.destroy)

	def _get_partition(self):
		'''Get the selected partition'''
		self.root.settings.section = self.CMD
		self.root.settings.raw(self.root.PARTITION).set(self._selected_part.get())
		self.partition_window.destroy()

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
		if not outdir or not filename:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.SOURCED_DEST_REQUIRED
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

if __name__ == '__main__':	# start here if called as application
	app = SQLiteCli(description=__description__.strip())
	app.parse()
	app.run()
