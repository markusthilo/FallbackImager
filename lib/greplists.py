#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .reglist import RegList

class GrepLists:
	'''Grep by blacklist or whitelist'''

	@staticmethod
	def false(*args):
		'''Dummy returning False'''
		return False

	def __init__(self, blacklist=None, whitelist=None, echo=None):
		'''Load lists'''
		self.blacklist = RegList(blacklist)
		self.whitelist = RegList(whitelist)

	def get_method(self):
		'''Deliver the method to check if path has to be dropped'''
		if self.whitelist.regs:
			if echo:
				echo(f'Using whitelist {whitelist}')
			return self._not_whitelist
		if self.blacklist.regs:
			if echo:
				echo(f'Using blacklist {blacklist}')
			return self._in_blacklist
		else:
			return self.false
		
	def _in_blacklist(self, string):
		'''Return True if has match in blacklist'''
		return self.blacklist.is_match(string)

	def _not_whitelist(self, string):
		'''Return True if string is not in whitelist'''
		return not self.whitelist.is_match(string)
