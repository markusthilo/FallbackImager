#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-08'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Blacklist and whiteliste'

from .reglist import RegList

class GrepLists:
	'''Grep by blacklist or whitelist'''

	def __init__(self, blacklist=None, whitelist=None, echo=print):
		'''Load lists'''
		self.blacklist = RegList(blacklist)
		self.whitelist = RegList(whitelist)
		if self.whitelist.regs:
			self.to_store = self._is_in_whitelist
			self.echo(f'Using whitelist {whitelist}')
		else:
			self.to_store = self._not_in_blacklist
			if self.blacklist.regs:
				self.echo(f'Using blacklist {blacklist}')

	def _not_in_blacklist(self, posix_str):
		'''Return True when path is blacklisted'''
		return not self.blacklist.is_match(posix_str.strip('/'))

	def _is_in_whitelist(self, posix_str):
		'''Return True when path is not in whitelist'''
		return self.whitelist.is_match(posix_str.strip('/'))