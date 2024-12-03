#!/usr/bin/env python3
# -*- coding: utf-8 -*-

### Labels, Tooltips and Errors ###
### English ###

class BasicLabels:
	AVAILABLE_MODULES = 'Available modules:'
	FATAL_ERROR = 'Fatal error'
	MODULE_ERROR = 'Unable to load any module'
	ERROR = 'Error'
	ERRORS = 'error(s)'
	HELP = 'Help'
	HELP_ERROR = 'Error: Unable to read help.txt'
	JOBS = 'Jobs'
	ADD_JOB = 'Add job'
	TIP_ADD_JOB = 'Add job as configured above to job queue'
	SELECT = 'Select'
	QUIT = 'Quit'
	STOP_WORK = 'Stop work'
	JOB_RUNNING = 'Job is running!'
	ARE_YOU_SURE = 'Are you sure?'
	REMOVE_LAST = 'Remove last'
	TIP_REMOVE_LAST_JOB = 'Remove last job from the job queue'
	START_JOBS = 'Start jobs'
	TIP_START_JOBS = 'Start job after job in queue'
	INFOS = 'Infos'
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
	SELECT_FILE = 'Select file'
	FILES = 'files'
	SELECT_FILES = 'file(s)'
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
	DESCRIPTION = 'Description'
	LOGGING = 'Logging'
	CONFIGURATION = 'Configuration'
	SETTINGS = 'Settings'
	COMPRESSION = 'Compression'
	REFRESH = 'Refresh'
	AUTO = 'auto'
	MISSING_ENTRY = 'Missing entry'
	ARE_YOU_ROOT = 'Are you root?'
	NOT_ADMIN = 'No admin privileges'
	YES = 'Yes'
	NO = 'No'

class SettingsLabels(BasicLabels):
	SUDO = 'Get admin privileges'
	SET_PASSWORD = 'Set sudo password'
	TIP_SUDO = 'Press when password for sudo is set'
	WRITE_PROTECTION = 'Block device write protection'
	OPEN_CONFIG_WINDOW = 'Open config window'
	TIP_CONFIG_WINDOW = '''Open a window to enable and disable
write protection for block devices'''
	SET_NEW_RO = 'Set new attached block devices to read only'
	TIP_SET_NEW_RO = '''When checked, all newly attached block devices
will be set to read only while running this app
(sudo blockdev --setro /dev/...)'''

class EwfImagerLabels(BasicLabels):
	TIP_SOURCE = 'Select source to image as EWF/E01'
	SETRO = 'Set device to read only'
	TIP_SETRO = '''Execute "blockdev --setro /dev/..."
to make sure, source stays untouched'''
	TIP_IMAGE_LOGS = 'Destination directory to write image and logs'
	CASE_NO = 'Case number'
	TIP_METADATA = 'Metadata stored in the EWF/E01 image'
	EVIDENCE_NO = 'Evidence number'
	DEF_EVIDENCE_NO = 'EAV'
	DEF_DESCRIPTION = 'HD'
	EXAMINER_NAME = 'Examiner name'
	NOTES = 'Notes'
	TIP_NOTE = 'Select this line to put in the image metadata'
	SEGMENT_SIZE = 'Segment size'
	TIP_SEGMENT_SIZE = '''Segment size of EWF/E01 image in
MiB, GiB or source size / n
(e.g. 512m, 4g, 40)'''
	DEF_SIZE = '40'
	TIP_COMPRESSION = 'Compression level of the EWF/E01 image'
	MEDIA_TYPE = 'Media type'
	MEDIA_FLAG = 'Media flag'
	UNABLE_ACCESS = 'Unable to access'
	MISSING_METADATA = 'Case number, evidence number and description are required to generate filename'
	METADATA_REQUIRED = 'Case number, evidence number and description are required as metadata for the EWF/E01 image'
	UNDECODEABLE_SEGMENT_SIZE = 'Undecodable segment size'
	SELECT_TARGET = 'Select target'

class OscdImagerLabels(BasicLabels):
	TIP_SOURCE = 'Select source root to build ISO image file from'

class DismImagerLabels(BasicLabels):
	TIP_SOURCE = 'Select source root to build WIM image file from'
	NAME = 'Name'
	TIP_NAME = 'Image name (stored in WIM-image)'
	TIP_DESCRIPTION = 'Image description (stored in WIM image)'
	TIP_COMPRESSION = 'Compression level for dismimg'
	COPY_EXE = 'Copy WimMount.exe to destination directory'
	TIP_COPY_EXE = '''WimMount.exe is a GUI tool to mount WIM-images.
The executable has to be placed in the bin-subfolder.'''
	IMAGE_OF = 'Image of'

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
	DUMP_SCHEMA = 'Dump database schema'
	DUMP_CONTENT = 'Dump content - all or select table/column'
	TABLE = 'Dump table'
	TIP_TABLE = '''Select table of DB to dump
(leave empty to dump all)'''
	COLUMN = 'Dump column'
	TIP_COLUMN = '''Select column of the DB table to dump
(leave empty to dump all)'''
	FIRST_CHOOSE_DB = 'First choose SQLite database file (.db)'
	SCHEMA = 'Schema'
	SQL_FILE_REQUIRED = 'File with SQL statements is required'

class ReporterLabels(BasicLabels):
	TEMPLATE = 'Template'
	SELECT_TEMPLATE = 'Select template text file to parse'
	TIP_TEMPLATE = 'Select tamplate to parse by JSON file'
	JSON = 'JSON file'
	SELECT_JSON = 'Select JSON file'
	TIP_JSON = 'JSON file to parse by template file'
	PARSE = 'Parse'
	TEMPLATE_REQUIRED = 'Template to parse is required'
	JSON_REQUIRED = 'JSON file is required'
	PREVIEW = 'Preview'
	PARSER_REPORTED = 'Parser reported'
	WRITE_TO_FILE = 'Write to file'

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

class WipeLabels(BasicLabels):
	WIPE = 'Wipe'
	TIP_TARGET = '''Target drive to wipe - Warning:
data will be irretrievably erased!'''
	TARGET_WARNING = 'WARNING: DATA WILL BE ERASED!'
	MOUNTPOINT = 'Moint point'
	SELECT_MOUNTPOINT = 'Select mount point'
	TIP_MOUNTPOINT = '''Choose directory to mount new partition
if you want to use it after creation'''
	NEW_PARTITION = 'New partition'
	ASSIGN_DRIVE_LETTER = 'Assign drive letter'
	NEXT_AVAILABLE = 'Next available'
	TIP_NEW_DRIVE_LETTER = '''Choose drive letter to assign
new partition to after wipe process'''
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

class ArchImagerLabels(EwfImagerLabels):
	SYSTEM_SETTINGS = 'System settings'
	DISPLAY = 'Display'
	TIP_DISPLAY = 'Configure display'
	KEYBOARD = 'Keyboard layout'
	KBD_CANDIDATES = ('de', 'es', 'fr', 'gb', 'us')
	DEFAULT_KBD = 'de'
	TIP_KEYBOARD = 'Choose keyboard layout'
	SYSTEM_TIME = 'System time'
	REAL_TIME = 'Real world time'
	TIP_TIME = '''The real world time will be written to the
hardware file when the system info acquirement is startet
(unrestricted format, notes/comments are possible)'''
	ACQUIRE_HARDWARE = 'Acquire hardware'
	TIP_ACQUIRE_HARDWARE = 'Acquire hardware information including hardware/mother board time'
	BASIC_METADATA = 'Basic metadata'
	HARDWARE = 'Hardware'