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

__all__ = ['IS_LAT', 'IS_LON', 'THIS_NOT_IN_DB', 'IS_UTC_DATETIME']

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

class IS_UTC_DATETIME(object):
    """
    example::

        INPUT(_type='text', _name='name', requires=IS_DATETIME())

    datetime has to be in the ISO8960 format YYYY-MM-DD hh:mm:ss
    """

    isodatetime = '%Y-%m-%d %H:%M:%S'
    
    def __init__(self,
        format='%Y-%m-%d %H:%M:%S',
        error_message='must be YYYY-MM-DD HH:MM:SS!',
        utc_offset=None,
        allow_future=True,
        max_future=900
        ):

        self.format = format
        self.error_message = error_message

        if utc_offset or utc_offset==0:
            self.utc_offset = utc_offset
        else:
            if time.daylight:
                self.utc_offset = -time.altzone
            else:
                self.utc_offset = -time.timezone

        self.allow_future = allow_future        # Future datetime allowed?
        self.max_future = max_future            # Max acceptable future in seconds

    def __call__(self,value):
        (y,m,d,hh,mm,ss,t0,t1,t2) = time.strptime(value, str(self.format))
        ivalue = datetime(y,m,d,hh,mm,ss)

        try:
            if self.allow_future:
                value = ivalue
            else:
                latest = datetime.utcnow() + timedelta(seconds=self.max_future)
                value = ivalue - timedelta(seconds=self.utc_offset)
                if value > latest:
                    self.error_message='future times not allowed!'
                    return (value, self.error_message)
        except:
            self.error_message='must be YYYY-MM-DD HH:MM:SS!'
            return(value, self.error_message)

        return (value, None)

    def formatter(self, value):
        return value.strftime(str(self.format))

