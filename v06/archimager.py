#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'ArchImager'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2025-01-06'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
This is a tool to include into an Arch ISO. The purpose ist to build a bootable ISO image to create
EWF images of the booted device`s drives. Booting and using should not change a single bit on the drives.
'''

from sys import argv
from pathlib import Path
from threading import Thread
from subprocess import Popen
from tkinter import Tk, PhotoImage, StringVar
from tkinter.font import nametofont
from tkinter.ttk import Frame, Notebook
from lib.pathutils import PathUtils
from lib.stringutils import StringUtils
from lib.linutils import LinUtils
from lib.guilabeling import ArchImagerLabels
from lib.guiconfig import GuiConfig
from lib.diskselectgui import DiskSelectGui
from lib.guielements import ExpandedFrame, GridLabel, StringSelector, GridMenu
from lib.guielements import GridSeparator, GridBlank, GridButton, ChildWindow
from lib.guielements import LeftButton, RightButton, DirSelector

class Gui(Tk, ArchImagerLabels, GuiConfig):
	'''Definitions for the GUI'''

	DEFAULT_SEGMENT_SIZE = '40'

	def __init__(self, debug=False):
		'''Build GUI'''
		self.debug = debug
		Tk.__init__(self)
		title = f'{__app_name__} v{__version__}'
		self.title(title)
		self.resizable(0, 0)
		self.appicon = PhotoImage(file=Path(__file__).parent/'appicon.png')
		self.iconphoto(True, self.appicon)
		#self.protocol('WM_DELETE_WINDOW', self._power_off)
		font = nametofont('TkTextFont').actual()
		self.font_family = font['family']
		self.font_size = font['size']
		self.padding = int(self.font_size / GuiConfig.PAD)
		frame = ExpandedFrame(self)
		GridLabel(frame, self.SYSTEM_SETTINGS)
		self.display_settings_button = GridButton(frame, self.DISPLAY, self._display_settings, incrow=False, tip=self.TIP_DISPLAY)
		GridMenu(
			frame,
			StringVar(value=self.DEFAULT_KBD),
			self.KEYBOARD,
			LinUtils.get_xkb_layouts(candidates=self.KBD_CANDIDATES),
			command = self._change_kbd,
			column = 3,
			tip = self.TIP_KEYBOARD
		)
		GridSeparator(frame)
		GridLabel(frame, self.BASIC_METADATA)
		self.case_no = StringSelector(
			frame,
			StringVar(value='CASE NO'),
			self.CASE_NO,
			tip = self.TIP_METADATA
		)
		self.evidence_no = StringSelector(
			frame,
			StringVar(value='EVIDENCE NO'),
			self.EVIDENCE_NO,
			tip = self.TIP_METADATA
		)
		self.examiner_name = StringSelector(
			frame,
			StringVar(value='EXAMINER NAME'),
			self.EXAMINER_NAME,
			tip = self.TIP_METADATA
		)
		GridSeparator(frame)
		GridLabel(frame, self.HARDWARE)
		GridButton(frame, self.SYSTEM_TIME, self._set_realtime, incrow=False, tip=self.TIP_TIME)
		self.system_time = LinUtils.get_system_time()
		self.clock = GridLabel(frame, self.system_time, column=2)
		self.real_time = StringSelector(
			frame,
			StringVar(value=self.system_time),
			self.REAL_TIME,
			command = self._set_realtime,
			tip=self.TIP_TIME
		)
		GridSeparator(frame)
		GridLabel(frame, self.SOURCE)
		self.source = StringSelector(
			frame,
			StringVar(),
			self.SELECT,
			command = self._select_source,
			tip = self.TIP_SOURCE
		)
		self.description = StringSelector(
			frame,
			StringVar(value='DESCRIPTION'),
			self.DESCRIPTION,
			tip = self.TIP_METADATA
		)
		self.notes = StringSelector(
			frame,
			StringVar(value='NOTES'),
			self.NOTES,
			tip = self.TIP_NOTE
		)
		self.segment_size = StringSelector(
			frame,
			StringVar(value=self.DEFAULT_SEGMENT_SIZE),
			self.SEGMENT_SIZE,
			width = GuiConfig.SMALL_FIELD_WIDTH,
			columnspan = 2,
			incrow = False,
			tip=self.TIP_SEGMENT_SIZE
		)
		self.compression = GridMenu(
			frame,
			StringVar(value='fast'),
			self.COMPRESSION,
			('fast', 'best', 'none'),
			column = 3,
			incrow = False,
			tip = self.TIP_COMPRESSION
		)
		self.media_type = GridMenu(
			frame,
			StringVar(value='fixed'),
			self.MEDIA_TYPE,
			('auto', 'fixed', 'removable', 'optical'),
			column = 5,
			incrow = False,
			tip = self.TIP_METADATA
		)
		self.media_flag = GridMenu(
			frame,
			StringVar(value='physical'),
			self.MEDIA_FLAG,
			('auto', 'logical', 'physical'),
			column = 7,
			tip = self.TIP_METADATA
		)
		GridSeparator(frame)
		GridLabel(frame, self.DESTINATION)
		self.initial_outdir = None
		self.outdir = DirSelector(

			frame,
			StringVar(),
			self.DIRECTORY,
			self.SELECT_OUTDIR,
			command = self._select_outdir,
			initialdir = self.initial_outdir,
			tip = self.TIP_OUTDIR
		)
		self.filename = StringSelector(
			frame,
			StringVar(),
			self.FILENAME,
			command = self._set_filename,
			tip = self.TIP_FILENAME
		)

		GridBlank(frame)

	def _power_off(self):
		'''Power off device'''
		pass

	def track(self):
		'''Track time'''
		if not LinUtils.pgrep('arandr'):
			self.display_settings_button.config(state='normal')
		newtime = LinUtils.get_system_time()
		if newtime != self.system_time:
			self.system_time = newtime
		self.clock.config(text=self.system_time)
		self.clock.after(200, self.track)

	def _display_settings(self):
		'''Launch app for display settings'''
		self.display_settings_button.config(state='disabled')
		Popen(['arandr'])

	def _change_kbd(self, kbd_layout):
		'''Change keyboard layout'''
		LinUtils.set_xkb_layout(kbd_layout)

	def _select_outdir(self):
		'''Open and select write destination'''
		askdirectory
		WriteDestinationGui(self, self.outdir)

	def _acquire_hardware(self):
		'''Acquire hardware infos'''
		pass

	def _select_source(self):
		'''Select source to image'''
		DiskSelectGui(self, self.SELECT_SOURCE, self.source._variable,
			physical = True,
			exclude = 'occupied'
		)

	def _set_filename(self):
		if not self.filename.get():
			case_no = self.case_no.get()
			evidence_number = self.evidence_no.get()
			description = self.description.get()
			if case_no and evidence_number and description:
				self.filename.set(f'{case_no}_{evidence_number}_{description}')
			else:
				MissingEntry(self.MISSING_METADATA)

	def _set_realtime(self):
		self.real_time.set(LinUtils.get_system_time())

		'''
    
    frame = ExpandedFrame(self)
    LeftLabel(frame, BasicLabels.AVAILABLE_MODULES)
    RightButton(frame, BasicLabels.HELP, self._show_help)	
    self.notebook = ExpandedNotebook(self)
    self.modules = [(Cli, Gui(self)) for Cli, Gui in modules]
    try:
        self.notebook.select(self.settings.get('ActiveTab', section='Base'))
    except (KeyError, TclError):
        pass
    frame = ExpandedFrame(self)
    LeftLabel(frame, BasicLabels.JOBS)
    RightButton(frame, BasicLabels.REMOVE_LAST, self._remove_last_job,
        tip=BasicLabels.TIP_REMOVE_LAST_JOB)
    self.jobs_text = ExpandedScrolledText(self, GuiConfig.JOB_HEIGHT)
    frame = ExpandedFrame(self)
    LeftLabel(frame, BasicLabels.INFOS)
    RightButton(frame, BasicLabels.CLEAR_INFOS, self._clear_infos,
        tip=BasicLabels.TIP_CLEAR_INFOS)
    self.infos_text = ExpandedScrolledText(self, GuiConfig.INFO_HEIGHT)
    self.infos_text.bind('<Key>', lambda dummy: 'break')
    self.infos_text.configure(state='disabled')
    frame = ExpandedFrame(self)
    self.start_disabled = False
    self.start_button = LeftButton(frame, BasicLabels.START_JOBS, self._start_jobs,
        tip=BasicLabels.TIP_START_JOBS)
    RightButton(frame, BasicLabels.QUIT, self._quit_app)
		'''

if __name__ == '__main__':  # start here
	if len(argv) > 1 and argv[1] in ('-d','--debug'):
		debug = True
		print('DEBUG MODE')
		for dev in LinUtils.get_unoccupied():
			print(dev)
	else:
		debug = False
		for dev in LinUtils.get_unoccupied():	# write protection
			LinUtils.set_ro(dev)
	while True:
		gui = Gui(debug=debug)
		gui.track()
		gui.mainloop()
		if debug:
			exit()
