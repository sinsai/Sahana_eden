# -*- coding: utf-8 -*-

"""
    DB configuration
"""

import os, traceback, datetime
import re
# All dates should be stored in UTC for Sync to work reliably
request.utcnow = datetime.datetime.utcnow()

# Switch to 'False' in Production for a Performance gain
# (need to set to 'True' again when amending Table definitions)
migrate = False

#if request.env.web2py_runtime_gae:            # if running on Google App Engine
#    db = DAL('gae')                           # connect to Google BigTable
#    session.connect(request, response, db=db) # and store sessions and tickets there
    ### or use the following lines to store sessions in Memcache
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db=MEMDB(Client())
#else:                                         # else use a normal relational database
db = DAL('sqlite://storage.db')       # if not, use SQLite or other DB
#db = DAL('mysql://sahanapy:password@localhost/sahanapy', pool_size=30) # or other DB
#db = DAL('postgres://postgres:password@localhost/db', pool_size=10)

# Custom classes which extend default Gluon & T2
exec('from applications.%s.modules.sahana import *' % request.application)
# Faster for Production (where app-name won't change):
#from applications.sahana.modules.sahana import *
# We should change this to use:
# sahana = local_import('sahana')
# t2 = sahana.S3(request, response, session, cache, T, db)
# auth = sahana.AuthS3(globals(), db)
# etc
t2 = S3(request, response, session, cache, T, db)

# Custom validators
exec('from applications.%s.modules.validators import *' % request.application)
# Faster for Production (where app-name won't change):
#from applications.sahana.modules.validators import *

# GIS Module
s3gis = local_import('s3gis')
gis = s3gis.GIS(globals(), db)

# VITA
s3vita = local_import('s3vita')
vita = s3vita.Vita(globals(), db)
