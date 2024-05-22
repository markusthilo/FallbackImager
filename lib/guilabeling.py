#!/usr/bin/env python3
# -*- coding: utf-8 -*-

### Labels, Tooltips and Errors ###
### English ###

class BasicLabels:
	AVAILABLE_MODULES = 'Available modules:'
	FATAL_ERROR = 'Fatal error'
	MODULE_ERROR = 'Unable to load any module'
	ERROR = 'Error'
	HELP = 'Help'
	JOBS = 'Jobs'
	ADD_JOB = 'Add job'
	TIP_ADD_JOB = 'Add job as configured above to job queue'
	SELECT = 'Select'
	QUIT = 'Quit'
	ARE_YOU_SURE = 'Are you sure?'
	REMOVE_LAST = 'Remove last'
	TIP_REMOVE_LAST_JOB = 'Remove last job from the job queue'
	INFOS = 'Infos'
	CLEAR_INFOS = 'Clear infos'
	TIP_CLEAR_INFOS = 'Clear info field'
	START_JOBS = 'Start jobs'
	TIP_START_JOBS = 'Start job after job in queue'
	RUNNING = 'Running'
	NOTHING2DO = 'Add jobs! Nothing to do here.'
	ALL_DONE = 'All done.'
	FINISHED_ALL_JOBS = 'Finished all jobs.'
	EXCEPTIONS = 'Exceptions occured!'
	UNDETECTED = 'Could not detect what to do!'
	DESTINATION = 'Destination'
	DESTINATION_REQUIRED = 'Destination is required'
	LOGGING_DIR_REQUIRED = 'Directory to write logs is required'
	DIRECTORY = 'Directory'
	SELECT_OUTDIR = 'Select destination directory'
	TIP_OUTDIR = '''Select destination directory to write
logs and resulting file(s)'''
	OUTDIR_REQUIRED = 'Destination directory is required'
	FILENAME = 'Filename'
	TIP_FILENAME = '''Base of filename for generated files,
click to auto generate (if empty)'''
	SELECT = 'Select'
	FILE = 'file'
	FILES = 'files'
	SELECT_FILE = 'Select file'
	SELECT_TEXT_FILE = 'Select text file'
	TASK = 'Task'
	TIP_RADIO_BUTTONS = 'Select one option'
	SOURCE = 'Source'
	SELECT_SOURCE = 'Select Source'
	SOURCE_REQUIRED = 'Source is required'
	TARGET = 'Target'
	IMAGE = 'Image'
	SELECT_IMAGE = 'Select image'
	IMAGE_REQUIRED = 'Image is required'
	LOGGING = 'Logging'
	CONFIGURATION = 'Configuration'
	COMPRESSION = 'Compression'
	NONE = 'None'
	REFRESH = 'Refresh'
	AUTO = 'auto'
	MISSING_ENTRY = 'Missing entry'
	ARE_YOU_ROOT = 'Are you root?'
	ADMIN_REQUIRED = 'Admin privileges required'

class EwfImagerLabels(BasicLabels):
	TIP_SOURCE = 'Select source to image as EWF/E01'
	SETRO = 'Set device to read only'
	TIP_SETRO = '''Execute "blockdev --setro /dev/..."
to make sure, source stays untouched'''
	TIP_IMAGE_LOGS = 'Destination directory to write image and logs'
	CASE_NO = 'Case number'
	TIP_METADATA = 'Metadata stored in the EWF/E91 image'
	EVIDENCE_NO = 'Evidence number'
	DEF_EVIDENCE_NO = 'EAV'
	DESCRIPTION = 'Description'
	DEF_DESCRIPTION = 'HD'
	EXAMINER_NAME = 'Examiner name'
	NOTES = 'Notes'
	TIP_NOTE = 'Select this line to put in the image metadata'
	SEGMENT_SIZE = 'Segment size'
	TIP_SEGMENT_SIZE = '''Segment size of EWF/E01 image in
MiB, GiB or number of segments
(e.g. 512m, 4g, 40)'''
	DEF_SIZE = '40'
	TIP_COMPRESSION = 'Compression level of the EWF/E01 image'
	MEDIA_TYPE = 'Media type'
	MEDIA_FLAG = 'Media flag'
	UNABLE_ACCESS = 'Unable to access'
	MISSING_METADATA = 'Case number, evidence number and description are required to generate filename'
	METADATA_REQUIRED = 'Case number, evidence number and description are required as metadata for the EWF/E01 image'

