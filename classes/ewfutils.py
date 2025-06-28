#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .coreutils import CoreUtils

class Ewf:
    '''Work with an EWF/E10 file'''

    def __init__(self, ewf_path, log=None):
        '''Initialize the Ewf class'''

        self.image_path = Path(image_path)
        self.ewfmount_path = Path(ewfmount_path)
        self.log = Logger(log=log)

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

