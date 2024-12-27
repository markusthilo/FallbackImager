#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.5.3_2024-12-27'
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
from shutil import rmtree, copy
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

	def move(self, dir_path):
		'''Move executable to destination directory and clean up'''
		try:
			self.exe_path = self.exe_path.replace(dir_path/self.exe_path.name)
		except:
			return
		rmtree(Path.cwd()/'build', ignore_errors=True)
		rmtree(Path.cwd()/'dist', ignore_errors=True)
		self.py_path.with_suffix('.spec').unlink(missing_ok=True)
		return self.exe_path

if __name__ == '__main__':	# start here if called as application
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('-c', '--cli', action='store_true', help='CLI tools')
	argparser.add_argument('-d', '--debug', action='store_true', help='Make executable to debug')
	argparser.add_argument('-g', '--gui', action='store_true', help='GUI tool FallbackImager')
	argparser.add_argument('-w', '--wim', action='store_true', help='GUI tool WimMount')
	argparser.add_argument('additional', nargs='?', type=Path,
		help='Additional Python files to compile', metavar='FILE'
	)
	args = argparser.parse_args()
	exes = list()
	dist_path = Path.cwd()/'dist-win'
	dist_path.mkdir(exist_ok=True)
	if not args.cli and not args.gui and not args.wim:
		make_all = True
	else:
		make_all = False
	copy('README.md', dist_path)
	copy('LICENSE', dist_path)
	copy('help.txt', dist_path)
	copy('reporter-example-template.txt', dist_path)
	copy('wipe-log-head.txt', dist_path)
	if args.cli or make_all:
		exes.append(MkExe('axchecker.py').move(dist_path))
		exes.append(MkExe('dismimager.py', admin=True).move(dist_path))
		exes.append(MkExe('oscdimager.py').move(dist_path))
		exes.append(MkExe('sqlite.py').move(dist_path))
		exes.append(MkExe('wipew.py', admin=True).move(dist_path))
		exes.append(MkExe('zipimager.py').move(dist_path))
		exes.append(MkExe('hashedcopy.py').move(dist_path))
		exes.append(MkExe('reporter.py').move(dist_path))
	if args.gui or make_all:
		if args.debug:
			exes.append(MkExe('fallbackimager.py').move(dist_path))
		else:
			exes.append(MkExe('fallbackimager.py', admin=True, noconsole=True).move(dist_path))
		copy('appicon.png', dist_path)
	if args.wim or make_all:
		exes.append(MkExe('wimmount.py', admin=True, noconsole=True).move(dist_path))
	if exes:
		print('\nBuild:')
		for path in exes:
			print(f'{path}')
	else:
		raise RuntimeError('No executables were generated')

