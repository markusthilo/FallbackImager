#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'FallbackImager'
__author__ = 'Markus Thilo'
__version__ = '0.6.0_2025-04-02'
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
from ewfimager import EwfImager, EwfImagerCli
from lib.ewfimagergui import EwfImagerGui
from ewfchecker import EwfChecker, EwfCheckerCli
from lib.ewfcheckergui import EwfCheckerGui
from hashedcopy import HashedCopy, HashedCopyCli
from lib.hashedcopygui import HashedCopyGui
from zipimager import ZipImager, ZipImagerCli
from lib.zipimagergui import ZipImagerGui
from sqlite import SQLite, SQLiteCli
from lib.sqlitegui import SQLiteGui
from reporter import Reporter, ReporterCli
from lib.reportergui import ReporterGui
from axchecker import AxChecker, AxCheckerCli
from lib.axcheckergui import AxCheckerGui
from wiper import WipeR, WipeRCli
from lib.wipergui import WipeRGui

class Gui(GuiBase):
	'''Define the GUI'''

	CANDIDATES = (
		(EwfImager, EwfImagerCli, EwfImagerGui),
		(EwfChecker, EwfCheckerCli, EwfCheckerGui),
		(HashedCopy, HashedCopyCli, HashedCopyGui),
		(ZipImager, ZipImagerCli, ZipImagerGui),
		(SQLite, SQLiteCli, SQLiteGui),
		(Reporter, ReporterCli, ReporterGui),
		(AxChecker, AxCheckerCli, AxCheckerGui),
		(WipeR, WipeRCli, WipeRGui)
	)

	def __init__(self, config=None, debug=False):
		'''Build GUI'''
		super().__init__(
			__app_name__,
			__version__,
			Path(__file__).parent,
			[(Cli, Gui) for Module, Cli, Gui in self.CANDIDATES if Module().available],
			Settings(config) if config else Settings(Path.home() / '.config/fallbackimager.conf.json'),
			debug = debug
		)

if __name__ == '__main__':  # start here
	argp = ArgumentParser(description=__description__.strip())
	argp.add_argument('-c', '--config', type=Path, help='Config file (default: ~/.config/fallbackimager.conf.json)')
	argp.add_argument('-d', '--debug', default=False, action='store_true', help='Debug mode')
	args = argp.parse_args()
	Gui(debug=args.debug).mainloop()
