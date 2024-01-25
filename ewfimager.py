#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'EwfImager'
__author__ = 'Markus Thilo'
__version__ = '0.3.1_2024-01-25'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This tool runs ewfacquire and ewfverify.
'''

from sys import executable as __executable__
from pathlib import Path
from argparse import ArgumentParser
from lib.timestamp import TimeStamp
from lib.extpath import ExtPath
from lib.logger import Logger
from lib.openproc import OpenProc
from lib.linutils import LinUtils
from ewfverify import EwfVerify

__executable__ = Path(__executable__)
__file__ = Path(__file__)
if __executable__.stem.lower() == __file__.stem.lower():
	__parent_path__ = __executable__.parent
else:
	__parent_path__ = __file__.parent

class EwfImager:
	'''Acquire and verify E01/EWF image'''

	def __init__(self):
		'''Check if ewfverify and ewfverify are present'''
		for self.ewfacquire_path in (
			Path('/usr/bin/ewfacquire'),
			Path('/usr/local/bin/ewfacquire'),
			__parent_path__/'bin/ewfacquire',
			__parent_path__/'ewfacquire'
		):
			if self.ewfacquire_path.is_file():
				break
		if not self.ewfacquire_path.is_file():
			raise RuntimeError('Unable to use ewfacquire from ewf-tools')
		self.ewfverify = EwfVerify()

	def acquire(self, source, case_number, evidence_number, examiner_name, description, *args,
			outdir = None,
			compression_values = None,
			media_type = None,
			notes = None,
			size = None,
			echo = print,
			log = None,
			**kwargs
		):
		'''Run ewfacquire'''
		self.source = Path(source)
		self.filename = Path(ExtPath.mkfname(f'{case_number}_{evidence_number}_{description}'))
		self.outdir = ExtPath.mkdir(outdir)
		self.echo = echo
		if log:
			self.log = log
		else:
			self.log = Logger(
				filename = f'{self.filename}_log.txt',
				outdir = self.outdir, 
				head = 'ewfimager.EwfImager',
				echo = self.echo
			)
		cmd = [f'{self.ewfacquire_path}', '-u', '-t', f'{self.outdir/self.filename}', '-d', 'sha256']
		cmd.extend(['-C', case_number])
		cmd.extend(['-D', description])
		cmd.extend(['-e', examiner_name])
		cmd.extend(['-E', evidence_number])
		if compression_values:
			cmd.extend(['-c', compression_values])
		else:
			cmd.extend(['-c', 'fast'])
		if media_type:
			cmd.extend(['-m', media_type])
		if notes:
			cmd.extend(['-N', notes])
		else:
			cmd.extend(['-N', '-'])
		if not size:
			source_size = ExtPath.get_size(self.source)
			if not source_size:
				if self.source.is_block_device():
					source_size = LinUtils.blkdevsize(self.source)
				else:
					raise RuntimeError(f'Unable to get size of {source}')
			size = max(int(source_size/85899345920) * 1073741824, 4294967296)
		cmd.extend(['-S', f'{size}'])
		for arg in args:
			cmd.append(f'-{arg}')
		for arg, par in kwargs.items():
			cmd.extend([f'-{arg}', f'{par}'])
		cmd.append(f'{self.source}')
		proc = OpenProc(cmd, log=self.log)
		proc.echo_output(self.log)
		if stderr := proc.stderr.read():
			self.log.error(f'ewfacquire terminated with: {stderr}', exception=stderr.split('\n'))

class EwfImagerCli(ArgumentParser):
	'''CLI, also used for GUI of FallbackImager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-c', '--compression_values', type=str,
			help='Compression level options: none, empty-block, fast (default) or best',
			metavar='STRING'
		)
		self.add_argument('-C', '--case_number', type=str, required=True,
			help='Case number (required)',
			metavar='STRING'
		)
		self.add_argument('-D', '--description', type=str, required=True,
			help='Description (required, e.g. drive number, example: "PC01_HD01")',
			metavar='STRING'
		)
		self.add_argument('-e', '--examiner_name', type=str, required=True,
			help='Examiner name (required)',
			metavar='STRING'
		)
		self.add_argument('-E', '--evidence_number', type=str, required=True,
			help='Evidence number (required)',
			metavar='STRING'
		)
		self.add_argument('-m', '--media_type', type=str,
			choices=['fixed', 'removable', 'optical', 'memory'],
			help='Media type, options: fixed (default), removable, optical, memory',
			metavar='STRING'
		)
		self.add_argument('-N', '--notes', type=str,
			help='Notes, e.g. used write blocker (default is "-")',
			metavar='STRING'
		)
		self.add_argument('-O', '--outdir', type=ExtPath.path,
			help='Directory to write generated files (default: current)',
			metavar='DIRECTORY'
		)
		self.add_argument('-S', '--size', type=int,
			help='Segment file size in bytes (default: calculated)',
			metavar='INTEGER'
		)
		self.add_argument('source', nargs=1, type=Path,
			help='The source device, partition or anything else that works with ewfacquire',
			metavar='BLOCKDEVICE/PARTITON/FILE'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.source = args.source[0]
		self.compression_values = args.compression_values
		self.case_number = args.case_number
		self.description = args.description
		self.examiner_name = args.examiner_name
		self.evidence_number = args.evidence_number
		self.media_type = args.media_type
		self.notes = args.notes
		self.outdir = args.outdir
		self.size = args.size

	def run(self, echo=print):
		'''Run EwfImager and EwfVerify'''
		image = EwfImager()
		image.acquire(self.source,
			self.case_number, self.evidence_number,
			self.examiner_name, self.description,
			compression_values = self.compression_values,
			media_type = self.media_type,
			notes = self.notes,
			size = self.size,
			outdir = self.outdir,
			echo = echo
		)
		EwfVerify().check(image.filename, echo=echo, log=image.log)
		image.log.close()

if __name__ == '__main__':	# start here if called as application
	app = EwfImagerCli()
	app.parse()
	app.run()
