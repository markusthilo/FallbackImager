#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'FallbackImager'
__author__ = 'Markus Thilo'
__version__ = '0.0.4_2023-06-03'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Imager for different formats as a fallback when the usual tools let you down
'''

from pathlib import Path
from sys import executable as __executable__
from os import name as __os_name__
from argparse import ArgumentParser
from tkinter.messagebox import showerror
from lib.guibase import GuiBase
from oscdimager import OscdimgGui, OscdimgCli
from isoverify import IsoVerifyGui, IsoVerifyCli
from dismimager import DismImagerGui, DismImagerCli
from zipimager import ZipImagerGui, ZipImagerCli
from axchecker import AxCheckerGui, AxCheckerCli

### MODULES ###
if __os_name__ == 'nt':
	from win32com.shell.shell import IsUserAnAdmin
	if IsUserAnAdmin():
		__modules__ = {
			OscdimgGui: OscdimgCli,
			IsoVerifyGui: IsoVerifyCli,
			DismImagerGui: DismImagerCli,
			ZipImagerGui: ZipImagerCli,
			AxCheckerGui: AxCheckerCli
		}
	else:
		__modules__ = {
			OscdimgGui: OscdimgCli,
			IsoVerifyGui: IsoVerifyCli,
			ZipImagerGui: ZipImagerCli,
			AxCheckerGui: AxCheckerCli
		}
else:
	raise NotImplementedError('Right now there is only a Win Version')
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
	MIN_ENTRY_WIDTH = 16
	MAX_ENTRY_WIDTH = 64
	MAX_ENTRY_HEIGHT = 8
	MAX_ROW_QUANT = 8
	MAX_COLUMN_QUANT = 10
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
	FILTER = 'Filter'
	ISO_IMAGE = 'ISO image'
	IMAGE = 'Image'
	SELECT_IMAGE = 'Select image file'
	IMAGE_NAME = 'Name'
	IMAGE_DESCRIPTION = 'Description'
	OSCDIMG_EXE = 'OSCDIMG'
	SELECT_OSCDIMG_EXE = 'Select OSCDIMG executable'
	TO_DO = 'To do'
	CREATE_AND_VERIFY = 'Create and verify image'
	VERIFY_FILE = 'Verify'
	SELECT_VERIFY_FILE = 'Select image file to verify'
	FILEFILTER = 'Filter by file list'
	NO_FILEFILTER = 'Do not filter by TSV/file list'
	SKIP_PATH_CHECK = 'Skip check of paths by blacklist or whitelist'
	PATHFILTER = 'Pathfilter'
	REGEXFILTER = 'RegEx filter'
	CHECK_ALL_PATHS = 'Check if all source paths are in image'
	NO_REGEXFILTER = 'Do not filter by regular expression(s)'
	BLACKLIST = 'Blacklist'
	SELECT_BLACKLIST = 'Select blacklist'
	WHITELIST = 'Whitelist'
	SELECT_WHITELIST = 'Select whitelist'
	COPY_EXE = 'Copy WimMount.exe to destination directory'
	ADD_JOB = 'Add job'
	RUNNING = 'Running'
	NOTHING2DO = 'Add jobs! Nothing to do here.\n'
	ALL_DONE = 'All done.\n'
	EXCEPTIONS = 'Exceptions occured'
	UNDETECTED = 'Could not detect what to do.\n'
	MISSING_ENTRIES = 'Missing entries'
	SOURCED_DEST_REQUIRED = 'Source and destination are required'
	COMPRESSION = 'Compression'
	MAX = 'Max'
	FAST = 'Fast'
	NONE = 'None'
	AXIOM = 'AXIOM'
	CASE_FILE = 'Case File'
	AXIOM_CASE_FILE = 'Case.mfdb'
	OPEN_CASE_FILE = 'Open case file'
	PARTITION = 'Partition'
	DO_NOT_COMPARE = 'Do not compare'
	COMPARE_TO = 'Compare to'
	FILE_STRUCTURE = 'File structure'
	TSV = 'Text/TSV file'
	TSV_REQUIRED = 'Text/TSV file is required'
	SELECT_TSV = 'Select Text/TSV file'
	COLUMN = 'Column'
	TSV_NO_HEAD = 'Text/TSV file does not have a head line'
	SELECT_FILE_STRUCTURE = 'Select root of file structure'
	SELECT_PARTITION = 'Select partition'
	SELECT = 'Select'
	FIRST_CHOOSE_CASE = 'First choose AXIOM case file (Case.mfdb)'
	UNABLE_DETECT_PARTITIONS = 'Unable to detect partitions'
	FIRST_CHOOSE_TSV = 'First choose text/TSV file'
	SELECT_COLUMN = 'Select column with path to compare'
	CASE_AND_PARTITION_REQUIRED = 'AXIOM case file and partition are required'
	ROOT_DIR_REQUIRED = 'Root directory is required' 
	TSV_AND_COL_REQUIRED = 'Text/TSV file and column matching the AXIOM partition are required'

	def __init__(self, debug=False):
		'''Build GUI'''
		super().__init__(__app_name__, __version__, __icon_path__, __settings_path__, debug=debug)

if __name__ == '__main__':  # start here
	argp = ArgumentParser(description=__description__.strip())
	argp.add_argument('-d', '--debug', default=False, action='store_true',
			help='Debug mode'
		)
	args = argp.parse_args()
	Gui(debug=args.debug).mainloop()
