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
		ret = run(cmd, capture_output=True, text=True)
		return loads(ret.stdout)['blockdevices'], ret.stderr

	@staticmethod
	def init_dev(dev, mbr=False, fs='ntfs'):
		'''Create partition table a one big partition'''
		if mbr:
			cmd = 'label: dos\n'
			if fs.lower() == 'fat32':
				cmd += ',,0c\n'
			elif fs.lower in ('ntfs', 'exfat'):
				cmd += ',,07\n'
			else:
				cmd += ',,83\n'
		else:
			cmd = 'label: gpt\n'
			if fs.lower() in ('ntfs', 'exfat','fat32'):
				cmd += ',,EBD0A0A2-B9E5-4433-87C0-68B6B72699C7\n'
			else:
				cmd += ',,,\n'
		ret = run(['sfdisk', f'{dev}'], capture_output=True, text=True, input=cmd)
		return ret.stdout, ret.stderr

	@staticmethod
	def mkfs(dev, fs='ntfs', label='Volume'):
		'''Make file system'''
		cmd = ['mkfs', '-t']
		if fs.lower() == 'fat32':
			cmd.extend(['vfat', '-n'])
		elif fs.lower() == 'ntfs':
			cmd.extend(['ntfs', '-f', '-L'])
		else:
			cmd.extend([fs.lower(), '-L'])
		cmd.extend([f'{label}', f'{dev}'])
		ret = run(cmd, capture_output=True, text=True)
		return ret.stdout, ret.stderr

	@staticmethod
	def mount(dev, target):
		'''Use mount'''
		ret = run(['mount', f'{dev}', f'{target}'], capture_output=True, text=True)
		return ret.stdout, ret.stderr

	@staticmethod
	def umount(target):
		'''Use umount'''
		run(['sync'], check=True)
		ret = run(['umount', f'{target}'], capture_output=True, text=True)
		return ret.stdout, ret.stderr




