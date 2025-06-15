#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__email__ = 'markus.thilo@gmail.com'
__version__ = '0.1.0_2025-06-15'
__status__ = 'Testing'
__license__ = 'GPL-3'
__description__ = 'Python script to fill a SQLite DB file by SQL dump and write content as CSV.'

from sqlite3 import connect as SqliteConnect
from re import compile as re_compile
from sys import stderr
from pathlib import Path
from argparse import ArgumentParser
import sys

class SqlFile:
	'''Reader for files with SQL statements'''

	def __init__(self, path):
		'''Open database'''
		self._path = path

	def read(self):
		'''Read statements from file (.sql)'''
		statement = ''
		inside_quotes = None
		inside_comment = None
		with self._path.open(encoding='utf-8') as fh:
			for line in fh:
				for char in line:
					if inside_comment == '/*':
						if char == '/' and statement and statement[-1] == '*':
							inside_comment = None
						continue
					elif inside_comment == '--':
						if char == '\n':
							inside_comment = None
						continue
					if inside_quotes:
						if char == inside_quotes:
							inside_quotes = None
						statement += char
						continue
					if char == '*' and statement and statement[-1] == '/' and not inside_comment == '/*':
						inside_comment = '/*'
						statement = statement[:-1]
						continue
					elif char == '-' and statement and statement[-1] == '-':
						inside_comment = '--'
						statement = statement[:-1]
						continue
					elif char in '\'"`':
						inside_quotes = char
					elif char in '\t\n ':
						if not statement or statement[-1] == ' ':
							continue
						else:
							statement += ' '
							continue
					if char != ';':
						statement += char
						continue
					yield statement + ';'
					statement = ''

class Translator(SqlFile):
	'''Translate SQL statements to SQLite compatible'''

	def __init__(self, path):
		'''Set path to SQL file and compile regular expressions'''
		super().__init__(path)
		self._remove = tuple(
			re_compile(pattern) for pattern in (
				r'(?i)AUTO_INCREMENT',
				r'(?i)ENGINE\s*=\s*\w+',
				r'(?i)DEFAULT\s+CHARACTER\s+SET\s+\w+',
				r'(?i)CHARACTER\s+SET\s+\w+',
				r'(?i)DEFAULT\s+CHARSET\s*=\s*\w+',
				r'(?i)COLLATE\s+\w+',
				r'(?i)DEFAULT\s+COLLATE\s+\w+',
				r'(?i)UNSIGNED',
				r'(?i)ON\s+UPDATE\s+CURRENT_TIMESTAMP',
				r'(?i)COMMENT\s*=\s*\'.*?\'',
				r'(?i)ROW_FORMAT\s*=\s*\w+',
				r'(?i)KEY_BLOCK_SIZE\s*=\s*\d+',
				r'(?i)USING\s+BTREE',
				r'(?i)USING\s+HASH',
			)
		)
		
	def read(self):
		'''Read and make statements compatible with SQLite'''
		for raw_statement in super().read():
			statement = raw_statement.strip()
			for remove in self._remove:
				statement = remove.sub('', statement)
			if statement:
				yield statement

class SqliteDb:
	'''Work with the SQLite database'''

	NO_QUOTE_TYPES = ('INTEGER', 'REAL', 'NUMERIC')
	IGNORED_TYPES = ('BLOB',)

	def __init__(self, path):
		'''Open database'''
		self._db = SqliteConnect(path)
		self._cursor = self._db.cursor()

	def commit(self):
		'''Commit to SQLite database'''
		self._db.commit()

	def close(self):
		'''Close database'''
		self._db.close()
	
	def execute(self, statement):
		'''Execute SQL statement, return Exception or None for success'''
		self._cursor.execute(statement)
		for res in self._cursor.fetchall():
			yield res

	def get_tables(self):
		'''Get tables from scheme'''
		self._cursor.execute(f'SELECT name FROM sqlite_schema WHERE type="table";')
		for res in self._cursor.fetchall():
			yield res[0]
	
	def table_exits(self, table):
		'''Check if table exists'''
		self._cursor.execute(f'SELECT name FROM sqlite_schema WHERE type="table" AND name="{table}";')
		return bool(self._cursor.fetchone())

	def get_columns(self, table):
		'''Get column names for one table'''
		self._cursor.execute(f'SELECT name FROM pragma_table_info("{table}");')
		for res in self._cursor.fetchall():
			yield res[0]
	
	def column_exits(self, table, column):
		'''Check if column exists'''
		self._cursor.execute(f'SELECT name FROM pragma_table_info("{table}") WHERE name="{column}";')
		return bool(self._cursor.fetchone())

	def count_rows(self, table):
		'''Get number of lines in a table'''
		self._cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
		return self._cursor.fetchone()[0]

	def fetch_table(self, table):
		'''Fetch one table row by row'''
		return self.execute(f'SELECT * FROM "{table}";')

	def fetch_column(self, table, column):
		'''Fetch one column of one table row by row'''
		return self.execute(f'SELECT "{column}" FROM "{table}";')

	def get_type(self, table, column):
		'''Return non printable type, quotes or no quotes'''
		self._cursor.execute(f'SELECT typeof("{column}") FROM "{table}";')
		try:
			tp = self._cursor.fetchone()[0].upper()
		except:
			return 'UNDETECTED', '"'
		if tp in self.NO_QUOTE_TYPES:
			return tp, ''
		if tp in self.IGNORED_TYPES:
			return tp, None
		return tp, '"'

