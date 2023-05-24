#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-24'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Read AXIOM case files'

from sqlite3 import connect as SqliteConnect

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
		self.images = {source_id: source_friendly_value
			for source_id, source_friendly_value in self.fetch_table('source',
				fields = ('source_id', 'source_friendly_value'),
				where = ('source_type', 'Image')
			)
		}
		self.partitions = {source_id: (self.images[root_source_id], source_friendly_value)
			for source_id, root_source_id, source_friendly_value in self.fetch_table('source',
				fields = ('source_id', 'root_source_id', 'source_friendly_value'),
				where = ('source_type', 'Partition')
			)
		}

	def fetchall(self):
		'''Read all needed data from case file'''
		self.paths = {source_id: source_path
			for source_id, source_path in self.fetch_table('source_path',
				fields = ('source_id', 'source_path')
			)
		}
		self.files = {source_id: self.paths[source_id]
			for source_id in self.fetch_table('source',
				fields = 'source_id',
				where = ('source_type', 'File')
			)
		}
		self.folders = {source_id: self.paths[source_id]
			for source_id in self.fetch_table('source',
				fields = 'source_id',
				where = ('source_type', 'Folder')
			)
		}
		self.hits = {source_id: self.paths[source_id]
			for source_id in self.fetch_table('hit_location',
				fields = 'source_id'
			)
		}
		self.file_ids = set(self.files)
		self.folder_ids = set(self.folders)
		self.hit_ids = set(self.hits)
		self.id_with_partition = dict()
		self.short_paths = dict()
		self.ignored_file_ids = self.file_ids-self.hit_ids
		for part_path in self.partitions.values():
			part_len = len(part_path)
			for source_id, path in self.paths.items():
				if path.startswith(part_path):
					self.id_with_partition[source_id] = part_path
					self.short_paths[source_id] = path[part_len:]
