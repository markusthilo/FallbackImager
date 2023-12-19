#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'MkIsoImager'
__author__ = 'Markus Thilo'
__version__ = '0.3.0_2023-12-18'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This tool generates an ISO file (UDF file system) using mkisofs. It will log files that cannot be handled properly.
'''

from sys import executable as __executable__
from os import name as __os_name__
from pathlib import Path
from argparse import ArgumentParser
from subprocess import Popen, PIPE, STDOUT, STARTUPINFO, STARTF_USESHOWWINDOW
from lib.extpath import ExtPath
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.hashes import FileHashes
from isoverify import IsoVerify

__executable__ = Path(__executable__)
__file__ = Path(__file__)
if __executable__.stem.lower() == __file__.stem.lower():
	__parent_path__ = __executable__.parent
else:
	__parent_path__ = __file__.parent

class MkIsoImager:
	'''MAKEISOFS via subprocess (mkisofs -udf -o $image -V %label $source)'''

	def __init__(self):
		'''Generate object to use mkisofs'''
		if __os_name__ == 'nt':
			for self.mkisofs_path in (
				__parent_path__/'bin/mkisofs.exe',
				__parent_path__/'mkisofs.exe'
			):
				if self.mkisofs_path.is_file():
					break
		else:
			for self.mkisofs_path in (
				Path('/usr/bin/mkisofs'),
				Path('/usr/local/bin/mkisofs'),
				__parent_path__/'bin/mkisofs',
				__parent_path__/'mkisofs'
			):
				if self.mkisofs_path.is_file():
					break
		if not self.mkisofs_path.is_file():
			if __os_name__ == 'nt':
				raise RuntimeError('Uanbale to locate mkisofs.exe')
			raise RuntimeError('Uanbale to locate mkisofs')

	def labelize(string):
		'''Generate ISO conform label from string'''
		return ''.join(char for char in string if char.isalnum() or char in ['_', '-'])[:32]

	def create(self, root,
			filename = None,
			outdir = None,
			name = None,
			log = None,
			echo = print
		):
		'''Create image'''
		self.root_path = Path(root)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		self.label = ''.join(char for char in self.root_path.stem
			if char.isalnum() or char in ['_', '-'])[:32]
		self.image_path = ExtPath.child(f'{self.filename}.iso', parent=self.outdir)
		self.content_path = ExtPath.child(f'{self.filename}_content.txt', parent=self.outdir)
		self.dropped_path = ExtPath.child(f'{self.filename}_dropped.txt', parent=self.outdir)
		if log:
			self.log = log
		else:
			self.log = Logger(self.filename, outdir=self.outdir, head='mkisoimager.MkIsoImager', echo=echo)
		self.cmd = f'{self.mkisofs_path} -udf -o "{self.image_path}" -V "{self.label}" "{self.root_path}"'
		self.log.info(f'> {self.cmd}', echo=True)
		self.startupinfo = STARTUPINFO()
		self.startupinfo.dwFlags |= STARTF_USESHOWWINDOW
		proc = Popen(self.cmd,
			shell = True,
			stdout = PIPE,
			stderr = STDOUT,
			encoding = 'utf-8',
			errors = 'ignore',
			universal_newlines = True,
			startupinfo = self.startupinfo
		)
		for line in proc.stdout:
			if line.strip():
				echo(line.strip())
		proc.stdout_str = None
		proc.stderr_str = None
		if self.image_path.is_file():
			self.log.finished(proc, echo=True)
		else:
			self.log.finished(proc, error=': Could not create image\n')
		self.log.info(f'\n--- Image hashes ---\n{FileHashes(self.image_path)}', echo=True)

class MkIsoImagerCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, prog=__app_name__.lower(), **kwargs)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-n', '--name', type=str,
			help='Label of the ISO', metavar='STRING'
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
		self.name = args.name
		self.outdir = args.outdir

	def run(self, echo=print):
		'''Run the imager'''
		imager = MkIsoImager()

		imager.create(self.root,
			filename = self.filename,
			outdir = self.outdir,
			name = self.name,
			echo = echo
		)
		IsoVerify(self.root,
			imagepath = imager.image_path,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo,
			log = imager.log
		).posix_verify()
		image.log.close()

if __name__ == '__main__':	# start here if called as application
	app = MkIsoImagerCli()
	app.parse()
	app.run()
