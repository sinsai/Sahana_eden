# -*- coding: utf-8 -*-

""" RESTful API

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{gluon}} <http://web2py.com>}
    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

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

__all__ = ["S3Resource", "S3Request", "S3Method"]

import os, sys, cgi, uuid, datetime, time, urllib, StringIO, re
import gluon.contrib.simplejson as json

from gluon.storage import Storage
from gluon.sql import Row, Rows
from gluon.html import *
from gluon.http import HTTP, redirect
from gluon.sqlhtml import SQLTABLE, SQLFORM
from gluon.validators import IS_EMPTY_OR
from gluon.tools import callback

from lxml import etree
from s3tools import SQLTABLES3
from s3import import S3Importer
from s3validators import IS_ONE_OF

# *****************************************************************************
class S3Resource(object):
    """
    API for resources

    """

    def __init__(self, manager, prefix, name,
                 id=None,
                 uid=None,
                 filter=None,
                 vars=None,
                 parent=None,
                 components=None):
        """
        Constructor

        @param manager: the S3ResourceController
        @param prefix: prefix of the resource name (=module name)
        @param name: name of the resource (without prefix)
        @param id: record ID (or list of record IDs)
        @param uid: record UID (or list of record UIDs)
        @param filter: filter query (DAL resources only)
        @param vars: dictionary of URL query variables
        @param parent: the parent resource
        @param components: component name (or list of component names)

        """

        self.manager = manager # S3ResourceController() defined in s3xrc.py
        self.db = manager.db

        self.HOOKS = manager.HOOKS  # "s3"
        self.ERROR = manager.ERROR

        # Export/Import hooks
        self.exporter = manager.exporter
        self.importer = manager.importer

        self.xml = manager.xml

        # XSLT Paths
        self.XSLT_PATH = "static/formats"
        self.XSLT_EXTENSION = "xsl"

        # Authorization hooks
        self.permit = manager.permit
        self.accessible_query = manager.auth.s3_accessible_query

        # Audit hook
        self.audit = manager.audit

        # Basic properties
        self.prefix = prefix
        self.name = name
        self.vars = None # set during build_query

        # Model and Resource Manager
        self.tablename = "%s_%s" % (self.prefix, self.name)
        self.table = self.db.get(self.tablename, None)
        if not self.table:
            raise KeyError("Undefined table: %s" % self.tablename)
        model = self.manager.model

        # The Query
        self.query_builder = manager.query_builder
        self._query = None
        self._multiple = True # multiple results expected by default

        # The Set
        self._rows = None
        self._ids = []
        self._uids = []
        self._length = None
        self._slice = False

        # Request control
        self.lastid = None

        self.files = Storage()

        # Attach components and build initial query
        self.components = Storage()
        self.parent = parent

        if self.parent is None:

            # Attach components as child resources
            if components and not isinstance(components, (list, tuple)):
                components = [components]
            clist = model.get_components(self.prefix, self.name)
            for i in xrange(len(clist)):
                c, pkey, fkey = clist[i]
                if components and c.name not in components:
                    continue
                resource = S3Resource(self.manager, c.prefix, c.name,
                                      parent=self)
                self.components[c.name] = Storage(component=c,
                                                  pkey=pkey,
                                                  fkey=fkey,
                                                  resource=resource,
                                                  filter=None)

            # Build query
            self.build_query(id=id, uid=uid, filter=filter, vars=vars)

        # Store CRUD and other method handlers
        self.crud = self.manager.crud
        # Get default search method for this resource
        self.search = model.get_config(self.table, "search_method", None)
        if not self.search:
            if "name" in self.table:
                T = self.manager.T
                self.search = self.manager.search(
                                name="search_simple",
                                label=T("Name"),
                                comment=T("Enter a name to search for. You may use % as wildcard. Press 'Search' without input to list all items."),
                                field=["name"])
            else:
                self.search = self.manager.search()

        # Store internal handlers
        self._handler = Storage(options=self.__get_options,
                                fields=self.__get_fields,
                                export_tree=self.__get_tree,
                                import_tree=self.__put_tree)

    # Method handler configuration ============================================

    def set_handler(self, method, handler):
        """
        Set a REST method handler for this resource

        @param method: the method name
        @param handler: the handler function
        @type handler: handler(S3Request, **attr)

        """

        self._handler[method] = handler


    # -------------------------------------------------------------------------
    def get_handler(self, method):
        """
        Get a REST method handler for this resource

        @param method: the method name
        @returns: the handler function

        """

        return self._handler.get(method, None)


    # -------------------------------------------------------------------------
    def add_method(self, method, handler):
        """
        Add a REST method for this resource

        @param method: the method name
        @param handler: the handler function
        @type handler: handler(S3Request, **attr)

        """

        model = self.manager.model

        if self.parent:
            model.set_method(self.parent.prefix, self.parent.name,
                             component=self.name, method=method, action=handler)
        else:
            model.set_method(self.prefix,self.name,
                             method=method, action=handler)


    # Query handling ==========================================================

    def build_query(self, id=None, uid=None, filter=None, vars=None):
        """
        Query builder

        @param id: record ID or list of record IDs to include
        @param uid: record UID or list of record UIDs to include
        @param filter: filtering query (DAL only)
        @param vars: dict of URL query variables

        """

        # Reset the rows counter
        self._length = None

        # self.query_builder = manager.query_builder = S3QueryBuilder() defined in s3xrc.py
        return self.query_builder.query(self,
                                        id=id,
                                        uid=uid,
                                        filter=filter,
                                        vars=vars)


    # -------------------------------------------------------------------------
    def add_filter(self, filter=None):
        """
        Extend the current query by a filter query

        @param filter: a web2py Query object

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
    def add_component_filter(self, name, filter=None):
        """
        Extend the filter query of a particular component

        @param name: the name of the component
        @param filter: a web2py Query object

        """

        component = self.components.get(name, None)
        if component is not None:
            if component.filter is not None:
                component.filter = (component.filter) & (filter)
            else:
                component.filter = filter


    # -------------------------------------------------------------------------
    def get_query(self):
        """
        Get the current query for this resource

        """

        if not self._query:
            self.build_query()
        return self._query


    # -------------------------------------------------------------------------
    def clear_query(self):
        """
        Removes the current query (does not remove the set!)

        """

        self._query = None
        if self.components:
            for c in self.components:
                self.components[c].resource.clear_query()


    # Data access =============================================================

    def select(self, *fields, **attributes):
        """
        Select records with the current query

        @param fields: fields to select
        @param attributes: select attributes

        """

        table = self.table
        if self._query is None:
            self.build_query()

        # Get the rows
        rows = self.db(self._query).select(*fields, **attributes)

        # Audit
        audit = self.manager.audit
        try:
            # Audit "read" record by record
            if self.tablename in rows:
                ids = [r[str(self.table.id)] for r in rows]
            else:
                ids = [r.id for r in rows]
            for i in ids:
                audit("read", self.prefix, self.name, record=i)
        except KeyError:
            # Audit "list" if no IDs available
            audit("list", self.prefix, self.name)

        # Keep the rows for later access
        self._rows = rows

        return rows


    # -------------------------------------------------------------------------
    def load(self, start=None, limit=None):
        """
        Simplified syntax for select():
            - reads all fields
            - start+limit instead of limitby

        @param start: the index of the first record to load
        @param limit: the maximum number of records to load

        """

        if self._rows is not None:
            self.clear()

        if not self._query:
            self.build_query()
        if not self._multiple:
            limitby = (0, 1)
        else:
            limitby = self.limitby(start=start, limit=limit)

        if limitby:
            rows = self.select(self.table.ALL, limitby=limitby)
        else:
            rows = self.select(self.table.ALL)

        self._ids = [row.id for row in rows]
        uid = self.manager.UID
        if uid in self.table.fields:
            self._uids = [row[uid] for row in rows]

        return self


    # -------------------------------------------------------------------------
    def insert(self, **fields):
        """
        Insert records into this resource

        @param fields: dict of fields to insert

        """

        # Check permission
        authorised = self.permit("create", self.tablename)
        if not authorised:
            raise IOError("Operation not permitted: INSERT INTO %s" % self.tablename)

        # Insert new record
        record_id = self.table.insert(**fields)

        # Audit
        if record_id:
            record = Storage(fields).update(id=record_id)
            self.audit("create", self.prefix, self.name, form=record)

        return record_id


    # -------------------------------------------------------------------------
    def delete(self, ondelete=None, format=None):
        """
        Delete all (deletable) records in this resource

        @param ondelete: on-delete callback
        @param format: the representation format of the request (optional)

        @returns: number of records deleted

        """

        model = self.manager.model

        settings = self.manager.s3.crud
        archive_not_delete = settings.archive_not_delete

        if "uuid" in self.table.fields:
            records = self.select(self.table.id, self.table.uuid)
        else:
            records = self.select(self.table.id)

        numrows = 0
        for row in records:

            # Check permission to delete this row
            if not self.permit("delete", self.table, record_id=row.id):
                continue

            # Clear session
            if self.manager.get_session(prefix=self.prefix, name=self.name) == row.id:
                self.manager.clear_session(prefix=self.prefix, name=self.name)

            # Test row for deletability
            try:
                del self.table[row.id]
            except:
                self.manager.error = self.ERROR.INTEGRITY_ERROR
            finally:
                # We don't want to delete yet, so let's rollback
                self.db.rollback()

            if self.manager.error != self.ERROR.INTEGRITY_ERROR:
                # Archive record?
                if archive_not_delete and "deleted" in self.table:
                    fields = dict(deleted=True)
                    if "deleted_fk" in self.table:
                        # "Park" foreign keys to resolve constraints,
                        # "un-delete" will have to restore valid FKs from this field!
                        record = self.table[row.id]
                        fk = []
                        for f in self.table.fields:
                            ftype = str(self.table[f].type)
                            if record[f] is not None and \
                               (ftype[:9] == "reference" or \
                                ftype[:14] == "list:reference"):
                                fk.append(dict(f=f, k=record[f]))
                                fields.update({f:None})
                            else:
                                continue
                        if fk:
                            fields.update(deleted_fk=json.dumps(fk))
                    self.db(self.table.id == row.id).update(**fields)
                    numrows += 1
                    self.audit("delete", self.prefix, self.name,
                                record=row.id, representation=format)
                    model.delete_super(self.table, row)
                    if ondelete:
                        callback(ondelete, row)
                # otherwise: delete record
                else:
                    del self.table[row.id]
                    numrows += 1
                    self.audit("delete", self.prefix, self.name,
                                record=row.id, representation=format)
                    model.delete_super(self.table, row)
                    if ondelete:
                        callback(ondelete, row)

        return numrows


    # -------------------------------------------------------------------------
    def update(self, **update_fields):
        """
        Update all records in this resource

        @todo: permission check
        @todo: audit

        @status: uncompleted

        """

        if not self._query:
            self.build_query()

        success = self.db(self._query).update(**update_fields)
        return success


    # -------------------------------------------------------------------------
    def search_simple(self, fields=None, label=None, filterby=None):
        """
        Simple fulltext search

        @param fields: list of fields to search for the label
        @param label: label to be found
        @param filterby: filter query for results

        """

        table = self.table
        prefix = self.prefix
        name = self.name

        model = self.manager.model

        mq = Storage()
        search_fields = Storage()

        if fields and not isinstance(fields, (list, tuple)):
            fields = [fields]
        elif not fields:
            raise SyntaxError("No search fields specified.")

        for f in fields:
            _table = None
            component = None

            if f.find(".") != -1:
                cname, f = f.split(".", 1)
                component, pkey, fkey = model.get_component(prefix, name, cname)
                if component:
                    _table = component.table
                    tablename = component.tablename
                    # Do not add queries for empty component tables
                    if not self.db(_table.id>0).select(_table.id, limitby=(0,1)).first():
                        continue
            else:
                _table = table
                tablename = table._tablename

            if _table and tablename not in mq:
                query = (self.accessible_query("read", _table))
                if "deleted" in _table.fields:
                    query = (query & (_table.deleted == "False"))
                if component:
                    join = (table[pkey] == _table[fkey])
                    query = (query & join)
                mq[_table._tablename] = query

            if _table and f in _table.fields:
                if _table._tablename not in search_fields:
                    search_fields[tablename] = [_table[f]]
                else:
                    search_fields[tablename].append(_table[f])

        if not search_fields:
            return None

        if label and isinstance(label,str):
            labels = label.split()
            results = []

            for l in labels:
                wc = "%"
                _l = "%s%s%s" % (wc, l.lower(), wc)

                query = None
                for tablename in search_fields:
                    hq = mq[tablename]
                    fq = None
                    fields = search_fields[tablename]
                    for f in fields:
                        if fq:
                            fq = (f.lower().like(_l)) | fq
                        else:
                            fq = (f.lower().like(_l))
                    q = hq & fq
                    if query is None:
                        query = q
                    else:
                        query = query | q

                if results:
                    query = (table.id.belongs(results)) & query
                if filterby:
                    query = (filterby) & (query)

                records = self.db(query).select(table.id)
                results = [r.id for r in records]
                if not results:
                    return None

            return results
        else:
            return None


    # -------------------------------------------------------------------------
    def count(self, left=None):
        """
        Get the total number of available records in this resource

        @param left: left joins, if required

        """

        if not self._query:
            self.build_query()

        if self._length is None:
            cnt = self.table[self.table.fields[0]].count()
            row = self.db(self._query).select(cnt, left=left).first()
            if row:
                self._length = row[cnt]

        return self._length


    # -------------------------------------------------------------------------
    def clear(self):
        """
        Removes the current set

        """

        self._rows = None
        self._length = None
        self._ids = []
        self._uids = []
        self.files = Storage()
        self._slice = False

        if self.components:
            for c in self.components:
                self.components[c].resource.clear()


    # -------------------------------------------------------------------------
    def records(self, fields=None):
        """
        Get the current set

        @returns: a Set or an empty list if no set is loaded

        """

        if self._rows is None:
            return Rows(self.db)
        else:
            if fields is not None:
                self._rows.colnames = map(str, fields)
            return self._rows


    # -------------------------------------------------------------------------
    def __getitem__(self, key):
        """
        Retrieves a record from the current set by its ID

        @param key: the record ID
        @returns: a Row

        """

        if self._rows is None:
            self.load()
        for i in xrange(len(self._rows)):
            row = self._rows[i]
            if str(row.id) == str(key):
                return row

        raise IndexError


    # -------------------------------------------------------------------------
    def __iter__(self):
        """
        Iterate over the selected rows

        """

        if self._rows is None:
            self.load()
        for i in xrange(len(self._rows)):
            yield self._rows[i]
        return


    # -------------------------------------------------------------------------
    def __call__(self, key, component=None):
        """
        Retrieves component records of a record in the current set

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
        """
        Returns all IDs of the current set, or, if no set is loaded,
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
        """
        Returns all UIDs of the current set, or, if no set is loaded,
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
        """
        Loads the IDs of all records matching the master query, or,
        if no query is given, all IDs in the primary table

        """

        uid = self.manager.UID

        if self._query is None:
            self.build_query()
        if uid in self.table.fields:
            fields = (self.table.id, self.table[uid])
        else:
            fields = (self.table.id,)

        rows = self.db(self._query).select(*fields)

        self._ids = [row.id for row in rows]

        if uid in self.table.fields:
            self._uids = [row[uid] for row in rows]


    # Representation ==========================================================

    def __repr__(self):
        """
        String representation of this resource

        """

        if self._rows:
            ids = [r.id for r in self]
            return "<S3Resource %s %s>" % (self.tablename, ids)
        else:
            return "<S3Resource %s>" % self.tablename


    # -------------------------------------------------------------------------
    def __len__(self):
        """
        The number of currently loaded rows

        """

        if self._rows is not None:
            return len(self._rows)
        else:
            return 0


    # -------------------------------------------------------------------------
    def __nonzero__(self):
        """
        Boolean test of this resource

        """

        return self is not None


    # -------------------------------------------------------------------------
    def __contains__(self, item):
        """
        Tests whether a record is currently loaded

        """

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
        """
        Execute a HTTP request

        @param r: the request to execute
        @type r: S3Request
        @param attr: attributes to pass to method handlers

        """

        r.resource = self
        r.next = None
        hooks = r.response.get(self.HOOKS, None)    # HOOKS = "s3"
        bypass = False
        output = None
        preprocess = None
        postprocess = None

        # Enforce primary record ID
        if not r.id and r.representation == "html":
            if r.component or r.method in ("read", "update"):
                count = self.count()
                if self.vars is not None and count == 1:
                    self.load()
                    r.record = self._rows.first()
                else:
                    model = self.manager.model
                    if self.search.interactive_search:
                        redirect(URL(r=r.request, f=self.name, args="search",
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
        if r.representation != "html":
            r.response.view = "xml.html"

        # Custom action?
        if not r.custom_action:
            model = self.manager.model
            r.custom_action = model.get_method(r.prefix, r.name,
                                               component_name=r.component_name,
                                               method=r.method)

        # Method handling
        handler = None
        if not bypass:
            # Find the method handler
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
            # Invoke the method handler
            if handler is not None:
                output = handler(r, **attr)
            elif r.method == "search":
                output = self.search(r, **attr)
            else:
                # Fall back to CRUD
                output = self.crud(r, **attr)

        # Post-process
        if hooks is not None:
            postprocess = hooks.get("postp", None)
        if postprocess is not None:
            output = postprocess(r, output)
        if output is not None and isinstance(output, dict):
            # Put a copy of r into the output for the view to be able to make use of it
            output.update(jr=r)

        # Redirection
        if r.next is not None and (r.http != "GET" or r.method == "clear"):
            if isinstance(output, dict):
                form = output.get("form", None)
                if form:
                    if not hasattr(form, "errors"):
                        form = form[0]
                    if form.errors:
                        return output
            r.session.flash = r.response.flash
            r.session.confirmation = r.response.confirmation
            r.session.error = r.response.error
            r.session.warning = r.response.warning
            redirect(r.next)

        return output


    # -------------------------------------------------------------------------
    def __get(self, r):
        """
        Get the GET method handler

        @param r: the S3Request

        """

        method = r.method
        model = self.manager.model

        tablename = r.component and r.component.tablename or r.tablename

        if method is None or method in ("read", "display"):
            if self.__transformable(r):
                method = "export_tree"
            elif r.component:
                if r.interactive and self.count() == 1:
                    # Load the record
                    if not self._rows:
                        self.load(start=0, limit=1)
                    if self._rows:
                        r.record = self._rows[0]
                        r.id = self.get_id()
                        r.uid = self.get_uid()
                if r.multiple and not r.component_id:
                    method = "list"
                else:
                    method = "read"
            else:
                if r.id or method in ("read", "display"):
                    # Enforce single record
                    if not self._rows:
                        self.load(start=0, limit=1)
                    if self._rows:
                        r.record = self._rows[0]
                        r.id = self.get_id()
                        r.uid = self.get_uid()
                    else:
                        r.error(404, self.ERROR.BAD_RECORD)
                    method = "read"
                else:
                    method = "list"

        elif method in ("create", "update"):
            if self.__transformable(r, method="import"):
                method = "import_tree"

        elif method == "delete":
            return self.__delete(r)

        elif method == "clear" and not r.component:
            self.manager.clear_session(self.prefix, self.name)
            if "_next" in r.request.vars:
                request_vars = dict(_next=r.request.vars._next)
            else:
                request_vars = {}
            if r.representation == "html" and self.search.interactive_search:
                r.next = URL(r=r.request,
                             f=self.name,
                             args="search",
                             vars=request_vars)
            else:
                r.next = URL(r=r.request, f=self.name)
            return lambda r, **attr: None

        return self.get_handler(method)


    # -------------------------------------------------------------------------
    def __put(self, r):
        """
        Get the PUT method handler

        @param r: the S3Request

        """

        if self.__transformable(r, method="import"):
            return self.get_handler("import_tree")
        else:
            r.error(501, self.ERROR.BAD_FORMAT)


    # -------------------------------------------------------------------------
    def __post(self, r):
        """
        Get the POST method handler

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
        """
        Get the DELETE method handler

        @param r: the S3Request

        """

        return self.get_handler("delete")


    # -------------------------------------------------------------------------
    def __get_tree(self, r, **attr):
        """
        Export this resource as XML

        @param r: the request
        @param attr: request attributes

        """

        json_formats = self.manager.json_formats
        content_type = self.manager.content_type

        # Find XSLT stylesheet
        stylesheet = self.stylesheet(r, method="export")

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
        if stylesheet is not None:
            if r.component:
                args.update(id=r.id, component=r.component.tablename)
            mode = r.request.vars.get("xsltmode", None)
            if mode is not None:
                args.update(mode=mode)

        # Get the exporter, set response headers
        if r.representation in json_formats:
            as_json = True # convert the output into JSON
            r.response.headers["Content-Type"] = \
                content_type.get(r.representation, "application/json")
        elif r.representation == "rss":
            as_json = False
            r.response.headers["Content-Type"] = \
                content_type.get(r.representation, "application/rss+xml")
        else:
            as_json = False
            r.response.headers["Content-Type"] = \
                content_type.get(r.representation, "text/xml")

        # Export the resource
        exporter = self.exporter.xml
        output = exporter(self,
                          stylesheet=stylesheet,
                          as_json=as_json,
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
        """
        Method handler to get field options in the current resource

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

        only_last = False

        if "only_last" in r.request.get_vars:
            only_last = r.request.get_vars["only_last"]

        if r.representation == "xml":
            return self.options(component=r.component_name,
                                fields=fields)
        elif r.representation == "s3json":
            return self.options(component=r.component_name,
                                fields=fields,
                                only_last=only_last,
                                as_json=True)
        else:
            r.error(501, self.ERROR.BAD_FORMAT)


    # -------------------------------------------------------------------------
    def __get_fields(self, r, **attr):
        """
        Method handler to get all fields in the primary table

        @param r: the request
        @param attr: the request attributes

        """

        if r.representation == "xml":
            return self.fields(component=r.component_name)
        elif r.representation == "s3json":
            return self.fields(component=r.component_name, as_json=True)
        else:
            r.error(501, self.ERROR.BAD_FORMAT)


    # -------------------------------------------------------------------------
    def __read_body(self, r):
        """
        Read data from request body

        @param r: the S3Request

        """

        self.files = Storage()
        content_type = r.request.env.get("content_type", None)

        source = []
        if content_type and content_type.startswith("multipart/"):
            ext = ".%s" % r.representation
            vars = r.request.post_vars
            for v in vars:
                p = vars[v]
                if isinstance(p, cgi.FieldStorage) and p.filename:
                    self.files[p.filename] = p.file
                    if p.filename.endswith(ext):
                        source.append(tuple(v, p.file))
                elif v.endswith(ext):
                    if isinstance(p, cgi.FieldStorage):
                        source.append(tuple(v, p.value))
                    elif isinstance(p, basestring):
                        source.append(tuple(v, StringIO.StringIO(p)))
        else:
            s = r.request.body
            s.seek(0)
            source.append(s)

        return source


    # -------------------------------------------------------------------------
    def __put_tree(self, r, **attr):
        """
        Import data using the XML Importer (transformable XML/JSON/CSV formats)

        @param r: the S3Request
        @param attr: the request attributes

        """

        xml = self.xml
        vars = Storage(r.request.vars)
        auth = self.manager.auth

        # Find all source names in the URL vars
        def findnames(vars, name):
            nlist = []
            if name in vars:
                names = vars[name]
                if isinstance(names, (list, tuple)):
                    names = ",".join(names)
                names = names.split(",")
                for n in names:
                    if n[0] == "(" and ")" in n[1:]:
                        nlist.append(n[1:].split(")", 1))
                    else:
                        nlist.append([None, n])
            return nlist

        filenames = findnames(vars, "filename")
        fetchurls = findnames(vars, "fetchurl")

        # Generate sources list
        json_formats = self.manager.json_formats
        csv_formats = self.manager.csv_formats

        # Get the source
        source = []
        format = r.representation
        if format in json_formats or \
           format in csv_formats:
            if filenames:
                try:
                    for f in filenames:
                        source.append((f[0], open(f[1], "rb")))
                except:
                    source = []
            elif fetchurls:
                import urllib
                try:
                    for u in fetchurls:
                        source.append((u[0], urllib.urlopen(u[1])))
                except:
                    source = []
            elif r.http != "GET":
                source = self.__read_body(r)
        else:
            if filenames:
                source = filenames
            elif fetchurls:
                source = fetchurls
            elif r.http != "GET":
                source = self.__read_body(r)

        if not source:
            if filenames or fetchurls:
                # Error: no source found
                r.error(400, "Invalid source")
            else:
                # GET/create without source: return the resource structure
                opts = vars.get("options", False)
                refs = vars.get("references", False)
                stylesheet = self.stylesheet(r)
                if format in json_formats:
                    as_json = True
                else:
                    as_json = False
                output = self.struct(options=opts,
                                     references=refs,
                                     stylesheet=stylesheet,
                                     as_json=as_json)
                if output is None:
                    # Transformation error
                    r.error(400, self.xml.error)
                return output

        # Find XSLT stylesheet
        stylesheet = self.stylesheet(r, method="import")

        # Target IDs
        if r.method == "create":
            id = None
        else:
            id = r.id

        # Skip invalid records?
        if "ignore_errors" in r.request.vars:
            ignore_errors = True
        else:
            ignore_errors = False

        # Transformation mode?
        if "xsltmode" in r.request.vars:
            args = dict(xsltmode=r.request.vars["xsltmode"])
        else:
            args = dict()

        # Format type?
        if format in json_formats:
            format = "json"
        elif format in csv_formats:
            format = "csv"
        else:
            format = "xml"

        # Import!
        importer = S3Importer(self.manager)
        try:
            return importer.xml(self, source,
                                id=id,
                                format=format,
                                stylesheet=stylesheet,
                                ignore_errors=ignore_errors,
                                **args)
        except IOError:
            auth.permission.fail()
        except SyntaxError:
            e = sys.exc_info()[1]
            r.error(400, e)


    # XML functions ===========================================================

    def export_xml(self,
                   stylesheet=None,
                   as_json=False,
                   pretty_print=False, **args):
        """
        Export this resource as XML

        @param stylesheet: path to the XSLT stylesheet (if not native S3-XML)
        @param as_json: convert the output into JSON
        @param pretty_print: insert newlines/indentation in the output
        @param args: arguments to pass to the XSLT stylesheet
        @returns: the XML as string

        """

        exporter = self.exporter.xml

        return exporter(self,
                        stylesheet=stylesheet,
                        as_json=as_json,
                        pretty_print=pretty_print, **args)


    # -------------------------------------------------------------------------
    def import_xml(self, source,
                   files=None,
                   id=None,
                   stylesheet=None,
                   as_json=False,
                   ignore_errors=False, **args):
        """
        Import data from an XML source into this resource

        @param source: the XML source (or ElementTree)
        @param files: file attachments as {filename:file}
        @param id: the ID or list of IDs of records to update (None for all)
        @param stylesheet: the XSLT stylesheet
        @param as_json: the source is JSONified XML
        @param ignore_errors: do not stop on errors (skip invalid elements)
        @param args: arguments to pass to the XSLT stylesheet
        @returns: a JSON message as string

        @raise SyntaxError: in case of a parser or transformation error
        @raise IOError: at insufficient permissions

        @todo 2.3: deprecate?

        """


        importer = self.importer.xml

        return importer(self, source,
                        files=files,
                        id=id,
                        stylesheet=stylesheet,
                        as_json=as_json,
                        ignore_errors=ignore_errors, **args)


    # -------------------------------------------------------------------------
    def push(self, url,
             stylesheet=None,
             as_json=False,
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
        """
        Push (=POST) the current resource to a target URL

        @param url: the URL to push to
        @param stylesheet: path to the XSLT stylesheet to be used by the exporter
        @param as_json: convert the output into JSON before push
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
        if stylesheet and xsltmode:
            args.update(mode=xsltmode)

        # Use the exporter to produce the XML
        exporter = self.exporter.xml
        data = exporter(start=start,
                        limit=limit,
                        marker=marker,
                        msince=msince,
                        show_urls=show_urls,
                        dereference=dereference,
                        stylesheet=stylesheet,
                        as_json=as_json,
                        pretty_print=False,
                        **args)

        if data:
            # Find the protocol
            url_split = url.split("://", 1)
            if len(url_split) == 2:
                protocol, path = url_split
            else:
                protocol, path = "http", None

            # Generate the request
            import urllib2
            req = urllib2.Request(url=url, data=data)
            if content_type:
                req.add_header('Content-Type', content_type)

            handlers = []

            # Proxy handling
            if proxy:
                proxy_handler = urllib2.ProxyHandler({protocol:proxy})
                handlers.append(proxy_handler)

            # Authentication handling
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

            # Install all handlers
            if handlers:
                opener = urllib2.build_opener(*handlers)
                urllib2.install_opener(opener)

            # Execute the request
            try:
                f = urllib2.urlopen(req)
            except urllib2.HTTPError, e:
                # Peer error => encode as JSON message
                code = e.code
                message = e.read()
                try:
                    # Sahana-Eden would send a JSON message,
                    # try to extract the actual error message:
                    message_json = json.loads(message)
                    message = message_json.get("message", message)
                except:
                    pass
                # @todo: prefix message as peer error?
                return xml.json_message(False, code, message)
            else:
                # Success => return what the peer returns
                response = f.read()
            return response
        else:
            # No data to send
            return None


    # -------------------------------------------------------------------------
    def fetch(self, url,
              username=None,
              password=None,
              proxy=None,
              as_json=False,
              stylesheet=None,
              ignore_errors=False, **args):
        """
        Fetch XML data from a remote URL into the current resource

        @param url: the peer URL
        @param username: username to authenticate at the peer site
        @param password: password to authenticate at the peer site
        @param proxy: URL of the proxy server to use
        @param stylesheet: path to the XSLT stylesheet to transform the data
        @param as_json: source is JSONified XML
        @param ignore_errors: skip invalid records

        """

        xml = self.xml

        response = None
        url_split = url.split("://", 1)
        if len(url_split) == 2:
            protocol, path = url_split
        else:
            protocol, path = "http", None

        # Prepare the request
        import urllib2
        req = urllib2.Request(url=url)
        handlers = []

        # Proxy handling
        if proxy:
            proxy_handler = urllib2.ProxyHandler({protocol:proxy})
            handlers.append(proxy_handler)

        # Authentication handling
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

        # Install all handlers
        if handlers:
            opener = urllib2.build_opener(*handlers)
            urllib2.install_opener(opener)

        # Execute the request
        try:
            f = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            # Peer error
            code = e.code
            message = e.read()
            try:
                # Sahana-Eden would send a JSON message,
                # try to extract the actual error message:
                message_json = json.loads(message)
                message = message_json.get("message", message)
            except:
                pass

            # Prefix as peer error and strip XML markup from the message
            # @todo: better method to do this?
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

            # Encode as JSON message
            return xml.json_message(False, code, message, tree=None)
        else:
            # Successfully downloaded
            response = f

        # Try to import the response
        try:
            success = self.import_xml(response,
                                      stylesheet=stylesheet,
                                      as_json=as_json,
                                      ignore_errors=ignore_errors,
                                      args=args)
        except IOError, e:
            return xml.json_message(False, 400, "LOCAL ERROR: %s" % e)
        if not success:
            error = self.manager.error
            return xml.json_message(False, 400, "LOCAL ERROR: %s" % error)
        else:
            return xml.json_message() # success


    # -------------------------------------------------------------------------
    def options(self, component=None, fields=None, as_json=False):
        """
        Export field options of this resource as element tree

        @param component: name of the component which the options are
            requested of, None for the primary table
        @param fields: list of names of fields for which the options
            are requested, None for all fields (which have options)
        @param as_json: convert the output into JSON
        @param only_last: Obtain the latest record (performance bug fix, 
            timeout at s3_tb_refresh for non-dropdown form fields)
        """

        if component is not None:
            c = self.components.get(component, None)
            if c:
                tree = c.resource.options(fields=fields, only_last=only_last, as_json=as_json)
                return tree
            else:
                raise AttributeError
        else:
            if as_json and only_last and len(fields) == 1:
                component_tablename = "%s_%s" % (self.prefix, self.name)
                field = self.db[component_tablename][fields[0]]
                req = field.requires
                if isinstance(req, IS_EMPTY_OR):
                    req = req.other
                assert(isinstance(req, IS_ONE_OF))
                rows = self.db().select(
                    self.db[req.ktable][req.kfield],
                    orderby=~self.db[req.ktable][req.kfield],
                    limitby=(0, 1))
                res = []
                for row in rows:
                    val = row[req.kfield]
                    res.append({ "@value" : val, "$" : field.represent(val) })
                return json.dumps({ 'option' : res })

            tree = self.xml.get_options(self.prefix,
                                        self.name,
                                        fields=fields)
            tree = etree.ElementTree(tree)

            if as_json:
                return self.xml.tree2json(tree, pretty_print=True)
            else:
                return self.xml.tostring(tree, pretty_print=True)


    # -------------------------------------------------------------------------
    def fields(self, component=None, as_json=False):
        """
        Export a list of fields in the resource as element tree

        @param component: name of the component to lookup the fields
                            (None for primary table)
        @param as_json: convert the output XML into JSON

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

            if as_json:
                return self.xml.tree2json(tree, pretty_print=True)
            else:
                return self.xml.tostring(tree, pretty_print=True)


    # -------------------------------------------------------------------------
    def struct(self,
               options=False,
               references=False,
               stylesheet=None,
               as_json=False,
               as_tree=False):
        """
        Get the structure of the resource

        @param options: include option lists in option fields
        @param references: include option lists even for reference fields
        @param stylesheet: the stylesheet to use for transformation
        @param as_json: convert into JSON after transformation

        """

        # Get the structure of the main resource
        root = etree.Element(self.xml.TAG.root)
        main = self.xml.get_struct(self.prefix, self.name,
                                   parent=root,
                                   options=options,
                                   references=references)

        # Include the selected components
        for c in self.components.values():
            component = c.resource
            prefix = component.prefix
            name = component.name
            sub = self.xml.get_struct(prefix, name,
                                      parent=main,
                                      options=options,
                                      references=references)

        # Transformation
        tree = etree.ElementTree(root)
        if stylesheet is not None:
            tfmt = self.xml.ISOFORMAT
            args = dict(domain=self.manager.domain,
                        base_url=self.manager.s3.base_url,
                        prefix=self.prefix,
                        name=self.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt))

            tree = self.xml.transform(tree, stylesheet, **args)
            if tree is None:
                return None

        # Return tree if requested
        if as_tree:
            return tree

        # Otherwise string-ify it
        if as_json:
            return self.xml.tree2json(tree, pretty_print=True)
        else:
            return self.xml.tostring(tree, pretty_print=True)


    # Utilities ===============================================================

    def readable_fields(self, subset=None):
        """
        Get a list of all readable fields in the resource table

        @param subset: list of fieldnames to limit the selection to

        """

        fkey = None
        table = self.table

        if self.parent:
            component = self.parent.components.get(self.name, None)
            if component:
                fkey = component.fkey

        if subset:
            return [table[f] for f in subset
                    if f in table.fields and table[f].readable and f != fkey]
        else:
            return [table[f] for f in table.fields
                    if table[f].readable and f != fkey]


    # -------------------------------------------------------------------------
    def limitby(self, start=None, limit=None):
        """
        Convert start+limit parameters into a limitby tuple
            - limit without start => start = 0
            - start without limit => limit = ROWSPERPAGE
            - limit 0 (or less)   => limit = 1
            - start less than 0   => start = 0

        @param start: index of the first record to select
        @param limit: maximum number of records to select

        """

        if start is None:
            if not limit:
                return None
            else:
                start = 0

        if not limit:
            limit = self.manager.ROWSPERPAGE
            if limit is None:
                return None

        if limit <= 0:
            limit = 1
        if start < 0:
            start = 0

        return (start, start + limit)


    # -------------------------------------------------------------------------
    def url(self,
            id=None,
            uid=None,
            prefix=None,
            format="html",
            method=None,
            vars=None):
        """
        URL of this resource

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
            elif self.parent:
                ids = self.parent.get_id()
                if not isinstance(ids, (list, tuple)):
                    args.insert(0, str(ids))
        elif id:
            if not isinstance(id, (list, tuple)):
                id = [id]
            if len(id) > 1:
                vars["%s.id" % x] = ",".join(map(str, id))
            else:
                args.append(str(id[0]))
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
        url = URL(r=r, c=p, f=n, args=args, vars=vars, extension="")
        return url


    # -------------------------------------------------------------------------
    def __transformable(self, r, method=None):
        """
        Check the request for a transformable format

        @param r: the S3Request
        @param method: "import" for import methods, else None

        """

        format = r.representation
        stylesheet = self.stylesheet(r, method=method, skip_error=True)

        if format != "xml" and not stylesheet:
            return False
        else:
            return True


    # -------------------------------------------------------------------------
    def stylesheet(self, r, method=None, skip_error=False):
        """
        Find the XSLT stylesheet for a request

        @param r: the S3Request
        @param method: "import" for data imports, else None

        """

        stylesheet = None
        format = r.representation
        request = r.request
        if r.component:
            resourcename = r.component.name
        else:
            resourcename = r.name

        # Native S3XML?
        if format == "xml":
            return stylesheet

        # External stylesheet specified?
        if "transform" in request.vars:
            return request.vars["transform"]

        # Stylesheet attached to the request?
        extension = self.XSLT_EXTENSION
        filename = "%s.%s" % (resourcename, extension)
        if filename in request.post_vars:
            p = request.post_vars[filename]
            if isinstance(p, cgi.FieldStorage) and p.filename:
                stylesheet = p.file
            return stylesheet

        # Internal stylesheet?
        folder = request.folder
        path = self.XSLT_PATH
        if method != "import":
            method = "export"
        filename = "%s.%s" % (method, extension)
        stylesheet = os.path.join(folder, path, format, filename)
        if not os.path.exists(stylesheet):
            if not skip_error:
                r.error(501, "%s: %s" % (self.ERROR.BAD_TEMPLATE, stylesheet))
            else:
                stylesheet = None

        return stylesheet


# *****************************************************************************
class S3Request(object):
    """
    Class to handle HTTP requests

    @todo: integrate into S3Resource

    """

    UNAUTHORISED = "Not Authorised" # @todo: internationalization

    DEFAULT_REPRESENTATION = "html"
    INTERACTIVE_FORMATS = ("html", "popup", "iframe") # @todo: read from settings

    # -------------------------------------------------------------------------
    def __init__(self, manager, prefix, name):
        """
        Constructor

        @param manager: the S3ResourceController
        @param prefix: prefix of the resource name (=module name)
        @param name: name of the resource (=without prefix)

        """

        self.manager = manager # S3ResourceController() defined in s3xrc.py

        # Get the environment
        self.session = manager.session or Storage()
        self.request = manager.request
        self.response = manager.response

        # Main resource parameters
        self.prefix = prefix or self.request.controller
        self.name = name or self.request.function

        # Parse the request
        self.http = self.request.env.request_method
        self.__parse()

        self.custom_action = None

        # Interactive representation format?
        self.interactive = self.representation in self.INTERACTIVE_FORMATS

        # Append component ID to the URL query
        vars = Storage(self.request.get_vars)
        if self.component_name and self.component_id:
            varname = "%s.id" % self.component_name
            if varname in vars:
                var = vars[varname]
                if not isinstance(var, (list, tuple)):
                    var = [var]
                var.append(self.component_id)
                vars[varname] = var
            else:
                vars[varname] = self.component_id

        # Define the target resource
        self.resource = manager.define_resource(self.prefix, self.name,
                                                id=self.id,
                                                filter=self.response[manager.HOOKS].filter, # manager.HOOKS="s3"
                                                vars=vars,
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
                manager.error = "%s not a component of %s" % (
                                        self.component_name,
                                        self.resource.tablename)
                raise SyntaxError(manager.error)

        # Find primary record
        uid = self.request.vars.get("%s.uid" % self.name, None)
        if self.component_name:
            cuid = self.request.vars.get("%s.uid" % self.component_name, None)
        else:
            cuid = None

        # Try to load primary record, if expected
        self.record = None
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
                    self.component = None # => avoid infinite loop
                    redirect(self.there())
                else:
                    raise KeyError(manager.error)


    # -------------------------------------------------------------------------
    def unauthorised(self):
        """
        Action upon unauthorised request

        """

        auth = self.manager.auth
        auth.permission.fail()


    # -------------------------------------------------------------------------
    def error(self, status, message, tree=None, next=None):
        """
        Action upon error

        @param status: HTTP status code
        @param message: the error message
        @param tree: the tree causing the error

        """

        xml = self.manager.xml

        if self.representation == "html":
            self.session.error = message
            if next is not None:
                redirect(next)
            else:
                redirect(URL(r=self.request, f="index"))
        else:
            raise HTTP(status,
                       body=xml.json_message(success=False,
                                             status_code=status,
                                             message=message,
                                             tree=tree))


    # Request Parser ==========================================================

    def __parse(self):
        """
        Parses a web2py request for the REST interface

        """

        request = self.request

        self.id = None
        self.component_name = None
        self.component_id = None
        self.method = None

        representation = request.extension

        # Get the names of all components
        model = self.manager.model
        components = [c[0].name for c in
                      model.get_components(self.prefix, self.name)]


        # Map request args, catch extensions
        f = []
        args = request["args"]
        if len(args) > 4:
            args = args[:4]
        method = self.name
        for arg in args:
            if "." in arg:
                arg, representation = arg.rsplit(".", 1)
            if method is None:
                method = arg
            elif arg.isdigit():
                f.append((method, arg))
                method = None
            else:
                f.append((method, None))
                method = arg
        if method:
            f.append((method, None))

        self.id = f[0][1]

        # Sort out component name and method
        l = len(f)
        if l > 1:
            m = f[1][0].lower()
            i = f[1][1]
            if m in components:
                self.component_name = m
                self.component_id = i
            else:
                self.method = m
                if not self.id:
                    self.id = i
        if self.component_name and l > 2:
            self.method = f[2][0].lower()
            if not self.component_id:
                self.component_id = f[2][1]

        # ?format= overrides extensions
        if "format" in request.vars:
            ext = request.vars["format"]
            if isinstance(ext, list):
                ext = ext[-1]
            representation = ext or representation
        self.representation = representation.lower()

        if not self.representation:
            self.representation = self.DEFAULT_REPRESENTATION


    # URL helpers =============================================================

    def __next(self, id=None, method=None, representation=None, vars=None):
        """
        Returns a URL of the current request

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
        """
        URL of the current request

        @param representation: the representation for the URL
        @param vars: the URL query variables

        """

        return self.__next(id=self.id, representation=representation, vars=vars)


    # -------------------------------------------------------------------------
    def other(self, method=None, record_id=None, representation=None, vars=None):
        """
        URL of a request with different method and/or record_id
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
        """
        URL of a HTTP/list request on the same resource

        @param representation: the representation for the URL
        @param vars: the URL query variables

        """

        return self.__next(method="", representation=representation, vars=vars)


    # -------------------------------------------------------------------------
    def same(self, representation=None, vars=None):
        """
        URL of the same request with neutralized primary record ID

        @param representation: the representation for the URL
        @param vars: the URL query variables

        """

        return self.__next(id="[id]", representation=representation, vars=vars)


    # Method handler helpers ==================================================

    def target(self):
        """
        Get the target table of the current request

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
class S3Method(object):
    """
    REST Method Handler Base Class

    Method handler classes should inherit from this class and implement the
    apply_method() method.

    """

    def __call__(self, r, method=None, **attr):
        """
        Entry point for the REST interface

        @param r: the S3Request
        @param method: the method established by the REST interface
        @param attr: dict of parameters for the method handler

        @returns: output object to send to the view

        """

        # Environment of the request
        self.manager = r.manager
        self.session = r.session
        self.request = r.request
        self.response = r.response

        self.T = self.manager.T
        self.db = self.manager.db

        # Settings
        self.permit = self.manager.auth.s3_has_permission
        self.download_url = self.manager.s3.download_url

        # Init
        self.next = None

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

        # Apply method
        output = self.apply_method(r, **attr)

        # Redirection
        if self.next and self.resource.lastid:
            self.next = str(self.next)
            placeholder = "%5Bid%5D"
            self.next = self.next.replace(placeholder, self.resource.lastid)
            placeholder = "[id]"
            self.next = self.next.replace(placeholder, self.resource.lastid)
        r.next = self.next

        # Add additional view variables (e.g. rheader)
        self._extend_view(output, r, **attr)

        return output


    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
        Stub for apply_method, to be implemented in subclass

        @param r: the S3Request
        @param attr: dictionary of parameters for the method handler

        @returns: output object to send to the view

        """

        output = dict()
        return output


    # Utilities ===============================================================

    @staticmethod
    def _record_id(r):
        """
        Get the ID of the target record of a S3Request

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
        """
        Get a configuration setting of the current table

        @param key: the setting key
        @param default: the default value

        """

        return self.manager.model.get_config(self.table, key, default)


    # -------------------------------------------------------------------------
    @staticmethod
    def _view(r, default, format=None):
        """
        Get the path to the view stylesheet file

        @param r: the S3Request
        @param default: name of the default view stylesheet file
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
        """
        Add additional view variables (invokes all callables)

        @param output: the output dict
        @param r: the S3Request
        @param attr: the view variables (e.g. 'rheader')

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
                    except TypeError:
                        # Argument list failure => pass callable to the view as-is
                        display = handler
                        continue
                    except:
                        # Propagate all other errors to the caller
                        raise
                else:
                    display = handler
                if isinstance(display, dict) and resolve:
                    output.update(**display)
                elif display is not None:
                    output.update(**{key:display})
                elif key in output:
                    del output[key]


# *****************************************************************************
