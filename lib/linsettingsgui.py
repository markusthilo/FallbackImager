#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from threading import Thread
from tkinter import Tk, PhotoImage, StringVar, BooleanVar
from tkinter.messagebox import askyesno
from .linutils import LinUtils
from .guielements import ExpandedFrame, GridSeparator, StringSelector, GridLabel
from .guielements import Checker, LeftButton, RightButton, LeftLabel, ChildWindow
from .guielements import GridScrolledText, GridFrame, GridButton, Error
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
		if LinUtils.i_am_root():
			self.sudo = None
		else:
			GridLabel(self, SettingsLabels.SUDO)
			self.sudo = StringSelector(
				self,
				StringVar(),
				SettingsLabels.SET_PASSWORD,
				show='*',
				command = self._become_root,
				tip = SettingsLabels.TIP_SUDO
			)
			GridSeparator(self)
		GridLabel(self, SettingsLabels.WRITE_PROTECTION)
		self.open_config_button = GridButton(self, SettingsLabels.OPEN_CONFIG_WINDOW, self._launch_dev_win,
			tip=SettingsLabels.TIP_CONFIG_WINDOW)
		#if not LinUtils.i_am_root():
		#	self.open_config_button.config(state='disabled')	### DEBUG ####
		root.linutils = LinUtils()
		self.root = root

	def _become_root(self):
		'''Executet to use root privileges'''
		self.root.linutils = LinUtils(password=self.sudo.get())
		if self.root.linutils.i_have_root():
			self.sudo.config(state='disabled')
			self.open_config_button.config(state='normal')
		else:
			self.sudo.set('')
			Error(SettingsLabels.NOT_ADMIN)
		
	def _launch_dev_win(self):
		'''Launch new window for RO/RW control'''
		thread = Thread(target=self._run_dev_win)
		thread.start()

	def _run_dev_win(self):
		'''Run Tk mainloop'''
		BlockDevWindow(self.root, self.open_config_button).mainloop()

class BlockDevWindow(Tk):
	'''Define GUI for block device monitor'''

	def __init__(self, root, open_config_button):
		'''Build Window to observe block devices and set rw/ro'''
		Tk.__init__(self)
		open_config_button.config(state='disabled')
		self.title(SettingsLabels.BLOCKDEVS)
		self.resizable(0, 0)
		#self.iconphoto(True, root.appicon) ### does not work, no idea why!

		#GridLabel(self, SettingsLabels.WRITE_PROTECTION)
		#self._ro = Checker(
		#	self,
		#	BooleanVar(),
		#	SettingsLabels.SET_NEW_RO,
		#	command = self._change_rorw,
		#	tip = SettingsLabels.TIP_SET_NEW_RO,
		#	columnspan = 3
		#)

		self.button = None
		self.physical = False
		self.exclude = None

		#print(f'DEBUG: >{stdout}<, >{stderr}<')

		#self._main_frame()


	def blockdevs(self):
		'''Handle blockdevs'''
		old_disks = self._disks
		self._disks = set(LinUtils.get_disks())
		new_disks = self._disks - old_disks
		for disk in new_disks:
			print('DEBUG', disk)
		self.root.after(100, self._blockdevs())
