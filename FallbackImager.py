#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'FallbackImager'
__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-15'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'GUI to generate images with forensics in mind'

from os import name as __os_name__
from sys import executable as __executable__
from pathlib import Path
from tkinter import Tk, END
from tkinter.ttk import Notebook, Frame, LabelFrame, Button
from tkinter.scrolledtext import ScrolledText
from tkinter.messagebox import askquestion, showwarning, showerror
from tkinter.filedialog import askopenfilename, askdirectory
from lib.settings import Settings
from lib.worker import Worker
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
	TEXT_WIDTH = 80
	JOB_HEIGHT = 8
	INFO_HEIGHT = 12

	class ExpandedFrame(Frame):
		'''|<- Frame ->|'''
		def __init__(self, parent):
			super().__init__(parent)
			self.pack(fill='both', padx=Gui.PAD, pady=Gui.PAD, expand=True)

	class ExpandedNotebook(Notebook):
		'''|<- Notebook ->|'''
		def __init__(self, parent):
			super().__init__(parent)
			self.pack(fill='both', padx=Gui.PAD, pady=Gui.PAD, expand=True)

	class ExpandedLabelFrame(LabelFrame):
		'''|<- LabelFrame ->|'''
		def __init__(self, parent, text):
			super().__init__(parent, text=text)
			self.pack(fill='both', padx=Gui.PAD, pady=Gui.PAD, expand=True)

	class ExpandedScrolledText(ScrolledText):
		'''|<- ScrolledText ->|'''
		def __init__(self, parent, height):
			super().__init__(parent,
				padx = Gui.PAD,
				pady = Gui.PAD,
				width = Gui.TEXT_WIDTH,
				height = height
			)
			self.pack(fill='both', padx=Gui.PAD, pady=Gui.PAD, expand=True)

	class LeftButton(Button):
		'''| Button ---|'''
		def __init__(self, parent, text, command):
			super().__init__(parent, text=text, command=command)
			self.pack(padx=Gui.PAD, pady=Gui.PAD, side='left')

	class RightButton(Button):
		'''|--- Button |'''
		def __init__(self, parent, text, command):
			super().__init__(parent, text=text, command=command)
			self.pack(padx=Gui.PAD, pady=Gui.PAD, side='right')

	class OutdirButton(Button):
		'''Button to select destination directory'''
		def __init__(self, parent, settings):
			settings.init_stringvar('outdir')
			super().__init__(parent,
				text = 'Destination:',
				command = lambda: settings.raw('outdir').set(
					askdirectory(
						title = 'Select destination directory',
						mustexist = False
					)
				)
			)
			self.grid(
			row=0, column=0, sticky='w', padx=Gui.PAD, pady=(Gui.PAD, 0))

	class BlacklistButton(Button):
		'''Button to select blacklist'''
		def __init__(self, parent, settings):
			super().__init__(parent,
				text = 'Blacklist:',
				command = lambda: settings.raw('blacklist').set(
					askopenfilename(
						title = 'Select blacklist',
						filetypes = (
							("Text files","*.txt"),
							("All files","*.*")
						)
					)
				)
			)

	class WhitelistButton(Button):
		'''Button to select whitelist'''
		def __init__(self, parent, settings):
			super().__init__(parent,
				text = 'Whitelist:',
				command = lambda: settings.raw('whitelist').set(
					askopenfilename(
						title = 'Select whitelist',
						filetypes = (
							("Text files","*.txt"),
							("All files","*.*")
						)
					)
				)
			)


	def __init__(self):
		self.settings = Settings(__app_parent__/f'{__app_name__.lower()}.json')
		super().__init__()
		self.title(f'{__app_name__} v{__version__}')
		self.resizable(0, 0)
		self.iconbitmap(__app_parent__/'appicon.ico')
		self.notebook = self.ExpandedNotebook(self)
		### OSCDIMAGER ###
		OscdimgGui(self)
		### Jobs ###
		labelframe = self.ExpandedLabelFrame(self, 'Jobs')
		self.jobstext = self.ExpandedScrolledText(labelframe, self.JOB_HEIGHT)
		### INFOS ###
		labelframe = self.ExpandedLabelFrame(self, 'Infos')
		self.infotext = self.ExpandedScrolledText(labelframe, self.INFO_HEIGHT)
		self.infotext.bind('<Key>', lambda e: 'break')
		self.infotext.configure(state='disabled')
		self.infotext.insert(END, 'Infos will be here')
		### START/QUIT FRAME ###
		frame = self.ExpandedFrame(self)
		self.start_button = self.LeftButton(frame, 'Start jobs', self.start_jobs)
		self.quit_button = self.RightButton(frame, 'Quit', self.quit_app)

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
