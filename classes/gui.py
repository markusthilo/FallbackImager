#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from threading import Thread, Event
from json import load, dump
from pathlib import Path
from subprocess import run
from tkinter import Tk, PhotoImage, StringVar, BooleanVar, Checkbutton, Toplevel, Menu
from tkinter.font import nametofont
from tkinter.ttk import Frame, Treeview, Scrollbar, Notebook, Label, LabelFrame, Combobox, Entry
from tkinter.ttk import Spinbox, Menubutton, Progressbar, Sizegrip, Button
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilenames, askdirectory
from tkinter.messagebox import showerror, askokcancel, askyesno, showwarning
from idlelib.tooltip import Hovertip
from classes.config import GuiDefs, LangPackage
from classes.coreutils import CoreUtils
from tkinter import IntVar

class WorkThread(Thread):
	'''The worker has tu run as thread not to freeze GUI/Tk'''

	def __init__(self, src_paths, dst_path, simulate, echo, finish):
		'''Pass arguments to worker'''
		super().__init__()
		self._finish = finish
		self._kill_event = Event()
		try:
			self._worker = Copy(src_paths, dst_path, simulate=simulate, echo=echo, kill=self._kill_event, finish=self._finish)
		except Exception as ex:
			self._finish(ex)

	def kill(self):
		'''Kill thread'''
		self._kill_event.set()

	def kill_is_set(self):
		'''Return True if kill event is set'''
		return self._kill_event.is_set()

	def run(self):
		'''Run thread'''
		try:
			self._finish(self._worker.run())
		except Exception as ex:
			self._finish(ex)

