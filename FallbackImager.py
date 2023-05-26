#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'FallbackImager'
__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-26'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Imager for different formats as a fallback when the usual tools do not work
'''

from pathlib import Path
from sys import executable as __executable__
from os import name as __os_name__
from tkinter.messagebox import showerror
from lib.guibase import GuiBase
from oscdimager import OscdimgGui, OscdimgCli
from pycdlibimager import PyCdlibGui, PyCdlibCli
from dismimager import DismImagerGui, DismImagerCli
from axchecker import AxCheckerGui, AxCheckerCli

### MODULES ###
if __os_name__ == 'nt':
	from win32com.shell.shell import IsUserAnAdmin
	if IsUserAnAdmin():
		__modules__ = {
			OscdimgGui: OscdimgCli,
			PyCdlibGui: PyCdlibCli,
			DismImagerGui: DismImagerCli,
			AxCheckerGui: AxCheckerCli
		}
	else:
		__modules__ = {
			OscdimgGui: OscdimgCli,
			PyCdlibGui: PyCdlibCli,
			AxCheckerGui: AxCheckerCli
		}
###############

__executable__ = Path(__executable__)
__file__ = Path(__file__)
if __executable__.stem.lower() == __file__.stem.lower():
	__app_name__ = __executable__.stem
	__parent_path__ = __executable__.parent
else:
	__app_name__ = __file__.stem
	__parent_path__ = __file__.parent
__icon_path__ = __parent_path__/'appicon.ico'
__settings_path__ = __parent_path__/f'{__app_name__.lower()}.json'

class Gui(GuiBase):
	'''GUI, not that I need one but there is Windows and Mac folks...'''

	PAD = 4
	JOB_HEIGHT = 4
	INFO_HEIGHT = 8
	ENTRY_WIDTH = 128
	IMAGERS = __modules__
	DESCRIPTION = __description__.strip()
	HELP = 'Help'
	JOBS = 'Jobs'
	REMOVE_LAST = 'Remove last'
	INFOS = 'Infos'
	CLEAR_INFOS = 'Clear infos'
	START_JOBS = 'Start jobs'
	RUNNING = 'Running...'
	QUIT = 'Quit'
	SOURCE = 'Source'
	ASK_SOURCE = 'Select source'
	PATH = 'Path'
	DIRECTORY = 'Directory'
	SELECT_ROOT = 'Select source root directory'
	DESTINATION = 'Destination'
	FILENAME = 'Filename'
	OUTDIR = 'Outdir'
	SELECT_DEST_DIR = 'Select destination directory'
	IMAGE_NAME = 'Name'
	IMAGE_DESCRIPTION = 'Description'
	TO_DO = 'To do'
	CREATE_AND_VERIFY = 'Create and verify image'
	VERIFY_FILE = 'Verify'
	SELECT_VERIFY_FILE = 'Select image file to verify'
	SKIP_PATH_CHECK = 'Skip check of paths by blacklist or whitelist'
	PATHFILTER = 'Pathfilter'
	CHECK_ALL_PATHS = 'Check if all source paths are in image'
	BLACKLIST = 'Blacklist'
	SELECT_BLACKLIST = 'Select blacklist'
	WHITELIST = 'Whitelist'
	SELECT_WHITELIST = 'Select whitelist'
	COPY_EXE = 'Copy WimMount.exe to destination directory'
	ADD_JOB = 'Add job'
	RUNNING = 'Running'
	NOTHING2DO = 'Add jobs! Nothing to do here.\n'
	ALL_DONE = 'All done.\n'
	UNDETECTED = 'Could not detect what to do.\n'
	MISSING_ENTRIES = 'Missing entries'
	SOURCED_DEST_REQUIRED = 'Source and destination are required'
	AXIOM = 'AXIOM'
	CASE_FILE = 'Case File'
	AXIOM_CASE_FILE = 'Case.mfdb'
	OPEN_CASE_FILE = 'Open case file'
	PARTITION = 'Partition'
	DO_NOT_COMPARE = 'Do not compare'
	COMPARE_TO = 'Compare to'
	FILE_STRUCTURE = 'File structure'
	ASK_FILE_STRUCTURE = 'Select root of file structure'

	def __init__(self):
		'''Build GUI'''
		super().__init__(__app_name__, __version__, __icon_path__, __settings_path__)

if __name__ == '__main__':  # start here
	#if IsUserAnAdmin():
	Gui().mainloop()
	#else:
	#	error = 'Admin rights required'
	#	showerror(title=__app_name__, message=error)
	#	raise RuntimeError(error)

	
