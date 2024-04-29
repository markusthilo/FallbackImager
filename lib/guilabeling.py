#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class AxCheckerLabels:

    TIP_CASE_FILE = 'Select Case.mfdb in the AXIOM case directory'


    '''
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
	ROOT = 'Root'
	FIRST_CHOOSE_CASE = 'First choose AXIOM case file (Case.mfdb)'
	UNABLE_DETECT_PATHS = 'Unable to detect paths'
	UNABLE_DETECT_PARTITIONS = 'Unable to detect partitions'
	FIRST_CHOOSE_TSV = 'First choose text/TSV file'
	SELECT_COLUMN = 'Select column with path to compare'
	CASE_REQUIRED = 'AXIOM case file is required'
	ID_REQUIRED = 'ID of AXIOM source as root to compare is required'
	ROOT_DIR_REQUIRED = 'Root directory is required' 
	TSV_AND_COL_REQUIRED = 'Text/TSV file and column matching the AXIOM partition are required'
	WIPE = 'Wipe'
	TARGET = 'Target'
	SELECT_DRIVE = 'Select drive'
	SELECT_FILES = 'Select file(s) to wipe'
	MOUNTPOINT = 'Mointpoint'
	SELECT_MOUNTPOINT = 'Select Directory to mount new partition'
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
	ADD_SRC_FILES = 'Add file(s) to source'
	ADD_SRC_DIR = 'Add directory to source'
	UNABLE_ACCESS = 'Unable to access'
	ROOT_HELP = 'Root permission might help'
    '''