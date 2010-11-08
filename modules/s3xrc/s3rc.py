# -*- coding: utf-8 -*-

""" S3XRC Resource Framework - Resource Controller

    @version: 2.2.2

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

__all__ = ["S3ResourceController",
           "S3Vector"]

import sys, datetime, time

from gluon.storage import Storage
from gluon.html import URL, A
from gluon.http import HTTP, redirect
from gluon.validators import IS_DATE, IS_TIME
from lxml import etree

from s3xml import S3XML
from s3rest import S3Resource, S3Request
from s3model import S3ResourceModel
from s3crud import S3CRUDHandler, S3SearchSimple
from s3export import S3Exporter
from s3import import S3Importer

# *****************************************************************************
class S3ResourceController(object):

    """ S3 Resource Controller

        @param environment: the environment of this run
        @param domain: name of the current domain
        @param base_url: base URL of this instance
        @param rpp: rows-per-page for server-side pagination
        @param messages: a function to retrieve message URLs tagged for a resource
        @param attr: configuration settings

        @keyword xml_export_formats: XML export format configuration (see 00_settings.py)
        @keyword xml_import_formats: XML import format configuration (see 00_settings.py)
        @keyword json_export_formats: JSON export format configuration (see 00_settings.py)
        @keyword json_import_formats: JSON import format configuration (see 00_settings.py)

        @todo 2.2: move formats into settings
        @todo 2.2: error messages internationalization!

    """

    UID = "uuid"
    DELETED = "deleted"

    HOOKS = "s3"
    RCVARS = "rcvars"

    XSLT_FILE_EXTENSION = "xsl"
    XSLT_IMPORT_TEMPLATES = "static/xslt/import" #@todo 2.2: move into settings
    XSLT_EXPORT_TEMPLATES = "static/xslt/export" #@todo 2.2: move into settings

    ACTION = Storage(
        create="create",
        read="read",
        update="update",
        delete="delete"
    )

    ROWSPERPAGE = 10
    MAX_DEPTH = 10

    # Prefixes of resources that must not be manipulated from remote
    PROTECTED = ("auth", "admin", "s3")

    # Error messages
    ERROR = Storage(
        BAD_RECORD = "Record not found",
        BAD_METHOD = "Unsupported method",
        BAD_FORMAT = "Unsupported data format",
        BAD_REQUEST = "Invalid request",
        BAD_TEMPLATE = "XSLT template not found",
        BAD_RESOURCE = "Nonexistent or invalid resource",
        PARSE_ERROR = "XML parse error",
        TRANSFORMATION_ERROR = "XSLT transformation error",
        BAD_SOURCE = "Invalid XML source",
        NO_MATCH = "No matching element found in the data source",
        VALIDATION_ERROR = "Validation error",
        DATA_IMPORT_ERROR = "Data import error",
        NOT_PERMITTED = "Operation not permitted",
        NOT_IMPLEMENTED = "Not implemented"
    )

    def __init__(self,
                 environment,
                 domain=None, # @todo 2.2: read fromm environment
                 base_url=None, # @todo 2.2: read from environment
                 rpp=None, # @todo 2.2: move into settings
                 messages=None, # @todo 2.2: move into settings
                 **attr):

        # Environment
        environment = Storage(environment)

        self.T = environment.T

        self.db = environment.db
        self.cache = environment.cache

        self.session = environment.session
        self.request = environment.request
        self.response = environment.response

        # Settings
        self.s3 = environment.s3 #@todo 2.2: rename variable?
        #self.settings = self.s3.<what?> @todo 2.2

        self.domain = domain
        self.base_url = base_url
        self.download_url = "%s/default/download" % base_url

        if rpp:
            self.ROWSPERPAGE = rpp

        self.show_ids = False

        # Errors
        self.error = None

        # Toolkits
        self.audit = environment.s3_audit       # Audit
        self.auth = environment.auth            # Auth
        self.gis = environment.gis              # GIS

        self.model = S3ResourceModel(self.db)   # Resource Model, @todo 2.2: reduce parameter list to (self)?
        self.crud = S3CRUDHandler(self)         # CRUD Handler
        self.xml = S3XML(self)                  # XML Toolkit

        # Hooks
        self.permit = self.auth.shn_has_permission  # Permission Checker
        self.messages = None                        # Messages Finder
        self.tree_resolve = None                    # Tree Resolver
        self.sync_resolve = None                    # Sync Resolver
        self.sync_log = None                        # Sync Logger

        # Import/Export formats, @todo 2.2: move into settings
        attr = Storage(attr)

        self.xml_import_formats = attr.get("xml_import_formats", ["xml"])
        self.xml_export_formats = attr.get("xml_export_formats",
                                           dict(xml="application/xml"))

        self.json_import_formats = attr.get("json_import_formats", ["json"])
        self.json_export_formats = attr.get("json_export_formats",
                                            dict(json="text/x-json"))

        self.exporter = S3Exporter(self)    # Resource Exporter
        self.importer = S3Importer(self)    # Resource Importer

        # Method Handlers, @todo 2.2: deprecate?
        self.__handler = Storage()


    # Utilities ===============================================================

    def __fields(self, table, skip=[]):

        """ Finds all readable fields in a table and splits
            them into reference and non-reference fields

            @param table: the DB table
            @param skip: list of field names to skip

        """

        fields = filter(lambda f:
                        f != self.xml.UID and
                        f not in skip and
                        f not in self.xml.IGNORE_FIELDS and
                        str(table[f].type) != "id",
                        table.fields)

        if self.show_ids and "id" not in fields:
            fields.insert(0, "id")

        rfields = filter(lambda f:
                         (str(table[f].type).startswith("reference") or
                          str(table[f].type).startswith("list:reference")) and
                         f not in self.xml.FIELDS_TO_ATTRIBUTES,
                         fields)

        dfields = filter(lambda f:
                         f not in rfields,
                         fields)

        return (rfields, dfields)


    # -------------------------------------------------------------------------
    def __vectorize(self, resource, element,
                    id=None,
                    files=[],
                    validate=None,
                    permit=None,
                    audit=None,
                    sync=None,
                    log=None,
                    tree=None,
                    directory=None,
                    vmap=None,
                    lookahead=True):

        """ Builds a list of vectors from an element

            @param resource: the resource name (=tablename)
            @param element: the element
            @param id: target record ID
            @param validate: validate hook (function to validate record)
            @param permit: permit hook (function to check table permissions)
            @param audit: audit hook (function to audit table access)
            @param sync: sync hook (function to resolve sync conflicts)
            @param log: log hook (function to log imports)
            @param tree: the element tree of the source
            @param directory: the resource directory of the tree
            @param vmap: the vector map for the import
            @param lookahead: resolve any references

        """

        imports = []

        if vmap is not None and element in vmap:
            return imports

        table = self.db[resource]
        original = self.original(table, element)
        record = self.xml.record(table, element,
                                 original=original,
                                 files=files,
                                 validate=validate)

        mtime = element.get(self.xml.MTIME, None)
        if mtime:
            mtime, error = self.validate(table, None, self.xml.MTIME, mtime)
            if error:
                mtime = None

        if not record:
            self.error = self.ERROR.VALIDATION_ERROR
            return None

        if lookahead:
            (rfields, dfields) = self.__fields(table)
            rmap = self.xml.lookahead(table, element, rfields,
                                      directory=directory, tree=tree)
        else:
            rmap = []

        (prefix, name) = resource.split("_", 1)
        onvalidation = self.model.get_config(table, "onvalidation")
        onaccept = self.model.get_config(table, "onaccept")
        vector = S3Vector(self, prefix, name, id,
                          record=record,
                          element=element,
                          mtime=mtime,
                          rmap=rmap,
                          directory=directory,
                          permit=permit,
                          audit=audit,
                          sync=sync,
                          log=log,
                          onvalidation=onvalidation,
                          onaccept=onaccept)

        if vmap is not None:
            vmap[element] = vector

        for r in rmap:
            entry = r.get("entry")
            relement = entry.get("element")
            if relement is None:
                continue
            vectors = self.__vectorize(entry.get("resource"),
                                     relement,
                                     validate=validate,
                                     permit=permit,
                                     audit=audit,
                                     sync=sync,
                                     log=log,
                                     tree=tree,
                                     directory=directory,
                                     vmap=vmap)
            if vectors:
                if entry["vector"] is None:
                    entry["vector"] = vectors[-1]
                imports.extend(vectors)

        imports.append(vector)
        return imports


    # -------------------------------------------------------------------------
    def __directory(self, d, l, k, v, e={}):

        """ Converts a list of dicts into a directory

            @param d: the directory
            @param l: the list
            @param k: the key field
            @param v: the value field
            @param e: directory of elements to exclude

        """

        if not d:
            d = {}

        for i in l:
            if k in i and v in i:
                if not isinstance(i[v], (list, tuple)):
                    vals = [i[v]]
                else:
                    vals = i[v]
                c = e.get(i[k], None)
                if c:
                    vals = [x for x in vals if x not in c]
                if not vals:
                    continue
                if i[k] in d:
                    vals = [x for x in vals if x not in d[i[k]]]
                    d[i[k]] += vals
                else:
                    d[i[k]] = vals
        return d


    # -------------------------------------------------------------------------
    def callback(self, hook, *args, **vars):

        """ Invoke a hook or a list of hooks

            @param hook: the hook function, a list or tuple of hook
                functions, or a tablename-keyed dict of hook functions
            @param args: args (position arguments) to pass to the hook
                function(s)
            @param vars: vars (named arguments) to pass to the hook
                function(s), may contain a name=tablename which is used
                to select a function from the dict (the "name" argument
                will not be passed to the functions)

        """

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


    # REST Functions ==========================================================

    def get_session(self, prefix, name):

        """ Reads the last record ID for a resource from a session

            @param prefix: the prefix of the resource name (=module name)
            @param name: the name of the resource (=without prefix)

        """

        session = self.session

        tablename = "%s_%s" % (prefix, name)
        if self.RCVARS in session and tablename in session[self.RCVARS]:
            return session[self.RCVARS][tablename]
        else:
            return None


    # -------------------------------------------------------------------------
    def store_session(self, prefix, name, id):

        """ Stores a record ID for a resource in a session

            @param prefix: the prefix of the resource name (=module name)
            @param name: the name of the resource (=without prefix)
            @param id: the ID to store

        """

        session = self.session

        if self.RCVARS not in session:
            session[self.RCVARS] = Storage()
        if self.RCVARS in session:
            tablename = "%s_%s" % (prefix, name)
            session[self.RCVARS][tablename] = id

        return True # always return True to make this chainable


    # -------------------------------------------------------------------------
    def clear_session(self, prefix=None, name=None):

        """ Clears one or all record IDs stored in a session

            @param prefix: the prefix of the resource name (=module name)
            @param name: the name of the resource (=without prefix)

        """

        session = self.session

        if prefix and name:
            tablename = "%s_%s" % (prefix, name)
            if self.RCVARS in session and tablename in session[self.RCVARS]:
                del session[self.RCVARS][tablename]
        else:
            if self.RCVARS in session:
                del session[self.RCVARS]

        return True # always return True to make this chainable


    # -------------------------------------------------------------------------
    def set_handler(self, method, handler):

        """ Set the default handler for a resource method

            @todo 2.2: deprecate?

        """

        self.__handler[method] = handler


    # -------------------------------------------------------------------------
    def get_handler(self, method):

        """ Get the default handler for a resource method

            @todo 2.2: deprecate?

        """

        return self.__handler.get(method, None)


    # -------------------------------------------------------------------------
    def _resource(self, prefix, name,
                  id=None,
                  uid=None,
                  filter=None,
                  vars=None,
                  parent=None,
                  components=None,
                  storage=None):

        """ Wrapper function for S3Resource, creates a resource

            @param prefix: the application prefix of the resource
            @param name: the resource name (without prefix)
            @param id: record ID or list of record IDs
            @param uid: record UID or list of record UIDs
            @param filter: web2py query to filter the resource query
            @param vars: dict of URL query parameters
            @param parent: the parent resource (if this is a component)
            @param components: list of component (names)
            @param storage: the data store (None for DB)

        """

        resource = S3Resource(self, prefix, name,
                              id=id,
                              uid=uid,
                              filter=filter,
                              vars=vars,
                              parent=parent,
                              components=components,
                              storage=storage)

        # Set default handlers
        for method in self.__handler:
            resource.set_handler(method, self.__handler[method])

        return resource


    # -------------------------------------------------------------------------
    def _request(self, prefix, name):

        """ Wrapper function for S3Request

            @param prefix: the module prefix of the resource
            @param name: the resource name (without prefix)

        """

        return S3Request(self, prefix, name)


    # -------------------------------------------------------------------------
    def parse_request(self, prefix, name):

        """ Parse an HTTP request and generate the corresponding
            S3Request and S3Resource objects.

            @param prefix: the module prefix of the resource
            @param name: the resource name (without prefix)

        """

        self.error = None

        try:
            req = self._request(prefix, name)
        except SyntaxError:
            raise HTTP(400, body=self.error)
        except KeyError:
            raise HTTP(404, body=self.error)
        except:
            raise

        res = req.resource

        return (res, req)


    # Resource functions ======================================================

    # -------------------------------------------------------------------------
    def validate(self, table, record, fieldname, value):

        """ Validates a single value

            @param table: the DB table
            @param record: the existing DB record
            @param fieldname: name of the field
            @param value: value to check

        """

        field = table.get(fieldname, None)
        if field:
            if record:
                v = record.get(fieldname, None)
                if v and v == value:
                    return (value, None)

            try:
                value, error = field.validate(value)
            except:
                return (None, None)
            else:
                return (value, error)
        else:
            raise AttributeError("No field %s in %s" % (fieldname, table._tablename))


    # -------------------------------------------------------------------------
    def represent(self, field,
                  value=None,
                  record=None,
                  linkto=None,
                  strip_markup=False,
                  xml_escape=False):

        """ Represent a field value

            @param field: the field (Field)
            @param value: the value
            @param record: record to retrieve the value from
            @param linkto: function or format string to link an ID column
            @param strip_markup: strip away markup from representation
            @param xml_escape: XML-escape the output

        """

        NONE = str(self.T("None")).decode("utf-8")

        cache = self.cache

        fname = field.name

        # Get the value
        if record is not None:
            text = val = record[fname]
        else:
            text = val = value

        # Get text representation
        if field.represent:
            text = str(cache.ram("%s_repr_%s" % (field, val),
                                 lambda: field.represent(val),
                                 time_expire=5))
        else:
            if val is None:
                text = NONE
            elif fname == "comments":
                ur = unicode(text, "utf8")
                if len(ur) > 48:
                    text = "%s..." % ur[:45].encode("utf8")
            else:
                text = str(text)

        # Strip away markup from text
        if strip_markup and "<" in text:
            try:
                markup = etree.XML(text)
                text = markup.xpath(".//text()")
                if text:
                    text = " ".join(text)
                else:
                    text = ""
            except etree.XMLSyntaxError:
                pass

        # Link ID field
        if fname == "id" and linkto:
            id = str(val)
            try:
                href = linkto(id)
            except TypeError:
                href = linkto % id
            href = str(href).replace(".aadata", "")
            #href = str(href).replace(".aaData", "")
            return A(text, _href=href).xml()

        # XML-escape text
        elif xml_escape:
            text = self.xml.xml_encode(text)

        try:
            text = text.decode("utf-8")
        except:
            pass

        return text


    # -------------------------------------------------------------------------
    def original(self, table, record):

        """ Find the original record for a possible duplicate:

                - if the record contains a UUID, then only that UUID is used
                    to match the record with an existing DB record

                - otherwise, if the record contains some values for unique fields,
                    all of them must match the same existing DB record

            @param table: the table
            @param record: the record as dict or S3XML Element

        """

        # Get primary keys
        pkeys = [f for f in table.fields if table[f].unique]
        pvalues = Storage()

        # Get the values from record
        if isinstance(record, etree._Element):
            for f in pkeys:
                v = None
                if f == self.xml.UID or f in self.xml.ATTRIBUTES_TO_FIELDS:
                    v = record.get(f, None)
                else:
                    xexpr = "%s[@%s='%s']" % (self.xml.TAG.data, self.xml.ATTRIBUTE.field, f)
                    child = record.xpath(xexpr)
                    if child:
                        child = child[0]
                        v = child.get(self.xml.ATTRIBUTE.value, child.text)
                if v:
                    value = self.xml.xml_decode(v)
                    pvalues[f] = value

        elif isinstance(record, dict):
            for f in pkeys:
                v = record.get(f, None)
                if v:
                    pvalues[f] = v
        else:
            raise TypeError

        # Build match query
        if self.xml.UID in pvalues:
            uid = pvalues[self.xml.UID]
            if self.xml.domain_mapping:
                uid = self.xml.import_uid(uid)
            query = (table[self.xml.UID] == uid)
        else:
            query = None
            for f in pvalues:
                _query = (table[f] == pvalues[f])
                if query is not None:
                    query = query | _query
                else:
                    query = _query

        if query:
            original = self.db(query).select(table.ALL)
            if len(original) == 1:
                return original.first()

        return None


    # -------------------------------------------------------------------------
    def match(self, tree, table, id):

        """ Find the matching element for a record

            @param tree: the S3XML element tree
            @param table: the table
            @param id: the record ID or a list of record IDs

            @returns: a list of matching elements

            @todo 2.2: implement this and use in import_tree()

        """

        raise NotImplementedError


    # -------------------------------------------------------------------------
    def export_tree(self, resource,
                    skip=[],
                    audit=None,
                    start=0,
                    limit=None,
                    marker=None,
                    msince=None,
                    show_urls=True,
                    dereference=True):

        """ Export a resource as S3XML element tree

            @param resource: the resource
            @param skip: list of fieldnames to skip
            @param audit: audit hook function
            @param start: index of the first record to export
            @param limit: maximum number of records to export
            @param marker: URL of the GIS default marker
            @param msince: to export only records which have been modified
                after that date/time (minimum modification date/time)
            @param show_urls: show URLs in resource elements
            @param dereference: export referenced resources in the tree

        """

        prefix = resource.prefix
        name = resource.name
        tablename = resource.tablename
        table = resource.table

        (rfields, dfields) = self.__fields(resource.table, skip=skip)

        if self.xml.filter_mci and "mci" in table.fields:
            mci_filter = (table.mci >= 0)
            resource.add_filter(mci_filter)

        # Total number of results
        results = resource.count()

        # Load slice
        resource.load(start=start, limit=limit)

        # Load component records
        crfields = Storage()
        cdfields = Storage()
        for c in resource.components.values():
            cresource = c.resource

            if self.xml.filter_mci and "mci" in cresource.table.fields:
                mci_filter = (cresource.table.mci >= 0)
                cresource.add_filter(mci_filter)

            cresource.load()
            ctablename = cresource.tablename
            crfields[ctablename], \
            cdfields[ctablename] = self.__fields(cresource.table, skip=skip)

        # Resource base URL
        if self.base_url:
            url = "%s/%s/%s" % (self.base_url, prefix, name)
        else:
            url = "/%s/%s" % (prefix, name)

        element_list = []
        export_map = Storage()
        reference_map = []

        for record in resource:
            if audit:
                audit(self.ACTION["read"], prefix, name,
                      record=record.id,
                      representation="xml")

            if show_urls:
                resource_url = "%s/%s" % (url, record.id)
            else:
                resource_url = None

            msince_add = True
            if msince is not None and self.xml.MTIME in record:
                if record[self.xml.MTIME] < msince:
                    msince_add = False

            rmap = self.xml.rmap(table, record, rfields)
            element = self.xml.element(table, record,
                                       fields=dfields,
                                       url=resource_url,
                                       download_url=self.download_url,
                                       marker=marker)
            self.xml.add_references(element, rmap, show_ids=self.show_ids)
            self.xml.gis_encode(resource, record, rmap,
                                download_url=self.download_url,
                                marker=marker)


            # Export components of this record
            r_url = "%s/%s" % (url, record.id)
            for c in resource.components.values():

                component = c.component

                cprefix = component.prefix
                cname = component.name
                if self.model.has_components(cprefix, cname):
                    continue

                ctable = component.table
                cresource = c.resource
                c_url = "%s/%s" % (r_url, cname)

                ctablename = component.tablename
                _rfields = crfields[ctablename]
                _dfields = cdfields[ctablename]

                crecords = resource(record.id, component=cname)
                for crecord in crecords:

                    if msince is not None and self.xml.MTIME in crecord:
                        if crecord[self.xml.MTIME] < msince:
                            continue
                    msince_add = True

                    if audit:
                        audit(self.ACTION["read"], cprefix, cname,
                              record=crecord.id,
                              representation="xml")

                    if show_urls:
                        resource_url = "%s/%s" % (c_url, crecord.id)
                    else:
                        resource_url = None

                    crmap = self.xml.rmap(ctable, crecord, _rfields)
                    celement = self.xml.element(ctable, crecord,
                                                fields=_dfields,
                                                url=resource_url,
                                                download_url=self.download_url,
                                                marker=marker)
                    self.xml.add_references(celement, crmap, show_ids=self.show_ids)
                    self.xml.gis_encode(cresource, crecord, rmap,
                                        download_url=self.download_url,
                                        marker=marker)

                    element.append(celement)
                    reference_map.extend(crmap)

                    if export_map.get(c.tablename, None):
                        export_map[c.tablename].append(crecord.id)
                    else:
                        export_map[c.tablename] = [crecord.id]

            if msince_add:
                reference_map.extend(rmap)
                element_list.append(element)
                if export_map.get(resource.tablename, None):
                    export_map[resource.tablename].append(record.id)
                else:
                    export_map[resource.tablename] = [record.id]
            else:
                results -= 1

        # Add referenced resources to the tree
        depth = dereference and self.MAX_DEPTH or 0
        while reference_map and depth:
            depth -= 1
            load_map = self.__directory(None, reference_map, "table", "id", e=export_map)
            reference_map = []

            for tablename in load_map:

                load_list = load_map[tablename]
                prefix, name = tablename.split("_", 1)
                rresource = self._resource(prefix, name, id=load_list, components=[])
                table = rresource.table
                rresource.load()

                if self.base_url:
                    url = "%s/%s/%s" % (self.base_url, prefix, name)
                else:
                    url = "/%s/%s" % (prefix, name)

                rfields, dfields = self.__fields(table, skip=skip)
                for record in rresource:
                    if audit:
                        audit(self.ACTION["read"], prefix, name,
                              record=record.id,
                              representation="xml")

                    rmap = self.xml.rmap(table, record, rfields)
                    if show_urls:
                        resource_url = "%s/%s" % (url, record.id)
                    else:
                        resource_url = None

                    element = self.xml.element(table, record,
                                               fields=dfields,
                                               url=resource_url,
                                               download_url=self.download_url,
                                               marker=marker)
                    self.xml.add_references(element, rmap, show_ids=self.show_ids)
                    self.xml.gis_encode(rresource, record, rmap,
                                        download_url=self.download_url,
                                        marker=marker)

                    element.set(self.xml.ATTRIBUTE.ref, "True")
                    element_list.append(element)

                    reference_map.extend(rmap)
                    if export_map.get(tablename, None):
                        export_map[tablename].append(record.id)
                    else:
                        export_map[tablename] = [record.id]

        # Complete the tree
        return self.xml.tree(element_list,
                             domain=self.domain,
                             url= show_urls and self.base_url or None,
                             results=results,
                             start=start,
                             limit=limit)


    # -------------------------------------------------------------------------
    def import_tree(self, resource, id, tree,
                    ignore_errors=False):

        """ Imports data from an S3XML element tree into a resource

            @param resource: the resource
            @param id: record ID or list of record IDs to update
            @param tree: the element tree
            @param ignore_errors: continue at errors (=skip invalid elements)

        """

        self.error = None

        if self.tree_resolve:
            if not isinstance(tree, etree._ElementTree):
                tree = etree.ElementTree(tree)
            self.callback(self.tree_resolve, tree)

        permit = self.auth.shn_has_permission
        audit = self.audit

        tablename = resource.tablename
        table = resource.table

        if "id" not in table:
            self.error = self.ERROR.BAD_RESOURCE
            return False

        elements = self.xml.select_resources(tree, tablename)
        if not elements:
            return True

        # if a record ID is given, import only matching elements
        # TODO: match all possible fields (see original())
        if id and self.xml.UID in table:
            if not isinstance(id, (tuple, list)):
                query = (table.id == id)
            else:
                query = (table.id.belongs(id))
            set = self.db(query).select(table[self.xml.UID])
            uids = [row[self.xml.UID] for row in set]
            matches = []
            for element in elements:
                element_uid = element.get(self.xml.UID, None)
                if not element_uid:
                    continue
                if self.xml.domain_mapping:
                    element_uid = self.xml.import_uid(element_uid)
                if element_uid in uids:
                    matches.append(element)
            if not matches:
                self.error = self.ERROR.NO_MATCH
                return False
            else:
                elements = matches

        # Import all matching elements
        error = None
        imports = []
        directory = {}
        vmap = {} # Element<->Vector Map

        for i in xrange(0, len(elements)):
            element = elements[i]
            vectors = self.__vectorize(tablename, element,
                                       id=id,
                                       files = resource.files(),
                                       validate=self.validate,
                                       permit=permit,
                                       audit=audit,
                                       sync=self.sync_resolve,
                                       log=self.sync_log,
                                       tree=tree,
                                       directory=directory,
                                       vmap=vmap,
                                       lookahead=True)

            if vectors:
                vector = vectors[-1]
            else:
                continue

            # Import components
            for item in resource.components.values():

                # Get component details
                c = item.component
                pkey = item.pkey
                fkey = item.fkey
                ctablename = c.tablename
                ctable = c.table

                # Find elements for the component
                celements = self.xml.select_resources(element, ctablename)

                if celements:
                    c_id = c_uid = None

                    # Get the original record ID/UID, if not multiple
                    if not c.attr.multiple:
                        if vector.id:
                            query = (table.id == vector.id) & (table[pkey] == ctable[pkey])
                            if self.xml.UID in ctable:
                                fields = (ctable.id, ctable[self.xml.UID])
                            else:
                                fields = (ctable.id,)
                            orig = self.db(query).select(limitby=(0,1), *fields).first()
                            if orig:
                                c_id = orig.id
                                c_uid = orig.get(self.xml.UID, None)

                        celements = [celements[0]]
                        if c_uid:
                            celements[0].set(self.xml.UID, c_uid)

                    # Generate vectors for the component elements
                    for k in xrange(0, len(celements)):
                        celement = celements[k]
                        cvectors = self.__vectorize(ctablename,
                                                    celement,
                                                    files = resource.files(),
                                                    validate=self.validate,
                                                    permit=permit,
                                                    audit=audit,
                                                    sync=self.sync_resolve,
                                                    log=self.sync_log,
                                                    tree=tree,
                                                    directory=directory,
                                                    vmap=vmap,
                                                    lookahead=True)

                        cvector = None
                        if cvectors:
                            cvector = cvectors.pop()
                        if cvectors:
                            vectors.extend(cvectors)
                        if cvector:
                            cvector.pkey = pkey
                            cvector.fkey = fkey
                            vector.components.append(cvector)

            if self.error is None:
                imports.extend(vectors)
            else:
                error = self.error
                self.error = None

        if error:
            self.error = error

        # Commit all vectors
        if self.error is None or ignore_errors:
            for i in xrange(0, len(imports)):
                vector = imports[i]
                success = vector.commit()
                if not success:
                    if not vector.permitted:
                        self.error = self.ERROR.NOT_PERMITTED
                    else:
                        self.error = self.ERROR.DATA_IMPORT_ERROR
                    if vector.element:
                        vector.element.set(self.xml.ATTRIBUTE.error, self.error)
                    if ignore_errors:
                        continue
                    else:
                        return False

        return ignore_errors or not self.error


    # -------------------------------------------------------------------------
    def search_simple(self, label=None, comment=None, fields=[]):

        """ Generate a search_simple method handler

            @param label: the label for the input field in the search form
            @param comment: help text for the input field in the search form
            @param fields: the fields to search for the string

        """

        if not label:
            label = self.T("Enter search text")

        if not fields:
            fields = ["id"]

        return S3SearchSimple(self,
                              label=label,
                              comment=comment,
                              fields=fields)


    # -------------------------------------------------------------------------
    def _search_simple(self, table, fields=None, label=None, filterby=None):

        """ Simple search function for resources

            @param table: the DB table
            @param fields: list of fields to search for the label
            @param label: label to be found
            @param filterby: filter query for results

        """

        mq = Storage()
        search_fields = Storage()

        prefix, name = table._tablename.split("_", 1)

        if fields and not isinstance(fields, (list, tuple)):
            fields = [fields]
        elif not fields:
            raise SyntaxError("No search fields specified.")

        for f in fields:
            _table = None
            component = None

            if f.find(".") != -1:
                cname, f = f.split(".", 1)
                component, pkey, fkey = self.model.get_component(prefix, name, cname)
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
                query = (self.auth.shn_accessible_query("read", _table))
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
                _l = "%s%s%s" % (wc, l, wc)
                query = None
                for tablename in search_fields:
                    hq = mq[tablename]
                    fq = None
                    fields = search_fields[tablename]
                    for f in fields:
                        if fq:
                            fq = (f.like(_l)) | fq
                        else:
                            fq = (f.like(_l))
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


# *****************************************************************************
class S3Vector(object):

    """ Helper class for data imports """

    METHOD = Storage(
        CREATE="create",
        UPDATE="update"
    )

    RESOLUTION = Storage(
        THIS="THIS",                # keep local instance
        OTHER="OTHER",              # import other instance
        NEWER="NEWER",              # import other if newer
        MASTER="MASTER",            # import other if master
        MASTERCOPY="MASTERCOPY"     # import other if lower master-copy-index
    )

    UID = "uuid"
    MCI = "mci"
    MTIME = "modified_on"


    # -------------------------------------------------------------------------
    def __init__(self, manager, prefix, name, id,
                 record=None,
                 element=None,
                 mtime=None,
                 rmap=None,
                 directory=None,
                 permit=None, # @todo 2.2: read from manager
                 audit=None, # @todo 2.2: read from manager
                 sync=None, # @todo 2.2: read from manager
                 log=None, # @todo 2.2: read from manager
                 onvalidation=None,
                 onaccept=None):

        """ Constructor

            @param manager: the resource controller
            @param prefix: prefix of the resource name (=module name)
            @param name: the resource name (=without prefix)
            @param id: the target record ID
            @param record: the record data to import
            @param element: the corresponding element from the element tree
            @param rmap: map of references for this record
            @param directory: resource directory of the input tree
            @param permit: permit hook (function to check table permissions)
            @param audit: audit hook (function to audit table access)
            @param sync: sync hook (function to resolve sync conflicts)
            @param log: log hook (function to log imports)
            @param onvalidation: extra function to validate records
            @param onaccept: callback function for committed importes

        """

        self.__manager = manager
        self.db = self.__manager.db
        self.prefix = prefix
        self.name = name

        self.tablename = "%s_%s" % (self.prefix, self.name)
        self.table = self.db[self.tablename]

        self.element = element
        self.record = record
        self.id = id

        if mtime:
            self.mtime = mtime
        else:
            self.mtime = datetime.datetime.utcnow()

        self.rmap = rmap

        self.components = []
        self.references = []
        self.update = []

        self.method = None
        self.strategy = [self.METHOD.CREATE, self.METHOD.UPDATE]

        self.resolution = self.RESOLUTION.OTHER
        self.default_resolution = self.RESOLUTION.THIS

        self.onvalidation = onvalidation
        self.onaccept = onaccept
        self.audit = audit
        self.sync = sync
        self.log = log

        self.accepted = True
        self.permitted = True
        self.committed = False

        self.uid = self.record.get(self.UID, None)
        self.mci = self.record.get(self.MCI, 2)

        if not self.id:
            self.id = 0
            self.method = permission = self.METHOD.CREATE
            orig = self.__manager.original(self.table, self.record)
            if orig:
                self.id = orig.id
                self.uid = orig.get(self.UID, None)
                self.method = permission = self.METHOD.UPDATE
        else:
            self.method = permission = self.METHOD.UPDATE
            if not self.db(self.table.id == id).count():
                self.id = 0
                self.method = permission = self.METHOD.CREATE

        # Do allow import to tables with these prefixes:
        if self.prefix in self.__manager.PROTECTED:
            self.permitted = False

        # ...or check permission explicitly:
        elif permit and not \
           permit(permission, self.tablename, record_id=self.id):
            self.permitted = False

        # Once the vector has been created, update the entry in the directory
        if self.uid and \
           directory is not None and self.tablename in directory:
            entry = directory[self.tablename].get(self.uid, None)
            if entry:
                entry.update(vector=self)


    # Data import =============================================================

    def get_resolution(self, field):

        """ Find Sync resolution for a particular field in this record

            @param field: the field name

        """

        if isinstance(self.resolution, dict):
            r = self.resolution.get(field, self.default_resolution)
        else:
            r = self.resolution
        if not r in self.RESOLUTION.values():
            r = self.default_resolution
        return r


    # -------------------------------------------------------------------------
    def commit(self):

        """ Commits the vector to the database

            @todo 2.2: propagate onvalidation errors properly to the element
            @todo 2.2: propagate import errors properly to the importer

        """

        self.resolve() # Resolve references

        model = self.__manager.model

        skip_components = False

        if not self.committed:
            if self.accepted and self.permitted:

                #print >> sys.stderr, "Committing %s id=%s mtime=%s" % (self.tablename, self.id, self.mtime)

                # Create pseudoform for callbacks
                form = Storage()
                form.method = self.method
                form.vars = self.record
                form.vars.id = self.id
                form.errors = Storage()

                # Validate
                if self.onvalidation:
                    self.__manager.callback(self.onvalidation, form, name=self.tablename)
                if form.errors:
                    #print >> sys.stderr, form.errors
                    if self.element:
                        #TODO: propagate errors to element
                        pass
                    return False

                # Call Sync resolver+logger
                if self.sync:
                    self.sync(self)
                if self.log:
                    self.log(self)

                # Check for strategy
                if not isinstance(self.strategy, (list, tuple)):
                    self.strategy = [self.strategy]

                if self.method not in self.strategy:
                    # Skip this record ----------------------------------------

                    # Do not create/update components when skipping primary
                    skip_components = True

                elif self.method == self.METHOD.UPDATE:
                    # Update existing record ----------------------------------

                    # Merge as per Sync resolution:
                    query = (self.table.id == self.id)
                    this = self.db(query).select(self.table.ALL, limitby=(0,1))
                    if this:
                        this = this.first()
                        if self.MTIME in self.table.fields:
                            this_mtime = this[self.MTIME]
                        else:
                            this_mtime = None
                        if self.MCI in self.table.fields:
                            this_mci = this[self.MCI]
                        else:
                            this_mci = 0
                        fields = self.record.keys()
                        for f in fields:
                            r = self.get_resolution(f)
                            if r == self.RESOLUTION.THIS:
                                del self.record[f]
                            elif r == self.RESOLUTION.NEWER:
                                if this_mtime and \
                                   this_mtime > self.mtime:
                                    del self.record[f]
                            elif r == self.RESOLUTION.MASTER:
                                if this_mci == 0 or self.mci != 1:
                                    del self.record[f]
                            elif r == self.RESOLUTION.MASTERCOPY:
                                if this_mci == 0 or \
                                   self.mci == 0 or \
                                   this_mci < self.mci:
                                    del self.record[f]
                                elif this_mci == self.mci and \
                                     this_mtime and this_mtime > self.mtime:
                                        del self.record[f]

                    if len(self.record):
                        self.record.update({self.MCI:self.mci})
                        if "deleted" in self.table.fields:
                            self.record.update(deleted=False) # Undelete re-imported records!
                        try:
                            success = self.db(self.table.id == self.id).update(**dict(self.record))
                        except: # TODO: propagate error to XML importer
                            return False
                        if success:
                            self.committed = True
                    else:
                        self.committed = True

                elif self.method == self.METHOD.CREATE:
                    # Create new record ---------------------------------------

                    if self.UID in self.record:
                        del self.record[self.UID]
                    if self.MCI in self.record:
                        del self.record[self.MCI]
                    for f in self.record:
                        r = self.get_resolution(f)
                        if r == self.RESOLUTION.MASTER and self.mci != 1:
                            del self.record[f]

                    if not len(self.record):
                        skip_components = True
                    else:
                        if self.uid and self.UID in self.table.fields:
                            self.record.update({self.UID:self.uid})
                        if self.MCI in self.table.fields:
                            self.record.update({self.MCI:self.mci})
                        try:
                            success = self.table.insert(**dict(self.record))
                        except: # TODO: propagate error to XML importer
                            return False
                        if success:
                            self.id = success
                            self.committed = True

                # audit + onaccept on successful commits
                if self.committed:
                    form.vars.id = self.id
                    if self.audit:
                        self.audit(self.method, self.prefix, self.name,
                                   form=form, record=self.id, representation="xml")
                    model.update_super(self.table, form.vars)
                    if self.onaccept:
                        self.__manager.callback(self.onaccept, form, name=self.tablename)

        # Load record if components pending
        if self.id and self.components and not skip_components:
            db_record = self.db(self.table.id == self.id).select(self.table.ALL)
            if db_record:
                db_record = db_record.first()

            # Commit components
            for i in xrange(0, len(self.components)):
                component = self.components[i]
                pkey = component.pkey
                fkey = component.fkey
                component.record[fkey] = db_record[pkey]
                component.commit()

        # Update referencing vectors
        if self.update and self.id:
            for u in self.update:
                vector = u.get("vector", None)
                if vector:
                    field = u.get("field", None)
                    vector.writeback(field, self.id)

        # Phew...done!
        return True


    # -------------------------------------------------------------------------
    def resolve(self):

        """ Resolve references of this record """

        if self.rmap:
            for r in self.rmap:
                fieldtype = str(self.table[r.field].type)
                multiple = False
                if fieldtype.startswith("list:reference"):
                    multiple = True
                if r.entry:
                    id = r.entry.get("id", None)
                    if not id:
                        vector = r.entry.get("vector", None)
                        if vector:
                            id = vector.id
                            r.entry.update(id=id)
                        else:
                            continue
                    if id:
                        if multiple:
                            val = self.record.get(r.field, None) or []
                            val.append(id)
                            self.record[r.field] = val
                        else:
                            self.record[r.field] = id
                    else:
                        if r.field in self.record and not multiple:
                            del self.record[r.field]
                        vector.update.append(dict(vector=self, field=r.field))


    # -------------------------------------------------------------------------
    def writeback(self, field, value):

        """ Update a field in the record

            @param field: field name
            @param value: value to write

        """

        if self.id and self.permitted:
            fieldtype = str(self.table[field].type)
            if fieldtype.startswith("list:reference"):
                record = self.db(self.table.id == self.id).select(self.table[field], limitby=(0,1)).first()
                if record:
                    values = record[field]
                    values.append(value)
                self.db(self.table.id == self.id).update(**{field:values})
            else:
                self.db(self.table.id == self.id).update(**{field:value})


# *****************************************************************************
