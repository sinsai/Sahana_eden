# -*- coding: utf-8 -*-

"""
This file was developed by Dominic König (aka nursix) as a web2py extension for Sahanapy.
This file is released under the BSD license 
(you can include it in bytecode compiled web2py apps as long as you acknowledge the author).

web2py (required to run this file) is released under the GPLv2 license.
"""

import time
import datetime

from gluon.storage import Storage, Messages
from gluon.http import *
from gluon.validators import *
from gluon.sqlhtml import *
from gluon.contrib.markdown import WIKI
try:
    from gluon.contrib.gql import SQLTable
except ImportError:
    from gluon.sql import SQLTable
import traceback

# Copied from Selenium Plone Tool
def getBrowserName(userAgent):
    "Determine which browser is being used."
    if userAgent.find('MSIE') > -1:
        return 'IE'
    elif userAgent.find('Firefox') > -1:
        return 'Firefox'
    elif userAgent.find('Gecko') > -1:
        return 'Mozilla'
    else:
        return 'Unknown'

from gluon.html import *

__all__ = ['Vita']

#
# VITA Toolkit ----------------------------------------------------------------
#
class Vita(object):
    """
        Toolkit for Person Identification, Tracking and Tracing

        Import:

        exec('from applications.%s.modules.vita import *' % request.application)
        vita = Vita(globals(),db)
    """

    def __init__(self, environment, db=None):
        self.environment = Storage(environment)
        self.db = db

    def pentity(self,entity):
        """
            Get the PersonEntity record for the given ID, ID label, sub-entity or related record
        """

        table = self.db.pr_pentity

        if entity:

            query = ((table.deleted==False) or (table.deleted==None))

            if isinstance(entity,int) or (isinstance(entity,str) and entity.strip().isdigit()):
                query = (table.id==entity) & query

            elif isinstance(entity,str):
                query = (table.label.strip().lower()==entity.strip().lower()) & query

            elif isinstance(entity,dict):
                if 'pr_pe_id' in entity:
                    query = (table.id==entity.pr_pe_id) & query
                else:
                    return None

            else:
                return None

            try:
                record = self.db(query).select()[0]
                return record
            except:
                return None

        else:
            return None

    def person(self,entity):
        """
            Get the Person record for the given ID, PersonEntity record or Person-related record
        """

        table = self.db.pr_person

        if entity:

            query = ((table.deleted==False) or (table.deleted==None))

            if isinstance(entity,int) or (isinstance(entity,str) and entity.strip().isdigit()):
                query = (table.id==entity) & query

            elif isinstance(entity,dict):
                if 'pr_pe_id' in entity:
                    query = (table.pr_pe_id==entity.pr_pe_id) & query
                elif 'person_id' in entity:
                    query = (table.id==entity.person_id) & query
                elif 'id' in entity:
                    query = (table.pr_pe_id==entity.id) & query
                else:
                    return None

            else:
                return None

            try:
                record = self.db(query).select()[0]
                return record
            except:
                return None

        else:
            return None

    def group(self,entity):
        """
            Get the Group record for the given ID, PersonEntity record or Group-related record
        """

        table = self.db.pr_group

        if entity:

            query = ((table.deleted==False) or (table.deleted==None))

            if isinstance(entity,int) or (isinstance(entity,str) and entity.strip().isdigit()):
                query = (table.id==entity) & query

            elif isinstance(entity,dict):
                if 'pr_pe_id' in entity:
                    query = (table.pr_pe_id==entity.pr_pe_id) & query
                elif 'group_id' in entity:
                    query = (table.id==entity.group_id) & query
                elif 'id' in entity:
                    query = (table.pr_pe_id==entity.id) & query
                else:
                    return None

            else:
                return None

            try:
                record = self.db(query).select()[0]
                return record
            except:
                return None

        else:
            return None


    def fullname(self,record):
        """
            Returns the full name of a person
        """

        if record:
            fname, mname, lname = '','',''
            if record.first_name:
                fname = "%s " % record.first_name.strip()
            if record.middle_name:
                mname = "%s " % record.middle_name.strip()
            if record.last_name:
                lname = record.last_name.strip()

            if mname.isspace():
                return "%s%s" % (fname, lname)
            else:
                return "%s%s%s" % (fname, mname, lname)
        else:
            return ''