class ZipImagerLabels(BasicLabels):
	TIP_SOURCE = 'Select source root to build ZIP file from'

class HashedCopyLabels(BasicLabels):
	ADD_FILES = 'Add file(s)'
	TIP_ADD_FILES = 'Select file(s) to copy'
	ADD_DIR = 'Add directory'
	TIP_ADD_DIR = 'Select a directory to copy'
	SELECT_DESTINATION = 'Select destination to copy to'
	TIP_DESTINATION = 'Destination directory (or device/volume) to copy to'

class SQLiteLabels(BasicLabels):
	SQLITE_DB = 'SQLite DB'
	SELECT_DB = 'Select SQLite database file'
	TIP_SQLITE_DB = '''Choose SQLite database file to
export content from
or to execute commands on'''
	EXECUTE_SQL_FILE = 'Execute SQL file'
	SELECT_SQL_FILE = 'Select SQL file'
	TIP_SQL_FILE = '''SQL file to execute on the given database
(choose "Execute" for SQLite driver or
"Alternative" to ignore commands only available
for server/client implementations)'''
	ALTERNATIVE = 'Alternative method to execute SQL file ignoring commands that do not work with SQLite'
	TABLE = 'Dump table'
	TIP_TABLE = 'Select table of DB to dump'
	COLUMN = 'Dump column'
	TIP_COLUMN = 'Select column of the DB table to dump'
	FIRST_CHOOSE_DB = 'First choose SQLite database file (.db)'

class AxCheckerLabels(BasicLabels):
	CASE_FILE = 'Case File'
	OPEN_CASE_FILE = 'Open case file'
	TIP_CASE_FILE = 'Select Case.mfdb in the AXIOM case directory'
	ROOT = 'Root ID '
	TIP_ROOT = '''Select Source ID of the root structure,
required when task is to compare to a
file structure or a TSV list of file paths'''
	CHECK = 'List files that are not represented in hits/artifacts'
	SELECT_COMP_DIR = 'Select directory to compare content'
	TIP_COMP_DIR = '''Compare filepaths under given directory to
files under given root (by ID) in AXIOM case'''
	TSV_FILE = 'TSV file'
	TIP_COMP_TSV = '''Compate filepaths in given Text/TSV file to
files under given root (by ID) in AXIOM case
(TSV: full path without image or partition name
has to be in the first column, paths should look like:
\\Windows\\System32\\...)'''
	ENCODING = 'Encoding'
	TIP_ENCODING = '''Encoding of TSV file (e.g. cp1252,
leave empty for default = utf-16-le on Win
and utf-8 on other systems)'''
	TSV_NO_HEAD = '''TSV file has no head row
containing row names'''
	TIP_TSV_NO_HEAD = '''Select if given TSV file
has no head line'''
	FIRST_CHOOSE_CASE = 'First choose AXIOM case file (Case.mfdb)'
	SELECT_ROOT = 'Select source root (e.g. partition or directory)'
	CASE_REQUIRED = 'AXIOM case file is required'
	ROOT_ID_REQUIRED = 'AXIOM source ID of root to compare is required'
	ROOT_DIR_REQUIRED = 'Root directory (or drive) to compare with AXIOM case is required'
	TSV_REQUIRED = 'Choose TSV file'

class DismImagerLabels(BasicLabels):
	NAME = 'Name'
	TIP_NAME = 'Image name (stored in WIM-image)'
	DESCRIPTION = 'Description'
	TIP_DESCRIPZION = 'Image description (stored in WIM-image)'
	TIP_COMPRESSION = 'Compression level for dismimg'
	NONE = 'none'
	FAST = 'fast'
	MAX = 'max'
	COPY_EXE = 'Copy WimMount.exe to destination directory'
	TIP_COPY_EXE = '''WimMount.exe is a GUI tool to mount WIM-images.
The executable has to be placed in the bin-subfolder.'''

