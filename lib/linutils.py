#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import getuid, getenv
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT, run
from json import loads
from re import findall
from time import strftime
from hashlib import md5
from getpass import getpass
from .stringutils import StringUtils

class LinUtils:
	'Tools for Linux based systems'

	### static methods where no root privileges are required ###

	@staticmethod
	def i_am_root():
		'''Return True if python is run as root'''
		return getuid() == 0

	@staticmethod
	def whoami():
		'''Get username'''
		ret = run(['whoami'], capture_output=True, text=True)
		return ret.stdout.rstrip()

	@staticmethod
	def no_pw_sudo():
		'''Return True if sudo does not need password'''
		ret = run(['sudo', '-n', 'blockdev', '--report'], capture_output=True, text=True)
		return ret.stderr == '' and len(ret.stdout.split('\n')) > 2

	@staticmethod
	def gen_cmd(*args, sudo=False, password=None):
		'''Build a command to run as subprocess from args'''
		if len(args) == 0:
			return
		if password or sudo:
			cmd = ['sudo']
			if password:
					cmd.extend(['-S', '-k'])
		else:
			cmd = list()
		for arg in args:
			if isinstance(arg, list):
				cmd.extend(arg)
			else:
				cmd.append(arg)
		return cmd

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
	def get_pid(name):
		'''Find process id to given program name'''
		ret = run(['ps', '-C', name, '-o', 'pid='], capture_output=True, text=True)
		return [int(line.strip()) for line in ret.stdout.split('\n') if line]

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
	def get_uuid(dev):
		'''Return UUID of given device = partition'''
		try:
			return loads(run(['lsblk', '--json', '-o', 'UUID', f'{dev}'],
					capture_output=True, text=True).stdout)['blockdevices'][0]['uuid']
		except IndexError:
			return False

	@staticmethod
	def get_partitions(dev):
		'''Use lsblk with JSON output to get partitions of device'''
		try:
			children = loads(run(['lsblk', '--json', '-o', 'NAME,TYPE', f'{dev}'],
					capture_output=True, text=True).stdout)['blockdevices'][0]['children']
		except IndexError:
			return False
		return [f'/dev/{child["name"]}' for child in children if child['type'] == 'part']

	@staticmethod
	def get_mountpoints(dev):
		'''Use lsblk with JSON output to check if device is a mounted partition and return mountpoint'''
		try:
			mps = loads(run(['lsblk', '--json', '-o', 'MOUNTPOINTS', f'{dev}'],
					capture_output=True, text=True).stdout)['blockdevices'][0]['mountpoints']
		except IndexError:
			return False
		return mps if mps and mps != [None] else False

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
		'''Use lsblk'''
		blkdevs = {
			dev['path']: {
				'type': dev['type'],
				'size': dev['size'],
				'label': dev['label'],
				'vendor': dev['vendor'],
				'model': dev['model'],
				'rev': dev['rev'],
				'serial': dev['serial'],
				'fs': dev['fstype'],
				'ro': dev['ro'],
				'mountpoints': dev['mountpoints']
			} for dev in loads(run(
				['lsblk', '--json', '-o', 'PATH,LABEL,TYPE,SIZE,VENDOR,MODEL,REV,SERIAL,FSTYPE,RO,MOUNTPOINTS'],
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
	def get_unoccupied():
		'''Set types part and disk not mounted to ro except /dev/zram*'''
		return set(LinUtils.get_physical_devs()) - LinUtils.get_occupied()

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

	def __init__(self, sudo=True, password=None, cli=False):
		'''Generate object to use shell commands that need root privileges'''
		if self.i_am_root():
			self.sudo = False
			self.password = None
		else:
			self.password = password
			self.sudo = True
			if not self.i_have_root() and cli:
				print('\n\nGive password for sudo')
				self.password=getpass()

	def _run(self, *args):
		'''Run command using sudo if password was given'''
		cmd = self.gen_cmd(*args, sudo=self.sudo, password=self.password)
		if self.password:
			ret = run(cmd, input=self.password, capture_output=True, text=True)
		else:
			ret = run(cmd, capture_output=True, text=True)
		return ret.stdout, ret.stderr

	def i_have_root(self):
		'''Return True if sudo works'''
		run(['faillock', '--user', getenv('USER'), '--reset'])
		stdout, stderr = self._run('whoami')
		return stdout.strip() == 'root' or self.i_am_root()

	def fdisk(self, path):
		'''Use fdisk -l to read partition table'''
		return self._run('fdisk', '-l', f'{path}')

	def mkdir(self, path, exists_ok=False):
		'''Generate directory with root privileges'''
		cmd = ['mkdir']
		if exists_ok:
			cmd.append('-p')
		return self._run(cmd, f'{path}')

	def mount(self, part, mnt=None):
		'''Create dir to mount and mount given partition'''
		if mnt:
			mountpoint = mnt
		else:
			parent = f'/run/media/{self.whoami()}'
			stdout, stderr = self.mkdir(parent, exists_ok=True)
			if stderr:
				return stdout, stderr
			name = self.get_uuid(part)
			if not name:
				name = md5(strftime('%s').encode()).hexdigest().upper()
			mountpoint = f'{parent}/{name}'
		stdout, stderr = self.mkdir(mountpoint, exists_ok=True)
		if stderr:
			return stdout, stderr
		stdout, stderr = self._run('mount', '-o', 'rw,umask=0000', part, mountpoint)
		if stderr:
			return stdout, stderr
		return mountpoint, ''

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

	def init_blkdev(self, dev, mbr=False, fs=None, name=None):
		'''Create partition table, one big partition, filesystem and mount'''
		table = 'msdos' if mbr else 'gpt'
		if not fs:
			tp = fs = 'ntfs'
		elif fs == 'exfat':
			tp = 'ntfs'
		else:
			tp = fs = fs.lower()
		if not name:
			name = 'Volume'
		stdout, stderr = self._run('parted', '--script', f'{dev}', 'mklabel', table)
		if stderr:
			return stdout, stderr
		stdout, stderr = self._run('parted', '--script', f'{dev}', 'mkpart', 'primary', tp, '0%', '100%')
		if stderr:
			return stdout, stderr
		part = self.get_partitions(dev)[0]
		cmd = ['mkfs', '-t']
		if fs == 'fat32':
			cmd.extend(['vfat', '-n'])
		elif fs == 'exfat':
			cmd.extend(['exfat', '-n'])
		elif fs == 'ntfs':
			cmd.extend(['ntfs', '-f', '-L'])
		else:
			cmd.extend([fs.lower(), '-L'])
		cmd.extend([name, part])
		stdout, stderr = self._run(cmd)
		if stderr and not ' lowercase labels ' in stderr:
			return stdout, stderr
		return part, ''

	def set_ro(self, dev):
		'''Set block device to read only'''
		return self._run('blockdev', '--setro', f'{dev}')

	def set_rw(self, dev):
		'''Set block device to read and write access'''
		return self._run('blockdev', '--setrw', f'{dev}')

	def mount_rw(self, part, target):
		'''Set partition and root device to rw and mount'''
		root_stdout, root_stderr = self.set_rw(LinUtils.rootdev_of(part))
		part_stdout, part_stderr = self.set_rw(part)
		mount_stdout, mount_stderr = self.mount(part, target)
		return root_stdout + part_stdout + mount_stdout, root_stderr + part_stderr + mount_stderr

	def chown(self, user, group, path):
		'''Set user and group of given file or directory'''
		return self._run('chown', f'{user}:{group}', f'{path}')

	def killall(self, name):
		'''Use killall to terminate process'''
		return self._run('killall', name)

	def poweroff(self):
		'''Poweroff machine'''
		return self._run('shutdown', '--poweroff')

class OpenProc(Popen):
	'''Use Popen the way it is needed here'''

	def __init__(self, *args, sudo=False, password=None, indie=False, log=None):
		'''Launch process'''
		self.log = log
		cmd = LinUtils.gen_cmd(*args, sudo=sudo, password=password)
		if password:
			super().__init__(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True, start_new_session=indie)
			self.stdin.write(password)
		else:
			super().__init__(cmd, stdout=PIPE, stderr=PIPE, text=True, start_new_session=indie)

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
