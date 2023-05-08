#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-07'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Generate timestamp'

from datetime import datetime

class TimeStamp:

	@staticmethod
	def now():
		'''Return timestamp with blank inbetween date and time'''
		return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
