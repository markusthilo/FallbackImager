#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.5.2_2024-06-10'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Use PyInstaller to build FallbackImager Windows Release
'''

from os import name as __os_name__
if __os_name__ != 'nt':
	raise EnvironmentError('Run on Windows (>=10)!')
from pathlib import Path
from shutil import rmtree
from sys import argv
from argparse import ArgumentParser
import PyInstaller.__main__


class MkExe:
	'''Use PyInstaller to build Windows executable'''

	def __init__(self, pyfile, noconsole=False, admin=False):
		'''Build standalone executable'''
		self.py_path = Path.cwd()/pyfile
		args = [pyfile, '--onefile', '--icon', 'appicon.ico']
		if noconsole:
			args.append('--noconsole')
		if admin:
			args.append('--uac-admin')
		PyInstaller.__main__.run(args)
		self.exe_path = Path.cwd()/'dist'/f'{self.py_path.stem}.exe'

	def move(self, to_bin=False):
		'''Move executable to destination directory and clean up'''
		dir_path = Path.cwd()/'dist-win'
		dir_path.mkdir(exist_ok=True)
		if to_bin:
			dir_path = dir_path/'bin'
			dir_path.mkdir(exist_ok=True)
		self.exe_path = self.exe_path.replace(dir_path/self.exe_path.name)
		rmtree('build', ignore_errors=True)
		rmtree('dist', ignore_errors=True)
		self.py_path.with_suffix('.spec').unlink(missing_ok=True)
		return self.exe_path

if __name__ == '__main__':	# start here if called as application
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('-c', '--cli', action='store_true', help='CLI tools')
	argparser.add_argument('-g', '--gui', action='store_true', help='GUI tool FallbackImager')
	argparser.add_argument('-w', '--wim', action='store_true', help='GUI tool WimMount')
	argparser.add_argument('additional', nargs='?', type=Path,
		help='Additional Python files to compile', metavar='FILE'
	)
	args = argparser.parse_args()
	exes = list()
	if args.cli or len(argv) == 1:
		exes.append(MkExe('axchecker.py').move())
		exes.append(MkExe('dismimager.py', admin=True).move())
		exes.append(MkExe('oscdimager.py').move())
		exes.append(MkExe('sqlite.py').move())
		exes.append(MkExe('wipew.py', admin=True).move())
		exes.append(MkExe('zipimager.py').move())
		exes.append(MkExe('hashedcopy.py').move())
		exes.append(MkExe('reporter.py').move())
	if args.gui or len(argv) == 1:
		exes.append(MkExe('fallbackimager.py', admin=True, noconsole=True).move())
	if args.wim or len(argv) == 1:
		exes.append(MkExe('wimmount.py', admin=True, noconsole=True).move(to_bin=True))
	if exes:
		print('\nBuild:')
		for path in exes:
			print(f'{path}')
	else:
		raise RuntimeError('No executables were generated')

