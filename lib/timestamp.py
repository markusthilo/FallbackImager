#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime

class TimeStamp:

	@staticmethod
	def now(path_comp=False, no_ms=False):
		'''Return timestamp, path_comp=True will give string to build file names'''
		if path_comp:
			string = datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
		elif no_ms:
			string = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		else:
			string = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
		return string

	@staticmethod
	def now_or(*args):
		'''Return filename compatible TimeStamp.now() or just return argument if None'''
		if len(args) > 0 and args[0]:
			return args[0]
		return TimeStamp.now(path_comp=True)
