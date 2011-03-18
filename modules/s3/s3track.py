# -*- coding: utf-8 -*-

""" Simple Generic Location Tracking System

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
from datetime import datetime

__all__ = ["S3Tracking"]

# =============================================================================
class S3Trackable(object):
    """
    Trackable types instance(s)

    """

    UID = "uuid"
    TRACK_ID = "track_id"

    def __init__(self, db, trackable,
                 record_id=None,
                 uid=None):
        """
        Constructor:

        @param db: the database (DAL)
        @param trackable: the trackable object
        @param record_id: the record ID(s) (if object is a table or tablename)
        @param uid: the record UID(s) (if object is a table or tablename)

        """

        self.db = db
        self.records = []

        self.table = db.sit_trackable

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

        @param timestmp: last datetime for presence (defaults to current time)

        @returns: a location record, or a list of location records (if multiple)

        """

        if timestmp is None:
            timestmp = datetime.utcnow()

        ptable = self.db.sit_presence
        ltable = self.db.gis_location
        locations = dict()
        for r in self.records:
            location = None
            query = ((ptable.deleted == False) &
                     (ptable[self.TRACK_ID] == r[self.TRACK_ID]) &
                     (ptable.timestmp <= timestmp))
            presence = self.db(query).select(orderby=~ptable.timestmp,
                                             limitby=(0, 1)).first()
            if presence:
                if presence.interlock:
                    tablename, record = presence.interlock.split(",", 1)
                    trackable = S3Trackable(self.db, tablename, record)
                    location = trackable.get_location(timestmp=timestmp)
                elif presence.location_id:
                    query = (ltable.id == presence.location_id)
                    location = self.db(query).select(ltable.ALL, limitby=(0, 1)).first()

            if not location:
                if len(self.records) > 1:
                    trackable = S3Trackable(self.db, r)
                else:
                    trackable = self
                location = trackable.get_base_location()

            locations.update({r[self.TRACK_ID]:location})

        if not locations:
            return None
        elif len(locations) == 1:
            return locations.values()[0]
        else:
            return locations


    # -------------------------------------------------------------------------
    def set_location(self, location, timestmp=None):
        """
        Set the current location of instance(s) (at the given time)

        @param location: the location (as Row or record ID)
        @param timestmp: the datetime of the presence (defaults to current time)

        @returns: nothing

        """

        if timestmp is None:
            timestmp = datetime.utcnow()

        if isinstance(location, Rows):
            location = location.first()

        if isinstance(location, Row):
            if "location_id" in location:
                # a record containing a location_id
                location = location.location_id
            elif "base_location" in location:
                # a record containing a base_location
                location = location.base_location
            else:
                # a gis_location record
                location = location.id

        # @todo: validate the location?

        ptable = self.db.sit_presence
        for r in self.records:
            if r[self.TRACK_ID]:
                data = dict(location_id = location, timestmp=timestmp)
                data.update({self.TRACK_ID:r[self.TRACK_ID]})
                ptable.insert(**data)


    # -------------------------------------------------------------------------
    def check_in(self, table, record, timestmp=None):
        """
        Bind the presence of the instance(s) to another resource (e.g. check in
        a person to a facility)

        @param table: table name of the other resource
        @param record: record in the other resource (as Row or record ID)
        @param timestmp: datetime of the check-in

        @returns: nothing

        @note: the other resource must be a trackable type, too!

        """

        ptable = self.db.sit_presence

        if isinstance(table, str):
            table = self.db[table]

        if self.TRACK_ID not in table.fields:
            raise SyntaxError("No trackable type: %s" % table._tablename)

        if isinstance(record, Rows):
            record = record.first()
        if not isinstance(record, Row):
            record = table[record]

        interlock = None
        if record and table._id.name in record:
            record = record[table._id.name]
            if record:
                interlock = "%s,%s" % (table, record)

        if interlock:
            if timestmp is None:
                timestmp = datetime.utcnow()
            q = ((ptable.deleted == False) & (ptable.timestmp <= timestmp))
            for r in self.records:
                query = q & (ptable[self.TRACK_ID] == r[self.TRACK_ID])
                presence = self.db(query).select(orderby=~ptable.timestmp,
                                                 limitby=(0, 1)).first()
                if presence.interlock == interlock:
                    continue
                data = dict(location_id=None,
                            timestmp=timestmp,
                            interlock=interlock)
                data.update({self.TRACK_ID:r[self.TRACK_ID]})
                ptable.insert(**data)


    # -------------------------------------------------------------------------
    def check_out(self):
        """
        Remove the interlock in the last presence record (if any)

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

        @returns: the base location(s) of the current instance

        """

        def _location(r, name):

            ttable = self.db.sit_trackable
            ltable = self.db.gis_location
            query = None
            if name in r:
                query = (ltable.id == r[name])
            else:
                query = (ttable[self.TRACK_ID] == r[self.TRACK_ID])
                trackable = self.db(query).select(limitby=(0, 1)).first()
                table = self.db[trackable.instance_type]
                if name in table.fields:
                    query = ((table[self.TRACK_ID] == r[self.TRACK_ID]) &
                             (ltable.id == table[name]))
            if query:
                location = self.db(query).select(ltable.ALL, limitby=(0, 1)).first()
                return location
            else:
                raise AttributeError

        locations = dict()
        for r in self.records:

            location = None
            try:
                location = _location(r, "location_id")
            except AttributeError:
                try:
                    location = _location(r, "base_location")
                except AttributeError:
                    pass

            locations.update({r[self.TRACK_ID]:location})

        if not locations:
            return None
        elif len(locations) == 1:
            return locations.values()[0]
        else:
            return locations


    # -------------------------------------------------------------------------
    def set_base_location(self, location=None):
        """
        Set the base location of the instance(s)

        @param location: the location for the base location as Row or record ID

        @returns: nothing

        @note: this requires the instance table to have a "location_id" field
               for the base location.

        @note: location=None creates empty location records (with just a name)
               and links them to the instances

        """

        if isinstance(location, Rows):
            location = location.first()
        if isinstance(location, Row):
            location = location.id

        track_ids = [r[self.TRACK_ID] for r in self.records]
        rows = self.db(self.table[self.TRACK_ID].belongs(track_ids)).select()
        tables = dict()
        for r in rows:
            instance_type = r.instance_type
            table = db[instance_type]
            if instance_type not in tables:
                if "location_id" in table.fields:
                    tables.update({instance_type:"location_id"})
                elif "base_location" in table.fields:
                    tables.update({instance_type:"base_location"})
                else:
                    # no base location in this type: ignore gracefully
                    continue
            if location is None:
                # Create and link empty base location record
                trackable = S3Trackable(r.instance_type, uid=r.uuid)
                record = trackable.records.first()
                if record:
                    base_location = trackable.get_base_location()
                    if base_location:
                        # base location already set => skip
                        continue
                    # Choose a name for the location
                    name = "Base location %s" % r[self.TRACK_ID] # Fallback
                    if "name" in record and record["name"]:
                        name = record["name"]
                    elif "first_name" in record and record["first_name"]:
                        name = record["first_name"]
                        middle = record.get("middle_name", None)
                        if middle:
                            name = "%s %s" % (name, middle)
                        last = record.get("last_name", None)
                        if last:
                            name = "%s %s" % (name, last_name)
                    # Insert a location record with just the name
                    base_location = ltable.insert(name=name)
                    # Link the new location
                    fn = tables[instance_type]
                    self.db(table[self.TRACK_ID] == r[self.TRACK_ID]
                                ).update({fn:base_location})

        if location is not None:
            # Location specified => update all base locations
            for tn, fn in tables.items():
                table = db[tn]
                self.db(table[self.TRACK_ID].belongs(track_ids)
                            ).update({fn:location})


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
    def __call__(self, trackable, record_id=None, uid=None):
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
