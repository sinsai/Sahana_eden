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

    def persons(self,**attr):
        """
            Find all persons with the given attributes
        """
        query = (self.db.pr_person.deleted==False)

        if not len(attr):
            # No attributes = return all persons
            return self.db(query).select(self.db.pr_person.ALL)
        else:
            return None

    def get_pentity_id(self,entity):
        if entity:
            if isinstance(entity, int):
                # Entity ID is given as int, just return it
                return None
            elif isinstance(entity, dict):
                # Entity ID is given as either .id or .pr_pe_id in the dict
                return None
            elif isinstance(entity, string):
                # Tag Label given => find corresponding entity and return id
                return None
            elif isinstance(entity, (list,tuple)):
                # List of entities given, return a list of ID's
                return None
            else:
                return None
        else:
            return None

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

    #
    # members -----------------------------------------------------------------
    #
    def members(self,group,filterby=None,inclusive=False):
        """
            Returns a list of all members of a group (a list of Person ID's),
            or, if a list of groups is given, a list of persons that are members
            to at least one (inclusive=True) or to all of the groups (inclusive=False)
        """

        if group and isinstance(group, int):

            query = (self.db.pr_group.deleted==False) & (self.db.pr_group.id==group)
            try:
                group_record = self.db(query).select(self.db.pr_group.ALL)[0]
                return self.members(group_record, filterby=filterby, inclusive=inclusive)
            except:
                # No such group or group deleted
                return None

        elif group and isinstance(group, dict) and 'id' in group:

            query = (self.db.pr_group_membership.deleted==False) & (self.db.pr_group_membership.group_id==group.id)

            if filterby and inclusive:
                query = (not(self.db.pr_group_membership.person_id.belongs(filterby))) & query
            elif filterby:
                query = (self.db.pr_group_membership.person_id.belongs(filterby)) & query

            rows = self.db(query).select(self.db.pr_group_membership.person_id)

            members = [row.person_id for row in rows]

            if len(members):
                return members
            else:
                return None

        elif group and isinstance(group, (list, tuple)):

            _filterby = filterby

            for _group in group:

                memberlist = self.members(_group, filterby=_filterby, inclusive=inclusive)

                if memberlist and inclusive:
                    _filterby.extend(memberlist)
                elif memberlist:
                    _filterby = memberlist
                elif not inclusive:
                    return None

            return memberlist

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
            before 'now'. If 'now' is omitted, it defaults to the current
            server time.
        """

        pentity_id = self.pentity_id( entity )

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

    def missing(self,entity):
        """
            Finds all "Missing" entries for the given entity
        """

        MISSING = 7

        if entity and isinstance(entity,int):
            pe_id = entity
        elif entity and isinstance(entity,dict):
            if pr_pe_id in entity and entity.pr_pe_id:
                pe_id = entity.pr_pe_id
            elif id in entity and entity.id:
                pe_id = entity.id
            else:
                return None
        else:
            return None

        query = (self.db.pr_presence.deleted==False) & (self.db.pr_presence.pr_pe_id==pe_id)
        query = (self.db.pr_presence.opt_pr_presence_condition==MISSING) & (query)

        records = self.db(query).select(self.db.pr_presence.ALL)

        return records
