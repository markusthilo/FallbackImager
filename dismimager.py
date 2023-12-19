#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'DismImager'
__author__ = 'Markus Thilo'
__version__ = '0.3.0_2023-12-15'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This module is only availible with Admin privileges. It generates an image in the WIM format using DISM/dism.exe. The CLI tool is built into Windows. You can either generate and verify a WMI image or just verify an existing.
'''

from win32com.shell.shell import IsUserAnAdmin
from pathlib import Path
from argparse import ArgumentParser
from sys import executable as __executable__
from shutil import copyfile
from tkinter.messagebox import showerror
from lib.extpath import ExtPath, FilesPercent
from lib.logger import Logger
from lib.dism import CaptureImage, ImageContent
from lib.hashes import FileHashes
from lib.timestamp import TimeStamp

class DismImager:
	'''Create and Verify image with Dism'''

	WIMMOUNT = 'WimMount.exe'

	def __init__(self, root,
			filename = None,
			imagepath = None,
			outdir = None,
			name = None,
			description = None,
			compress = 'none',
			log = None,
			echo = print
		):
		'''Definitihons'''
		self.root_path = Path(root)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		if imagepath:
			self.image_path = Path(imagepath)
		else:
			self.image_path = ExtPath.child(f'{self.filename}.wim', parent=self.outdir)
		self.name = name
		self.description = description
		if compress in ['max', 'fast', 'none']:
			self.compress = compress
		else:
			raise NotImplementedError(self.compress)
		self.echo = echo
		if log:
			self.log = log
		else:
			self.log = Logger(self.filename, outdir=self.outdir, head='dismimager.DismImage', echo=echo)

	def create(self):
		'''Create image'''
		proc = CaptureImage(self.image_path, self.root_path,
			name = self.name,
			description = self.description,		
			compress = self.compress,
			echo = self.echo
		)
		self.log.info(f'Creating {self.image_path.name}', echo=True)
		for line in proc.readlines_stdout():
			self.echo(line)
		if self.image_path.is_file():
			self.log.finished(proc, echo=True)
		else:
			self.log.finished(proc, error=': Could not create image\n')

	def verify(self):
		'''Compare content if image to source'''
		self.log.info(f'\n--- Image hashes ---\n{FileHashes(self.image_path)}\n', echo=True)
		proc = ImageContent(self.image_path, echo=self.echo)
		self.log.info(f'Verifying {self.image_path.name}', echo=True)
		image = set()
		with ExtPath.child(f'{self.filename}_content.txt',
			parent=self.outdir).open(mode='w', encoding='utf-8') as fh:
			for line in proc.readlines_stdout():
				if line and line[0] == '\\':
					print(line, file=fh)
					image.add(line.strip('\\'))
		if len(image) > 0:
			self.log.finished(proc, echo=True)
		else:
			self.log.finished(proc, error=': No or empty image\n')
		missing_file_cnt = 0
		missing_dir_cnt = 0
		missing_else_cnt = 0
		self.echo(f'Comparing {self.image_path.name} to {self.root_path.name}')
		progress = FilesPercent(self.root_path, echo=self.echo)
		with ExtPath.child(f'{self.filename}_missing.txt',
			parent=self.outdir).open(mode='w', encoding='utf-8') as fh:
			for path in ExtPath.walk(self.root_path):
				short = str(path.relative_to(self.root_path)).strip("\\")
				if short in image:
					continue
				if path.is_file():
					progress.inc()
					print(f'\\{short}', file=fh)
					missing_file_cnt += 1
				elif path.is_dir():
					print(f'\\{short}\\', file=fh)
					missing_dir_cnt += 1
				else:
					print(f'\\{short}', file=fh)
					missing_else_cnt += 1
		missing_all_cnt = missing_file_cnt + missing_dir_cnt + missing_else_cnt
		msg = 'Verification:'
		if missing_all_cnt == 0:
			msg += f' no missing files or directories in {self.image_path.name}'
			self.log.info(msg, echo=True)
		else:
			msg += f'\nMissing content {missing_all_cnt} / {missing_file_cnt}'
			msg += f' / {missing_dir_cnt} / {missing_else_cnt}'
			msg += ' (all/files/dirs/other)\n'
			msg += f'Check {self.filename}_missing.txt if relevant content is missing!'
			self.log.warning(msg)

	def copy_exe(self, path=None):
		'''Copy WimMount.exe into destination directory'''
		dest_path = self.outdir/self.WIMMOUNT
		if dest_path.exists():
			self.log.warning(f'{self.WIMMOUNT} already exists in destination directory')
			return
		if not path:
			if Path(__executable__).name.lower() == 'python.exe':
				parent = Path(__file__).parent
			else:
				parent = Path(__executable__).parent
			path = parent/self.WIMMOUNT
			if not path.is_file():
				path = parent/'bin'/self.WIMMOUNT
				if not path.is_file():
					self.log.warning(f'Did not find executable {self.WIMMOUNT}')
					return
		copyfile(path, dest_path)
		self.log.info(f'Copied {self.WIMMOUNT} to destination directory', echo=True)

class DismImagerCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
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
		self.add_argument('-o', '--outdir', type=ExtPath.path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('-p', '--imagepath', type=ExtPath.path,
			help='Image path', metavar='FILE'
		)
		self.add_argument('-v', '--verify', default=False, action='store_true',
			help='Compare content of image to source, do not create'
		)
		self.add_argument('-x', '--exe', default=False, action='store_true',
			help='Copy WimMount.exe to destination directory'
		)
		self.add_argument('root', nargs=1, type=ExtPath.path,
			help='Source', metavar='DIRECTORY'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.root = args.root[0]
		self.description = args.description
		self.filename = args.filename
		self.imagepath = args.imagepath
		self.outdir = args.outdir
		self.name = args.name
		self.compress = args.compress
		self.exe = args.exe
		self.verify = args.verify

	def run(self, echo=print):
		'''Run the imager'''
		image = DismImager(self.root,
			filename = self.filename,
			imagepath = self.imagepath,
			outdir = self.outdir,
			name = self.name,
			description = self.description,
			compress = self.compress,
			echo = echo
		)
		if not self.verify:
			image.create()
		image.verify()
		if self.exe:
			image.copy_exe()
		image.log.close()

if __name__ == '__main__':	# start here if called as application
	if IsUserAnAdmin():
		app = DismImagerCli()
		app.parse()
		app.run()
	else:
		raise RuntimeError('Admin rights required')
