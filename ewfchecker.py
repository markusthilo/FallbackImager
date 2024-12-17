#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'EwfVerify'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2024-12-17'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Verify EWF/E01 image using ewfinfo, ewfverify and ewfmount.
'''

from pathlib import Path
from subprocess import run
from re import sub
from argparse import ArgumentParser
from lib.extpath import ExtPath
from lib.timestamp import TimeStamp
from lib.linutils import LinUtils, OpenProc
from lib.logger import Logger

class EwfChecker:
	'''Verify E01/EWF image file'''

	def __init__(self, echo=print, utils=None):
		'''Check if the needed binaries are present'''
		parent_path = Path(__file__).parent
		self.ewfverify_path = LinUtils.find_bin('ewfverify', parent_path)
		self.ewfinfo_path = LinUtils.find_bin('ewfinfo', parent_path)
		self.ewfmount_path = LinUtils.find_bin('ewfmount', parent_path)
		self.available = True if self.ewfverify_path and self.ewfinfo_path and self.ewfmount_path else False
		self.echo = echo
		self.utils = utils

	def check(self, image, outdir=None, filename=None, echo=print, log=None, hashes=None, sudo=None):
		'''Verify image'''
		self.image_path = ExtPath.path(image)
		if not self.image_path.suffix:
			self.image_path = self.image_path.with_suffix('.E01')
		self.outdir = ExtPath.mkdir(outdir)
		self.filename = filename if filename else self.image_path.name
		self.log = log if log else Logger(filename=self.filename, outdir=self.outdir, 
			head='ewfchecker.EwfChecker', echo=self.echo)
		self.log.info('Image informations', echo=True)
		proc = OpenProc([f'{self.ewfinfo_path}', f'{self.image_path}'], log=self.log, sudo=sudo)
		proc.echo_output(skip=2)
		if proc.returncode != 0:
			self.log.warning(proc.stderr.read())
		self.log.info('Verifying image', echo=True)
		proc = OpenProc([f'{self.ewfverify_path}', '-V'])
		if proc.wait() != 0:
			self.log.error(proc.stderr.read())
		info = proc.stdout.read().splitlines()[0]
		self.log.info(f'Using {info}', echo=True)
		proc = OpenProc([f'{self.ewfverify_path}', '-d', 'sha256', f'{self.image_path}'],
			log=self.log, sudo=sudo)
		if proc.echo_output(cnt=8) != 0:
			self.log.error(f'ewfverify terminated with:\n{proc.stderr.read()}')
		self.hashes = dict()
		for line in proc.stack:
			if line.startswith('MD5 hash calculated over data:'):
				self.hashes['md5'] = line.split(':', 1)[1].strip()
			elif line.startswith('SHA256 hash calculated over data:'):
				self.hashes['sha256'] = line.split(':', 1)[1].strip()
		if hashes:
			for alg, hash in self.hashes.items():
				if hash.lower() != hashes[alg].lower():
					selg.log.error('Mismatching hashes')
		parent = f'/run/media/{LinUtils.whoami()}'
		stdout, stderr = self.utils.mkdir(parent, exists_ok=True)
		if stderr:
			self.log.warning(f'Unable to create directory {parent}\n{stderr}')
		mountpoint = f'{parent}/{self.hashes["md5"]}'
		stdout, stderr = self.utils.mkdir(mountpoint, exists_ok=True)
		if stderr:
			self.log.warning(f'Unable to create directory {mountpoint} to mount image\n{stderr}')
		else:
			self.log.debug(stdout, echo=True)
			proc = OpenProc([f'{self.ewfmount_path}', f'{self.image_path}', f'{mountpoint}'],
				sudo=self.utils.sudo, password=self.utils.password, log=self.log)
			if proc.echo_output() != 0:
				self.log.error(f'ewfmount terminated with:\n{proc.stderr.read()}')
			else:
				ewf = mountpoint/'ewf1'
				xxd = ExtPath.read_bin(ewf)
				self.log.info(f'Image starts with:\n\n{xxd}', echo=True)
				self.log.info('Trying to read partition table')
				rrun = LinUtils(sudo=sudo)
				stdout, stderr = rrun.fdisk(ewf)
				if stderr:
					self.log.warning(stderr)
				else:
					msg = ''
					for line in stdout.split('\n'):
						if not line:
							continue
						line = sub(' {2,}', ' ', line)
						if line.startswith(f'Disk {ewf}:'):
							msg += f'This might be a disk image\nDisk size:{line.split(":", 1)[1]}\n'
						elif line.startswith(f'{ewf}'):
							msg += f'Part{line[len(f"{ewf}p"):]}\n'
						else:
							msg += f'{line}\n'
					self.log.info(msg, echo=True)
				if ret.stderr:
					self.log.warning(proc.stderr)
				stdout, stderr = self.utils.umount(mountpoint, rmdir=True)
				if stderr:
					self.log.warning(f'Something went wrong while unmounting and deleting {mountpoint}\n{stderr}')
		
class EwfCheckerCli(ArgumentParser):
	'''CLI for EwfVerify'''

	def __init__(self):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, prog=__app_name__.lower())
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('image', nargs=1, type=ExtPath.path,
			help='EWF/E01 image file', metavar='FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.image = args.image[0]
		self.filename = args.filename
		self.outdir = args.outdir

	def run(self, echo=print):
		'''Run the verification'''
		checker = EwfChecker()
		checker.check(self.image,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo
		)
		checker.log.close()

if __name__ == '__main__':	# start here if called as application
	app = EwfCheckerCli()
	app.parse()
	app.run()
