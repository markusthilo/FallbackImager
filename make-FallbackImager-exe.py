#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__	=	'Markus Thilo'
__license__	=	'GPL-3'
__email__	=	'markus.thilo@gmail.com'

import PyInstaller.__main__
from shutil import move, rmtree
from os import remove

PyInstaller.__main__.run([
	'FallbackImager.py',
	'--noconsole',
	'--onefile',
	'--uac-admin',
	'--icon', 'appicon.ico'
])
move('dist/FallbackImager.exe', 'FallbackImager.exe')
rmtree('build')
rmtree('dist')
remove('FallbackImager.spec')