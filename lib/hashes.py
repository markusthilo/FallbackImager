#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hashlib import file_digest
from threading import Thread

class FileHashes:
	'''Calculate hashes of files'''

	@staticmethod
	def hashsum(path, algorithm='md5'):
		'''Calculate hash of one file'''
		if path.is_file():
			with path.open('rb') as fh:
				return file_digest(fh, algorithm).hexdigest()
		else:
			return ''

class HashThread(Thread):
	'''Calculate hashes of files in thread'''

	def __init__(self, paths, algorithms=['md5']):
		'''Generate object to calculate hashes of files using multiprocessing pool'''
		super().__init__()
		self._paths = paths
		self._algs = algorithms

	def run(self):
		'''Calculate all hashes (multiple algorithms) in parallel - this method launches the worker'''
		self.hashes = {path: dict() for path in self._paths}
		for alg in self._algs:
			for path in self._paths:
				self.hashes[path][alg] = FileHashes.hashsum(path, algorithm=alg)
