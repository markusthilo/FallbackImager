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
from pathlib import Path
from argparse import ArgumentParser


class SQLiteReader:
	'''Read SQLite files'''

	NO_QUOTE_TYPES = ('INTEGER', 'REAL', 'NUMERIC')
	IGNORED_TYPES = ('BLOB',)

	def __init__(self, path):
		'''Open database'''
		self._db = SqliteConnect(path)
		self._cursor = self.db.cursor()

	def commit(self):
		'''Commit to SQLite database'''
		self.db.commit()

	def close(self):
		'''Close database'''
		self.commit()
		self._db.close()

	def __del__(self):
		'''Close database'''
		self.close()
	
	def try_execute(self, statement):
		'''Rey to execute SQL statement, return Exception or None for success'''
		try:
			self._cursor.execute(statement)
		except Exception as ex:
			return ex
		return

	def get_tables(self):
		'''List tables from scheme'''
		self.cursor.execute(f'SELECT name FROM sqlite_schema WHERE type="table"')
		for table in self.cursor.fetchall():
			yield table[0]

	def get_columns(self, table):
		'''Get column names for one table'''
		self.cursor.execute(f'SELECT name FROM pragma_table_info("{table}");')
		return (res[0] for res in self.cursor.fetchall())

	def count(self, table):
		'''Get number of lines in a table'''
		self.cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
		return self.cursor.fetchone()[0]

	def get_type(self, table, column):
		'''Get column type'''
		self.cursor.execute(f'SELECT typeof("{column}") FROM "{table}"')
		try:
			return self.cursor.fetchone()[0]
		except:
			return None
		
	def get_printable(self, table, column):
		'''Return non printable type, quotes or no quotes'''
		tp = self.get_type(table, column).upper()
		if tp in self.NO_QUOTE_TYPES:
			return ''
		if tp in self.IGNORED_TYPES:
			return tp.upper()
		return '"'

	def list_tables(self):
		'''List tables with column names from scheme'''
		for table in self.get_tables():
			yield table, self.get_columns(table)

	def fetch_table(self, table, column=None, columns=None, where=None):
		'''Fetch one table row by row'''
		if column and columns:
			raise ValueError('Argument "column=" or "columns=" is possible, not both')
		cmd = 'SELECT '
		if column:
			cmd += f'"{column}"'
		elif columns:
			cmd += ', '.join(f'"{column}"' for column in columns)
		else:
			cmd += '*'
		cmd += f' FROM "{table}"'
		if where:
			cmd += f' WHERE {where}'
		if column:
			for row in self.cursor.execute(cmd):
				yield row[0]
		else:
			for row in self.cursor.execute(cmd):
				yield row




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
		self.log.info('Done', echo=True)
		reader.close()
		self.log.close()

	def schema(self):
		'''Get database schema'''
		self.start_log()
		self.log.info('Write database schema to text/CSV file')
		reader = SQLiteReader(self.db_path)
		with self.outdir.joinpath(f'{self.filename}_schema.txt').open(mode='w', encoding='utf-8') as fh:
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
		'''Rey to execute SQL statement, return Exception or None for success'''
		self._cursor.execute(statement)

	def try_execute(self, statement):
		'''Rey to execute SQL statement, return Exception or None for success'''
		try:
			self.execute(statement)
		except Exception as ex:
			return ex
		return

class Workers:
	'''Do the work'''

	@staticmethod
	def command(db_path, statement):
		'''Execute given SQL statements'''
		db = SqliteDb(db_path)
		db.execute(statement)
		db.commit()
		db.close()

	@staticmethod
	def execute(db_path, sql_path):
		'''Execute SQL statements from file'''
		db = SqliteDb(db_path)
		for statement in SqlFile(sql_path).read():
			print(statement)
			if ex := db.try_execute(statement):
				print(type(ex), ex)
		db.commit()
		db.close()
		



if __name__ == '__main__':	# start here if called as application
		arg_parser = ArgumentParser(description=__description__)

		arg_parser.add_argument('-c', '--command', type=str,
			help='Execute SQL statements and apply to database', metavar='SQL STATEMENT'
		)
		arg_parser.add_argument('-f', '--file', type=Path,
			help='Execute SQL statements from file and apply to database', metavar='SQL FILE'
		)


		arg_parser.add_argument('db', nargs=1, type=Path,
			help='Database file', metavar='FILE'
		)
		args = arg_parser.parse_args()
		if args.command:
			Workers.command(args.db[0], args.command)
		if args.file:
			Workers.execute(args.db[0], args.execute)
		

