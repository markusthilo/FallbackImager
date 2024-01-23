#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class StringUtils:
	'Functions (okay, still called methods) to handle and build strings'

	@staticmethod
	def join(iterable, delimiter=' '):
		'''Join iterable to list but be telerant'''
		return delimiter.join([f'{item}' for item in iterable if item])
