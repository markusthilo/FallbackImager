#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import Tk, Canvas, Scrollbar
from tkinter.ttk import Frame

class ScrollFrame
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

		for i in range(10)
			Label(self.scrolled_frame, text="Hello World").grid(row=i, column=i)
	i+=1

	# Update the scroll region after new widgets are added
	updateScrollRegion()

	root.after(1000, addNewLabel)

	def _update_canvas():
		'''Updates the scrollable region of the canvas'''
		self.canvas.update_idletasks()
		self.canvas.config(scrollregion=fTable.bbox())


# Adds labels diagonally across the screen to demonstrate the scrollbar adapting to the increasing size
i=0
def addNewLabel():
	global i
	tk.Label(fTable, text="Hello World").grid(row=i, column=i)
	i+=1

	# Update the scroll region after new widgets are added
	updateScrollRegion()

	root.after(1000, addNewLabel)

createScrollableContainer()
addNewLabel()

root.mainloop()


if __name__ == '__main__':	# start here if called as application
	root = Tk()
	
	root.mainloop()