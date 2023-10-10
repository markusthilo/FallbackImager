#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlite3 import connect as SqliteConnect

class SQLiteExec:
	'''Execute statements'''

	QUOTES = '\'"'

	def __init__(self, sqlite_path, echo=print):
		'''Open database'''
		self.db = SqliteConnect(sqlite_path)
		self.cursor = self.db.cursor()
		self.echo = echo

	def read_file(self, statements_path):
		'''Read statements from file (.sql)'''
		statement = ''
		inside_quotes = None
		with statements_path.open(encoding='utf-8') as fh:
			for line in fh:
				for char in line:
					if char == '\n':
						continue
					statement += char
					if char == inside_quotes:
						inside_quotes = None
						continue
					if inside_quotes:
						continue
					if char in self.QUOTES:
						inside_quotes = char
						continue
					if char == ';' and not inside_quotes:
						yield statement
						statement = ''

	def alter(self, statements_path):
		'''Change data base'''
		if self.echo == print:
			print('1', end='')
			for cnt, statement in enumerate(self.read_file(statements_path), start=1):
				self.cursor.execute(statement)
				if cnt % 10000 == 0:
					print(f'\r{cnt}', end='')
					self.db.commit()
			print('\r', end='')
		else:
			self.echo('1')
			for cnt, statement in enumerate(self.read_file(statements_path), start=1):	
				self.cursor.execute(statement)
				if cnt % 10000 == 0:
					self.echo(cnt, overwrite=True)
					self.db.commit()
		self.db.commit()  
		self.db.close()
		return cnt

class SQLiteReader:
	'''Read SQLite files'''

	def __init__(self, sqlite_path):
		'''Open database'''
		self.db = SqliteConnect(sqlite_path)
		self.cursor = self.db.cursor()

	def list_tables(self):
		'''List tables from scheme'''
		self.cursor.execute("SELECT name FROM sqlite_schema WHERE type = 'table';")
		for table in self.cursor.fetchall():
			self.cursor.execute(f"SELECT name FROM PRAGMA_TABLE_INFO('{table[0]}');")
			rows = (des[0] for des in self.cursor.fetchall())
			yield table[0], rows

	def fetch_table(self, table, fields, where=None):
		'''Fetch one table row by row'''
		cmd = 'SELECT '
		if isinstance(fields, str):
			cmd += f'"{fields}"'
		else:
			cmd += ', '.join(f'"{field}"' for field in fields)
		cmd += f' FROM "{table}"'
		if where:
			cmd += f' WHERE "{where[0]}"='
			cmd += f"'{where[1]}'"
		if isinstance(fields, str):
			for row in self.cursor.execute(cmd):
				yield row[0]
		else:
			for row in self.cursor.execute(cmd):
				yield row

	def close(self):
		'Close SQLite database'
		self.db.close()
