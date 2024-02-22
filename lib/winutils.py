#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from wmi import WMI
from win32api import GetCurrentProcessId, GetLogicalDriveStrings
from subprocess import Popen, PIPE, STDOUT, STARTUPINFO, STARTF_USESHOWWINDOW, TimeoutExpired
from time import sleep
from pathlib import Path
from lib.extpath import ExtPath, Progressor
from lib.stringutils import StringUtils

class WinUtils:
	'Needed Windows functions'

	WINCMD_TIMEOUT = 120
	WINCMD_RETRIES = 120
	WINCMD_DELAY = 1

	@staticmethod
	def find_exe(name, parent_path, *possible_paths):
		'''Find executable file'''
		for parent in parent_path/'bin', parent_path, *possible_paths:
			exe_path = parent/name
			if exe_path.is_file():
				return exe_path

	@staticmethod
	def get_used_letters():
		'''Get drive letters that are already in use as set'''
		return {drive.rstrip(':\\') for drive in GetLogicalDriveStrings().split('\0') if drive}

	@staticmethod
	def get_free_letters():
		'''Get free drive letters'''
		return sorted(set('DEFGHIJKLMNOPQRSTUVWXYZ') - WinUtils.get_used_letters())

	@staticmethod
	def drive_letter_is_free(letter):
		'''Check if drive letter is free for new assignment'''
		return not letter in WinUtils.get_used_letters()

	@staticmethod
	def is_physical_drive(path):
		'''Return True if physical drive'''
		return f'{path}'.upper().startswith('\\\\.\\PHYSICALDRIVE')

	@staticmethod
	def list_drives():
		'''List drive infos, partitions and logical drives'''
		conn = WMI()
		disk2part = {(rel.Antecedent.DeviceID, rel.Dependent.DeviceID)
			for rel in conn.Win32_DiskDriveToDiskPartition()
		}
		part2logical = {(rel.Antecedent.DeviceID, rel.Dependent.DeviceID)
			for rel in conn.Win32_LogicalDiskToPartition()
		}
		disk2logical = { logical: disk
			for disk, part_disk in disk2part
			for part_log, logical in part2logical
			if part_disk == part_log
		}
		log_disks = dict()
		for log_disk in conn.Win32_LogicalDisk():
			info = f'\n- {log_disk.DeviceID} '
			if log_disk.VolumeName:
				info += f'{log_disk.VolumeName}, '
			if log_disk.FileSystem:
				info += f'{log_disk.FileSystem}, '
			info += f'{StringUtils.bytes(log_disk.Size)}'
			log_disks[log_disk.DeviceID] = info
		drives = dict()
		for drive in conn.Win32_DiskDrive():
			drive_info = f'{drive.Caption.strip()}, {drive.InterfaceType}, '
			drive_info += f'{drive.MediaType}, {StringUtils.bytes(drive.Size)}'
			drives[drive.DeviceID] = drive_info
		for drive_id, drive_info in sorted(drives.items()):
			for log_id, disk_id in disk2logical.items():
				if disk_id == drive_id:
					try:
						drive_info += log_disks[log_id]
					except KeyError:
						continue
			yield drive_id, drive_info

	@staticmethod
	def echo_drives(echo=print):
		'''List drives and show infos'''
		for drive_id, drive_info in WinUtils.list_drives():
			echo(f'\n{drive_id} - {drive_info}')
		echo()

	@staticmethod
	def diskpart(script, outdir):
		'Run diskpart script'
		tmpscriptpath = outdir/f'_script_{GetCurrentProcessId()}.tmp'
		tmpscriptpath.write_text(script)
		proc = OpenProc([f'diskpart', '/s', f'{tmpscriptpath}'])
		try:
			proc.wait(timeout=WinUtils.WINCMD_TIMEOUT)
		except TimeoutExpired:
			pass
		try:
			tmpscriptpath.unlink()
			return False
		except:
			return True

	@staticmethod
	def create_partition(drive_id, outdir, label='Volume', driveletter=None, mbr=False, fs='ntfs'):
		'''Create partition using diskpart'''
		if not driveletter:
			driveletter = WinUtils.get_free_letters()[0]
		if mbr:
			table = 'mbr'
		else:
			table = 'gpt'
		WinUtils.diskpart(f'''select disk {drive_id[17:]}
clean
convert {table}
create partition primary
format quick fs={fs} label={label}
assign letter={driveletter}
''', outdir)
		for cnt in range(WinUtils.WINCMD_RETRIES):
			sleep(WinUtils.WINCMD_DELAY)
			try:
				if Path(f'{driveletter}:\\').exists():
					return driveletter
			except OSError:
				pass

	@staticmethod
	def get_value(string):
		'''Get value after colon'''
		try:
			return string.split(':', 1)[1].strip(' "')
		except IndexError:
			return ''

class OpenProc(Popen):
	'''Use Popen to run tools on Windows'''

	def __init__(self, cmd, stderr=False, log=None):
		'''Launch process'''
		self.log = log
		self.startupinfo = STARTUPINFO()
		self.startupinfo.dwFlags |= STARTF_USESHOWWINDOW
		if stderr:
			stderr = PIPE
		else:
			stderr = STDOUT
		super().__init__(cmd,
			stdout = PIPE,
			stderr = stderr,
			encoding = 'utf-8',
			errors = 'ignore',
			universal_newlines = True,
			startupinfo = self.startupinfo
		)

	def echo_output(self, echo=print, cnt=None, skip=0):
		'''Echo stdout, cnt: max. lines to log, skip: skip lines to log'''
		if self.log:
			stdout_cnt = 0
			self.stack = list()
			for line in self.stdout:
				stripped = line.strip()
				if stripped:
					stdout_cnt += 1
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

	def grep_stdout(self, string, *ln_key):
		'''Get values indicated by grep string'''
		lower_str = string.lower()
		stdout = self.stdout.read()
		for ln, line in enumerate(stdout):
			if line.lower().startswith(lower_str):
				yield {key: WinUtils.get_value(stdout[ln+ln_delta]) for ln_delta, key in ln_key}