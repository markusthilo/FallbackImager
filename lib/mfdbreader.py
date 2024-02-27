#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .sqliteutils import SQLiteReader

class MfdbReader(SQLiteReader):
	'''Extend SqliteReader for AXIOM data base'''

	def read_paths(self):
		'''Read table source_path and get source_type from table source'''
		self.types = {int(source_id): source_type
			for source_id, source_type
			in self.fetch_table('source', columns=('source_id', 'source_type'))
		}
		self.paths = dict()
		self.file_ids = set()	# files to compare with hits
		self.root_ids = set()	# potential root path to compare
		for source_id, source_path in self.fetch_table('source_path',
			columns=('source_id', 'source_path')):
			source_id_int = int(source_id)
			source_type = self.types[source_id]
			self.paths[source_id_int] = (source_type, source_path)
			if self.types[source_id_int] == 'File':
				self.file_ids.add(source_id_int)
			elif self.types[source_id_int] in ('Folder', 'Partition', 'Volume', 'Image'):
				self.root_ids.add(source_id_int)
			yield source_id_int, source_type, source_path

	def get_hit_ids(self):
		'''Get hits'''
		self.hit_ids = {source_id
			for source_id
			in self.fetch_table('hit_location', column='hit_location_id')}
		return self.hit_ids

	def read_roots(self, max_depth=2):
		'''Read potential root paths to compare'''
		for source_id, source_type, source_path in self.read_paths():
			if source_id in self.root_ids and source_path.count('\\') < max_depth:
				yield source_id, source_type, source_path
