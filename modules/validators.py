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

__all__ = ['IS_LAT', 'IS_LON', 'THIS_NOT_IN_DB', 'IS_PE_ID']

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

#
# VITA special validators -----------------------------------------------------
#

class IS_PE_ID(object):

    def __init__(
        self,
        dbset,
        class_opts=None,
        filter_opts=None,
        error_message='not a person entity!',
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
