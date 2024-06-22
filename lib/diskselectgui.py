#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .guilabeling import BasicLabels, ArchImagerLabels
from .guiconfig import GuiConfig
from .guielements import ChildWindow, ExpandedFrame, Tree, LeftButton, RightButton
from .linutils import LinUtils
from .stringutils import StringUtils

class DiskSelectGui(ChildWindow, BasicLabels):
	'''GUI to select disk (Linux)'''

	def __init__(self, root, title, select, physical=False, exclude=None):
		'''Window to select disk'''
		try:
			if root.child_win_active:
				return
		except AttributeError:
			pass
		self.root = root
		self._select = select
		self.physical = physical
		self.exclude = exclude
		self.root.child_win_active = True
		ChildWindow.__init__(self, self.root, title)
		self._main_frame()

	def _main_frame(self):
		'''Main frame'''
		self.main_frame = ExpandedFrame(self)
		self.lsblk(self.main_frame)
		frame = ExpandedFrame(self.main_frame)
		LeftButton(frame, self.REFRESH, self._refresh)
		frame = ExpandedFrame(self.main_frame)
		LeftButton(frame, self.SELECT, self._done)
		RightButton(frame, self.QUIT, self.destroy)

	def lsblk(self, root):
		'''Frame with of lsblk tree'''
		frame = ExpandedFrame(root)
		blkdevs = LinUtils.lsblk(physical=self.physical, exclude=self.exclude)
		self.tree = Tree(frame,
			text='name',
			width=GuiConfig.LSBLK_NAME_WIDTH,
			columns=GuiConfig.LSBLK_COLUMNS_WIDTH
		)
		for path, details in LinUtils.lsblk(physical=self.physical, exclude=self.exclude).items():
			values = (
				details['type'],
				details['size'],
				StringUtils.str(details['label']),
				StringUtils.str(details['vendor']),
				StringUtils.str(details['model']),
				StringUtils.join(details['mountpoints'], delimiter=', ')
			)
			self.tree.insert(details['parent'], 'end', text=path, values=values, iid=path, open=True)

	def _refresh(self):
		'''Destroy and reopen Target Window'''
		self.main_frame.destroy()
		self._main_frame()

	def _done(self):
		'''Set variable and quit'''
		self._select.set(self.tree.focus())
		self.destroy()

class WriteDestinationGui(ChildWindow, ArchImagerLabels):
	'''GUI to select disk to write(Linux)'''

	def __init__(self, root, select):
		'''Window to select disk'''
		try:
			if root.child_win_active:
				return
		except AttributeError:
			pass
		self.root = root
		self._select = select
		self.root.child_win_active = True
		ChildWindow.__init__(self, self.root, self.SELECT_TARGET)
		self._main_frame()
		
	def _main_frame(self):
		'''Main frame'''
		blkdevs = LinUtils.lsblk(physical=self.physical, exclude=self.exclude)
		self.main_frame = ExpandedFrame(self)
		frame = ExpandedFrame(self.main_frame)
		self.tree = Tree(frame,
			text = 'name',
			width = GuiConfig.LSBLK_NAME_WIDTH,
			columns = GuiConfig.LSBLK_COLUMNS_WIDTH
		)
		for path, details in blkdevs.items():
			values = (
				details['type'],
				details['size'],
				StringUtils.str(details['label']),
				StringUtils.str(details['vendor']),
				StringUtils.str(details['model']),
				StringUtils.str(details['rev']),
				StringUtils.join(details['mountpoints'], delimiter=', ')
			)
			self.tree.insert(details['parent'], 'end', text=path, values=values, iid=path, open=True)
		frame = ExpandedFrame(self.main_frame)
		LeftButton(frame, self.REFRESH, self._refresh)
		frame = ExpandedFrame(self.main_frame)
		LeftButton(frame, self.SELECT, self._done)
		RightButton(frame, self.QUIT, self.destroy)

	def _refresh(self):
		'''Destroy and reopen Target Window'''
		self.main_frame.destroy()
		self._main_frame()

	def _done(self):
		'''Set variable and quit'''
		self._select.set(self.tree.focus())
		self.destroy()
