#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import name as __os_name__
from subprocess import Popen, PIPE, STDOUT

if __os_name__ == 'nt':
    from subprocess import STARTUPINFO, STARTF_USESHOWWINDOW
    class OpenProc(Popen):
        '''Subprocess for Windows'''
        def __init__(cmd):
            self.startupinfo = STARTUPINFO()
            self.startupinfo.dwFlags |= STARTF_USESHOWWINDOW
            super().__init__(self, cmd,
                stdout = PIPE,
                stderr = STDOUT,
                encoding = 'utf-8',
                universal_newlines = True,
                startupinfo = self.startupinfo
            )
else:
    class OpenProc(Popen):
        '''Subprocess for real operating systems'''
        def __init__(cmd):
        super().__init__(self, cmd, stdout=PIPE, stderr=STDOUT)
