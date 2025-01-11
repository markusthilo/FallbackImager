#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hashlib import file_digest
from multiprocessing import Pool, cpu_count

class FileHashes:
	'''Calculate hashes of file in parallel'''

	@staticmethod
	def hashsum(path, fn='md5'):
		'''Calculate hash of file'''
		if path.is_file():
			with path.open('rb', buffering=0) as fh:
				return path, file_digest(fh, fn).hexdigest()
		else:
			return path, ''

	def __init__(self, paths, fn='md5', parallel=50):
		'''Generate object to calculate hashes of files using multiprocessing pool'''
		self.paths = paths
		self.fn = fn
		self.pool = Pool(processes=max(1, int(cpu_count() * parallel / 100)))

	#def _sum(self, path):
	#	'''Calculate hash of file'''
	#	return self.hashsum(path, fn=self.fn)

	def calculate(self):
		'''Calculate all hashes in parallel'''
		return dict(self.pool.map(self.hashsum, (path for path in self.paths)))

	def __del__(self):
		'''Cleanup pool resources'''
		if hasattr(self, 'pool'):
			self.pool.close()
			self.pool.join()
