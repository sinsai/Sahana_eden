#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage:
    Install py2exe: http://sourceforge.net/projects/py2exe/files/
    Check you have the right version of msvcr90.dll (http://www.py2exe.org/index.cgi/Tutorial#Step52)
    Copy script to the web2py directory
    c:\bin\python26\python standalone_exe.py py2exe
"""

from distutils.core import setup
import py2exe
from gluon.import_all import base_modules, contributed_modules
import os
import shutil
import fnmatch
try:
	print 'Removing sneaky3 - Not Python 2.5 friendly'
	os.remove('gluon/sneaky3.py')
except:
	pass
try:
	shutil.copytree('applications', 'dist/applications')
except:
	# This is entered when applications directory already exists in dist
	shutil.rmtree('dist/applications')
	shutil.copytree('applications', 'dist/applications')

try:
	shutil.copy('C:\Bin\Python26\DLLs\geos.dll', 'dist/')
	shutil.copy('C:\Bin\Python26\DLLs\libgeos-3-2-2.dll', 'dist/')
except:
	print "Copy geos.dll and libgeos-3-2-2.dll from Python26\DLLs into the dist directory"

setup(
  console=['web2py.py'],
  windows=[{'script':'web2py.py',
    'dest_base':'web2py_no_console',    # MUST NOT be just 'web2py' otherwise it overrides the standard web2py.exe
    }],
  data_files=[
        'NEWINSTALL',
        'ABOUT',
        'LICENSE',
        'VERSION',
        ],
  options={'py2exe': {
    'packages': 
contributed_modules + ['lxml', 'serial', 'reportlab', 'geraldo', 'xlwt', 'shapely', 'PIL'],
    'includes': base_modules,
    }},
  )

