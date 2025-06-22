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
from lib.pathutils import PathUtils
from lib.timestamp import TimeStamp
from lib.linutils import LinUtils, OpenProc
from lib.logger import Logger

class EwfChecker:
	'''Verify E01/EWF image file'''

	def __init__(self, echo=print):
		'''Check if the needed binaries are present'''
		parent_path = Path(__file__).parent
		self.ewfverify_path = LinUtils.find_bin('ewfverify', parent_path)
		self.ewfinfo_path = LinUtils.find_bin('ewfinfo', parent_path)
		self.ewfmount_path = LinUtils.find_bin('ewfmount', parent_path)
		self.available = True if self.ewfverify_path and self.ewfinfo_path and self.ewfmount_path else False
		self.echo = echo

	def check(self, image, outdir=None, filename=None, echo=print, log=None, hashes=None, sudo=None):
		'''Verify image'''
		self.image_path = Path(image)
		if not self.image_path.suffix:
			self.image_path = self.image_path.with_suffix('.E01')
		self.outdir = PathUtils.mkdir(outdir)
		self.filename = filename if filename else self.image_path.stem
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
		mount_path = Path(f'/tmp/{self.image_path.stem}_{self.hashes["md5"]}')
		try:
			mount_path.mkdir(exist_ok=True)
		except Exception as ex:
			self.log.warning(f'Unable to create directory {mount_path}\n{ex}')
			return
		proc = OpenProc([f'{self.ewfmount_path}', f'{self.image_path}', f'{mount_path}'], log=self.log)
		if proc.echo_output() != 0:
			self.log.error(f'ewfmount terminated with:\n{proc.stderr.read()}')
		else:
			ewf_path = mount_path.joinpath(next(mount_path.iterdir()))
			xxd = PathUtils.read_bin(ewf_path)
			self.log.info(f'Image starts with:\n\n{xxd}', echo=True)
			self.log.info('Trying to read partition table')
			ret = run(['fdisk', '-l', f'{ewf_path}'], capture_output=True, text=True)
			if ret.stderr:
				self.log.warning(ret.stderr)
			else:
				msg = ''
				for line in ret.stdout.split('\n'):
					if not line:
						continue
					line = sub(' {2,}', ' ', line)
					if line.startswith(f'Disk {ewf_path}:'):
						msg += f'This might be a disk image\nDisk size:{line.split(":", 1)[1]}\n'
					elif line.startswith(f'{ewf_path}'):
						msg += f'Part{line[len(f"{ewf_path}p"):]}\n'
					else:
						msg += f'{line}\n'
				self.log.info(msg, echo=True)
			ret = run(['umount', f'{mount_path}'], capture_output=True, text=True)
			if ret.stderr:
				self.log.warning(ret.stderr)
			mount_path.rmdir()
		
class EwfCheckerCli(ArgumentParser):
	'''CLI for EwfVerify'''

	def __init__(self, echo=print):
		'''Define CLI using argparser'''
		self.echo = echo
		super().__init__(description=__description__, prog=__app_name__.lower())
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('image', nargs=1, type=Path,
			help='EWF/E01 image file', metavar='FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.image = args.image[0]
		self.filename = args.filename
		self.outdir = args.outdir

	def run(self):
		'''Run the verification'''
		checker = EwfChecker(echo=self.echo)
		checker.check(self.image,
			filename = self.filename,
			outdir = self.outdir
		)
		checker.log.close()

if __name__ == '__main__':	# start here if called as application
	app = EwfCheckerCli()
	app.parse()
	app.run()
