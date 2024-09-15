#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class GuiConfig:
	'''Configurations for the GUI'''

	PAD = 2
	JOB_HEIGHT = 8
	#TEXT_WIDTH = 120
	#TEXT_HEIGHT = 40
	HELP_WIDTH = 80
	ENTRY_WIDTH = 144
	MIN_ENTRY_WIDTH = 8
	MAX_ENTRY_WIDTH = 32
	MAX_ENTRY_HEIGHT = 8
	MAX_ROW_QUANT = 5
	MAX_COLUMN_QUANT = 10
	FILES_FIELD_WIDTH = 94
	SMALL_FIELD_WIDTH = 24
	BUTTON_WIDTH = 24
	MENU_WIDTH = 18
	#TREE_HEIGHT = 24
	#TREE_WIDTH = 640
	SOURCE_PATH_WIDTH = 80
	SOURCE_ID_WIDTH = 16
	TREE_WALK_DEPTH = 10
	TREE_WALK_WIDTH = 100
	LSBLK_NAME_WIDTH = 16
	LSBLK_COLUMNS = (
		('type', 10),
		('size', 10),
		('label', 16),
		('vendor', 12),
		('model', 24),
		('rev', 12),
		('ro', 4),
		('mountpoints', 20)
	)	
	WRITE_DEST_NAME_WIDTH = 200
	WRITE_DEST_COLUMNS = (
		('type', 10),
		('size', 10),
		('label', 16),
		('vendor', 12),
		('model', 12),
		('rev', 12),
		('ro', 4)
	)
