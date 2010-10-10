# -*- coding: utf-8 -*-

""" S3XRC Resource Framework - CRUD method handlers

    @version: 2.1.7

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>} on Eden wiki

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
           "S3CRUDHandler"]

import datetime, os

from gluon.storage import Storage
from gluon.html import URL, A
from gluon.http import HTTP, redirect
from gluon.serializers import json
from gluon.sql import Field, Row
from gluon.validators import IS_EMPTY_OR

from s3import import S3Importer
from s3export import S3Exporter

from lxml import etree

# *****************************************************************************
class S3Audit(object):

    """ Audit Trail Writer Class """

    # -------------------------------------------------------------------------
    def __init__(self, db, session,
                 tablename="s3_audit",
                 migrate=True):

        """ Constructor

            @param db: the database
            @param session: the current session
            @param tablename: the name of the audit table
            @param migrate: migration setting

        """

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

        """ Caller

            @param operation: Operation to log, one of
                "create", "update", "read", "list" or "delete"
            @param prefix: the module prefix of the resource
            @param name: the name of the resource (without prefix)
            @param form: the form
            @param record: the record ID
            @param representation: the representation format

            @todo 2.2: correct parameter naming for record ID
            @todo 2.2: default for representation, HTML?

        """

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

    """ REST Method Handler Base Class

        @todo 2.2: implement parent class S3Responder
        
    """

    # -------------------------------------------------------------------------
    def __init__(self, manager):

        """ Constructor

            @todo 2.2: fix docstring

        """

        self.manager = manager
        self.db = self.manager.db

        self.permit = self.manager.auth.shn_has_permission

        self.next = None

    # -------------------------------------------------------------------------
    def __call__(self, r, method=None, **attr):

        """ Caller, invoked by REST interface

            @todo 2.2: fix docstring

        """

        # Get the environment
        self.request = r.request
        self.session = r.session
        self.response = r.response

        # Settings
        self.download_url = URL(r=self.request, f="download")

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

        # Redirection to next
        r.next = self.next

        # Done
        return output


    # -------------------------------------------------------------------------
    def respond(self, r, **attr):

        """ Responder, to be implemented in subclass

            @todo: fix docstring

        """

        output = dict()

        return output


# *****************************************************************************
class S3CRUDHandler(S3MethodHandler):

    """ Interactive CRUD Method Handler Base Class """

    def respond(self, r, **attr):

        """ Responder

            @todo 2.2: fix docstring
            @todo 2.2: complete this

        """

        settings = self.manager.s3.crud
        if settings:
            self.formstyle = settings.formstyle
        else:
            self.formstyle = "table3cols"

        self.representation = r.representation.lower()
        self.INTERACTIVE_FORMATS = ("html", "popup", "iframe")

        # Page elements configuration
        self.download_url = None

        vars = self.request.get_vars

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

        #elif self.method == "search":
            #pass

        #elif self.method == "search_simple":
            #pass

        else:
            # Unsupported method
            pass

        representation = r.representation.lower()

        if representation in self.INTERACTIVE_FORMATS and \
           isinstance(output, dict):

            # Resource header
            rheader = attr.get("rheader", None)
            sticky = attr.get("sticky", rheader is not None)

            if rheader and r.id and (r.component or sticky):
                try:
                    rh = rheader(r)
                except TypeError:
                    rh = rheader
                output.update(rheader=rh)

        return output

    # -------------------------------------------------------------------------
    def create(self, r, **attr):

        """ Create new records

            @todo 2.2: implement this
            @todo 2.2: fix docstring
            
        """

        return dict()


    # -------------------------------------------------------------------------
    def read(self, r, **attr):

        """ Read a single record

            @todo 2.2: implement this
            @todo 2.2: fix docstring
            
        """
        
        return dict()


    # -------------------------------------------------------------------------
    def update(self, r, **attr):

        """ Update a record

            @todo 2.2: implement this
            @todo 2.2: fix docstring
            
        """
        
        return dict()


    # -------------------------------------------------------------------------
    def delete(self, r, **attr):

        """ Delete record(s)

            @todo 2.2: implement this
            @todo 2.2: fix docstring
            
        """
        
        return dict()


    # -------------------------------------------------------------------------
    def select(self, r, **attr):

        """ Get a list view of the requested resource

            @todo 2.2: complete this
            @todo 2.2: fix docstring

        """

        # Initialize output
        output = dict()

        model = self.manager.model
        representation = r.representation.lower()

        # Table-specific parameters
        _attr = r.component and r.component.attr or attr
        orderby = _attr.get("orderby", None)
        sortby = _attr.get("sortby", [[1,'asc']])
        linkto = _attr.get("linkto", None)
        listadd = _attr.get("listadd", True)

        # main and extra for searchbox
        main = _attr.get("main", None)
        extra = _attr.get("extra", None)

        # GET vars
        vars = self.request.get_vars

        # Pagination
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

        # Audit
        audit = self.manager.audit
        audit("list", self.prefix, self.name, representation=representation)

        # Linkto
        if not linkto:
            linkto = self._linkto(r)

        # List fields
        table = self.resource.table
        list_fields = model.get_config(table, "list_fields")
        if not list_fields:
            fields = resource.readable_fields()
        else:
            fields = resource.readable_fields(subset=list_fields)
        if not fields:
            fields = [table.id]

        if representation in self.INTERACTIVE_FORMATS:

            # Pagination?
            if self.response.s3.pagination:
                limit = 1

            # Store the query for SSPag
            self.session.s3.filter = self.request.get_vars

            # Get the list
            items = self.resource.select(fields=fields,
                                         start=start,
                                         limit=limit,
                                         orderby=orderby,
                                         linkto=linkto,
                                         download_url=self.download_url)

            if not items:
                if self.db(self.table.id > 0).count():
                    items = self.crud_string(self.tablename, "msg_no_match")
                else:
                    items = self.crud_string(self.tablename, "msg_list_empty")

            output.update(items=items)

            # Title and subtitle
            if r.component:
                title = self.crud_string(r.tablename, "title_display")
            else:
                title = self.crud_string(self.tablename, "title_list")
            subtitle = self.crud_string(self.tablename, "subtitle_list")
            output.update(title=title, subtitle=subtitle)

            # Add add-form
            if listadd:
                form = self.resource.create()
                output.update(form=form)
                addtitle = self.crud_string(self.tablename, "subtitle_create")
                output.update(addtitle=addtitle)
                showaddbtn = self.crud_button(self.tablename,
                                              "label_create_button",
                                              _id="show-add-btn")
                output.update(showaddbtn=showaddbtn)
                self.response.view = self._view(r, "list_create.html")

            else:
                self.response.view = self._view(r, "list.html")

            #output.update(_map=_map)
            output.update(main=main, extra=extra, sortby=sortby)

        elif representation == "aadata":

            # Get the master query for SSPag
            if self.session.s3.filter is not None:
                self.resource.build_query(id=self.record,
                                          vars=self.session.s3.filter)

            displayrows = totalrows = self.resource.count()

            # SSPag dynamic filter?
            if vars.sSearch:
                squery = self.ssp_filter(table, fields)
                if squery is not None:
                    self.resource.add_filter(squery)
                    displayrows = self.resource.count()

            # SSPag sorting
            if vars.iSortingCols and orderby is None:
                orderby = self.ssp_orderby(table, fields)

            # Echo
            sEcho = int(vars.sEcho or 0)

            # Get the list
            items = self.resource.select(fields=fields,
                                         start=start,
                                         limit=limit,
                                         orderby=orderby,
                                         linkto=linkto,
                                         download_url=self.download_url,
                                         as_page=True) or []

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
            raise HTTP(501, body=self.manager.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def _view(self, r, default, format=None):

        """ Get the target view path

            @todo 2.2: fix docstring
            
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
    def crud_button(self, tablename, label,
                    _href=None,
                    _id=None,
                    _class="action-btn"):

        """ Generate a link button

            @todo 2.2: fix docstring
            
        """

        labelstr = self.crud_string(tablename, label)

        if not _href:
            button = A(labelstr, _id=_id, _class=_class)
        else:
            button = A(labelstr, _href=href, _id=_id, _class=_class)

        return button


    # -------------------------------------------------------------------------
    def crud_string(self, tablename, name):

        """ Get a CRUD info string for interactive pages

            @todo 2.2: fix docstring
            
        """

        s3 = self.manager.s3

        crud_strings = s3.crud_strings.get(tablename, s3.crud_strings)
        not_found = s3.crud_strings.get(name, None)

        return crud_strings.get(name, not_found)


    # -------------------------------------------------------------------------
    def _linkto(self, r, authorised=None, update=None, native=False):

        """ Linker for the record ID column in list views

            @todo 2.2: fix docstring
            
        """

        c = None
        f = None

        permit = self.manager.auth.shn_has_permission
        response = self.response

        if r.component:
            if authorised is None:
                authorised = permit("update", r.component.tablename)
            if authorised and update:
                linkto = r.component.attr.get("linkto_update", None)
            else:
                linkto = r.component.attr.get("linkto", None)
            if native:
                # link to native component controller (be sure that you have one)
                c = r.component.prefix
                f = r.component.name
        else:
            if authorised is None:
                authorised = permit("update", r.tablename)
            if authorised and update:
                linkto = response.s3.get("linkto_update", None)
            else:
                linkto = response.s3.get("linkto", None)

        def list_linkto(record_id, r=r, c=c, f=f, linkto=linkto,
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
                        return str(URL(r=r.request, c=c, f=f, args=args + ["update"], vars=r.request.vars))
                    else:
                        return str(URL(r=r.request, c=c, f=f, args=args, vars=r.request.vars))
                else:
                    args = [record_id]
                    if update:
                        return str(URL(r=r.request, c=c, f=f, args=args + ["update"]))
                    else:
                        return str(URL(r=r.request, c=c, f=f, args=args))

        return list_linkto


    # -------------------------------------------------------------------------
    def ssp_filter(self, table, fields):

        """ Convert the SSPag GET vars into a filter query

            @todo 2.2: fix docstring
            
        """

        vars = self.request.get_vars

        context = str(vars.sSearch).lower()
        columns = int(vars.iColumns)

        searchq = None

        wildcard = "%%%s%%" % context

        for i in xrange(0, columns):
            field = fields[i]
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
    def ssp_orderby(self, table, fields):

        """ Convert the SSPag GET vars into a sorting query

            @todo 2.2: fix docstring
            
        """

        vars = self.request.get_vars

        tablename = table._tablename

        iSortingCols = int(vars["iSortingCols"])

        #colname = lambda i: \
                  #"%s.%s" % (tablename,
                  #fields[int(vars["iSortCol_%s" % str(i)])])

        colname = lambda i: fields[int(vars["iSortCol_%s" % str(i)])]

        def direction(i):
            dir = vars["sSortDir_%s" % str(i)]
            return dir and " %s" % dir or ""

        return ", ".join(["%s%s" %
                        (colname(i), direction(i))
                        for i in xrange(iSortingCols)])


# *****************************************************************************
