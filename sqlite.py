#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'Sqlite'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2024-12-26'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
The Sqlite module uses the Python library sqlite3. It can show the structure of a .db file or dump the content as CSV/TSV. In addition SQL code can be executed by the library. An alternative method is implemented that is designed to generate a .db file from a MySQL dump file in case sqlite3 fails.
'''

from argparse import ArgumentParser
from pathlib import Path
from lib.pathutils import PathUtils
from lib.sqliteutils import SQLiteExec, SQLiteReader, SQLDump
from lib.timestamp import TimeStamp
from lib.logger import Logger

class SQLite:
	'''The easy way to work with SQLite'''

	def __init__(self, echo=print):
		'''Generate object'''
		self.available = True
		self.echo = echo

	def open(self, db,
		filename = None,
		outdir = None,
		log = None
	):
		'''Prepare to create zip file'''
		self.db_path = Path(db)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = PathUtils.mkdir(outdir)
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
		if alternative:
			gen_ex = self.trans_ex(sql_path, executor)
		else:
			gen_ex = executor.from_file(sql_path)
		if self.echo == print:
			echo = lambda msg: print(f'\r{msg}', end='')
		else:
			echo = lambda msg: self.echo(msg, overwrite=True)
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
						for value in reader.fetch_table(table, column=column):
							print(value, file=fh)
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

	def get_schema(self):
		'''Get short version of database schema and print/echo'''
		schema = ''
		for name, columns in self.list_tables():
			schema += f'{name}: {", ".join(columns)}\n'
		return schema

class SQLiteCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self, echo=print, **kwargs):
		'''Define CLI using argparser'''
		self.echo = echo
		super().__init__(description=__description__, **kwargs)
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

	def run(self):
		'''Run the imager'''
		sqlite = SQLite(echo=self.echo)
		sqlite.open(self.db,
			filename = self.filename,
			outdir = self.outdir,
		)
		if self.echo_schema:
			self.echo(sqlite.get_schema())
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

if __name__ == '__main__':	# start here if called as application
	app = SQLiteCli()
	app.parse()
	app.run()
