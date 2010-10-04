# -*- coding: utf-8 -*-

""" S3XRC Resource Framework - RESTful API

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

__all__ = ["S3Resource", "S3Request"]

import os, sys, cgi, uuid, datetime, time, urllib, StringIO
import gluon.contrib.simplejson as json

from gluon.storage import Storage
from gluon.sql import Row
from gluon.html import URL
from gluon.http import HTTP, redirect

from lxml import etree
from s3crud import S3CRUDHandler

# *****************************************************************************
class S3Resource(object):

    """ API for resources """

    # -------------------------------------------------------------------------
    def __init__(self, manager, prefix, name,
                 id=None,
                 uid=None,
                 filter=None,
                 url_vars=None,
                 parent=None,
                 components=None,
                 storage=None,
                 debug=None):

        """ Constructor

            @param manager: the resource controller
            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (without prefix)
            @param id: record ID (or list of record IDs)
            @param uid: record UID (or list of record UIDs)
            @param filter: filter query (DAL resources only)
            @param url_vars: dictionary of URL query variables
            @param parent: the parent resource
            @param components: component name (or list of component names)
            @param storage: URL of the data store, None for DAL
            @param debug: whether to write debug messages to stderr or not
            @type debug: bool

        """

        assert manager is not None, "Undefined Resource Manager"
        self.__manager = manager

        self.ERROR = self.__manager.ERROR

        if debug is None:
            self.__debug = self.__manager.debug
        else:
            self.__debug = debug

        self.__permit = self.__manager.auth.shn_has_permission
        self.__accessible = self.__manager.auth.shn_accessible_query

        self.prefix = prefix
        self.name = name
        self.url_vars = None

        self.__query = None
        self.__length = None
        self.__multiple = True

        self.__set = None
        self.__ids = []
        self.__uids = []

        self.__bind(storage)

        self.components = Storage()
        self.parent = parent

        if self.parent is None:
            self.__attach(select=components)
            self.build_query(id=id, uid=uid, filter=filter, url_vars=url_vars)

        self.__files = Storage()

        self.crud = S3CRUDHandler(self.__db, self.__manager)
        self.__handler = Storage(options=self.__get_options,
                                 fields=self.__get_fields,
                                 export_tree=self.__get_tree,
                                 import_tree=self.__put_tree)


    # -------------------------------------------------------------------------
    def __dbg(self, msg):

        """ Write debug messages to stderr.

            @param msg: the debug message

        """

        if self.__debug:
            print >> sys.stderr, "S3Resource: %s" % msg


    # Configuration ===========================================================

    def set_handler(self, method, handler):

        """ Set method handler for this resource

            @param method: the method name
            @param handler: the handler function
            @type handler: handler(S3Request, **attr)

        """

        self.__handler[method] = handler


    # -------------------------------------------------------------------------
    def get_handler(self, method):

        """ Get method handler for this resource

            @param method: the method name
            @returns: the handler function

        """

        return self.__handler.get(method, None)


    # Data binding ============================================================

    def __bind(self, storage):

        """ Bind this resource to model and data store

            @param storage: the URL of the data store, None for DAL
            @type storage: str

        """

        self.__storage = storage

        self.__db = self.__manager.db
        self.tablename = "%s_%s" % (self.prefix, self.name)

        self.table = self.__db.get(self.tablename, None)
        if not self.table:
            raise KeyError("Undefined table: %s" % self.tablename)

        if self.__storage is not None:
            raise NotImplementedError


    # -------------------------------------------------------------------------
    def __attach(self, select=None):

        """ Attach components to this resource

            @param select: name or list of names of components to attach.
                If select is None (default), then all declared components
                of this resource will be attached, to attach none of the
                components, pass an empty list instead.

        """

        if select and not isinstance(select, (list, tuple)):
            select = [select]

        self.components = Storage()

        if self.parent is None:
            components = self.__manager.model.get_components(self.prefix, self.name)

            for i in xrange(len(components)):
                c, pkey, fkey = components[i]

                if select and c.name not in select:
                    continue

                resource = S3Resource(self.__manager, c.prefix, c.name,
                                      parent=self,
                                      storage=self.__storage,
                                      debug=self.__debug)

                self.components[c.name] = Storage(component=c,
                                                   pkey=pkey,
                                                   fkey=fkey,
                                                   resource=resource)


    # -------------------------------------------------------------------------
    def parse_context(self, resource, url_vars):

        c = Storage()
        for k in url_vars:
            if k[:8] == "context.":
                context_name = k[8:]
                context = url_vars[k]
                if not isinstance(context, str):
                    continue

                if context.find(".") > 0:
                    rname, field = context.split(".", 1)
                    if rname in resource.components:
                        table = resource.components[rname].component.table
                    else:
                        continue
                else:
                    rname = resource.name
                    table = resource.table
                    field = context

                if field in table.fields:
                    fieldtype = str(table[field].type)
                else:
                    continue

                multiple = False
                if fieldtype.startswith("reference"):
                    ktablename = fieldtype[10:]
                elif fieldtype.startswith("list:reference"):
                    ktablename = fieldtype[15:]
                    multiple = True
                else:
                    continue

                c[context_name] = Storage(
                    rname = rname,
                    field = field,
                    table = ktablename,
                    multiple = multiple)
            else:
                continue

        return c


    # -------------------------------------------------------------------------
    def url_query(self, resource, url_vars):

        """ URL query parser """

        c = self.parse_context(resource, url_vars)
        q = Storage(context=c)
        for k in url_vars:
            if k.find(".") > 0:
                rname, field = k.split(".", 1)
                if rname == "context":
                    continue
                elif rname == resource.name:
                    table = resource.table
                elif rname in resource.components:
                    table = resource.components[rname].component.table
                elif rname in c.keys():
                    table = self.__db.get(c[rname].table, None)
                    if not table:
                        continue
                else:
                    continue
                if field.find("__") > 0:
                    field, op = field.split("__", 1)
                else:
                    op = "eq"
                if field == "uid":
                    field = self.__manager.UID
                if field not in table.fields:
                    continue
                else:
                    ftype = str(table[field].type)
                    values = url_vars[k]

                    if op in ("lt", "le", "gt", "ge"):
                        if ftype not in ("integer", "double", "date", "time", "datetime"):
                            continue
                        if not isinstance(values, (list, tuple)):
                            values = [values]
                        vlist = []
                        for v in values:
                            if v.find(",") > 0:
                                v = v.split(",", 1)[-1]
                            vlist.append(v)
                        values = vlist
                    elif op == "eq":
                        if isinstance(values, (list, tuple)):
                            values = values[-1]
                        if values.find(",") > 0:
                            values = values.split(",")
                        else:
                            values = [values]
                    elif op == "ne":
                        if not isinstance(values, (list, tuple)):
                            values = [values]
                        vlist = []
                        for v in values:
                            if v.find(",") > 0:
                                v = v.split(",")
                                vlist.extend(v)
                            else:
                                vlist.append(v)
                        values = vlist
                    elif op in ("like", "unlike"):
                        if ftype not in ("string", "text"):
                            continue
                        if not isinstance(values, (list, tuple)):
                            values = [values]
                    elif op in ("in", "ex"):
                        if not ftype.startswith("list:"):
                            continue
                        if not isinstance(values, (list, tuple)):
                            values = [values]
                    else:
                        continue

                    vlist = []
                    for v in values:
                        if ftype == "boolean":
                            if v in ("true", "True"):
                                value = True
                            else:
                                value = False
                        elif ftype == "integer":
                            try:
                                value = float(v)
                            except ValueError:
                                continue
                        elif ftype == "double":
                            try:
                                value = float(v)
                            except ValueError:
                                continue
                        elif ftype == "date":
                            validator = IS_DATE()
                            value, error = validator(v)
                            if error:
                                continue
                        elif ftype == "time":
                            validator = IS_TIME()
                            value, error = validator(v)
                            if error:
                                continue
                        elif ftype == "datetime":
                            tfmt = "%Y-%m-%dT%H:%M:%SZ"
                            try:
                                (y,m,d,hh,mm,ss,t0,t1,t2) = time.strptime(v, tfmt)
                                value = datetime.datetime(y,m,d,hh,mm,ss)
                            except ValueError:
                                continue
                        else:
                            value = v

                        vlist.append(value)
                    values = vlist

                    if values:
                        if rname not in q:
                            q[rname] = Storage()
                        if field not in q[rname]:
                            q[rname][field] = Storage()
                        q[rname][field][op] = values

        return q


    # -------------------------------------------------------------------------
    def build_query(self, id=None, uid=None, filter=None, url_vars=None):

        """ Query builder

            @param id: record ID or list of record IDs to include
            @param uid: record UID or list of record UIDs to include
            @param filter: filtering query (DAL only)
            @param url_vars: dict of URL query variables

        """

        # Initialize
        self.clear()
        self.clear_query()

        xml = self.__manager.xml

        if url_vars:
            url_query = self.url_query(self, url_vars)
            if url_query:
                self.url_vars = url_vars
        else:
            url_query = Storage()

        if self.__storage is None:

            deletion_status = self.__manager.DELETED

            self.__multiple = True # multiple results expected by default

            # Master Query
            if self.__accessible is not None:
                master_query = self.__accessible("read", self.table)
            else:
                master_query = (self.table.id > 0)

            self.__query = master_query

            # Component Query
            if self.parent:

                parent_query = self.parent.get_query()
                if parent_query:
                    self.__query = self.__query & parent_query

                component = self.parent.components.get(self.name, None)
                if component:
                    pkey = component.pkey
                    fkey = component.fkey
                    self.__multiple = component.get("multiple", True)
                    join = self.parent.table[pkey] == self.table[fkey]
                    if str(self.__query).find(str(join)) == -1:
                        self.__query = self.__query & (join)

                if deletion_status in self.table.fields:
                    remaining = (self.table[deletion_status] == False)
                    self.__query = self.__query & remaining

            # Primary Resource Query
            else:

                if id or uid:
                    if self.name not in url_query:
                        url_query[self.name] = Storage()

                # Collect IDs
                if id:
                    if not isinstance(id, (list, tuple)):
                        self.__multiple = False # single result expected
                        id = [id]
                    id_queries = url_query[self.name].get("id", Storage())

                    ne = id_queries.get("ne", [])
                    eq = id_queries.get("eq", [])
                    eq = eq + [v for v in id if v not in eq]

                    if ne and "ne" not in id_queries:
                        id_queries.ne = ne
                    if eq and "eq" not in id_queries:
                        id_queries.eq = eq

                    if "id" not in url_query[self.name]:
                        url_query[self.name]["id"] = id_queries

                # Collect UIDs
                if uid:
                    if not isinstance(uid, (list, tuple)):
                        self.__multiple = False # single result expected
                        uid = [uid]
                    uid_queries = url_query[self.name].get(self.__manager.UID, Storage())

                    ne = uid_queries.get("ne", [])
                    eq = uid_queries.get("eq", [])
                    eq = eq + [v for v in uid if v not in eq]

                    if ne and "ne" not in uid_queries:
                        uid_queries.ne = ne
                    if eq and "eq" not in uid_queries:
                        uid_queries.eq = eq

                    if self.__manager.UID not in url_query[self.name]:
                        url_query[self.name][self.manager.__UID] = uid_queries

                # URL Queries
                contexts = url_query.context
                for rname in url_query:

                    if rname == "context":
                        continue

                    elif contexts and rname in contexts:
                        context = contexts[rname]

                        cname = context.rname
                        if cname != self.name and \
                           cname in self.components:
                            component = self.components[cname]
                            rtable = component.resource.table
                            pkey = component.pkey
                            fkey = component.fkey
                            cjoin = (self.table[pkey]==rtable[fkey])
                        else:
                            rtable = self.table
                            cjoin = None

                        table = self.__db[context.table]
                        if context.multiple:
                            join = (rtable[context.field].contains(table.id))
                        else:
                            join = (rtable[context.field] == table.id)
                        if cjoin:
                            join = (cjoin & join)

                        self.__query = self.__query & join

                        if deletion_status in table.fields:
                            remaining = (table[deletion_status] == False)
                            self.__query = self.__query & remaining

                    elif rname == self.name:
                        table = self.table

                    elif rname in self.components:
                        component = self.components[rname]
                        table = component.resource.table
                        pkey = component.pkey
                        fkey = component.fkey

                        join = (self.table[pkey]==table[fkey])
                        self.__query = self.__query & join

                        if deletion_status in table.fields:
                            remaining = (table[deletion_status] == False)
                            self.__query = self.__query & remaining

                    for field in url_query[rname]:
                        if field in table.fields:
                            for op in url_query[rname][field]:
                                values = url_query[rname][field][op]
                                if field == xml.UID and xml.domain_mapping:
                                    uids = map(xml.import_uid, values)
                                    values = uids
                                if op == "eq":
                                    if len(values) == 1:
                                        if values[0] == "NONE":
                                            query = (table[field] == None)
                                        elif values[0] == "EMPTY":
                                            query = ((table[field] == None) | (table[field] == ""))
                                        else:
                                            query = (table[field] == values[0])
                                    elif len(values):
                                        query = (table[field].belongs(values))
                                elif op == "ne":
                                    if len(values) == 1:
                                        if values[0] == "NONE":
                                            query = (table[field] != None)
                                        elif values[0] == "EMPTY":
                                            query = ((table[field] != None) & (table[field] != ""))
                                        else:
                                            query = (table[field] != values[0])
                                    elif len(values):
                                        query = (~(table[field].belongs(values)))
                                elif op == "lt":
                                    v = values[-1]
                                    query = (table[field] < v)
                                elif op == "le":
                                    v = values[-1]
                                    query = (table[field] <= v)
                                elif op == "gt":
                                    v = values[-1]
                                    query = (table[field] > v)
                                elif op == "ge":
                                    v = values[-1]
                                    query = (table[field] >= v)
                                elif op == "in":
                                    query = None
                                    for v in values:
                                        q = (table[field].contains(v))
                                        if query:
                                            query = query | q
                                        else:
                                            query = q
                                    query = (query)
                                elif op == "ex":
                                    query = None
                                    for v in values:
                                        q = (~(table[field].contains(v)))
                                        if query:
                                            query = query & q
                                        else:
                                            query = q
                                    query = (query)
                                elif op == "like":
                                    query = None
                                    for v in values:
                                        q = (table[field].lower().contains(v.lower()))
                                        if query:
                                            query = query | q
                                        else:
                                            query = q
                                    query = (query)
                                elif op == "unlike":
                                    query = None
                                    for v in values:
                                        q = (~(table[field].lower().contains(v.lower())))
                                        if query:
                                            query = query & q
                                        else:
                                            query = q
                                    query = (query)
                                else:
                                    continue
                                self.__query = self.__query & query

                # Filter
                if filter:
                    self.__query = self.__query & filter

                # Deletion status
                if deletion_status in self.table.fields:
                    remaining = (self.table[deletion_status] == False)
                    self.__query = self.__query & remaining

        else:
            raise NotImplementedError

        return self.__query


    # -------------------------------------------------------------------------
    def add_filter(self, filter=None):

        """ Add a filter to the current query """

        if filter is not None:

            if self.__query:
                query = self.__query
                self.clear()
                self.clear_query()
                self.__query = (query) & (filter)
            else:
                self.build_query(filter=filter)

        return self.__query


    # -------------------------------------------------------------------------
    def get_query(self):

        """ Get the current query for this resource """

        if not self.__query:
            self.build_query()

        return self.__query


    # Data access =============================================================

    def count(self):

        """ Get the total number of available records in this resource """

        if not self.__query:
            self.build_query()
            self.__length = None

        if self.__length is None:

            if self.__storage is None:
                self.__length = self.__db(self.__query).count()
            else:
                raise NotImplementedError

        return self.__length


    # -------------------------------------------------------------------------
    def __load_ids(self):

        """ Loads the IDs of all records matching the master query, or,
            if no query is given, all IDs in the primary table

        """

        if self.__query is None:
            self.build_query()

        if self.__storage is None:

            if self.__manager.UID in self.table.fields:
                fields = (self.table.id, self.table[self.__manager.UID])
            else:
                fields = (self.table.id,)

            set = self.__db(self.__query).select(*fields)
            self.__ids = [row.id for row in set]
            if self.__manager.UID in self.table.fields:
                self.__uids = [row.uid for row in set]

        else:
            raise NotImplementedError


    # -------------------------------------------------------------------------
    def get_id(self):

        """ Returns all IDs of the current set, or, if no set is loaded,
            all IDs of the resource

        """

        if not self.__ids:
            self.__load_ids()

        if not self.__ids:
            return None
        elif len(self.__ids) == 1:
            return self.__ids[0]
        else:
            return self.__ids


    # -------------------------------------------------------------------------
    def get_uid(self):

        """ Returns all UIDs of the current set, or, if no set is loaded,
            all UIDs of the resource

        """

        if self.__manager.UID not in self.table.fields:
            return None

        if not self.__uids:
            self.__load_ids()

        if not self.__uids:
            return None
        elif len(self.__uids) == 1:
            return self.__uids[0]
        else:
            return self.__uids


    # -------------------------------------------------------------------------
    def load(self, start=None, limit=None):

        """ Loads a set of records of the current resource, which can be
            either a slice (for pagination) or all records

            @param start: the index of the first record to load
            @param limit: the maximum number of records to load

        """

        if self.__set is not None:
            self.clear()

        if not self.__query:
            self.build_query()

        if self.__storage is None:

            if not self.__multiple:
                limitby = (0, 1)
            else:
                # Slicing
                if start is not None:
                    self.__slice = True
                    if not limit:
                        limit = self.__manager.ROWSPERPAGE
                    if limit <= 0:
                        limit = 1
                    if start < 0:
                        start = 0
                    limitby = (start, start + limit)
                else:
                    limitby = None

            self.__set = self.__db(self.__query).select(self.table.ALL, limitby=limitby)

            self.__ids = [row.id for row in self.__set]
            uid = self.__manager.UID
            if uid in self.table.fields:
                self.__uids = [row[uid] for row in self.__set]

        else:
            raise NotImplementedError


    # -------------------------------------------------------------------------
    def save(self):

        """ Write the current set to the data store (not implemented yet)

            @todo 2.1: implement this.
        """

        # Not implemented yet
        raise NotImplementedError


    # -------------------------------------------------------------------------
    def clear(self):

        """ Removes the current set """

        self.__set = None
        self.__length = None
        self.__ids = []
        self.__uids = []
        self.__files = Storage()

        self.__slice = False

        if self.components:
            for c in self.components:
                self.components[c].resource.clear()


    # -------------------------------------------------------------------------
    def clear_query(self):

        """ Removes the current query (does not remove the set) """

        self.__query = None

        if self.components:
            for c in self.components:
                self.components[c].resource.clear_query()


    # -------------------------------------------------------------------------
    def records(self):

        """ Get the current set """

        if self.__set is None:
            return []
        else:
            return self.__set


    # -------------------------------------------------------------------------
    def __getitem__(self, key):

        """ Retrieves a record from the current set by its ID

            @param key: the record ID

        """

        if self.__set is None:
            self.load()

        for i in xrange(len(self.__set)):
            row = self.__set[i]
            if str(row.id) == str(key):
                return row

        raise IndexError


    # -------------------------------------------------------------------------
    def __iter__(self):

        """ Generator for the current set """

        if self.__set is None:
            self.load()

        for i in xrange(len(self.__set)):
            yield self.__set[i]

        return


    # -------------------------------------------------------------------------
    def __call__(self, key, component=None):

        """ Retrieves component records of a record in the current set

            @param key: the record ID
            @param component: the name of the component
                (None to get the primary record)

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


    # Representation ==========================================================

    def __repr__(self):

        """ String representation of this resource """

        if self.__set:
            ids = [r.id for r in self]
            return "<S3Resource %s %s>" % (self.tablename, ids)
        else:
            return "<S3Resource %s>" % self.tablename


    # -------------------------------------------------------------------------
    def __len__(self):

        """ The number of records in the current set """

        if self.__set is not None:
            return len(self.__set)
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
        uid = item.get(self.__manager.UID, None)

        if (id or uid) and not self.__ids:
            self.__load_ids()

        if id and id in self.__ids:
            return 1
        elif uid and uid in self.__uids:
            return 1
        else:
            return 0


    # -------------------------------------------------------------------------
    def url(self):

        """ URL of this resource (not implemented yet)

            @todo 2.1: implement this.

        """

        # Not implemented yet
        raise NotImplementedError


    # -------------------------------------------------------------------------
    def files(self):

        """ Get the list of attached files """

        return self.__files


    # REST Interface ==========================================================

    def execute_request(self, r, **attr):

        """ Execute a request on this resource

            @param r: the request to execute
            @type r: S3Request
            @param attr: attributes to pass to method handlers

        """

        self.__dbg("execute_request(%s)" % self)

        r._bind(self) # Bind request to resource
        r.next = None

        bypass = False
        output = None

        hooks = r.response.get(self.__manager.HOOKS, None)
        preprocess = None
        postprocess = None

        # Enforce primary record ID
        if not r.id and not r.custom_action and r.representation == "html":
            if r.component or r.method in ("read", "update"):
                count = self.count()
                if self.url_vars is not None and count == 1:
                    self.load()
                    r.record = self.__set.first()
                else:
                    model = self.__manager.model
                    search_simple = model.get_method(self.prefix, self.name,
                                                    method="search_simple")
                    if search_simple:
                        self.__dbg("no record ID - redirecting to search_simple")
                        redirect(URL(r=r.request, f=self.name, args="search_simple",
                                    vars={"_next": r.same()}))
                    else:
                        r.session.error = self.ERROR.BAD_RECORD
                        redirect(URL(r=r.request, c=self.prefix, f=self.name))

        # Pre-process
        if hooks is not None:
            preprocess = hooks.get("prep", None)
        if preprocess:
            self.__dbg("pre-processing")
            pre = preprocess(r)
            if pre and isinstance(pre, dict):
                bypass = pre.get("bypass", False) is True
                output = pre.get("output", None)
                if not bypass:
                    success = pre.get("success", True)
                    if not success:
                        self.__dbg("pre-process returned an error - aborting")
                        if r.representation == "html" and output:
                            if isinstance(output, dict):
                                output.update(jr=r)
                            return output
                        else:
                            status = pre.get("status", 400)
                            message = pre.get("message", self.ERROR.BAD_REQUEST)
                            raise HTTP(status, message)
            elif not pre:
                self.__dbg("pre-process returned an error - aborting")
                raise HTTP(400, body=self.ERROR.BAD_REQUEST)

        # Default view
        if r.representation <> "html":
            r.response.view = "xml.html"

        # Method handling
        handler = None
        if bypass:
            self.__dbg("bypass directive - skipping method handler")
        else:
            if r.method and r.custom_action:
                self.__dbg("custom method %s" % r.method)
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
                raise HTTP(501, body=self.ERROR.BAD_METHOD)
            if handler is not None:
                self.__dbg("method handler found - executing request")
                output = handler(r, **attr)
            else:
                self.__dbg("no method handler - finalizing request")

        # Post-process
        if hooks is not None:
            postprocess = hooks.get("postp", None)
        if postprocess is not None:
            self.__dbg("post-processing")
            output = postprocess(r, output)

        if output is not None and isinstance(output, dict):
            output.update(jr=r)

        # Redirection (makes no sense in GET)
        if r.next is not None and r.http != "GET" or r.method == "delete":
            if isinstance(output, dict):
                form = output.get("form", None)
                if form and form.errors:
                    return output
            self.__dbg("redirecting to %s" % str(r.next))
            r.session.flash = r.response.flash
            r.session.confirmation = r.response.confirmation
            r.session.error = r.response.error
            r.session.warning = r.response.warning
            redirect(r.next)

        return output


    # -------------------------------------------------------------------------
    def __get(self, r):

        """ Get GET method handler

            @param r: the S3Request

        """

        self.__dbg("GET method")

        method = r.method
        permit = self.__permit

        model = self.__manager.model

        tablename = r.component and r.component.tablename or r.tablename

        xml_export_formats = self.__manager.xml_export_formats
        json_export_formats = self.__manager.json_export_formats
        xml_import_formats = self.__manager.xml_import_formats
        json_import_formats = self.__manager.json_import_formats

        if method is None or method in ("read", "display"):
            authorised = permit("read", tablename)
            if r.representation in xml_export_formats or \
               r.representation in json_export_formats:
                method = "export_tree"
            elif r.component:
                if r.multiple and not r.component_id:
                    method = "list"
                else:
                    method = "read"
            else:
                if r.id or method in ("read", "display"):
                    # Enforce single record
                    if not self.__set:
                        self.load(start=0, limit=1)
                    if self.__set:
                        r.record = self.__set[0]
                        r.id = self.get_id()
                        r.uid = self.get_uid()
                    else:
                        raise HTTP(404, self.ERROR.BAD_RECORD)
                    method = "read"
                else:
                    method = "list"

        elif method in ("create", "update"):
            authorised = permit(method, tablename)
            # TODO: Add user confirmation here:
            if r.representation in xml_import_formats or \
               r.representation in json_import_formats:
                method = "import_tree"

        elif method == "copy":
            authorised = permit("create", tablename)

        elif method == "delete":
            return self.__delete(r)

        elif method in ("options", "fields", "search", "barchart"):
            authorised = permit("read", tablename)

        elif method == "clear" and not r.component:
            self.__manager.clear_session(r.session, self.prefix, self.name)
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
            raise HTTP(501, body=self.ERROR.BAD_METHOD)

        if not authorised:
            r.unauthorised()
        else:
            return self.get_handler(method)


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
            raise HTTP(501, body=self.ERROR.BAD_FORMAT)


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
            raise HTTP(501, body=self.ERROR.BAD_FORMAT)


    # -------------------------------------------------------------------------
    def __get_tree(self, r, **attr):

        """ Method handler to export this resource in XML or JSON formats

            @param r: the request
            @param attr: request attributes

        """

        xml_formats = self.__manager.xml_export_formats
        json_formats = self.__manager.json_export_formats

        template = None
        show_urls = True
        dereference = True

        if r.representation in xml_formats:
            r.response.headers["Content-Type"] = \
                xml_formats.get(r.representation, "application/xml")
        else:
            r.response.headers["Content-Type"] = \
                json_formats.get(r.representation, "text/x-json")
            if r.representation == "json":
                show_urls = False
                dereference = False

        if r.representation not in ("xml", "json"):
            template_name = "%s.%s" % (r.representation,
                                       self.__manager.XSLT_FILE_EXTENSION)

            template = os.path.join(r.request.folder,
                                    self.__manager.XSLT_EXPORT_TEMPLATES,
                                    template_name)

            if not os.path.exists(template):
                raise HTTP(501, body="%s: %s" % (self.ERROR.BAD_TEMPLATE, template))

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

        marker = r.request.vars.get("marker", None)

        msince = r.request.vars.get("msince", None)
        if msince is not None:
            tfmt = "%Y-%m-%dT%H:%M:%SZ"
            try:
                (y,m,d,hh,mm,ss,t0,t1,t2) = time.strptime(msince, tfmt)
                msince = datetime.datetime(y,m,d,hh,mm,ss)
            except ValueError:
                msince = None

        tree = self.__export_tree(start=start,
                                  limit=limit,
                                  marker=marker,
                                  msince=msince,
                                  show_urls=True,
                                  dereference=True)

        if template is not None:
            tfmt = "%Y-%m-%d %H:%M:%S"
            args = dict(domain=self.__manager.domain,
                        base_url=self.__manager.base_url,
                        prefix=self.prefix,
                        name=self.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt))

            if r.component:
                args.update(id=r.id, component=r.component.tablename)

            mode = r.request.vars.get("xsltmode", None)
            if mode is not None:
                args.update(mode=mode)

            tree = self.__manager.xml.transform(tree, template, **args)
            if not tree:
                error = self.__manager.xml.json_message(False, 400,
                            str("XSLT Transformation Error: %s ") % \
                            self.__manager.xml.error)
                raise HTTP(400, body=error)

        if r.representation in xml_formats:
            return self.__manager.xml.tostring(tree, pretty_print=True)
        else:
            return self.__manager.xml.tree2json(tree, pretty_print=True)


    # -------------------------------------------------------------------------
    def __put(self, r):

        """ Get PUT method handler

            @param r: the S3Request

        """

        self.__dbg("PUT method")
        permit = self.__permit

        xml_formats = self.__manager.xml_import_formats
        json_formats = self.__manager.json_import_formats

        if r.representation in xml_formats or \
           r.representation in json_formats:
            authorised = permit("create", self.tablename) and \
                         permit("update", self.tablename)
            if not authorised:
                r.unauthorised()
            else:
                return self.get_handler("import_tree")
        else:
            raise HTTP(501, body=self.ERROR.BAD_FORMAT)


    # -------------------------------------------------------------------------
    def __read_body(self, r):

        """ Read data from request body """

        self.__files = Storage()
        content_type = r.request.env.get("content_type", None)

        if content_type and content_type.startswith("multipart/"):

            # Get all attached files from POST
            for p in r.request.post_vars.values():
                if isinstance(p, cgi.FieldStorage) and p.filename:
                    self.__files[p.filename] = p.file

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

        """ Import XML/JSON data """

        xml = self.__manager.xml
        xml_formats = self.__manager.xml_import_formats

        vars = r.request.vars
        if r.representation in xml_formats:
            if "filename" in vars:
                source = vars["filename"]
            elif "fetchurl" in vars:
                source = vars["fetchurl"]
            else:
                source = self.__read_body(r)
            tree = xml.parse(source)
        else:
            if "filename" in vars:
                source = open(vars["filename"])
            elif "fetchurl" in vars:
                import urllib
                source = urllib.urlopen(vars["fetchurl"])
            else:
                source = self.__read_body(r)
            tree = xml.json2tree(source)

        if not tree:
            item = xml.json_message(False, 400, xml.error)
            raise HTTP(400, body=item)

        # XSLT Transformation
        if not r.representation in ("xml", "json"):
            template_name = "%s.%s" % (r.representation,
                                       self.__manager.XSLT_FILE_EXTENSION)

            template = os.path.join(r.request.folder,
                                    self.__manager.XSLT_IMPORT_TEMPLATES,
                                    template_name)

            if not os.path.exists(template):
                raise HTTP(501, body="%s: %s" % (self.ERROR.BAD_TEMPLATE, template))

            tree = xml.transform(tree, template,
                                 domain=self.__manager.domain,
                                 base_url=self.__manager.base_url)

            if not tree:
                error = xml.json_message(False, 400,
                            str("XSLT Transformation Error: %s ") % \
                            self.__manager.xml.error)
                raise HTTP(400, body=error)

        if r.component:
            skip_resource = True
        else:
            skip_resource = False

        if r.method == "create":
            id = None
        else:
            id = r.id

        if "ignore_errors" in r.request.vars:
            ignore_errors = True
        else:
            ignore_errors = False

        success = self.__import_tree(id, tree,
                                     ignore_errors=ignore_errors)

        if success:
            item = xml.json_message()
        else:
            tree = xml.tree2json(tree)
            item = xml.json_message(False, 400, self.__manager.error, tree=tree)
            raise HTTP(400, body=item)

        #return dict(item=item)
        return item


    # -------------------------------------------------------------------------
    def __post(self, r):

        """ Get POST method handler

            @param r: the S3Request

        """

        self.__dbg("POST method")

        if r.representation in self.__manager.xml_import_formats or \
           r.representation in self.__manager.json_import_formats:
            return self.__put(r)
        else:
            post_vars = r.request.post_vars
            table = r.target()[2]
            if "deleted" in table and \
               "id" not in post_vars and "uuid" not in post_vars:
                original = self.__manager.original(table, post_vars)
                if original and original.deleted:
                    r.request.post_vars.update(id=original.id)
                    r.request.vars.update(id=original.id)
            return self.__get(r)


    # -------------------------------------------------------------------------
    def __delete(self, r):

        """ Get DELETE method handler

            @param r: the S3Request

        """

        self.__dbg("DELETE method")

        permit = self.__permit

        tablename = r.component and r.component.tablename or r.tablename

        if r.id or \
           r.component and r.component_id:
            authorised = permit("delete", tablename, r.id)
            if not authorised:
                r.unauthorised()

            if r.next is None:
                r.next = r.there()
            return self.get_handler("delete")
        else:
            raise HTTP(501, body=self.ERROR.BAD_METHOD)


    # XML/JSON functions ======================================================

    def __export_tree(self,
                      start=None,
                      limit=None,
                      marker=None,
                      msince=None,
                      show_urls=True,
                      dereference=True):

        """ Export this resource as element tree """

        return self.__manager.export_tree(self,
                                          audit=self.__manager.audit,
                                          start=start,
                                          limit=limit,
                                          marker=marker,
                                          msince=msince,
                                          show_urls=show_urls,
                                          dereference=dereference)


    # -------------------------------------------------------------------------
    def export_xml(self, template=None, pretty_print=False, **args):

        """ Export this resource as XML """

        tree = self.__export_tree()

        if tree and template is not None:
            tfmt = "%Y-%m-%d %H:%M:%S"
            args.update(domain=self.__manager.domain,
                        base_url=self.__manager.base_url,
                        prefix=self.prefix,
                        name=self.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt))

            tree = self.__manager.xml.transform(tree, template, **args)

        if tree:
            return self.__manager.xml.tostring(tree, pretty_print=pretty_print)
        else:
            return None


    # -------------------------------------------------------------------------
    def export_json(self, template=None, pretty_print=False, **args):

        """ Export this resource as JSON """

        tree = self.__export_tree()

        if tree and template is not None:
            tfmt = "%Y-%m-%d %H:%M:%S"
            args.update(domain=self.__manager.domain,
                        base_url=self.__manager.base_url,
                        prefix=self.prefix,
                        name=self.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt))

            tree = self.__manager.xml.transform(tree, template, **args)

        if tree:
            return self.__manager.xml.tree2json(tree, pretty_print=pretty_print)
        else:
            return None


    # -------------------------------------------------------------------------
    def __import_tree(self, id, tree,
                      files=None,
                      ignore_errors=False):

        """ Import data from an element tree to this resource

            @param files: file attachments as {filename:file}

            @raise IOError: at insufficient permissions
        """

        json_message = self.__manager.xml.json_message

        if files is not None and isinstance(files, dict):
            self.__files = Storage(files)

        success = self.__manager.import_tree(self, id, tree,
                                             ignore_errors=ignore_errors)

        self.__files = Storage()
        return success


    # -------------------------------------------------------------------------
    def import_xml(self, source,
                   files=None,
                   id=None,
                   template=None,
                   ignore_errors=False, **args):

        """ Import data from an XML source to this resource

            @param source: the XML source (or ElementTree)
            @param files: file attachments as {filename:file}
            @param id: the ID or list of IDs of records to update (None for all)
            @param template: the XSLT template
            @param ignore_errors: do not stop on errors (skip invalid elements)
            @param args: arguments to pass to the XSLT template

            @raise SyntaxError: in case of a parser or transformation error
            @raise IOError: at insufficient permissions

        """

        xml = self.__manager.xml
        permit = self.__permit

        authorised = permit("create", self.table) and \
                     permit("update", self.table)
        if not authorised:
            raise IOError("Insufficient permissions")

        if isinstance(source, etree._ElementTree):
            tree = source
        else:
            tree = xml.parse(source)

        if tree:
            if template is not None:
                tree = xml.transform(tree, template, **args)
                if not tree:
                    raise SyntaxError(xml.error)
            return self.__import_tree(id, tree,
                                      files=files,
                                      ignore_errors=ignore_errors)
        else:
            raise SyntaxError("Invalid XML source")


    # -------------------------------------------------------------------------
    def import_json(self, source,
                    files=None,
                    id=None,
                    template=None,
                    ignore_errors=False, **args):

        """ Import data from a JSON source to this resource

            @param source: the JSON source (or ElementTree)
            @param files: file attachments as {filename:file}
            @param id: the ID or list of IDs of records to update (None for all)
            @param template: the XSLT template
            @param ignore_errors: do not stop on errors (skip invalid elements)
            @param args: arguments to pass to the XSLT template

            @raise SyntaxError: in case of a parser or transformation error
            @raise IOError: at insufficient permissions

        """

        xml = self.__manager.xml
        permit = self.__permit

        authorised = permit("create", self.table) and \
                     permit("update", self.table)
        if not authorised:
            raise IOError("Insufficient permissions")

        if isinstance(source, etree._ElementTree):
            tree = source
        elif isinstance(source, basestring):
            from StringIO import StringIO
            source = StringIO(source)
            tree = xml.json2tree(source)
        else:
            tree = xml.json2tree(source)

        if tree:
            if template is not None:
                tree = xml.transform(tree, template, **args)
                if not tree:
                    raise SyntaxError(xml.error)
            return self.__import_tree(id, tree,
                                      files=files,
                                      ignore_errors=ignore_errors)
        else:
            raise SyntaxError("Invalid JSON source.")


    # -------------------------------------------------------------------------
    def options_tree(self, component=None, fields=None):

        """ Export field options of this resource as element tree """

        if component is not None:
            c = self.components.get(component, None)
            if c:
                tree = c.resource.options_tree(fields=fields)
                return tree
            else:
                raise AttributeError
        else:
            tree = self.__manager.xml.get_options(self.prefix,
                                                  self.name,
                                                  fields=fields)
            return tree


    # -------------------------------------------------------------------------
    def options_xml(self, component=None, fields=None):

        """ Export field options of this resource as XML """

        tree = self.options_tree(component=component, fields=fields)
        return self.__manager.xml.tostring(tree, pretty_print=True)


    # -------------------------------------------------------------------------
    def options_json(self, component=None, fields=None):

        """ Export field options of this resource as JSON """

        tree = etree.ElementTree(self.options_tree(component=component,
                                                   fields=fields))
        return self.__manager.xml.tree2json(tree, pretty_print=True)


    # -------------------------------------------------------------------------
    def fields_tree(self, component=None):

        """ Export a list of fields in the primary table as element tree """

        if component is not None:
            c = self.components.get(component, None)
            if c:
                tree = c.resource.fields_tree()
                return tree
            else:
                raise AttributeError
        else:
            tree = self.__manager.xml.get_fields(self.prefix, self.name)
            return tree


    # -------------------------------------------------------------------------
    def fields_xml(self, component=None):

        """ Export a list of fields in the primary table as XML """

        tree = self.fields_tree(component=component)
        return self.__manager.xml.tostring(tree, pretty_print=True)


    # -------------------------------------------------------------------------
    def fields_json(self, component=None):

        """ Export a list of fields in the primary table as JSON """

        tree = etree.ElementTree(self.fields_tree(component=component))
        return self.__manager.xml.tree2json(tree, pretty_print=True)


    # -------------------------------------------------------------------------
    def __push_tree(self, url,
                    converter=None,
                    template=None,
                    xsltmode=None,
                    content_type=None,
                    username=None,
                    password=None,
                    proxy=None,
                    start=None,
                    limit=None,
                    marker=None,
                    msince=None,
                    show_urls=True,
                    dereference=True):

        """ Push (=POST) the current resource to a target URL """

        if not converter:
            raise SyntaxError

        xml = self.__manager.xml
        response = None

        tree = self.__export_tree(start=start,
                                  limit=limit,
                                  marker=marker,
                                  msince=msince,
                                  show_urls=show_urls,
                                  dereference=dereference)

        if tree:
            if template:
                tfmt = "%Y-%m-%d %H:%M:%S"
                args = dict(domain=self.__manager.domain,
                            base_url=self.__manager.base_url,
                            prefix=self.prefix,
                            name=self.name,
                            utcnow=datetime.datetime.utcnow().strftime(tfmt))

                if xsltmode:
                    args.update(mode=xsltmode)

                tree = xml.transform(tree, template, **args)
            data = converter(tree)

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


    # -------------------------------------------------------------------------
    def push_xml(self, url,
                 template=None,
                 xsltmode=None,
                 username=None,
                 password=None,
                 proxy=None,
                 start=None,
                 limit=None,
                 marker=None,
                 msince=None,
                 show_urls=True,
                 dereference=True):

        """ Push (=POST) this resource as XML to a target URL

            @param url: the URL to push to
            @param template: path to the XSLT stylesheet to use
            @param xsltmode: XSLT stylesheet "mode" parameter
            @param username: username for HTTP basic auth (optional)
            @param password: password for HTTP basic auth (optional)
            @param proxy: proxy server to use (optional)
            @param start: start record (for pagination)
            @param limit: maximum number of records to send (for pagination)
            @param marker: path to the default marker for GIS features
            @param msince: export only records modified after that datetime (ISO-format)
            @param show_urls: show URLs in resource elements
            @param dereference: export referenced objects in the tree

            @returns: the response from the peer as string

        """

        xml = self.__manager.xml

        converter = lambda tree: xml.tostring(tree)
        content_type = "application/xml"

        return self.__push_tree(url,
                                converter=converter,
                                template=template,
                                xsltmode=xsltmode,
                                content_type=content_type,
                                username=username,
                                password=password,
                                proxy=proxy,
                                start=start,
                                limit=limit,
                                marker=marker,
                                msince=msince,
                                show_urls=show_urls,
                                dereference=dereference)

    # -------------------------------------------------------------------------
    def push_json(self, url,
                  template=None,
                  xsltmode=None,
                  username=None,
                  password=None,
                  proxy=None,
                  start=None,
                  limit=None,
                  marker=None,
                  msince=None,
                  show_urls=True,
                  dereference=True):

        """ Push (=POST) this resource as JSON to a target URL

            @param url: the URL to push to
            @param template: path to the XSLT stylesheet to use
            @param xsltmode: XSLT stylesheet "mode" parameter
            @param username: username for HTTP basic auth (optional)
            @param password: password for HTTP basic auth (optional)
            @param proxy: proxy server to use (optional)
            @param start: start record (for pagination)
            @param limit: maximum number of records to send (for pagination)
            @param marker: path to the default marker for GIS features
            @param msince: export only records modified after that datetime (ISO-format)
            @param show_urls: show URLs in resource elements
            @param dereference: export referenced objects in the tree

            @returns: the response from the peer as string

        """

        xml = self.__manager.xml

        converter = lambda tree: xml.tree2json(tree)
        content_type = "text/x-json"

        return self.__push_tree(url,
                                converter=converter,
                                template=template,
                                xsltmode=xsltmode,
                                content_type=content_type,
                                username=username,
                                password=password,
                                proxy=proxy,
                                start=start,
                                limit=limit,
                                marker=marker,
                                msince=msince,
                                show_urls=show_urls,
                                dereference=dereference)


    # -------------------------------------------------------------------------
    def fetch(self, url,
              username=None,
              password=None,
              proxy=None,
              json=False,
              template=None,
              ignore_errors=False, **args):

        """ Fetch data to the current resource from a remote URL """

        xml = self.__manager.xml

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
            error = self.__manager.error
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

        return self.fetch(url,
                          username=username,
                          password=password,
                          proxy=proxy,
                          json=True,
                          template=template,
                          ignore_errors=ignore_errors, **args)



