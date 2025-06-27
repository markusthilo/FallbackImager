#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.7.0_2025-06-27'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Augmentation to ewfacquire from libewf. Also runs ewfverify after imaging.
'''

from argparse import ArgumentParser
from pathlib import Path
from json import dump
from classes.coreutils import CoreUtils
from classes.logger import Logger
from ewfverify import EwfVerify

class EwfAcquire(EwfVerify):
	'''Acquire E01/EWF image'''

	def __init__(self, src_paths, target_path,
		codepage = None,
		chunk_size = None,
		bytes_to_acquire = None,
		compression = None,
		case_number = None,
		digest_type = None,
		description = None,
		examiner_name = None,
		evidence_number = None,
		ewf_format = None,
		error_granularity = None,
		media_type = None,
		media_flags = None,
		notes = None,
		offset = None,
		process_buffer_size = None,
		bytes_per_sector = None,
		read_error_retries = None,
		resume = False,
		swap_byte_pairs = False,
		segment_size = '40',
		toc = None,
		zero_sectors = False,
		unbuffered = False,
		target2 = None,
		utils = None,
		echo = print,
		kill = None
	):
		'''Define job'''
		self._echo = echo
		self._utils = utils if utils else CoreUtils()	### utils ###
		self.details = self._utils.diskdetails(src_paths[0])	### analyze_source
		if self.details:
			if len(src_paths) > 1:
				raise ValueError('Only one blockdevice allowed as source')
			if not media_flags and self.details['type'] != 'disk':
				media_flags = 'logical'
			self._size = self.details['size']
		else:
			if not media_flags:
				media_flags = 'logical'
			self._size = 0
			self.details['files'] = list()
			for path in src_paths:
				size = self._utils.get_file_size(path)
				if isinstance(size, int):
					self._size += size
				else:
					raise ValueError(f'Unable to get size of {path}')
				self.details['files'].append({'path': f'{path.absolute()}', 'size': size})
			if toc:
				self.details['toc'] = f'{toc.absolute()}'
		if segment_size:	### segment size ###
			max_segment_size = 0x80000000 if ewf_format and not ewf_format in ('encase6', 'encase7') else min(2*self._size, 0x7777777777777700)
			segment_size = segment_size.lower().replace(' ', '')
			if segment_size in ('max', 'maximum', 'maximal', 'm'):
				segment_size = None
			elif segment_size.endswith('mib') or segment_size.endswith('m'):
				try:
					segment_size = 0x100000 * int(segment_size.split('m', 1)[0])
				except:
					segment_size = None
			elif segment_size.endswith('gib') or segment_size.endswith('g'):
				try:
					segment_size = 0x40000000 * int(segment_size.split('g', 1)[0])
				except:
					segment_size = None
			elif segment_size.endswith('tib') or segment_size.endswith('t'):
				try:
					segment_size = 0x40000000000 * int(segment_size.split('t', 1)[0])
				except:
					segment_size = None
			else:
				try:
					segment_size = self._size // int(segment_size)
				except:
					segment_size = None
			if not segment_size or segment_size < 0x100000 or segment_size > max_segment_size:
				segment_size = max_segment_size
		self.target_path = target_path
		self.target_dir_path = target_path.parent	### target ###
		self.target_dir_path.mkdir(parents=True, exist_ok=True)
		self.log = Logger(target_path.with_suffix('.log.txt'), kill=kill)	### logging ###
		if target2:	### secondary target ###
			self.target2_path = target2_path
			self.target2_dir_path = target2.parent
			self.target2_dir_path.mkdir(parents=True, exist_ok=True)
			self.log.add(target2.with_suffix('.log.txt'))	# additional log file if 2nd destination is given
		else:
			self.target2_path = None
		self._cmd = ['ewfacquire']	### assemble command to execute ###
		if codepage:
			self._cmd.extend(['-A', codepage])
		if chunk_size:
			self._cmd.extend(['-b', chunk_size])
		if bytes_to_acquire:
			self._cmd.extend(['-B', bytes_to_acquire])
		if compression:
			self._cmd.extend(['-c', compression])
		if case_number:
			self._cmd.extend(['-C', case_number])
		if digest_type:
			self._cmd.extend(['-d', digest_type])
		if description:
			self._cmd.extend(['-D', description])
		if examiner_name:
			self._cmd.extend(['-e', examiner_name])
		if evidence_number:
			self._cmd.extend(['-E', evidence_number])
		if ewf_format:
			self._cmd.extend(['-f', ewf_format])
		if error_granularity:
			self._cmd.extend(['-g', error_granularity])
		if media_type:
			self._cmd.extend(['-m', media_type])
		if media_flags:
			self._cmd.extend(['-M', media_flags])
		if notes:
			self._cmd.extend(['-N', notes])
		if offset:
			self._cmd.extend(['-o', offset])
		if process_buffer_size:
			self._cmd.extend(['-p', process_buffer_size])
		if bytes_per_sector:
			self._cmd.extend(['-P', bytes_per_sector])
		if read_error_retries:
			self._cmd.extend(['-r', read_error_retries])
		if resume:
			self._cmd.append('-R')
		if swap_byte_pairs:
			self._cmd.append('-s')
		if segment_size:
			self._cmd.extend(['-S', segment_size])
		self._cmd.extend(['-t', f'{target_path}'])
		if toc:
			self._cmd.extend(['-T', f'{toc}'])
		self._cmd.append('-u')
		if zero_sectors:
			self._cmd.append('-w')
		if unbuffered:
			self._cmd.append('-x')
		if target2:
			self._cmd.extend(['-2', target2])
		self._cmd.extend([f'{path}' for path in src_paths])

	def run(self):
		'''Run ewfacquire'''
		self._proc, cmd_str = utils.popen(self._cmd)
		head = [f'Executing: {cmd_str}']
		self._echo(head[0])
		tail = None
		for line in self._proc.stdout:
			if self.log.check_kill_signal():
				return
			stripped = line.strip()
			if not stripped:
				continue
			if self._echo_info(stripped):
				if head != False:
					if stripped.startswith('Acquiry started at: '):
						head.append(stripped)
						self.log.write('\n'.join(head))
						head = False
					else:
						head.append(stripped)
				elif tail:
					tail.append(stripped)
				elif stripped.startswith('Acquiry completed at: '):
					tail = [stripped]
		if tail:
			self.log.write('\n'.join(tail))
			for line in tail:
				if line.startswith('MD5 '):
					self.details['acquire_md5'] = line.split(':')[1].strip()
				elif line.startswith('SHA1 '):
					self.details['acquire_sha1'] = line.split(':')[1].strip()
				elif line.startswith('SHA256 '):
					self.details['acquire_sha256'] = line.split(':')[1].strip()
		return self.details

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
	arg_parser.add_argument('-B', '--bytes_to_acquire',
		help='specify the number of bytes to acquire (default is all bytes)', metavar='BYTES'
	)
	arg_parser.add_argument('-c', '--compression', type=str,
		choices=('none', 'empty-block', 'fast', 'best'),
		help='Compression level (default: none)', metavar='STRING'
	)
	arg_parser.add_argument('-C', '--case_number', type=str, help='Case number', metavar='STRING')
	arg_parser.add_argument('-d', '--digest_type', type=str, choices=('sha1', 'sha256'),
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
		help='Media type (default is fixed)', metavar='STRING'
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
	arg_parser.add_argument('-s', '--swap_byte_pairs', action='store_true', help='Swap byte pairs of the media data (from AB to BA)')
	arg_parser.add_argument('-S', '--segment_size', type=str,
			help='Segment file size in MiB, GiB, TiB, max or integer n where segment_size = source_size / n (default is 1.4 GiB)',
			metavar='STRING/GiB/MiB/INTEGER'
		)
	arg_parser.add_argument('-t', '--target', type=Path, required=True,
			help='Specify the target file (without extension) to write to', metavar='FILE'
		)
	arg_parser.add_argument('-T', '--toc', type=Path,
		help='Specify the file containing the table of contents (TOC) of an optical disc (CUE format)',
		metavar='FILE'
	)
	arg_parser.add_argument('-v', '--verify', action='store_true', help='Verify image after ewfacquire has finished')
	arg_parser.add_argument('-w', '--zero_sectors', action='store_true', help='Zero sectors on read error (mimic EnCase like behavior)')
	arg_parser.add_argument('-x', '--unbuffered', action='store_true', help='Use the chunk data instead of the buffered read and write functions.')
	arg_parser.add_argument('-2', '--secondary_target', type=Path,
		help='Specify the secondary target file (without extension) to write to', metavar='FILE'
	)
	arg_parser.add_argument('source', nargs='+', type=Path,
			help='The source file(s), device, partition or anything else that works with ewfacquire',
			metavar='FILE'
		)
	args = arg_parser.parse_args()
	utils = CoreUtils()
	if not utils.are_readable(args.source) and not utils.i_have_root():
		utils.read_password()
	ewfacquire = EwfAcquire(args.source, args.target,
		codepage = args.codepage,
		chunk_size = args.chunk_size,
		bytes_to_acquire = args.bytes_to_acquire,
		compression = args.compression,
		case_number = args.case_number,
		digest_type = args.digest_type,
		description = args.description,
		examiner_name = args.examiner_name,
		evidence_number = args.evidence_number,
		ewf_format = args.ewf_format,
		error_granularity = args.error_granularity,
		media_type = args.media_type,
		media_flags = args.media_flags,
		notes = args.notes,
		offset = args.offset,
		process_buffer_size = args.process_buffer_size,
		bytes_per_sector = args.bytes_per_sector,
		read_error_retries = args.read_error_retries,
		resume = args.resume,
		swap_byte_pairs = args.swap_byte_pairs,
		segment_size = args.segment_size,
		toc = args.toc,
		zero_sectors = args.zero_sectors,
		unbuffered = args.unbuffered,
		target2 = args.secondary_target,
		utils = utils,
	)
	ewfacquire.run()
	if args.verify:
		ewfverify = EwfVerify([args.target.with_suffix('.E01')], ewfacquire.log,
			codepage = args.codepage,
			digest_type = args.digest_type,
			#input_format = args.ewf_format,
			process_buffer_size = args.process_buffer_size,
			zero_sectors = args.zero_sectors,
			unbuffered = args.unbuffered
		)
		ewfverify.run()
	ewfacquire.finish()