#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2023-05-15'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'United Working Class :)'

from threading import Thread

class Worker(Thread):
	'''Work job after job'''

	def __init__(self, jobs, echo=print, debug=False):
		'''Give job list and info handler to Worker object'''
		self.jobs = jobs
		self.echo = echo
		if debug:
			self.debug = print
		else:
			self.debug = FileImagerCLI.no_echo
		self.imager = PyCdlibCli(exit_on_error=False)

	def run(self):
		'''Start the work'''
		for job in self.jobs:
			cmd = ' '.join(job)
			self.echo(f'Processing >{cmd}<...')
			if job[0].lower() == 'pycdlib':
				self.debug(f'job: {job}')
				self.imager.parse(job[1:])
				self.imager.run(echo=self.debug)
				self.echo('Job done.')
			else:
				self.echo(f'Unknown command >{job[0]}<')
		self.echo('All done.')
