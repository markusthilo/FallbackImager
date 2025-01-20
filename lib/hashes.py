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

	@staticmethod
	def _hashsum(path_algorithm):
		'''Calculate hash of file, one parameter to use with multiprocessing.pool'''
		path, algorithm = path_algorithm
		return path, FileHashes.hashsum(path, algorithm=algorithm)

	def __init__(self, paths, algorithm='md5', parallel=50):
		'''Generate object to calculate hashes of files using multiprocessing pool'''
		self._paths = paths
		self._alg = algorithm
		self._parallel = max(1, int(cpu_count() * parallel / 100))	# max processes in percent of cores

	def calculate(self):
		'''Calculate all hashes in parallel'''
		with Pool(processes=self._parallel) as pool:
			return dict(pool.map(self.hashsum, ((path, self._alg) for path in self._paths)))

