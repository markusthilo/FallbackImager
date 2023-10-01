#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from wmi import WMI
from win32api import GetCurrentProcessId, GetLogicalDriveStrings
from subprocess import Popen, PIPE, STDOUT, STARTUPINFO, STARTF_USESHOWWINDOW, TimeoutExpired
from time import sleep
from lib.extpath import ExtPath, FilesPercent

class WinUtils:
	'Needed Windows functions'

	WINCMD_TIMEOUT = 60
	WINCMD_RETRIES = 20
	WINCMD_DELAY = 1

	def __init__(self, parent_path):
		'''Generate Windows tools'''
		self.conn = WMI()
		self.cmd_startupinfo = STARTUPINFO()
		self.cmd_startupinfo.dwFlags |= STARTF_USESHOWWINDOW
		self.process_id = GetCurrentProcessId()
		self.tmpscriptpath = parent_path/f'_script_{self.process_id}.tmp'

	def cmd_launch(self, cmd):
		'''Start command line subprocess without showing a terminal window'''
		return Popen(
			cmd,
			shell = True,
			stdout = PIPE,
			stderr = PIPE,
			encoding = 'utf-8',
			errors = 'ignore',
			universal_newlines = True,
			startupinfo = self.cmd_startupinfo
		)

	def list_drives(self):
		'''List drive infos, partitions and logical drives'''
		disk2part = {(rel.Antecedent.DeviceID, rel.Dependent.DeviceID)
			for rel in self.conn.Win32_DiskDriveToDiskPartition()
		}
		part2logical = {(rel.Antecedent.DeviceID, rel.Dependent.DeviceID)
			for rel in self.conn.Win32_LogicalDiskToPartition()
		}
		disk2logical = { logical: disk
			for disk, part_disk in disk2part
			for part_log, logical in part2logical
			if part_disk == part_log
		}
		log_disks = dict()
		for log_disk in self.conn.Win32_LogicalDisk():
			info = f'\n- {log_disk.DeviceID} '
			if log_disk.VolumeName:
				info += f'{log_disk.VolumeName}, '
			if log_disk.FileSystem:
				info += f'{log_disk.FileSystem}, '
			info += f'{ExtPath.readable_size(log_disk.Size)}'
			log_disks[log_disk.DeviceID] = info
		drives = dict()
		for drive in self.conn.Win32_DiskDrive():
			drive_info = f'{drive.Caption.strip()}, {drive.InterfaceType}, '
			drive_info += f'{drive.MediaType}, {ExtPath.readable_size(drive.Size)}'
			drives[drive.DeviceID] = drive_info
		for drive_id, drive_info in sorted(drives.items()):
			drive_letters = list()
			for log_id, disk_id in disk2logical.items():
				if disk_id == drive_id:
					try:
						drive_info += log_disks[log_id]
						drive_letters.append(log_id)
					except KeyError:
						continue
			yield drive_id, drive_info, drive_letters

	def dismount_drives(self, driveletters):
		'Dismount Drives'
		for driveletter in driveletters:
			proc = self.cmd_launch(f'mountvol {driveletter} /p')
			try:
				proc.wait(timeout=self.WINCMD_TIMEOUT)
			except:
				pass
		stillmounted = driveletters
		for cnt in range(self.WINCMD_RETRIES):
			for driveletter in stillmounted:
				if not Path(driveletter).exists():
					stillmounted.remove(driveletter)
			if stillmounted == list():
				return
			sleep(self.WINCMD_DELAY)
		return stillmounted

	def run_diskpart(self, script):
		'Run diskpart script'
		self.tmpscriptpath.write_text(script)
		proc = self.cmd_launch(f'diskpart /s {self.tmpscriptpath}')
		try:
			proc.wait(timeout=self.WINCMD_TIMEOUT)
		except TimeoutExpired:
			pass
		try:
			self.tmpscriptpath.unlink()
		except:
			pass
		return

	def clean_table(self, driveid):
		'Clean partition table using diskpart'
		try:
			driveno = driveid[17:]
		except:
			return
		self.run_diskpart(f'''select disk {driveno}
clean
'''
		)

	def create_partition(self, drive_path, label='Volume', letter=None, mbr=False, fs='ntfs'):
		'''Create partition using diskpart'''
		try:
			drive_no = str(drive_path)[17:].rstrip('\\')
		except:
			return
		if not letter:
			used_letters = GetLogicalDriveStrings().split(':\\\x00')
			for char in range(ord('D'),ord('Z')+1):
				if not chr(char) in used_letters:
					letter = chr(char)
					break
			else:
				return
		if mbr:
			table = 'mbr'
		else:
			table = 'gpt'
		self.run_diskpart(f'''select disk {drive_no}
clean
convert {table}
create partition primary
format quick fs={fs} label={label}
assign letter={letter}
''')
		for cnt in range(self.WINCMD_RETRIES):
			sleep(self.WINCMD_DELAY)
			if Path(f'{letter}:').exists():
				return letter
