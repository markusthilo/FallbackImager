#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'OscdImager'
__author__ = 'Markus Thilo'
__version__ = '0.5.0_2024-04-24'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
The module uses oscdimg.exe (from the Windows ADK Package) to generate an ISO file (UDF file system).
'''

from sys import executable as __executable__
from pathlib import Path
from argparse import ArgumentParser
from lib.extpath import ExtPath
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.winutils import WinUtils, OpenProc
from lib.hashes import FileHashes

if Path(__file__).suffix.lower() == '.pyc':
	__parent_path__ = Path(__executable__).parent
else:
	__parent_path__ = Path(__file__).parent

class OscdImager:
	'''OSCDIMG via subprocess (oscdimg.exe -h -m -u2 -l$label $source $image)'''

	def __init__(self):
		'''Look for oscdimg.exe'''
		self.oscdimg_path = WinUtils.find_exe('oscdimg.exe', __parent_path__,
		Path(__parent_path__/'Oscdimg'),
		Path(__parent_path__/'bin'/'Oscdimg'),
		Path('C:\\Program Files (x86)\\Windows Kits\\10\\Assessment and Deployment Kit\\Deployment Tools\\amd64\\Oscdimg'))
		if self.oscdimg_path:
			self.available = True
		else:
			self.available = False

	def create (self, root,
			filename = None,
			outdir = None,
			log = None,
			echo = print
		):
		'''Create logical ISO/UDF image'''
		self.root_path = ExtPath.path(root)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		if filename:
			self.label = filename
		else:
			self.filename = ''.join(char for char in self.root_path.stem
				if char.isalnum() or char in ['_', '-']
			)
		self.label = self.filename[:32]
		self.image_path = ExtPath.child(f'{self.filename}.iso', parent=self.outdir)
		if log:
			self.log = log
		else:
			self.log = Logger(self.filename, outdir=self.outdir, head='oscdimager.OscdImager', echo=echo)
		self.cmd = [
			f'{self.oscdimg_path}',
			'-h', '-m', '-u2',
			f'-l{self.label}',
			f'{self.root_path}',
			f'{self.image_path}'
		]
		self.log.info(f'> {" ".join(self.cmd)}', echo=True)
		proc = OpenProc(self.cmd, log=self.log)
		proc.echo_output(cnt=3)
		if not self.image_path.is_file():
			self.log.error(f'Could not create image {self.image_path}')
		self.log.info('Calculating hashes', echo=True)
		self.log.info(FileHashes(self.image_path), echo=True)

class OscdImagerCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('root', nargs=1, type=ExtPath.path,
			help='Source', metavar='DIRECTORY'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.root = args.root[0]
		self.filename = args.filename
		self.outdir = args.outdir

	def run(self, echo=print):
		'''Run the imager'''
		image = OscdImager()
		image.create(self.root,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo
		)
		image.log.close()

if __name__ == '__main__':	# start here if called as application
	app = OscdImagerCli()
	app.parse()
	app.run()
