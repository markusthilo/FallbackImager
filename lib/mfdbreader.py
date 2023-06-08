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
		self.re_filename = re_compile(' (\([^\)]*\) )|([ *.;:#"/\\\])')

	def get_partitions(self):
		'''One string for each partition'''
		for source_id, (image, partition) in self.partitions.items():
			yield source_id, f'{image} - {partition}'

	def fetch_paths(self):
		'''Read all needed data from case file'''
		self.paths = {source_id: source_path
			for source_id, source_path in self.fetch_table('source_path',
				fields = ('source_id', 'source_path')
			)
		}
		self.short_paths = dict()
		for partition_id, partition in self.get_partitions():
			part_len = len(partition)
			for source_id, path in self.paths.items():
				if len(path) > part_len and path[:part_len] == partition:
					self.short_paths[source_id] = (
						partition_id,
						path[:part_len],
						path[part_len:]
					)
		self.file_ids = {source_id for source_id in self.fetch_table('source',
				fields = 'source_id',
				where = ('source_type', 'File')
			)
		}
		self.folder_ids = {source_id for source_id in self.fetch_table('source',
				fields = 'source_id',
				where = ('source_type', 'Folder')
			)
		}
		self.hit_ids = {source_id for source_id in self.fetch_table('hit_location',
				fields = 'source_id'
			)
		}
		self.ignored_file_ids = self.file_ids-self.hit_ids

	def get_partition_fnames(self):
		'''One string that would work as file name for each partition'''
		for source_id, partition in self.get_partitions():
			yield source_id, self.re_filename.sub('_', partition)

	def normalized_path(self, source_id):
		'''Return a normalized path'''
		return self.short_paths[source_id][2].replace('\\', '/').strip('/')
