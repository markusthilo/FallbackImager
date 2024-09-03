#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from threading import Thread
from tkinter import Tk, PhotoImage, StringVar, BooleanVar
from tkinter.messagebox import askyesno, showerror
from .linutils import LinUtils
from .guielements import ExpandedFrame, GridSeparator, StringSelector, GridLabel
from .guielements import Checker, LeftButton, RightButton, LeftLabel, ChildWindow
from .guielements import GridScrolledText, GridFrame, GridButton
from .diskselectgui import DiskSelectGui
from .guilabeling import SettingsLabels

class SettingsFrame(ExpandedFrame):
	'''Notebook tab'''

	def __init__(self, root):
		'''Settings Notebook for Linux'''
		super().__init__(root.notebook)
		root.notebook.add(self, text=SettingsLabels.SETTINGS)
		GridSeparator(self)
		self.row = 1
		if not LinUtils.i_am_root():
			GridLabel(self, SettingsLabels.SUDO)
			self.sudo = StringSelector(
			self,
			StringVar(),
			SettingsLabels.PASSWORD,
			show='*',
			command = self._become_root,
			tip = SettingsLabels.TIP_SUDO
		)
			GridSeparator(self)
		GridButton(self, SettingsLabels.WRITE_PROTECTION, self._launch_dev_win,
			tip=SettingsLabels.TIP_SET_NEW_RO)
		#GridLabel(self, SettingsLabels.WRITE_PROTECTION)
		#self._ro = Checker(
		#	self,
		#	BooleanVar(),
		#	SettingsLabels.SET_NEW_RO,
		#	command = self._change_rorw,
		#	tip = SettingsLabels.TIP_SET_NEW_RO,
		#	columnspan = 3
		#)
		self.root = root

	def _become_root(self):
		'''Executet to use root privileges'''
		print('DEBUG:', self.sudo.get())

	def _launch_dev_win(self):
		'''Launch new window for RO/RW control'''
		thread = Thread(target=self._run_dev_win)
		thread.start()

	def _run_dev_win(self):
		'''Run Tk mainloop'''
		BlockDevGui(self.root).mainloop()

class BlockDevGui(DiskSelectGui, Tk):
	'''Define GUI for block device monitor'''

	def __init__(self, root):
		'''Build GUI'''
		Tk.__init__(self)
		self.title('''DEBUG''')
		self.resizable(0, 0)
		#self.iconphoto(True, root.appicon)
		#self.protocol('WM_DELETE_WINDOW', root._quit_app)

		self.button = None
		self.physical = False
		self.exclude = None
		
		print(root.__dict__)

		#self._main_frame()


	def blockdevs(self):
		'''Handle blockdevs'''
		old_disks = self._disks
		self._disks = set(LinUtils.get_disks())
		new_disks = self._disks - old_disks
		for disk in new_disks:
			print('DEBUG', disk)
		self.root.after(100, self._blockdevs())

class BlockDevWindow(Thread, Tk):
	'''Window to set new block devices to ro'''

	def __init__(self, root):
		'''Pass attributes from root window'''
		self.root = root

	def run(self):
		'''Run thread'''
		BlockDevGui(self.root).mainloop()
