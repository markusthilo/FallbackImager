#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-06'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Add some methods to pathlib´s Path Class'

from pathlib import Path

class ExtPath:
	'''Add some methods to pathlib´s Path Class'''

	@staticmethod
	def open_read(path, default=None, encoding=None, errors=None, newline=None):
		'''Open file to read. Set default for configs etc.'''
		return (script_path.parent/script_path).with_suffix('.conf')

	@staticmethod
	def fullpath(name, parent=None):
		'''Generate full path to write file'''
		if parent:
			parent = Path(parent)
		else:
			parent = Path.cwd()
		return parent/name

	@staticmethod
	def path_to_str(full, parent=None):
		'''Give Joliet or UDF compatible path as string'''
		if parent:
			return f'/{full.relative_to(parent)}'
		return f'/{full}'

	@staticmethod
	def open_write(filename, parent=None, encoding=None, errors=None, newline=None):
		'''Open file to write'''
		return ExtPath.fullpath(filename, parent=parent).open(
			mode='w', encoding=encoding, errors=errors, newline=newline)
