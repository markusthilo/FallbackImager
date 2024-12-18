#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'WipeR'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2024-12-18'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This is a wipe tool designed for SSDs and HDDs. There is also the possibility to overwrite files but without erasing file system metadata.

By default only unwiped blocks (or SSD pages) are overwritten though it is possible to force the overwriting of every block or even use a two pass wipe (1st pass writes random values). Instead of zeros you can choose to overwrite with a given byte value.

Whe the target is a physical drive, you can create a partition where (after a successful wipe) the log is copied into. A custom head for this log can be defined in a text file (wipe-head.txt by default).

Be aware that this module is extremely dangerous as it is designed to erase data!
'''

from pathlib import Path
from argparse import ArgumentParser
from lib.timestamp import TimeStamp
from lib.extpath import ExtPath
from lib.logger import Logger
from lib.linutils import LinUtils, OpenProc

__parent_path__ = Path(__file__).parent

class WipeR:
	'''Frontend and Python wrapper for zd'''

	MIN_BLOCKSIZE = 512
	STD_BLOCKSIZE = 4096
	MAX_BLOCKSIZE = 32768

	def __init__(self, echo=print, utils=None):
		'''Look for zd'''
		self.zd_path = LinUtils.find_bin('zd', __parent_path__)
		if self.zd_path:
			self.available = True
		else:
			self.available = False
		self.echo = echo
		self.utils = utils

	def wipe(self, targets,
			verify = False,
			allbytes = False,
			extra = False,
			value = False,
			blocksize = None,
			maxbadblocks = None,
			maxretries = None,
			log = None,
			outdir = None,
		):
		if len(targets) == 0:
			raise FileNotFoundError('Missing drive or file(s) to wipe')
		if verify and allbytes and extra:
			raise RuntimeError(f'Too many arguments - you can perform normal wipe, all bytes, extra/2-pass or just verify')
		if blocksize and (
				blocksize % self.MIN_BLOCKSIZE != 0 or blocksize < self.MIN_BLOCKSIZE or blocksize > self.MAX_BLOCKSIZE
			):
				raise ValueError(f'Block size has to be n * {MIN_BLOCKSIZE}, >={MIN_BLOCKSIZE} and <={MAX_BLOCKSIZE}')
		if value:
			try:
				int(value, 16)
			except ValueError:
				raise ValueError('Byte to overwrite with (-f/--value) has to be a hex value')
			if int(value, 16) < 0 or int(value, 16) > 0xff:
				raise ValueError('Byte to overwrite (-f/--value) has to be inbetween 00 and ff')
		if not self.utils:
			self.utils = LinUtils()
		if ExtPath.path(targets[0]).is_block_device():
			if len(targets) > 1:
				raise RuntimeError('Only one physical drive at a time')
			if not verify:
				for partition in LinUtils.lspart(targets[0]):
					if LinUtils.get_mountpoints(partition):
						stdout, stderr = self.utils.umount(partition)
						if stderr:
							raise RuntimeError(stderr)
		elif not extra and not verify:
			allbytes = True
		self.outdir = ExtPath.mkdir(outdir)
		self.log = log if log else Logger(
			filename = f'{TimeStamp.now(path_comp=True, no_ms=True)}_wipe',
			outdir = self.outdir, 
			head = 'wiper.WipeR',
			echo = self.echo
		)
		self.cmd = [f'{self.zd_path}']
		if blocksize:
			self.cmd.extend(['-b', f'{blocksize}'])
		if value:
			self.cmd.extend(['-f', f'{value}'])
		if maxbadblocks:
			self.cmd.extend(['-m', f'{maxbadblocks}'])
		if maxretries:
			self.cmd.extend(['-r', f'{maxretries}'])
		if verify:
			cmd.append('-v')
		elif allbytes:
			self.cmd.append('-a')
		elif extra:
			self.cmd.append('-x')


		return

		show_progress = lambda msg: print(f'\r{msg}', end='') if self.echo == print else lambda msg: self.echo(f'\n{msg}', overwrite=True)
		for target in targets:
			proc = OpenProc(self.cmd, target, sudo=self.utils.sudo, password=self.utils.password)
			for line in proc.stdout:
				msg = line.strip()
				if msg.startswith('...'):
					show_progress(msg)
				elif msg == '':
					self.echo('')
				else:
					self.log.info(msg, echo=True)
			if stderr := proc.stderr.read():
				msg = f'Unable to wipe {target}, zd terminated: {stderr}'
				if target == targets[-1]:
					self.log.error(msg)
				else:
					self.log.warning(msg)

	def create(self, target,
			fs = None,
			loghead = None,
			mbr = False,
			name = None,
			mnt = None
		):
		'''Generate partition and file system'''
		if loghead:
			loghead = ExtPath.path(loghead)
		else:
			loghead = __parent_path__/'wipe-log-head.txt'
		partition, stderr = self.utils.init_blkdev(target, mbr=mbr, fs=fs, name=name)
		if stderr:
			self.log.warning(stderr)
			return

		mountpoint, stderr = self.utils.mount(partition, mnt=mnt)

		if stderr:
			self.log.warning(stderr)
			return
		self.log.info('Disk preparation successful', echo=True)
		self.log.close()
		log_path = Path(mountpoint)/'wipe-log.txt'
		try:
			head = loghead.read_text()
		except FileNotFoundError:
			head = ''
		with log_path.open('w') as fh:
			fh.write(head + self.log.path.read_text())

class WipeRCli(ArgumentParser):
	'''CLI, also used for GUI of FallbackImager'''

	def __init__(self, echo=print, utils=None, **kwargs):
		self.echo = echo
		self.utils = utils
		'''Define CLI using argparser'''
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
		self.add_argument('-f', '--value', type=str,
			help='Byte to overwrite with as hex (00 - ff)',
			metavar='HEX_BYTE'
		)
		self.add_argument('-g', '--loghead', type=ExtPath.path,
			help='Use the given file as head when writing log to new drive',
			metavar='FILE'
		)
		self.add_argument('-m', '--mbr', action='store_true',
			help='Use mbr instead of gpt Partition table (when target is a physical drive)'
		)
		self.add_argument('-n', '--name', type=str,
			help='Name/label of the new partition (when target is a physical drive)',
			metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write log', metavar='DIRECTORY'
		)
		self.add_argument('-p', '--mount', type=ExtPath.path,
			help='Mountpoint to the new partition (when target is a physical drive)',
			metavar='DIRECTORY'
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
		self.add_argument('targets', nargs='*', type=ExtPath.path,
			help='Target blockdevice or file(s) (/dev/sdc)', metavar='BLOCKDEVICE/FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.targets = args.targets
		self.allbytes = args.allbytes
		self.blocksize = args.blocksize
		self.create = args.create
		self.loghead = args.loghead
		self.maxbadblocks = args.maxbadblocks
		self.maxretries = args.maxretries
		self.mbr = args.mbr
		self.mountpoint = args.mount
		self.name = args.name
		self.outdir = args.outdir
		self.value = args.value
		self.verify = args.verify
		self.extra = args.extra

	def run(self):
		'''Run zd'''
		if self.verify and (
			self.create or
			self.extra or
			self.mbr or
			self.mountpoint or
			self.name
		):
			raise RuntimeError(f'Arguments incompatible with --verify/-v')
		if self.targets[0].is_block_device():
			if len(self.targets) > 1:
				raise ValueError('Too many arguments: only one block device at a time')
			if LinUtils.is_part(self.targets[0]) and self.create:
				raise ValueError(f'{self.targets[0]} is a partition but parameter to generate one was given)')
		else:
			for file_path in self.targets:
				if not file_path.exists():
					raise FileNotFoundError(f'{file_path} does not exist')
				if not file_path.is_file():
					raise ValueError(f'{file_path} is not a regular file')
		wiper = WipeR(echo=self.echo, utils=self.utils)
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
			wiper.create(self.targets[0],
				fs = self.create,
				loghead = self.loghead,
				mbr = self.mbr,
				name = self.name,
				mnt = self.mountpoint
			)
		wiper.log.close()

if __name__ == '__main__':	# start here if called as application
	app = WipeRCli()
	app.parse()
	app.run()
