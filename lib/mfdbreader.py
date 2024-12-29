#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .sqliteutils import SQLiteReader
from .pathutils import PathUtils

class MfdbReader(SQLiteReader):
	'''Extend SqliteReader for AXIOM data base'''

	def _read_source(self):
		'''Read table source'''
		for source_id, parent_source_id, source_type, source_friendly_value in self.fetch_table('source',
			columns=('source_id', 'parent_source_id', 'source_type', 'source_friendly_value')):
			source_id = int(source_id)
			try:
				parent_source_id = int(parent_source_id)
			except TypeError:
				parent_source_id = None
			yield source_id, parent_source_id, source_type, source_friendly_value

	def _read_paths(self):
		'''Read table source_path'''
		for source_id, source_path in self.fetch_table('source_path',
			columns=('source_id', 'source_path')):
			yield int(source_id), source_path

	def get_types(self):
		'''Read table source and get types'''
		self.types = {int(source_id): source_type
			for source_id, source_type
			in self.fetch_table('source', columns=('source_id', 'source_type'))
		}

	def read_roots(self, max_depth=2):
		'''Read potential root paths to compare'''
		self.get_types()
		for source_id, source_path in self._read_paths():
			source_type = self.types[source_id]
			if source_type != 'File' and source_path.count('\\') < max_depth:
				yield source_id, source_type, source_path

	def read_paths(self):
		'''Read table source_path and get source_type from table source'''
		self.get_types()
		self.paths = dict()
		self.file_ids = set()	# ids of files to compare with hits
		for source_id, source_path in self._read_paths():
			source_type = self.types[source_id]
			self.paths[source_id] = (source_type, source_path)
			if self.types[source_id] == 'File':
				self.file_ids.add(source_id)
			yield source_id, source_type, source_path

	def get_hit_ids(self):
		'''Get hit ids'''
		self.hit_ids = {source_id
			for source_id
			in self.fetch_table('hit_location', column='hit_location_id')}
		return self.hit_ids

	def get_paths(self):
		'''Get paths as dict'''
		self.get_types()
		self.paths = { source_id: (self.types[source_id], source_path)
			for source_id, source_path in self._read_paths()
		}

	def walk(self, root_id):
		'''Recursivly get sub-paths'''
		self.get_paths()
		root_path = f'{self.paths[root_id][1]}\\'
		root_len = len(root_path)
		for source_id, (source_type, source_path) in self.paths.items():
			if source_path.startswith(root_path):
				yield source_id, source_type, source_path[root_len:]

	def get_relative_paths(self, root_id):
		'''Get relative paths under given root'''
		return {PathUtils.normalize(relative_path)
			for source_id, source_type, relative_path in self.walk(root_id)
		}

	def tree(self):
		'''Read table source and give possible roots'''
		for source_id, parent_source_id, source_type, source_friendly_value in self._read_source():
			if source_type != 'File':
				yield source_id, parent_source_id, source_type, source_friendly_value
