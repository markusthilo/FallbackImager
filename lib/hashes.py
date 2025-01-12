#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hashlib import file_digest
from multiprocessing import Pool, cpu_count

class FileHashes:
	'''Calculate hashes of file in parallel'''

	@staticmethod
	def hashsum(path, algorithm='md5'):
		'''Calculate hash of file'''
		if path.is_file():
			with path.open('rb', buffering=0) as fh:
				return path, file_digest(fh, algorithm).hexdigest()
		else:
			return path, ''

	def __init__(self, paths, algorithm='md5', parallel=50):
		'''Generate object to calculate hashes of files using multiprocessing pool'''
		self._paths = paths
		self._alg = algorithm
		self._parallel = parallel

	def _sum(self, path):
		'''Calculate hash of file'''
		return self.hashsum(path, algorithm=self._alg)

	def calculate(self):
		'''Calculate all hashes in parallel'''
		with Pool(processes=max(1, int(cpu_count() * self._parallel / 100))) as pool:
			return dict(pool.map(self.hashsum, (path for path in self._paths)))

