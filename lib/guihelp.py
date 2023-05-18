#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-18'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Show help window'

from threading import Thread
from tkinter import Tk
from tkinter.scrolledtext import ScrolledText

class Help(Thread):
	'''Show help window, usually from __description__'''

	def __init__(self, root):
		super().__init__()
		window = Tk()
		window.title(root.HELP)
		window.iconbitmap(root.icon_path)
		text = ScrolledText(window, width=root.ENTRY_WIDTH, height=4*root.INFO_HEIGHT)
		text.pack(fill='both', expand=True)
		text.bind('<Key>', lambda dummy: 'break')
		text.insert('end', f'{root.app_name} v{root.version}\n\n')
		for ImagerGui in root.IMAGERS:
			text.insert('end', f'{ImagerGui.CMD}:\n{ImagerGui.DESCRIPTION}\n\n')
		text.configure(state='disabled')

	def run(self):
		self.window.mainloop()
