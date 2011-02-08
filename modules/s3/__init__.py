# -*- coding: utf-8 -*-

""" S3 Framework Extensions for web2py

    This package is loaded in models/000_1st_run.py as "s3base",
    this namespace can be used to access all S3 classes, e.g.::

        s3base.S3Resource()

    @see: U{B{I{S3 Developer Guidelines}} <http://eden.sahanafoundation.org/wiki/DeveloperGuidelinesS3>}

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @author: Fran Boon <francisboon[at]gmail.com>
    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2009-2011 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

"""

# Import all names from the S3 modules that shall be accessible
# under the s3base namespace:

# Basic Tools
from s3tools import *

# Deployment Settings
from s3cfg import *

# Authentication, Authorization, Accounting
from s3aaa import *

# Utilities, Validators and Widgets
# These names are also imported into the global namespace in
# 00_db.py in order to access them without the s3base prefix:
from s3utils import *
from s3validators import *
from s3widgets import *

# Test framework (currently unused)
#from s3test import *

# Resource API
from s3xrc import S3ResourceController
from s3rest import S3Resource, S3Method

# RESTful Methods
from s3crud import S3CRUD
from s3search import S3Search, S3LocationSearch, S3PersonSearch

# GIS Mapping
from s3gis import *

# Messaging
from s3msg import *

# VITA Person Data Toolkit
from s3vita import *
