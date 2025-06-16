#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from json import load, dump
from pathlib import Path

class Config:
	'''Handle configuration file in JSON format'''

	def __init__(self):
		'''Read config file'''
		self.path = Path.home().joinpath('.config', 'fallbackimager.conf.json')
		self._config = dict()
	
	def update_path(self, path):
		'''Get config file path'''
		if path:
			self.path = path

	def load(self):
		'''Load config file'''
		if self.path.exists():
			try:
				with self.path.open(encoding='utf-8') as fp:
					self._config = load(fp)
			except Exeption as ex:
				return ex
	
	def set(self, key, value, force=False):
		'''Insert key-value pair if new key'''
		if not key in self._config or force:
			self._config[key] = value

	def get(self, key, default=None):
		'''Get value by key'''
		if key in self._config:
			return self._config[key]
		self._config[key] = default
		return default

	def save(self, path=None):
		'''Save config file'''
		if path:
			self.path = path
		try:
			with self.path.open('w', encoding='utf-8') as fp:
				dump(self._config, fp)
		except Exception as ex:
			return ex

class GuiDefs:
	'''Define GUI elements'''

	def __init__(self):
		'''Read GUI definitions file'''
		with Path(__file__).parent.parent.joinpath('gui.json').open(encoding='utf-8') as fp:
			for key, value in load(fp).items():
				self.__dict__[key] = value

class LangPackage:

	def __init__(self, lang, config):
		'''Read language package file'''
		with Path(__file__).parent.parent.joinpath('lang.json').open(encoding='utf-8') as fp:
			all_langs = dict(load(fp).items())
		self.lang = lang if lang in all_langs else config.get('lang', default='en')
		if not self.lang in all_langs:
			self.lang = 'en'
		config.set('lang', self.lang)
		for key, value in all_langs[self.lang].items():
			self.__dict__[key] = value
