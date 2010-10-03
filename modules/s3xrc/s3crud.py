# -*- coding: utf-8 -*-

""" S3XRC Resource Framework - CRUD method handlers

    @see: U{B{I{S3XRC-2}} <http://eden.sahanafoundation.org/wiki/S3XRC>} on Eden wiki

    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

    @author: nursix
    @contact: dominic AT nursix DOT org
    @copyright: 2009-2010 (c) Sahana Software Foundation
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

__all__ = ["S3MethodHandler"]

import datetime

from gluon.storage import Storage
from gluon.html import URL
from gluon.http import HTTP, redirect
from gluon.serializers import json

from gluon.sql import Field, Row
from gluon.sqlhtml import SQLTABLE, SQLFORM

# *****************************************************************************
class S3Audit(object):

    """ Audit Trail Writer Class """

    # -------------------------------------------------------------------------
    def __init__(self, db, session,
                 tablename="s3_audit",
                 migrate=True):

        self.db = db
        self.table = db.get(tablename, None)
        if not self.table:
            self.table = db.define_table(tablename,
                            Field("timestmp", "datetime"),
                            Field("person", "integer"),
                            Field("operation"),
                            Field("tablename"),
                            Field("record", "integer"),
                            Field("representation"),
                            Field("old_value", "text"),
                            Field("new_value", "text"),
                            migrate=migrate)

        self.session = session

        if session.auth and session.auth.user:
            self.user = session.auth.user.id
        else:
            self.user = None


    # -------------------------------------------------------------------------
    def __call__(self, operation, prefix, name,
                 form=None,
                 record=None,
                 representation=None):

        now = datetime.datetime.utcnow()

        audit = self.session.s3
        table = self.table
        db = self.db

        if record:
            if isinstance(record, Row):
                record = record.get("id", None)
                if not record:
                    return True
            try:
                record = int(record)
            except ValueError:
                record = None
        else:
            record = None

        #print "Audit: %s on %s_%s #%s" % (operation, prefix, name, record or 0)

        tablename = "%s_%s" % (prefix, name)

        if operation in ("list", "read"):
            if audit.audit_read:
                table.insert(timestmp = now,
                             person = self.user,
                             operation = operation,
                             tablename = tablename,
                             record = record,
                             representation = representation)

        elif operation in ("create", "update"):
            if audit.audit_write:
                if form:
                    record =  form.vars.id
                    new_value = ["%s:%s" % (var, str(form.vars[var])) for var in form.vars]
                else:
                    new_value = []
                table.insert(timestmp = now,
                             person = self.user,
                             operation = operation,
                             tablename = tablename,
                             record = record,
                             representation = representation,
                             new_value = new_value)

        elif operation == "delete":
            if audit.audit_write:

                row = db(db[tablename].id == record).select(limitby=(0, 1)).first()
                old_value = []
                if row:
                    old_value = ["%s:%s" % (field, row[field]) for field in row]
                table.insert(timestmp = now,
                             person = self.user,
                             operation = operation,
                             tablename = tablename,
                             record = record,
                             representation = representation,
                             old_value = old_value)

        return True


# *****************************************************************************
class S3MethodHandler(object):

    """ REST Method Handler Base Class """

    # -------------------------------------------------------------------------
    def __init__(self, db):

        """ Constructor """

        self.db = db

        self.next = None

    # -------------------------------------------------------------------------
    def __call__(self, r, **attr):

        """ Caller, invoked by REST interface """

        # Get the environment
        self.request = r.request
        self.session = r.session
        self.response = r.response

        # Get the right table
        self.prefix, self.name, self.table, self.tablename = r.target()
        if r.component:
            self.record = r.component_id
            component = r.resource.components.get(r.component_name, None)
            self.resource = component.resource
        else:
            self.record = r.id
            self.resource = r.resource

        # Invoke the responder
        output = self.respond(r, **attr)

        # Redirection to next
        r.next = self.next

        # Done
        return output


    # -------------------------------------------------------------------------
    def respond(self, r, **attr):

        """ Responder, to be implemented in subclass """

        output = dict()

        return output


    # -------------------------------------------------------------------------
    def callback(self, hook, *args, **vars):

        name = vars.pop("name", None)

        if name and isinstance(hook, dict):
            hook = hook.get(name, None)

        if hook:
            if isinstance(hook, (list, tuple)):
                result = [f(*args, **vars) for f in hook]
            else:
                result = hook(*args, **vars)
            return result
        else:
            return None


# *****************************************************************************
class S3CRUDHandler(S3MethodHandler):

    """ Interactive CRUD Method Handler Base Class """

    def respond(self, r, **attr):

        output = dict()

        return output


    # -------------------------------------------------------------------------
    #def _create(self, table):

    # -------------------------------------------------------------------------
    #def _read(self, table, record):

    # -------------------------------------------------------------------------
    #def _update(self, table, record):

    # -------------------------------------------------------------------------
    #def _delete(self, table, record):

    # -------------------------------------------------------------------------
    #def _list(self, table, query=None):

# *****************************************************************************
