# -*- coding: utf-8 -*-

""" RESTful Record Merger

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/BluePrintRecordMerger>}
    @status: work in progress

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

__all__ = ["S3RecordMerger"]

import datetime, os, sys

from gluon.storage import Storage
from gluon.html import *
from gluon.http import HTTP, redirect
from gluon.serializers import json
from gluon.sql import Field, Row
from gluon.validators import IS_EMPTY_OR
from gluon.tools import callback

from s3rest import S3Method
from s3crud import S3CRUD

from gluon.sqlhtml import SQLFORM
from s3tools import SQLTABLES3

# *****************************************************************************
class S3RecordMerger(S3CRUD):
    """
    Interactive Record Merger

    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
        Apply method

        @param r: the S3Request
        @param attr: dictionary of parameters for the method handler

        @returns: output object to send to the view

        """

        self.settings = self.manager.s3.crud

        # Environment
        db = self.db
        session = self.manager.session
        request = self.manager.request
        response = self.manager.response

        # Get the CRUD settings
        audit = self.manager.audit
        settings = self.settings

        output = dict()
        resource = self.resource
        table = self.table

        if r.interactive and r.record:

            # Check if there's an ID field in this resource
            if not "id" in self.table.fields:
                r.error(501, self.manager.ERROR.BAD_RESOURCE)

            merge_id = r.record.id

            # Get/check the merge source
            vars =r.request.get_vars
            source_id = vars.get("from", None)
            if not source_id or not source_id.isdigit():
                # Need a source record ID
                r.error(501, self.manager.ERROR.BAD_RECORD)

            source = db(table.id==source_id).select(table.ALL,
                                                    limitby=(0, 1)).first()
            if not source:
                r.error(501, self.manager.ERROR.BAD_RECORD)

            # Generate form
            form = self.merge_form(merge_id, source)

            # Process form
            pass

            output.update(form=form)

        elif r.interactive:
            # Need a primary record
            r.error(501, self.manager.ERROR.BAD_RECORD)

        else:
            # Non-interactive formats not allowed
            r.error(501, self.manager.ERROR.BAD_FORMAT)

        self.response.view = self._view(r, "merge.html")
        print response.view
        return output

    # -------------------------------------------------------------------------
    def merge_form(self,
                   merge_id,
                   source,
                   onvalidation=None,
                   onaccept=None,
                   message="Records merged",
                   format=None):
        """
        DRY helper function for SQLFORM in Merge

        """

        # Environment
        db = self.db
        session = self.manager.session
        request = self.manager.request
        response = self.manager.response

        # Get the CRUD settings
        audit = self.manager.audit
        settings = self.settings

        # Table and model
        prefix = self.prefix
        name = self.name
        tablename = self.tablename
        table = self.table
        model = self.manager.model

        record = None
        labels = None

        # Add asterisk to labels of required fields
        labels = Storage()
        mark_required = self._config("mark_required")
        response.s3.has_required = False
        for field in table:
            if field.writable:
                required = field.required or \
                        field.notnull or \
                        mark_required and field.name in mark_required
                validators = field.requires
                if not validators and not required:
                    continue
                if not required:
                    if not isinstance(validators, (list, tuple)):
                        validators = [validators]
                    for v in validators:
                        if hasattr(v, "options"):
                            if hasattr(v, "zero") and v.zero is None:
                                continue
                        val, error = v("")
                        if error:
                            required = True
                            break
                if required:
                    response.s3.has_required = True
                    labels[field.name] = DIV("%s:" % field.label,
                                                SPAN(" *", _class="req"))

        for f in source:
            row = self.db(table.id==merge_id).select(limitby=(0, 1)).first()
            if f in row.keys():
                print f
                if table[f].represent is not None:
                    value = table[f].represent(source[f])
                else:
                    value = str(source[f])
                comment = DIV(INPUT(_type="hidden", _value=row[f]), value)

        # Get formstyle from settings
        formstyle = self.settings.formstyle

        # Get the form
        form = SQLFORM(table,
                       record = merge_id,
                       col3 = dict(), # using this for the copy button+merge data
                       deletable = False,
                       showid = False,
                       upload = self.download_url,
                       labels = labels,
                       formstyle = formstyle,
                       submit_button = self.settings.submit_button)

        # Process the form
        logged = False

        # Set form name
        formname = "%s/%s" % (self.tablename, form.record_id)

        # Get the proper onvalidation routine
        if isinstance(onvalidation, dict):
            onvalidation = onvalidation.get(self.tablename, [])

        if form.accepts(request.post_vars,
                        session,
                        formname=formname,
                        onvalidation=onvalidation,
                        keepvalues=False,
                        hideerror=False):

            # Message
            response.flash = message

            # Audit
            if merge_id is None:
                audit("create", prefix, name, form=form,
                      representation=format)
            else:
                audit("update", prefix, name, form=form,
                      record=merge_id, representation=format)
            logged = True

            # Update super entity links
            model.update_super(table, form.vars)

            # Store session vars
            if form.vars.id:
                if record_id is None:
                    self.manager.auth.s3_make_session_owner(table, form.vars.id)
                self.resource.lastid = str(form.vars.id)
                self.manager.store_session(prefix, name, form.vars.id)

            # Execute onaccept
            callback(onaccept, form, tablename=tablename)

        if not logged and not form.errors:
            audit("read", prefix, name, record=merge_id, representation=format)

        return form

# END
# *****************************************************************************
