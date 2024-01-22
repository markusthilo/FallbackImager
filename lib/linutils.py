#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from subprocess import run
from json import loads

class LinUtils:
	'Use command line tools'

	@staticmethod
	def lsdisk():
		'''Use lsblk with JSON output to get disks'''
		return [dev['path'] for dev in loads(run(['lsblk', '--json', '-o', 'PATH,TYPE'],
			capture_output=True, text=True).stdout)['blockdevices']
			if dev['type'] == 'disk' and not dev['path'].startswith('/dev/zram')
		]

	@staticmethod
	def lspart(dev):
		'''Use lsblk with JSON output to get partitions'''
		return [(dev['path'], dev['label'], dev['size'], dev['mountpoints'])
			for dev in loads(run(['lsblk', '--json', '-o', 'PATH,LABEL,TYPE,SIZE,MOUNTPOINTS', f'{dev}'],
				capture_output=True, text=True).stdout)['blockdevices']
				if dev['type'] == 'part'
		]

	@staticmethod
	def diskinfo():
		'''Use lsblk with JSON output to get infos about disks'''
		return {dev['path']: (dev['label'], dev['size'], dev['mountpoints'], LinUtils.lspart(dev['path']))
			for dev in loads(run(['lsblk', '--json', '-o', 'PATH,LABEL,TYPE,SIZE,MOUNTPOINTS'],
				capture_output=True, text=True).stdout)['blockdevices']
				if dev['type'] == 'disk'  and not dev['path'].startswith('/dev/zram')
		}

	@staticmethod
	def blkdevsize(dev):
		'''Use lsblk with JSON output to get disk ort partition size'''
		return int(loads(run(['lsblk', '--json', '-o', 'SIZE', '-b', f'{dev}'],
				capture_output=True, text=True).stdout)['blockdevices'][0]['size'])

	@staticmethod
	def init_dev(dev, mbr=False, fs='ntfs'):
		'''Create partition table a one big partition'''
		if mbr:
			cmd = 'label: dos\n'
			if fs.lower() == 'fat32':
				cmd += ',,0c\n'
			elif fs.lower() in ('ntfs', 'exfat'):
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
		return run(['mount', f'{dev}', f'{target}'], capture_output=True, text=True).stderr

	@staticmethod
	def umount(target):
		'''Use umount'''
		run(['sync'], check=True)
		return run(['umount', f'{target}'], capture_output=True, text=True).stderr




