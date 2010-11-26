# -*- coding: utf-8 -*-

""" S3XRC Resource Framework - CRUD Method Handlers

    @version: 2.2.6

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

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

__all__ = ["S3Audit",
           "S3MethodHandler",
           "S3CRUDHandler",
           "S3SearchSimple"]

import datetime, os, sys

from gluon.storage import Storage
from gluon.html import URL, DIV, A, SCRIPT, FORM, TABLE, TR, TD, INPUT
from gluon.http import HTTP, redirect
from gluon.serializers import json
from gluon.sql import Field, Row
from gluon.validators import IS_EMPTY_OR

from s3import import S3Importer
from s3export import S3Exporter

# *****************************************************************************
class S3Audit(object):

    """ Audit Trail Writer Class

        @param db: the database
        @param session: the current session
        @param tablename: the name of the audit table
        @param migrate: migration setting

    """

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
                 representation="unknown"):

        """ Caller

            @param operation: Operation to log, one of
                "create", "update", "read", "list" or "delete"
            @param prefix: the module prefix of the resource
            @param name: the name of the resource (without prefix)
            @param form: the form
            @param record: the record ID
            @param representation: the representation format

        """

        settings = self.session.s3

        now = datetime.datetime.utcnow()
        db = self.db
        table = self.table
        tablename = "%s_%s" % (prefix, name)

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

        if operation in ("list", "read"):
            if settings.audit_read:
                table.insert(timestmp = now,
                             person = self.user,
                             operation = operation,
                             tablename = tablename,
                             record = record,
                             representation = representation)

        elif operation in ("create", "update"):
            if settings.audit_write:
                if form:
                    record =  form.vars.id
                    new_value = ["%s:%s" % (var, str(form.vars[var]))
                                 for var in form.vars]
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
            if settings.audit_write:

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

    """ REST Method Handler Base Class

        @param manager: the resource controller
        @type manager: S3ResourceController

    """

    def __init__(self, manager):

        self.manager = manager
        self.db = manager.db
        self.T = manager.T

        self.session = manager.session
        self.request = manager.request
        self.response = manager.response

        self.permit = manager.auth.shn_has_permission

        self.next = None


    # -------------------------------------------------------------------------
    def __call__(self, r, method=None, **attr):

        """ Caller, invoked by REST interface

            @param r: the S3Request
            @param method: the method established by the REST interface
            @param attr: dict of parameters for the method handler

            @returns: output object to send to the view

        """

        # Settings
        self.download_url = self.manager.download_url

        # Get the right table and method
        self.prefix, self.name, self.table, self.tablename = r.target()

        # Override request method
        if method is not None:
            self.method = method
        else:
            self.method = r.method
        if r.component:
            self.record = r.component_id
            component = r.resource.components.get(r.component_name, None)
            self.resource = component.resource
            if not self.method:
                if r.multiple and not r.component_id:
                    self.method = "list"
                else:
                    self.method = "read"
        else:
            self.record = r.id
            self.resource = r.resource
            if not self.method:
                if r.id or r.method in ("read", "display"):
                    self.method = "read"
                else:
                    self.method = "list"

        # Invoke the responder
        output = self.respond(r, **attr)

        # Redirection
        if self.next and self.resource.lastid:
            self.next = str(self.next)
            placeholder = "%5Bid%5D"
            self.next = self.next.replace(placeholder, self.resource.lastid)
            placeholder = "[id]"
            self.next = self.next.replace(placeholder, self.resource.lastid)
        r.next = self.next

        # Add additional view variables
        self._extend_view(output, r, **attr)

        return output


    # -------------------------------------------------------------------------
    def respond(self, r, **attr):

        """ Responder stub, to be overloaded in subclass

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @returns: output object to send to the view

        """

        output = dict()
        return output


    # Utilities ===============================================================

    @staticmethod
    def _record_id(r):

        """ Get the ID of the target record of a S3Request

            @param r: the S3Request

        """

        if r.component:
            if r.multiple and not r.component_id:
                return None
            resource = r.resource.components.get(r.component_name).resource
            resource.load(start=0, limit=1)
            if len(resource):
                return resource.records().first().id
        else:
            return r.id

        return None


    # -------------------------------------------------------------------------
    def _config(self, key, default=None):

        """ Get a configuration setting of the current table

            @param key: the setting key
            @param default: the default value

        """

        return self.manager.model.get_config(self.table, key, default)


    # -------------------------------------------------------------------------
    @staticmethod
    def _view(r, default, format=None):

        """ Get the path to the view template file

            @param r: the S3Request
            @param default: name of the default view template file
            @param format: format string (optional)

        """

        request = r.request
        folder = request.folder
        prefix = request.controller

        if r.component:
            view = "%s_%s_%s" % (r.name, r.component_name, default)
            path = os.path.join(folder, "views", prefix, view)
            if os.path.exists(path):
                return "%s/%s" % (prefix, view)
            else:
                view = "%s_%s" % (r.name, default)
                path = os.path.join(folder, "views", prefix, view)
        else:
            if format:
                view = "%s_%s_%s" % (r.name, default, format)
            else:
                view = "%s_%s" % (r.name, default)
            path = os.path.join(folder, "views", prefix, view)

        if os.path.exists(path):
            return "%s/%s" % (prefix, view)
        else:
            if format:
                return default.replace(".html", "_%s.html" % format)
            else:
                return default


    # -------------------------------------------------------------------------
    @staticmethod
    def _extend_view(output, r, **attr):

        """ Add additional view variables (invokes all callables)

            @param output: the output dict
            @param r: the S3Request
            @param attr: the view variables

            @note: overload this method in subclasses if you don't want
                   additional view variables to be added automatically

        """

        if r.interactive and isinstance(output, dict):
            for key in attr:
                handler = attr[key]
                if callable(handler):
                    resolve = True
                    try:
                        display = handler(r)
                    except:
                        continue
                else:
                    display = handler
                if isinstance(display, dict) and resolve:
                    output.update(**display)
                elif display is not None:
                    output.update(**{key:display})
                elif key in output:
                    del output[key]


# *****************************************************************************
class S3CRUDHandler(S3MethodHandler):

    """ Interactive CRUD Method Handler """

    # -------------------------------------------------------------------------
    def respond(self, r, **attr):

        """ Responder

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @returns: output object to send to the view

        """

        self.settings = self.manager.s3.crud

        if r.http == "DELETE" or self.method == "delete":
            output = self.delete(r, **attr)
        elif self.method == "create":
            output = self.create(r, **attr)
        elif self.method == "read":
            output = self.read(r, **attr)
        elif self.method == "update":
            output = self.update(r, **attr)
        elif self.method == "list":
            output = self.select(r, **attr)
        else:
            r.error(501, self.manager.ERROR.BAD_METHOD)

        return output


    # -------------------------------------------------------------------------
    def create(self, r, **attr):

        """ Create new records

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @todo 2.3: plain representation

        """

        T = self.manager.T

        session = self.session
        request = self.request
        response = self.response

        table = self.table
        tablename = self.tablename
        representation = r.representation

        output = dict()

        # Get table configuration
        insertable = self._config("insertable", True)
        if not insertable:
            if r.method is not None:
                r.error(400, self.resource.ERROR.BAD_METHOD)
            else:
                return dict(form=None)

        # Check permission for create
        authorised = self.permit("create", self.tablename)
        if not authorised:
            if r.method is not None:
                r.unauthorised()
            else:
                return dict(form=None)

        # Get callbacks
        onvalidation = self._config("create_onvalidation") or \
                       self._config("onvalidation")
        onaccept = self._config("create_onaccept") or \
                   self._config("onaccept")

        if r.interactive:

            # Form configuration
            create_next = self._config("create_next")
            subheadings = self._config("subheadings")

            # Set view
            if representation in ("popup", "iframe"):
                response.view = self._view(r, "popup.html")
                output.update(caller=request.vars.caller)
            else:
                response.view = self._view(r, "create.html")

            # Title and subtitle
            if r.component:
                title = self.crud_string(r.tablename, "title_display")
                subtitle = self.crud_string(self.tablename, "subtitle_create")
                output.update(title=title, subtitle=subtitle)
            else:
                title = self.crud_string(self.tablename, "title_create")
                output.update(title=title)

            # Component join
            if r.component:
                table[r.fkey].comment = None
                table[r.fkey].default = r.record[r.pkey]
                if r.http == "POST":
                    table[r.fkey].writable = True
                    r.request.post_vars.update({r.fkey: str(r.record[r.pkey])})
                else:
                    table[r.fkey].readable = False
                    table[r.fkey].writable = False

            # Copy record
            from_table = None
            from_record = r.request.get_vars.get("from_record", None)
            map_fields = r.request.get_vars.get("from_fields", None)

            if from_record:
                del r.request.get_vars["from_record"] # forget it
                if from_record.find(".") != -1:
                    from_table, from_record = from_record.split(".", 1)
                    from_table = self.db.get(from_table, None)
                    if not from_table:
                        r.error(404, self.resource.ERROR.BAD_RESOURCE)
                else:
                    from_table = table
                authorised = self.permit("read",
                                         from_table._tablename,
                                         from_record)
                if not authorised:
                    r.unauthorised()
                if map_fields:
                    del r.request.get_vars["from_fields"]
                    if map_fields.find("$") != -1:
                        mf = map_fields.split(",")
                        mf = [f.find("$") != -1 and f.split("$") or \
                             [f, f] for f in mf]
                        map_fields = Storage(mf)
                    else:
                        map_fields = map_fields.split(",")

            # Link record
            link = None
            _vars = r.request.get_vars
            for k in _vars:
                if k[:5] == "link.":
                    cmd = k.split(".")
                    if len(cmd) > 2:
                        linkdir = cmd[1]
                        linktable = self.db.get(cmd[2], None)
                        linkid = _vars[k].split(",")
                        del _vars[k] # forget it
                        if linkid and not linkid[0].isdigit():
                            linkclass = linkid.pop(0)
                        else:
                            linkclass = None
                        if linktable and linkid:
                            link = Storage(linkdir=linkdir,
                                           linktable=linktable,
                                           linkclass=linkclass,
                                           linkid=linkid)
                    break

            # Success message
            message = self.crud_string(self.tablename, "msg_record_created")

            # Get the form
            if "id" in request.post_vars:

                # Copy formkey if un-deleting a duplicate
                original = str(request.post_vars.id)
                formkey = session.get("_formkey[%s/None]" % tablename)
                formname = "%s/%s" % (tablename, original)
                session["_formkey[%s]" % formname] = formkey
                if "deleted" in table:
                    table.deleted.writable = True
                    request.post_vars.update(deleted=False)
                request.post_vars.update(_formname=formname, id=original)
                request.vars.update(**request.post_vars)

                form = self.resource.update(original,
                                            message=message,
                                            onvalidation=onvalidation,
                                            onaccept=onaccept,
                                            link=link,
                                            download_url=self.download_url,
                                            format=representation)

            else:
                form = self.resource.create(onvalidation=onvalidation,
                                            onaccept=onaccept,
                                            message=message,
                                            from_table=from_table,
                                            from_record=from_record,
                                            map_fields=map_fields,
                                            link=link,
                                            download_url=self.download_url,
                                            format=representation)

            # Insert subheadings
            if subheadings:
                self.insert_subheadings(form, tablename, subheadings)

            # Cancel button?
            if response.s3.cancel:
                form[0][-1][1].append(INPUT(_type="button",
                                            _value=T("Cancel"),
                                            _onclick="window.location='%s';" %
                                                     response.s3.cancel))

            # Navigate-away confirmation
            if self.settings.navigate_away_confirm:
                form.append(SCRIPT("EnableNavigateAwayConfirm();"))

            # Put the form into output
            output.update(form=form)

            # Add map
            location_id = [f for f in table if f.writable and
                           str(f.type) == "reference gis_location"]
            if location_id:
                response.s3.gis.location_id = True
                if response.s3.gis.map_selector:
                    _map = self.manager.gis.form_map(r, method="create")
                    output.update(_map=_map)

            # Buttons
            buttons = self.insert_buttons(r, "list")
            if buttons:
                output.update(buttons)

            # Redirection
            if representation in ("popup", "iframe"):
                self.next = None
            elif not create_next:
                #self.next = r.there(representation=representation)
                self.next = self.resource.url(id=[])
            else:
                try:
                    self.next = create_next(self)
                except TypeError:
                    self.next = create_next

        #elif representation == "plain":
            #if onaccept:
                #_onaccept = lambda form: \
                            #s3xrc.audit("create", prefix, name, form=form,
                                        #representation=representation) and \
                            #onaccept(form)
            #else:
                #_onaccept = lambda form: \
                            #s3xrc.audit("create", prefix, name, form=form,
                                        #representation=representation)

            #form = crud.create(table,
                            #onvalidation=onvalidation, onaccept=_onaccept)

            #if deployment_settings.get_ui_navigate_away_confirm():
                #form.append( SCRIPT ("EnableNavigateAwayConfirm();") )

            #response.view = "plain.html"
            #return dict(item=form)

        elif representation == "url":
            importer = self.resource.importer.url
            return importer(r)

        elif representation == "csv":
            import csv, cgi
            csv.field_size_limit(1000000000)
            infile = request.vars.filename
            importer = self.resource.importer.csv
            if isinstance(infile, cgi.FieldStorage) and infile.filename:
                infile = infile.file
            else:
                try:
                    infile = open(infile, "rb")
                except:
                    session.error = T("Cannot read from file: %s" % infile)
                    redirect(r.there(representation="html"))
            try:
                importer(infile, table=table)
            except:
                session.error = T("Unable to parse CSV file or file contains invalid data")
            else:
                session.flash = T("Data uploaded")

        else:
            r.error(501, self.manager.ERROR.BAD_FORMAT)

        return output


    # -------------------------------------------------------------------------
    def read(self, r, **attr):

        """ Read a single record

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @todo 2.3: add update form if permitted + show_add_btn

        """

        session = self.session
        request = self.request
        response = self.response

        table = self.table
        tablename = self.tablename

        representation = r.representation

        output = dict()

        editable = self._config("editable", True)
        deletable = self._config("deletable", True)

        # Get the target record ID
        record_id = self._record_id(r)
        if not record_id:
            if r.component and not r.multiple:
                authorised = self.permit("create", tablename)
                if authorised:
                    return self.create(r, **attr)

        if r.interactive:

            # Redirect to update if user has permission unless
            # a method has been specified in the URL
            if not r.method:
                authorised = self.permit("update", tablename, record_id)
                if authorised and representation == "html" and editable:
                    return self.update(r, **attr)

            # Form configuration
            subheadings = self._config("subheadings")

            # Title and subtitle
            title = self.crud_string(r.tablename, "title_display")
            output.update(title=title)
            if r.component:
                subtitle = self.crud_string(tablename, "title_display")
                output.update(subtitle=subtitle)

            # Item
            if record_id:
                item = self.resource.read(record_id,
                                          download_url=self.download_url,
                                          format=representation)
                if subheadings:
                    self.insert_subheadings(item, self.tablename, subheadings)
            else:
                item = self.crud_string(tablename, "msg_list_empty")

            # View
            if representation == "html":
                self.response.view = self._view(r, "display.html")
                output.update(item=item)
            elif representation in ("popup", "iframe"):
                self.response.view = self._view(r, "popup.html")
                caller = attr.get("caller", None)
                output.update(form=item, caller=caller)

            # Buttons
            buttons = self.insert_buttons(r, "update", "delete", "list",
                                          record_id=record_id)
            if buttons:
                output.update(buttons)

        elif representation == "plain":
            item = self.resource.read(record_id,
                                      download_url=self.download_url,
                                      format=representation)
            response.view = "plain.html"
            output.update(item=item)

        elif representation == "csv":
            exporter = self.resource.exporter.csv
            return exporter(self.resource)

        elif representation == "pdf":
            list_fields = self._config("list_fields")
            exporter = self.resource.exporter.pdf
            return exporter(self.resource, list_fields=list_fields)

        elif representation == "xls":
            list_fields = self._config("list_fields")
            exporter = self.resource.exporter.xls
            return exporter(self.resource, list_fields=list_fields)

        else:
            r.error(501, self.manager.ERROR.BAD_FORMAT)

        return output


    # -------------------------------------------------------------------------
    def update(self, r, **attr):

        """ Update a record

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @todo 2.3: plain representation

        """

        session = self.session
        request = self.request
        response = self.response

        table = self.table
        tablename = self.tablename

        T = self.manager.T

        representation = r.representation

        output = dict()

        # Get table configuration
        editable = self._config("editable", True)
        deletable = self._config("deletable", True)

        # Get callbacks
        onvalidation = self._config("update_onvalidation") or \
                       self._config("onvalidation")
        onaccept = self._config("update_onaccept") or \
                   self._config("onaccept")

        # Get the target record ID
        record_id = self._record_id(r)
        if not record_id:
            r.error(404, self.resource.ERROR.BAD_RECORD)

        # Check if editable
        if not editable:
            if r.interactive:
                return self.read(r, **attr)
            else:
                r.error(400, self.resource.ERROR.BAD_METHOD)

        # Check permission for update
        authorised = self.permit("update", self.tablename, record_id)
        if not authorised:
            r.unauthorised()

        if r.interactive:

            # Form configuration
            update_next = self._config("update_next")
            subheadings = self._config("subheadings")

            # Set view
            if representation == "html":
                self.response.view = self._view(r, "update.html")
            elif representation in ("popup", "iframe"):
                self.response.view = self._view(r, "popup.html")

            # Title and subtitle
            if r.component:
                title = self.crud_string(r.tablename, "title_display")
                subtitle = self.crud_string(self.tablename, "title_update")
                output.update(title=title, subtitle=subtitle)
            else:
                title = self.crud_string(self.tablename, "title_update")
                output.update(title=title)

            # Component join
            if r.component:
                _comment = table[r.fkey].comment
                table[r.fkey].comment = None
                table[r.fkey].default = r.record[r.pkey]
                if r.http == "POST":
                    table[r.fkey].writable = True
                    request.post_vars.update({r.fkey: str(r.record[r.pkey])})
                else:
                    table[r.fkey].readable = False
                    table[r.fkey].writable = False

            # Success message
            message = self.crud_string(self.tablename, "msg_record_modified")

            # Get the form
            form = self.resource.update(record_id,
                                        message=message,
                                        onvalidation=onvalidation,
                                        onaccept=onaccept,
                                        download_url=self.download_url,
                                        format=representation)

            # Insert subheadings
            if subheadings:
                self.insert_subheadings(form, tablename, subheadings)

            # Cancel button?
            if response.s3.cancel:
                form[0][-1][1].append(INPUT(_type="button",
                                            _value=T("Cancel"),
                                            _onclick="window.location='%s';" %
                                                     response.s3.cancel))

            # Navigate-away confirmation
            if self.settings.navigate_away_confirm:
                form.append(SCRIPT("EnableNavigateAwayConfirm();"))

            # Put form into output
            output.update(form=form)

            # Add map
            location_id = [f for f in table if f.writable and
                            str(f.type) == "reference gis_location"]
            if location_id:
                response.s3.gis.location_id = True
                if response.s3.gis.map_selector:
                    gis = self.manager.gis
                    _map = gis.form_map(r, method="update",
                                        tablename=tablename,
                                        prefix=self.prefix,
                                        name=self.name)
                    oldlocation = _map["oldlocation"]
                    _map = _map["_map"]
                    output.update(_map=_map, oldlocation=oldlocation)

            # Add delete and list buttons
            buttons = self.insert_buttons(r, "delete", "list",
                                          record_id=record_id)
            if buttons:
                output.update(buttons)

            # Redirection
            if representation in ("popup", "iframe"):
                self.next = None
            elif not update_next:
                #if r.component:
                    #self.next = r.there(representation=r.representation)
                #else:
                    #self.next = r.here(representation=r.representation)
                self.next = self.resource.url(id=[])
            else:
                try:
                    self.next = update_next(self)
                except TypeError:
                    self.next = update_next

        #elif representation == "plain":
            #pass

        elif representation == "url":
            importer = self.resource.importer.url
            return importer(r)

        else:
            r.error(501, self.manager.ERROR.BAD_FORMAT)

        return output


    # -------------------------------------------------------------------------
    def delete(self, r, **attr):

        """ Delete record(s)

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @todo 2.3: put style information into stylesheet
            @todo 2.3: move confirmation form into resource

        """

        session = self.session
        request = self.request
        response = self.response

        table = self.table
        tablename = self.tablename

        T = self.manager.T

        representation = r.representation

        output = dict()

        # Get callback
        ondelete = self._config("ondelete")

        # Get table-specific parameters
        deletable = self._config("deletable", True)
        delete_next = self._config("delete_next", None)

        # Get the target record ID
        record_id = self._record_id(r)

        # Check permission for delete
        if not deletable:
            r.error(403, self.manager.ERROR.NOT_PERMITTED)
        authorised = self.permit("delete", self.tablename, record_id)
        if not authorised:
            r.unauthorised()

        elif r.http == "GET" and not record_id:
            # Provide a confirmation form and a record list
            form = FORM(TABLE(TR(
                        TD(T("Do you really want to delete these records?"),
                           _style="color: red;"),
                        TD(INPUT(_type="submit", _value=T("Delete"),
                           _style="margin-left: 10px;")))))
            items = self.select(r, **attr).get("items", None)
            output.update(form=form, items=items)
            response.view = self._view(r, "delete.html")

        elif r.http == "POST" or \
             r.http == "GET" and record_id:
            # Delete the records, notify success and redirect to the next view
            numrows = self.resource.delete(ondelete=ondelete,
                                           format=representation)
            if numrows > 1:
                response.confirmation = "%s %s" % \
                                        (numrows, T("records deleted"))
            else:
                response.confirmation = self.crud_string(self.tablename,
                                                         "msg_record_deleted")
            r.http = "DELETE"
            self.next = delete_next or r.there()

        elif r.http == "DELETE":
            # Delete the records and return a JSON message
            numrows = self.resource.delete(ondelete=ondelete,
                                           format=representation)
            message = "%s %s" % (numrows, T("records deleted"))
            item = self.manager.xml.json_message(message=message)
            self.response.view = "xml.html"
            output.update(item=item)

        else:
            r.error(400, self.manager.ERROR.BAD_METHOD)

        return output


    # -------------------------------------------------------------------------
    def select(self, r, **attr):

        """ Get a list view of the requested resource

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

        """

        session = self.session
        request = self.request
        response = self.response

        table = self.table
        tablename = self.tablename

        representation = r.representation

        output = dict()

        # Get table-specific parameters
        orderby = self._config("orderby", None)
        sortby = self._config("sortby", [[1,'asc']])
        linkto = self._config("linkto", None)
        insertable = self._config("insertable", True)
        listadd = self._config("listadd", True)
        list_fields = self._config("list_fields")

        # Pagination
        vars = request.get_vars
        if representation == "aadata":
            start = vars.get("iDisplayStart", 0)
            limit = vars.get("iDisplayLength", None)
        else:
            start = vars.get("start", 0)
            limit = vars.get("limit", None)
        if limit is not None:
            try:
                start = int(start)
                limit = int(limit)
            except ValueError:
                start = 0
                limit = None

        # Linkto
        if not linkto:
            linkto = self._linkto(r)

        # List fields
        if not list_fields:
            fields = self.resource.readable_fields()
        else:
            fields = [table[f] for f in list_fields if f in table.fields]
        if not fields:
            fields = []
        if fields[0].name != table.fields[0]:
            fields.insert(0, table[table.fields[0]])

        # Filter
        if response.s3.filter is not None:
            self.resource.add_filter(response.s3.filter)

        if r.interactive:

            # SSPag?
            if not response.s3.no_sspag:
                limit = 1
                session.s3.filter = request.get_vars

            # Add hidden add-form (do this before retrieving the list!)
            if listadd:
                form = self.create(r, **attr).get("form", None)
                if form is not None:
                    output.update(form=form)
                    addtitle = self.crud_string(tablename, "subtitle_create")
                    output.update(addtitle=addtitle)
                    # Show-Add button to activate the form:
                    showadd_btn = self.crud_button(None,
                                                   tablename=tablename,
                                                   name="label_create_button",
                                                   _id="show-add-btn")
                    output.update(showadd_btn=showadd_btn)
                    # Add map where appropriate:
                    location_id = [f for f in table if f.writable and
                                str(f.type) == "reference gis_location"]
                    if location_id:
                        response.s3.gis.location_id = True
                        if response.s3.gis.map_selector:
                            _map = self.manager.gis.form_map(r, method="create")
                            output.update(_map=_map)
                    # Switch to list_create view
                    self.response.view = self._view(r, "list_create.html")
                else:
                    self.response.view = self._view(r, "list.html")
            elif insertable:
                buttons = self.insert_buttons(r, "add")
                if buttons:
                    output.update(buttons)
                self.response.view = self._view(r, "list.html")

            # Get the list
            items = self.resource.select(fields=fields,
                                         start=start,
                                         limit=limit,
                                         orderby=orderby,
                                         linkto=linkto,
                                         download_url=self.download_url,
                                         format=representation)

            # Empty table - or just no match?
            if not items:
                if "deleted" in self.table:
                    available_records = self.db(self.table.deleted == False)
                else:
                    available_records = self.db(self.table.id > 0)
                if available_records.count():
                    items = self.crud_string(self.tablename, "msg_no_match")
                else:
                    items = self.crud_string(self.tablename, "msg_list_empty")

            # Title and subtitle
            if r.component:
                title = self.crud_string(r.tablename, "title_display")
            else:
                title = self.crud_string(self.tablename, "title_list")
            subtitle = self.crud_string(self.tablename, "subtitle_list")

            # Update output
            output.update(title=title,
                          subtitle=subtitle,
                          items=items,
                          sortby=sortby)

        elif representation == "aadata":

            left = []

            # Get the master query for SSPag
            if session.s3.filter is not None:
                self.resource.build_query(filter=response.s3.filter,
                                          vars=session.s3.filter)

            displayrows = totalrows = self.resource.count()

            # SSPag dynamic filter?
            if vars.sSearch:
                squery = self.ssp_filter(table, fields, left=left)
                if squery is not None:
                    self.resource.add_filter(squery)
                    displayrows = self.resource.count(left=left)

            # SSPag sorting
            if vars.iSortingCols and orderby is None:
                orderby = self.ssp_orderby(table, fields, left=left)

            # Echo
            sEcho = int(vars.sEcho or 0)

            # Get the list
            items = self.resource.select(fields=fields,
                                         left=left,
                                         start=start,
                                         limit=limit,
                                         orderby=orderby,
                                         linkto=linkto,
                                         download_url=self.download_url,
                                         as_page=True,
                                         format=representation) or []

            result = dict(sEcho = sEcho,
                          iTotalRecords = totalrows,
                          iTotalDisplayRecords = displayrows,
                          aaData = items)

            output = json(result)

        elif representation == "plain":
            items = self.resource.select(fields, as_list=True)
            self.response.view = "plain.html"
            return dict(item=items)

        elif representation == "csv":
            exporter = S3Exporter(self.manager)
            return exporter.csv(self.resource)

        elif representation == "pdf":
            exporter = S3Exporter(self.manager)
            return exporter.pdf(self.resource,
                                list_fields=list_fields)

        elif representation == "xls":
            exporter = S3Exporter(self.manager)
            return exporter.xls(self.resource,
                                list_fields=list_fields)

        else:
            r.error(501, self.manager.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def crud_button(self, label,
                    tablename=None,
                    name=None,
                    _href=None,
                    _id=None,
                    _class="action-btn"):

        """ Generate a link button

            @param label: the link label (None if using CRUD string)
            @param tablename: the name of table for CRUD string selection
            @param name: name of CRUD string for the button label
            @param _href: the target URL
            @param _id: the HTML-ID of the link
            @param _class: the HTML-class of the link

        """

        if name:
            labelstr = self.crud_string(tablename, name)
        else:
            labelstr = str(label)

        if not _href:
            button = A(labelstr, _id=_id, _class=_class)
        else:
            button = A(labelstr, _href=_href, _id=_id, _class=_class)

        return button


    # -------------------------------------------------------------------------
    def crud_string(self, tablename, name):

        """ Get a CRUD info string for interactive pages

            @param tablename: the table name
            @param name: the name of the CRUD string

        """

        s3 = self.manager.s3

        crud_strings = s3.crud_strings.get(tablename, s3.crud_strings)
        not_found = s3.crud_strings.get(name, None)

        return crud_strings.get(name, not_found)


    # -----------------------------------------------------------------------------
    @staticmethod
    def insert_subheadings(form, tablename, subheadings):

        """ Insert subheadings into forms

            @param form: the form
            @param tablename: the tablename
            @param subheadings: a dict of {"Headline": Fieldnames}, where Fieldname can
                be either a single field name or a list/tuple of field names belonging
                under that headline

        """

        if subheadings:
            if tablename in subheadings:
                subheadings = subheadings.get(tablename)
            form_rows = iter(form[0])
            tr = form_rows.next()
            i = 0
            done = []
            while tr:
                f = tr.attributes.get("_id", None)
                if f.startswith(tablename):
                    f = f[len(tablename)+1:-6]
                    for k in subheadings.keys():
                        if k in done:
                            continue
                        fields = subheadings[k]
                        if not isinstance(fields, (list, tuple)):
                            fields = [fields]
                        if f in fields:
                            done.append(k)
                            form[0].insert(i, TR(TD(k, _colspan=3,
                                                    _class="subheading"),
                                                 _class = "subheading",
                                                 _id = "%s_%s__subheading" %
                                                       (tablename, f)))
                            tr.attributes.update(_class="after_subheading")
                            tr = form_rows.next()
                            i += 1
                try:
                    tr = form_rows.next()
                except StopIteration:
                    break
                else:
                    i += 1


    # -------------------------------------------------------------------------
    def insert_buttons(self, r, *buttons, **attr):

        """ Insert resource action buttons

            @param r: the S3Request
            @param buttons: button names ("add", "edit", "delete", "list")
            @keyword record_id: the record ID

        """

        output = dict()

        T = self.manager.T

        tablename = self.tablename
        representation = r.representation

        record_id = attr.get("record_id", None)

        # Button labels
        ADD = self.crud_string(tablename, "label_create_button")
        EDIT = T("Edit")
        DELETE = self.crud_string(tablename, "label_delete_button")
        LIST = self.crud_string(tablename, "label_list_button")

        # Button URLs
        href_add = r.other(method="create", representation=representation)
        href_edit = r.other(method="update", representation=representation)
        href_delete = r.other(method="delete", representation=representation)
        href_list = r.there()

        # Table CRUD configuration
        insertable = self._config("insertable", True)
        editable = self._config("editable", True)
        deletable = self._config("deletable", True)

        # Add button
        if "add" in buttons:
            authorised = self.permit("create", tablename)
            if authorised and href_add and insertable:
                add_btn = self.crud_button(ADD, _href=href_add, _id="add-btn")
                output.update(add_btn=add_btn)

        # List button
        if "list" in buttons:
            if not r.component or r.multiple:
                list_btn = self.crud_button(LIST, _href=href_list,
                                            _id="list-btn")
                output.update(list_btn=list_btn)

        if not record_id:
            return output

        # Edit button
        if "edit" in buttons:
            authorised = self.permit("update", tablename, record_id)
            if authorised and href_edit and editable and r.method != "update":
                edit_btn = self.crud_button(EDIT, _href=href_edit,
                                            _id="edit-btn")
                output.update(edit_btn=edit_btn)

        # Delete button
        if "delete" in buttons:
            authorised = self.permit("delete", tablename, record_id)
            if authorised and href_delete and deletable:
                delete_btn = self.crud_button(DELETE, _href=href_delete,
                                              _id="delete-btn")
                output.update(delete_btn=delete_btn)

        return output


    # -------------------------------------------------------------------------
    def _linkto(self, r, authorised=None, update=None, native=False):

        """ Returns a linker function for the record ID column in list views

            @param r: the S3Request
            @param authorised: user authorised for update (override internal check)
            @param update: provide link to update rather than to read
            @param native: link to the native controller rather than to
                           component controller

        """

        c = None
        f = None

        response = self.response

        prefix, name, table, tablename = r.target()
        permit = self.manager.auth.shn_has_permission
        model = self.manager.model

        if authorised is None:
            authorised = permit("update", tablename)

        if authorised and update:
            linkto = model.get_config(table, "linkto_update", None)
        else:
            linkto = model.get_config(table, "linkto", None)

        if r.component and native:
            # link to native component controller (be sure that you have one)
            c = prefix
            f = name

        def list_linkto(record_id, r=r, c=c, f=f,
                        linkto=linkto,
                        update=authorised and update):

            if linkto:
                try:
                    url = str(linkto(record_id))
                except TypeError:
                    url = linkto % record_id
                return url
            else:
                if r.component:
                    if c and f:
                        args = [record_id]
                    else:
                        c = r.request.controller
                        f = r.request.function
                        args = [r.id, r.component_name, record_id]
                    if update:
                        return str(URL(r=r.request, c=c, f=f,
                                       args=args + ["update"],
                                       vars=r.request.vars))
                    else:
                        return str(URL(r=r.request, c=c, f=f,
                                       args=args,
                                       vars=r.request.vars))
                else:
                    args = [record_id]
                    if update:
                        return str(URL(r=r.request, c=c, f=f,
                                       args=args + ["update"]))
                    else:
                        return str(URL(r=r.request, c=c, f=f,
                                       args=args))

        return list_linkto


    # -------------------------------------------------------------------------
    def ssp_filter(self, table, fields, left=[]):

        """ Convert the SSPag GET vars into a filter query

            @param table: the table
            @param fields: list of fields displayed in the list view (same order!)
            @param left: list of joins

        """

        vars = self.request.get_vars

        context = str(vars.sSearch).lower()
        columns = int(vars.iColumns)

        searchq = None

        wildcard = "%%%s%%" % context

        # Retrieve the list of search fields
        flist = []
        for i in xrange(0, columns):
            field = fields[i]
            fieldtype = str(field.type)
            if fieldtype.startswith("reference") and \
               hasattr(field, "sortby") and field.sortby:
                tn = fieldtype[10:]
                join = [j for j in left if j.table._tablename == tn]
                if not join:
                    left.append(self.db[tn].on(field == self.db[tn].id))
                else:
                    join[0].query = (join[0].query) | (field == self.db[tn].id)
                if isinstance(field.sortby, (list, tuple)):
                    flist.extend([self.db[tn][f] for f in field.sortby])
                else:
                    flist.append(self.db[tn][field.sortby])
            else:
                flist.append(field)

        # Build search query
        for field in flist:
            query = None
            if str(field.type) == "integer":
                requires = field.requires
                if not isinstance(requires, (list, tuple)):
                    requires = [requires]
                if requires:
                    r = requires[0]
                    if isinstance(r, IS_EMPTY_OR):
                        r = r.other
                    try:
                        options = r.options()
                    except:
                        continue
                    vlist = []
                    for (value, text) in options:
                        if str(text).lower().find(context) != -1:
                            vlist.append(value)
                    if vlist:
                        query = field.belongs(vlist)
                else:
                    continue
            elif str(field.type) in ("string", "text"):
                query = field.lower().like(wildcard)
            if searchq is None and query:
                searchq = query
            elif query:
                searchq = searchq | query

        return searchq


    # -------------------------------------------------------------------------
    def ssp_orderby(self, table, fields, left=[]):

        """ Convert the SSPag GET vars into a sorting query

            @param table: the table
            @param fields: list of fields displayed in the list view (same order!)
            @param left: list of joins

        """

        vars = self.request.get_vars
        tablename = table._tablename

        iSortingCols = int(vars["iSortingCols"])

        def direction(i):
            dir = vars["sSortDir_%s" % str(i)]
            return dir and " %s" % dir or ""

        orderby = []
        columns = [fields[int(vars["iSortCol_%s" % str(i)])]
                   for i in xrange(iSortingCols)]
        for i in xrange(len(columns)):
            c = columns[i]
            fieldtype = str(c.type)
            if fieldtype.startswith("reference") and \
               hasattr(c, "sortby") and c.sortby:
                tn = fieldtype[10:]
                join = [j for j in left if j.table._tablename == tn]
                if not join:
                    left.append(self.db[tn].on(c == self.db[tn].id))
                else:
                    join[0].query = (join[0].query) | (c == self.db[tn].id)
                if not isinstance(c.sortby, (list, tuple)):
                    orderby.append("%s.%s%s" % (tn, c.sortby, direction(i)))
                else:
                    orderby.append(", ".join(["%s.%s%s" % (tn, fn, direction(i))
                                   for fn in c.sortby]))
            else:
                orderby.append("%s%s" % (c, direction(i)))

        return ", ".join(orderby)


# *****************************************************************************
class S3SearchSimple(S3CRUDHandler):

    """ Simple string-search method handler

        @param manager: the resource controller
        @param label: the label for the input field in the search form
        @param comment: help text for the input field in the search form
        @param fields: the fields to search for the string

    """


    def __init__(self, manager, label=None, comment=None, fields=None):

        S3CRUDHandler.__init__(self, manager)
        self.__label = label
        self.__comment = comment
        self.__fields = fields


    # -------------------------------------------------------------------------
    def respond(self, r, **attr):

        """ Responder

            @param r: the S3Request
            @param attr: request parameters

        """

        # Get environment
        session = self.session
        request = self.request
        response = self.response
        resource = self.resource
        table = self.table
        tablename = self.tablename
        T = self.manager.T

        # Get representation
        representation = r.representation

        # Initialize output
        output = dict()

        # Get table-specific parameters
        sortby = self._config("sortby", [[1,'asc']])
        orderby = self._config("orderby", None)
        list_fields = self._config("list_fields")

        # GET vars
        vars = request.get_vars

        if r.interactive:
            form = FORM(TABLE(TR("%s: " % self.__label,
                                 INPUT(_type="text", _name="label", _size="40"),
                                 DIV(DIV(_class="tooltip",
                                         _title="%s|%s" % (self.__label,
                                                           self.__comment)))),
                              TR("", INPUT(_type="submit",
                                           _value=T("Search")))))
            output.update(form=form)

            if form.accepts(request.vars, session, keepvalues=True):
                if form.vars.label == "":
                    form.vars.label = "%"
                results = self.manager._search_simple(table,
                                                      fields = self.__fields,
                                                      label = form.vars.label)
                if results:
                    linkto = self._linkto(r)
                    if not list_fields:
                        fields = resource.readable_fields()
                    else:
                        fields = [table[f]
                                  for f in list_fields if f in table.fields]
                    if not fields:
                        fields = []
                    if fields[0].name != table.fields[0]:
                        fields.insert(0, table[table.fields[0]])
                    resource.build_query(id=results)
                    items = resource.select(fields=fields,
                                            orderby=orderby,
                                            linkto=linkto,
                                            download_url=self.download_url,
                                            format=representation)
                    session.s3.filter = {"%s.id" % resource.name:
                                         ",".join(map(str,results))}
                else:
                    items = T("No matching records found.")
                output.update(items=items, sortby=sortby)

                # Add-button
                buttons = self.insert_buttons(r, "add")
                if buttons:
                    output.update(buttons)

            # Title and subtitle
            title = self.crud_string(tablename, "title_search")
            subtitle = T("Matching Records")
            output.update(title=title, subtitle=subtitle)

            # View
            response.view = "search_simple.html"

        elif representation == "aadata":
            return self.select(r, **attr)

        else:
            r.error(resource.ERROR.BAD_FORMAT)

        return output


# END
# *****************************************************************************
