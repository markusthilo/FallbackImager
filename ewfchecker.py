#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'EwfVerify'
__author__ = 'Markus Thilo'
__version__ = '0.4.0_2024-02-08'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Verify EWF/E01 image using disktype. ewfinfo, ewfverify and ewfexport.
'''

from sys import executable as __executable__
from pathlib import Path
from argparse import ArgumentParser
from lib.extpath import ExtPath
from lib.openproc import OpenProc
from lib.timestamp import TimeStamp
from lib.linutils import LinUtils
from lib.logger import Logger

if Path(__file__).suffix.lower() == '.pyc':
	__parent_path__ = Path(__executable__).parent
else:
	__parent_path__ = Path(__file__).parent

class EwfChecker:
	'''Verify E01/EWF image file'''

	def __init__(self):
		'''Check if the needed binaries are present'''
		self.ewfverify_path = LinUtils.find_bin('ewfverify', __parent_path__)
		if not self.ewfverify_path:
			raise RuntimeError('Unable to find ewfverify from libewf')
		self.ewfinfo_path = LinUtils.find_bin('ewfinfo', __parent_path__)
		if not self.ewfinfo_path:
			raise RuntimeError('Unable to find ewfinfo from libewf')
		self.ewfexport_path = LinUtils.find_bin('ewfexport', __parent_path__)
		if not self.ewfexport_path:
			raise RuntimeError('Unable to find ewfexport from libewf')
		self.disktype_path = LinUtils.find_bin('disktype', __parent_path__)
		if not self.disktype_path:
			raise RuntimeError('Unable to find disktype')

	def check(self, image, outdir=None, filename=None, echo=print, log=None):
		'''Verify image'''
		self.image_path = Path(image)
		if not self.image_path.suffix:
			self.image_path = self.image_path.with_suffix('.E01')
		self.echo = echo
		self.outdir = ExtPath.mkdir(outdir)
		if filename:
			self.filename = filename
		else:
			self.filename = self.image_path.name
		if log:
			self.log = log
		else:
			self.log = Logger(filename=self.filename, outdir=self.outdir, 
				head='ewfchecker.EwfChecker', echo=self.echo)
		self.log.info('Image informations', echo=True)
		proc = OpenProc([f'{self.ewfinfo_path}', f'{self.image_path}'], log=self.log)
		proc.echo_output(skip=2)
		if proc.returncode != 0:
			self.log.warning(proc.stderr.read())
		raw = (self.outdir/self.filename).with_suffix('')
		proc = OpenProc([f'{self.ewfexport_path}', '-B', '10240', '-u', '-q', '-t', f'{raw}', f'{self.image_path}'])
		if proc.wait() != 0:
			self.log.warning(proc.stderr.read())
		else:
			raw = Path(f'{raw}.raw')
			info = Path(f'{raw}.info')
			xxd = ExtPath.readable_bin(raw)
			self.log.info(f'Image starts with:\n\n{xxd}', echo=True)
			self.log.info('Probing for partition table')
			proc = OpenProc([f'{self.disktype_path}', f'{raw}'], log=self.log)
			proc.echo_output(skip=2)
			raw.unlink(missing_ok=True)
			info.unlink(missing_ok=True)
		self.log.info('Verifying image', echo=True)
		proc = OpenProc([f'{self.ewfverify_path}', '-V'])
		if proc.wait() != 0:
			self.log.error(proc.stderr.read())
		info = proc.stdout.read().splitlines()[0]
		self.log.info(f'Using {info}', echo=True)
		proc = OpenProc([f'{self.ewfverify_path}', '-d', 'sha256', f'{self.image_path}'], log=self.log)
		proc.echo_output(cnt=8)
		if stderr := proc.stderr.read():
			self.log.error(f'ewfacquire terminated with: {stderr}', exception=stderr.split('\n'))

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