class Worker:
	'''Do the work'''

	def __init__(self, db_path, write=None, delimiter=None, headless=False, lines=None, debug=False):
		'''Prepare worker'''
		self._db = SqliteDb(db_path)
		self._w = write.open(mode='w', encoding='utf-8') if write else None
		self._d = delimiter if delimiter else '\t'
		self._l = headless
		self._n = lines
		self._debug = debug

	def _print_lines(self, rows, types=None):
		'''Print result'''
		if types:
			for cnt, columns in enumerate(rows):
				if cnt == self._n:
					break
				line = list()
				for column, tp in zip(columns, types):
					if tp == '"':
						line.append(f'"{column}"')
					elif tp == '':
						line.append(f'{column}')
					else:
						line.append('')
				print(self._d.join(line), file=self._w)
		else:
			for cnt, columns in enumerate(rows):
				if cnt == self._n:
					break
				print(f'{columns}', file=self._w)

	def execute(self, statement):
		'''Execute given SQL statements'''
		try:
			for line in self._db.execute(statement):
				if self._debug:
					self._print_lines(line)
		except Exception as ex:
			print(statement, file=stderr)
			raise ex
		self._db.commit()

	def execute_file(self, sql_path, raw=False):
		'''Execute SQL statements from file'''
		sql_file = SqlFile(sql_path) if raw else Translator(sql_path)
		for statement in sql_file.read():
			exception = None
			try:
				for line in self._db.execute(statement):
					if self._debug:
						self._print_lines(line)
			except Exception as ex:
				exception = ex
			if exception:
				print(statement, file=stderr)
				if self._debug:
					raise exception
				print(f'{type(exception)}: {exception}', file=stderr)
		self._db.commit()

	def schema(self):
		'''Print database schema'''
		tables = list()
		max_rows = 0
		max_entries = 0
		max_table_size = 0
		max_col_name_size = 0
		for table in self._db.get_tables():
			if len(table) > max_table_size:
				max_table_size = len(table)
			rows = self._db.count_rows(table)
			if rows > max_rows:
				max_rows = rows
			entries = [(table, rows)]
			for column in self._db.get_columns(table):
				if len(column) > max_col_name_size:
					max_col_name_size = len(column)
				tp = self._db.get_type(table, column)[0]
				entries.append((column, tp))
			if len(entries) > max_entries:
				max_entries = len(entries)
			tables.append(entries)
		max_rows_size = len(str(max_rows))
		if not self._l:
			print(f'{"TABLE":<{max_table_size}}  {"ROWS":>{max_rows_size}}')
			print(f'      {"COLUMNS":<{max_col_name_size}}  TYPE')
			print()
		for table in tables:
			print(f'{table[0][0]:<{max_table_size}}  {table[0][1]:>{max_rows_size}}')
			for column in table[1:]:
				print(f'      {column[0]:<{max_col_name_size}}  {column[1]}')
			print()
		if self._w:
			if not self._l:
				print(f'TABLE{self._d}ROWS' + f'{self._d}COLUMN{self._d}TYPE' * max_entries, file=self._w)
			self._print_lines((f'{name}{self._d}{attr}' for name, attr in table) for table in tables)

	def table(self, table):
		'''Print table content'''
		if not self._db.table_exits(table):
			raise ChildProcessError(f'Table "{table}" does not exist')
		columns = tuple(self._db.get_columns(table))
		if not self._l:
			print('"' + f'"{self._d}"'.join(columns) + '"', file=self._w)
		self._print_lines(self._db.fetch_table(table),
			types = tuple(self._db.get_type(table, column)[1] for column in columns)
		)

	def column(self, table, column):
		'''Print table content, one column only'''
		if not self._db.table_exits(table):
			raise ChildProcessError(f'Column "{column}" does not exist in Table "{table}"')
		if not self._l:
			print(f'"{column}"', file=self._w)
		self._print_lines(self._db.fetch_column(table, column),
			types = (self._db.get_type(table, column)[1], )
		)

	def dump_all(self, dir_path):
		'''Dump DB to folder'''
		for table_name in self._db.get_tables():
			file_path = dir_path / f'{table_name}.csv'
			with file_path.open(mode='w', encoding='utf-8') as self._w:
				self.table(table_name)
		self._w = None

	def close(self):
		'''Close database'''
		self._db.close()
		if self._w:
			self._w.close()

