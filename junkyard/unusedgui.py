#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class BasicTab:
	'''Basic notebook tab'''

	def __init__(self, root):
		'''Notebook page'''
		root.settings.init_section(self.MODULE)
		frame = ExpandedFrame(root.notebook)
		root.notebook.add(frame, text=f' {self.CMD} ')
		SourceDirSelector(frame)
		GridLabel(frame, root.DESTINATION, columnspan=2)
		FilenameSelector(frame, root.FILENAME, root.FILENAME)
		DirSelector(frame, root.OUTDIR, root.DIRECTORY, root.SELECT_DEST_DIR)
		AddJobButton(frame, self.MODULE, self._add_job)
		self.root = root
	
	def _add_job(self):
		'''Generate command line'''
		self.root.settings.section = self.CMD
		source = self.root.settings.get(self.root.SOURCE)
		outdir = self.root.settings.get(self.root.OUTDIR)
		filename = self.root.settings.get(self.root.FILENAME)
		if not source or not outdir or not filename:
			showerror(
				title = self.root.MISSING_ENTRIES,
				message = self.root.SOURCED_DEST_REQUIRED
			)
			return
		cmd = self.root.settings.section.lower()
		cmd += f' --{self.root.OUTDIR.lower()} "{outdir}"'
		cmd += f' --{self.root.FILENAME.lower()} "{filename}"'
		cmd += f' "{source}"'
		self.root.append_job(cmd)

class SelectTsvColumn(ChildWindow):
	'''Window to select column of a TSV file'''

	def __init__(self, root, column_var, file_var):
		'''Open child window to select column of TSV file'''
		if root.child_win_active:
			return
		self.column_var = column_var
		self.file_var = file_var
		tsv = self.file_var.get()
		if not tsv:
			showerror(
				title = BasicLabels.MISSING_ENTRY,
				message = BasicLabels.FIRST_CHOOSE_TSV
			)
			return
		encoding, head = ExtPath.read_utf_head(Path(tsv), lines_out=GuiConfig.MAX_ROW_QUANT)
		try:
			columns = len(head[0].split('\t'))
		except IndexError:
			columns = 1
		if columns == 1:
			self.file_var.set('1')
			return
		if len(head) < 2:
			tsv = None
		super().__init__(root, BasicLabels.SELECT_COLUMN)
		self._selected_column = StringVar()
		frame = ExpandedFrame(self)
		preview = {(row, column): entry
			for row, line in enumerate(head)
			for column, entry in enumerate(line.split('\t'))
		}
		entry_heights = [0]*GuiConfig.MAX_ROW_QUANT
		for row in range(GuiConfig.MAX_ROW_QUANT):
			for column in range(GuiConfig.MAX_COLUMN_QUANT):
				try:
					entry_heights[row] = max(
						entry_heights[row],
						min(int(len(preview[row, column])/GuiConfig.MAX_ENTRY_WIDTH)+1,
							GuiConfig.MAX_ENTRY_HEIGHT)
					)
				except KeyError:
					break
		entry_widths = [GuiConfig.MIN_ENTRY_WIDTH]*GuiConfig.MAX_COLUMN_QUANT
		for column in range(GuiConfig.MAX_COLUMN_QUANT):
			for row in range(GuiConfig.MAX_ROW_QUANT):
				try:
					entry_widths[column] = max(
						entry_widths[column],
						min(len(preview[row, column]), GuiConfig.MAX_ENTRY_WIDTH)
					)
				except KeyError:
					break
		for row, height in enumerate(entry_heights):
			for column, width in enumerate(entry_widths):
				try:
					entry = preview[row, column]
				except KeyError:
					break
				text = ScrolledText(frame, width=width, height=height)
				text.grid(row=row, column=column)
				text.bind('<Key>', lambda dummy: 'break')
				text.insert('end', preview[row, column])
				text.configure(state='disabled')
		if columns > GuiConfig.MAX_COLUMN_QUANT:
			columns = GuiConfig.MAX_COLUMN_QUANT
		row += 1
		for column in range(columns):
			Button(frame,
				text = f'{column+1}',
				command = partial(self._get_column, column+1)
			).grid(row=row, column=column, padx=GuiConfig.PAD, pady=GuiConfig.PAD)
		frame = ExpandedFrame(self)
		RightButton(frame, BasicLabels.QUIT, self.destroy)

	def _get_column(self, column):
		'''Get the selected column'''
		self.column_var.set(f'{column}')
		self.destroy()