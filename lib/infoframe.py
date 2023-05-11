#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-10'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Info TTk LabelFrame'

from tkinter import END
from tkinter.ttk import Frame, LabelFrame, Label, Button
from tkinter.scrolledtext import ScrolledText

class InfoFrame:
	'''Info frame for TTk using ScrolledText'''

	def __init__(self, parent):
		'''Plug into TTk app'''
		labelframe = LabelFrame(parent, text='Infos')
		labelframe.pack(fill='both', padx=self.PAD, pady=self.PAD, expand=True)
		self.text = ScrolledText(labelframe,
			padx = self.PAD,
			pady = self.PAD,
			width = self.T_WIDTH,
			height = self.T_HEIGHT
		)
		self.text.bind("<Key>", lambda e: "break")
		self.text.insert(END, 'Infos will be here')
		self.text.pack(fill='both', padx=self.PAD, pady=self.PAD, side='left')

	def append_info(self, msg):
		'''Append message in info box'''
		self.text.configure(state='normal')
		self.text.insert(END, f'{msg}\n')
		self.text.configure(state='disabled')
		self.text.yview(END)