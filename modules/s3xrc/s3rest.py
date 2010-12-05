# -*- coding: utf-8 -*-

""" S3XRC Resource Framework - Resource API

    @version: 2.2.7

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

__all__ = ["S3Resource", "S3Request"]

import os, sys, cgi, uuid, datetime, time, urllib, StringIO, re
import gluon.contrib.simplejson as json

from gluon.storage import Storage
from gluon.sql import Row
from gluon.html import *
from gluon.http import HTTP, redirect
from gluon.sqlhtml import SQLTABLE, SQLFORM
from gluon.validators import IS_EMPTY_OR

from lxml import etree
from s3crud import S3CRUDHandler


# *****************************************************************************
class S3SQLTable(SQLTABLE):

    """ Custom version of gluon.sqlhtml.SQLTABLE """

    def __init__(self, sqlrows,
                 linkto=None,
                 upload=None,
                 orderby=None,
                 headers={},
                 truncate=16,
                 columns=None,
                 th_link='',
                 **attributes):

        """ Constructor

            @todo 2.3: fix docstring
            @todo 2.3: PEP8

        """

        table_field = re.compile('[\w_]+\.[\w_]+')

        TABLE.__init__(self, **attributes)
        self.components = []
        self.attributes = attributes
        self.sqlrows = sqlrows
        (components, row) = (self.components, [])
        if not columns:
            columns = sqlrows.colnames
        if headers=="fieldname:capitalize":
            headers = {}
            for c in columns:
                headers[c] = " ".join([w.capitalize() for w in c.split(".")[-1].split("_")])

        for c in columns:
            if orderby:
                row.append(TH(A(headers.get(c, c),
                                _href=th_link+"?orderby=" + c)))
            else:
                row.append(TH(headers.get(c, c)))

        components.append(THEAD(TR(*row)))
        tbody = []
        for (rc, record) in enumerate(sqlrows):
            row = []
            if rc % 2 == 0:
                _class = "even"
            else:
                _class = "odd"
            for colname in columns:
                if not table_field.match(colname):
                    r = record._extra[colname]
                    row.append(TD(r))
                    continue
                (tablename, fieldname) = colname.split(".")
                field = sqlrows.db[tablename][fieldname]
                if tablename in record \
                        and isinstance(record,Row) \
                        and isinstance(record[tablename],Row):
                    r = record[tablename][fieldname]
                elif fieldname in record:
                    r = record[fieldname]
                else:
                    raise SyntaxError, "something wrong in Rows object"
                r_old = r
                if field.represent:
                    r = field.represent(r)
                elif field.type == "blob" and r:
                    r = "DATA"
                elif field.type == "upload":
                    if upload and r:
                        r = A("file", _href="%s/%s" % (upload, r))
                    elif r:
                        r = "file"
                    else:
                        r = ""
                elif field.type in ["string","text"]:
                    r = str(field.formatter(r))
                    ur = unicode(r, "utf8")
                    if truncate!=None and len(ur) > truncate:
                        r = ur[:truncate - 3].encode("utf8") + "..."
                elif linkto and field.type == "id":
                    #try:
                        #href = linkto(r, "table", tablename)
                    #except TypeError:
                        #href = "%s/%s/%s" % (linkto, tablename, r_old)
                    #r = A(r, _href=href)
                    try:
                        href = linkto(r)
                    except TypeError:
                        href = "%s/%s" % (linkto, r)
                    r = A(r, _href=href)
                #elif linkto and str(field.type).startswith("reference"):
                    #ref = field.type[10:]
                    #try:
                        #href = linkto(r, "reference", ref)
                    #except TypeError:
                        #href = "%s/%s/%s" % (linkto, ref, r_old)
                        #if ref.find(".") >= 0:
                            #tref,fref = ref.split(".")
                            #if hasattr(sqlrows.db[tref],"_primarykey"):
                                #href = "%s/%s?%s" % (linkto, tref, urllib.urlencode({fref:ur}))
                    #r = A(r, _href=href)
                elif linkto and hasattr(field._table,"_primarykey") and fieldname in field._table._primarykey:
                    # have to test this with multi-key tables
                    key = urllib.urlencode(dict( [ \
                                ((tablename in record \
                                      and isinstance(record, Row) \
                                      and isinstance(record[tablename], Row)) and
                                 (k, record[tablename][k])) or (k, record[k]) \
                                    for k in field._table._primarykey ] ))
                    r = A(r, _href="%s/%s?%s" % (linkto, tablename, key))
                row.append(TD(r))
            tbody.append(TR(_class=_class, *row))
        components.append(TBODY(*tbody))


# *****************************************************************************
class S3Resource(object):

    """ API for resources

        @param manager: the resource controller
        @param prefix: prefix of the resource name (=module name)
        @param name: name of the resource (without prefix)
        @param id: record ID (or list of record IDs)
        @param uid: record UID (or list of record UIDs)
        @param filter: filter query (DAL resources only)
        @param vars: dictionary of URL query variables
        @param parent: the parent resource
        @param components: component name (or list of component names)

    """

    def __init__(self, manager, prefix, name,
                 id=None,
                 uid=None,
                 filter=None,
                 vars=None,
                 parent=None,
                 components=None):

        self.manager = manager
        self.db = manager.db

        self.HOOKS = manager.HOOKS
        self.ERROR = manager.ERROR

        # Export/Import hooks
        self.exporter = manager.exporter
        self.importer = manager.importer

        self.xml = manager.xml

        # XSLT Paths
        self.XSLT_PATH = "static/formats"
        self.XSLT_EXTENSION = "xsl"
        #self.XSLT_FILE_EXTENSION = "xsl"
        #self.XSLT_IMPORT_TEMPLATES = "static/xslt/import"
        #self.XSLT_EXPORT_TEMPLATES = "static/xslt/export"

        # Authorization hooks
        self.permit = manager.permit
        self.accessible_query = manager.auth.shn_accessible_query

        # Audit hook
        self.audit = manager.audit

        # Basic properties
        self.prefix = prefix
        self.name = name
        self.vars = None # set during build_query

        # Model and Data Store
        self.tablename = "%s_%s" % (self.prefix, self.name)
        self.table = self.db.get(self.tablename, None)
        if not self.table:
            raise KeyError("Undefined table: %s" % self.tablename)

        # The Query
        self.query_builder = manager.query_builder
        self._query = None
        self._multiple = True # multiple results expected by default

        # The Set
        self._set = None
        self._ids = []
        self._uids = []
        self._length = None
        self._slice = False

        # Request control
        self.lastid = None

        self._files = Storage()

        # Attach components and build initial query
        self.components = Storage()
        self.parent = parent

        if self.parent is None:
            self.__attach(select=components)
            self.build_query(id=id, uid=uid, filter=filter, vars=vars)

        # Store CRUD and other method handlers
        self.crud = self.manager.crud
        self._handler = Storage(options=self.__get_options,
                                fields=self.__get_fields,
                                export_tree=self.__get_tree,
                                import_tree=self.__put_tree)

    # Method handler configuration ============================================

    def set_handler(self, method, handler):

        """ Set a REST method handler for this resource

            @param method: the method name
            @param handler: the handler function
            @type handler: handler(S3Request, **attr)

        """

        self._handler[method] = handler


    # -------------------------------------------------------------------------
    def get_handler(self, method):

        """ Get a REST method handler for this resource

            @param method: the method name
            @returns: the handler function

        """

        return self._handler.get(method, None)


    # Data binding ============================================================

    def __attach(self, select=None):

        """ Attach components to this resource

            @param select: name or list of names of components to attach.
                If select is None (default), then all declared components
                of this resource will be attached, to attach none of the
                components, pass an empty list.

        """

        if select and not isinstance(select, (list, tuple)):
            select = [select]

        self.components = Storage()

        if self.parent is None:
            components = self.manager.model.get_components(self.prefix, self.name)

            for i in xrange(len(components)):
                c, pkey, fkey = components[i]

                if select and c.name not in select:
                    continue

                resource = S3Resource(self.manager, c.prefix, c.name,
                                      parent=self)

                self.components[c.name] = Storage(component=c,
                                                   pkey=pkey,
                                                   fkey=fkey,
                                                   resource=resource)


    # Query handling ==========================================================

    def build_query(self, id=None, uid=None, filter=None, vars=None):

        """ Query builder

            @param id: record ID or list of record IDs to include
            @param uid: record UID or list of record UIDs to include
            @param filter: filtering query (DAL only)
            @param vars: dict of URL query variables

        """

        return self.query_builder.query(self,
                                        id=id,
                                        uid=uid,
                                        filter=filter,
                                        vars=vars)


    # -------------------------------------------------------------------------
    def add_filter(self, filter=None):

        """ Extend the current query by a filter query

            @param filter: a web2py query

        """

        if filter is not None:
            if self._query:
                query = self._query
                self.clear()
                self.clear_query()
                self._query = (query) & (filter)
            else:
                self.build_query(filter=filter)
        return self._query


    # -------------------------------------------------------------------------
    def get_query(self):

        """ Get the current query for this resource """

        if not self._query:
            self.build_query()
        return self._query


    # -------------------------------------------------------------------------
    def clear_query(self):

        """ Removes the current query (does not remove the set!) """

        self._query = None
        if self.components:
            for c in self.components:
                self.components[c].resource.clear_query()


    # Data access =============================================================

    def count(self, left=None):

        """ Get the total number of available records in this resource """

        if not self._query:
            self.build_query()
            self._length = None

        if self._length is None:
            x = self.table[self.table.fields[0]].count()
            row = self.db(self._query).select(x, left=left).first()
            if row:
                self._length = row[x]
        return self._length


    # -------------------------------------------------------------------------
    def load(self, start=None, limit=None):

        """ Loads a set of records of the current resource, which can be
            either a slice (for pagination) or all records

            @param start: the index of the first record to load
            @param limit: the maximum number of records to load

        """

        if self._set is not None:
            self.clear()
        if not self._query:
            self.build_query()
        if not self._multiple:
            limitby = (0, 1)
        else:
            # Slicing
            if start is not None:
                self._slice = True
                if not limit:
                    limit = self.manager.ROWSPERPAGE
                if limit <= 0:
                    limit = 1
                if start < 0:
                    start = 0
                limitby = (start, start + limit)
            else:
                limitby = None

        self._set = self.db(self._query).select(self.table.ALL,
                                                limitby=limitby)
        self._ids = [row.id for row in self._set]
        uid = self.manager.UID
        if uid in self.table.fields:
            self._uids = [row[uid] for row in self._set]


    # -------------------------------------------------------------------------
    def clear(self):

        """ Removes the current set """

        self._set = None
        self._length = None
        self._ids = []
        self._uids = []
        self._files = Storage()
        self._slice = False

        if self.components:
            for c in self.components:
                self.components[c].resource.clear()


    # -------------------------------------------------------------------------
    def records(self):

        """ Get the current set

            @returns: a Set or an empty list if no set is loaded

        """

        if self._set is None:
            return []
        else:
            return self._set


    # -------------------------------------------------------------------------
    def __getitem__(self, key):

        """ Retrieves a record from the current set by its ID

            @param key: the record ID
            @returns: a Row

        """

        if self._set is None:
            self.load()
        for i in xrange(len(self._set)):
            row = self._set[i]
            if str(row.id) == str(key):
                return row

        raise IndexError


    # -------------------------------------------------------------------------
    def __iter__(self):

        """ Generator for the current set

            @returns: an Iterator

        """

        if self._set is None:
            self.load()
        for i in xrange(len(self._set)):
            yield self._set[i]
        return


    # -------------------------------------------------------------------------
    def __call__(self, key, component=None):

        """ Retrieves component records of a record in the current set

            @param key: the record ID
            @param component: the name of the component
                (None to get the primary record)
            @returns: a record (if component is None) or a list of records

        """

        if not component:
            return self[key]
        else:
            if isinstance(key, Row):
                master = key
            else:
                master = self[key]
            if component in self.components:
                c = self.components[component]
                r = c.resource
                pkey, fkey = c.pkey, c.fkey
                l = [record for record in r if master[pkey] == record[fkey]]
                return l
            else:
                raise AttributeError


    # -------------------------------------------------------------------------
    def get_id(self):

        """ Returns all IDs of the current set, or, if no set is loaded,
            all IDs of the resource

            @returns: a list of record IDs

        """

        if not self._ids:
            self.__load_ids()
        if not self._ids:
            return None
        elif len(self._ids) == 1:
            return self._ids[0]
        else:
            return self._ids


    # -------------------------------------------------------------------------
    def get_uid(self):

        """ Returns all UIDs of the current set, or, if no set is loaded,
            all UIDs of the resource

            @returns: a list of record UIDs

        """

        if self.manager.UID not in self.table.fields:
            return None

        if not self._uids:
            self.__load_ids()
        if not self._uids:
            return None
        elif len(self._uids) == 1:
            return self._uids[0]
        else:
            return self._uids


    # -------------------------------------------------------------------------
    def __load_ids(self):

        """ Loads the IDs of all records matching the master query, or,
            if no query is given, all IDs in the primary table

        """

        if self._query is None:
            self.build_query()
        if self.manager.UID in self.table.fields:
            fields = (self.table.id, self.table[self.manager.UID])
        else:
            fields = (self.table.id,)
        set = self.db(self._query).select(*fields)
        self._ids = [row.id for row in set]
        if self.manager.UID in self.table.fields:
            self._uids = [row[self.manager.UID] for row in set]


    # Representation ==========================================================

    def __repr__(self):

        """ String representation of this resource """

        if self._set:
            ids = [r.id for r in self]
            return "<S3Resource %s %s>" % (self.tablename, ids)
        else:
            return "<S3Resource %s>" % self.tablename


    # -------------------------------------------------------------------------
    def __len__(self):

        """ The number of records in the current set """

        if self._set is not None:
            return len(self._set)
        else:
            return 0


    # -------------------------------------------------------------------------
    def __nonzero__(self):

        """ Boolean test of this resource """

        return self is not None


    # -------------------------------------------------------------------------
    def __contains__(self, item):

        """ Tests whether a record is currently loaded """

        id = item.get("id", None)
        uid = item.get(self.manager.UID, None)

        if (id or uid) and not self._ids:
            self.__load_ids()
        if id and id in self._ids:
            return 1
        elif uid and uid in self._uids:
            return 1
        else:
            return 0


    # REST Interface ==========================================================

    def execute_request(self, r, **attr):

        """ Execute a request

            @param r: the request to execute
            @type r: S3Request
            @param attr: attributes to pass to method handlers

        """

        r.resource = self
        r.next = None
        hooks = r.response.get(self.HOOKS, None)
        bypass = False
        output = None
        preprocess = None
        postprocess = None

        # Enforce primary record ID
        if not r.id and not r.custom_action and r.representation == "html":
            if r.component or r.method in ("read", "update"):
                count = self.count()
                if self.vars is not None and count == 1:
                    self.load()
                    r.record = self._set.first()
                else:
                    model = self.manager.model
                    search_simple = model.get_method(self.prefix, self.name,
                                                    method="search_simple")
                    if search_simple:
                        redirect(URL(r=r.request, f=self.name, args="search_simple",
                                    vars={"_next": r.same()}))
                    else:
                        r.session.error = self.ERROR.BAD_RECORD
                        redirect(URL(r=r.request, c=self.prefix, f=self.name))

        # Pre-process
        if hooks is not None:
            preprocess = hooks.get("prep", None)
        if preprocess:
            pre = preprocess(r)
            if pre and isinstance(pre, dict):
                bypass = pre.get("bypass", False) is True
                output = pre.get("output", None)
                if not bypass:
                    success = pre.get("success", True)
                    if not success:
                        if r.representation == "html" and output:
                            if isinstance(output, dict):
                                output.update(jr=r)
                            return output
                        else:
                            status = pre.get("status", 400)
                            message = pre.get("message", self.ERROR.BAD_REQUEST)
                            r.error(status, message)
            elif not pre:
                r.error(400, self.ERROR.BAD_REQUEST)

        # Default view
        if r.representation <> "html":
            r.response.view = "xml.html"

        # Method handling
        handler = None
        if not bypass:
            if r.method and r.custom_action:
                handler = r.custom_action
            elif r.http == "GET":
                handler = self.__get(r)
            elif r.http == "PUT":
                handler = self.__put(r)
            elif r.http == "POST":
                handler = self.__post(r)
            elif r.http == "DELETE":
                handler = self.__delete(r)
            else:
                r.error(501, self.ERROR.BAD_METHOD)
            if handler is not None:
                output = handler(r, **attr)
            else:
                output = self.crud(r, **attr)

        # Post-process
        if hooks is not None:
            postprocess = hooks.get("postp", None)
        if postprocess is not None:
            output = postprocess(r, output)
        if output is not None and isinstance(output, dict):
            output.update(jr=r)

        # Redirection (makes no sense in GET)
        if r.next is not None and r.http != "GET":
            if isinstance(output, dict):
                form = output.get("form", None)
                if form and form.errors:
                    return output
            r.session.flash = r.response.flash
            r.session.confirmation = r.response.confirmation
            r.session.error = r.response.error
            r.session.warning = r.response.warning
            redirect(r.next)

        return output


    # -------------------------------------------------------------------------
    def __get(self, r):

        """ Get the GET method handler

            @param r: the S3Request

        """

        method = r.method
        permit = self.permit

        model = self.manager.model

        tablename = r.component and r.component.tablename or r.tablename

        if method is None or method in ("read", "display"):
            authorised = permit("read", tablename)
            if self.__transformable(r):
                method = "export_tree"
            elif r.component:
                if r.multiple and not r.component_id:
                    method = "list"
                else:
                    method = "read"
            else:
                if r.id or method in ("read", "display"):
                    # Enforce single record
                    if not self._set:
                        self.load(start=0, limit=1)
                    if self._set:
                        r.record = self._set[0]
                        r.id = self.get_id()
                        r.uid = self.get_uid()
                    else:
                        r.error(404, self.ERROR.BAD_RECORD)
                    method = "read"
                else:
                    method = "list"

        elif method in ("create", "update"):
            authorised = permit(method, tablename)
            # @todo 2.3: Add user confirmation here:
            if self.__transformable(r, method="import"):
                method = "import_tree"

        elif method == "copy":
            authorised = permit("create", tablename)

        elif method == "delete":
            return self.__delete(r)

        elif method in ("options", "fields", "search", "barchart"):
            authorised = permit("read", tablename)

        elif method == "clear" and not r.component:
            self.manager.clear_session(self.prefix, self.name)
            if "_next" in r.request.vars:
                request_vars = dict(_next=r.request.vars._next)
            else:
                request_vars = {}
            search_simple = model.get_method(self.prefix, self.name,
                                             method="search_simple")
            if r.representation == "html" and search_simple:
                r.next = URL(r=r.request,
                             f=self.name,
                             args="search_simple",
                             vars=request_vars)
            else:
                r.next = URL(r=r.request, f=self.name)
            return None

        else:
            r.error(501, self.ERROR.BAD_METHOD)

        if not authorised:
            r.unauthorised()
        else:
            return self.get_handler(method)


    # -------------------------------------------------------------------------
    def __put(self, r):

        """ Get the PUT method handler

            @param r: the S3Request

        """

        permit = self.permit

        if self.__transformable(r, method="import"):
            authorised = permit("create", self.tablename) and \
                         permit("update", self.tablename)
            if not authorised:
                r.unauthorised()
            else:
                return self.get_handler("import_tree")
        else:
            r.error(501, self.ERROR.BAD_FORMAT)


    # -------------------------------------------------------------------------
    def __post(self, r):

        """ Get the POST method handler

            @param r: the S3Request

        """

        method = r.method

        if method == "delete":
            return self.__delete(r)
        else:
            if self.__transformable(r, method="import"):
                return self.__put(r)
            else:
                post_vars = r.request.post_vars
                table = r.target()[2]
                if "deleted" in table and \
                "id" not in post_vars and "uuid" not in post_vars:
                    original = self.manager.original(table, post_vars)
                    if original and original.deleted:
                        r.request.post_vars.update(id=original.id)
                        r.request.vars.update(id=original.id)
                return self.__get(r)


    # -------------------------------------------------------------------------
    def __delete(self, r):

        """ Get the DELETE method handler

            @param r: the S3Request

        """

        permit = self.permit

        tablename = r.component and r.component.tablename or r.tablename

        authorised = permit("delete", tablename)
        if not authorised:
            r.unauthorised()

        return self.get_handler("delete")


    # -------------------------------------------------------------------------
    def __get_tree(self, r, **attr):

        """ Export this resource in XML or JSON formats

            @param r: the request
            @param attr: request attributes

        """

        json_formats = self.manager.json_formats
        content_type = self.manager.content_type

        if r.representation == "json":
            show_urls = False
            dereference = False
        else:
            show_urls = True
            dereference = True

        # Find XSLT stylesheet
        template = self.stylesheet(r, method="export")

        # Slicing
        start = r.request.vars.get("start", None)
        if start is not None:
            try:
                start = int(start)
            except ValueError:
                start = None
        limit = r.request.vars.get("limit", None)
        if limit is not None:
            try:
                limit = int(limit)
            except ValueError:
                limit = None

        # Default GIS marker
        marker = r.request.vars.get("marker", None)

        # msince
        msince = r.request.vars.get("msince", None)
        if msince is not None:
            tfmt = "%Y-%m-%dT%H:%M:%SZ"
            try:
                (y,m,d,hh,mm,ss,t0,t1,t2) = time.strptime(msince, tfmt)
                msince = datetime.datetime(y,m,d,hh,mm,ss)
            except ValueError:
                msince = None

        # Add stylesheet parameters
        args = Storage()
        if template is not None:
            if r.component:
                args.update(id=r.id, component=r.component.tablename)
            mode = r.request.vars.get("xsltmode", None)
            if mode is not None:
                args.update(mode=mode)

        # Get the exporter, set response headers
        if r.representation in json_formats:
            exporter = self.exporter.json
            r.response.headers["Content-Type"] = \
                content_type.get(r.representation, "text/x-json")
        else:
            exporter = self.exporter.xml
            r.response.headers["Content-Type"] = \
                content_type.get(r.representation, "application/xml")

        # Export the resource
        output = exporter(self,
                          template=template,
                          start=start,
                          limit=limit,
                          marker=marker,
                          msince=msince,
                          show_urls=True,
                          dereference=True, **args)

        # Transformation error?
        if not output:
            r.error(400, "XSLT Transformation Error: %s " % self.xml.error)

        return output

    # -------------------------------------------------------------------------
    def __get_options(self, r, **attr):

        """ Method handler to get field options in the current resource

            @param r: the request
            @param attr: request attributes

        """

        if "field" in r.request.get_vars:
            items = r.request.get_vars["field"]
            if not isinstance(items, (list, tuple)):
                items = [items]
            fields = []
            for item in items:
                f = item.split(",")
                if f:
                    fields.extend(f)
        else:
            fields = None

        if r.representation == "xml":
            return self.options_xml(component=r.component_name, fields=fields)
        elif r.representation == "json":
            return self.options_json(component=r.component_name, fields=fields)
        else:
            r.error(501, self.ERROR.BAD_FORMAT)


    # -------------------------------------------------------------------------
    def __get_fields(self, r, **attr):

        """ Method handler to get all fields in the primary table

            @param r: the request
            @param attr: the request attributes

        """

        if r.representation == "xml":
            return self.fields_xml(component=r.component_name)
        elif r.representation == "json":
            return self.fields_json(component=r.component_name)
        else:
            r.error(501, self.ERROR.BAD_FORMAT)


    # -------------------------------------------------------------------------
    def __read_body(self, r):

        """ Read data from request body

            @param r: the S3Request

        """

        self._files = Storage()
        content_type = r.request.env.get("content_type", None)

        if content_type and content_type.startswith("multipart/"):

            # Get all attached files from POST
            for p in r.request.post_vars.values():
                if isinstance(p, cgi.FieldStorage) and p.filename:
                    self._files[p.filename] = p.file

            # Find the source
            source_name = "%s.%s" % (r.name, r.representation)
            post_vars = r.request.post_vars
            source = post_vars.get(source_name, None)
            if isinstance(source, cgi.FieldStorage):
                if source.filename:
                    source = source.file
                else:
                    source = source.value
            if isinstance(source, basestring):
                source = StringIO.StringIO(source)
        else:
            # Body is source
            source = r.request.body
            source.seek(0)

        return source


    # -------------------------------------------------------------------------
    def __put_tree(self, r, **attr):

        """ Import XML/JSON data

            @param r: the S3Request
            @param attr: the request attributes

        """

        xml = self.xml
        vars = r.request.vars

        json_formats = self.manager.json_formats

        # Get the source
        if r.representation in json_formats:
            if "filename" in vars:
                source = open(vars["filename"])
            elif "fetchurl" in vars:
                import urllib
                source = urllib.urlopen(vars["fetchurl"])
            else:
                source = self.__read_body(r)
            format = r.representation
            if format == "json":
                format = None
            tree = xml.json2tree(source, format=format)
        else:
            if "filename" in vars:
                source = vars["filename"]
            elif "fetchurl" in vars:
                source = vars["fetchurl"]
            else:
                source = self.__read_body(r)
            tree = xml.parse(source)
        if not tree:
            r.error(400, xml.error)

        # Find XSLT stylesheet
        template = self.stylesheet(r, method="import")

        # Transform source
        if template:
            tfmt = "%Y-%m-%d %H:%M:%S"
            args = dict(domain=self.manager.domain,
                        base_url=self.manager.base_url,
                        prefix=self.prefix,
                        name=self.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt))
            tree = xml.transform(tree, template, **args)
            if not tree:
                r.error(400, "XSLT Transformation Error: %s" % self.xml.error)

        if r.method == "create":
            id = None
        else:
            id = r.id
        if "ignore_errors" in r.request.vars:
            ignore_errors = True
        else:
            ignore_errors = False

        success = self.manager.import_tree(self, id, tree,
                                           ignore_errors=ignore_errors)

        if success:
            item = xml.json_message()
        else:
            tree = xml.tree2json(tree)
            r.error(400, self.manager.error, tree=tree)
        return item


    # XML/JSON functions ======================================================

    def export_xml(self, template=None, pretty_print=False, **args):

        """ Export this resource as XML

            @param template: path to the XSLT stylesheet (if not native S3-XML)
            @param pretty_print: insert newlines/indentation in the output
            @param args: arguments to pass to the XSLT stylesheet
            @returns: the XML as string

            @todo 2.3: slicing?

        """

        exporter = self.exporter.xml

        return exporter(self,
                        template=template,
                        pretty_print=pretty_print, **args)


    # -------------------------------------------------------------------------
    def export_json(self, template=None, pretty_print=False, **args):

        """ Export this resource as JSON

            @param template: path to the XSLT stylesheet (if not native S3-JSON)
            @param pretty_print: insert newlines/indentation in the output
            @param args: arguments to pass to the XSLT stylesheet
            @returns: the JSON as string

            @todo 2.3: slicing?

        """

        exporter = self.exporter.json

        return exporter(self,
                        template=template,
                        pretty_print=pretty_print, **args)


    # -------------------------------------------------------------------------
    def import_xml(self, source,
                   files=None,
                   id=None,
                   template=None,
                   ignore_errors=False, **args):

        """ Import data from an XML source into this resource

            @param source: the XML source (or ElementTree)
            @param files: file attachments as {filename:file}
            @param id: the ID or list of IDs of records to update (None for all)
            @param template: the XSLT template
            @param ignore_errors: do not stop on errors (skip invalid elements)
            @param args: arguments to pass to the XSLT template
            @returns: a JSON message as string

            @raise SyntaxError: in case of a parser or transformation error
            @raise IOError: at insufficient permissions

        """


        importer = self.importer.xml

        return importer(self, source,
                        files=files,
                        id=id,
                        template=template,
                        ignore_errors=ignore_errors, **args)


    # -------------------------------------------------------------------------
    def import_json(self, source,
                    files=None,
                    id=None,
                    template=None,
                    ignore_errors=False, **args):

        """ Import data from a JSON source into this resource

            @param source: the JSON source (or ElementTree)
            @param files: file attachments as {filename:file}
            @param id: the ID or list of IDs of records to update (None for all)
            @param template: the XSLT template
            @param ignore_errors: do not stop on errors (skip invalid elements)
            @param args: arguments to pass to the XSLT template
            @returns: a JSON message as string

            @raise SyntaxError: in case of a parser or transformation error
            @raise IOError: at insufficient permissions

        """

        importer = self.importer.json

        return importer(self, source,
                        files=files,
                        id=id,
                        template=template,
                        ignore_errors=ignore_errors, **args)


    # -------------------------------------------------------------------------
    @staticmethod
    def push(url,
             exporter=None,
             template=None,
             xsltmode=None,
             start=None,
             limit=None,
             marker=None,
             msince=None,
             show_urls=True,
             dereference=True,
             content_type=None,
             username=None,
             password=None,
             proxy=None):

        """ Push (=POST) the current resource to a target URL

            @param exporter: the exporter function
            @param template: path to the XSLT stylesheet to be used by the exporter
            @param xsltmode: "mode" parameter for the XSLT stylesheet
            @param start: index of the first record to export (slicing)
            @param limit: maximum number of records to export (slicing)
            @param marker: default map marker URL
            @param msince: export only records which have been modified after
                           this datetime
            @param show_urls: show URLs in the <resource> elements
            @param dereference: include referenced resources in the export
            @param content_type: content type specification for the export
            @param username: username to authenticate at the peer site
            @param password: password to authenticate at the peer site
            @param proxy: URL of the proxy server to use

            @todo 2.3: error handling?

        """

        args = Storage()
        if template and xsltmode:
            args.update(mode=xsltmode)

        data = exporter(start=start,
                        limit=limit,
                        marker=marker,
                        msince=msince,
                        show_urls=show_urls,
                        dereference=dereference,
                        template=template,
                        pretty_print=False, **args)

        if data:
            url_split = url.split("://", 1)
            if len(url_split) == 2:
                protocol, path = url_split
            else:
                protocol, path = http, None
            import urllib2
            req = urllib2.Request(url=url, data=data)
            if content_type:
                req.add_header('Content-Type', content_type)
            handlers = []
            if proxy:
                proxy_handler = urllib2.ProxyHandler({protocol:proxy})
                handlers.append(proxy_handler)
            if username and password:
                # Send auth data unsolicitedly (the only way with Eden instances):
                import base64
                base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
                req.add_header("Authorization", "Basic %s" % base64string)
                # Just in case the peer does not accept that, add a 401 handler:
                passwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
                passwd_manager.add_password(realm=None,
                                            uri=url,
                                            user=username,
                                            passwd=password)
                auth_handler = urllib2.HTTPBasicAuthHandler(passwd_manager)
                handlers.append(auth_handler)
            if handlers:
                opener = urllib2.build_opener(*handlers)
                urllib2.install_opener(opener)
            try:
                f = urllib2.urlopen(req)
            except urllib2.HTTPError, e:
                code = e.code
                message = e.read()
                try:
                    message_json = json.loads(message)
                    message = message_json.get("message", message)
                except:
                    pass
                return xml.json_message(False, code, message)
            else:
                response = f.read()

            return response

        else:
            return None


    # -------------------------------------------------------------------------
    def push_xml(self, url, **args):

        """ Push (=POST) this resource as XML to a target URL

            @param url: the URL to push to
            @param args: see push argument list

            @returns: the response from the peer as string

        """

        exporter = self.exporter.xml
        return self.push(url, exporter=exporter, **args)


    # -------------------------------------------------------------------------
    def push_json(self, url, **args):

        """ Push (=POST) this resource as JSON to a target URL

            @param url: the URL to push to
            @param args: see push argument list

            @returns: the response from the peer as string

        """

        exporter = self.exporter.json
        return self.push(url, exporter=exporter, **args)


    # -------------------------------------------------------------------------
    def fetch(self, url,
              username=None,
              password=None,
              proxy=None,
              json=False,
              template=None,
              ignore_errors=False, **args):

        """ Fetch XML (JSON) data to the current resource from a remote URL

            @param url: the peer URL
            @param username: username to authenticate at the peer site
            @param password: password to authenticate at the peer site
            @param proxy: URL of the proxy server to use
            @param json: use JSON importer instead of XML importer
            @param template: path to the XSLT stylesheet to transform the data
            @param ignore_errors: skip invalid records

        """

        xml = self.xml

        response = None
        url_split = url.split("://", 1)
        if len(url_split) == 2:
            protocol, path = url_split
        else:
            protocol, path = http, None
        import urllib2
        req = urllib2.Request(url=url)
        handlers = []
        if proxy:
            proxy_handler = urllib2.ProxyHandler({protocol:proxy})
            handlers.append(proxy_handler)
        if username and password:
            # Send auth data unsolicitedly (the only way with Eden instances):
            import base64
            base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
            req.add_header("Authorization", "Basic %s" % base64string)
            # Just in case the peer does not accept that, add a 401 handler:
            passwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passwd_manager.add_password(realm=None,
                                        uri=url,
                                        user=username,
                                        passwd=password)
            auth_handler = urllib2.HTTPBasicAuthHandler(passwd_manager)
            handlers.append(auth_handler)
        if handlers:
            opener = urllib2.build_opener(*handlers)
            urllib2.install_opener(opener)
        try:
            f = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            code = e.code
            message = e.read()
            try:
                message_json = json.loads(message)
                message = message_json.get("message", message)
            except:
                pass
            message = "<message>PEER ERROR: %s</message>" % message
            try:
                markup = etree.XML(message)
                message = markup.xpath(".//text()")
                if message:
                    message = " ".join(message)
                else:
                    message = ""
            except etree.XMLSyntaxError:
                pass
            return xml.json_message(False, code, message, tree=None)
        else:
            response = f

        try:
            if json:
                success = self.import_json(response,
                                           template=template,
                                           ignore_errors=ignore_errors,
                                           args=args)
            else:
                success = self.import_xml(response,
                                          template=template,
                                          ignore_errors=ignore_errors,
                                          args=args)
        except IOError, e:
            return xml.json_message(False, 400, "LOCAL ERROR: %s" % e)

        if not success:
            error = self.manager.error
            return xml.json_message(False, 400, "LOCAL ERROR: %s" % error)
        else:
            return xml.json_message()


    # -------------------------------------------------------------------------
    def fetch_xml(self, url,
                  username=None,
                  password=None,
                  proxy=None,
                  template=None,
                  ignore_errors=False, **args):

        """ Fetch resource data from a remote HTTP XML source

            @param url: the URL of the source
            @param username: username to authenticate at the source
            @param password: password to authenticate at the source
            @param proxy: URL of the proxy server to use
            @param template: the URL or path to the XSLT stylesheet
                to transform the import data into S3XML
            @param ignore_errors: skip any invalid records
            @param args: arguments for the XSLT stylesheet

        """

        return self.fetch(url,
                          username=username,
                          password=password,
                          proxy=proxy,
                          json=False,
                          template=template,
                          ignore_errors=ignore_errors, **args)


    # -------------------------------------------------------------------------
    def fetch_json(self, url,
                   username=None,
                   password=None,
                   proxy=None,
                   template=None,
                   ignore_errors=False, **args):

        """ Fetch resource data from a remote HTTP JSON source

            @param url: the URL of the source
            @param username: username to authenticate at the source
            @param password: password to authenticate at the source
            @param proxy: URL of the proxy server to use
            @param template: the URL or path to the XSLT stylesheet
                to transform the import data into S3XML
            @param ignore_errors: skip any invalid records
            @param args: arguments for the XSLT stylesheet

        """

        return self.fetch(url,
                          username=username,
                          password=password,
                          proxy=proxy,
                          json=True,
                          template=template,
                          ignore_errors=ignore_errors, **args)


    # -------------------------------------------------------------------------
    def options(self, component=None, fields=None):

        """ Export field options of this resource as element tree

            @param component: name of the component which the options are
                requested of, None for the primary table
            @param fields: list of names of fields for which the options
                are requested, None for all fields (which have options)

        """

        if component is not None:
            c = self.components.get(component, None)
            if c:
                tree = c.resource.options(fields=fields)
                return tree
            else:
                raise AttributeError
        else:
            tree = self.xml.get_options(self.prefix,
                                                self.name,
                                                fields=fields)
            return tree


    # -------------------------------------------------------------------------
    def options_xml(self, component=None, fields=None):

        """ Export field options of this resource as XML

            @param component: name of the component which the options are
                requested of, None for the primary table
            @param fields: list of names of fields for which the options
                are requested, None for all fields (which have options)

        """

        tree = self.options(component=component, fields=fields)
        return self.xml.tostring(tree, pretty_print=True)


    # -------------------------------------------------------------------------
    def options_json(self, component=None, fields=None):

        """ Export field options of this resource as JSON

            @param component: name of the component which the options are
                requested of, None for the primary table
            @param fields: list of names of fields for which the options
                are requested, None for all fields (which have options)

        """

        tree = etree.ElementTree(self.options(component=component,
                                              fields=fields))
        return self.xml.tree2json(tree, pretty_print=True)


    # -------------------------------------------------------------------------
    def fields(self, component=None):

        """ Export a list of fields in the resource as element tree

            @param component: name of the component to lookup the fields
                              (None for primary table)

        """

        if component is not None:
            c = self.components.get(component, None)
            if c:
                tree = c.resource.fields()
                return tree
            else:
                raise AttributeError
        else:
            tree = self.xml.get_fields(self.prefix, self.name)
            return tree


    # -------------------------------------------------------------------------
    def fields_xml(self, component=None):

        """ Export a list of fields in the resource as XML

            @param component: name of the component to lookup the fields
                              (None for primary table)

        """

        tree = self.fields(component=component)
        return self.xml.tostring(tree, pretty_print=True)


    # -------------------------------------------------------------------------
    def fields_json(self, component=None):

        """ Export a list of fields in the resource as JSON

            @param component: name of the component to lookup the fields
                              (None for primary table)

        """

        tree = etree.ElementTree(self.fields(component=component))
        return self.xml.tree2json(tree, pretty_print=True)


    # CRUD functions ==========================================================

    def create(self,
               onvalidation=None,
               onaccept=None,
               message="Record created",
               download_url=None,
               from_table=None,
               from_record=None,
               map_fields=None,
               link=None,
               format=None):

        """ Provides and processes an Add-form for this resource

            @param onvalidation: onvalidation callback
            @param onaccept: onaccept callback
            @param message: flash message after successul operation
            @param download_url: default download URL of the application
            @param from_table: copy a record from this table
            @param from_record: copy from this record ID
            @param map_fields: field mapping for copying of records
            @param format: the representation format of the request

        """

        # Get the CRUD settings
        settings = self.manager.s3.crud

        # Get the table
        table = self.table

        # Copy data from a previous record?
        data = None
        if from_table is not None:
            if map_fields:
                if isinstance(map_fields, dict):
                    fields = [from_table[map_fields[f]]
                              for f in map_fields
                                  if f in table.fields and
                                  map_fields[f] in from_table.fields and
                                  table[f].writable]
                elif isinstance(map_fields, (list, tuple)):
                    fields = [from_table[f]
                              for f in map_fields
                                  if f in table.fields and
                                  f in from_table.fields and
                                  table[f].writable]
                else:
                    raise TypeError
            else:
                fields = [from_table[f]
                          for f in table.fields
                              if f in from_table.fields and
                              table[f].writable]

            # Audit read => this is a read method, finally
            audit = self.manager.audit
            prefix, name = from_table._tablename.split("_", 1)
            audit("read", prefix, name, record=from_record, representation=format)

            row = self.db(from_table.id == from_record).select(limitby=(0,1), *fields).first()
            if row:
                if isinstance(map_fields, dict):
                    data = Storage([(f, row[map_fields[f]]) for f in map_fields])
                else:
                    data = Storage(row)

            if data:
                missing_fields = Storage()
                for f in table.fields:
                    if f not in data and table[f].writable:
                        missing_fields[f] = table[f].default
                data.update(missing_fields)
                data.update(id=None)

        # Get the form
        form = self.update(None,
                           data=data,
                           onvalidation=onvalidation,
                           onaccept=onaccept,
                           message=message,
                           download_url=download_url,
                           format=format,
                           link=link)

        return form


    # -------------------------------------------------------------------------
    def read(self, id, download_url=None, format=None):

        """ View a record of this resource

            @param id: the ID of the record to display
            @param download_url: download URL for uploaded files in this resource
            @param format: the representation format

        """

        # Get the CRUD settings
        settings = self.manager.s3.crud

        # Get the table
        table = self.table

        # Audit
        audit = self.manager.audit
        audit("read", self.prefix, self.name, record=id, representation=format)

        # Get the form
        form = SQLFORM(table, id,
                       readonly=True,
                       comments=False,
                       showid=False,
                       upload=download_url,
                       formstyle=settings.formstyle)

        return form


    # -------------------------------------------------------------------------
    def update(self, id,
               data=None,
               onvalidation=None,
               onaccept=None,
               message="Record updated",
               download_url=None,
               format=None,
               link=None):

        """ Update form for this resource

            @param id: the ID of the record to update (None to create a new record)
            @param data: the data to prepopulate the form with (only with id=None)
            @param onvalidation: onvalidation callback hook
            @param onaccept: onaccept callback hook
            @param message: success message
            @param download_url: Download URL for uploaded files in this resource
            @param format: the representation format

        """

        # Environment
        session = self.manager.session
        request = self.manager.request
        response = self.manager.response

        # Get the CRUD settings
        s3 = self.manager.s3
        settings = s3.crud

        # Table
        table = self.table
        model = self.manager.model

        # Copy from another record?
        if id is None and data:
            record = Storage(data)
        else:
            record = id

        # Add asterisk to labels of required fields
        labels = Storage()
        mark_required = model.get_config(table, "mark_required")
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
                            continue
                        val, error = v("")
                        if error:
                            required = True
                            break
                if required:
                    labels[field.name] = DIV("%s:" % field.label, SPAN(" *", _class="req"))

        # Get the form
        form = SQLFORM(table,
                       record=record,
                       record_id=id,
                       labels = labels,
                       showid=False,
                       deletable=False,
                       upload=download_url,
                       submit_button=settings.submit_button or self.manager.T("Save"),
                       formstyle=settings.formstyle)

        # Set form name
        formname = "%s/%s" % (self.tablename, form.record_id)

        # Get the proper onvalidation routine
        if isinstance(onvalidation, dict):
            onvalidation = onvalidation.get(self.tablename, [])

        # Run the form
        audit = self.manager.audit
        if form.accepts(request.post_vars,
                        session,
                        formname=formname,
                        onvalidation=onvalidation,
                        keepvalues=False,
                        hideerror=False):

            # Message
            response.flash = message

            # Audit
            if id is None:
                audit("create", self.prefix, self.name, form=form, representation=format)
            else:
                audit("update", self.prefix, self.name, form=form, representation=format)

            # Update super entity links
            model.update_super(table, form.vars)

            # Link record
            if link and form.vars.id:
                linker = self.manager.linker
                if link.linkdir == "to":
                    linker.link(table, form.vars.id, link.linktable, link.linkid,
                                link_class=link.linkclass)
                else:
                    linker.link(link.linktable, link.linkid, table, form.vars.id,
                                link_class=link.linkclass)

            # Store session vars
            if form.vars.id:
                self.lastid = str(form.vars.id)
                self.manager.store_session(self.prefix, self.name, form.vars.id)

            # Execute onaccept
            self.manager.callback(onaccept, form, name=self.tablename)

        elif id:
            # Audit read (user is reading even when not updating the data)
            audit("read", self.prefix, self.name, form=form, representation=format)

        return form


    # -------------------------------------------------------------------------
    def delete(self, ondelete=None, format=None):

        """ Delete all (deletable) records in this resource

            @param ondelete: on-delete callback
            @param format: the representation format of the request

            @returns: number of records deleted

            @todo 2.3: move error message into resource controller
            @todo 2.3: check for integrity error exception explicitly

        """

        settings = self.manager.s3.crud
        archive_not_delete = settings.archive_not_delete

        T = self.manager.T
        INTEGRITY_ERROR = T("Cannot delete whilst there are linked records. Please delete linked records first.")

        self.load()
        records = self.records()

        permit = self.permit
        audit = self.manager.audit

        numrows = 0
        for row in records:
            if permit("delete", self.tablename, row.id):

                # Clear session
                if self.manager.get_session(prefix=self.prefix, name=self.name) == row.id:
                    self.manager.clear_session(prefix=self.prefix, name=self.name)

                # Archive record?
                if archive_not_delete and "deleted" in self.table:
                    self.db(self.table.id == row.id).update(deleted=True)
                    numrows += 1
                    audit("delete", self.prefix, self.name,
                          record=row.id, representation=format)
                    self.manager.model.delete_super(self.table, row)
                    if ondelete:
                        ondelete(row)

                # otherwise: delete record
                else:
                    try:
                        del self.table[row.id]
                    except: # Integrity Error
                        self.manager.session.error = INTEGRITY_ERROR
                    else:
                        numrows += 1
                        audit("delete", self.prefix, self.name,
                              record=row.id, representation=format)
                        self.manager.model.delete_super(self.table, row)
                        if ondelete:
                            ondelete(row)

        return numrows


    # -------------------------------------------------------------------------
    def select(self,
               fields=None,
               left=None,
               start=0,
               limit=None,
               orderby=None,
               linkto=None,
               download_url=None,
               as_page=False,
               as_list=False,
               format=None):

        """ List of all records of this resource

            @param fields: list of fields to display
            @param left: left outer joins
            @param start: index of the first record to display
            @param limit: maximum number of records to display
            @param orderby: orderby for the query
            @param linkto: hook to link record IDs
            @param download_url: the default download URL of the application
            @param as_page: return the list as JSON page
            @param as_list: return the list as Python list
            @param format: the representation format

        """

        db = self.db
        table = self.table
        query = self.get_query()

        if not fields:
            fields = [table.id]
        if limit is not None:
            limitby = (start, start + limit)
        else:
            limitby = None

        # Audit
        audit = self.manager.audit
        audit("list", self.prefix, self.name, representation=format)

        rows = db(query).select(*fields, **dict(left=left,
                                                orderby=orderby,
                                                limitby=limitby))

        if not rows:
            return None
        if as_page:
            represent = self.manager.represent
            items = [[represent(f, record=row, linkto=linkto)
                    for f in fields]
                    for row in rows]

        elif as_list:
            items = rows.as_list()
        else:
            headers = dict(map(lambda f: (str(f), f.label), fields))
            items= S3SQLTable(rows,
                              headers=headers,
                              linkto=linkto,
                              upload=download_url,
                              _id="list", _class="display")

        return items


    # Utilities ===============================================================

    def readable_fields(self, subset=None):

        """ Get a list of all readable fields in the resource table

            @param subset: list of fieldnames to limit the selection to

        """

        table = self.table

        if subset:
            return [table[f] for f in subset
                    if f in table.fields and table[f].readable]
        else:
            return [table[f] for f in table.fields
                    if table[f].readable]


    # -------------------------------------------------------------------------
    def url(self,
            id=None,
            uid=None,
            prefix=None,
            format="html",
            method=None,
            vars=None):

        """ URL of this resource

            @param id: record ID or list of record IDs
            @param uid: record UID or list of record UIDs (ignored if id is specified)
            @param prefix: override current controller prefix
            @param format: representation format
            @param method: URL method
            @param vars: override current URL query

        """

        r = self.manager.request
        v = r.get_vars
        p = prefix or r.controller
        n = self.name
        x = n
        c = None
        args = []
        vars = vars or v or Storage()

        if self.parent:
            n = self.parent.name
            c = self.name
        if c:
            x = c
            args.append(c)
        if id is not None and not id:
            if not self._multiple:
                ids = self.get_id()
                if not isinstance(ids, (list, tuple)):
                    args.append(str(ids))
            elif self.parent and not self.parent._multiple:
                ids = self.parent.get_id()
                if not isinstance(ids, (list, tuple)):
                    args.insert(0, str(ids))
        elif id:
            if isinstance(id, (list, tuple)):
                vars["%s.id" % x] = ",".join(map(str, id))
            else:
                args.append(str(id))
        elif uid:
            if isinstance(uid, (list, tuple)):
                uids = ",".join(map(str, uid))
            else:
                uids = str(uid)
            vars["%s.uid" % x] = uids
        if method:
            args.append(method)
        if format != "html":
            if args:
                args[-1] = "%s.%s" % (args[-1], format)
            else:
                n = "%s.%s" % (n, format)
        return URL(r=r, c=p, f=n, args=args, vars=vars, extension="")


    # -------------------------------------------------------------------------
    def __transformable(self, r, method=None):

        """ Check the request for a transformable format

            @param r: the S3Request
            @param method: "import" for import methods, else None

        """

        format = r.representation
        request = self.manager.request
        if r.component:
            resourcename = r.component.name
        else:
            resourcename = r.name
        if format in ("xml", "json"):
            return True
        if "transform" in request.vars:
            return True
        extension = self.XSLT_EXTENSION
        filename = "%s.%s" % (resourcename, extension)
        if filename in request.post_vars:
            p = request.post_vars[filename]
            if isinstance(p, cgi.FieldStorage) and p.filename:
                return True
        if method != "import":
            method = "export"
        path = self.XSLT_PATH
        filename = "%s.%s" % (method, extension)
        template = os.path.join(r.request.folder, path, format, filename)
        if os.path.exists(template):
            return True
        return False


    # -------------------------------------------------------------------------
    def stylesheet(self, r, method=None):

        """ Find the XSLT stylesheet for a request

            @param r: the S3Request
            @param method: "import" for data imports, else None

        """

        stylesheet = None
        format = r.representation
        if format in ("xml", "json"):
            return stylesheet
        resourcename = r.component and \
                       r.component.name or r.name
        request = r.request
        if "transform" in request.vars:
            return request.vars["transform"]
        extension = self.XSLT_EXTENSION
        filename = "%s.%s" % (resourcename, extension)
        if filename in request.post_vars:
            p = request.post_vars[filename]
            if isinstance(p, cgi.FieldStorage) and p.filename:
                stylesheet = p.file
            return stylesheet
        folder = request.folder
        path = self.XSLT_PATH
        if method != "import":
            method = "export"
        filename = "%s.%s" % (method, extension)
        stylesheet = os.path.join(folder, path, format, filename)
        if not os.path.exists(stylesheet):
            r.error(501, "%s: %s" % (self.ERROR.BAD_TEMPLATE, stylesheet))
        return stylesheet


    # -------------------------------------------------------------------------
    def content_type(self):

        return None

    # -------------------------------------------------------------------------
    def files(self, files=None):

        """ Get/set the list of attached files

            @param files: the file list as dict {filename:file},
                None to not update the current list

            @returns: the file list as dict {filename:file}

        """

        if files is not None:
            self._files = files

        return self._files


# *****************************************************************************
class S3Request(object):

    """ Class to handle requests """

    UNAUTHORISED = "Not Authorised"

    DEFAULT_REPRESENTATION = "html"
    INTERACTIVE_FORMATS = ("html", "popup", "iframe")

    # -------------------------------------------------------------------------
    def __init__(self, manager, prefix, name):

        """ Constructor

            @param manager: the resource controller
            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)

        """

        self.manager = manager

        # Get the environment
        self.session = manager.session or Storage()
        self.request = manager.request
        self.response = manager.response

        # Main resource parameters
        self.prefix = prefix or self.request.controller
        self.name = name or self.request.function

        # Prepare parsing
        self.representation = self.request.extension
        self.http = self.request.env.request_method
        self.extension = False

        self.args = []
        self.id = None
        self.component_name = None
        self.component_id = None
        self.record = None
        self.method = None

        # Parse the request
        self.__parse()

        # Interactive representation format?
        self.representation = self.representation.lower()
        self.interactive = self.representation in self.INTERACTIVE_FORMATS

        # Append component ID to the URL query
        if self.component_name and self.component_id:
            varname = "%s.id" % self.component_name
            if varname in self.request.vars:
                var = self.request.vars[varname]
                if not isinstance(var, (list, tuple)):
                    var = [var]
                var.append(self.component_id)
                self.request.vars[varname] = var
            else:
                self.request.vars[varname] = self.component_id

        # Create the resource
        self.resource = manager._resource(self.prefix, self.name,
                                          id=self.id,
                                          filter=self.response[manager.HOOKS].filter,
                                          vars=self.request.vars,
                                          components=self.component_name)

        self.tablename = self.resource.tablename
        self.table = self.resource.table

        # Check for component
        self.component = None
        self.pkey = None
        self.fkey = None
        self.multiple = True
        if self.component_name:
            c = self.resource.components.get(self.component_name, None)
            if c:
                self.component = c.component
                self.pkey, self.fkey = c.pkey, c.fkey
                self.multiple = self.component.multiple
            else:
                manager.error = "%s not a component of %s" % \
                                (self.component_name, self.resource.tablename)
                raise SyntaxError(manager.error)

        # Find primary record
        uid = self.request.vars.get("%s.uid" % self.name, None)
        if self.component_name:
            cuid = self.request.vars.get("%s.uid" % self.component_name, None)
        else:
            cuid = None

        # Try to load primary record, if expected
        if self.id or self.component_id or \
           uid and not isinstance(uid, (list, tuple)) or \
           cuid and not isinstance(cuid, (list, tuple)):
            # Single record expected
            self.resource.load()
            if len(self.resource) == 1:
                self.record = self.resource.records().first()
                self.id = self.record.id
                self.manager.store_session(self.resource.prefix,
                                           self.resource.name,
                                           self.id)
            else:
                manager.error = self.manager.ERROR.BAD_RECORD
                if self.representation == "html":
                    self.session.error = manager.error
                    redirect(self.there())
                else:
                    raise KeyError(manager.error)

        # Check for custom action
        model = manager.model
        self.custom_action = model.get_method(self.prefix, self.name,
                                              component_name=self.component_name,
                                              method=self.method)


    # -------------------------------------------------------------------------
    def unauthorised(self):

        """ Action upon unauthorised request """

        if self.representation == "html":
            self.session.error = self.UNAUTHORISED
            login = URL(r=self.request,
                        c="default",
                        f="user",
                        args="login",
                        vars={"_next": self.here()})
            redirect(login)
        else:
            raise HTTP(401, body=self.UNAUTHORISED)


    # -------------------------------------------------------------------------
    def error(self, status, message, tree=None):

        """ Action upon error

            @param status: HTTP status code
            @param message: the error message
            @param tree: the tree causing the error

        """

        xml = self.manager.xml

        if self.representation == "html":
            self.session.error = message
            redirect(URL(r=self.request, f="index"))
        else:
            raise HTTP(status,
                       body=xml.json_message(success=False,
                                             status_code=status,
                                             message=message,
                                             tree=tree))


    # Request Parser ==========================================================

    def __parse(self):

        """ Parses a web2py request for the REST interface """

        self.args = []

        model = self.manager.model
        components = [c[0].name
                     for c in model.get_components(self.prefix, self.name)]

        if len(self.request.args) > 0:
            for i in xrange(len(self.request.args)):
                arg = self.request.args[i]
                if "." in arg:
                    arg, ext = arg.rsplit(".", 1)
                    if ext and len(ext) > 0:
                        self.representation = str.lower(ext)
                        self.extension = True
                if arg:
                    self.args.append(str.lower(arg))

            args = self.args
            if args[0].isdigit():
                self.id = args[0]
                if len(args) > 1:
                    if args[1] in components:
                        self.component_name = args[1]
                        if len(args) > 2:
                            if args[2].isdigit():
                                self.component_id = args[2]
                                if len(args) > 3:
                                    self.method = args[3]
                            else:
                                self.method = args[2]
                                if len(args) > 3 and \
                                   args[3].isdigit():
                                    self.component_id = args[3]
                    else:
                        self.method = args[1]
            else:
                if args[0] in components:
                    self.component_name = args[0]
                    if len(args) > 1:
                        if args[1].isdigit():
                            self.component_id = args[1]
                            if len(args) > 2:
                                self.method = args[2]
                        else:
                            self.method = args[1]
                            if len(args) > 2 and args[2].isdigit():
                                self.component_id = args[2]
                else:
                    self.method = args[0]
                    if len(args) > 1 and args[1].isdigit():
                        self.id = args[1]

        if "format" in self.request.get_vars:
            self.representation = str.lower(self.request.get_vars.format)

        if not self.representation:
            self.representation = self.DEFAULT_REPRESENTATION


    # URL helpers =============================================================

    def __next(self, id=None, method=None, representation=None, vars=None):

        """ Returns a URL of the current request

            @param id: the record ID for the URL
            @param method: an explicit method for the URL
            @param representation: the representation for the URL
            @param vars: the URL query variables

        """

        if vars is None:
            vars = self.request.get_vars
        if "format" in vars:
            del vars["format"]

        args = []
        read = False

        component_id = self.component_id
        if id is None:
            id = self.id
        else:
            read = True

        if not representation:
            representation = self.representation
        if method is None:
            method = self.method
        elif method=="":
            method = None
            if not read:
                if self.component:
                    component_id = None
                else:
                    id = None
        else:
            if id is None:
                id = self.id
            else:
                id = str(id)
                if len(id) == 0:
                    id = "[id]"

        if self.component:
            if id:
                args.append(id)
            args.append(self.component_name)
            if component_id:
                args.append(component_id)
            if method:
                args.append(method)
        else:
            if id:
                args.append(id)
            if method:
                args.append(method)

        f = self.request.function
        if not representation==self.DEFAULT_REPRESENTATION:
            if len(args) > 0:
                args[-1] = "%s.%s" % (args[-1], representation)
            else:
                f = "%s.%s" % (f, representation)

        return URL(r=self.request,
                   c=self.request.controller,
                   f=f,
                   args=args, vars=vars)


    # -------------------------------------------------------------------------
    def here(self, representation=None, vars=None):

        """ URL of the current request

            @param representation: the representation for the URL
            @param vars: the URL query variables

        """

        return self.__next(id=self.id, representation=representation, vars=vars)


    # -------------------------------------------------------------------------
    def other(self, method=None, record_id=None, representation=None, vars=None):

        """ URL of a request with different method and/or record_id
            of the same resource

            @param method: an explicit method for the URL
            @param record_id: the record ID for the URL
            @param representation: the representation for the URL
            @param vars: the URL query variables

        """

        return self.__next(method=method, id=record_id,
                           representation=representation, vars=vars)


    # -------------------------------------------------------------------------
    def there(self, representation=None, vars=None):

        """ URL of a HTTP/list request on the same resource

            @param representation: the representation for the URL
            @param vars: the URL query variables

        """

        return self.__next(method="", representation=representation, vars=vars)


    # -------------------------------------------------------------------------
    def same(self, representation=None, vars=None):

        """ URL of the same request with neutralized primary record ID

            @param representation: the representation for the URL
            @param vars: the URL query variables

        """

        return self.__next(id="[id]", representation=representation, vars=vars)


    # Method handler helpers ==================================================

    def target(self):

        """ Get the target table of the current request

            @returns: a tuple of (prefix, name, table, tablename) of the target
                resource of this request

        """

        if self.component is not None:
            return (self.component.prefix,
                    self.component.name,
                    self.component.table,
                    self.component.tablename)
        else:
            return (self.prefix,
                    self.name,
                    self.table,
                    self.tablename)


# *****************************************************************************
