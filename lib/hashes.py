#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-12'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Build and verify hashes'

from hashlib import md5, sha256

class FileHashes:
	'''Calculate MD5 and SHA256 from file (as pathlib.Path)'''

	def __init__(self, path):
		'''Shut up and calculate'''
		self.path = path
		self.md5 = md5()
		self.sha256 = sha256()
		self.block_size = max(self.md5.block_size, self.sha256.block_size)
		with self.path.open('rb') as fh:
			while True:
				block = fh.read(self.block_size)
				if not block:
					break
				self.md5.update(block)
				self.sha256.update(block)
		self.md5 = self.md5.hexdigest()
		self.sha256 = self.sha256.hexdigest()

	def __repr__(self):
		'''Representation for logs etc.'''
		return f'md5: {self.md5}\nsha256: {self.sha256}'