# *****************************************************************************
class S3Request(object):

    """ Class to handle requests """

    DEFAULT_REPRESENTATION = "html"
    UNAUTHORISED = "Not Authorised"

    # -------------------------------------------------------------------------
    def __init__(self, manager, prefix, name,
                 request=None,
                 session=None,
                 response=None,
                 debug=None):

        """ Constructor

            @param manager: the resource controller
            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param request: the web2py request object
            @param session: the session store
            @param response: the web2py response object
            @param debug: whether to print debug messages or not

        """

        assert manager is not None, "Undefined Resource Manager"
        self.__manager = manager

        if debug is None:
            self.debug = self.__manager.debug
        else:
            self.debug = debug

        self.error = None

        self.prefix = prefix or request.controller
        self.name = name or request.function

        self.request = request
        self.response = response
        self.session = session or Storage()

        # Prepare parsing
        self.representation = request.extension
        self.http = request.env.request_method
        self.extension = False

        self.args = []
        self.id = None
        self.component_name = None
        self.component_id = None
        self.record = None
        self.method = None

        # Parse the request
        self.__parse()

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
        self.resource = manager.resource(self.prefix, self.name,
                                         id=self.id,
                                         filter=self.response[manager.HOOKS].filter,
                                         url_vars=self.request.vars,
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
                self.multiple = self.component.attr.get("multiple", True)
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
                self.__manager.store_session(self.session,
                                             self.resource.prefix,
                                             self.resource.name,
                                             self.id)
            else:
                manager.error = "No matching record found"
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
            raise HTTP(401, body = self.UNAUTHORISED)


    # -------------------------------------------------------------------------
    def _bind(self, resource):

        self.resource = resource


    # -------------------------------------------------------------------------
    def __dbg(self, msg):

        if self.debug:
            print >> sys.stderr, "S3Request: %s" % msg


    # Request Parser ==========================================================

    def __parse(self):

        """ Parses a web2py request for the REST interface """

        self.args = []

        model = self.__manager.model
        components = [c[0].name for c in model.get_components(self.prefix, self.name)]

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
            if self.args[0].isdigit():
                self.id = self.args[0]
                if len(self.args) > 1:
                    if self.args[1] in components:
                        self.component_name = self.args[1]
                        if len(self.args) > 2:
                            if self.args[2].isdigit():
                                self.component_id = self.args[2]
                                if len(self.args) > 3:
                                    self.method = self.args[3]
                            else:
                                self.method = self.args[2]
                                if len(self.args) > 3 and \
                                   self.args[3].isdigit():
                                    self.component_id = self.args[3]
                    else:
                        self.method = self.args[1]
            else:
                if self.args[0] in components:
                    self.component_name = self.args[0]
                    if len(self.args) > 1:
                        if self.args[1].isdigit():
                            self.component_id = self.args[1]
                            if len(self.args) > 2:
                                self.method = self.args[2]
                        else:
                            self.method = self.args[1]
                            if len(self.args) > 2 and self.args[2].isdigit():
                                self.component_id = self.args[2]
                else:
                    self.method = self.args[0]
                    if len(self.args) > 1 and self.args[1].isdigit():
                        self.id = self.args[1]

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
                #if self.component:
                    #component_id = None
                    #method = None

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
                #vars.update(format=representation)
                f = "%s.%s" % (f, representation)

        return URL(r=self.request,
                   c=self.request.controller,
                   f=f,
                   args=args, vars=vars)


    # -------------------------------------------------------------------------
    def here(self, representation=None, vars=None):

        """ URL of the current request

            @param representation: the representation for the URL

        """

        return self.__next(id=self.id, representation=representation, vars=vars)


    # -------------------------------------------------------------------------
    def other(self, method=None, record_id=None, representation=None, vars=None):

        """ URL of a request with different method and/or record_id
            of the same resource

            @param method: an explicit method for the URL
            @param record_id: the record ID for the URL
            @param representation: the representation for the URL

        """

        return self.__next(method=method, id=record_id,
                           representation=representation, vars=vars)


    # -------------------------------------------------------------------------
    def there(self, representation=None, vars=None):

        """ URL of a HTTP/list request on the same resource

            @param representation: the representation for the URL

        """

        return self.__next(method="", representation=representation, vars=vars)


    # -------------------------------------------------------------------------
    def same(self, representation=None, vars=None):

        """ URL of the same request with neutralized primary record ID

            @param representation: the representation for the URL

        """

        return self.__next(id="[id]", representation=representation, vars=vars)


    # Method handler helpers ==================================================

    def target(self):

        """ Get the target table of the current request """

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

