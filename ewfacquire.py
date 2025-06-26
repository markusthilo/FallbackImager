#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.7.0_2025-06-25'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Augmentation to ewfacquire from libewf. Also runs ewfverify after imaging.
'''

import logging
from argparse import ArgumentParser
from pathlib import Path
#from math import ceil
#from datetime import datetime
#from json import dump
#from lib.timestamp import TimeStamp
#from lib.pathutils import PathUtils

from classes.coreutils import CoreUtils

class EwfAcquire:
	'''Acquire E01/EWF image'''

	def __init__(self, src_paths, dst_dir_path, dst_name,
		codepage = None,
		number_of_sectors = None,
		number_of_bytes = None,
		compression_type = None,
		case_number = None,
		digest_type = None,
		description = None,
		examiner_name = None,
		evidence_number = None,
		file_format = None,
		media_type = None,
		media_flags = None,
		notes = None,
		offset = None,
		process_buffer_size = None,
		bytes_per_sector = None,
		read_error_retries = None,
		resume = False,
		swap_byte_pairs = False,
		toc_path = None,
		wipe_sectors = False,
		dst_dir2_path = None,
		dst_name2 = None,
		echo = print,
		utils = None,
		kill = None
	):
		'''Define job'''
		self._dst = f'{dst_dir_path / dst_name}'
		dst_dir_path.mkdir(parents=True, exist_ok=True)
		self._codepage = codepage
		self._number_of_sectors = number_of_sectors
		self._number_of_bytes = number_of_bytes
		self._compression_type = compression_type
		self._case_number = case_number
		self._digest_type = digest_type
		self._description = description
		self._examiner_name =examiner_name
		self._evidence_number = evidence_number
		self._file_format = file_format
		self._media_type = media_type
		self._media_flags = media_flags
		self._notes = notes
		self._offset = offset
		self._process_buffer_size = process_buffer_size
		self._bytes_per_sector = bytes_per_sector
		self._read_error_retries = read_error_retries
		self._resume = resume
		self._swap_byte_pairs = swap_byte_pairs
		self._toc_path = toc_path
		self._wipe_sectors = wipe_sectors
		if dst_dir2_path:
			self._dst2 = f'{dst_dir2_path / dst_name2}'
			dst_dir2_path.mkdir(parents=True, exist_ok=True)
		else:
			self._dst2 = None
		self._src_paths = src_paths
		self._echo = echo
		self._utils = utils if utils else CoreUtils()
		self._log_path = dst_dir_path / '.log.txt'	### logging ###
		formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
		logger = logging.getLogger()
		logger.setLevel(logging.INFO)
		log_fh = logging.FileHandler(filename=self._log_path, mode='w')
		log_fh.setFormatter(formatter)
		logger.addHandler(log_fh)
		if self._dst2:	# additional log file if 2nd destination is given
			self._log2_path = dst_dir2_path / '.log.txt'
			log2_fh = logging.FileHandler(filename=self._log2_path, mode='w')
			log2_fh.setFormatter(formatter)
			logger.addHandler(log2_fh)
		self._json_path = dst_dir_path / '.infos.json'	### infos as json ###

	def run(self):
		'''Run ewfacquire + ewfverify'''
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

if __name__ == '__main__':	# start here if called as application
	arg_parser = ArgumentParser(description=__description__)
	arg_parser.add_argument('-a', '--codepage', type=str,
		choices=(
			'ascii', 'windows-874', 'windows-932', 'windows-936', 'windows-949',
			'windows-950', 'windows-1250', 'windows-1251', 'windows-1252',
			'windows-1253', 'windows-1254', 'windows-1255', 'windows-1256',
			'windows-1257', 'windows-1258'),
		help='Codepage of header section (default: ascii)', metavar='STRING'
	)
	arg_parser.add_argument('-b', '--chunk_size', type=int,
		choices=(16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768),
		help='Secify the number of sectors to read at once (per chunk. default: 64)',
		metavar='INTEGER'
	)
	args_parser.add_argument('-B', '--bytes_to_acquire',
		help='specify the number of bytes to acquire (default is all bytes)', metavar='BYTES'
	)
	arg_parser.add_argument('-c', '--compression', type=str,
		choices=('none', 'empty-block', 'fast', 'best'),
		help='Compression level (default: none)', metavar='STRING'
	)
	arg_parser.add_argument('-C', '--case_number', type=str, help='Case number', metavar='STRING')
	argg_parser.add_argument('-d', '--digest_type', type=str, choices=('sha1', 'sha256'),
		help='Calculate additional digest (hash) types besides md5', metavar='STRING'
	)
	arg_parser.add_argument('-D', '--description', type=str,
		help='Description (required, e.g. drive number, example: "PC01_HD01")', metavar='STRING'
	)
	arg_parser.add_argument('-e', '--examiner_name', type=str, help='Examiner name', metavar='STRING')
	arg_parser.add_argument('-E', '--evidence_number', type=str, help='Evidence number', metavar='STRING')
	arg_parser.add_argument('-f', '--ewf_format', type=str,
		choices=('ewf', 'smart', 'ftk', 'encase2', 'encase3', 'encase4', 'encase5',
		'encase6', 'encase7', 'encase7-v2', 'linen5', 'linen6', 'linen7', 'ewfx'),
		help='Specify the EWF file format to write to (default: encase6)', metavar='STRING'
	)
	arg_parser.add_argument('-g', '--error_granularity', type=int,
		help='specify the number of sectors to be used as error granularity', metavar='INTEGER'
	)
	arg_parser.add_argument('-m', '--media_type', type=str, choices=('fixed', 'removable', 'optical', 'memory'),
		help='Media type (try to detect if not set)', metavar='STRING'
	)
	arg_parser.add_argument('-M', '--media_flags', type=str, choices=('logical', 'physical'),
		help='Specify the media flags, options: logical, physical (try to detect if not set)',
		metavar='STRING'
	)
	arg_parser.add_argument('-N', '--notes', type=str,
		help='Notes, e.g. used write blocker', metavar='STRING'
	)
	arg_parser.add_argument('-o', '--offset', type=int,
		help='Specify the offset to start to acquire (default is 0)', metavar='BYTES'
	)
	arg_parser.add_argument('-p', '--process_buffer_size', type=int,
		help='Specify the process buffer size (default is the chunk size)', metavar='INTEGER'
	)
	arg_parser.add_argument('-P', '--bytes_per_sector', type=int,
		help='Specify the number of bytes per sector (default is 512, set to override the automatic detection)',
		metavar='BYTES'
		)
	arg_parser.add_argument('-r', '--read_error_retries', type=int,
		help = 'Specify the number of retries when a read error occurs (default is 2)',
		metavar='INTEGER'
	)
	arg_parser.add_argument('-R', '--resume', help='Resume acquiry at a safe point (if something went wrong before)')
	arg_parser.add_argument('-s', '--swap_byte_pairs', help='Swap byte pairs of the media data (from AB to BA)')
	arg_parser.add_argument('-S', '--segment_size', type=str,
			help='Segment file size in MiB, GiB or n where size = source source / n (default is 40)',
			metavar='GiB/MiB/INTEGER'
		)
	arg_parser.add_argument('-t', '--target', type=Path, required=True,
			help='Specify the target file (without extension) to write to', metavar='FILE'
		)
	arg_parser.add_argument('-T', '--toc', type=Path,
		help='Specify the file containing the table of contents (TOC) of an optical disc (CUE format)',
		metavar='FILE'
	)
	arg_parser.add_argument('-w', '--zero_sectors', help='Zero sectors on read error (mimic EnCase like behavior)')
	arg_parser.add_argument('-x', '--unbuffered', help='Use the chunk data instead of the buffered read and write functions.')
	arg_parser.add_argument('-2', '--secondary_target', type=Path,
		help='Specify the secondary target file (without extension) to write to', metavar='FILE'
	)
	arg_parser.add_argument('source', nargs='+', type=Path,
			help='The source file(s), device, partition or anything else that works with ewfacquire',
			metavar='FILE'
		)
	args = arg_parser.parse_args()
	ewfacquire = EwfAcquire(args.src_paths, args.target.parent, args.target.stem,
		codepage = args.codepage,
		chunk_size = args.chunk_size,
		bytes_to_acquire = args.bytes_to_acquire,
		compression = args.compression,
		case_number = args.case_number,
		digest_type= args.digest_type,
		description = args.description,
		examiner_name = args.examiner_name,
		evidence_number = args.evidence_number,
		ewf_format = args.ewf_format,
		error_granularity = args.error_granularity,
		media_type = args.media_type,
		media_flags = args.media_flags,
		notes = args.notes,
		offset = args.offest,
		process_buffer_size = args.process_buffer_size,
		bytes_per_sector = args.bytes_per_sector,
		read_error_retries = args.read_error_retries,
		resume = args.resume,
		swap_byte_pairs = args.swap_byte_pairs,
		segment_size = args.segment_size,
		toc_path = args.toc,
		zero_sectors = args.zero_sectors,
		unbuffered = args.unbuffered,
		dst_dir2_path = args.secondary_target.parent if args.secondary_target else None,
		dst_name2 = args.secondary_target.stem if args.secondary_target else None,
		utils = None,
	)

