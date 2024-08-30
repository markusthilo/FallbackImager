#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import getuid
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT, run
from json import loads
from re import findall
from time import strftime
from .stringutils import StringUtils

class LinUtils:
	'Tools for Linux based systems'

	### static methods where no root privileges are required ###

	@staticmethod
	def i_am_root():
		'''Return Tru if python is run as root'''
		return getuid == 0

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
	def get_blockdevs():
		'''Use lsblk with JSON output to get block devices'''
		return [
			dev['path'] for dev in loads(run(['lsblk', '--json', '-o', 'PATH'],
				capture_output=True, text=True).stdout)['blockdevices']
		]

	#@staticmethod
	#def get_disks():
	#	'''Get type disk except /dev/zram*'''
	#	return [
	#		dev['path'] for dev in loads(run(['lsblk', '--json', '-o', 'PATH,TYPE'],
	#			capture_output=True, text=True).stdout)['blockdevices']
	#			if dev['type'] == 'disk' and not dev['path'].startswith('/dev/zram')
	#	]

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
	def is_type(dev, tp):
		'''Use lsblk with JSON output to check if device is of given type'''
		try:
			return loads(run(['lsblk', '--json', '-o', 'TYPE', f'{dev}'],
					capture_output=True, text=True).stdout)['blockdevices'][0]['type'] == tp
		except IndexError:
			return False

	@staticmethod
	def is_disk(dev):
		'''Use lsblk with JSON output to check if device is a disk'''
		return LinUtils.is_type(dev, 'disk')

	@staticmethod
	def is_part(dev):
		'''Use lsblk with JSON output to check if device is a partition'''
		return LinUtils.is_type(dev, 'part')

	#@staticmethod
	#def diskinfo():
	#	'''Use lsblk with JSON output to get infos about disks'''
	#	return {
	#		dev['path']: {
	#				'disk': [dev['size'], dev['label'], dev['vendor'], dev['model']] + dev['mountpoints'],
	#				'partitions': LinUtils.lspart(dev['path'])
	#			}
	#			for dev in loads(run(['lsblk', '--json', '-o', 'PATH,LABEL,TYPE,SIZE,VENDOR,MODEL,MOUNTPOINTS'],
	#			capture_output=True, text=True).stdout)['blockdevices']
	#			if dev['type'] == 'disk' and not dev['path'].startswith('/dev/zram')
	#	}

	@staticmethod
	def lsblk(physical=False, ro=False, exclude=None):
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
		if ro:
			blkdevs = {
				path: details for path, details in blkdevs.items()
					if details['ro'] == '1'
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

	#@staticmethod
	#def get_blockdev(dev):
	#	'''Get infos about one block device'''
	#	try:
	#		return loads(run(
	#			['lsblk', '--json', '-o', 'PATH,LABEL,TYPE,SIZE,VENDOR,MODEL,REV,SERIAL,RO,MOUNTPOINTS', dev],
	#			capture_output=True, text=True).stdout)['blockdevices'][0]
	#	except IndexError:
	#		return

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
	def mountpoint(part):
		'''Return mountpoint if partition is mounted'''
		ret = run(['mount'], capture_output=True, text=True)
		for line in ret.stdout.split('\n'):
			if line.startswith(part):
				try:
					return Path(line.split(' ', 3)[2])
				except IndexError:
					return

	@staticmethod
	def get_ro(dev):
		'''Get rw/ro of given blockdevice'''
		return loads(run(['lsblk', '--json', '-o', 'RO', f'{dev}'],
			capture_output=True, text=True).stdout)['blockdevices'][0]['ro']

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

	### root / sudo required ###

	def __init__(self, sudo=None):
		'''Generate object to use shell commands that need root privileges'''
		if sudo:
			self._sudo = ['sudo', '-S']
			self._pw = sudo
		else:
			self._sudo = list()
			self._pw = None

	def _run(self, *args):
		'''Run command (given arg after arg) using sudo if password was given'''
		if len(args) == 0:
			return '', 'missing command'
		cmd = self._sudo.copy()
		if isinstance(args[0], list):
			if len(args) > 1:
				return '', f'{args}: unprocessable command'
			cmd.extend(args[0])
		else:
			cmd .extend(args)
		ret = run(cmd, input=self._pw, capture_output=True, text=True)
		if ret.stderr.startswith('[sudo]') and ret.stderr.count(':') <= 1:	# [sudo] password for ...: is no error
			return ret.stdout, ''
		return ret.stdout, ret.stderr

	def fdisk(self, path):
		'''Use fdisk -l to read partition table'''
		return self._run('fdisk', '-l', f'{path}')

	def mount(self, part, mountpoint, mkdir=True):
		'''Use mount'''
		mp = Path(mountpoint)
		if mp.exists():
			if not mp.isdir():
				return '', f'{mp.absolute()} is not a possible mount point'
		else:
			mkdir_stdout, mkdir_stderr = self._run('mkdir', f'{mountpoint}')
		mount_stdout, mount_stderr = self._run('mount', f'{part}', f'{mountpoint}')
		return mkdir_stdout + mount_stdout, mkdir_stderr + mount_stderr

	def umount(self, target, rmdir=False):
		'''Use umount'''
		run(['sync'], check=True)
		if rmdir:
			if LinUtils.is_part(target):
				mountpoint = LinUtils.mountpoint(target)
				print(mountpoint)
			else:
				mountpoint = target
		umount_stdout, umount_stderr = self._run('umount', f'{target}')
		if not rmdir:
			return umount_stdout, umount_stderr
		rmdir_stdout, rmdir_stderr = self._run('rmdir', f'{mountpoint}')
		return umount_stdout + rmdir_stdout, umount_stderr + rmdir_stderr

	def init_blkdev(self, dev, mountpoint, mbr=False, fs='ntfs', label='Volume'):
		'''Create partition table, one big partition, filesystem and mount'''
		if mbr:
			mklabel_stdout, mklabel_stderr = self._run('parted', '--script', f'{dev}', 'mklabel', 'msdos')
		else:
			mklabel_stdout, mklabel_stderr = self._run('parted', '--script', f'{dev}', 'mklabel', 'gpt')
		mkpart_stdout, mkpart_stderr = self._run('parted', '--script', f'{dev}', 'mkpart', 'primary', fs, '0%', '100%')
		try:
			part = list(LinUtils.lspart(dev))[0]
		except IndexError:
			return mklabel_stdout + mkpart_stdout + mkfs_stdout, mklabel_stderr + mkpart_stderr + f'\nno partition on {dev}\n'
		cmd = ['mkfs', '-t']
		if fs.lower() == 'fat32':
			cmd.extend(['vfat', '-n'])
		elif fs.lower() == 'ntfs':
			cmd.extend(['ntfs', '-f', '-L'])
		else:
			cmd.extend([fs.lower(), '-L'])
		cmd.extend([f'{label}', f'{part}'])
		mkfs_stdout, mkfs_stderr = self._run(cmd)
		mount_stdout, mount_stderr = self.mount(part, mountpoint)
		return (
			mklabel_stdout + mkpart_stdout + mkfs_stdout + mount_stdout, 
			mklabel_stderr + mkpart_stderr + mkfs_stderr + mount_stderr
		)

	def set_ro(self, dev):
		'''Set block device to read only'''
		return self._run('blockdev', '--setro', f'{dev}')

	def set_rw(self, dev):
		'''Set block device to read and write access'''
		return self._run('blockdev', '--setrw', f'{dev}')

	def set_unoccupied_ro(self):
		'''Set types part and disk not mounted to ro except /dev/zram*'''
		occopied_physical_blkdevs = set(LinUtils.get_physical_devs()) - LinUtils.get_occupied()
		for dev in occopied_physical_blkdevs:
			self.set_ro(dev)
		return occopied_physical_blkdevs

	def mount_rw(self, part, target):
		'''Set partition and root device to rw and mount'''
		root_stdout, root_stderr = self.set_rw(LinUtils.rootdev_of(part))
		part_stdout, part_stderr = self.set_rw(part)
		mount_stdout, mount_stderr = self.mount(part, target)
		return root_stdout + part_stdout + mount_stdout, root_stderr + part_stderr + mount_stderr

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