if __name__ == '__main__':	# start here if called as application
		arg_parser = ArgumentParser(
			description = __description__,
			epilog = f'Author: {__author__} ({__email__}), License: {__license__ }'
		)
		arg_parser.add_argument('-a', '--all', type=Path,
			help='Write all tables in an empty directory, use tabel names for file names', metavar='DIRECTORY'
		)
		arg_parser.add_argument('-c', '--column', type=str,
			help='Select column to dump a single column of a table (-t/--tabel)', metavar='COLUMN NAME / STRING'
		)
		arg_parser.add_argument('-d', '--delimiter', type=str,
			help='Delimiter inbetween columns', metavar='CHAR / STRING'
		)
		arg_parser.add_argument('-e', '--execute', type=str,
			help='Execute SQL statements and apply to database', metavar='SQL STATEMENT / STRING'
		)
		arg_parser.add_argument('-f', '--file', type=Path,
			help='Execute SQL statements from file and apply to database', metavar='SQL FILE'
		)
		arg_parser.add_argument('-g', '--debug', action='store_true',
			help='Debug mode'
		)
		arg_parser.add_argument('-l', '--headless', action='store_true',
			help='No headers / fieldnames'
		)
		arg_parser.add_argument('-n', '--lines', type=int,
			help='Abort after n lines, 0 for head line only', metavar='INTEGER'
		)
		arg_parser.add_argument('-r', '--read', type=Path,
			help='Read SQL statements from file and execute'
		)
		arg_parser.add_argument('-s', '--schema', action='store_true',
			help='Print database schema'
		)
		arg_parser.add_argument('-t', '--table', type=str,
			help='Select table to dump', metavar='TABLE NAME / STRING'
		)
		arg_parser.add_argument('-w', '--write', type=Path,
			help='Write to file instead of stdout', metavar='FILE'
		)
		arg_parser.add_argument('db', nargs=1, type=Path,
			help='Database file', metavar='FILE'
		)
		args = arg_parser.parse_args()
		if not args.db[0].is_file() and not ( args.execute or args.file or args.read ):
			raise FileNotFoundError(f'Unable to read SQLite file "{args.db[0]}"')
		if args.column and not args.table:
			raise ValueError('Argument -c/--column is only possible with -t/--table')
		if args.execute and (args.file or args.read):
			raise ValueError('Only one option -e/--execute,  -f/--file or -r/--read at a time')
		if args.all and (args.write or args.table or args.column):
			raise ValueError('Option -a/--all is not possible with -t/--table')
		worker = Worker(args.db[0],
			delimiter = args.delimiter,
			headless = args.headless,
			lines = args.lines,
			write = args.write,
			debug = args.debug
		)
		if args.execute:
			worker.execute(args.execute)
		elif args.file:
			worker.execute_file(args.file)
		elif args.read:
			worker.execute_file(args.read, raw=True)
		if args.table and args.column:
			worker.column(args.table, args.column)
		elif args.table:
			worker.table(args.table)
		elif args.all:
			if args.all.exists():
				if args.all.is_dir() and any(args.all.iterdir()):
					raise FileExistsError(f'"{args.all}" is not empty')
				else:
					raise FileExistsError(f'"{args.all}" exits but is not a directory')
			else:
				args.all.mkdir(parents=True)
			worker.dump_all(args.all)
			worker.schema()
		elif args.schema or not (args.execute or args.file or args.read):
			worker.schema()
		worker.close()
