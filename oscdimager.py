#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-13'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Create ISO image using OSCDIMG'

from pathlib import Path
from argparse import ArgumentParser
from subprocess import Popen, PIPE, STDOUT, STARTUPINFO, STARTF_USESHOWWINDOW
from lib.extpath import ExtPath
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.hashes import FileHashes

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
			imagepath = None,
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
		if imagepath:
			self.image_path = Path(imagepath)
		else:
			self.image_path = ExtPath.child(f'{self.filename}.iso', parent=self.outdir)
		self.content_path = ExtPath.child(f'{self.filename}_content.txt', parent=self.outdir)
		self.dropped_path = ExtPath.child(f'{self.filename}_dropped.txt', parent=self.outdir)
		self.echo = echo
		self.log = Logger(self.filename, outdir=self.outdir, head='oscdimg.Oscdimg')
		self.args_str = f'-u2 {self.root_path} {self.image_path}'
		self.cmd_str = f'{self.exe_path} {self.args_str}'
		self.startupinfo = STARTUPINFO()
		self.startupinfo.dwFlags |= STARTF_USESHOWWINDOW

	def _read_stream(self, stream, verbose=False):
		'''Read stdout or stderr to string'''
		string = stream.read().strip()
		if verbose:
			self.echo(string)
		return string

	def read_stdout(self):
		'''Read stdout'''
		self.stdout_str = self._read_stream(self.stdout, verbose=self.verbose_stdout)
		return self.stdout_str

	def read_stderr(self):
		'''Read stderr'''
		self.stderr_str = self._read_stream(self.stderr, verbose=self.verbose_stderr)
		return self.stderr_str

	def read_all(self):
		'''Get full stdout and stderr as strings'''
		return self.read_stdout(), self.read_stderr()

	def readlines_stdout(self):
		'''Read stdout line by line''' 
		for line in self.stdout:
			line = line.strip()
			if self.verbose_stdout:
				self.echo(line)
			if line:
				yield line
		self.stdout_str = None
		self.read_stderr()

	def create_iso(self):
		'''Create image'''
		self.log.info(f'> {self.exe_path.name} {self.args_str}', echo=True)
		proc = Popen(self.cmd_str,
			shell = True,
			stdout = PIPE,
			stderr = STDOUT,#PIPE,
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

	def verify_iso(self):
		'''Compare content if image to source'''
		pass
		'''
		self.log.info(f'\n\n--- Image hashes ---\n{FileHashes(self.image_path)}\n', echo=True)
		source = {str(path.relative_to(self.root_path)).strip("/\\")
			for path in ExtPath.walk(self.root_path)}
		image = set()
		proc = ImageContent(self.image_path, echo=self.echo)
		self.log.info('>', proc.cmd_str)
		with self.content_path.open(mode='w') as content_fh:
			for line in proc.readlines_stdout():
				if line and line[0] == '\\':
					print(line, file=content_fh)
					image.add(line.strip('\\'))
		if len(image) > 0:
			self.log.finished(proc, echo=True)
		else:
			self.log.finished(proc, error=': No or empty image\n')
		diff = source - image
		if diff:
			with self.dropped_path.open(mode='w') as dropped_fh:
				dropped_fh.write('\n'.join(sorted(diff)))
			self.log.warning(
				f'{len(diff)} differences between source and image, see: {self.dropped_path.name}'
			)
		else:
			self.log.info(f'Image contains all items', echo=True)
		self.log.close()
		'''

class OscdimgCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('-p', '--imagepath', type=Path,
			help='Image path', metavar='FILE'
		)
		self.add_argument('-v', '--verify', default=False, action='store_true',
			help='Compare content of image to source, do not create'
		)
		self.add_argument('root', nargs=1, type=Path,
			help='Source', metavar='DIRECTORY'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.root = args.root[0]
		self.filename = args.filename
		self.imagepath = args.imagepath
		self.outdir = args.outdir
		self.verify = args.verify

	def run(self, echo=print, exe=None):
		'''Run the imager'''
		image = Oscdimg(self.root,
			filename = self.filename,
			imagepath = self.imagepath,
			outdir = self.outdir,
			echo = echo,
			exe = exe
		)
		if not self.verify:
			image.create_iso()
		image.verify_iso()

if __name__ == '__main__':	# start here if called as application
	app = OscdimgCli()
	app.parse()
	app.run()
