#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'FallbackImager'
__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-16'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Forensic imager for diverse formats'

from os import name as __os_name__
from sys import executable as __executable__
from pathlib import Path
from tkinter import Tk
from tkinter.messagebox import askquestion, showwarning, showerror
from lib.settings import Settings
from lib.worker import Worker
from lib.guielements import ExpandedNotebook, ExpandedLabelFrame, ExpandedFrame
from lib.guielements import ExpandedScrolledText, LeftButton, RightButton, LeftLabel
from lib.oscdimg_gui import OscdimgGui

__executable__ = Path(__executable__)
if __executable__.stem.lower() == __app_name__.lower():
	__app_parent__ = __executable__.parent
else:
	__app_parent__ = Path(__file__).parent
if __os_name__ == 'nt':
	from win32com.shell.shell import IsUserAnAdmin
	__admin__ = IsUserAnAdmin()

class Gui(Tk):
	'''GUI look and feel'''

	PAD = 4
	JOB_HEIGHT = 4
	INFO_HEIGHT = 8
	ENTRY_WIDTH = 128

	def __init__(self):
		self.settings = Settings(__app_parent__/f'{__app_name__.lower()}.json')
		super().__init__()
		self.title(f'{__app_name__} v{__version__}')
		self.resizable(0, 0)
		self.iconbitmap(__app_parent__/'appicon.ico')
		self.notebook = ExpandedNotebook(self)
		### OSCDIMAGER ###
		OscdimgGui(self)
		### Jobs ###
		frame = ExpandedFrame(self, self)
		LeftLabel(self, frame, 'Jobs')
		self.rm_last_job_button = RightButton(self, frame, 'Remove last', self.remove_last)
		self.jobstext = ExpandedScrolledText(self, self, self.JOB_HEIGHT)

		### INFOS ###
		frame = ExpandedFrame(self, self)
		LeftLabel(self, frame, 'Info')
		self.clear_info_button = RightButton(self, frame, 'Clear infos', self.clear_infos)
		self.infotext = ExpandedScrolledText(self, self, self.INFO_HEIGHT)
		self.infotext.bind('<Key>', lambda e: 'break')
		self.infotext.configure(state='disabled')
		self.infotext.insert('end', 'Infos will be here')
		### START/QUIT FRAME ###
		frame = ExpandedFrame(self, self)
		self.start_button = LeftButton(self, frame, 'Start jobs', self.start_jobs)
		self.quit_button = RightButton(self, frame, 'Quit', self.quit_app)

	def remove_last(self):
		pass

	def clear_infos(self):
		pass

	def append_info(self, msg):
		'''Append message in info box'''
		self.text.configure(state='normal')
		self.text.insert(END, f'{msg}\n')
		self.text.configure(state='disabled')
		self.text.yview(END)

	def start_jobs(self):
		'''Start working job list'''
		print('Starting jobs...')
		self.jobs.configure(state='disabled')
		work = Worker(
			(job.split() for job in self.jobs.get('1.0', END).split('\n') if job != ''),
			debug = True
		)
		work.run()

	def	quit_app(self):
		'''Store configuration and quit application'''
		self.settings.write()
		self.destroy()

if __name__ == '__main__':  # start here
	Gui().mainloop()
