#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'EwfVerify'
__author__ = 'Markus Thilo'
__version__ = '0.3.0_2023-12-26'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Wrapper for ewfverify.
'''

from pathlib import Path
from subprocess import run, Popen, PIPE
from argparse import ArgumentParser
from lib.extpath import ExtPath, FilesPercent
from lib.timestamp import TimeStamp
from lib.logger import Logger

class EwfVerify:
	'''Verify E01/EWF image file'''

	def __init__(self):
		'''Check if ewfverify is callable'''
		if run(['ewfverify' '-h'], capture_output=True, text=True).stderr:
			raise RuntimeError('Unable to use ewfverify from ewf-tools')

	def check(self, image, outdir=None, filename=None, echo=print, log=None):
		'''Verify image'''
		self.image_path = Path(image)
		self.outdir = ExtPath.mkdir(outdir)
		if filename:
			self.filename = filename
		else:
			self.filename = TimeStamp.now_or(filename)
		self.echo = echo
		if log:
			self.log = log
		else:
			self.log = Logger(filename=self.filename, outdir=self.outdir, 
				head=f'isoverify.IsoVerify', echo=echo)
		self.log.info(f'Verifying {self.image_path}', echo=True)
		proc = Popen(['isoverify', f'{self.image_path}'], stdout=PIPE, stderr=PIPE)
		for line in proc.stdout:
			if line:
				print(line)
		#self.log.info(
		#	f'ISO/UDF contains {len(self.files_posix)} files', echo=True)
		#with ExtPath.child(f'{self.filename}_files.txt', parent=self.outdir).open('w') as fh:
		#	fh.write('\n'.join(self.files_posix))

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
