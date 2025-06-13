#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'SQL2CSV'
__author__ = 'Markus Thilo'
__version__ = '0.1.0_2025-06-13'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
The Sqlite module uses the Python library sqlite3. It can show the structure of a .db file or dump the content as CSV/TSV. In addition SQL code can be executed by the library. An alternative method is implemented that is designed to generate a .db file from a MySQL dump file in case sqlite3 fails.
'''

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

	def get_tables(self):
		'''Get tables from scheme'''
		self.execute(f'SELECT name FROM sqlite_schema WHERE type="table"')
		for res in self._cursor.fetchall():
			yield res[0]

	def get_columns(self, table):
		'''Get column names for one table'''
		self.execute(f'SELECT name FROM pragma_table_info("{table}");')
		for res in self._cursor.fetchall():
			yield res[0]
			
	def count_column(self, table):
		'''Get number of columns in a table'''
		self.execute(f'SELECT COUNT(*) FROM pragma_table_info("{table}")')
		return self._cursor.fetchone()[0]

	def count_rows(self, table):
		'''Get number of lines in a table'''
		self.execute(f'SELECT COUNT(*) FROM "{table}"')
		return self._cursor.fetchone()[0]

	def get_type(self, table, column):
		'''Get column type'''
		self.execute(f'SELECT typeof("{column}") FROM "{table}"')
		try:
			return self._cursor.fetchone()[0]
		except:
			return 'NULL'

	def fetch_table(self, table):
		'''Fetch one table row by row'''
		self.execute(f'SELECT * FROM "{table}"')
		for res in self._cursor.fetchall():
			yield res

	def fetch_column(self, table, column):
		'''Fetch one column of one table row by row'''
		self.execute(f'SELECT "{column}" FROM "{table}"')
		for res in self._cursor.fetchall():
			yield res[0]

	def get_printable(self, table, column):
		'''Return non printable type, quotes or no quotes'''
		tp = self.get_type(table, column).upper()
		if tp in self.NO_QUOTE_TYPES:
			return ''
		if tp in self.IGNORED_TYPES:
			return tp.upper()
		return '"'

class Worker:
	'''Do the work'''

	def __init__(self, db_path, write=None, delimiter='\t', debug=False):
		'''Prepare worker'''
		self._db = SqliteDb(db_path)
		self._w = write.open(mode='w', encoding='utf-8') if write else None
		self._d = delimiter
		self._debug = debug

	def execute(self, statement):
		'''Execute given SQL statements'''
		self._db.execute(statement)
		self._db.commit()
		self._db.close()

	def execute_file(self, sql_path, raw=False):
		'''Execute SQL statements from file'''
		sql_file = SqlFile(sql_path) if raw else Translator(sql_path)
		for statement in sql_file.read():
			exception = None
			try:
				self._db.execute(statement)
			except Exception as ex:
				exception = ex
			if exception:
				print(statement)
				if self._debug:
					raise exception
				print(f'{type(exception)}: {exception}', file=stderr)
		self._db.commit()
		self._db.close()

	def schema(self):
		'''Print database schema'''
		#print(f'table (rows):{self._d}columns (type){self._d}...', file=sel._w)
		for table in self._db.get_tables():
			line = f'{table}{self._d}{self._db.count_rows(table)}'
			for column in self._db.get_columns(table):
				line += f'{self._d}{column}{self._d}{self._db.get_type(table, column)}'
			print(line, file=self._w)

	def table(self, table):
		'''Print table content'''
		#	print(f'Column {column} of table {table}:', file=self._w)
		#	print(f'Table {table}:', file=self._w)
		for row in self._db.fetch_table(table):
			print(row, file=self._w)

	def column(self, table, column):
		'''Print table content, one column only'''
		#print(f'Column {column} of table {table}:', file=self._w)
		for col in self._db.fetch_column(table, column):
			print(row, file=self._w)


	def dump(self, table, columns):
		'''Dump table'''
		if column:
			for row in self.fetch_table(table, columns=columns):
				print(row[0])
		else:
			for row in self.fetch_table(table):
				print('\t'.join(str(item) for item in row))
				if column:
					tp = reader.get_printable(table, column)
					if tp != '' and tp != '"':
						self.log.info(f'{column} of {table} contains {len_table} of type {tp}')
						continue
					if not column in reader.get_columns(table):
						self.log.info(f'Table {table} does not have {column}', echo=True)
						continue
					with self.outdir.joinpath(f'{self.filename}_{table}_{column}.txt').open(mode='w', encoding='utf-8') as fh:
						for value in reader.fetch_table(table, column=column):
							print(value, file=fh)
					continue
				columns = tuple(col for col in reader.get_columns(table))
				types = tuple(reader.get_printable(table, col) for col in columns)
				self.log.info(f'Creating file for table {table}', echo=True)
				with self.outdir.joinpath(f'{self.filename}_{table}.csv').open(mode='w', encoding='utf-8') as fh:
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

if __name__ == '__main__':	# start here if called as application
		arg_parser = ArgumentParser(description=__description__)
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
		arg_parser.add_argument('-r', '--raw', action='store_true',
			help='Execute SQL statements without translation to SQLite compatibility'
		)
		arg_parser.add_argument('-s', '--schema', action='store_true',
			help='Show database schema'
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
		if args.execute and args.file:
			raise ValueError('Argument -e/--execute is not possible with -f/--file')
		worker = Worker(args.db[0], debug=args.debug)
		if args.execute:
			worker.execute(args.execute)
		elif args.file:
			worker.execute_file(args.file)
		elif args.schema:
			worker.schema()
		if args.column and not args.table:
			raise ValueError('Argument -c/--column is only possible with -t/--table')
		if args.column:
			worker.column(args.table, args.column)
		elif args.table:
			worker.table(args.table)
