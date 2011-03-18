# -*- coding: utf-8 -*-

""" Tracking System

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

from gluon.dal import Table, Query, Set, Expression, Rows, Row

__all__ = ["S3Tracking"]

# =============================================================================
class S3Trackable(object):

    UID = "uuid"
    TRACK_ID = "track_id"

    def __init__(self, db, trackable,
                 record_id=None,
                 uid=None):

        self.db = db
        self.records = []

        if isinstance(trackable, (Table, str)):
            if hasattr(trackable, "_tablename"):
                table = trackable
            else:
                table = db[trackable]
            if self.TRACK_ID not in table.fields:
                raise SyntaxError("No trackable type: %s" % tablename)
            query = (table._id > 0)
            if uid is None:
                if record_id is not None:
                    if isinstance(record_id, (list, tuple)):
                        query = (table._id.belongs(record_id))
                    else:
                        query = (table._id == record_id)
            elif UID in table.fields:
                if not isinstance(uid, (list, tuple)):
                    query = (table[UID].belongs(uid))
                else:
                    query = (table[UID] == uid)
            rows = self.db(query).select(table._id, table[self.TRACK_ID])

        elif isinstance(trackable, Row):
            rows = Rows(records=[trackable])

        elif isinstance(trackable, Rows):
            rows = trackable

        elif isinstance(trackable, (list, tuple)):
            rows = Rows(records=trackable)

        elif isinstance(trackable, (Query, Expression)):
            tablename = self.db._adapter.get_table(trackable)
            table = self.db[tablename]
            if self.TRACK_ID not in table.fields:
                raise SyntaxError("No trackable type: %s" % tablename)
            query = trackable
            rows = self.db(query).select(table._id, table[self.TRACK_ID])

        elif isinstance(trackable, Set):
            query = trackable.query
            tablename = self.db._adapter.get_table(query)
            table = self.db[tablename]
            if self.TRACK_ID not in table.fields:
                raise SyntaxError("No trackable type: %s" % tablename)
            rows = trackable.select(table._id, table[self.TRACK_ID])

        else:
            raise SyntaxError("Invalid parameter type %s" % type(trackable))

        self.records = [r for r in rows if self.TRACK_ID in r]


    # -------------------------------------------------------------------------
    def get_location(self, timestmp=None):
        """
        Get the current location of the instance(s) (at the given time)
        """
        raise NotImplementedError


    # -------------------------------------------------------------------------
    def set_location(self, location, timestmp=None):
        """
        Set the current location of instance(s) (at the given time)
        """
        raise NotImplementedError


    # -------------------------------------------------------------------------
    def remove_location(self, location=None):
        """
        Remove a location from the presence log of the instance(s)
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def get_base_location(self):
        """
        Get the base location of the instance(s)
        """
        raise NotImplementedError


    # -------------------------------------------------------------------------
    def set_base_location(self, location):
        """
        Set the base location of the instance(s)
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def remove_base_location(self, location=None):
        """
        Remove the base location of the instance(s)
        """
        raise NotImplementedError


# =============================================================================
class S3Tracking(object):

    """
    S3 Tracking system, to be instantiated once as global "s3_trackable" object
    """

    def __init__(self, env):
        """
        Constructor

        @param env: the global environment (globals())

        """

        self.db = env["db"]

    # -------------------------------------------------------------------------
    def trackable(self, trackable, record_id=None, uid=None):
        """
        Get a tracking interface for a record or set of records

        @param trackable: a Row, Rows, Query, Expression, Set object or
                          a Table or a tablename
        @param record_id: a record ID or a list/tuple of record IDs (together
                          with Table or tablename)
        @param uid: a record UID or a list/tuple of record UIDs (together with
                    Table or tablename)

        @returns: a S3Trackable instance for the specified record(s)

        """

        return S3Trackable(self.db, trackable,
                           record_id=record_id,
                           uid=uid)


    # -------------------------------------------------------------------------
    def get_all(self, entity, location=None, timestmp=None):
        """
        Get all instances of the given entity at the given location and time
        """
        raise NotImplementedError

# =============================================================================
