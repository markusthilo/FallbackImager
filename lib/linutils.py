#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from subprocess import run
from json import loads

class LinUtils:
	'Use command line tools'

	@staticmethod
	def lsblk(dev=None):
		'''Use lsblk with JSON output'''
		cmd = ['lsblk', '--json', '-o', 'PATH,LABEL,SIZE,TYPE,FSTYPE,MOUNTPOINTS']
		if dev:
			cmd.append(dev)
		return loads(run(cmd, capture_output=True, text=True).stdout)['blockdevices']

	@staticmethod
	def init_dev(dev, mbr=False, fs='ntfs'):
		'''Create partition table a one big partition'''
		if mbr:
			label = 'dos'
			try:
				pt = {'ntfs': '07', 'exfat': '07', 'fat32': '0b'}[fs.lower()]
			except KeyError:
				pt = '83'
		else:
			label = 'gpt'
			if fs.lower() in ('ntfs', 'exfat','fat32'):
				pr = '11'
			else:
				pt = '20'
		return run(['sfdisk', dev], capture_output=True, text=True,
			input=f'label: {label}\n,,{pt},-\n')

	@staticmethod
	def mkfs(dev, fs='ntfs', label='Volume'):
		'''Make file system'''
		cmd = ['mkfs', '-t']
		if fs == 'fat32':
			cmd.extend(['vfat', '-n'])
		else:
			cmd.extend([fs, '-L'])
		cmd.extend([label, dev])
		return run(cmd, capture_output=True, text=True)

	@staticmethod
	def mount():
		pass

	@staticmethod
	def umount():
		pass




