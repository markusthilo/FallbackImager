#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-17'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Forensic imager for diverse formats'

from os import name as __os_name__
from sys import executable as __executable__
from pathlib import Path
from lib.guibase import GuiBase
from oscdimager import OscdimgCli, OscdimgGui
from pycdlibimager import PyCdlibCli, PyCdlibGui

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
if __os_name__ == 'nt':
	from win32com.shell.shell import IsUserAnAdmin
	__admin__ = IsUserAnAdmin()

class Gui(GuiBase):
	'''GUI'''

	IMAGERS = {OscdimgGui: OscdimgCli, PyCdlibGui: PyCdlibCli}
	PAD = 4
	JOB_HEIGHT = 4
	INFO_HEIGHT = 8
	ENTRY_WIDTH = 128
	DESCRIPTION = 'Imager for different formats as a fallback when the usual tools do not work'
	HELP = 'Help'
	JOBS = 'Jobs'
	REMOVE_LAST = 'Remove last'
	INFOS = 'Infos'
	CLEAR_INFOS = 'Clear infos'
	START_JOBS = 'Start jobs'
	RUNNING = 'Running...'
	QUIT = 'Quit'
	SOURCE = 'Source'
	DIRECTORY = 'Directory'
	SELECT_ROOT = 'Select source root directory'
	DESTINATION = 'Destination'
	FILENAME = 'Filename'
	SELECT_FILENAME = 'Select file to use name', 
	OUTDIR = 'Outdir'
	SELECT_DEST_DIR = 'Select destination directory'
	SKIP_PATH_CHECK = 'Skip check of paths by blacklist or whitelist'
	PATHFILTER = 'Pathfilter'
	CHECK_ALL_PATHS = 'Check if all source paths are in image'
	BLACKLIST = 'Blacklist'
	SELECT_BLACKLIST = 'Select blacklist'
	WHITELIST = 'Whitelist'
	SELECT_WHITELIST = 'Select whitelist'
	ADD_JOB = 'Add job'
	RUNNING = 'Running'
	NOTHING2DO = 'Add jobs! Nothing to do here.\n'
	ALL_DONE = 'All done.\n'
	UNDETECTED = 'Could not detect what to do.\n'

	def __init__(self):
		'''Buld GUI'''
		super().__init__(__app_name__, __version__, __icon_path__, __settings_path__)

if __name__ == '__main__':  # start here
	Gui().mainloop()
