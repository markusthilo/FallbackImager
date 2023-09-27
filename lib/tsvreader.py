#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .extpath import ExtPath

class TsvReader:
	'''Read TSV files UTF-8 or UTF-16'''

	def __init__(self, path, column=None, nohead=False):
		'''Read first line and detetct dencoding'''
		self.path = path
		self.encoding, self.head = ExtPath.read_utf_head(self.path, after=0)
		self.head = self.head.strip()
		self.nohead = nohead
		self.columns = self.head.split('\t')
		self.columns_len = len(self.columns)
		if not column:
			column = 1
		if self.columns_len == 1:
			self.column = 0
		else:
			try:
				self.column = int(column)-1
			except ValueError:
				if self.nohead:
					self.column = -1
				else:
					for self.column, col_str in enumerate(self.columns):
						if col_str == column:
							break
			else:
				if self.column > self.columns_len:
					self.column = -1
		if self.nohead:
			self.head = None
			self.columns = None
		self.errors = list()

	def read_lines(self):
		'''Read line by line and decode'''
		with self.path.open('r', encoding=self.encoding) as fh:
			if not self.nohead:
				fh.readline()
			for line in fh:
				stripped_line = line.rstrip('\n')
				columns = stripped_line.split('\t')
				while len(columns) < self.columns_len:
					stripped_line += ' ' + next(fh).rstrip('\n')
					columns = stripped_line.split('\t')
				try:
					yield columns[self.column], stripped_line
				except:
					self.errors.append(line)
