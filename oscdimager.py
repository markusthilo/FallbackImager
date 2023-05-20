#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'OscdImager'
__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-19'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Create ISO image using MS OSCDIMG
'''

from pathlib import Path
from argparse import ArgumentParser
from subprocess import Popen, PIPE, STDOUT, STARTUPINFO, STARTF_USESHOWWINDOW
from lib.extpath import ExtPath
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.greplists import GrepLists
from lib.guielements import BasicFilterTab
from isoverify import IsoVerify

class Oscdimg:
	'''OSCDIMG via subprocess (../bin/oscdimg.exe -u2 $source $image)'''

	EXE_PATHS = (
		Path.cwd()/'oscdimg.exe',
		Path.cwd()/'bin'/'oscdimg.exe',
		Path(__file__)/'oscdimg.exe',
		Path(__file__)/'bin'/'oscdimg.exe',
		(Path('C:')/
			'Program Files (x86)'/'Windows Kits'/
			'10'/'Assessment and Deployment Kit'/'Deployment Tools'/'amd64'/'Oscdimg'/
			'oscdimg.exe'
		)
	)

	def __init__(self, root,
			filename = None,
			outdir = None,
			exe = None,
			echo = print
		):
		'''Init subprocess for OSCDIMG without showing a terminal window'''
		if exe:
			self.exe_path = Path(exe)
		else:
			for self.exe_path in self.EXE_PATHS:
				if self.exe_path.is_file():
					break
		self.root_path = Path(root)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		self.image_path = ExtPath.child(f'{self.filename}.iso', parent=self.outdir)
		self.content_path = ExtPath.child(f'{self.filename}_content.txt', parent=self.outdir)
		self.dropped_path = ExtPath.child(f'{self.filename}_dropped.txt', parent=self.outdir)
		self.echo = echo
		self.log = Logger(self.filename, outdir=self.outdir, head='oscdimg.Oscdimg', echo=echo)
		self.args_str = f'-u2 {self.root_path} {self.image_path}'
		self.cmd_str = f'{self.exe_path} {self.args_str}'
		self.startupinfo = STARTUPINFO()
		self.startupinfo.dwFlags |= STARTF_USESHOWWINDOW

	def create_iso(self):
		'''Create image'''
		self.log.info(f'> {self.exe_path.name} {self.args_str}', echo=True)
		proc = Popen(self.cmd_str,
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
				self.echo(line.strip())
		proc.stdout_str = None
		proc.stderr_str = None
		if self.image_path.is_file():
			self.log.finished(proc, echo=True)
		else:
			self.log.finished(proc, error=': Could not create image\n')

class OscdimgCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-b', '--blacklist', type=Path,
			help='Blacklist (textfile with one regex per line)', metavar='FILE'
		)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('-w', '--whitelist', type=Path,
			help='Whitelist (if given, blacklist is ignored)', metavar='FILE'
		)
		self.add_argument('-x', '--exe', type=Path,
			help='Path to oscdimg.exe (use if not found automatically)', metavar='FILE'
		)
		self.add_argument('root', nargs=1, type=Path,
			help='Source', metavar='DIRECTORY'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.root = args.root[0]
		self.blacklist = args.blacklist
		self.filename = args.filename
		self.outdir = args.outdir
		self.whitelist = args.whitelist
		self.exe = args.exe

	def run(self, echo=print):
		'''Run the imager'''
		image = Oscdimg(self.root,
			filename = self.filename,
			outdir = self.outdir,
			exe = self.exe,
			echo = echo
		)
		image.create_iso()
		drop = GrepLists(
			blacklist = self.blacklist,
			whitelist = self.whitelist, 
			echo = echo
		).get_method()
		IsoVerify(self.root,
			imagepath = image.image_path,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo,
			drop = drop,
			log = image.log
		).posix_verify()
		image.log.close()

class OscdimgGui(BasicFilterTab):
	'''Notebook page'''
	CMD = __app_name__
	DESCRIPTION = __description__
	def __init__(self, root):
		super().__init__(root)

if __name__ == '__main__':	# start here if called as application
	app = OscdimgCli()
	app.parse()
	app.run()
