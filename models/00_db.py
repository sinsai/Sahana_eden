# -*- coding: utf-8 -*-

"""
    DB configuration
"""

import os, traceback, datetime
import re
# All dates should be stored in UTC for Sync to work reliably
request.utcnow = datetime.datetime.utcnow()

########################
# Database Configuration
########################

# Switch to "False" in Production for a Performance gain
# (need to set to "True" again when amending Table definitions)
migrate = True

#if request.env.web2py_runtime_gae:            # if running on Google App Engine
#    db = DAL("gae")                           # connect to Google BigTable
#    session.connect(request, response, db=db) # and store sessions and tickets there
    ### or use the following lines to store sessions in Memcache
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db=MEMDB(Client())
#else:                                         # else use a normal relational database
#db = DAL("sqlite://storage.db")       # if not, use SQLite or other DB
db = DAL("mysql://sahanapy:password@localhost/sahanapy", pool_size=30) # or other DB
#db = DAL("postgres://postgres:password@localhost/db", pool_size=10)

##################################
# Instantiate Classes from Modules
##################################

# Custom classes which extend default Gluon & T2
exec("from applications.%s.modules.sahana import *" % request.application)

# Faster for Production (where app-name won't change):
#from applications.sahana.modules.sahana import *
# We should change this to use:
# sahana = local_import("sahana")

# t2 = sahana.S3(request, response, session, cache, T, db)
# auth = sahana.AuthS3(globals(), db)
# etc
t2 = S3(request, response, session, cache, T, db)

# Custom validators
exec("from applications.%s.modules.validators import *" % request.application)
# Faster for Production (where app-name won't change):
#from applications.sahana.modules.validators import *

# Custom Utilities and Widgets
exec("from applications.%s.modules.shn_utils import *" % request.application)
exec("from applications.%s.modules.widgets import *" % request.application)
# Faster for Production (where app-name won't change):
#from applications.sahana.modules.shn_utils import *
#from applications.sahana.modules.widgets import *

mail = Mail()
auth = AuthS3(globals(), db)
crud = CrudS3(globals(), db)
from gluon.tools import Service
service = Service(globals())

# GIS Module
s3gis = local_import("s3gis")
gis = s3gis.GIS(globals(), db, auth)

# VITA
s3vita = local_import("s3vita")
vita = s3vita.Vita(globals(), db)

# Logout session clearing
# shn_on_login ----------------------------------------------------------------
# added 2009-08-27 by nursix
def shn_auth_on_login(form):
    """
        Actions that need to be performed on successful login (Do not redirect from here!)
    """

    # S3XRC
    s3xrc.clear_session(session)

# shn_on_logout ---------------------------------------------------------------
# added 2009-08-27 by nursix
def shn_auth_on_logout(user):
    """
        Actions that need to be performed on logout (Do not redirect from here!)
    """

    # S3XRC
    s3xrc.clear_session(session)

from gluon.storage import Storage
# Keep all S3 framework-level elements stored off here, so as to avoid polluting global namespace & to make it clear which part of the framework is being interacted with
# Avoid using this where a method parameter could be used: http://en.wikipedia.org/wiki/Anti_pattern#Programming_anti-patterns
s3 = Storage()

