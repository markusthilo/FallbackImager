#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'EwfVerify'
__author__ = 'Markus Thilo'
__version__ = '0.4.0_2024-02-07'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Wrapper for ewfverify.
'''

from sys import executable as __executable__
from pathlib import Path
from argparse import ArgumentParser
from lib.extpath import ExtPath
from lib.openproc import OpenProc
from lib.timestamp import TimeStamp
from lib.linutils import LinUtils
from lib.logger import Logger

__executable__ = Path(__executable__)
__file__ = Path(__file__)
if __executable__.stem.lower() == __file__.stem.lower():
	__parent_path__ = __executable__.parent
else:
	__parent_path__ = __file__.parent

class EwfVerify:
	'''Verify E01/EWF image file'''

	def __init__(self):
		'''Check if ewfverify are present'''
		self.ewfverify_path = LinUtils.find_bin('ewfverify', __parent_path__)
		if not self.ewfverify_path:
			raise RuntimeError('Unable to find ewfverify from libewf')

	def check(self, image, outdir=None, filename=None, echo=print, log=None):
		'''Verify image'''
		self.image_path = Path(image)
		if not self.image_path.suffix:
			self.image_path = self.image_path.with_suffix('.E01')
		self.echo = echo
		if log:
			self.log = log
		else:
			self.outdir = ExtPath.mkdir(outdir)
			if filename:
				self.filename = filename
			else:
				self.filename = TimeStamp.now_or(filename)
			self.log = Logger(filename=self.filename, outdir=self.outdir, 
				head='ewfverify.EwfVerify', echo=self.echo)
		self.log.info('Verifying image', echo=True)
		proc = OpenProc([f'{self.ewfverify_path}', f'{self.image_path}'], log=self.log)
		proc.echo_output()
		if stderr := proc.stderr.read():
			self.log.error(f'ewfverify terminated with: {stderr}', exception=stderr.split('\n')[0])

class EwfVerifyCli(ArgumentParser):
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
		ver = EwfVerify()
		ver.check(self.image,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo
		)
		ver.log.close()

if __name__ == '__main__':	# start here if called as application
	app = EwfVerifyCli()
	app.parse()
	app.run()
