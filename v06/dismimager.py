#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'DismImager'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2024-12-27'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This module is only availible with Admin privileges. It generates an image in the WIM format using DISM/dism.exe. The CLI tool is built into Windows. You can either generate and verify a WMI image or just verify an existing.
'''

from sys import executable as __executable__
from os import environ
from win32com.shell.shell import IsUserAnAdmin
from pathlib import Path
from argparse import ArgumentParser
from shutil import copyfile
from lib.pathutils import PathUtils, Progressor
from lib.winutils import WinUtils, OpenProc
from lib.logger import Logger
from lib.hashes import FileHashes
from lib.timestamp import TimeStamp

__parent_path__ = Path(__executable__).parent if Path(__file__).suffix.lower() == '.pyc' else Path(__file__).parent

class DismImager:
	'''Create and Verify image with Dism'''

	WIMMOUNT = 'WimMount.exe'

	def __init__(self, echo=print):
		'''Look for dism.exe'''
		self.dism_path = Path(environ['SYSTEMDRIVE'])/'\\Windows\\system32\\dism.exe'
		if self.dism_path.is_file() and IsUserAnAdmin():
			self.available = True
			self.echo = echo
		else:
			self.available = False

	def create(self, root,
			filename = None,
			image = None,
			outdir = None,
			name = None,
			description = None,
			compress = 'none',
			log = None,
		):
		'''Create image'''
		if root:
			self.root_path = Path(root)
		else:
			raise ValueError('Source is missing')
		self.filename = TimeStamp.now_or(filename)
		self.outdir = PathUtils.mkdir(outdir)
		self.image_path = Path(image) if image else outdir / f'{self.filename}.wim'
		self.name = name if name else self.root_path.name
		self.description = TimeStamp.now_or(description)
		if compress in ['max', 'fast', 'none']:
			self.compress = compress
		else:
			raise NotImplementedError(f'Unknown compression "{compress}"')
		self.log = log if log else Logger(self.filename, outdir=self.outdir, head='dismimager.DismImage', echo=self.echo)
		self.log.info(f'Creating image', echo=True)
		cmd = f'{self.dism_path} /Capture-Image /ImageFile:"{self.image_path}"'
		cmd += f' /CaptureDir:"{self.root_path}" /Name:"{self.name}" /Description:"{self.description}"'
		cmd += f' /Compress:{self.compress}'
		self.log.info(f'> {cmd}', echo=True)
		if self.echo == print:
			echo = lambda msg: print(f'\r{msg}', end='')
		else:
			echo = lambda msg: self.echo(f'\n{msg}', overwrite=True)
		proc = OpenProc(cmd, log=self.log)
		for line in proc.stdout:
			msg = line.strip()
			if msg:
				if msg.endswith(']'):
					echo(msg)
					if msg.endswith('=]'):
						self.echo()
				else:
					self.log.info(msg, echo=True)
		if not self.image_path.is_file():
			self.log.error(f'Could not create image {self.image_path}')
		self.echo('Calculating hashes')
		self.log.info(f'\n--- Image hashes ---\n{FileHashes(self.image_path)}\n', echo=True)
		cmd = f'{self.dism_path} /List-Image /ImageFile:"{self.image_path}" /Index:1'
		file_cnt = 0
		dir_cnt = 0
		self.log.info(f'> {cmd}', echo=True)
		with self.outdir.joinpath(f'{self.filename}.tsv').open('w', encoding='utf-8') as tsv_fh:
			print('Path\tType', file=tsv_fh)
			proc = OpenProc(cmd, log=self.log)
			for line in proc.stdout:
				path = line.strip()
				if path:
					if path.startswith('\\'):
						path = path.lstrip('\\')
						if path:
							if path.endswith('\\'):
								print(f'"{path}"\tDir', file=tsv_fh)
								dir_cnt += 1
							else:
								print(f'"{path}"\tFile', file=tsv_fh)
								file_cnt += 1
					else:
						self.log.info(msg, echo=True)
		self.log.info(f'Image contains {file_cnt} file(s) and {dir_cnt} dir(s)', echo=True)

	def copy_exe(self, path=None):
		'''Copy WimMount.exe into destination directory'''
		dest_path = self.outdir/self.WIMMOUNT
		if dest_path.exists():
			self.log.warning(f'{self.WIMMOUNT} already exists in destination directory')
			return
		if path:
			self.wimmount_path = path
		else:
			self.wimmount_path = WinUtils.find_exe(self.WIMMOUNT, __parent_path__)
		if self.wimmount_path:
			copyfile(self.wimmount_path, dest_path)
			self.log.info(f'Copied {self.WIMMOUNT} to destination directory', echo=True)
		else:
			self.log.warning(f'Did not find executable {self.WIMMOUNT}')

class DismImagerCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self, echo=print, **kwargs):
		'''Define CLI using argparser'''
		self.echo = echo
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-c', '--compress', type=str, default='none',
			choices=['max', 'fast', 'none'],
			help='Compression max|fast|none, none is default', metavar='STRING'
		)
		self.add_argument('-d', '--description', type=str,
			help='Additional description to the image file', metavar='STRING'
		)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-n', '--name', type=str,
			help='Intern name of the image in the WMI file', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('-x', '--exe', default=False, action='store_true',
			help='Copy WimMount.exe to destination directory'
		)
		self.add_argument('root', nargs='?', type=Path,
			help='Source', metavar='DIRECTORY'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.root = args.root
		self.description = args.description
		self.filename = args.filename
		self.outdir = args.outdir
		self.name = args.name
		self.compress = args.compress
		self.exe = args.exe

	def run(self):
		'''Run the imager'''
		imager = DismImager(echo=self.echo)
		imager.create(self.root,
			filename = self.filename,
			outdir = self.outdir,
			name = self.name,
			description = self.description,
			compress = self.compress
		)
		if self.exe:
			imager.copy_exe()
		imager.log.close()

if __name__ == '__main__':	# start here if called as application
	if IsUserAnAdmin():
		app = DismImagerCli()
		app.parse()
		app.run()
	else:
		raise RuntimeError('Admin rights required')
