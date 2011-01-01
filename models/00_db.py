# -*- coding: utf-8 -*-

"""
    Import Modules
    Configure the Database
    Instantiate Classes
"""


import datetime
import os
import re
import time
import traceback
import uuid

from lxml import etree

import gluon.contrib.simplejson as json

from gluon.sql import SQLCustomType

# All dates should be stored in UTC for Sync to work reliably
request.utcnow = datetime.datetime.utcnow()

########################
# Database Configuration
########################

migrate = deployment_settings.get_base_migrate()

db_string = deployment_settings.get_database_string()
if db_string[0].find("sqlite") != -1:
    db = DAL(db_string[0], check_reserved=["mysql", "postgres"])
else:
    # Tuple (inc pool_size)
    try:
        db = DAL(db_string[0], pool_size=db_string[1])
    except:
        db_type = db_string[0].split(":", 1)[0]
        db_location = db_string[0].split("@", 1)[1]
        raise(HTTP(503, "Cannot connect to %s Database: %s" % (db_type, db_location)))

#if request.env.web2py_runtime_gae:        # if running on Google App Engine
#session.connect(request, response, db=db) # Store sessions and tickets in DB
### or use the following lines to store sessions in Memcache (GAE-only)
# from gluon.contrib.memdb import MEMDB
# from google.appengine.api.memcache import Client
# session.connect(request, response, db=MEMDB(Client())

###################################
# Instantiate Classes from Modules
###################################

from gluon.tools import Mail
mail = Mail()

# AAA
auth = s3base.AuthS3(globals(), deployment_settings, db)
s3_audit = s3base.S3Audit(db, session, migrate=migrate)

# Shortcuts
shn_has_role = auth.shn_has_role
shn_has_permission = auth.shn_has_permission
shn_accessible_query = auth.shn_accessible_query

# Custom classes which extend default Gluon
FieldS3 = s3base.FieldS3
MENUS3 = s3base.MENUS3
crud = s3base.CrudS3(globals(), db)
S3ReusableField = s3base.S3ReusableField

from gluon.tools import Service
service = Service(globals())

from gluon.tools import callback

# Keep all S3 framework-level elements stored off here, so as to avoid polluting global namespace & to make it clear which part of the framework is being interacted with
# Avoid using this where a method parameter could be used: http://en.wikipedia.org/wiki/Anti_pattern#Programming_anti-patterns
s3 = Storage()

# S3 Custom Validators,
# imported here into the global namespace in order
# to access them without the s3base namespace prefix
exec("from applications.%s.modules.s3.s3validators import *" % request.application)
# Faster for Production (where app-name won't change):
#from applications.eden.modules.s3.s3validators import *

# S3 Custom Utilities and Widgets
# imported here into the global namespace in order
# to access them without the s3base namespace prefix
exec("from applications.%s.modules.s3.s3utils import *" % request.application)
exec("from applications.%s.modules.s3.s3widgets import *" % request.application)
# Faster for Production (where app-name won't change):
#from applications.eden.modules.s3.s3utils import *
#from applications.eden.modules.s3.s3widgets import *

# GIS Module
gis = s3base.GIS(globals(), deployment_settings, db, auth, cache=cache)

# VITA
vita = s3base.S3Vita(globals(), db)

# S3XRC
s3.crud = Storage()
s3xrc = s3base.S3DataStore(globals(), db)

# MSG
msg = s3base.S3Msg(globals(), deployment_settings, db, T, mail)

# Logout session clearing
# shn_on_login ----------------------------------------------------------------
# added 2009-08-27 by nursix
def shn_auth_on_login(form):
    """
        Actions that need to be performed on successful login (Do not redirect from here!)
    """

    # S3XRC
    s3xrc.clear_session()

# shn_on_logout ---------------------------------------------------------------
# added 2009-08-27 by nursix
def shn_auth_on_logout(user):
    """
        Actions that need to be performed on logout (Do not redirect from here!)
    """

    # S3XRC
    s3xrc.clear_session()

# END
# *****************************************************************************
