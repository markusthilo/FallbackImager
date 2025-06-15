#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'WipeW'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2024-12-27'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This is a wipe tool designed for SSDs and HDDs. There is also the possibility to overwrite files but without erasing file system metadata. It runs on Windows.

By default only unwiped blocks (or SSD pages) are overwritten though it is possible to force the overwriting of every block or even use a two pass wipe (1st pass writes random values). Instead of zeros you can choose to overwrite with a given byte value.

Whe the target is a physical drive, you can create a partition where (after a successful wipe) the log is copied into. A custom head for this log can be defined in a text file (wipe-head.txt by default).

Be aware that this module is extremely dangerous as it is designed to erase data! There will be no "Are you really really sure questions" as Windows users might be used to.
'''

from sys import executable as __executable__
from win32com.shell.shell import IsUserAnAdmin
from pathlib import Path
from argparse import ArgumentParser
from lib.timestamp import TimeStamp
from lib.pathutils import PathUtils
from lib.logger import Logger
from lib.winutils import WinUtils, OpenProc

__parent_path__ = Path(__executable__).parent if Path(__file__).suffix.lower() == '.pyc' else Path(__file__).parent

class WipeW:
	'''Frontend and Python wrapper for zd-win.exe'''

	MIN_BLOCKSIZE = 512
	STD_BLOCKSIZE = 4096
	MAX_BLOCKSIZE = 32768

	def __init__(self, echo=print):
		'''Look for zd-win.exe'''
		self.zd_path = WinUtils.find_exe('zd-win.exe', __parent_path__)
		if self.zd_path:
			self.available = True
			self.echo = echo
		else:
			self.available = False

	def wipe(self, targets,
			verify = False,
			allbytes = False,
			extra = False,
			value = False,
			blocksize = None,
			maxbadblocks = None,
			maxretries = None,
			log = None,
			outdir = None
		):
		self.outdir = PathUtils.mkdir(outdir)
		self.log = log if log else Logger(
			filename = f'{TimeStamp.now(path_comp=True, no_ms=True)}_wipe',
			outdir = self.outdir, 
			head = 'wipew.WipeW',
			echo = self.echo
		)
		if len(targets) == 0:
			self.log.error('Missing drive or file(s) to wipe')
		if verify and allbytes and extra:
			self.log.error(f'Too many arguments - you can perform normal wipe, all bytes, extra/2-pass or just verify')
		if blocksize and (
				blocksize % self.MIN_BLOCKSIZE != 0 or blocksize < self.MIN_BLOCKSIZE or blocksize > self.MAX_BLOCKSIZE
			):
				self.log.error(f'Block size has to be n * {MIN_BLOCKSIZE}, >={MIN_BLOCKSIZE} and <={MAX_BLOCKSIZE}')
		if value:
			try:
				int(value, 16)
			except ValueError:
				self.log.error('Byte to overwrite with (-f/--value) has to be a hex value')
			if int(value, 16) < 0 or int(value, 16) > 0xff:
				self.log.error('Byte to overwrite (-f/--value) has to be inbetween 00 and ff')
		self.physical_drive = None
		if len(targets) == 1:
			self.physical_drive = WinUtils.physical_drive(targets[0])
			if self.physical_drive:
				if not IsUserAnAdmin():
					self.log.error('Admin rights are required to access bphysical drives')
				targets[0] = self.physical_drive
		else:
			for target in targets:
				if WinUtils.physical_drive(target):
					self.log.error('Only one physical drive at a time')
		cmd = f'{self.zd_path}'
		if blocksize:
			cmd += f' -b {blocksize}'
		if value:
			cmd += f' -f {value}'
		if maxbadblocks:
			cmd += f' -m {maxbadblocks}'
		if maxretries:
			cmd += f' -r {maxretries}'
		if verify:
			cmd += ' -v'
		elif allbytes:
			cmd += ' -a'
		elif extra:
			cmd += ' -x'
		self.zd_error = False
		for target in targets:
			self.echo()
			proc = OpenProc(f'{cmd} "{target}"', stderr=True)
			for line in proc.stdout:
				msg = line.strip()
				if msg.startswith('...'):
					self.echo(msg, end='\r')
				elif msg == '':
					self.echo('')
				else:
					self.log.info(msg, echo=True)
			if stderr := proc.stderr.read():
				self.log.error(f'zd-win.exe terminated with: {stderr}')

	def mkfs(self, target,
			fs = None,
			driveletter = None,
			loghead = None,
			mbr = False,
			name = None
		):
		'''Generate partition and file system'''
		if not self.physical_drive:
				wiper.log.error('Creating partition only works on physical drive')
		if not name:
			name = 'Volume'
		if not fs:
			fs = 'ntfs'
		loghead = Path(loghead) if loghead else __parent_path__/'wipe-log-head.txt'
		driveletter = WinUtils.create_partition(target, self.outdir,
			label = name,
			driveletter = driveletter,
			mbr = mbr,
			fs = fs
		)
		if not driveletter:
			self.log.error('Could not assign a letter to the wiped drive')
		self.log.info('Disk preparation successful', echo=True)
		self.log.close()
		log_path = Path(f'{driveletter}:\\wipe-log.txt')
		try:
			head = loghead.read_text(encoding='utf-8')
		except FileNotFoundError:
			head = ''
		log_path.write_text(head + self.log.path.read_text(encoding='utf-8'), encoding='utf-8')

class WipeWCli(ArgumentParser):
	'''CLI, also used for GUI of FallbackImager'''

	def __init__(self, echo=print, **kwargs):
		'''Define CLI using argparser'''
		self.echo = echo
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-a', '--allbytes', action='store_true',
			help='Write every byte/block (do not check before overwriting block)'
		)
		self.add_argument('-b', '--blocksize', type=int,
			help='Block size in bytes (=n*512, >=512, <= 32768,default is 4096)', metavar='INTEGER'
		)
		self.add_argument('-c', '--create', type=str,
			choices=['ntfs', 'fat32', 'exfat', 'NTFS', 'FAT32', 'EXFAT', 'ExFAT', 'exFAT'],
			help='Create partition [fat32/exfat/ntfs] after wiping a physical drive',
			metavar='STRING'
		)
		self.add_argument('-d', '--driveletter', type=str,
			help='Assign letter to drive (when target is a physical drive)',
			metavar='DRIVE LETTER'
		)
		self.add_argument('-f', '--value', type=str,
			help='Byte to overwrite with as hex (00 - ff)',
			metavar='HEX_BYTE'
		)
		self.add_argument('-g', '--loghead', type=Path,
			help='Use the given file as head when writing log to new drive',
			metavar='FILE'
		)
		self.add_argument('-l', '--listdrives', action='store_true',
			help='List physical drives (ignore all other arguments)'
		)
		self.add_argument('-m', '--mbr', action='store_true',
			help='Use mbr instead of gpt Partition table (when target is a physical drive)'
		)
		self.add_argument('-n', '--name', type=str,
			help='Name/label of the new partition (when target is a physical drive)',
			metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write log', metavar='DIRECTORY'
		)
		self.add_argument('-q', '--maxbadblocks', type=int,
			help='Abort after given number of bad blocks (default is 200)', metavar='INTEGER'
		)
		self.add_argument('-r', '--maxretries', type=int,
			help='Maximum of retries after read or write error (default is 200)',
			metavar='INTEGER'
		)
		self.add_argument('-v', '--verify', action='store_true',
			help='Verify, but do not wipe'
		)
		self.add_argument('-x', '--extra', action='store_true',
			help='Overwrite all bytes/blocks twice, write random bytes at 1st pass'
		)
		self.add_argument('targets', nargs='*', type=str,
			help='Target drive or file(s) (e.g. \\\\.\\PHYSICALDRIVE1)', metavar='DRIVE/FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.targets = args.targets
		self.allbytes = args.allbytes
		self.blocksize = args.blocksize
		self.create = args.create
		self.driveletter = args.driveletter
		self.listdrives = args.listdrives
		self.loghead = args.loghead
		self.maxbadblocks = args.maxbadblocks
		self.maxretries = args.maxretries
		self.mbr = args.mbr
		self.name = args.name
		self.outdir = args.outdir
		self.value = args.value
		self.verify = args.verify
		self.extra = args.extra

	def run(self):
		'''Run zd.exe'''
		if self.listdrives:
			if len(self.targets) > 0:
				raise RuntimeError('Giving targets makes no sense with --listdrives')
			WinUtils.echo_drives(echo=self.echo)
			return
		if self.verify and (self.create or self.extra or self.mbr or self.driveletter or self.name):
			raise RuntimeError(f'Arguments incompatible with --verify/-v')
		wiper = WipeW(echo=self.echo)
		wiper.wipe(self.targets,
			allbytes = self.allbytes,
			blocksize = self.blocksize,
			maxbadblocks = self.maxbadblocks,
			maxretries = self.maxretries,
			outdir = self.outdir,
			value = self.value,
			verify = self.verify,
			extra = self.extra
		)
		if self.create:
			wiper.mkfs(self.targets[0],
				fs = self.create,
				driveletter = self.driveletter,
				loghead = self.loghead,
				mbr = self.mbr,
				name = self.name
			)
		wiper.log.close()

if __name__ == '__main__':	# start here if called as application
	app = WipeWCli()
	app.parse()
	app.run()
