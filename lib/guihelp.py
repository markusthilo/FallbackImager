#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from threading import Thread
from tkinter import Tk
from tkinter.ttk import Frame, Button
from tkinter.scrolledtext import ScrolledText

class Help(Thread):
	'''Show help window, usually from __description__'''

	def __init__(self, root):
		super().__init__()
		self.root = root

	def run(self):
		window = Tk()
		window.title(self.root.HELP)
		window.iconbitmap(self.root.icon_path)
		text = ScrolledText(window, width=self.root.ENTRY_WIDTH, height=4*self.root.INFO_HEIGHT)
		text.pack(fill='both', expand=True)
		text.bind('<Key>', lambda dummy: 'break')
		text.insert('end', f'{self.root.app_name} v{self.root.version}\n\n')
		for ImagerGui in self.root.IMAGERS:
			text.insert('end', f'{ImagerGui.CMD}:\n{ImagerGui.DESCRIPTION}\n\n')
		text.configure(state='disabled')
		frame = Frame(window)
		frame.pack(fill='both', expand=True)
		Button(frame, text=self.root.QUIT, command=window.destroy).pack(
			padx=self.root.PAD, pady=self.root.PAD, side='right')
		window.mainloop()