class Gui(Tk):
	'''GUI look and feel'''

	def __init__(self, config, lang=None, debug=False):
		'''Open application window'''
		self._config = config
		self._defs = GuiDefs()
		self._labels = LangPackage(lang, self._config)
		self._work_thread = None
		super().__init__()
		self.title(f'{self._config.get("app_name")} v{self._config.get("version")}')	### define the gui ###
		for row, weight in enumerate(self._defs.row_weights):
			self.rowconfigure(row, weight=weight)
		for column, weight in enumerate(self._defs.column_weights):
			self.columnconfigure(column, weight=weight)
		self.iconphoto(True, PhotoImage(file=Path(__file__).parent.parent.joinpath('appicon.png')))
		self.protocol('WM_DELETE_WINDOW', self._quit_app)
		self._font = nametofont('TkTextFont').actual()
		min_size_x = self._font['size'] * self._defs.x_factor
		min_size_y = self._font['size'] * self._defs.y_factor
		self.minsize(min_size_x , min_size_y)
		self.geometry(f'{min_size_x}x{min_size_y}')
		self.resizable(True, True)
		self._pad = int(self._font['size'] * self._defs.pad_factor)
		###### block devices in tree view ######
		frame = Frame(self)
		frame.grid(row=0, column=0, columnspan=5, sticky='nsew', padx=self._pad, pady=self._pad)
		self._blockdev_tree = Treeview(frame,
			selectmode = 'browse',
			columns = ('label', 'type', 'size', 'fstype', 'ro', 'info'),
			show = 'tree headings'
		)
		for i, column in enumerate(['#0', 'label', 'type', 'size', 'fstype', 'ro', 'info']):
			self._blockdev_tree.heading(column, text=self._labels.blockdev_heading[i], anchor='w')
			width = self._font['size'] * self._defs.blockdev_tree_widths[i]
			self._blockdev_tree.column(column, width=width, minwidth=width, stretch=self._defs.blockdev_tree_stretch[i]==1, anchor='w')
		self._gen_blockdev_tree()
		self._blockdev_tree.pack(side='left', expand=True, fill='both')
		vsb = Scrollbar(frame, orient='vertical', command=self._blockdev_tree.yview)
		vsb.pack(side='right', fill='y')
		self._blockdev_tree.configure(yscrollcommand=vsb.set)
		Hovertip(frame, self._labels.blockdev_tip)
		#self._drive_tree.bind('<Button-1>', self._select_blockdev)
		###### notebook ######
		self._notebook = Notebook(self, padding=self._pad)
		self._notebook.grid(row=1, column=0, columnspan=5, sticky='nsew')
		self._ewfacquire_frame = Frame(self._notebook)
		self._notebook.add(self._ewfacquire_frame, text=' ewfaquire ', sticky='nswe')
		self._ewfverify_frame = Frame(self._notebook)
		self._notebook.add(self._ewfverify_frame, text=' ewfverify ', sticky='nswe')
		self._wipe_frame = Frame(self._notebook)
		self._notebook.add(self._wipe_frame, text=' wipe ', sticky='nswe')
		self._monitor_frame = Frame(self._notebook)
		self._notebook.add(self._monitor_frame, text=f' {self._labels.operations_monitor} ', sticky='nswe')
		####### EWFACQUIRE #######
		for col in range(4):
			self._ewfacquire_frame.columnconfigure(col, weight=1)
		source_frame = LabelFrame(self._ewfacquire_frame, text=self._labels.source)	### source selector
		source_frame.grid(row=0, column=0, columnspan=5, sticky='nswe')
		Hovertip(source_frame, self._labels.source_tip)
		self._source_text = ScrolledText(source_frame,
			font = (self._font['family'], self._font['size']),
			wrap = "none",
			padx = self._pad,
			pady = self._pad,
			height = 2
		)
		self._source_text.pack(side='left', expand=True, fill='both', padx=self._pad, pady=self._pad)
		Hovertip(self._source_text, self._labels.source_tip)
		button = Button(source_frame, text=self._labels.add_source_files, command=self._select_source_files)
		button.pack(side='right', fill='y', padx=self._pad, pady=self._pad)
		Hovertip(button, self._labels.add_source_files_tip)
		self._case_no = StringVar()	### case numnber ###
		self._dropdown_entry(
			self._ewfacquire_frame,
			self._labels.case_no,
			self._case_no,
			'case_no',
			self._labels.ewf_metadata_tip
		).grid(row=1, column=0, columnspan=2, sticky='nsew', padx=self._pad, pady=self._pad)
		self._evidence_no = StringVar()	### evidence numnber ###
		self._dropdown_entry(
			self._ewfacquire_frame,
			self._labels.evidence_no,
			self._evidence_no,
			'evidence_no',
			self._labels.ewf_metadata_tip
		).grid(row=1, column=2, columnspan=2, sticky='nsew', padx=self._pad, pady=self._pad)
		self._description = StringVar()	### description ###
		self._dropdown_entry(
			self._ewfacquire_frame,
			self._labels.description,
			self._description,
			'description',
			self._labels.ewf_metadata_tip
		).grid(row=2, column=0, columnspan=4, sticky='nsew', padx=self._pad, pady=self._pad)
		self._examiner = StringVar()	### examiner ###
		self._dropdown_entry(
			self._ewfacquire_frame,
			self._labels.examiner,
			self._examiner,
			'examiner',
			self._labels.ewf_metadata_tip
		).grid(row=3, column=0, columnspan=4, sticky='nsew', padx=self._pad, pady=self._pad)
		self._notes = StringVar()	### notes ###
		self._dropdown_entry(
			self._ewfacquire_frame,
			self._labels.notes,
			self._notes,
			'notes',
			self._labels.ewf_metadata_tip
		).grid(row=4, column=0, columnspan=5, sticky='nsew', padx=self._pad, pady=self._pad)
		self._media_type = StringVar(value=self._config.get('media_type', default='auto'))	### media type ###
		self._dropdown_selector(
			self._ewfacquire_frame,
			self._labels.media_type,
			self._media_type,
			('auto', 'fixed', 'removable', 'optical'),
			self._labels.ewf_metadata_tip
		).grid(row=1, column=4, sticky='nsew', padx=self._pad, pady=self._pad)
		self._media_flag = StringVar(value=self._config.get('media_flag', default='auto'))	### media flag ###
		self._dropdown_selector(
			self._ewfacquire_frame,
			self._labels.media_flag,
			self._media_type,
			('auto', 'logical', 'physical'),
			self._labels.ewf_metadata_tip
		).grid(row=2, column=4, sticky='nsew', padx=self._pad, pady=self._pad)
		self._codepage = StringVar(value=self._config.get('codepage', default='ascii'))	### codepage ###
		self._dropdown_selector(
			self._ewfacquire_frame,
			self._labels.codepage,
			self._codepage,
			('ascii', 'windows-874', 'windows-932', 'windows-936', 'windows-949',
				'windows-950', 'windows-1250', 'windows-1251', 'windows-1252',
				'windows-1253', 'windows-1254', 'windows-1255', 'windows-1256',
				'windows-1257', 'windows-1258'
			),
			self._labels.ewf_metadata_tip
		).grid(row=3, column=4, sticky='nsew', padx=self._pad, pady=self._pad)
		self._compression = StringVar(value=self._config.get('compression', default='fast'))	### compression ###
		self._dropdown_selector(
			self._ewfacquire_frame,
			self._labels.compression,
			self._compression,
			('fast', 'best', 'empty-block', 'none'),
			self._labels.compression_tip
		).grid(row=5, column=0, sticky='nsew', padx=self._pad, pady=self._pad)
		self._segment_size = StringVar(value=self._config.get('segment_size', default='size/40'))	### segment size ###
		self._dropdown_selector(
			self._ewfacquire_frame,
			self._labels.segment_size,
			self._segment_size,
			(' file size', 'size/10', 'size/20', 'size/40', 'size/80',
				'1.4GiB', '4GiB', '8GiB', '16GiB', '32GiB', '256GiB', '512GiB', '1TiB'
			),
			self._labels.segment_size_tip,
			state = 'normal'
		).grid(row=5, column=1, sticky='nsew', padx=self._pad, pady=self._pad)
		self._additional_hash = StringVar(value=self._config.get('additional_hash', default='-'))	### additional hash ###
		self._dropdown_selector(
			self._ewfacquire_frame,
			self._labels.additional_hash,
			self._additional_hash,
			('-', 'sha1', 'sha256'),
			self._labels.additional_hash_tip
		).grid(row=5, column=2, sticky='nsew', padx=self._pad, pady=self._pad)
		self._bytes_per_sector = IntVar(value=512)	### bytes per sector ###
		self._dropdown_selector(
			self._ewfacquire_frame,
			self._labels.bytes_per_sector,
			self._bytes_per_sector,
			tuple(2 ** p for p in range(9, 17)),
			self._labels.bytes_per_sector_tip
		).grid(row=5, column=3, sticky='nsew', padx=self._pad, pady=self._pad)
		self._sectors_at_once = IntVar(value=self._config.get('sectors_at_once', default=64))	### sectors at once ###
		self._dropdown_selector(
			self._ewfacquire_frame,
			self._labels.sectors_at_once,
			self._sectors_at_once,
			tuple(2 ** p for p in range(4, 16)),
			self._labels.sectors_at_once_tip
		).grid(row=5, column=4, sticky='nsew', padx=self._pad, pady=self._pad)
		self._retries = IntVar(value=self._config.get('retries', default=2))	### retries on error ###
		self._int_spinbox(
			self._ewfacquire_frame,
			self._labels.retries,
			self._retries,
			0, 255,
			self._labels.retries_tip
		).grid(row=6, column=0, sticky='nsew', padx=self._pad)
		self._granularity = IntVar(value=self._config.get('granularity', default=64))	### error granularity ###
		self._int_spinbox(
			self._ewfacquire_frame,
			self._labels.granularity,
			self._granularity,
			1, 64,
			self._labels.granularity_tip
		).grid(row=6, column=1, sticky='nsew', padx=self._pad, pady=self._pad)
		self._offset = IntVar(value=0)	### offset ###
		self._int_spinbox(
			self._ewfacquire_frame,
			self._labels.offset,
			self._offset,
			0, (2 ** 63) - 1,
			self._labels.offset_tip
		).grid(row=6, column=2, sticky='nsew', padx=self._pad, pady=self._pad)
		self._bytes_to_acquire = IntVar(value=0)	### bytes to aquire ###
		self._int_spinbox(
			self._ewfacquire_frame,
			self._labels.bytes_to_acquire,
			self._bytes_to_acquire,
			0, (2 ** 63) - 1,
			self._labels.bytes_to_acquire_tip
		).grid(row=6, column=3, sticky='nsew', padx=self._pad, pady=self._pad)
		self._file_format = StringVar(value=self._config.get('file_format', default='encase6'))	### file format ###
		self._dropdown_selector(
			self._ewfacquire_frame,
			self._labels.file_format,
			self._file_format,
			('ewf', 'smart', 'ftk', 'encase1', 'encase2', 'encase3', 'encase4', 'encase5', 'encase6', 'linen5', 'linen6', 'ewfx'),
			self._labels.file_format_tip
		).grid(row=6, column=4, sticky='nsew', padx=self._pad, pady=self._pad)
		self._destination_ewf = StringVar()	### destination ###
		self._destination_selector(
			self._ewfacquire_frame,
			self._labels.destination_ewf,
			self._destination_ewf,
			self._labels.destination_ewf_tip
		).grid(row=7, column=0, columnspan=4, sticky='nsew', padx=self._pad, pady=self._pad)
		frame = LabelFrame(self._ewfacquire_frame, text=self._labels.more_options)	### more options ###
		frame.grid(row=7, column=4, sticky='nswe', padx=self._pad, pady=self._pad)
		self._more_options_text = StringVar(value='\u2610')
		button = Menubutton(frame, textvariable=self._more_options_text)
		button.pack(fill='x', padx=self._pad, pady=self._pad)
		menu = Menu(button)
		button.config(menu=menu)
		self._mimic_encase = IntVar(value=self._config.get('mimic_encase', default=0))	### mimic encase like behavior ###
		menu.add_checkbutton(label=self._labels.mimic_encase, onvalue=1, offvalue=0, variable=self._mimic_encase)
		self._swap_bytes = IntVar(value=self._config.get('swap_bytes', default=0))	### swap byte pairs ###
		menu.add_checkbutton(label=self._labels.swap_bytes, onvalue=1, offvalue=0, variable=self._swap_bytes)
		self._resume_activity = IntVar(value=self._config.get('resume_activity', default=0))	### resume activity ###
		menu.add_checkbutton(label=self._labels.resume_activity, onvalue=1, offvalue=0, variable=self._resume_activity)
		Hovertip(frame, self._labels.more_options_tip)
		Hovertip(button, self._labels.more_options_tip)
		self._destination2_ewf = StringVar()	### 2nd destination ###
		self._destination_selector(
			self._ewfacquire_frame,
			self._labels.destination2_ewf,
			self._destination2_ewf,
			self._labels.destination2_ewf_tip
		).grid(row=8, column=0, columnspan=4, sticky='nsew', padx=self._pad, pady=self._pad)
	
		#	-T:     specify the file containing the table of contents (TOC) of an optical disc. The TOC file must be in the CUE format.
		#-2:     specify the secondary target file (without extension) to writeto

		self._queue_frame = LabelFrame(self._monitor_frame, text=self._labels.queue)	### queue ###
		self._queue_frame.pack(fill='both', expand=True, padx=self._pad, pady=self._pad)
		self._control_frame = LabelFrame(self._monitor_frame, text='\u25AD')	### control ###
		self._control_frame.pack(fill='both', expand=True, padx=self._pad, pady=self._pad)
		self._start_button = Button(self._control_frame, text='\u25B6', command=self._start)
		self._start_button.pack(side='left', padx=self._pad, pady=(0, self._pad))
		Hovertip(self._start_button, self._labels.start_tip)
		self._stop_button = Button(self._control_frame, text='\u25A0', command=self._stop)
		self._stop_button.pack(side='left', padx=self._pad, pady=(0, self._pad))
		Hovertip(self._stop_button, self._labels.stop_tip)
		self._quit_button = Button(self._control_frame, text='\u2716', width=2, command=self._quit_app)
		self._quit_button.pack(side='right', padx=(0, self._pad*4), pady=(0, self._pad))
		Hovertip(button, self._labels.quit_tip)
		self._shutdown = BooleanVar(value=False)
		self._shutdown_button = Checkbutton(self._control_frame,
			text = self._labels.shutdown,
			variable = self._shutdown,
			command = self._toggle_shutdown
		)
		self._shutdown_button.pack(side='right', padx=self._pad, pady=(0, self._pad))
		Hovertip(self._shutdown_button, self._labels.shutdown_tip)
		button = Button(self._control_frame,	### sudo ###
			text = self._labels.sudo_password,
			command = self._test_sudo
			)
		button.pack(side='right', padx=self._pad, pady=(0, self._pad))
		Hovertip(button, self._labels.sudo_check_tip)
		self._sudo_password = StringVar()
		entry = Entry(self._control_frame, textvariable=self._sudo_password, show='*')
		entry.pack(side='right', fill='x', expand=True, padx=self._pad, pady=(0, self._pad))
		Hovertip(entry, self._labels.sudo_password_tip)
		

		self._info_frame = LabelFrame(self._monitor_frame, text=self._labels.info)	### info ###
		self._info_frame.pack(fill='both', expand=True, padx=self._pad, pady=self._pad)
		self._info_text = ScrolledText(self._info_frame,	### info ###
			font = (self._font['family'], self._font['size']),
			padx = self._pad,
			pady = self._pad
		)
		self._info_text.pack(expand=True, fill='both', padx=self._pad, pady=self._pad)
		self._info_text.bind('<Key>', lambda dummy: 'break')
		self._info_text.configure(state='disabled')
		self._info_fg = self._info_text.cget('foreground')
		self._info_bg = self._info_text.cget('background')
		self._info_newline = True

		Sizegrip(self).grid(row=3, column=3, sticky='se', padx=self._pad, pady=self._pad)
		self._init_warning()

	def _dropdown_entry(self, parent, text, textvariable, key, hovertip):
		'''Combobox with LabelFrame and Buttons'''
		def _store():
			if value := textvariable.get():
				values = self._config.get(key)
				if not value in values:
					values.append(value)
					values.sort()
					textvariable.set(value)
					entry['values'] = values
					self._config.set(key, values)
		def _remove():
			if value := textvariable.get():
				values = self._config.get(key)
				if value in values:
					values.remove(value)
					textvariable.set(values[0] if values else '')
					entry['values'] = values
					self._config.set(key, values)
		frame = LabelFrame(parent, text=text)
		button_remove = Button(frame, text='\u2421', width=2, command=_remove)
		button_remove.pack(side='right', padx=self._pad, pady=(0, self._pad))
		button_store = Button(frame, text='\u272A', width=2, command=_store)
		button_store.pack(side='right', padx=self._pad, pady=(0, self._pad))
		entry = Combobox(frame, textvariable=textvariable, values=self._config.get(key, default=list()))
		entry.pack(side='right', expand=True, fill='x', padx=self._pad, pady=self._pad)
		Hovertip(frame, hovertip)
		Hovertip(entry, hovertip)
		Hovertip(button_store, self._labels.store_value_tip)
		Hovertip(button_remove, self._labels.remove_value_tip)
		return frame

	def _dropdown_selector(self, parent, text, textvariable, values, hovertip, state='readonly', justify='left'):
		'''Combobox with LabelFrame'''
		frame = LabelFrame(parent, text=text)
		entry = Combobox(frame, textvariable=textvariable, values=values, state=state)
		entry.pack(expand=True, fill='x', padx=self._pad, pady=self._pad)
		Hovertip(frame, hovertip)
		Hovertip(entry, hovertip)
		return frame

	def _int_spinbox(self, parent, text, textvariable, from_, to, hovertip):
		'''Spinbox with LabelFrame'''
		frame = LabelFrame(parent, text=text)
		spinbox = Spinbox(frame, from_=from_, to=to, textvariable=textvariable, justify='right')
		spinbox.pack(fill='x', padx=self._pad, pady=self._pad)
		Hovertip(frame, hovertip)
		Hovertip(spinbox, hovertip)
		return frame

	def _destination_selector(self, parent, text, textvariable, tip):
		'''Entry field with Button for destination file selector'''
		frame = LabelFrame(parent, text=text)
		name_button = Button(frame, text='\U0001F4CB', width=2, command=self._gen_destination_name)
		name_button.pack(side='right', padx=self._pad, pady=(0, self._pad))
		entry = Entry(frame, textvariable=textvariable)
		entry.pack(side='right', expand=True, fill='x', padx=self._pad, pady=self._pad)
		dir_button = Button(frame, text='\U0001F5C2', width=2, command=self._select_destination_dir)
		dir_button.pack(side='right', padx=self._pad, pady=(0, self._pad))
		Hovertip(dir_button, self._labels.destination_dir_tip)
		Hovertip(entry, tip)
		Hovertip(name_button, self._labels.destination_file_tip)
		return frame

	def _clean(self, info):
		'''Clean info text'''
		if info == None:
			return ''
		if isinstance(info, str):
			return info.strip() if info else ''
		if isinstance(info, bool):
			return self._labels.yes if info else self._labels.no
		return ', '.join(f'{value}'.strip() for value in info)

	def _gen_blockdev_tree(self):
		'''Refresh tree of block devices'''
		self._blockdev_tree.delete(*self._blockdev_tree.get_children())
		paths = list()
		for path, dev in CoreUtils.lsblk().items():
			self._blockdev_tree.insert(dev['parent'], 'end',
				iid = path,
				text = path,
				values = (
					self._clean(dev['label']),
					self._clean(dev['type']),
					self._clean(dev['size']),
					'',
					self._clean(dev['ro']),
					self._clean([dev['vendor'], dev['model'], dev['rev'], dev['serial']])
				) if dev['type'] == 'disk' else (
					self._clean(dev['label']),
					self._clean(dev['type']),
					self._clean(dev['size']),
					self._clean(dev['fstype']),
					self._clean(dev['ro']),
					self._clean(dev['mountpoints'])
				),
				open = True
			)

	def _select_destination_dir(self):
		'''Select directory to add into field'''
		if directory := askdirectory(title=self._labels.select_dir, mustexist=True, initialdir=self._config.initial_dir):
			path = Path(directory).absolute()
			self._destination_ewf.set(f'{path}')
			self._config.initial_dir = f'{path}'

	def _gen_destination_name(self):
		'''Generate destination file name'''
		pass

	def _read_source_paths(self):
		'''Read paths from text field'''
		if text := self._source_text.get('1.0', 'end').strip():
			return [Path(line.strip()).absolute() for line in text.split('\n')]
		return ()

	def _chck_source_path(self, source):
		'''Check if source path is valid'''
		if not source:
			return
		path = Path(source)
		if path.exists():
			return path
			showerror(title=self._labels.error, message=self._labels.src_path_not_found.replace('#', f'{path}'))

	def _select_source_dir(self):
		'''Select directory to add into field'''
		if directory := askdirectory(title=self._labels.select_dir, mustexist=True, initialdir=self._config.initial_dir):
			path = Path(directory).absolute()
			if path in self._read_source_paths():
				showerror(title=self._labels.error, message=self._labels.already_added.replace('#', f'{path}'))
				return
			self._source_text.insert('end', f'{path}\n')
			self._config.initial_dir = f'{path}'

	def _select_source_files(self):
		'''Select file(s) to add into field'''
		if filenames := askopenfilenames(title=self._labels.select_files, initialdir=self._config.initial_dir):
			if len(filenames) == 1:
				path = Path(filenames[0]).absolute()
				if path in self._read_source_paths():
					showerror(title=self._labels.error, message=self._labels.already_added.replace('#', f'{path}'))
					return
			for filename in filenames:
				path = Path(filename).absolute()
				if not path in self._read_source_paths():
					self._source_text.insert('end', f'{path}\n')
			self._config.initial_dir = f'{path.parent}'

	def _select_multiple(self):
		'''Select multiple files and directories to add into field'''
		if paths := askpaths(
			title = self._labels.select_multiple,
			confirm = self._labels.confirm,
			cancel = self._labels.cancel,
			initialdir = self._config.initial_dir
		):
			for path in paths:
				if not path in self._read_source_paths():
					self._source_text.insert('end', f'{path}\n')
			self._config.initial_dir = f'{path.parent}'

	def _get_source_paths(self):
		'''Get source paths from text field'''
		unverified_paths = self._read_source_paths()
		if not unverified_paths:
			showerror(title=self._labels.error, message=self._labels.no_source)
			return
		src_paths = list()
		for path in unverified_paths:
			src_path = self._chck_source_path(path)
			if not src_path:
				return
			src_paths.append(src_path)
		return src_paths

	def _select_destination(self):
		'''Select destination directory'''
		if directory := askdirectory(title=self._labels.select_destination, mustexist=False, initialdir=self._config.dst_dir):
			path = Path(directory).absolute()
			self._destination.set(path)
			self._config.dst_dir = f'{path}'
	
	def _get_destination_path(self, src_paths):
		'''Get destination directory'''
		dst_dir = self._destination.get()
		if not dst_dir:
			self._select_destination()
			dst_dir = self._destination.get()
			if not dst_dir:
				showerror(title=self._labels.error, message=self._labels.no_destination)
				return
		try:
			dst_path = Path(dst_dir).absolute()
		except:
			showerror(title=self._labels.error, message=self._labels.invalid_destination.replace('#', f'{dst_dir}'))
			return
		for src_path in src_paths:	# collisions with source paths?
			is_dir = src_path.is_dir()
			if (
				( is_dir and src_path.parent in [dst_path] + list(dst_path.parents) ) or
				( not is_dir and src_path.parent == dst_path )
			):
				showerror(title=self._labels.error, message=self._labels.source_collides_destination.replace('#', f'{src_path}').replace('&', f'{dst_path}'))
				return
				showerror(
					title = self._labels.error,
					message = self._labels.source_collides_destination.replace('#', f'{src_path}').replace('&', f'{dst_path}')
				)
				return
		if dst_path.exists() and not dst_path.is_dir():
			showerror(self._labels.error, self._labels.destination_no_directory.replace('#', f'{dst_path}'))
			return
		return dst_path

	def _mk_destination_path(self, dst_path):
		'''Make destination directory'''
		if dst_path.exists():
			top = dst_path.samefile(dst_path.parent)
			for path in dst_path.iterdir():
				if top and path.is_dir() and path.name.upper() in ('$RECYCLE.BIN', 'SYSTEM VOLUME INFORMATION'):
					continue
				if askyesno(self._labels.warning, self._labels.destination_not_empty.replace('#', f'{dst_path}')):
					return
				else:
					return True
			return
		try:
			dst_path.mkdir(parents=True)
		except Exception as ex:
			showerror(
				title = self._labels.error,
				message = f'{self._labels.invalid_dst_path.replace("#", dst_dir)}\n{type(ex): {ex}}'
			)
			return True

	def _select_log(self):
		'''Select directory '''
		if directory := askdirectory(title=self._labels.select_log, mustexist=False, initialdir=self._config.log_dir):
			path = Path(directory).absolute()
			self._log.set(path)
			self._config.log_dir = f'{path}'

	def _get_log_dir(self):
		'''Get log directory'''
		if log_dir := self._log.get():
			try:
				self._config.log_dir = f'{Path(log_dir).absolute()}'
			except:
				return
		else:
			self._config.log_dir = ''

	def _mk_log_dir(self):
		'''Create log directory if not exists'''
		if log_dir := self._log_entry.get():
			try:
				self._config.log_dir = f'{Path(log_dir).absolute()}'
			except Exception as ex:
				showerror(
					title = self._labels.error,
					message = f'{self._labels.invalid_log_path.replace("#", f"{log_dir_path}")}\n{type(ex)}: {ex}'
				)
				self._config.log_dir = ''
		else:
			self._config.log_dir = ''
		if not self._config.log_dir and self._config.hashes:
			self._select_log()
			if not self._config.log_dir:
				showerror(title=self._labels.error, message=self._labels.log_required)
				return True
		if self._config.log_dir:
			try:
				Path(log_dir).mkdir(parents=True, exist_ok=True)
			except Exception as ex:
				showerror(
					title = self._labels.error,
					message = f'{self._labels.invalid_log_path.replace("#", self._config.log_dir)}\n{type(ex)}: {ex}'
				)
				return True
			
	def _gen_options_list(self):
		'''Generate list of options'''
		return [
			f'\u2611 {option}' if option in self._config.options else f'\u2610 {option}'
			for option in self._config.robocopy_parameters
		]

	def _gen_hash_list(self):
		'''Generate list of hashes to check'''
		return [
			f'\u2611 {hash}' if hash in self._config.hashes else f'\u2610 {hash}'
			for hash in self.possible_hashes
		]

	def _gen_verify_list(self):
		'''Generate list of verification methodes'''
		return [
			f'\u2611 {self._labels.size}' if self._config.verify == 'size' else f'\u2610 {self._labels.size}'
		] + [
			f'\u2611 {hash}' if self._config.verify == hash else f'\u2610 {hash}'
			for hash in self._config.hashes
		]

	def _options_event(self, dummy_event):
		'''Robocopy options selection'''
		choosen = self._options_var.get()[2:]
		self._options_var.set(self._labels.options)	# reset shown text
		if choosen in self._config.options:
			self._config.options.remove(choosen)
		else:
			self._config.options.append(choosen)
			self._config.options.sort()
			for deselect in self._config.robocopy_parameters[choosen]:
				try:
					self._config.options.remove(deselect)
				except ValueError:
					pass
		self._options_selector['values'] = self._gen_options_list()

	def _hash_event(self, dummy_event):
		'''Hash algorithm selection'''
		choosen = self._hash_var.get()[2:]
		self._hash_var.set(self._labels.hash)	# reset shown text
		if choosen in self._config.hashes:
			self._config.hashes.remove(choosen)
			if choosen == self._config.verify:
				self._config.verify = 'size'
		else:
			self._config.hashes.append(choosen)
			self._config.hashes.sort()
		self._hash_selector['values'] = self._gen_hash_list()
		self._verify_selector['values'] = self._gen_verify_list()

	def _verify_event(self, dummy_event):
		'''Hash algorithm selection'''
		choosen = self._verify_var.get()[2:]
		self._verify_var.set(self._labels.verify)	# reset shown text
		choosen = 'size' if choosen == self._labels.size else choosen
		if choosen == self._config.verify:
			self._config.verify = ''
		else:
			self._config.verify = choosen
		self._verify_selector['values'] = self._gen_verify_list()

	def _clear_source(self):
		'''Clear source text'''
		self._source_text.delete('1.0', 'end')

	def _clear_info(self):
		'''Clear info text'''
		self._info_text.configure(state='normal')
		self._info_text.delete('1.0', 'end')
		self._info_text.configure(state='disabled')
		self._info_text.configure(foreground=self._info_fg, background=self._info_bg)
		self._warning_state = 'stop'

	def _start_worker(self, src_paths, dst_path, simulate):
		'''Disable source selection and start worker'''
		if self._mk_log_dir():
			return
		try:
			self._config.save()
		except:
			showerror(title=self._labels.warning, message=self._labels.config_error)
			return
		self._exec_button.configure(state='disabled')
		self._warning_state = 'disabled'
		self._clear_info()
		self._quit_button_text.set(self._labels.abort)
		if simulate:
			self._simulate_button_text.set(self._labels.abort)
		else:
			self._simulate_button.configure(state='disabled')
			self._clear_source()
		self._work_thread = WorkThread(
			src_paths,
			dst_path,
			simulate,
			self.echo,
			self.finished
		)
		self._work_thread.start()

	def _simulate(self):
		'''Run simulation'''
		if self._work_thread:
			self._work_thread.kill()
			return
		src_paths = self._get_source_paths()
		if not src_paths:
			return
		dst_path = self._get_destination_path(src_paths)
		if not dst_path:
			return
		self._start_worker(src_paths, dst_path, True)

	def _execute(self):
		'''Start copy process / worker'''
		if self._work_thread:
			return
		src_paths = self._get_source_paths()
		if not src_paths:
			return
		dst_path = self._get_destination_path(src_paths)
		if not dst_path:
			return
		if self._mk_destination_path(dst_path):
			return
		self._start_worker(src_paths, dst_path, False)

	def _echo_help(self):
		'''Show RoboCopy help'''
		self._clear_info()
		for line in RoboCopy(parameters='/?').popen().stdout:
			self.echo(line.strip())
		self.echo(self._labels.help_text)

	def _init_warning(self):
		'''Init warning functionality'''
		self._warning_state = 'disabled'
		self._warning()

	def _enable_warning(self):
		'''Enable red text field and blinking Label'''
		self._info_text.configure(foreground=self._defs.red_fg, background=self._defs.red_bg)
		self._warning_state = 'enable'

	def _warning(self):
		'''Show flashing warning'''
		if self._warning_state == 'enable':
			self._info_label.configure(text=self._labels.warning)
			self._warning_state = '1'
		if self._warning_state == '1':
			self._info_label.configure(foreground=self._defs.red_fg, background=self._defs.red_bg)
			self._warning_state = '2'
		elif self._warning_state == '2':
			self._info_label.configure(foreground=self._label_fg, background=self._label_bg)
			self._warning_state = '1'
		elif self._warning_state != 'disabled':
			self._info_label.configure(text= '', foreground=self._label_fg, background=self._label_bg)
			self._warning_state = 'disabled'
		self.after(500, self._warning)

	def _toggle_shutdown(self):
		'''Toggle select switch to shutdown after finish'''
		if self._shutdown.get():
			self._shutdown.set(False)
			if askyesno(title=self._labels.warning, message=self._labels.shutdown_warning):
				self._shutdown.set(True)

	def _reset(self):
		'''Run this when worker has finished copy process'''
		self._simulate_button_text.set(self._labels.simulate)
		self._simulate_button.configure(state='normal')
		self._exec_button.configure(state='normal')
		self._quit_button_text.set(self._labels.quit)
		self._work_thread = None

	def _test_sudo(self):
		'''Test sudo password'''
		if not self._coreutils.i_have_root():
			if not self._coreutils.no_pw_sudo():
				showerror(title=self._labels.error, message=self._labels.no_sudo)
				return False
			if not self._coreutils.whoami():
				showerror(title=self._labels.error, message=self._labels.no_root)
				return False
			if not self._coreutils.gen_cmd('echo', 'test', sudo=True, password='test'):
				showerror(title=self._labels.error, message=self._labels.invalid_password)
				return False
		return True

	def _start(self):
		'''Start queue processing'''
		pass

	def _stop(self):
		'''Stop queue processing'''
		pass

	def _quit_app(self):
		'''Quit app or ask to abort process'''
		if self._work_thread:	
			if self._work_thread.kill_is_set():
				self._reset()
			else:
				if askokcancel(title=self._labels.warning, message=self._labels.abort_warning):
					self._work_thread.kill() # kill running work thread
				return
		try:
			self._config.save()
		except:
			pass
		self.destroy()

	def _delay_shutdown(self):
		'''Delay shutdown and update progress bar'''
		if self._shutdown_cnt < self._defs.shutdown_delay:
			self._shutdown_cnt += 1
			self._delay_progressbar.step(1)
			self._shutdown_window.after(1000, self._delay_shutdown)
		else:
			run(['shutdown', '/s'])

	def _shutdown_dialog(self):
		'''Show shutdown dialog'''
		self._shutdown_window = Toplevel(self)
		self._shutdown_window.title(self._labels.warning)
		self._shutdown_window.transient(self)
		self._shutdown_window.focus_set()
		self._shutdown_window.resizable(False, False)
		self._shutdown_window.grab_set()
		frame = Frame(self._shutdown_window, padding=self._pad)
		frame.pack(fill='both', expand=True)
		Label(frame,
			text = '\u26A0',
			font = (self._font['family'], self._font['size'] * self._defs.symbol_factor),
			foreground = self._defs.symbol_fg,
			background = self._defs.symbol_bg
		).pack(side='left', padx=self._pad, pady=self._pad)
		Label(frame, text=self._labels.shutdown_question, anchor='s').pack(
			side='right', fill='both', padx=self._pad, pady=self._pad
		)
		frame = Frame(self._shutdown_window, padding=self._pad)
		frame.pack(fill='both', expand=True)
		self._delay_progressbar = Progressbar(frame, mode='determinate', maximum=self._defs.shutdown_delay)
		self._delay_progressbar.pack(side='top', fill='x', padx=self._pad, pady=self._pad)
		cancel_button = Button(frame, text=self._labels.cancel_shutdown, command=self._shutdown_window.destroy)
		cancel_button.pack(side='bottom', fill='both', padx=self._pad, pady=self._pad)
		self.update_idletasks()
		self._shutdown_cnt = 0
		self._delay_shutdown()
		self._shutdown_window.wait_window(self._shutdown_window)

	def echo(self, *args, end=None):
		'''Write message to info field (ScrolledText)'''
		msg = ' '.join(f'{arg}' for arg in args)
		self._info_text.configure(state='normal')
		if not self._info_newline:
			self._info_text.delete('end-2l', 'end-1l')
		self._info_text.insert('end', f'{msg}\n')
		self._info_text.configure(state='disabled')
		if self._info_newline:
			self._info_text.yview('end')
		self._info_newline = end != '\r'

	def finished(self, returncode):
		'''Run this when worker has finished copy process'''
		if returncode:
			if self._admin_rights and self._shutdown.get():	### Shutdown dialog ###
				self._shutdown_dialog()
			if isinstance(returncode, Exception):
				self._enable_warning()
				showerror(
					title = self._labels.error, 
					message = f'{self._labels.aborted_on_error}\n\n{type(returncode)}:\n{returncode}'
				)
			elif isinstance(returncode, str):
				self._enable_warning()
				showwarning(title=self._labels.warning, message=self._labels.process_returned.replace('#', returncode))
			else:
				self._info_text.configure(foreground=self._defs.green_fg, background=self._defs.green_bg)
		self._reset()

if __name__ == '__main__':  # start here when run as application
	Gui().mainloop()