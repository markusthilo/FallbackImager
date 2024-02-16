#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'FallbackImager'
__author__ = 'Markus Thilo'
__version__ = '0.4.0_2024-02-16'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This is a modular utility for forensic work as a complement or fallback to the commercial and/or established tools. The modules write log files into given output directories, calculate hashes and/or lists of copied files etc. Multiple jobs can be generated and executed sequentially.

This is work in progress.
'''

from pathlib import Path
from sys import executable as __executable__
from os import name as __os_name__
from argparse import ArgumentParser
from tkinter.messagebox import showerror
from lib.guibase import GuiBase
from zipimager import ZipImager, ZipImagerCli
from lib.zipimagergui import ZipImagerGui
from axchecker import AxChecker, AxCheckerCli
from lib.axcheckergui import AxCheckerGui
from sqlite import SQLite, SQLiteCli
from lib.sqlitegui import SQLiteGui
from reporter import Reporter, ReporterCli
from lib.reportergui import ReporterGui
if __os_name__ == 'nt':
	from win32com.shell.shell import IsUserAnAdmin
	from oscdimager import OscdImager, OscdImagerCli
	from lib.oscdimagergui import OscdImagerGui
	from dismimager import DismImager, DismImagerCli
	from lib.dismimagergui import DismImagerGui
	from wipew import WipeW, WipeWCli
	from lib.wipewgui import WipeWGui
else:
	from ewfimager import EwfImager, EwfImagerCli
	from lib.ewfimagergui import EwfImagerGui
	from ewfchecker import EwfChecker, EwfCheckerCli
	from lib.ewfcheckergui import EwfCheckerGui
	from wiper import WipeR, WipeRCli
	from lib.wipergui import WipeRGui
if Path(__executable__).stem == __app_name__:
	__parent_path__ = Path(__executable__).parent
else:
	__parent_path__ = Path(__file__).parent

class Gui(GuiBase):
	'''GUI, not that I need one but there is Windows and Mac folks...'''

	PAD = 4
	JOB_HEIGHT = 4
	INFO_HEIGHT = 8
	ENTRY_WIDTH = 144
	MIN_ENTRY_WIDTH = 8
	MAX_ENTRY_WIDTH = 32
	MAX_ENTRY_HEIGHT = 8
	MAX_ROW_QUANT = 5
	MAX_COLUMN_QUANT = 10
	FILES_FIELD_WIDTH = 94
	SMALL_FIELD_WIDTH = 24
	BUTTON_WIDTH = 24
	DESCRIPTION = __description__.strip()
	NOT_ADMIN = 'No Admin Privileges'
	FATAL_ERROR = 'Fatal error'
	MODULE_ERROR = 'Unable to load any module'
	ERROR = 'Error'
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
	EWF_IMAGE = 'EWF/E01 image'
	IMAGE = 'Image'
	IMAGE_REQUIRED = 'Image required'
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
	WRONG_ENTRY = 'Wrong entry'
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
	ALL_BYTES = 'Wipe all bytes/blocks'
	EXTRA_PASS = 'Extra/2 pass wipe'
	VERIFY = 'Verify'
	BLOCKSIZE = 'Block size'
	VALUE = 'Byte to overwrite'
	MAXBADBLOCKS = 'Max. bad blocks'
	MAXRETRIES = 'Max. retries'
	LOG_HEAD = 'Head of log file'
	SELECT_TEXT_FILE = 'Select text file'
	EXE = 'Executable'
	SELECT_EXE = 'Select executable'
	FILE_SYSTEM = 'File system'
	DO_NOT_CREATE = 'Do not create'
	PARTITION_TABLE = 'Partition table'
	VOLUME_NAME = 'Volume name'
	DEFAULT_VOLUME_NAME = 'Volume'
	DRIVE_LETTER = 'Drive letter'
	FILE = 'file'
	FILES = 'files'
	NEXT_AVAILABLE = 'Next available'
	NEED_HEX = 'Byte to overwrite with has to be a hex value'
	BYTE_RANGE = 'Byte to overwrite has to be inbetween 00 and ff'
	NEED_INT = 'An integer value is needed for '
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
	CASE_NO = 'Case number'
	EVIDENCE_NO = 'Evidence number'
	DEF_EVIDENCE_NO = 'EAV'
	DESCRIPTION = 'Description'
	DEF_DESCRIPTION = 'HD'
	EXAMINER_NAME = 'Examiner name'
	NOTES = 'Notes'
	MEDIA_TYPE = 'Media type'
	MEDIA_FLAG = 'Media flag'
	SEGMENT_SIZE = 'Segment size (MiB)'
	AUTO = 'auto'
	SELECT_SOURCE = 'Select source'
	IMAGE_DETAILS_REQUIRED = 'Image details required'
	SETRO = 'Set target to read only'
	TEMPLATE = 'Template'
	SELECT_TEMPLATE = 'Select template file'
	JSON_FILE = 'JSON file'
	SELECT_JSON = 'Select JSON file'
	PARSE_NOW = 'Parse now'
	PREVIEW = 'Preview'
	WRITE_TO_FILE = 'Write to file'
	PARSER_REPORTED = 'Parser reported'
	ERRORS = 'error(s)'

	def __init__(self, debug=False):
		'''Build GUI'''
		not_admin = False
		if __os_name__ == 'nt':
			candidates = (
				(OscdImager, OscdImagerCli, OscdImagerGui),
				(DismImager, DismImagerCli, DismImagerGui),
				(ZipImager, ZipImagerCli, ZipImagerGui),
				(SQLite, SQLiteCli, SQLiteGui),
				(Reporter, ReporterCli, ReporterGui),
				(AxChecker, AxCheckerCli, AxCheckerGui),
				(WipeW, WipeWCli, WipeWGui)
			)
			if not IsUserAnAdmin():
				not_admin = True
		else:
			candidates = (
				(EwfImager, EwfImagerCli, EwfImagerGui),
				(EwfChecker, EwfCheckerCli, EwfCheckerGui),
				(EwfChecker, ReporterCli, ReporterGui),
				(ZipImager, ZipImagerCli, ZipImagerGui),
				(SQLite, SQLiteCli, SQLiteGui),
				(AxChecker, AxCheckerCli, AxCheckerGui),
				(WipeR, WipeRCli, WipeRGui)
			)
		super().__init__(__app_name__,__version__, __parent_path__,
			[(Cli, Gui) for Module, Cli, Gui in candidates if Module().available],
			not_admin = not_admin,
			debug = debug
		)

if __name__ == '__main__':  # start here
	argp = ArgumentParser(description=__description__.strip())
	argp.add_argument('-d', '--debug', default=False, action='store_true', help='Debug mode')
	args = argp.parse_args()
	Gui(debug=args.debug).mainloop()
