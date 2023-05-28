#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from json import load, dump
from tkinter import StringVar, IntVar
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
			value = self[section][key]
		except KeyError:
			return ''
		try:
			return value.get()
		except AttributeError:
			return value

	def init_stringvar(self, key, default=None, section=None):
		'''Generate StringVar for one setting'''
		value = self.get(key, section=section)
		if not value and default:
			self[self.section][key] = StringVar(value=default)
		else:
			self[self.section][key] = StringVar(value=value)
		return self[self.section][key]

	def init_intvar(self, key, default=None, section=None):
		'''Generate IntVar for one setting'''
		value = self.get(key, section=section)
		if not value and default:
			self[self.section][key] = IntVar(value=default)
		else:
			self[self.section][key] = IntVar(value=value)
		return self[self.section][key]

	def raw(self, key, section=None):
		'''Get value as it is'''
		if not section:
			section = self.section
		return self[self.section][key]

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
		with self.path.open('w') as fh:
			dump(self.decoded(), fh)
