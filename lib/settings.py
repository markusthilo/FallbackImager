#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from json import load, dump
from tkinter import StringVar, IntVar, BooleanVar
from pathlib import Path

class Settings(dict):
	'''Handle settings'''

	def __init__(self, path):
		'''Set path to JSON config file, default is app or script name with .json'''
		self.path = path
		try:
			with self.path.open() as fh:
				loaded = load(fh)
		except FileNotFoundError:
			loaded = dict()
		self.update(loaded)

	def init_section(self, section):
		'''Open a section in settings'''
		self.section = section
		if not section in self:
			self[section] = dict()

	def get(self, key, section=None):
		'Get value'
		if not section:
			section = self.section
		try:
			return self[section][key].get()
		except (KeyError, AttributeError):
			return None

	def init_stringvar(self, key, default=None, section=None):
		'''Generate StringVar for one setting'''
		if not section:
			section = self.section
		value = self.get(key, section=section)
		if value:
			self[section][key] = StringVar(value=value)
		elif default:
			self[section][key] = StringVar(value=default)
		else:
			self[section][key] = StringVar(value='')
		return self[section][key]

	def init_intvar(self, key, default=None, section=None):
		'''Generate IntVar for one setting'''
		if not section:
			section = self.section
		value = self.get(key, section=section)
		if value:
			self[section][key] = IntVar(value=value)
		else:
			self[section][key] = IntVar(value=default)
		return self[section][key]

	def init_boolvar(self, key, default=False, section=None):
		'''Generate BooleanVar for one setting'''
		if not section:
			section = self.section
		value = self.get(key, section=section)
		if value:
			self[section][key] = BooleanVar(value=value)
		else:
			self[section][key] = BooleanVar(value=default)
		return self[section][key]

	def decoded(self):
		'''Decode settings using get method'''
		dec_settings = dict()
		for section in self:
			dec_section = dict()
			for key in self[section]:
				value = self.get(key, section=section)
				if value:
					dec_section[key] = value
			if dec_section != dict():
				dec_settings[section] = dec_section
		return dec_settings

	def write(self):
		'''Write config file'''
		try:
			with self.path.open('w') as fh:
				dump(self.decoded(), fh)
		except PermissionError as err:
			return err

