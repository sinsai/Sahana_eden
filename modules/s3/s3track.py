# -*- coding: utf-8 -*-

""" Simple Generic Location Tracking System

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2011 (c) Sahana Software Foundation
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
from datetime import datetime, timedelta

__all__ = ["S3Tracking"]

# =============================================================================
class S3Trackable(object):
    """
    Trackable types instance(s)

    """

    UID = "uuid" # field name for UIDs

    TRACK_ID = "track_id" # field name for track ID
    LOCATION_ID = "location_id" # field name for base location

    LOCATION = "gis_location" # location tablename
    PRESENCE = "sit_presence" # presence tablename

    def __init__(self, db, trackable, record_id=None, uid=None):
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
                tablename = table._tablename
            else:
                table = db[trackable]
                tablename = trackable
            fields = self.__get_fields(table)
            if not fields:
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
            fields = [table[f] for f in fields]
            rows = self.db(query).select(*fields)

        elif isinstance(trackable, Row):
            fields = self.__get_fields(trackable)
            if not fields:
                raise SyntaxError("Required fields not present in the row")
            rows = Rows(records=[trackable])

        elif isinstance(trackable, Rows):
            rows = [r for r in trackable if self.__get_fields(r)]
            fail = len(trackable) - len(rows)
            if fail:
                raise SyntaxError("Required fields not present in %d of the rows" % fail)
            rows = Rows(records=rows)

        elif isinstance(trackable, (Query, Expression)):
            tablename = self.db._adapter.get_table(trackable)
            table = self.db[tablename]
            fields = self.__get_fields(table)
            if not fields:
                raise SyntaxError("No trackable type: %s" % tablename)
            query = trackable
            fields = [table[f] for f in fields]
            rows = self.db(query).select(*fields)

        elif isinstance(trackable, Set):
            query = trackable.query
            tablename = self.db._adapter.get_table(query)
            table = self.db[tablename]
            fields = self.__get_fields(table)
            if not fields:
                raise SyntaxError("No trackable type: %s" % tablename)
            fields = [table[f] for f in fields]
            rows = trackable.select(*fields)

        else:
            raise SyntaxError("Invalid parameter type %s" % type(trackable))

        self.records = rows


    # -------------------------------------------------------------------------
    @classmethod
    def __get_fields(cls, trackable):
        """
        Check a trackable for presence of required fields

        @param: the trackable object

        """

        fields = []

        if hasattr(trackable, "fields"):
            keys = trackable.fields
        else:
            keys = trackable

        try:
            if cls.LOCATION_ID in keys:
                fields.append(cls.LOCATION_ID)
            if cls.TRACK_ID in keys:
                fields.append(cls.TRACK_ID)
                return fields
            elif hasattr(trackable, "update_record") or \
                    isinstance(trackable, Table):
                return fields
        except:
            pass
        return None


    # -------------------------------------------------------------------------
    def get_location(self, timestmp=None):
        """
        Get the current location of the instance(s) (at the given time)

        @param timestmp: last datetime for presence (defaults to current time)

        @returns: a location record, or a list of location records (if multiple)

        """

        ptable = self.db[self.PRESENCE]
        ltable = self.db[self.LOCATION]

        if timestmp is None:
            timestmp = datetime.utcnow()

        locations = []
        for r in self.records:
            location = None
            if self.TRACK_ID in r:
                query = ((ptable.deleted == False) &
                         (ptable[self.TRACK_ID] == r[self.TRACK_ID]) &
                         (ptable.timestmp <= timestmp))
                presence = self.db(query).select(orderby=~ptable.timestmp,
                                                 limitby=(0, 1)).first()
                if presence:
                    if presence.interlock:
                        tablename, record = presence.interlock.split(",", 1)
                        trackable = S3Trackable(self.db, tablename, record)
                        record = trackable.records.first()
                        if self.TRACK_ID not in record or \
                           record[self.TRACK_ID] != r[self.TRACK_ID]:
                            location = trackable.get_location(timestmp=timestmp)
                    elif presence.location_id:
                        query = (ltable.id == presence.location_id)
                        location = self.db(query).select(ltable.ALL,
                                                         limitby=(0, 1)).first()

            if not location:
                if len(self.records) > 1:
                    trackable = S3Trackable(self.db, r)
                else:
                    trackable = self
                location = trackable.get_base_location()

            locations.append(location)

        if not locations:
            return None
        elif len(locations) == 1:
            return locations[0]
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

        ptable = self.db[self.PRESENCE]

        if timestmp is None:
            timestmp = datetime.utcnow()

        if isinstance(location, Rows):
            location = location.first()
        if isinstance(location, Row):
            if "location_id" in location:
                location = location.location_id
            elif "base_location" in location:
                location = location.base_location
            else:
                location = location.id

        # @todo: validate the location?

        for r in self.records:
            if self.TRACK_ID not in r:
                # No track ID => set base location
                if len(self.records) > 1:
                    trackable = S3Trackable(r)
                else:
                    trackable = self
                trackable.set_base_location(location)
            elif r[self.TRACK_ID]:
                # Track ID => create new presence entry
                data = dict(location_id=location,
                            timestmp=timestmp)
                data.update({self.TRACK_ID:r[self.TRACK_ID]})
                ptable.insert(**data)


    # -------------------------------------------------------------------------
    def check_in(self, table, record, timestmp=None):
        """
        Bind the presence of the instance(s) to another instance

        @param table: table name of the other resource
        @param record: record in the other resource (as Row or record ID)
        @param timestmp: datetime of the check-in

        @returns: nothing

        """

        ptable = self.db[self.PRESENCE]

        if isinstance(table, str):
            table = self.db[table]
        fields = self.__get_fields(table)
        if not fields:
            raise SyntaxError("No location data in %s" % table._tablename)

        interlock = None
        if isinstance(record, Rows):
            record = record.first()
        if not isinstance(record, Row):
            record = table[record]
        if record and table._id.name in record:
            record = record[table._id.name]
            if record:
                interlock = "%s,%s" % (table, record)
        else:
            raise SyntaxError("No record specified for %s" % table._tablename)

        if interlock:
            if timestmp is None:
                timestmp = datetime.utcnow()
            data = dict(location_id=None,
                        timestmp=timestmp,
                        interlock=interlock)
            q = ((ptable.deleted == False) & (ptable.timestmp <= timestmp))
            for r in self.records:
                if self.TRACK_ID not in r:
                    # Cannot check-in a non-trackable
                    continue
                query = q & (ptable[self.TRACK_ID] == r[self.TRACK_ID])
                presence = self.db(query).select(orderby=~ptable.timestmp,
                                                 limitby=(0, 1)).first()
                if presence and presence.interlock == interlock:
                    # already checked-in to the same instance
                    continue
                data.update({self.TRACK_ID:r[self.TRACK_ID]})
                ptable.insert(**data)


    # -------------------------------------------------------------------------
    def check_out(self, table=None, record=None, timestmp=None):
        """
        Make the last log entry before timestmp independent from
        the referenced entity (if any)

        @param timestmp: the date/time of the check-out, defaults
                         to current time

        """

        ptable = self.db[self.PRESENCE]

        if timestmp is None:
            timestmp = datetime.utcnow()

        interlock = None
        if table is not None:
            if isinstance(table, str):
                table = self.db[table]
            if isinstance(record, Rows):
                record = record.first()
            if isinstance(record, Row) and table._id.name in record:
                record = record[table._id.name]
            if record:
                interlock = "%s,%s" % (table, record)

        q = ((ptable.deleted == False) & (ptable.timestmp <= timestmp))

        for r in self.records:
            if self.TRACK_ID not in r:
                # Cannot check-out a non-trackable
                continue
            query = q & (ptable[self.TRACK_ID] == r[self.TRACK_ID])
            presence = self.db(query).select(orderby=~ptable.timestmp,
                                             limitby=(0, 1)).first()
            if presence and presence.interlock:
                if interlock and presence.interlock != interlock:
                    continue
                elif not interlock and table and \
                     not presence.interlock.startswith("%s" % table):
                    continue
                tablename, record = presence.interlock.split(",", 1)
                trackable = S3Trackable(self.db, tablename, record)
                location = trackable.get_location(timestmp=timestmp)
                if timestmp - presence.timestmp < timedelta(seconds=1):
                    timestmp = timestmp + timedelta(seconds=1)
                data = dict(location_id=location,
                            timestmp=timestmp,
                            interlock=None)
                data.update({self.TRACK_ID:r[self.TRACK_ID]})
                ptable.insert(**data)


    # -------------------------------------------------------------------------
    def remove_location(self, location=None):
        """
        Remove a location from the presence log of the instance(s)

        @todo: implement
        
        """
        raise NotImplementedError


    # -------------------------------------------------------------------------
    def get_base_location(self):
        """
        Get the base location of the instance(s)

        @returns: the base location(s) of the current instance

        """

        ltable = self.db[self.LOCATION]

        locations = []
        for r in self.records:
            location = None
            query = None
            if self.LOCATION_ID in r:
                query = (ltable.id == r[self.LOCATION_ID])
            elif self.TRACK_ID in r:
                q = (self.table[self.TRACK_ID] == r[self.TRACK_ID])
                trackable = self.db(q).select(limitby=(0, 1)).first()
                table = self.db[trackable.instance_type]
                if self.LOCATION_ID in table.fields:
                    query = ((table[self.TRACK_ID] == r[self.TRACK_ID]) &
                             (table[self.LOCATION_ID] == ltable.id))
            if query:
                location = self.db(query).select(ltable.ALL,
                                                 limitby=(0, 1)).first()
            if location:
                locations.append(location)

        if not locations:
            return None
        elif len(locations) == 1:
            return locations[0]
        else:
            return locations


    # -------------------------------------------------------------------------
    def set_base_location(self, location=None):
        """
        Set the base location of the instance(s)

        @param location: the location for the base location as Row or record ID

        @returns: nothing

        @note: instance tables without a location_id field will be ignored

        """

        if isinstance(location, Rows):
            location = location.first()
        if isinstance(location, Row):
            location = location.id

        if not location:
            return
        else:
            # @todo: validate location?
            data = {self.LOCATION_ID:location}

        # Update records without track ID
        for r in self.records:
            if self.TRACK_ID in r:
                continue
            elif self.LOCATION_ID in r and hasattr(r, "update_record"):
                r.update_record(**data)

        # Update records with track ID
        # => this can happen table-wise = less queries
        track_ids = [r[self.TRACK_ID] for r in self.records
                                      if self.TRACK_ID in r]
        rows = self.db(self.table[self.TRACK_ID].belongs(track_ids)).select()
        tables = []
        for r in rows:
            instance_type = r.instance_type
            table = db[instance_type]
            if instance_type not in tables and \
               self.LOCATION_ID in table.fields:
                   tables.append(table)
            else:
                # No location ID in this type => ignore gracefully
                continue

        # Location specified => update all base locations
        for table in tables:
            self.db(table[self.TRACK_ID].belongs(track_ids)).update(**data)


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
    def get_all(self, entity,
                location=None,
                bbox=None,
                timestmp=None):
        """
        Get all instances of the given entity at the given location and time

        """
        raise NotImplementedError


    # -------------------------------------------------------------------------
    def get_checked_in(self, table, record,
                       instance_type=None,
                       timestmp=None):
        """
        Get all trackables of the given type that are checked-in
        to the given instance at the given time

        """
        raise NotImplementedError


# =============================================================================
