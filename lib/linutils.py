#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from subprocess import Popen, PIPE, run
from json import loads
from re import findall
from time import strftime
from .stringutils import StringUtils

class LinUtils:
	'Tools for Linux based systems'

	@staticmethod
	def find_bin(name, parent_path):
		'''Find a binary'''
		for parent in (
			parent_path/'bin',
			parent_path/'dist-lin/bin',
			Path('/usr/bin/'),
			Path('/usr/local/bin/'),
			Path('/opt/FallbackImager/bin')
		):
			bin_path = parent/name
			if bin_path.is_file():
				return bin_path

	@staticmethod
	def set_ro(dev):
		'''Set block device to read only'''
		ret = run(['blockdev', '--setro', f'{dev}'], capture_output=True, text=True)
		return ret.stdout, ret.stderr

	@staticmethod
	def set_rw(dev):
		'''Set block device to read and write access'''
		ret = run(['blockdev', '--setrw', f'{dev}'], capture_output=True, text=True)
		return ret.stdout, ret.stderr

	@staticmethod
	def get_blockdevs():
		'''Use lsblk with JSON output to get block devices'''
		return [
			dev['path'] for dev in loads(run(['lsblk', '--json', '-o', 'PATH'],
				capture_output=True, text=True).stdout)['blockdevices']
		]

	@staticmethod
	def get_disks():
		'''Get type disk except /dev/zram*'''
		return [
			dev['path'] for dev in loads(run(['lsblk', '--json', '-o', 'PATH,TYPE'],
				capture_output=True, text=True).stdout)['blockdevices']
				if dev['type'] == 'disk' and not dev['path'].startswith('/dev/zram')
		]

	@staticmethod
	def get_physical_devs():
		'''Get types part and disk except /dev/zram*'''
		return [
			dev['path'] for dev in loads(run(['lsblk', '--json', '-o', 'PATH,TYPE'],
				capture_output=True, text=True).stdout)['blockdevices']
				if dev['type'] in ('disk', 'part') and not dev['path'].startswith('/dev/zram')
		]

	@staticmethod
	def get_rootdevs():
		'''Get root devices = block devices without partition'''
		return [
			dev['path'] for dev in loads(run(['lsblk', '--json', '-o', 'PATH,TYPE'],
				capture_output=True, text=True).stdout)['blockdevices']
				if dev['type'] != 'part'
		]

	@staticmethod
	def rootdev_of(part):
		'''Root device of given partition'''
		for rootdev in LinUtils.get_rootdevs():
			if part.startswith(rootdev):
				return rootdev

	@staticmethod
	def lspart(dev):
		'''Use lsblk with JSON output to get partitions'''
		return {
			dev['path']: [dev['size'], dev['label']] + dev['mountpoints']
				for dev in loads(run(['lsblk', '--json', '-o', 'PATH,LABEL,TYPE,SIZE,MOUNTPOINTS', f'{dev}'],
					capture_output=True, text=True).stdout)['blockdevices']
					if dev['type'] == 'part'
		}

	@staticmethod
	def is_disk(dev):
		'''Use lsblk with JSON output to check if device is a disk'''
		try:
			return loads(run(['lsblk', '--json', '-o', 'TYPE', f'{dev}'],
					capture_output=True, text=True).stdout)['blockdevices'][0]['type'] == 'disk'
		except IndexError:
			return False

	@staticmethod
	def diskinfo():
		'''Use lsblk with JSON output to get infos about disks'''
		return {
			dev['path']: {
					'disk': [dev['size'], dev['label'], dev['vendor'], dev['model']] + dev['mountpoints'],
					'partitions': LinUtils.lspart(dev['path'])
				}
				for dev in loads(run(['lsblk', '--json', '-o', 'PATH,LABEL,TYPE,SIZE,VENDOR,MODEL,MOUNTPOINTS'],
				capture_output=True, text=True).stdout)['blockdevices']
				if dev['type'] == 'disk' and not dev['path'].startswith('/dev/zram')
		}

	@staticmethod
	def lsblk(physical=False, exclude=None):
		'''Use block devices'''
		blkdevs = {
			dev['path']: {
				'type': dev['type'],
				'size': dev['size'],
				'label': dev['label'],
				'vendor': dev['vendor'],
				'model': dev['model'],
				'rev': dev['rev'],
				'serial': dev['serial'],
				'ro': dev['ro'],
				'mountpoints': dev['mountpoints']
			} for dev in loads(run(
				['lsblk', '--json', '-o', 'PATH,LABEL,TYPE,SIZE,VENDOR,MODEL,REV,SERIAL,RO,MOUNTPOINTS'],
				capture_output=True, text=True).stdout)['blockdevices']
		}
		for outer_path in blkdevs:
			blkdevs[outer_path]['parent'] = ''
			for inner_path in blkdevs:
				if outer_path.startswith(inner_path) and outer_path != inner_path:
					blkdevs[outer_path]['parent'] = inner_path
					break
		if physical:
			blkdevs = {
				path: details for path, details in blkdevs.items()
					if not path.startswith('/dev/zram') and (
						details['type'] in ('disk', 'rom')
						or ( details['type'] == 'part' and details['parent'] and blkdevs[details['parent']]['type'] in ('disk', 'rom') )
					)
			}
		if exclude == 'mounted':
			exclude = LinUtils.get_mounted()
		elif exclude == 'occupied':
			exclude = LinUtils.get_occupied()
		if exclude:
			blkdevs = {
				path: details for path, details in blkdevs.items()
					if not StringUtils.startswith(path, exclude)
			}
		return blkdevs

	@staticmethod
	def get_blockdev(dev):
		'''Get infos about one block device'''
		try:
			return loads(run(
				['lsblk', '--json', '-o', 'PATH,LABEL,TYPE,SIZE,VENDOR,MODEL,REV,SERIAL,RO,MOUNTPOINTS', dev],
				capture_output=True, text=True).stdout)['blockdevices'][0]
		except IndexError:
			return

	@staticmethod
	def diskdetails(dev):
		'''Use lsblk with JSON output to get enhanced infos about block devoce'''
		details = dict()
		for key, value in loads(run(
			['lsblk', '--json', '-o', 'LABEL,SIZE,VENDOR,MODEL,REV,SERIAL', f'{dev}'],
			capture_output=True, text=True).stdout)['blockdevices'][0].items():
			if value:
				details[key] = value.strip()
			else:
				details[key] = ''
		return details

	@staticmethod
	def blkdevsize(dev):
		'''Use lsblk with JSON output to get disk or partition size'''
		return int(loads(run(['lsblk', '--json', '-o', 'SIZE', '-b', f'{dev}'],
			capture_output=True, text=True).stdout)['blockdevices'][0]['size'])
	
	@staticmethod
	def fdisk(path):
		'''Use fdisk -l to read partition table'''
		ret = run(['fdisk', '-l', f'{path}'], capture_output=True, text=True)
		return ret.stdout, ret.stderr

	@staticmethod
	def init_dev(dev, mbr=False, fs='ntfs'):
		'''Create partition table and one big partition'''
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
		ret = run(['mount', f'{dev}', f'{target}'], capture_output=True, text=True)
		return ret.stdout, ret.stderr

	@staticmethod
	def umount(target):
		'''Use umount'''
		run(['sync'], check=True)
		ret = run(['umount', f'{target}'], capture_output=True, text=True)
		return ret.stdout, ret.stderr

	@staticmethod
	def get_mounted():
		'''Get mounted partitions'''
		ret = run(['mount'], capture_output=True, text=True)
		return [line.split(' ', 1)[0] for line in ret.stdout.split('\n') if line.startswith('/dev/')]

	@staticmethod
	def get_occupied():
		'''Get mounted partition and their root devices'''
		mounted = LinUtils.get_mounted()
		return {LinUtils.rootdev_of(part) for part in mounted} | set(mounted)

	@staticmethod
	def get_ro(dev):
		'''Get rw/ro of given blockdevice'''
		return loads(run(['lsblk', '--json', '-o', 'RO', f'{dev}'],
			capture_output=True, text=True).stdout)['blockdevices'][0]['ro']

	@staticmethod
	def set_unoccupied_ro():
		'''Set types part and disk not mounted to ro except /dev/zram*'''
		occopied_physical_blkdevs = set(LinUtils.get_physical_devs()) - LinUtils.get_occupied()
		for dev in occopied_physical_blkdevs:
			LinUtils.set_ro(dev)
		return occopied_physical_blkdevs

	@staticmethod
	def dmidecode(*args):
		'''Run dmidecode'''
		cmd = ['dmidecode']
		if args:
			cmd.extend(args)
		ret = run(cmd, capture_output=True, text=True)
		return ret.stdout, ret.stderr

	@staticmethod
	def get_workarea():
		'''Use xprop -root to get _NET_WORKAREA(CARDINAL)'''
		ret = run(['xprop', '-root'], capture_output=True, text=True)
		if ret.stderr:
			return ret.stdout, ret.stderr
		for line in ret.stdout.split('\n'):
			if line.startswith('_NET_WORKAREA(CARDINAL)'):
				parts = line.split(',')
				return int(parts[2].strip()), int(parts[3].strip())

	@staticmethod
	def get_xkb_layouts(candidates=None):
		'''Get possible layouts for setxkbmap'''
		layouts = { match.rstrip(':') for match in findall('[a-z]{2}:', Path('/usr/share/X11/xkb/rules/xorg.lst').read_text())}
		if candidates:
			layouts = layouts.intersection(candidates)
		return sorted(list(layouts))

	@staticmethod
	def set_xkb_layout(layout):
		'''Set keyboard layout using setxkbmap'''
		ret = run(['setxkbmap', layout], capture_output=True, text=True)
		return ret.stdout, ret.stderr

	@staticmethod
	def get_system_time():
		return strftime('%G-%m-%d %T %Z/%z')

