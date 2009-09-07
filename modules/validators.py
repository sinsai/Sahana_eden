# -*- coding: utf-8 -*-

"""
This file was developed by Fran Boon as a web2py extension.
"""

#import os, re, copy, sys, types, datetime, time, cgi, hmac
#try: 
#    import hashlib
#    have_hashlib = True
#except:
#    import sha, md5
#    have_hashlib = False
#from gluon.storage import Storage

import time
from datetime import datetime, timedelta

__all__ = ['IS_LAT', 'IS_LON', 'THIS_NOT_IN_DB', 'IS_UTC_OFFSET', 'IS_UTC_DATETIME', 'IS_ONE_OF']

class IS_LAT(object):
    """
    example:

    INPUT(_type='text', _name='name', requires=IS_LAT())

    latitude has to be in degrees between -90 & 90
    """
    def __init__(self, 
            error_message = 'Latitude/Northing should be between -90 & 90!'):
        self.minimum = -90
        self.maximum = 90
        self.error_message = error_message
    def __call__(self, value):
        try:
            value = float(value)
            if self.minimum <= value <= self.maximum:
                return (value, None)
        except ValueError:
            pass
        return (value, self.error_message)

class IS_LON(object):
    """
    example:

    INPUT(_type='text', _name='name' ,requires=IS_LON())

    longitude has to be in degrees between -180 & 180
    """
    def __init__(self, 
            error_message = 'Longitude/Easting should be between -180 & 180!'):
        self.minimum = -180
        self.maximum = 180
        self.error_message = error_message
    def __call__(self, value):
        try:
            value = float(value)
            if self.minimum <= value <= self.maximum:
                return (value, None)
        except ValueError:
            pass
        return (value, self.error_message)

class THIS_NOT_IN_DB(object):
    """
    Unused currently since doesn't quite work.
    See: http://groups.google.com/group/web2py/browse_thread/thread/27b14433976c0540
    """
    def __init__(self, dbset, field, this,
            error_message = 'value already in database!'):
        if hasattr(dbset, 'define_table'):
            self.dbset = dbset()
        else:
            self.dbset = dbset
        self.field = field
        self.value = this
        self.error_message = error_message
        self.record_id = 0
    def set_self_id(self, id):
        self.record_id = id
    def __call__(self, value):
        tablename, fieldname = str(self.field).split('.')
        field = self.dbset._db[tablename][fieldname]
        rows = self.dbset(field==self.value).select(limitby=(0, 1))
        if len(rows)>0 and str(rows[0].id) != str(self.record_id):
            return (self.value, self.error_message)
        return (value, None)

# IS_ONE_OF -------------------------------------------------------------------
# added 2009-08-23 by nursix
#
class IS_ONE_OF(object):
    """
        Filtered version of IS_IN_DB():

        validates a given value as key of another table, filtered by the 'filterby'
        field for one of the 'filter_opts' options (=a selective IS_IN_DB())

        For the dropdown representation:

        'represent' can be a string template for the record, or a set of field
        names of the fields to be used as option labels, or a function or lambda
        to create an option label from the respective record (which has to return
        a string, of course)
    """

    def __init__(
        self,
        dbset,
        field,
        represent=None,
        filterby=None,
        filter_opts=None,
        error_message='invalid value!',
        multiple=False
        ):

        self.error_message = error_message

        self.field = field
        (ktable, kfield) = str(self.field).split('.')

        self.ktable = ktable

        if not kfield or not len(kfield):
            self.kfield = 'id'
        else:
            self.kfield = kfield

        self.represent = represent or ('%%(%s)s' % self.kfield)

        self.filterby = filterby
        self.filter_opts = filter_opts

        self.error_message = error_message

        self.multiple = False # ignore multiple

        if hasattr(dbset, 'define_table'):
            self.dbset = dbset()
        else:
            self.dbset = dbset

    def options(self):

        if self.ktable in self.dbset._db:

            _table = self.dbset._db[self.ktable]

            if 'deleted' in _table:
                query = ((_table['deleted']==False) | (_table['deleted']==None))
            else:
                query = (_table['id'])

            if self.filterby and self.filterby in _table:
                if self.filter_opts:
                    query = (_table[self.filterby].belongs(self.filter_opts)) & query
                records = self.dbset(query).select(orderby=_table[self.filterby])
            else:
                records = self.dbset(query).select()

            set = []
            for r in records:
                try:
                    set.append((r[self.kfield], self.represent(r)))
                except TypeError:
                    if isinstance(self.represent, str):
                        set.append((r[self.kfield], self.represent %dict(r)))
                    elif isinstance(self.represent, (list,tuple)):
                        _label = ""
                        for l in self.represent:
                            if l in r:
                                _label = '%s %s' % ( _label, r[l] )
                        set.append((r[self.kfield],  _label))
                    elif 'name' in _table:
                        set.append((r[self.kfield], r.name))
                    else:
                        set.append(( r[self.kfield], r[self.kfield] ))

            return( set )

        else:
            return None

    def __call__(self,value):

        try:
            _table = self.dbset._db[self.ktable]

            query = (_table[self.kfield]==value)

            if 'deleted' in _table:
                query = ((_table['deleted']==False) | (_table['deleted']==None)) & query

            if self.filterby and self.filterby in _table:
                if self.filter_opts:
                    query = (_table[self.filterby].belongs(self.filter_opts)) & query

            if self.dbset(query).count():
                return (value, None)

        except:
            pass

        return (value, self.error_message)

