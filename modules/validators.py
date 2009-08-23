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

__all__ = ['IS_LAT', 'IS_LON', 'THIS_NOT_IN_DB', 'IS_UNIT']

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

#added by Dominic König

class IS_UNIT(object):

    def __init__(
        self,
        dbset,
        filter_opts=None,
        error_message='not a unit!',
        multiple=False
        ):
        self.error_message = error_message
        self.filter_opts = filter_opts
        self.multiple = multiple

        if hasattr(dbset, 'define_table'):
            self.dbset = dbset()
        else:
            self.dbset = dbset

    def options(self):
        query = self.dbset._db['lms_unit']['deleted']==False
        if self.filter_opts:
            query = (self.dbset._db['lms_unit']['opt_lms_unit_type'].belongs(self.filter_opts)) & query
        records = self.dbset(query).select(orderby=self.dbset._db['lms_unit'].opt_lms_unit_type)
        set = []
        for r in records:
            set.append((r.id, r.label+' '+r.name))
        return( set )

    def __call__(self,value):
        try:
            query = self.dbset._db['lms_unit']['deleted']==False
            if self.filter_opts:
                query = (self.dbset._db['lms_unit']['opt_lms_unit_type'].belongs(self.filter_opts)) & query
            if self.dbset(query).count():
                return (value, None)
            else:
                pass
        except ValueError:
            pass
        return (value, self.error_message)
	