class OpenProc(Popen):
	'''Use Popen the way it is needed here'''

	def __init__(self, cmd, stderr=True, log=None):
		'''Launch process'''
		self.log = log
		if stderr:
			stderr = PIPE
		else:
			stderr = STDOUT
		super().__init__(cmd, stdout=PIPE, stderr=stderr, encoding='utf-8')

	def echo_output(self, echo=print, cnt=None, skip=0):
		'''Echo stdout, cnt: max. lines to log, skip: skip lines to log'''
		if self.log:
			stdout_cnt = 0
			self.stack = list()
			for line in self.stdout:
				if line:
					stdout_cnt += 1
					stripped = line.strip()
					self.log.echo(stripped)
					if stdout_cnt > skip:
						self.stack.append(stripped)
				if cnt and len(self.stack) > cnt:
					self.stack.pop(0)
			if self.stack:
				self.log.info('\n' + '\n'.join(self.stack))
		else:
			for line in self.stdout:
				if line:
					echo(line.strip())
		self.poll()
		return self.returncode

	def grep_stack(self, *searches, delimiter=':'):
		'''Get values by given search strings and keys from self.stack'''
		return {
			key:line.split(delimiter, 1)[1].strip()
				for line in self.stack
					for pattern, key in searches
						if line.startswith(pattern)
		}
