#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from json import load, dump
from tkinter import StringVar, IntVar, BooleanVar

class Settings(dict):
	'''Handle settings'''

	def __init__(self, path):
		'''Set path to JSON config file'''
		self.path = path
		try:
			with self.path.open() as fh:
				self.update(load(fh))
		except:
			pass
		self.this_section = 'Base'

	def _init_section(self, section=None):
		'''Open a section in settings if necessary'''
		if not section:
			section = self.this_section
		if not section in self:
			self[section] = dict()

	def set(self, key, value, section=None):
		'''Set value directly into settings dict'''
		if not section:
			section = self.this_section
		self._init_section(section=section)
		self[section][key] = value

	def get(self, key, section=None):
		'''Get value from settings dict'''
		if not section:
			section = self.this_section
		if not section in self or not key in self[section]:
			return None
		try:
			return self[section][key].get()
		except AttributeError:
			return self[section][key]

	def init_stringvar(self, key, section=None, default=None):
		'''Get or generate StringVar for one setting'''
		if not section:
			section = self.this_section
		self._init_section(section)
		value = self.get(key, section=section)
		if value:
			self[section][key] = StringVar(value=value)
		elif default:
			self[section][key]= StringVar(value=default)
		else:
			self[section][key] = StringVar(value='')
		return self[section][key]

	def init_intvar(self, key, section=None, default=None):
		'''Get or generate IntVar for one setting'''
		if not section:
			section = self.this_section
		self._init_section(section)
		value = self.get(key, section=section)
		if value:
			self[section][key] = IntVar(value=value)
		else:
			self[section][key] = IntVar(value=default)
		return self[section][key]

	def init_boolvar(self, key, section=None, default=None):
		'''Get or generate BooleanVar for one setting'''
		if not section:
			section = self.this_section
		self._init_section(section)
		value = self.get(key, section=section)
		if value != None:
			self[section][key] = BooleanVar(value=value)
		else:
			self[section][key] = BooleanVar(value=default)
		return self[section][key]

	def decoded(self):
		'''Decode settings by fetching values from tk variables'''
		dec_settings = dict()
		for section in self:
			dec_section = dict()
			for key in self[section]:
				value = self.get(key, section=section)
				if value:
					dec_section[key] = value
			if dec_section:
				dec_settings[section] = dec_section
		return dec_settings

	def write(self):
		'''Write settings to JSON file'''
		try:
			with self.path.open('w') as fh:
				dump(self.decoded(), fh)
		except OSError as err:
			return err
