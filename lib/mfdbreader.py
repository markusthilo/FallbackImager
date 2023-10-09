#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .sqliteutils import SQLiteReader

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
