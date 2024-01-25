#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'OscdImager'
__author__ = 'Markus Thilo'
__version__ = '0.3.1_2024-01-25'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
The module uses oscdimg.exe (from the Windows ADK Package) to generate an ISO file (UDF file system).
'''

from pathlib import Path
from argparse import ArgumentParser
from subprocess import Popen, PIPE, STDOUT, STARTUPINFO, STARTF_USESHOWWINDOW
from lib.extpath import ExtPath
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.winutils import WinPopen
from lib.hashes import FileHashes

class OscdImager:
	'''OSCDIMG via subprocess (oscdimg.exe -h -m -l$label -u2 $source $image)'''

	@staticmethod
	def _label(string):
		'''Normalize string so it can be used as ISO label'''
		return ''.join(char for char in string if char.isalnum() or char in ['_', '-'])[:32]

	def __init__(self):
		'''Find oscdimg.exe to gnerate object'''
		for self.exe_path in (
			Path.cwd()/'oscdimg.exe',
			Path.cwd()/'bin'/'oscdimg.exe',
			Path(__file__)/'oscdimg.exe',
			Path(__file__)/'bin'/'oscdimg.exe',
			(Path('C:')/
				'Program Files (x86)'/'Windows Kits'/'10'/'Assessment and Deployment Kit'/
				'Deployment Tools'/'amd64'/'Oscdimg'/'oscdimg.exe'
			)
		):
			if self.exe_path.is_file():
				return
		raise RuntimeError('Unable to find escdimg.exe')

	def create (self, root,
			filename = None,
			outdir = None,
			log = None,
			echo = print
		):
		'''Create logical ISO/UDF image'''
		self.root_path = Path(root)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		if filename:
			self.label = filename
		else:
			self.label = self._label(self.root_path.stem)
		self.image_path = ExtPath.child(f'{self.filename}.iso', parent=self.outdir)
		if log:
			self.log = log
		else:
			self.log = Logger(self.filename, outdir=self.outdir, head='oscdimager.OscdImage', echo=echo)
		self.cmd = [f'{self.exe_path}', '-u2', f'{self.root_path}', f'{self.image_path}']
		self.log.info(f'> {" ".join(self.cmd)}', echo=True)
		proc = WinPopen(self.cmd)
		proc.exec(self.log)
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
