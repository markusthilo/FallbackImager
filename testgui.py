#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import Tk, Canvas, Scrollbar
from tkinter.ttk import Frame, Label

class ScrollFrame:
	'''Frame with scroll bars and buttons'''

	def __init__(self, root):
		'''Build the frame'''
		self.canvas = Canvas(root)
		self.scrolled_frame = Frame(self.canvas)
		self.h_scrollbar = Scrollbar(root)
		self.v_scrollbar = Scrollbar(root)

		self.canvas.config(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set, highlightthickness=0)
		self.h_scrollbar.config(orient='horizontal', command=self.canvas.xview)
		self.v_scrollbar.config(orient='vertical', command=self.canvas.yview)
		self.h_scrollbar.pack(fill='x', side='bottom', expand=False)
		self.v_scrollbar.pack(fill='y', side='right', expand=False)
		self.canvas.pack(fill='both', side='left', expand=True)
		self.canvas.create_window(0, 0, window=self.scrolled_frame, anchor='nw')

		self.scrolled_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

		for i in range(10):
			Label(self.scrolled_frame, text="Hello World").grid(row=i, column=i)



		#self.canvas.update_idletasks()
		#self.canvas.config(scrollregion=self.canvas.bbox('all'))



		#updateScrollRegion()


if __name__ == '__main__':	# start here if called as application
	root = Tk()
	ScrollFrame(root)
	root.mainloop()