#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'FallbackImager'
__author__ = 'Markus Thilo'
__version__ = '0.5.1_2024-05-25'
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

from pathlib import Path
from sys import executable as __executable__
from os import name as __os_name__
from argparse import ArgumentParser
from lib.settings import Settings
from lib.guibase import GuiBase
from zipimager import ZipImager, ZipImagerCli
from lib.zipimagergui import ZipImagerGui
from axchecker import AxChecker, AxCheckerCli
from lib.axcheckergui import AxCheckerGui
from sqlite import SQLite, SQLiteCli
from lib.sqlitegui import SQLiteGui
from reporter import Reporter, ReporterCli
from lib.reportergui import ReporterGui
from hashedcopy import HashedCopy, HashedCopyCli
from lib.hashedcopygui import HashedCopyGui
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
	'''Definitions for the GUI'''

	def __init__(self, debug=False):
		'''Build GUI'''
		not_admin = False
		if __os_name__ == 'nt':
			if not IsUserAnAdmin():
				not_admin = True
			candidates = (
				(OscdImager, OscdImagerCli, OscdImagerGui),
				(DismImager, DismImagerCli, DismImagerGui),
				(ZipImager, ZipImagerCli, ZipImagerGui),
				(HashedCopy, HashedCopyCli, HashedCopyGui),
				(SQLite, SQLiteCli, SQLiteGui),
				(Reporter, ReporterCli, ReporterGui),
				(AxChecker, AxCheckerCli, AxCheckerGui),
			#	(WipeW, WipeWCli, WipeWGui)
			)
		else:
			candidates = (
				(EwfImager, EwfImagerCli, EwfImagerGui),
				(EwfChecker, EwfCheckerCli, EwfCheckerGui),
				(ZipImager, ZipImagerCli, ZipImagerGui),
				(HashedCopy, HashedCopyCli, HashedCopyGui),
				(SQLite, SQLiteCli, SQLiteGui),
				(Reporter, ReporterCli, ReporterGui),
				(AxChecker, AxCheckerCli, AxCheckerGui),
				(WipeR, WipeRCli, WipeRGui)
			)
		super().__init__(__app_name__,__version__, __parent_path__,
			[(Cli, Gui) for Module, Cli, Gui in candidates if Module().available],
			Settings(__parent_path__/'fisettings.json'),
			not_admin = not_admin,
			debug = debug
		)

if __name__ == '__main__':  # start here
	argp = ArgumentParser(description=__description__.strip())
	argp.add_argument('-d', '--debug', default=False, action='store_true', help='Debug mode')
	args = argp.parse_args()
	Gui(debug=args.debug).mainloop()
