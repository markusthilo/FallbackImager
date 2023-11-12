#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__	=	'Markus Thilo'
__license__	=	'GPL-3'
__email__	=	'markus.thilo@gmail.com'

import PyInstaller.__main__
from shutil import move, rmtree
from os import remove

### axchecker.py ###
PyInstaller.__main__.run([
	'axchecker.py',
	'--onefile',
	'--icon', 'appicon.ico'
])
move('dist/axchecker.exe', 'axchecker.exe')
rmtree('build')
rmtree('dist')
remove('axchecker.spec')

### dismimager.py ###
PyInstaller.__main__.run([
	'dismimager.py',
	'--onefile',
	'--uac-admin',
	'--icon', 'appicon.ico'
])
move('dist/dismimager.exe', 'dismimager.exe')
rmtree('build')
rmtree('dist')
remove('dismimager.spec')

### hdzero.py ###
PyInstaller.__main__.run([
	'hdzero.py',
	'--onefile',
	'--uac-admin',
	'--icon', 'appicon.ico'
])
move('dist/hdzero.exe', 'hdzero.exe')
rmtree('build')
rmtree('dist')
remove('hdzero.spec')

### isoverify.py ###
PyInstaller.__main__.run([
	'isoverify.py',
	'--onefile',
	'--icon', 'appicon.ico'
])
move('dist/isoverify.exe', 'isoverify.exe')
rmtree('build')
rmtree('dist')
remove('isoverify.spec')

### mkisoimager.py ###
PyInstaller.__main__.run([
	'mkisoimager.py',
	'--onefile',
	'--icon', 'appicon.ico'
])
move('dist/mkisoimager.exe', 'mkisoimager.exe')
rmtree('build')
rmtree('dist')
remove('mkisoimager.spec')

### oscdimager.py ###
PyInstaller.__main__.run([
	'oscdimager.py',
	'--onefile',
	'--icon', 'appicon.ico'
])
move('dist/oscdimager.exe', 'oscdimager.exe')
rmtree('build')
rmtree('dist')
remove('oscdimager.spec')

### sqlite.py ###
PyInstaller.__main__.run([
	'sqlite.py',
	'--onefile',
	'--icon', 'appicon.ico'
])
move('dist/sqlite.exe', 'sqlite.exe')
rmtree('build')
rmtree('dist')
remove('sqlite.spec')

### zipimager.py ###
PyInstaller.__main__.run([
	'zipimager.py',
	'--onefile',
	'--icon', 'appicon.ico'
])
move('dist/zipimager.exe', 'zipimager.exe')
rmtree('build')
rmtree('dist')
remove('zipimager.spec')
