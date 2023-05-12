#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-12'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Create and check WMI Image'

from pathlib import Path
from argparse import ArgumentParser
from lib.extpath import ExtPath
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.dism import CaptureImage, ImageContent
from lib.hashes import FileHashes

class DismImage:
	'''Create and Verify image with Dism'''

	def __init__(self, root,
			filename = None,
			imagepath = None,
			outdir = None,
			name = None,
			description = None,
			compress = 'none',
			echo = print
		):
		'''Definitihons'''
		self.root_path = Path(root)
		if imagepath:
			self.image_path = Path(imagepath)
			self.filename = self.image_path.stem
			self.outdir = self.image_path.parent
		else:
			self.filename = TimeStamp.now_or(filename)
			self.outdir = ExtPath.mkdir(outdir)
			self.image_path = ExtPath.child(f'{self.filename}.wim', parent=self.outdir)
		self.description = description
		if compress in ['max', 'fast', 'none']:
			self.compress = compress
		else:
			raise NotImplementedError(self.compress)
		self.content_path = ExtPath.child(f'{self.filename}_content.txt', parent=self.outdir)
		self.dropped_path = ExtPath.child(f'{self.filename}_dropped.txt', parent=self.outdir)
		self.echo = echo
		self.log = Logger(self.filename, outdir=self.outdir, head='dismimager.DismImage')

	def create(self):
		'''Create image'''
		proc = CaptureImage(self.image_path, self.root_path,
			description = self.description,		
			compress = self.compress,
			echo = self.echo
		)
		self.log.info('>', proc.cmd_str)
		for line in proc.readlines_stdout():
			self.echo(line)
		if self.image_path.is_file():
			self.log.finished(proc, echo=True)
		else:
			self.log.finished(proc, error=': Could not create image\n')

	def verify(self):
		'''Compare content if image to source'''
		self.log.info('Image hashes', FileHashes(self.image_path), echo=True)
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
			self.log.warning(f'{len(diff)} differences in source and image: {self.dropped_path}')
		else:
			self.log.info(f'Image content = {self.root_path}', echo=True)
		self.log.close()

class DismImageCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(**kwargs)
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
		self.description = args.description
		self.filename = args.filename
		self.imagepath = args.imagepath
		self.outdir = args.outdir
		self.name = args.name
		self.compress = args.compress
		self.verify = args.verify

	def run(self, echo=print):
		'''Run the imager'''
		image = DismImage(self.root,
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

if __name__ == '__main__':	# start here if called as application
	app = DismImageCli(description=__description__)
	app.parse()
	app.run()
