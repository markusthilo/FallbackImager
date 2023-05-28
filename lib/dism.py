#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE, STARTUPINFO, STARTF_USESHOWWINDOW
from .timestamp import TimeStamp

class Dism(Popen):
	'''Dism via subprocess'''

	@staticmethod
	def get_value(string):
		'''Get value after colon'''
		try:
			return string.split(':', 1)[1].strip(' "')
		except IndexError:
			return ''

	def __init__(self, args, echo=print, verbose_stdout=False, verbose_stderr=True):
		'''Init subprocess for Dism without showing a terminal window'''
		self.cmd_str = f'Dism {args}'
		self.echo = echo
		self.verbose_stdout = verbose_stdout
		self.verbose_stderr = verbose_stderr
		self.startupinfo = STARTUPINFO()
		self.startupinfo.dwFlags |= STARTF_USESHOWWINDOW
		super().__init__(
			self.cmd_str,
			shell = True,
			stdout = PIPE,
			stderr = PIPE,
			encoding = 'utf-8',
			errors = 'ignore',
			universal_newlines = True,
			startupinfo = self.startupinfo
		)

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

	def grep_stdout(self, string, *ln_key):
		'''Get values indicated by grep string'''
		stdout = [line for line in self.readlines_stdout()]
		lower_str = string.lower()
		for ln, line in enumerate(stdout):
			if line.lower().startswith(lower_str):
				yield {key: self.get_value(stdout[ln+ln_delta]) for ln_delta, key in ln_key}

class CaptureImage(Dism):
	'''
	Dism /Capture-Image /ImageFile:$image /CaptureDir:$capture /Name:$name
	/Description:$description /Compress:{max|fast|none}
	'''

	def __init__(self, image, capture, name=None, description=None, compress='none',
		echo=print, verbose_stdout=False, verbose_stderr=True
	):
		'''Launch Dism'''
		args = f'/Capture-Image /ImageFile:"{image}" /CaptureDir:"{capture}"'
		if name:
			args += f' /Name:"{name}"'
		else:
			args += f' /Name:"{capture}"'
		args += f' /Description:"{TimeStamp.now_or(description)}" /Compress:{compress}'
		super().__init__(args,
			echo = echo,
			verbose_stdout = verbose_stdout,
			verbose_stderr = verbose_stderr
		)

class ImageContent(Dism):
	'''Dism /List-Image /ImageFile:$image /Index:$i'''

	def __init__(self, image, index=1, echo=print, verbose_stdout=False, verbose_stderr=True):
		'''Launch Dism'''
		super().__init__(f'/List-Image /ImageFile:"{image}" /Index:{index}',
			echo = echo,
			verbose_stdout = verbose_stdout,
			verbose_stderr = verbose_stderr
		)

class GetImageInfo(Dism):
	'''Dism /Get-ImageInfo /ImageFile:$image'''

	def __init__(self, image, echo=print, verbose_stdout=False, verbose_stderr=True):
		'''Launch Dism'''
		super().__init__(f'/Get-ImageInfo /ImageFile:"{image}"',
			echo = echo,
			verbose_stdout = verbose_stdout,
			verbose_stderr = verbose_stderr
		)
		
	def decode(self):
		'''Decode to tuples'''
		return self.grep_stdout('Index:',
			(0, 'index'),
			(1, 'name' ),
			(2, 'descr'),
			(3, 'size')
		)

class GetMountedImageInfo(Dism):
	'''Dism /Get-MountedImageInfo'''

	def __init__(self, echo=print, verbose_stdout=False, verbose_stderr=True):
		'''Launch Dism'''
		super().__init__('/Get-MountedImageInfo',
			echo = echo,
			verbose_stdout = verbose_stdout,
			verbose_stderr = verbose_stderr
		)

	def decode(self):
		'''Decode to tuples'''
		return self.grep_stdout('Imageindex:',
			(-2, 'mnt'),
			(-1, 'path'),
			(0, 'index')
		)

class MountImage(Dism):
	'''Dism /Mount-Image /ImageFile:$image /index:$i /MountDir:$mnt /ReadOnly'''

	def __init__(self, image, index, mnt, echo=print, verbose_stdout=False, verbose_stderr=True):
		'''Launch Dism'''
		super().__init__(f'/Mount-Image /ImageFile:"{image}" /index:{index} /MountDir:{mnt} /ReadOnly',
			echo = echo,
			verbose_stdout = verbose_stdout,
			verbose_stderr = verbose_stderr
		)

class UnmountImage(Dism):
	'''Dism /Unmount-Image /MountDir:$mnt /discard'''

	def __init__(self, mnt, echo=print, verbose_stdout=False, verbose_stderr=True):
		'''Launch Dism'''
		super().__init__(f'/Unmount-Image /MountDir:{mnt} /discard',
			echo = echo,
			verbose_stdout = verbose_stdout,
			verbose_stderr = verbose_stderr
		)
