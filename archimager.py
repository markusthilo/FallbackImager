#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'ArchImager'
__author__ = 'Markus Thilo'
__version__ = '0.5.2_2024-06-17'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Arch ISO to image (EWF) booted device
'''

from pathlib import Path
from tkinter import Tk, PhotoImage
from lib.linutils import LinUtils


class Gui(Tk):
    '''Definitions for the GUI'''
    super().__init__()
    #self.title(f'{__app_name__} {__version__}')
    #self.area_x, self.area_y = LinUtils.get_workarea()
    #self.geometry(f'{self.area_x}x{self.area_y}')
    #self.resizable(0, 0)
    #self.appicon = PhotoImage(file='/opt/ArchImager/appicon.png')
    #self.iconphoto(True, self.appicon)


    '''
    self.protocol('WM_DELETE_WINDOW', self._quit_app)
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
