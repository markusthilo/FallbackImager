#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'ArchImager'
__author__ = 'Markus Thilo'
__version__ = '0.5.3_2024-06-18'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Arch ISO to image (EWF) booted device
'''

from pathlib import Path
from tkinter import Tk, PhotoImage, StringVar
from lib.linutils import LinUtils
from lib.guilabeling import EwfImagerLabels
from lib.diskselectgui import DiskSelectGui
from lib.guielements import ExpandedFrame, GridLabel, StringSelector


class Gui(Tk, EwfImagerLabels):
	'''Definitions for the GUI'''

	PAD = 16

	def __init__(self):
		'''Build GUI'''
		Tk.__init__(self)
		self.title(f'{__app_name__} {__version__}')
		self.area_x, self.area_y = LinUtils.get_workarea()
		self.size_x = min(self.area_x-2*self.PAD, 1920-2*self.PAD)
		self.size_y = min(self.area_y-2*self.PAD, 1080-2*self.PAD)
		self.geometry(f'{self.size_x}x{self.size_y}')
		self.resizable(0, 0)
		self.appicon = PhotoImage(file='appicon.png')
		self.iconphoto(True, self.appicon)
		#self.protocol('WM_DELETE_WINDOW', self._quit_app)
		frame = ExpandedFrame(self)
		GridLabel(frame, self.SOURCE)
		self.source_var = StringVar()
		self.source_sel = StringSelector(
			frame,
			self.source_var,
			self.SELECT,
			command = self._select_source,
			tip = self.TIP_SOURCE
		)
		GridLabel(frame, self.SETTINGS)
		self.case_no_var = StringVar(value='CASE NO')
		self.case_no_sel = StringSelector(
			frame,
			self.case_no_var,
			self.CASE_NO,
			tip = self.TIP_METADATA
		)
		self.evidence_no_var = StringVar(value='EVIDENCE NO')
		self.evidence_no_sel = StringSelector(
			frame,
			self.evidence_no_var,
			self.EVIDENCE_NO,
			tip = self.TIP_METADATA
		)
		self.description_var = StringVar(value='DESCRIPTION')
		self.description_sel = StringSelector(
			frame,
			self.description_var,
			self.DESCRIPTION,
			tip = self.TIP_METADATA
		)
		self.examiner_name_var = StringVar(value='EXAMINER NAME')
		self.examiner_name = StringSelector(
			frame,
			self.examiner_name_var,
			self.EXAMINER_NAME,
			tip = self.TIP_METADATA
		)

	def _select_source(self):
		'''Select source to image'''
		DiskSelectGui(self, self.source_var, physical=True)

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
	Gui().mainloop()
