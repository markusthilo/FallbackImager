#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .reglist import RegList

class GrepLists:
	'''Grep by blacklist or whitelist'''

	@staticmethod
	def false(*args):
		'''Dummy returning False'''
		return False

	def __init__(self, blacklist=None, whitelist=None):
		'''Load lists'''
		self.blacklist = RegList(blacklist)
		self.whitelist = RegList(whitelist)

	def get_method(self):
		'''Deliver the method to check if path has to be dropped'''
		if self.whitelist.regs:
			return self._in_whitelist
		if self.blacklist.regs:
			return self._not_in_blacklist
		else:
			return self.false
		
	def _not_in_blacklist(self, string):
		'''Return True if has match in blacklist'''
		return not self.blacklist.is_match(string)

	def _in_whitelist(self, string):
		'''Return True if string is not in whitelist'''
		return self.whitelist.is_match(string)
