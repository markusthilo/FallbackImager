#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlite3 import connect as SqliteConnect
from re import compile as re_compile

class SQLiteReader:
	'''Read SQLite files'''

	def __init__(self, sqlite_path):
		'''Open database'''
		self.db = SqliteConnect(sqlite_path)
		self.cursor = self.db.cursor()

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

class MfdbReader(SQLiteReader):
	'''Extend SqliteReader for AXIOM data base'''

	def __init__(self, mfdb):
		'''Read what you need from Case.mfdb'''
		super().__init__(mfdb)
		self.paths = {source_id: source_path
			for source_id, source_path in self.fetch_table('source_path',
				fields = ('source_id', 'source_path')
			)
		}
		self.types = {source_id: source_type
			for source_id, source_type in self.fetch_table('source',
				fields = ('source_id', 'source_type')
			)
		}
		self.partitions = {source_id: self.paths[source_id]
			for source_id, source_type in self.types.items()
			if source_type == 'Partition'
		}
		self.files = {source_id: self.paths[source_id]
			for source_id, source_type in self.types.items()
			if source_type == 'File'
		}
		self.hits = {source_id: self.paths[source_id]
			for source_id in self.fetch_table('hit_location', fields = 'source_id')
		}

	def get_files_of_partition(self, partition):
		'''Get hits in files'''
		len_partition = len(partition)
		return {source_id: self.paths[source_id]
			for source_id, source_path in self.files.items()
			if source_path[:len_partition] == partition
		}

	def get_no_hit_files(self):
		'''Get hits in files'''
		return {source_id: self.paths[source_id]
			for source_id in self.files
			if not source_id in self.hits
		}
