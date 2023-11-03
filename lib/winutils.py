#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from wmi import WMI
from win32api import GetCurrentProcessId, GetLogicalDriveStrings
from subprocess import Popen, PIPE, STDOUT, STARTUPINFO, STARTF_USESHOWWINDOW, TimeoutExpired
from time import sleep
from pathlib import Path
from lib.extpath import ExtPath, FilesPercent

class WinUtils:
	'Needed Windows functions'

	WINCMD_TIMEOUT = 60
	WINCMD_RETRIES = 20
	WINCMD_DELAY = 1

	def __init__(self, outdir=None):
		'''Generate Windows tools'''
		self.conn = WMI()
		self.cmd_startupinfo = STARTUPINFO()
		self.cmd_startupinfo.dwFlags |= STARTF_USESHOWWINDOW
		self.process_id = GetCurrentProcessId()
		if outdir:
			self.tmpscriptpath = Path(outdir)/f'_script_{self.process_id}.tmp'

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

	def drive_letter_is_free(self, letter):
		'''Check if drive letter is free for new assignment'''
		try:
			return not Path(str(letter).rstrip(':\\')).exists()
		except OSError:
			return True

	def get_free_letters(self):
		'''Get free drive letters'''
		for letter in 'DEFGHIJKLMNOPQRSTUVWXYZ':
			if self.drive_letter_is_free(letter):
				yield(letter)

	def is_physical_drive(self, path):
		'''Return True if physical drive'''
		return str(path).upper().startswith('\\\\.\\PHYSICALDRIVE')

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
			for log_id, disk_id in disk2logical.items():
				if disk_id == drive_id:
					try:
						drive_info += log_disks[log_id]
					except KeyError:
						continue
			yield drive_id, drive_info

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
			return False
		except:
			return True

	def get_drive_no(self, drive_id):
		'Get number of physical drive from full drive id'
		try:
			return drive_id[17:]
		except:
			return

	def clean_table(self, drive_id):
		'Clean partition table using diskpart'
		if drive_no := self.get_drive_no(drive_id):
			return self.run_diskpart(f'select disk {drive_no}\nclean\n')

	def create_partition(self, drive_id, label='Volume', letter=None, mbr=False, fs='ntfs'):
		'''Create partition using diskpart'''
		if drive_no := self.get_drive_no(drive_id):
			if not letter:
				letter = next(self.get_free_letters())
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
'''
			)
			for cnt in range(self.WINCMD_RETRIES):
				sleep(self.WINCMD_DELAY)
				try:
					if Path(f'{letter}:\\').exists():
						return letter
				except OSError:
					pass
