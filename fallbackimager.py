#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'FallbackImager'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2024-12-29'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This is a modular utility for forensic work as a complement
or fallback to the commercial and/or established tools.
The modules write log files into given output directory,
calculate hashes and/or lists of copied files etc.
Multiple jobs can be generated and executed sequentially.
This is the GUI but I would recommand the CLI tools that
are provided alongside. This is work in progress.
'''

from os import name as __os_name__
from pathlib import Path
from argparse import ArgumentParser
from lib.settings import Settings
from lib.guibase import GuiBase
__candidates__ = list()
try:
	from ewfimager import EwfImager, EwfImagerCli
	from lib.ewfimagergui import EwfImagerGui
	__candidates__.append((EwfImager, EwfImagerCli, EwfImagerGui))
except Exception as ex:
	print(f'EwfImager: {ex}')
try:
	from ewfchecker import EwfChecker, EwfCheckerCli
	from lib.ewfcheckergui import EwfCheckerGui
	__candidates__.append((EwfChecker, EwfCheckerCli, EwfCheckerGui))
except Exception as ex:
	print(f'EwfChecker: {ex}')
try:
	from oscdimager import OscdImager, OscdImagerCli
	from lib.oscdimagergui import OscdImagerGui
	__candidates__.append((OscdImager, OscdImagerCli, OscdImagerGui))
except Exception as ex:
	print(f'OscdImager: {ex}')
try:
	from dismimager import DismImager, DismImagerCli
	from lib.dismimagergui import DismImagerGui
	__candidates__.append((DismImager, DismImagerCli, DismImagerGui))
except Exception as ex:
	print(f'DismImager: {ex}')
try:
	from zipimager import ZipImager, ZipImagerCli
	from lib.zipimagergui import ZipImagerGui
	__candidates__.append((ZipImager, ZipImagerCli, ZipImagerGui))
except Exception as ex:
	print(f'ZipImager: {ex}')
try:
	from hashedcopy import HashedCopy, HashedCopyCli
	from lib.hashedcopygui import HashedCopyGui
	__candidates__.append((HashedCopy, HashedCopyCli, HashedCopyGui))
except Exception as ex:
	print(f'HashedCopy: {ex}')
try:
	from sqlite import SQLite, SQLiteCli
	from lib.sqlitegui import SQLiteGui
	__candidates__.append((SQLite, SQLiteCli, SQLiteGui))
except Exception as ex:
	print(f'SQLite: {ex}')
try:
	from reporter import Reporter, ReporterCli
	from lib.reportergui import ReporterGui
	__candidates__.append((Reporter, ReporterCli, ReporterGui))
except Exception as ex:
	print(f'Reporter: {ex}')
try:
	from axchecker import AxChecker, AxCheckerCli
	from lib.axcheckergui import AxCheckerGui
	__candidates__.append((AxChecker, AxCheckerCli, AxCheckerGui))
except Exception as ex:
	print(f'AxChecker: {ex}')
try:
	from wiper import WipeR, WipeRCli
	from lib.wipergui import WipeRGui
	__candidates__.append((WipeR, WipeRCli, WipeRGui))
except Exception as ex:
	print(f'WipeR: {ex}')	
try:
	from wipew import WipeW, WipeWCli
	from lib.wipewgui import WipeWGui
	__candidates__.append((WipeW, WipeWCli, WipeWGui))
except Exception as ex:
	print(f'WipeW: {ex}')
if __os_name__ == 'posix':
	__parent_path__ = Path(__file__).parent
	__def_conf_path__ = Path.home() / '.config/fallbackimager.conf.json'
else:
	from sys import executable as __exe__
	__exe_path__ = Path(__exe__)
	__parent_path__ = Path(__file__).parent if __exe_path__.name == 'python.exe' else __exe_path__.parent
	__def_conf_path__ = __parent_path__ / 'config.json'

class Gui(GuiBase):
	'''Define the GUI'''

	def __init__(self, config=None, debug=False):
		'''Build GUI'''
		super().__init__(
			__app_name__,
			__version__,
			__parent_path__,
			[(Cli, Gui) for Module, Cli, Gui in __candidates__ if Module().available],
			Settings(config) if config else Settings(__def_conf_path__ ),
			debug = debug
		)

if __name__ == '__main__':  # start here
	argp = ArgumentParser(description=__description__.strip())
	argp.add_argument('-c', '--config', type=Path, help='Config file (default: ~/.config/fallbackimager.conf.json)')
	argp.add_argument('-d', '--debug', default=False, action='store_true', help='Debug mode')
	args = argp.parse_args()
	Gui(debug=args.debug).mainloop()
