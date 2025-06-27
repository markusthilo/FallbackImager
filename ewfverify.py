#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.7.0_2025-06-27'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Verify EWF/E01 image using ewfinfo, ewfverify and ewfmount.
'''

from pathlib import Path
from re import sub
from argparse import ArgumentParser
from classes.coreutils import PipedPopen
from classes.logger import Logger

class EwfVerify:
	'''Verify E01/EWF image file'''

	def __init__(self, ewf_paths, log,
		codepage = None,
		digest_type = None,
		input_format = None,
		process_buffer_size = None,
		zero_sectors = False,
		unbuffered = False,
		details = None,
		echo = print,
		kill = None
	):
		'''Define job'''
		self._kill = kill
		self._echo = echo
		self.details = details if details else {'ewf': [f'{path.absolute()}' for path in ewf_paths]}
		self.log = Logger(log, kill=kill) if isinstance(log, Path) else log	### logging ###
		self._cmd = ['ewfverify']	### assemble command to execute ###
		if codepage:
			self._cmd.extend(['-A', codepage])
		if digest_type:
			self._cmd.extend(['-d', digest_type])
		if input_format:
			self._cmd.extend(['-f', input_format])
		if process_buffer_size:
			self._cmd.extend(['-p', process_buffer_size])
		if zero_sectors:
			self._cmd.append('-w')
		if unbuffered:
			self._cmd.append('-x')
		self._cmd.extend([f'{path}' for path in ewf_paths])

	def _echo_info(self, stripped):
		'''Print information or progress, return False on progress indication'''
		if stripped.startswith('Status: '):
			status = stripped.rstrip('.').split(' ')
			status.extend(next(self._proc.stdout).split(' '))
			msg = f'{status[2]}, {status[12]} {status[13]} of {status[18]} {status[19]}'
			next_stripped = next(self._proc.stdout).strip()
			if next_stripped.startswith('completion '):
				msg += f', {next_stripped.rstrip('.')}'
			self._echo(msg, end='\r')
			return False
		self._echo(stripped)
		return True

	def run(self):
		'''Run ewfverify'''
		self._proc = PipedPopen(self._cmd)
		head = [f'Executing: {self._proc}']
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
					if stripped.startswith('Verify started at: '):
						head.append(stripped)
						self.log.write('\n'.join(head))
						head = False
					else:
						head.append(stripped)
				elif tail:
					tail.append(stripped)
				elif stripped.startswith('Verify completed at: '):
					tail = [stripped]
		if tail:
			self.log.write('\n'.join(tail))
			for line in tail:
				splitted = line.split(':', 1)
				key = splitted[0].strip()
				value = splitted[1].strip()
				if key.startswith('MD5 '):
					if key.endswith('file'):
						self.details['verify_stored_md5'] = value
					elif key.endswith('data'):
						self.details['verify_calculated_md5'] = value
				elif key.startswith('SHA1 '):
					if key.endswith('file'):
						self.details['verify_stored_sha1'] = value
					elif key.endswith('data'):
						self.details['verify_calculated_sha1'] = value
				elif key.startswith('SHA256 '):
					if key.endswith('file'):
						self.details['verify_stored_sha256'] = value
					elif key.endswith('data'):
						self.details['verify_calculated_sha256'] = value
				elif key == 'ewfverify':
					self.details['ewfverify'] = value
		return self.details


	def check(self, image, outdir=None, filename=None, echo=print, log=None, hashes=None, sudo=None):
		'''Verify image'''

		mount_path = Path(f'/tmp/{self.image_path.stem}_{self.hashes["md5"]}')
		try:
			mount_path.mkdir(exist_ok=True)
		except Exception as ex:
			self.log.warning(f'Unable to create directory {mount_path}\n{ex}')
			return
		proc = OpenProc([f'{self.ewfmount_path}', f'{self.image_path}', f'{mount_path}'], log=self.log)
		if proc.echo_output() != 0:
			self.log.error(f'ewfmount terminated with:\n{proc.stderr.read()}')
		else:
			ewf_path = mount_path.joinpath(next(mount_path.iterdir()))
			xxd = PathUtils.read_bin(ewf_path)
			self.log.info(f'Image starts with:\n\n{xxd}', echo=True)
			self.log.info('Trying to read partition table')
			ret = run(['fdisk', '-l', f'{ewf_path}'], capture_output=True, text=True)
			if ret.stderr:
				self.log.warning(ret.stderr)
			else:
				msg = ''
				for line in ret.stdout.split('\n'):
					if not line:
						continue
					line = sub(' {2,}', ' ', line)
					if line.startswith(f'Disk {ewf_path}:'):
						msg += f'This might be a disk image\nDisk size:{line.split(":", 1)[1]}\n'
					elif line.startswith(f'{ewf_path}'):
						msg += f'Part{line[len(f"{ewf_path}p"):]}\n'
					else:
						msg += f'{line}\n'
				self.log.info(msg, echo=True)
			ret = run(['umount', f'{mount_path}'], capture_output=True, text=True)
			if ret.stderr:
				self.log.warning(ret.stderr)
			mount_path.rmdir()


	def finish(self):
		'''Run to close process without verification'''
		try:
			with self.target_path.with_suffix('.infos.json').open('w') as f:
				dump(self.details, f)
		except Exception as ex:
			self.log.exception(ex)
		if self.target2_path:
			try:
				with self.target2_path.with_suffix('.infos.json').open('w') as f:
					dump(self.details, f)
			except Exception as ex:
				self.log.exception(ex)
		self.log.close()

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
	arg_parser.add_argument('-d', '--digest_type', type=str, choices=('sha1', 'sha256'),
		help='Calculate additional digest (hash) types besides md5', metavar='STRING'
	)
	arg_parser.add_argument('-f', '--input_format', type=str, choices=('raw', 'files'),
		help='Specify the input format (default is raw, files is restricted to logical volume files)',
		metavar='STRING'
	)
	arg_parser.add_argument('-l', '--log', type=Path, required=True, help='Specify log file (required)', metavar='FILE')
	arg_parser.add_argument('-p', '--process_buffer_size', type=int,
		help='Specify the process buffer size (default is the chunk size)', metavar='INTEGER'
	)
	arg_parser.add_argument('-w', '--zero_sectors', action='store_true', help='Zero sectors on checksum error (mimic EnCase like behavior)')
	arg_parser.add_argument('-x', '--unbuffered', action='store_true', help='Use the chunk data instead of the buffered read and write functions.')
	arg_parser.add_argument('ewf_files', nargs='+', type=Path,
		help='The first or the entire set of EWF segment files', metavar='FILE'
	)
	args = arg_parser.parse_args()
	ewfverify = EwfVerify(args.ewf_files,
		codepage = args.codepage,
		digest_type= args.digest_type,
		input_format = args.input_format,
		log = args.log,
		process_buffer_size = args.process_buffer_size,
		zero_sectors = args.zero_sectors,
		unbuffered = args.unbuffered
	)
	print(ewfverify.run())