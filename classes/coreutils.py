#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import getuid, getenv
from pathlib import Path
from os import access, R_OK
from subprocess import Popen, PIPE, STDOUT, run
from json import loads
from re import findall
from time import strftime
from hashlib import md5
from getpass import getpass
import shlex

class PipedPopen(Popen):
	'''Popen piping stdout and stderr'''

	def __init__(self, cmd, start_new_session=False):
		'''Generate string from list'''
		super().__init__(cmd, stdout=PIPE, stderr=PIPE, text=True, start_new_session=start_new_session)

	def __repr__(self):
		'''String representation'''
		rep = self.args[0]
		for arg in self.args[1:]:
			rep += f' {arg}' if arg.isdigit() or arg.startswith('-') else f' "{arg}"'
		return rep

class CoreUtils:
	'Wrapper for shell core utilities'

	### static methods where no root privileges are required ###

	@staticmethod
	def i_am_root():
		'''Return True if python is run as root'''
		return getuid() == 0

	@staticmethod
	def no_pw_sudo():
		'''Return True if sudo does not need password'''
		ret = run(['sudo', '-n', 'whoami'], capture_output=True, text=True)
		return ret.stderr == ''

	@staticmethod
	def whoami():
		'''Get username'''
		ret = run(['whoami'], capture_output=True, text=True)
		return ret.stdout.rstrip()

	@staticmethod
	def are_readable(paths):
		'''Check if every path is readable'''
		for path in paths:
			if not access(path, R_OK):
				return False
		return True

	@staticmethod
	def get_pid(name):
		'''Find process id to given program name'''
		ret = run(['ps', '-C', name, '-o', 'pid='], capture_output=True, text=True)
		return [int(line.strip()) for line in ret.stdout.split('\n') if line]


	@staticmethod
	def lsblk(no_zram=True):
		'''Use lsblk'''
		blkdevs = {	# fill dict with json output from lsblk
			dev['path']: {
				'label': dev['label'] if dev['label'] else None,
				'type': dev['type'],
				'size': dev['size'],
				'vendor': dev['vendor'] if dev['vendor'] else None,
				'model': dev['model'] if dev['model'] else None,
				'rev': dev['rev'] if dev['rev'] else None,
				'serial': dev['serial'] if dev['serial'] else None,
				'fstype': dev['fstype'],
				'ro': dev['ro'] == '1',
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
		if no_zram:
			blkdevs = {path: details for path, details in blkdevs.items() if not path.startswith('/dev/zram')} 
		return blkdevs

		#if physical:
		#	blkdevs = {
		#		path: details for path, details in blkdevs.items()
		#			if not path.startswith('/dev/zram') and (
		#				details['type'] in ('disk', 'rom')
		#				or ( details['type'] == 'part' and details['parent'] and blkdevs[details['parent']]['type'] in ('disk', 'rom') )
		#			)
		#	}
		#if ro:
		#	blkdevs = {
		#		path: details for path, details in blkdevs.items()
		#			if details['ro']
		#	}
		#if exclude == 'mounted':
		#	exclude = CoreUtils.get_mounted()
		#elif exclude == 'occupied':
		#	exclude = CoreUtils.get_occupied()
		#if exclude:
		#	blkdevs = {
		#		path: details for path, details in blkdevs.items()
		#			if path.startswith(exclude)
		#	}
		#return blkdevs


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
		for rootdev in CoreUtils.get_rootdevs():
			if part.startswith(rootdev):
				return rootdev

	@staticmethod
	def get_occupied():
		'''Get mounted partition and their root devices'''
		mounted = LinUtils.get_mounted()
		return {CoreUtils.rootdev_of(part) for part in mounted} | set(mounted)

	@staticmethod
	def get_mounted():
		'''Get mounted partitions'''
		ret = run(['mount'], capture_output=True, text=True)
		return [line.split(' ', 1)[0] for line in ret.stdout.split('\n') if line.startswith('/dev/')]

	@staticmethod
	def get_blockdevs():
		'''Use lsblk with JSON output to get block devices'''
		return [
			dev['path'] for dev in loads(run(['lsblk', '--json', '-o', 'PATH'],
				capture_output=True, text=True).stdout)['blockdevices']
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


	#@staticmethod
	#def get_disks():
	#	'''Get type disk except /dev/zram*'''
	#	return [
	#		dev['path'] for dev in loads(run(['lsblk', '--json', '-o', 'PATH,TYPE'],
	#			capture_output=True, text=True).stdout)['blockdevices']
	#			if dev['type'] == 'disk' and not dev['path'].startswith('/dev/zram')
	#	]

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
	def blkdevsize(dev):
		'''Use lsblk with JSON output to get disk or partition size'''
		return int(loads(run(['lsblk', '--json', '-o', 'SIZE', '-b', f'{dev}'],
			capture_output=True, text=True).stdout)['blockdevices'][0]['size'])

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
		'''Give system time in readable form / as string'''
		return strftime('%G-%m-%d %T %Z/%z')

	@staticmethod
	def pgrep(name):
		'''Run pgrep'''
		return run(['pgrep', name], capture_output=True, text=True).stdout

	### root / sudo required ###

	def __init__(self):
		'''Generate object to use shell commands that need root privileges'''
		self._password = ''
		if self.i_am_root():
			self._sudo = False
			self._no_pw_sudo = False
			self._i_am_root = True
		else:
			self._sudo = True
			self._i_m_root = False
			if self.no_pw_sudo():
				self._no_pw_sudo = True
			else:
				self._no_pw_sudo = False

	def i_have_root(self):
		'''Return True if sudo works'''
		if self.i_am_root() or self._no_pw_sudo:
			return True
		ret = run(['sudo', '-S', '-k', 'whoami'], input=self._password, capture_output=True, text=True)
		return ret.stdout.endswith('root\n')

	def set_password(self, password):
		'''Set sudo password'''
		self._password = password
		self._sudo = True
		self._no_pw_sudo = False

	def read_password(self):
		'''Get sudo password on command line'''
		print('\nGive password for sudo')
		self.set_password(getpass())
		if not self.i_have_root():
			raise PermissionError('Unable to become root')

	def gen_cmd(self, cmd):
		'''Build a command to run as subprocess from args'''
		new_cmd = list()
		cmd_str = ''
		if len(cmd) > 0:
			if self._sudo:
				new_cmd.append('sudo')
				if self._password:
					new_cmd.extend(['-S', '-k'])
			new_cmd.append(cmd[0])
			cmd_str = f'{cmd[0]}'
			for arg in cmd[1:]:
				arg_str = f'{arg}'
				new_cmd.append(arg_str)
				cmd_str += f' {arg_str}' if isinstance(arg, int) or arg_str.startswith('-') else f' "{arg_str}"'
		return new_cmd, cmd_str

	def popen(self, cmd, start_new_session=False):
		'''Launch process'''
		cmd, cmd_str = self.gen_cmd(cmd)
		if self._password:
			proc = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True, start_new_session=start_new_session)
			proc.stdin.write(password)
		else:
			proc = Popen(cmd, stdout=PIPE, stderr=PIPE, text=True, start_new_session=start_new_session)
		return proc, cmd_str

	def run(self, cmd):
		'''Run command using sudo if password was given'''
		cmd, cmd_str = self.gen_cmd(cmd)
		if self._password:
			ret = run(cmd, input=self.password, capture_output=True, text=True)
		else:
			ret = run(cmd, capture_output=True, text=True)
		return ret.stdout, ret.stderr, cmd_str

	def diskdetails(self, dev):
		'''Use lsblk with JSON output to get enhanced infos about block devoce'''
		details = dict()
		stdout, stderr, cmd_str = self.run(['lsblk', '--json', '-O', '-b', f'{dev}'])
		if stderr:
			details
		try:
			for key, value in loads(stdout)['blockdevices'][0].items():
				try:
					details[key] = int(value)
				except:
					pass
				try:
					details[key] = value.strip()
				except:
					pass
				try:
					details[key] = value
				except:
					details[key] = ''
		except IndexError:
			pass
		return details

	def get_file_size(self, path):
		'''Return file suze in bytes as int'''
		stdout, stderr, cmd_str = self.run(['stat', '-c', '%s', f'{path}'])
		try:
			return int(stdout)
		except:
			return

	def fdisk(self, path):
		'''Use fdisk -l to read partition table'''
		return self.run('fdisk', '-l', f'{path}')

	def mkdir(self, path, exists_ok=False):
		'''Generate directory with root privileges'''
		cmd = ['mkdir']
		if exists_ok:
			cmd.append('-p')
		return self.run(cmd, f'{path}')

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
		stdout, stderr = self.run('mount', '-o', 'rw,umask=0000', part, mountpoint)
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
		umount_stdout, umount_stderr = self.run('umount', f'{target}')
		if not rmdir:
			return umount_stdout, umount_stderr
		rmdir_stdout, rmdir_stderr = self.run('rmdir', f'{mountpoint}')
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
		stdout, stderr = self.run(cmd)
		if stderr and not ' lowercase labels ' in stderr:
			return stdout, stderr
		return part, ''

	def set_ro(self, dev):
		'''Set block device to read only'''
		return self.run('blockdev', '--setro', f'{dev}')

	def set_rw(self, dev):
		'''Set block device to read and write access'''
		return self.run('blockdev', '--setrw', f'{dev}')

	def mount_rw(self, part, target):
		'''Set partition and root device to rw and mount'''
		root_stdout, root_stderr = self.set_rw(LinUtils.rootdev_of(part))
		part_stdout, part_stderr = self.set_rw(part)
		mount_stdout, mount_stderr = self.mount(part, target)
		return root_stdout + part_stdout + mount_stdout, root_stderr + part_stderr + mount_stderr

	def chown(self, user, group, path):
		'''Set user and group of given file or directory'''
		return self.run('chown', f'{user}:{group}', f'{path}')

	def killall(self, name):
		'''Use killall to terminate process'''
		return self.run('killall', name)

	def poweroff(self):
		'''Poweroff machine'''
		return self.run('shutdown', '--poweroff')