class WipeLabels(BasicLabels):
	WIPE = 'Wipe'
	TIP_TARGET = 'Target drive to wipe'
	MOUNTPOINT = 'Moint point'
	SELECT_MOUNTPOINT = 'Select mount point'
	TIP_MOUNTPOINT = '''Choose directory to mount new partition
if you want to use it after creation'''
	NORMAL_WIPE = 'Normal wipe'
	ALL_BYTES = 'Wipe all bytes/blocks'
	EXTRA_PASS = 'Extra/2 pass wipe'
	VERIFY = 'Verify'
	BLOCKSIZE = 'Block size'
	TIP_BLOCKSIZE = '''Choose block/page size
to check and wipe at once'''
	PARTITION_TABLE = 'Partition table'
	TIP_PARTITION_TABLE = '''Choose partition table to create a
new partition after wipe (None: do not create)'''
	FILE_SYSTEM = 'File system'
	TIP_FILE_SYSTEM = 'Choose file system for new partition'
	PART_NAME = 'Partiton name'
	DEF_PART_NAME = 'Volume'
	TIP_PART_NAME = 'Name the new partition/volume'
	VALUE = 'Byte to overwrite'
	TIP_VALUE = 'Hex value 00 - ff, (00 is default)'
	MAXBADBLOCKS = 'Max. bad blocks'
	TIP_MAXBADBLOCKS = 'Maximum of bad blocks before abort'
	MAXRETRIES = 'Max. retries'
	TIP_MAXRETRIES = 'Maximum retry attempts while reading/writing'
	LOG_HEAD = 'Head of log file'
	TIP_LOG_HEAD = 'The text will be put on top of the log'
	TARGET_REQUIRED = 'Target (drive/files) is required)'
	SELECT_DRIVE_TO_WIPE = 'Select drive to wipe'
	SELECT_FILES_TO_WIPE = 'Select file(s) to wipe'

'''
	SELECT_IMAGE = 'Select EWF/E01 image (1st file/...e01)'
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
	EXE = 'Executable'
	SELECT_EXE = 'Select executable'
	DO_NOT_CREATE = 'Do not create'
	VOLUME_NAME = 'Volume name'
	DEFAULT_VOLUME_NAME = 'Volume'
	DRIVE_LETTER = 'Drive letter'
	NEXT_AVAILABLE = 'Next available'
	NEED_HEX = 'Byte to overwrite with has to be a hex value'
	BYTE_RANGE = 'Byte to overwrite has to be inbetween 00 and ff'
	NEED_INT = 'An integer value is needed for '
	TARGET_REQUIRED = 'Physical drive or file(s) to wipe required'
	LOGDIR_REQUIRED = 'Target directory for logging required'
	DRIVE_LETTER_IN_USE = 'Drive letter is in use'
	USE_IT_ANYWAY = 'Use it anyway?'
	PATH = 'Path'
	FLAT = 'Flat structure without folders'
	ISO_IMAGE = 'ISO image'
	IMAGE_REQUIRED = 'Image required'
	SELECT_IMAGE = 'Select image file'
	IMAGE_NAME = 'Name'
	IMAGE_DESCRIPTION = 'Description'
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
	WRONG_ENTRY = 'Wrong entry'
	SOURCE_REQUIRED = 'Source is required'
	DEST_DIR_REQUIRED = 'Destination directory is required'
	DEST_FN_REQUIRED = 'Destination filename is required'
	IMAGE_REQUIRED = 'Image file is required'
	MAX = 'Max'
	FAST = 'Fast'
	NONE = 'None'
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
	SQLITE_DB_REQUIRED = 'SQLite database file is required'
	SQL_FILE_REQUIRED = 'SQL file is required'
'''