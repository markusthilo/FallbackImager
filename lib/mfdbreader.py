#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .sqliteutils import SQLiteReader

class MfdbReader(SQLiteReader):
	'''Extend SqliteReader for AXIOM data base'''

	def __init__(self, mfdb):
		'''Read what you need from Case.mfdb'''
		super().__init__(mfdb)
		self.paths = {int(source_id): source_path
			for source_id, source_path in self.fetch_table('source_path',
				columns = ('source_id', 'source_path')
			)
		}
		self.types = {int(source_id): source_type
			for source_id, source_type in self.fetch_table('source',
				columns = ('source_id', 'source_type')
			)
		}

	def get_partition_ids(self):
		'''Get partitions in case file'''
		self.partition_ids = [source_id
			for source_id, source_type in self.types.items()
			if source_type == 'Partition'
		]
		return self.partition_ids

	def get_hit_ids(self):
		'''Get hits'''		
		self.hit_ids = {source_id for source_id in self.fetch_table('hit_location', column='hit_location_id')}
		return self.hit_ids

	def get_root_ids(self):
		'''Get root images ("Image" / source_id == root_source_id)'''
		self.root_ids = {source_id for source_id in self.fetch_table('source', column='root_source_id')}
		return self.root_ids

	def get_file_ids(self):
		'''Get files ("File" & "Image")'''
		self.get_root_ids()
		self.file_ids = {source_id
			for source_id, source_type in self.types.items()
			if source_type == 'File' or (
				source_type == 'Image' and not source_id in self.root_ids
			)
		}
		return self.file_ids

	def get_partition_name(self, partition):
		'''Get name of given partition'''
		if isinstance(partition, int):
			try:
				return self.paths[self.partition_ids[partition-1]]
			except IndexError:
				return None
		return partition

	def grep_partition(self, partition_name):
		'''Get files ("File" & "Image") for given partition'''
		for path in self.paths.values():
			if path.startswith(partition_name):
				yield path
