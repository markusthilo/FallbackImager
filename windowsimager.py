#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-11'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Create and check WMI Image'

from pathlib import Path
from argparse import ArgumentParser
from lib.extpath import ExtPath
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.powershell import PowerShell

class NewImage(PowerShell):
	'''New-WindowsImage -ImagePath $imagepath -CapturePath $capturepath -Name $name'''

	def __init__(self, imagepath, capturepath, name=None, description=None):
		if not name:
			name = capturepath
		super().__init__(['New-WindowsImage',
			'-ImagePath', f'"{imagepath}"',
			'-CapturePath', f'"{capturepath}"',
			'-Name', f'"{name}"',
			'-Description', f'"{TimeStamp.now_or(description)}"'
		])

class ImageContent(PowerShell):
	'''Get-WindowsImageContent -ImagePath $imagepath -Index $indes'''

	def __init__(self, imagepath, index=1):
		super().__init__(['Get-WindowsImageContent',
			'-ImagePath', f'"{imagepath}"',
			'-Index', f'{index}'
		])

class WindowsImage:
	'''Create and Verify images in WMI format'''

	def __init__(self, sourcepath,
			filename = None,
			imagepath = None,
			outdir = None,
			description = None
		):
		'''Definitihons'''
		self.source_path = Path(sourcepath)
		if imagepath:
			self.image_path = Path(imagepath)
			self.filename = self.image_path.stem
			self.outdir = self.image_path.parent
		else:
			self.filename = TimeStamp.now_or(filename)
			self.outdir = ExtPath.mkdir(outdir)
			self.image_path = ExtPath.child(f'{self.filename}.wim', parent=self.outdir)
		self.description = description
		self.log = Logger(self.filename, outdir=self.outdir)

	def create(self):
		'''Create image'''
		proc = NewImage(self.image_path, self.source_path, description=self.description)
		self.log.info(proc.cmd_str)
		proc.read_all()
		self.log.finished(proc)

	def compare(self):
		'''Compare content if image to source'''
		source = {win_str for win_str in ExtPath.walk_win_str(self.source_path)}
		proc = ImageContent(self.image_path)
		self.log.info(proc.cmd_str)
		image = set()
		content_path = ExtPath.child(f'{self.filename}_content.txt', parent=self.outdir)
		with content_path.open(mode='w') as fh:
			for line in proc.readlines_stdout():
				print(line, file=fh)
				image.add(line.strip('\\'))
		self.log.finished(proc)
		diff = source - image
		if len(diff) > 0:
			dropped_path = ExtPath.child(f'{self.filename}_dropped.txt', parent=self.outdir)
			with dropped_path.open(mode='w') as fh:
				fh.write('\n'.join(sorted(diff)))
			self.log.warning(f'{len(diff)} differences in source and image, look at {dropped_path}')
		self.log.close()

class WindowsImageCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(**kwargs)
		self.add_argument('-c', '--compare', default=False, action='store_true',
			help='Compare content of image to source, do not create'
		)
		self.add_argument('-d', '--description', type=str,
			help='Additional description to the image file', metavar='STRING'
		)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('-p', '--imagepath', type=Path,
			help='Image path', metavar='FILE'
		)
		self.add_argument('sourcepath', nargs=1, type=Path,
			help='Source', metavar='DIRECTORY'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.sourcepath = args.sourcepath[0]
		self.compare = args.compare
		self.description = args.description
		self.filename = args.filename
		self.imagepath = args.imagepath
		self.outdir = args.outdir

	def run(self, echo=print):
		'''Run the imager'''
		image = WindowsImage(self.sourcepath,
			filename = self.filename,
			imagepath = self.imagepath,
			outdir = self.outdir,
			description = self.description
		)
		if not self.compare:
			image.create()
		image.compare()

if __name__ == '__main__':	# start here if called as application
	app = WindowsImageCli(description=__description__)
	app.parse()
	app.run()
