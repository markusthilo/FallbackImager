#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hashlib import md5, sha256

class FileHashes:
	'''Calculate MD5 and SHA256 from file (as pathlib.Path)'''

	BLOCK_SIZE = max(md5().block_size, sha256().block_size) * 1024

	def __init__(self, path):
		'''Shut up and calculate'''
		self.md5 = md5()
		self.sha256 = sha256()
		with path.open('rb') as fh:
			while True:
				block = fh.read(self.BLOCK_SIZE)
				if not block:
					break
				self.md5.update(block)
				self.sha256.update(block)
		self.md5 = self.md5.hexdigest()
		self.sha256 = self.sha256.hexdigest()

	def __repr__(self):
		'''Representation for logs etc.'''
		return f'md5: {self.md5}\nsha256: {self.sha256}'

class CopyFile(FileHashes):
	'''Copy one file (as pathlib.Path) and calculate hashes'''

	def __init__(self, src, dst):
		'''Copy source file to destination'''
		self.md5 = md5()
		self.sha256 = sha256()
		with src.open('rb') as sfh, dst.open('wb') as dfh:
			while True:
				block = sfh.read(self.BLOCK_SIZE)
				if not block:
					break
				dfh.write(block)
				self.md5.update(block)
				self.sha256.update(block)
		self.md5 = self.md5.hexdigest()
		self.sha256 = self.sha256.hexdigest()