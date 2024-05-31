#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.5.1_2024-05-31'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Use PyInstaller to build FallbackImager release
'''

from pathlib import Path
from shutil import rmtree
from sys import argv
from argparse import ArgumentParser
import PyInstaller.__main__

class MkBin:
	'''Use PyInstaller to build executable binary files'''

	def __init__(self, pyfile):
		'''Build standalone executable'''
		self.py_path = Path.cwd()/pyfile
		args = [pyfile, '--onefile', '--icon', 'appicon.ico']
		PyInstaller.__main__.run(args)
		self.bin_path = Path.cwd()/'dist'/self.py_path.stem

	def move(self, tobin=False):
		'''Move executable to destination directory and clean up'''
		dir_path = Path.cwd()
		if tobin:
			dir_path = dir_path/'bin'
		self.bin_path = self.bin_path.replace(dir_path/self.bin_path.name)
		rmtree('build')
		rmtree('dist')
		self.py_path.with_suffix('.spec').unlink()
		return self.bin_path

if __name__ == '__main__':	# start here if called as application
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('-c', '--cli', action='store_true', help='CLI tools')
	argparser.add_argument('-g', '--gui', action='store_true', help='GUI tool FallbackImager')
	argparser.add_argument('additional', nargs='?', type=Path,
		help='Additional Python files to compile', metavar='FILE'
	)
	args = argparser.parse_args()
	bins = list()
	if args.cli:
		bins.append(MkBin('axchecker.py').move())
		bins.append(MkBin('ewfchecker.py').move())
		bins.append(MkBin('ewfimager.py').move())
		bins.append(MkBin('reporter.py').move())
		bins.append(MkBin('sqlite.py').move())
		bins.append(MkBin('wiper.py').move())
		bins.append(MkBin('zipimager.py').move())
		bins.append(MkBin('hashedcopy.py').move())
	if args.gui or len(argv) == 1:
		bins.append(MkBin('FallbackImager.py').move())
	if bins:
		print('\nBuild:')
		for path in bins:
			print(f'{path}')
	else:
		raise RuntimeError('No executables were generated')

