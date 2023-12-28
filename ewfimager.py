#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'EwfImager'
__author__ = 'Markus Thilo'
__version__ = '0.3.0_2023-12-28'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This tool runs ewfacquire and ewfverify.
'''

from sys import executable as __executable__
from subprocess import Popen, PIPE
from pathlib import Path
from argparse import ArgumentParser
from lib.timestamp import TimeStamp
from lib.extpath import ExtPath
from lib.logger import Logger
from lib.linutils import LinUtils
from ewfverify import EwfVerify

__executable__ = Path(__executable__)
__file__ = Path(__file__)
if __executable__.stem.lower() == __file__.stem.lower():
	__parent_path__ = __executable__.parent
else:
	__parent_path__ = __file__.parent

class EwfImager:
	'''Acquire and verify E01/EWF image'''

	def __init__(self):
		'''Check if ewfverify and ewfverify are present'''
		for self.ewfacquire_path in (
			Path('/usr/bin/ewfacquire'),
			Path('/usr/local/bin/ewfacquire'),
			__parent_path__/'bin/ewfacquire',
			__parent_path__/'ewfacquire'
		):
			if self.ewfverify_path.is_file():
				break
		if not self.ewfverify_path.is_file():
			raise RuntimeError('Unable to use ewfacquire from ewf-tools')
		self.ewfverify = EwfVerify()

	def acquire(self, sources, *args, outdir=None filename=None, echo=print, log=None, **kwargs):
		'''Run ewfacquire'''
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		self.echo = echo
		if log:
			self.log = log
		else:
			self.log = Logger(
				filename = f'{TimeStamp.now(path_comp=True, no_ms=True)}_log.txt',
				outdir = self.outdir, 
				head = 'ewfimager.EwfImager',
				echo = self.echo
			)
		cmd = [f'{self.ewfverify_path}']
		if blocksize:
			cmd.extend(['-b', f'{blocksize}'])
		if value:
			cmd.extend(['-f', f'{value}'])
		if maxbadblocks:
			cmd.extend(['-m', f'{maxbadblocks}'])
		if maxretries:
			cmd.extend(['-r', f'{maxretries}'])
		if verify:
			cmd.append('-v')
		elif allbytes:
			cmd.append('-a')

		for arg in args:
			cmd.append(f'-{arg}')
		for arg, par in kwargs.items():
			cmd.extend([f'-{arg}', f'{par}'])
		for source in sources:
			cmd.append(source)

		print(cmd)
		exit()

		proc = Popen(cmd, stdout=PIPE, stderr=PIPE, text=True)
		for line in proc.stdout:
			msg = line.strip()
			if msg.startswith('...'):
				echo(msg)
			elif msg == '':
				self.echo('')
			else:
				self.log.info(msg, echo=True)
		if stderr := proc.stderr.read():
			self.log.error(f'ewfacquire terminated with: {stderr}')



class WipeRCli(ArgumentParser):
	'''CLI, also used for GUI of FallbackImager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, **kwargs)

		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)



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
		self.add_argument('-f', '--filename', type=str,
			help='Byte to overwrite with as hex (00 - ff)',
			metavar='HEX_BYTE'
		)
		self.add_argument('-g', '--loghead', type=Path,
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
		self.add_argument('source', nargs=1, type=str,
			help='The source file(s) or device', metavar='BLOCKDEVICE/FILE'
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
		self.name = args.name
		self.outdir = args.outdir
		self.value = args.value
		self.verify = args.verify
		self.extra = args.extra

	def run(self, echo=print):
		'''Run zd'''
		if self.verify and (self.create or self.extra or self.mbr or self.driveletter or self.name):
			raise RuntimeError(f'Arguments incompatible with --verify/-v')
		wiper = WipeR()
		wiper.wipe(self.targets,
			allbytes = self.allbytes,
			blocksize = self.blocksize,
			maxbadblocks = self.maxbadblocks,
			maxretries = self.maxretries,
			outdir = self.outdir,
			value = self.value,
			verify = self.verify,
			extra = self.extra,
			echo = echo
		)
		if self.create:
			wiper.mkfs(self.targets[0],
				fs = self.create,
				loghead = self.loghead,
				mbr = self.mbr,
				name = self.name
			)
		wiper.log.close()

if __name__ == '__main__':	# start here if called as application
	app = WipeRCli()
	app.parse()
	app.run()
