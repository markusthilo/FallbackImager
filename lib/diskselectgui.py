#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .guilabeling import EwfImagerLabels
from .guiconfig import GuiConfig
from .guielements import ChildWindow, ExpandedFrame, Tree, LeftButton, RightButton
from .linutils import LinUtils
from .stringutils import StringUtils

class DiskSelectGui(ChildWindow, EwfImagerLabels):
	'''GUI to select disk (Linux)'''

	def __init__(self, root, select, physical=False, exclude=None):
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
		ChildWindow.__init__(self, self.root, self.SELECT_SOURCE)
		self._main_frame()
		
	def _main_frame(self):
		'''Main frame'''
		blkdevs = LinUtils.lsblk(physical=self.physical, exclude=self.exclude)
		self.main_frame = ExpandedFrame(self)
		frame = ExpandedFrame(self.main_frame)
		self.tree = Tree(frame, text='name', width=GuiConfig.LSBLK_NAME_WIDTH, columns=GuiConfig.LSBLK_COLUMNS_WIDTH)
		for path, details in blkdevs.items():
			values = (
				details['type'],
				details['size'],
				StringUtils.str(details['label']),
				StringUtils.str(details['vendor']),
				StringUtils.str(details['model']),
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
