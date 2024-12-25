#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'EwfImager'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2024-12-17'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Use libewf to create and check an EWF/E01 image of a block device.
'''

from os import name as __os_name__
from os import getlogin
from pathlib import Path
from math import ceil
from argparse import ArgumentParser
from datetime import datetime
from json import dump
from lib.timestamp import TimeStamp
from lib.pathutils import PathUtils
from lib.logger import Logger
from lib.linutils import LinUtils, OpenProc
from lib.stringutils import StringUtils
from ewfchecker import EwfChecker

class EwfImager:
	'''Acquire and verify E01/EWF image'''

	def __init__(self, echo=print, utils=None):
		'''Check if ewfacquire and ewfverify are present'''
		self.available = False
		if __os_name__ == 'posix' and EwfChecker().available:
			self.ewfacquire_path = LinUtils.find_bin('ewfacquire', Path(__file__).parent)
			if self.ewfacquire_path:
				self.echo = echo
				self.utils = utils
				self.available = True

	def acquire(self, source, case_number, evidence_number, description, *args,
			outdir = None,
			compression_values = None,
			examiner_name = None,
			filename = None,
			media_type = None,
			media_flags = None,
			notes = None,
			setro = False,
			size = None,
			log = None,
			sudo = None
		):
		'''Run ewfacquire'''
		self.source = Path(source)
		self.filename = filename if filename else PathUtils.mkfname(f'{case_number}_{evidence_number}_{description}')
		self.outdir = PathUtils.mkdir(outdir)
		if not self.utils:
			self.utils = LinUtils()
		self.log = log if log else Logger(filename=self.filename, outdir=self.outdir,
			head='ewfimager.EwfImager', echo=self.echo)
		now = datetime.now()
		self.infos = {'year': f'{now.year:04d}', 'month': f'{now.month:02d}', 'day': f'{now.day:02d}'}
		if setro:
			stdout, stderr = LinUtils.set_ro(self.source)
			if stderr:
				self.log.warning(stderr)
		self.source_size = LinUtils.blkdevsize(self.source) if self.source.is_block_device() else PathUtils.get_size(self.source)
		if not self.source_size:
			self.log.error(f'Unable to get size of {self.source}')
		self.infos['source_size'] = StringUtils.bytes(self.source_size, format_k='{iec} ({b} bytes)')
		self.source_details = LinUtils.diskdetails(self.source)
		self.infos.update(self.source_details)
		msg = '\n'.join(f'{key.upper()}:\t{value}' for key, value in self.source_details.items())
		self.log.info(f'Source:\n{msg}', echo=True)
		proc = OpenProc([f'{self.ewfacquire_path}', '-V'])
		if proc.wait() != 0:
			self.log.warning(proc.stderr.read())
		self.log.info(f'Using {proc.stdout.read().splitlines()[0]}')
		self.image_path = self.outdir/self.filename
		self.infos['case_number'] = case_number
		self.infos['examiner_name'] = examiner_name if examiner_name else getlogin().upper()
		self.infos['evidence_number'] = evidence_number
		self.infos['compression_values'] = compression_values if compression_values else 'fast'
		self.infos['description'] = description
		if media_type:
			self.media_type = media_type
			self.infos['media_type'] = f'{media_type} (set by user)'
		else:
			if self.infos['vendor'] == 'ATA':
				self.media_type = 'fixed'
				self.infos['media_type'] = 'fixed (detected/estimated)'
			else:
				self.media_type = 'removable'
				self.infos['media_type'] = 'removable (detected/estimated)'
		if media_flags:
			self.infos['media_flags'] = media_flags
		else:
			self.infos['media_flags'] = 'physical (detected/estimated)' if LinUtils.is_disk(self.source) else 'logical (detected/estimated)'
		self.infos['notes'] = notes if notes else '-'
		if not size:
			size = 40
		try:
			size = self.segment_size = ceil(self.source_size/int(size)/1073741824) * 1073741824
		except ValueError:
			size = size.replace(' ', '').rstrip('bB')
			if size[-1].lower() == 'm':
				self.segment_size = int(size[:-1]) * 1048576
			elif size[-1].lower() == 'g':
				self.segment_size = int(size[:-1]) * 1073741824
			else:
				self.log.error(exception='Undecodable segment size')
			if self.segment_size <= 0:
				self.log.error(exception='Invalid segment size')
		self.infos['segment_size'] = StringUtils.bytes(self.segment_size)
		cmd = [f'{self.ewfacquire_path}', '-u', '-t', f'{self.image_path}', '-d', 'sha256']
		cmd.extend(['-C', self.infos['case_number']])
		cmd.extend(['-D', self.infos['description']])
		cmd.extend(['-e', self.infos['examiner_name']])
		cmd.extend(['-E', self.infos['evidence_number']])
		cmd.extend(['-c', self.infos['compression_values']])
		cmd.extend(['-m', f'{self.media_type}'])
		cmd.extend(['-M', self.infos['media_flags']])
		cmd.extend(['-N', self.infos['notes']])
		cmd.extend(['-S', f'{self.segment_size}'])
		for arg in args:
			cmd.append(arg)
		cmd.append(f'{self.source}')
		proc = OpenProc(cmd, sudo=self.utils.sudo, log=self.log)
		if proc.echo_output(cnt=9) != 0:
			self.log.error(f'ewfacquire terminated with:\n{proc.stderr.read()}')
		self.infos.update(proc.grep_stack(
				('MD5 hash calculated over data:', 'md5'),
				('SHA256 hash calculated over data:', 'sha256'),
				('ewfacquire:', 'ewfacquire')
			)
		)
		for line in proc.stack:
			if line.startswith('acquired '):
				acquired = line.rstrip('.').split(' ')
				self.infos['size_stored'] = ' '.join(acquired[1:5])
				self.infos['size_acquired'] = ' '.join(acquired[7:11])
		try:
			with self.image_path.with_suffix('.json').open('w') as fh:
				dump(self.infos, fh)
		except Exception as err:
			self.log.warning(f'Unable to create JSON file:\n{err}')
		if not LinUtils.i_am_root():
			user, group = self.log.path.owner(), self.log.path.group()
			for path in self.outdir.glob(f'{self.filename}.*'):
				self.utils.chown(user, group, path)
		return self.infos

class EwfImagerCli(ArgumentParser):
	'''CLI, also used for GUI of FallbackImager'''

	def __init__(self, echo=print, utils=None, **kwargs):
		'''Define CLI using argparser'''
		self.echo = echo
		self.utils = utils
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
		self.add_argument('-f', '--filename', type=str,
			help='Image filename (without extension) to write to (default is assembled by case number etc.)',
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
		self.add_argument('-O', '--outdir', type=Path,
			help='Directory to write generated files (default: current)',
			metavar='DIRECTORY'
		)
		self.add_argument('-S', '--size', type=str,
			help='Segment file size in MiB or GiB or MiB number of segments (e.g. "4g", "100m", "20", default: "40")',
			default='40', metavar='GiB/MiB/INTEGER/STRING'
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
		self.filename = args.filename
		self.media_type = args.media_type
		self.notes = args.notes
		self.outdir = args.outdir
		self.size = args.size
		self.setro = args.setro

	def run(self):
		'''Run EwfImager and EwfVerify'''
		imager = EwfImager(echo=self.echo, utils=self.utils)
		hashes = imager.acquire(self.source, self.case_number, self.evidence_number, self.description,
			compression_values = self.compression_values,
			examiner_name = self.examiner_name,
			filename = self.filename,
			media_type = self.media_type,
			notes = self.notes,
			setro = self.setro,
			size = self.size,
			outdir = self.outdir,
		)
		EwfChecker(echo=self.echo).check(imager.image_path,
			outdir = self.outdir,
			log = imager.log,
			hashes = hashes
		)
		imager.log.close()

if __name__ == '__main__':	# start here if called as application
	app = EwfImagerCli()
	app.parse()
	app.run()
