#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'FallbackImager'
__author__ = 'Markus Thilo'
__version__ = '0.2.3_2023-11-23'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This is a modular utility for forensic work as a complement or fallback to the commercial and/or established tools. The modules write log files into given output directories, calculate hashes and/or lists of copied files etc. Multiple jobs can be generated and executed sequentially.

In this testing state only Windows (10/11) is supported. It is work in progress.
'''

from pathlib import Path
from sys import executable as __executable__
from os import name as __os_name__
from argparse import ArgumentParser
from tkinter.messagebox import showerror
from lib.guibase import GuiBase
from mkisoimager import MkIsoImagerGui, MkIsoImagerCli
from oscdimager import OscdimgGui, OscdimgCli
from isoverify import IsoVerifyGui, IsoVerifyCli
from dismimager import DismImagerGui, DismImagerCli
from zipimager import ZipImagerGui, ZipImagerCli
from axchecker import AxCheckerGui, AxCheckerCli
from hdzero import HdZeroGui, HdZeroCli
from sqlite import SQLiteGui, SQLiteCli

### MODULES, SYSTEM AND SYSTEM REALTED SETTINGS ###
__not_admin__ = None
if __os_name__ == 'nt':
	from win32com.shell.shell import IsUserAnAdmin
	if IsUserAnAdmin():
		__modules__ = {
			MkIsoImagerGui: MkIsoImagerCli,
			OscdimgGui: OscdimgCli,
			IsoVerifyGui: IsoVerifyCli,
			DismImagerGui: DismImagerCli,
			ZipImagerGui: ZipImagerCli,
			SQLiteGui: SQLiteCli,
			AxCheckerGui: AxCheckerCli,
			HdZeroGui: HdZeroCli
		}
	else:
		__modules__ = {
			MkIsoImagerGui: MkIsoImagerCli,
			OscdimgGui: OscdimgCli,
			IsoVerifyGui: IsoVerifyCli,
			ZipImagerGui: ZipImagerCli,
			SQLiteGui: SQLiteCli,
			AxCheckerGui: AxCheckerCli
		}
		__not_admin__ = 'No Admin Privileges'
else:
		__modules__ = {
			MkIsoImagerGui: MkIsoImagerCli,
			IsoVerifyGui: IsoVerifyCli,
			ZipImagerGui: ZipImagerCli,
			SQLiteGui: SQLiteCli,
			AxCheckerGui: AxCheckerCli
		}
__executable__ = Path(__executable__)
__file__ = Path(__file__)
if __executable__.stem.lower() == __file__.stem.lower():
	__app_name__ = __executable__.stem
	__parent_path__ = __executable__.parent
else:
	__app_name__ = __file__.stem
	__parent_path__ = __file__.parent
__icon_path__ = __parent_path__/'appicon.ico'
__settings_path__ = __parent_path__/'settings.json'
###############

class Gui(GuiBase):
	'''GUI, not that I need one but there is Windows and Mac folks...'''

	PAD = 4
	JOB_HEIGHT = 4
	INFO_HEIGHT = 8
	ENTRY_WIDTH = 128
	MIN_ENTRY_WIDTH = 8
	MAX_ENTRY_WIDTH = 32
	MAX_ENTRY_HEIGHT = 8
	MAX_ROW_QUANT = 5
	MAX_COLUMN_QUANT = 10
	FILES_FIELD_WIDTH = 94
	VOLUME_NAME_WIDTH = 24
	IMAGERS = __modules__
	DESCRIPTION = __description__.strip()
	AVAILABLE_MODULES = 'Available modules:'
	HELP = 'Help'
	JOBS = 'Jobs'
	REMOVE_LAST = 'Remove last'
	INFOS = 'Infos'
	CLEAR_INFOS = 'Clear infos'
	START_JOBS = 'Start jobs'
	RUNNING = 'Running...'
	QUIT = 'Quit'
	ARE_YOU_SURE = 'Are you sure?'
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
	FLAT = 'Flat structure without folders'
	ISO_IMAGE = 'ISO image'
	IMAGE = 'Image'
	SELECT_IMAGE = 'Select image file'
	IMAGE_NAME = 'Name'
	IMAGE_DESCRIPTION = 'Description'
	CONFIGURATION = 'Configuration'
	MKISOFS = 'mkisofs'
	SELECT_MKISOFS = 'Select mkisofs executable/binary'
	OSCDIMG_EXE = 'OSCDIMG'
	SELECT_OSCDIMG_EXE = 'Select OSCDIMG executable'
	TO_DO = 'To do'
	ISO_REQUIRED = 'ISO image is required'
	CREATE_AND_VERIFY = 'Create and verify image'
	VERIFY_FILE = 'Verify'
	SELECT_VERIFY_FILE = 'Select image file to verify'
	FILEFILTER = 'Filter by file list'
	NO_FILTER = 'No filter'
	NO_FILEFILTER = 'Do not filter by TSV/file list'
	SKIP_PATH_CHECK = 'Skip check of paths by blacklist or whitelist'
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
	FINISHED_ALL_JOBS = 'Finished all jobs.\n'
	EXCEPTIONS = 'Exceptions occured'
	UNDETECTED = 'Could not detect what to do.\n'
	MISSING_ENTRIES = 'Missing entries'
	SOURCE_REQUIRED = 'Source is required'
	DEST_DIR_REQUIRED = 'Destination directory is required'
	DEST_FN_REQUIRED = 'Destination filename is required'
	IMAGE_REQUIRED = 'Image file is required'
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
	CASE_REQUIRED = 'AXIOM case file is required'
	PARTITION_REQUIRED = 'Partition in the AXIOM case is required'
	ROOT_DIR_REQUIRED = 'Root directory is required' 
	TSV_AND_COL_REQUIRED = 'Text/TSV file and column matching the AXIOM partition are required'
	WIPE = 'Wipe'
	TARGET = 'Target'
	SELECT_DRIVE = 'Select drive'
	SELECT_FILES = 'Select file(s) to wipe'
	LOGGING = 'Logging'
	NORMAL_WIPE = 'Normal wipe'
	EVERY_BLOCK = 'Wipe every block'
	EXTRA_PASS = 'Extra/2 pass wipe'
	VERIFY = 'Verify'
	BLOCKSIZE = 'Block size'
	USE_FF = 'Use 0xFF to wipe'
	LOG_HEAD = 'Head of log file'
	SELECT_TEXT_FILE = 'Select text file'
	ZEROD_EXE = 'zerod'
	SELECT_ZEROD_EXE = 'Select ZEROD executable'
	FILE_SYSTEM = 'File system'
	DO_NOT_CREATE = 'Do not create'
	PARTITION_TABLE = 'Partition table'
	VOLUME_NAME = 'Volume name'
	DEFAULT_VOLUME_NAME = 'Volume'
	DRIVE_LETTER = 'Drive letter'
	FILE = 'file'
	FILES = 'files'
	NEXT_AVAILABLE = 'Next available'
	REFRESH = 'Refresh'
	TARGET_REQUIRED = 'Physical drive or file(s) to wipe required'
	LOGDIR_REQUIRED = 'Target directory for logging required'
	DRIVE_LETTER_IN_USE = 'Drive letter is in use'
	USE_IT_ANYWAY = 'Use it anyway?'
	DATABASE = 'Database'
	SQLITE_DB = 'SQLite DB'
	SELECT_DB = 'Select DB'
	DUMP = 'Dump'
	SCHEMA = 'Schema'
	EXECUTE_SQL = 'Execute SQL'
	ALTERNATIVE = 'Alternative'
	DUMP_SCHEMA = 'Dump schema'
	DUMP_CONTENT = 'Dump content'
	TABLE = 'Table'
	SQL_FILE = 'SQL file'
	SELECT_SQL_FILE = 'Select SQL file'
	FIRST_CHOOSE_DB = 'First choose SQLite database file (.db)'
	SQLITE_DB_REQUIRED = 'SQLite database file is required'
	SQL_FILE_REQUIRED = 'SQL file is required'

	def __init__(self, debug=False):
		'''Build GUI'''
		super().__init__(__app_name__,__version__, __icon_path__, __settings_path__,
			not_admin = __not_admin__,
			debug = debug
		)

if __name__ == '__main__':  # start here
	argp = ArgumentParser(description=__description__.strip())
	argp.add_argument('-d', '--debug', default=False, action='store_true', help='Debug mode')
	args = argp.parse_args()
	Gui(debug=args.debug).mainloop()
