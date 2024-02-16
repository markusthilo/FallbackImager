#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'EwfImager'
__author__ = 'Markus Thilo'
__version__ = '0.4.0_2024-02-16'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Use libewf to create and check an EWF/E01 image of a block device.
'''

from sys import executable as __executable__
from os import getlogin
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime
from json import dump
from lib.timestamp import TimeStamp
from lib.extpath import ExtPath
from lib.logger import Logger
from lib.linutils import LinUtils, OpenProc
from ewfchecker import EwfChecker

if Path(__file__).suffix.lower() == '.pyc':
	__parent_path__ = Path(__executable__).parent
else:
	__parent_path__ = Path(__file__).parent

class EwfImager:
	'''Acquire and verify E01/EWF image'''

	def __init__(self):
		'''Check if ewfacquire and ewfverify are present'''
		self.ewfacquire_path = LinUtils.find_bin('ewfacquire', __parent_path__)
		if not self.ewfacquire_path:
			raise RuntimeError('Unable to find ewfacquire from libewf')
		self.ewfchecker = EwfChecker()

	def acquire(self, source, case_number, evidence_number, description, *args,
			outdir = None,
			compression_values = None,
			examiner_name = None,
			media_type = None,
			media_flags = None,
			notes = None,
			size = None,
			setro = False,
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
			self.log = Logger(filename=self.filename, outdir=self.outdir,
				head='ewfimager.EwfImager', echo=self.echo)
		now = datetime.now()
		self.infos = {'year': f'{now.year:04d}', 'month': f'{now.month:02d}', 'day': f'{now.day:02d}'}
		if setro:
			stdout, stderr = LinUtils.set_ro(source)
			if stderr:
				self.log.warning(stderr)
		self.infos['size_in_bytes'] = ExtPath.get_size(self.source)
		if not self.infos['size_in_bytes']:
			if self.source.is_block_device():
				self.infos['size_in_bytes'] = LinUtils.blkdevsize(self.source)
			else:
				raise RuntimeError(f'Unable to get size of {source}')
		self.source_details = LinUtils.diskdetails(source)
		self.infos.update(self.source_details)
		msg = '\n'.join(f'{key.upper()}:\t{value}' for key, value in self.source_details.items())
		self.log.info(f'Source:\n{msg}', echo=True)
		proc = OpenProc([f'{self.ewfacquire_path}', '-V'])
		if proc.wait() != 0:
			self.log.warning(proc.stderr.read())
		self.log.info(f'Using {proc.stdout.read().splitlines()[0]}')
		self.image_path = self.outdir/self.filename
		self.infos['case_number'] = case_number
		if examiner_name:
			self.infos['examiner_name'] = examiner_name
		else:
			self.infos['examiner_name'] = getlogin().upper()
		self.infos['evidence_number'] = evidence_number
		if compression_values:
			self.infos['compression_values'] = compression_values
		else:
			self.infos['compression_values'] = 'fast'
		self.infos['description'] = description
		if media_type:
			self.infos['media_type'] = media_type
		else:
			if self.infos['vendor'] == 'ATA':
				self.infos['media_type'] = 'fixed'
			else:
				self.infos['media_type'] = 'removable'
		if media_flags:
			self.infos['media_flags'] = media_flags
		else:
			if LinUtils.isdisk(source):
				self.infos['media_flags'] = 'physical'
			else:
				self.infos['media_flags'] = 'logical'
		if notes:
			self.infos['notes'] = notes
		else:
			self.infos['notes'] = '-'
		if size:
			self.infos['size'] = size
		else:
			self.infos['segment_size'] = max(int(self.infos['size_in_bytes']/85899345920) * 1073741824, 4294967296)
		cmd = [f'{self.ewfacquire_path}', '-u', '-t', f'{self.image_path}', '-d', 'sha256']
		cmd.extend(['-C', self.infos['case_number']])
		cmd.extend(['-D', self.infos['description']])
		cmd.extend(['-e', self.infos['examiner_name']])
		cmd.extend(['-E', self.infos['evidence_number']])
		cmd.extend(['-c', self.infos['compression_values']])
		cmd.extend(['-m', self.infos['media_type']])
		cmd.extend(['-M', self.infos['media_flags']])
		cmd.extend(['-N', self.infos['notes']])
		cmd.extend(['-S', f'{self.infos["segment_size"]}'])
		for arg in args:
			cmd.append(f'-{arg}')
		for arg, par in kwargs.items():
			cmd.extend([f'-{arg}', f'{par}'])
		cmd.append(f'{self.source}')
		proc = OpenProc(cmd, log=self.log)
		if proc.echo_output(cnt=9) != 0:
			self.log.error(f'ewfacquire terminated with:\n{proc.stderr.read()}')
		for line in proc.stack:
			if line.startswith('MD5 hash calculated over data:'):
				self.infos['md5'] = line.split(':', 1)[1].strip()
			elif line.startswith('SHA256 hash calculated over data:'):
				self.infos['sha256'] = line.split(':', 1)[1].strip()
		try:
			with self.image_path.with_suffix('.json').open('w') as fh:
				dump(self.infos, fh)
		except Exception as err:
			self.log.warning(f'Unable to create JSON file:\n{err}')
		return self.infos

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
		self.add_argument('-e', '--examiner_name', type=str,
			help='Examiner name (required)',
			metavar='STRING'
		)
		self.add_argument('-E', '--evidence_number', type=str, required=True,
			help='Evidence number (required)',
			metavar='STRING'
		)
		self.add_argument('-m', '--media_type', type=str,
			choices=['fixed', 'removable', 'optical', 'memory'],
			help='Media type, options: fixed, removable, optical, memory (auto if not set)',
			metavar='STRING'
		)
		self.add_argument('-M', '--media_flags', type=str,
			choices=['logical', 'physical'],
			help='Specify the media flags, options: logical, physical (auto if not set)',
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
		self.add_argument('--setro', action='store_true',
			help='Set target block device to read only'
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
		self.setro = args.setro

	def run(self, echo=print):
		'''Run EwfImager and EwfVerify'''
		imager = EwfImager()
		hashes = imager.acquire(self.source, self.case_number, self.evidence_number, self.description,
			compression_values = self.compression_values,
			examiner_name = self.examiner_name,
			media_type = self.media_type,
			notes = self.notes,
			size = self.size,
			setro = self.setro,
			outdir = self.outdir,
			echo = echo
		)
		EwfChecker().check(imager.image_path,
			outdir = self.outdir,
			echo = echo,
			log = imager.log,
			hashes = hashes
		)
		imager.log.close()

if __name__ == '__main__':	# start here if called as application
	app = EwfImagerCli()
	app.parse()
	app.run()
