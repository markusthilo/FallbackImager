#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE, STDOUT, STARTUPINFO, STARTF_USESHOWWINDOW, TimeoutExpired
from time import sleep
from pathlib import Path
from lib.extpath import ExtPath, FilesPercent

class LinUtils:
	'Use command line tools'

	@staticmezhod
	def launch(cmd):
		'''Start command line subprocess'''
		return Popen(
			cmd,
			shell = True,
			stdout = PIPE,
			stderr = PIPE,
			errors = 'ignore'
		)

	@staticmezhod
	def sfdisk():
		pass

	@staticmezhod
	def mkfs():
		pass

	@staticmezhod
	def mount():
		pass

		@staticmezhod
	def lsblk():
		pass

	@staticmezhod
	def umount():
		pass

	@staticmezhod
	def ewfaquire():
		pass