# IS_UTC_OFFSET ---------------------------------------------------------------
# added 2009-08-20 by nursix
#
class IS_UTC_OFFSET(object):
    """
    validates a given string value as UTC offset in the format +/-HHMM

    Note: all leading parts of the string (before the trailing offset specification)
    will be ignored and replaced by 'UTC ' in the return value, if the string passes
    through.
    """

    def __init__(self,
        error_message='invalid UTC offset!'
        ):
        self.error_message = error_message

    @staticmethod
    def get_offset_value(offset_str):
        if offset_str and len(offset_str)>=5 and \
            (offset_str[-5]=='+' or offset_str[-5]=='-') and \
            offset_str[-4:].isdigit():
            offset_hrs = int(offset_str[-5]+offset_str[-4:-2])
            offset_min = int(offset_str[-5]+offset_str[-2:])
            offset = 3600*offset_hrs + 60*offset_min
            return offset
        else:
            return None

    def __call__(self,value):

        if value and isinstance(value, str):
            _offset_str = value.strip()

            offset = self.get_offset_value(_offset_str)

            if offset and offset>-86340 and offset <86340:
                # Add a leading 'UTC ',
                # otherwise leading '+' and '0' will be stripped away by web2py
                return ('UTC '+_offset_str[-5:], None)

        return (value, self.error_message)

# IS_UTC_DATETIME -------------------------------------------------------------
# added 2009-08-19 by nursix
#
class IS_UTC_DATETIME(object):
    """
    validates a given value as datetime string and returns the corresponding UTC datetime

    example:

        INPUT(_type='text', _name='name', requires=IS_UTC_DATETIME())

    datetime has to be in the ISO8960 format YYYY-MM-DD hh:mm:ss, with an optional
    trailing UTC offset specified as +/-HHMM (+ for eastern, - for western timezones)

    optional parameters:
        format              str         strptime/strftime format template string, for
                                        directives refer to your strptime implementation

        error_message       str         error message to be returned

        utc_offset          integer     offset to UTC in seconds,
                                        if not specified, the value is considered to be UTC

        allow_future        boolean     whether future date/times are allowed or not, if
                                        set to False, all date/times beyond now+max_future
                                        will fail

        max_future          integer     the maximum acceptable future time interval in seconds
                                        from now for unsynchronized local clocks
    """

    isodatetime = '%Y-%m-%d %H:%M:%S'

    def __init__(self,
        format='%Y-%m-%d %H:%M:%S',
        error_message='must be YYYY-MM-DD HH:MM:SS (+/-HHMM)!',
        utc_offset=None,
        allow_future=True,
        max_future=900
        ):

        self.format = format
        self.error_message = error_message

        validate = IS_UTC_OFFSET()
        offset, error = validate(utc_offset)

        if error:
            self.utc_offset = 'UTC +0000' # fallback to UTC
        else:
            self.utc_offset = offset

        self.allow_future = allow_future
        self.max_future = max_future

    def __call__(self,value):

        try:
            _dtstr = value.strip()

            if len(_dtstr)>6 and \
                (_dtstr[-6:-4]==' +' or _dtstr[-6:-4]==' -') and \
                _dtstr[-4:].isdigit():
                # UTC offset specified in dtstr
                dtstr = _dtstr[0:-6]
                _offset_str = _dtstr[-5:]
            else:
                # use default UTC offset
                dtstr = _dtstr
                _offset_str = self.utc_offset

            offset_hrs = int(_offset_str[-5]+_offset_str[-4:-2])
            offset_min = int(_offset_str[-5]+_offset_str[-2:])
            offset = 3600*offset_hrs + 60*offset_min

            # Offset must be in range -1439 to +1439 minutes
            if offset<-86340 or offset >86340:
                self.error_message='invalid UTC offset!'
                return (dt, self.error_message)

            (y,m,d,hh,mm,ss,t0,t1,t2) = time.strptime(dtstr, str(self.format))
            dt = datetime(y,m,d,hh,mm,ss)

            if self.allow_future:
                return (dt, None)
            else:
                latest = datetime.utcnow() + timedelta(seconds=self.max_future)
                dt_utc = dt - timedelta(seconds=offset)
                if dt_utc > latest:
                    self.error_message='future times not allowed!'
                    return (dt_utc, self.error_message)
                else:
                    return (dt_utc, None)
        except:
            self.error_message='must be YYYY-MM-DD HH:MM:SS (+/-HHMM)!'
            return(value, self.error_message)

    def formatter(self, value):
        # Always format with trailing UTC offset
        return value.strftime(str(self.format))+' +0000'
