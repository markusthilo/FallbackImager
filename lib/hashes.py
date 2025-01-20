#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hashlib import file_digest
from multiprocessing import Pool, cpu_count
from threading import Thread

class FileHashes:
	'''Calculate hashes of files'''

	@staticmethod
	def hashsum(path, algorithm='md5'):
		'''Calculate hash of one file'''
		if path.is_file():
			with path.open('rb', buffering=0) as fh:
				return path, file_digest(fh, algorithm).hexdigest()
		else:
			return path, ''

	@staticmethod
	def _hashsum(path_algorithm):
		'''Calculate hash of file (1 arg to use with multiprocessing.pool)'''
		path, algorithm = path_algorithm
		return path, FileHashes.hashsum(path, algorithm=algorithm)

	def __init__(self, paths, algorithm='md5', processes=None):
		'''Generate object to calculate hashes of files using multiprocessing pool'''
		self._paths = paths
		self._alg = algorithm
		self._procs = processes if processes else int(cpu_count() / 2)

	def calculate(self):
		'''Calculate all hashes in parallel'''
		with Pool(processes=self._procs) as pool:
			return pool.map(self._hashsum, ((path, self._alg) for path in self._paths))

class HashThread(Thread):
	'''Calculate hashes of files in thread'''

	def __init__(self, paths, algorithms=['md5'], processes=None):
		'''Generate object to calculate hashes of files using multiprocessing pool'''
		super().__init__()
		self._paths = paths
		self._algs = algorithms
		self._procs = processes

	def run(self):
		'''Calculate all hashes (multiple algorithms) in parallel - this method launches the worker'''
		self.hashes = {path: dict() for path in self._paths}
		for alg in self._algs:
			for path, hash in FileHashes(self._paths, algorithm=alg, processes=self._procs).calculate():
				self.hashes[path][alg] = hash
