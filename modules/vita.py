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

    trackable_types = None
    presence_conditions = None

    DEFAULT_TRACKABLE = 1
    DEFAULT_PRESENCE = 4

    def __init__(self, environment, db=None, T=None):
        self.environment = Storage(environment)
        self.db = db

        if T:
            self.T = T
        elif 'T' in self.environment:
            self.T = self.environment['T']

        # -------------------------------------------------------------------------
        # Trackable entity types
        self.trackable_types = {
            1:self.T('Person'),          # an individual
            2:self.T('Group'),           # a group
            3:self.T('Body'),            # a dead body or body part
            4:self.T('Object')           # other objects belonging to persons
        }
        self.DEFAULT_TRACKABLE = 1

        # -------------------------------------------------------------------------
        # Presence Conditions
        self.presence_conditions = {
            1:self.T('Check-In'),        # Arriving at a location for accommodation/storage
            2:self.T('Reconfirmation'),  # Reconfirmation of accomodation/storage at a location
            3:self.T('Check-Out'),       # Leaving from a location after accommodation/storage
            4:self.T('Found'),           # Temporarily at a location
            5:self.T('Procedure'),       # Temporarily at a location for a procedure (checkpoint)
            6:self.T('Transit'),         # Temporarily at a location between two transfers
            7:self.T('Transfer'),        # On the way from one location to another
            8:self.T('Missing'),         # Been at a location, and missing from there
            9:self.T('Lost')             # Been at a location, and destroyed/disposed/deceased there
        }
        self.DEFAULT_PRESENCE = 4

    def pentity(self,entity):
        """
            Get the PersonEntity record for the given ID, ID label, sub-entity or related record
        """

        table = self.db.pr_pentity

        if entity:

            query = ((table.deleted==False) | (table.deleted==None))

            if isinstance(entity,int) or (isinstance(entity,str) and entity.strip().isdigit()):
                query = (table.id==entity) & query

            elif isinstance(entity,str):
                query = (table.label.strip().lower()==entity.strip().lower()) & query

            elif isinstance(entity,dict):
                if 'pr_pe_id' in entity:
                    query = (table.id==entity.pr_pe_id) & query
                else:
                    return entity # entity already given?

            else:
                return None

            try:
                record = self.db(query).select(table.ALL)[0]
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

            query = ((table.deleted==False) | (table.deleted==None))

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
                record = self.db(query).select(table.ALL)[0]
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

            query = ((table.deleted==False) | (table.deleted==None))

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
                record = self.db(query).select(table.ALL)[0]
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

    def rlevenshtein(self,str1,str2):
        """
            Returns a relative value for the Levenshtein distance of two strings

            Levenshtein distance:
            Number of character insertions/deletions/replacements necessary to
            morph one string into the other. Here calculated in relation to the
            maximum string length, hence 0.0 for identical and 1.0 for completely
            different strings.

            Note: Unfortunately, this doesn't work in SQL queries :(
        """

        matrix = {}
        l1 = len(str1)
        l2 = len(str2)

        for i in range(0,l1+1): matrix[i,0] = i
        for j in range(0,l2+1): matrix[0,j] = j 

        for i in range(1,l1+1):
            for j in range(1,l2+1):
                x = matrix[i-1,j]+1
                y = matrix[i,j-1]+1

                if str1[i-1] == str2[j-1]:
                    z = matrix[i-1,j-1]
                else:
                    z = matrix[i-1,j-1]+1

                matrix[i,j] = min(x,y,z)

        return float(matrix[l1,l2])/float(max(l1,l2))
