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

__all__ = ['Vita','IS_PE_ID']

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

    def identity(self,entity):
        """
            Returns the person_id to which this entity belongs,
            or None, if the entity is unidentified
        """

        if entity and isinstance(entity,int):
            pr_pe_id = entity
        elif entity and isinstance(entity,dict):
            if 'pr_pe_id' in entity:
                pr_pe_id = entity.pr_pe_id
            elif 'id' in entity:
                pr_pe_id = entity.id
            else:
                return None
        else:
            return None

        query = (self.db.pr_pentity.deleted==False) & (self.db.pr_pentity.id==pr_pe_id)

        try:
            pentity = self.db(query).select(
                self.db.pr_pentity.id,
                self.db.pr_pentity.parent,
                self.db.pr_pentity.opt_pr_pentity_class
                )[0]
            if pentity.opt_pr_pentity_class==1:
                query = (self.db.pr_person.deleted==False) & (self.db.pr_person.pr_pe_id==pentity.id)
                person = self.db(query).select(self.db.pr_person.id)[0]
                return person.id
            elif pentity.parent:
                return( self.identify(pentity.parent))
            else:
                return None
        except:
            return None

    def identify(self,entity,person):
        """
            Establishes the identity of an entity
        """
        return

    def samples(self,entity,types=None):
        """
            Returns a list of all entities that belong to the given
            entity (filtered by types, if given)
        """
        return None

    def members(self,group):
        """
            Returns a list of all members of a group, or, if a list
            of groups is given, all members that belong to all groups
        """
        return None

    def presence_before(self,entity,when):
        """
            Returns a list of all registered appearances of the given
            entity before 'when'
        """
        return None

    def presence_after(self,entity,when):
        """
            Returns a list of all registered appearances of the given
            entity after 'when'
        """
        return None

    def presence(self,entity,starttime,endtime):
        """
            Returns a list of all registered appearances of the given
            entity between 'starttime' and 'endtime'
        """
        return None

    def locate(self,entity,now):
        """
            Finds the latest registered appearance of the given entity
            before 'now'
        """
        return None

    def locate_all(self,entity,now):
        """
            Finds the lastest registered appearances of the given entity
            and all belonging entities before 'now'
        """
        return None

    def candidates(self,description,threshold=None):
        """
            Searches for persons in the database that match the given
            description above a certain threshold, and returns a list
            of candidates
        """
        return None

    def count(self,**attr):
        """
            Counts registered persons with the given attributes
        """
        return None

    def persons(self,**attr):
        """
            Finds all persons in the registry with the given attributes
        """
        return None

#
# Validators ------------------------------------------------------------------
#

class IS_PE_ID(object):
    """
        PersonEntity ID validator, to be used in DB definition
    """

    def __init__(
        self,
        dbset,
        class_opts=None,
        filter_opts=None,
        error_message='not a person entity!', # CAVE: Internationalization!
        multiple=False
        ):
        self.error_message = error_message
        self.class_opts = class_opts
        self.filter_opts = filter_opts
        self.multiple = multiple

        if hasattr(dbset, 'define_table'):
            self.dbset = dbset()
        else:
            self.dbset = dbset

    def pentity_represent(self,pentity):
        if pentity and pentity.opt_pr_pentity_class==1:
            subentity_record=self.dbset(self.dbset._db['pr_person']['pr_pe_id']==pentity.id).select()[0]
            if subentity_record:
                pentity_str = '%s %s [%s] (%s %s)' % (
                    subentity_record.first_name,
                    subentity_record.last_name or '',
                    subentity_record.pr_pe_label or 'no label',
                    self.class_opts[1],
                    subentity_record.id
                )
            else:
                pentity_str = '[%s] (%s PE=%s)' % (
                    pentity.label or 'no label',
                    self.class_opts[1],
                    pentity.id
                )
        elif pentity and pentity.opt_pr_pentity_class==2:
            subentity_record=self.dbset(self.dbset._db['pr_group']['pr_pe_id']==pentity.id).select()[0]
            if subentity_record:
                pentity_str = '%s (%s %s)' % (
                    subentity_record.group_name,
                    self.class_opts[2],
                    subentity_record.id
                )
            else:
                pentity_str = '(%s PE=%s)' % (
                    pr_pentity_class_opts[2],
                    pentity.id
                )
        elif pentity and pentity.opt_pr_pentity_class==3:
            subentity_record=self.dbset(self.dbset._db['hrm_body']['pr_pe_id']==pentity.id).select()[0]
            if subentity_record:
                pentity_str = '[%s] (%s %s)' % (
                    subentity_record.pr_pe_label or 'no label',
                    self.class_opts[3],
                    subentity_record.id
                )
            else:
                pentity_str = '[%s] (%s PE=%s)' % (
                    pentity.label or 'no label',
                    self.class_opts[3],
                    pentity.id
                )
        elif pentity:
            pentity_str = '[%s] (%s PE=%s)' % (
                pentity.label or 'no label',
                self.class_opts[pentity.opt_pr_pentity_class],
                pentity.id
            )
        return pentity_str

    def options(self):
        query = self.dbset._db['pr_pentity']['deleted']==False
        if self.filter_opts:
            query = (self.dbset._db['pr_pentity']['opt_pr_pentity_class'].belongs(self.filter_opts)) & query
        records = self.dbset(query).select(orderby=self.dbset._db['pr_pentity'].opt_pr_pentity_class)
        set = []
        for r in records:
            set.append((r.id,  self.pentity_represent(r)))
        return( set )

    def __call__(self,value):
        try:
            query = self.dbset._db['pr_pentity']['deleted']==False
            if self.filter_opts:
                query = (self.dbset._db['pr_pentity']['opt_pr_pentity_class'].belongs(self.filter_opts)) & query
            if self.dbset(query).count():
                return (value, None)
            else:
                pass
        except ValueError:
            pass
        return (value, self.error_message)
