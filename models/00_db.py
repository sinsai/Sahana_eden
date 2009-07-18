# -*- coding: utf-8 -*-

import os, traceback, datetime
import re

# Switch to 'False' in Production for a Performance gain
# (need to set to 'True' again when amending Table definitions)
migrate = True

#if request.env.web2py_runtime_gae:            # if running on Google App Engine
#    db = DAL('gae')                           # connect to Google BigTable
#    session.connect(request, response, db=db) # and store sessions and tickets there
    ### or use the following lines to store sessions in Memcache
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db=MEMDB(Client())
#else:                                         # else use a normal relational database
db = DAL('sqlite://storage.db')       # if not, use SQLite or other DB
#db = DAL('mysql://root:password@localhost/db', pools=10) # or other DB
#db = DAL('postgres://postgres:password@localhost/db', pools=10)

# Custom classes which extend default Gluon & T2
from applications.sahana.modules.sahana import *
#from applications.sahana.modules.ldapconnect import AuthLDAP

t2 = S3(request, response, session, cache, T, db)

# Custom validators
from applications.sahana.modules.validators import *

def shn_sessions(f):
    """
    Extend session to support:
        Multiple flash classes
        Settings
            Debug mode
            Audit modes
    """
    response.error = session.error
    response.confirmation = session.confirmation
    response.warning = session.warning
    session.error = []
    session.confirmation = []
    session.warning = []
    # Keep all our configuration options in a single global variable
    if not session.s3:
        session.s3 = Storage()
    # Are we running in debug mode?
    session.s3.debug = db().select(db.s3_setting.debug)[0].debug
    # We Audit if either the Global or Module asks us to (ignore gracefully if module author hasn't implemented this)
    try:
        session.s3.audit_read = db().select(db.s3_setting.audit_read)[0].audit_read or db().select(db['%s_setting' % request.controller].audit_read)[0].audit_read
    except:
        session.s3.audit_read = db().select(db.s3_setting.audit_read)[0].audit_read
    try:
        session.s3.audit_write = db().select(db.s3_setting.audit_write)[0].audit_write or db().select(db['%s_setting' % request.controller].audit_write)[0].audit_write
    except:
        session.s3.audit_write = db().select(db.s3_setting.audit_write)[0].audit_write
    return f()
response._caller = lambda f: shn_sessions(f)

#
# Widgets
#

# See test.py

