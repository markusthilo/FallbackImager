#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'OscdImager'
__author__ = 'Markus Thilo'
__version__ = '0.0.4_2023-05-30'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Create ISO image using MS OSCDIMG
'''

from pathlib import Path
from argparse import ArgumentParser
from subprocess import Popen, PIPE, STDOUT, STARTUPINFO, STARTF_USESHOWWINDOW
from lib.extpath import ExtPath
from lib.timestamp import TimeStamp
from lib.logger import Logger
from lib.greplists import GrepLists
from lib.hashes import FileHashes
from lib.guielements import ExpandedFrame, SourceDirSelector, GridLabel, FilenameSelector
from lib.guielements import GridSeparator, DirSelector, StringSelector, FileSelector, GridButton
from isoverify import IsoVerify

__oscdimg_exe_name__ = 'oscdimg.exe'
for __oscdimg_exe_path__ in (
		Path.cwd()/__oscdimg_exe_name__,
		Path.cwd()/'bin'/__oscdimg_exe_name__,
		Path(__file__)/__oscdimg_exe_name__,
		Path(__file__)/'bin'/__oscdimg_exe_name__,
		(Path('C:')/
			'Program Files (x86)'/'Windows Kits'/
			'10'/'Assessment and Deployment Kit'/'Deployment Tools'/'amd64'/'Oscdimg'/
			__oscdimg_exe_name__
		)
	):
	if __oscdimg_exe_path__.is_file():
		break
else:
	__oscdimg_exe_path__ = None

class Oscdimg:
	'''OSCDIMG via subprocess (oscdimg.exe -h -m -l$label -u2 $source $image)'''

	@staticmethod
	def _label(string):
		'''Normalize string so it can be used as ISO label'''
		return ''.join(char for char in string if char.isalnum() or char in ['_', '-'])[:32]

	def __init__(self, root,
			filename = None,
			outdir = None,
			name = None,
			exe = None,
			log = None,
			echo = print
		):
		'''Init subprocess for OSCDIMG without showing a terminal window'''
		self.root_path = Path(root)
		self.filename = TimeStamp.now_or(filename)
		self.outdir = ExtPath.mkdir(outdir)
		self.label = self._label(self.root_path.stem)
		self.image_path = ExtPath.child(f'{self.filename}.iso', parent=self.outdir)
		self.content_path = ExtPath.child(f'{self.filename}_content.txt', parent=self.outdir)
		self.dropped_path = ExtPath.child(f'{self.filename}_dropped.txt', parent=self.outdir)
		self.args_str = f'-h -k -m -l"{self.label}" -u2 "{self.root_path}" "{self.image_path}"'
		self.echo = echo
		if log:
			self.log = log
		else:
			self.log = Logger(self.filename, outdir=self.outdir, head='oscdimg.Oscdimg', echo=echo)
		if exe:
			self.exe_path = exe
		else:
			if __oscdimg_exe_path__:
				self.exe_path = __oscdimg_exe_path__
			else:
				self.log.error('Path to oscdimg.exe is not given and cannot be found')
		self.cmd_str = f'{self.exe_path} {self.args_str}'
		self.startupinfo = STARTUPINFO()
		self.startupinfo.dwFlags |= STARTF_USESHOWWINDOW
		self.echo = echo
		if log:
			selg.log = log
		else:
			self.log = Logger(self.filename, outdir=self.outdir, head='oscdimg.Oscdimg', echo=echo)

	def create_iso(self):
		'''Create image'''
		self.log.info(f'> {self.exe_path.name} {self.args_str}', echo=True)
		proc = Popen(self.cmd_str,
			shell = True,
			stdout = PIPE,
			stderr = STDOUT,
			encoding = 'utf-8',
			errors = 'ignore',
			universal_newlines = True,
			startupinfo = self.startupinfo
		)
		for line in proc.stdout:
			if line.strip():
				self.echo(line.strip())
		proc.stdout_str = None
		proc.stderr_str = None
		if self.image_path.is_file():
			self.log.finished(proc, echo=True)
		else:
			self.log.finished(proc, error=': Could not create image\n')
		self.log.info(f'\n--- Image hashes ---\n{FileHashes(self.image_path)}', echo=True)

class OscdimgCli(ArgumentParser):
	'''CLI for the imager'''

	def __init__(self, **kwargs):
		'''Define CLI using argparser'''
		super().__init__(description=__description__, **kwargs)
		self.add_argument('-f', '--filename', type=str,
			help='Filename to generated (without extension)', metavar='STRING'
		)
		self.add_argument('-n', '--name', type=str,
			help='Label of the ISO', metavar='STRING'
		)
		self.add_argument('-o', '--outdir', type=Path,
			help='Directory to write generated files (default: current)', metavar='DIRECTORY'
		)
		self.add_argument('-x', '--exe', type=Path,
			help='Path to oscdimg.exe (use if not found automatically)', metavar='FILE'
		)
		self.add_argument('root', nargs=1, type=Path,
			help='Source', metavar='DIRECTORY'
		)

	def parse(self, *cmd):
		'''Parse arguments'''
		args = super().parse_args(*cmd)
		self.root = args.root[0]
		self.filename = args.filename
		self.name = args.name
		self.outdir = args.outdir
		self.exe = args.exe

	def run(self, echo=print):
		'''Run the imager'''
		image = Oscdimg(self.root,
			filename = self.filename,
			outdir = self.outdir,
			name = self.name,
			exe = self.exe,
			echo = echo
		)
		image.create_iso()
		IsoVerify(self.root,
			imagepath = image.image_path,
			filename = self.filename,
			outdir = self.outdir,
			echo = echo,
			log = image.log
		).posix_verify()
		image.log.close()

class OscdimgGui:
	'''Notebook page'''

	CMD = __app_name__
	DESCRIPTION = __description__

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.CMD)
		frame = ExpandedFrame(root, root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		root.row = 0
		SourceDirSelector(root, frame)
		GridLabel(root, frame, root.DESTINATION, columnspan=2)
		FilenameSelector(root, frame, root.FILENAME, root.FILENAME)
		DirSelector(root, frame, root.OUTDIR,
			root.DIRECTORY, root.SELECT_DEST_DIR)
		self.name_str = StringSelector(root, frame, root.IMAGE_NAME, root.IMAGE_NAME,
			command=self._gen_name)
		GridSeparator(root, frame)	
		FileSelector(root, frame, root.OSCDIMG_EXE, root.OSCDIMG_EXE, root.SELECT_OSCDIMG_EXE,
			filetype=(root.OSCDIMG_EXE, 'oscdimg.exe'), default=__oscdimg_exe_path__)
		GridSeparator(root, frame)
		GridButton(root, frame, f'{root.ADD_JOB} {self.CMD}' , self._add_job, columnspan=3)
		self.root = root
	
	def _gen_name(self):
		'''Generate a name for the image'''
		self.root.settings.section = self.CMD
		if not self.name_str.string.get() and self.root.settings.get(self.root.SOURCE):
			self.name_str.string.set(
				Oscdimg._label(Path(self.root.settings.get(self.root.SOURCE)).stem))
	
	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		source = self.root.settings.get(self.root.SOURCE)
		outdir = self.root.settings.get(self.root.OUTDIR)
		filename = self.root.settings.get(self.root.FILENAME)
		name = self.root.settings.get(self.root.IMAGE_NAME)
		oscdimg_exe = self.root.settings.get(self.root.OSCDIMG_EXE)
		if not source or not outdir or not filename:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.SOURCED_DEST_REQUIRED
			)
			return
		cmd = self.root.settings.section.lower()
		if oscdimg_exe and oscdimg_exe != __oscdimg_exe_path__:
			cmd += f' --exe "{oscdimg_exe}"'
		cmd += f' --{self.root.OUTDIR.lower()} "{outdir}"'
		cmd += f' --{self.root.FILENAME.lower()} "{filename}"'
		if name:
			cmd += f' --{self.root.IMAGE_NAME.lower()} "{name}"'
		cmd += f' "{source}"'
		self.root.append_job(cmd)

if __name__ == '__main__':	# start here if called as application
	app = OscdimgCli()
	app.parse()
	app.run()
