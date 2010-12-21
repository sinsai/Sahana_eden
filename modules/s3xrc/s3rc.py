# -*- coding: utf-8 -*-

""" S3XRC Resource Framework - Data Store Manager

    @version: 2.2.10

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

__all__ = ["S3DataStore", "S3ImportJob"]

import sys, datetime, time

from gluon.sql import Field
from gluon.storage import Storage
from gluon.html import URL, A
from gluon.http import HTTP, redirect
from gluon.validators import IS_DATE, IS_TIME
from lxml import etree

from s3xml import S3XML
from s3rest import S3Resource, S3Request
from s3model import S3ResourceModel, S3ResourceLinker
from s3crud import S3CRUD
from s3search import S3SearchSimple
from s3export import S3Exporter
from s3import import S3Importer

# *****************************************************************************
class S3DataStore(object):

    """
    Data Store Manager

    """

    UID = "uuid"
    DELETED = "deleted"

    HOOKS = "s3"
    RCVARS = "rcvars"

    ACTION = Storage(
        create="create",
        read="read",
        update="update",
        delete="delete"
    )

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
        NOT_IMPLEMENTED = "Not implemented",
        INTEGRITY_ERROR = "Integrity error" #T("Cannot delete whilst there are linked records. Please delete linked records first.")
    )

    def __init__(self, environment, db):
        """
        Constructor

        @param environment: the environment of this run
        @param db: the database

        """

        self.db = db

        # Environment
        environment = Storage(environment)
        self.T = environment.T
        self.ROWSPERPAGE = environment.ROWSPERPAGE
        self.cache = environment.cache
        self.session = environment.session
        self.request = environment.request
        self.response = environment.response
        self.migrate = environment.migrate

        # Settings
        self.s3 = environment.s3
        self.domain = self.request.env.server_name
        self.rlink_tablename = "s3_rlink"
        self.show_ids = False

        # Errors
        self.error = None

        # Toolkits
        self.audit = environment.s3_audit
        self.auth = environment.auth
        self.gis = environment.gis

        # Helpers
        self.query_builder = S3QueryBuilder(self)
        self.model = S3ResourceModel(self.db)
        self.linker = S3ResourceLinker(self)
        self.crud = S3CRUD()
        self.xml = S3XML(self)
        self.exporter = S3Exporter(self)
        self.importer = S3Importer(self)

        # Hooks
        self.permit = self.auth.shn_has_permission
        self.messages = None
        self.tree_resolve = None
        self.resolve = None
        self.log = None

        # JSON formats and content-type headers
        self.json_formats = []
        self.content_type = Storage()


    # Utilities ===============================================================

    def __fields(self, table, skip=[]):
        """
        Find all readable fields in a table and split them into reference
        and non-reference fields

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
    def __create_job(self, resource, element,
                     id=None,
                     files=[],
                     validate=None,
                     tree=None,
                     directory=None,
                     joblist=None,
                     lookahead=True):
        """
        Builds a list of import jobs from an element

        @param resource: the resource name (=tablename)
        @param element: the element
        @param id: target record ID
        @param validate: validate hook (function to validate record)
        @param tree: the element tree of the source
        @param directory: the resource directory of the tree
        @param joblist: the job list for the import
        @param lookahead: resolve any references

        """

        imports = []

        if joblist is not None and element in joblist:
            return imports

        table = self.db[resource]

        # Get the original record
        original = self.original(table, element)

        # Convert element into a record and validate it
        record = self.xml.record(table, element,
                                 original=original,
                                 files=files,
                                 validate=validate)

        # Get the modification date/time from the element
        # @todo: import this
        mtime = element.get(self.xml.MTIME, None)
        if mtime:
            mtime, error = self.validate(table, None, self.xml.MTIME, mtime)
            if error:
                mtime = None

        if not record:
            self.error = self.ERROR.VALIDATION_ERROR
            return None

        # Look ahead for referenced elements
        if lookahead:
            (rfields, dfields) = self.__fields(table)
            rmap = self.xml.lookahead(table, element, rfields,
                                      directory=directory, tree=tree)
        else:
            rmap = []

        # Create an import job
        (prefix, name) = resource.split("_", 1)
        onvalidation = self.model.get_config(table, "onvalidation")
        onaccept = self.model.get_config(table, "onaccept")
        job = S3ImportJob(self, prefix, name, id,
                          record=record,
                          element=element,
                          mtime=mtime,
                          rmap=rmap,
                          directory=directory,
                          onvalidation=onvalidation,
                          onaccept=onaccept)

        # Create a job list
        if joblist is not None:
            joblist[element] = job

        # Create import jobs for the referenced elements
        for r in rmap:
            entry = r.get("entry")
            relement = entry.get("element")
            if relement is None:
                continue
            jobs = self.__create_job(entry.get("resource"),
                                     relement,
                                     validate=validate,
                                     tree=tree,
                                     directory=directory,
                                     joblist=joblist)
            if jobs:
                if entry["job"] is None:
                    entry["job"] = jobs[-1]
                imports.extend(jobs)

        # Add job to the import list
        imports.append(job)

        return imports


    # -------------------------------------------------------------------------
    def __directory(self, d, l, k, v, e={}):
        """
        Converts a list of dicts into a directory

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
        """
        Invoke a hook or a list of hooks

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
        """
        Reads the last record ID for a resource from a session

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
        """
        Stores a record ID for a resource in a session

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
        """
        Clears one or all record IDs stored in a session

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
    def _resource(self, prefix, name,
                  id=None,
                  uid=None,
                  filter=None,
                  vars=None,
                  parent=None,
                  components=None):
        """
        Wrapper function for S3Resource, creates a resource

        @param prefix: the application prefix of the resource
        @param name: the resource name (without prefix)
        @param id: record ID or list of record IDs
        @param uid: record UID or list of record UIDs
        @param filter: web2py query to filter the resource query
        @param vars: dict of URL query parameters
        @param parent: the parent resource (if this is a component)
        @param components: list of component (names)

        """

        resource = S3Resource(self, prefix, name,
                              id=id,
                              uid=uid,
                              filter=filter,
                              vars=vars,
                              parent=parent,
                              components=components)

        return resource


    # -------------------------------------------------------------------------
    def _request(self, prefix, name):
        """
        Wrapper function for S3Request

        @param prefix: the module prefix of the resource
        @param name: the resource name (without prefix)

        @todo 2.3: deprecate

        """

        return S3Request(self, prefix, name)


    # -------------------------------------------------------------------------
    def parse_request(self, prefix, name):
        """
        Parse an HTTP request and generate the corresponding S3Request and
        S3Resource objects.

        @param prefix: the module prefix of the resource
        @param name: the resource name (without prefix)

        @todo 2.3: move into S3Resource

        """

        self.error = None
        try:
            req = self._request(prefix, name)
        except SyntaxError:
            raise HTTP(400, body=self.xml.json_message(False, 400, message=self.error))
        except KeyError:
            raise HTTP(404, body=self.xml.json_message(False, 404, message=self.error))
        except:
            raise
        res = req.resource
        return (res, req)


    # Resource functions ======================================================

    def validate(self, table, record, fieldname, value):
        """
        Validates a single value

        @param table: the DB table
        @param record: the existing DB record
        @param fieldname: name of the field
        @param value: value to check

        @todo 2.3: make static method
        @todo 2.3: move into model

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
        """
        Represent a field value

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
        """
        Find the original record for a possible duplicate:
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
        UID = self.xml.UID
        if UID in pvalues:
            uid = self.xml.import_uid(pvalues[UID])
            query = (table[UID] == uid)
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
        """
        Find the matching element for a record

        @param tree: the S3XML element tree
        @param table: the table
        @param id: the record ID or a list of record IDs

        @returns: a list of matching elements

        @todo 2.3: implement this and use in import_tree()

        """

        return NotImplementedError


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
        """
        Export a resource as S3XML element tree

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

        @todo 2.3: move into S3Resource

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
            cdfields[ctablename] = self.__fields(cresource.table,
                                                 skip=skip+[c.fkey])

        # Resource base URL
        if self.s3.base_url:
            url = "%s/%s/%s" % (self.s3.base_url, prefix, name)
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
                                       url=resource_url)
            self.xml.add_references(element, rmap, show_ids=self.show_ids)
            self.xml.gis_encode(resource, record, rmap,
                                download_url=self.s3.download_url,
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
                                                url=resource_url)
                    self.xml.add_references(celement, crmap, show_ids=self.show_ids)
                    self.xml.gis_encode(cresource, crecord, rmap,
                                        download_url=self.s3.download_url,
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

                if self.s3.base_url:
                    url = "%s/%s/%s" % (self.s3.base_url, prefix, name)
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
                                               url=resource_url)
                    self.xml.add_references(element, rmap, show_ids=self.show_ids)
                    self.xml.gis_encode(rresource, record, rmap,
                                        download_url=self.s3.download_url,
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
                             url= show_urls and self.s3.base_url or None,
                             results=results,
                             start=start,
                             limit=limit)


    # -------------------------------------------------------------------------
    def import_tree(self, resource, id, tree,
                    ignore_errors=False):
        """
        Imports data from an S3XML element tree into a resource

        @param resource: the resource
        @param id: record ID or list of record IDs to update
        @param tree: the element tree
        @param ignore_errors: continue at errors (=skip invalid elements)

        @todo 2.3: move into S3Resource

        """

        self.error = None

        # Call the tree-resolver to cleanup the tree
        if self.tree_resolve:
            if not isinstance(tree, etree._ElementTree):
                tree = etree.ElementTree(tree)
            self.callback(self.tree_resolve, tree)

        permit = self.auth.shn_has_permission
        audit = self.audit

        tablename = resource.tablename
        table = resource.table

        # Do not import into tables without "id" field
        if "id" not in table.fields:
            self.error = self.ERROR.BAD_RESOURCE
            return False

        # Select the elements for this table
        elements = self.xml.select_resources(tree, tablename)
        if not elements:
            return True # nothing to import => still ok

        # if a record ID is given, import only matching elements
        # @todo: match all possible fields (see original())
        UID = self.xml.UID
        if id and UID in table:
            if not isinstance(id, (tuple, list)):
                query = (table.id == id)
            else:
                query = (table.id.belongs(id))
            set = self.db(query).select(table[UID])
            uids = [row[UID] for row in set]
            matches = []
            for element in elements:
                element_uid = self.xml.import_uid(element.get(UID, None))
                if not element_uid:
                    continue
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
        joblist = {} # Element<->Job Map

        for i in xrange(0, len(elements)):
            element = elements[i]
            jobs = self.__create_job(tablename, element,
                                     id=id,
                                     files = resource.files,
                                     validate=self.validate,
                                     tree=tree,
                                     directory=directory,
                                     joblist=joblist,
                                     lookahead=True)

            if jobs:
                job = jobs[-1]
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
                    if not c.multiple:
                        if job.id:
                            query = (table.id == job.id) & (table[pkey] == ctable[pkey])
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

                    # Generate jobs for the component elements
                    for k in xrange(0, len(celements)):
                        celement = celements[k]
                        cjobs = self.__create_job(ctablename,
                                                  celement,
                                                  files = resource.files,
                                                  validate=self.validate,
                                                  tree=tree,
                                                  directory=directory,
                                                  joblist=joblist,
                                                  lookahead=True)

                        cjob = None
                        if cjobs:
                            cjob = cjobs.pop()
                        if cjobs:
                            jobs.extend(cjobs)
                        if cjob:
                            cjob.pkey = pkey
                            cjob.fkey = fkey
                            job.components.append(cjob)

            if self.error is None:
                imports.extend(jobs)
            else:
                error = self.error
                self.error = None

        if error:
            self.error = error

        # Commit all jobs
        if self.error is None or ignore_errors:
            for i in xrange(0, len(imports)):
                job = imports[i]
                success = job.commit()
                if not success:
                    if not job.permitted:
                        self.error = self.ERROR.NOT_PERMITTED
                    elif not self.error:
                        self.error = self.ERROR.DATA_IMPORT_ERROR
                    if job.element:
                        if not job.element.get(self.xml.ATTRIBUTE.error):
                            job.element.set(self.xml.ATTRIBUTE.error,
                                            self.xml.xml_encode(str(self.error).decode("utf-8")))
                    if ignore_errors:
                        continue
                    else:
                        return False

        return ignore_errors or not self.error


    # -------------------------------------------------------------------------
    def search_simple(self, label=None, comment=None, fields=[]):
        """
        Generate a search_simple method handler

        @param label: the label for the input field in the search form
        @param comment: help text for the input field in the search form
        @param fields: the fields to search for the string

        """

        if not label:
            label = self.T("Enter search text")

        if not fields:
            fields = ["id"]

        return S3SearchSimple(label=label,
                              comment=comment,
                              fields=fields)


# *****************************************************************************
class S3ImportJob(object):

    """ Helper class for data imports

        @param datastore: the resource controller
        @param prefix: prefix of the resource name (=module name)
        @param name: the resource name (=without prefix)
        @param id: the target record ID
        @param record: the record data to import
        @param element: the corresponding element from the element tree
        @param rmap: map of references for this record
        @param directory: resource directory of the input tree
        @param onvalidation: extra function to validate records
        @param onaccept: callback function for committed importes

    """

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
    def __init__(self, datastore, prefix, name, id,
                 record=None,
                 element=None,
                 mtime=None,
                 rmap=None,
                 directory=None,
                 onvalidation=None,
                 onaccept=None):

        self.datastore = datastore
        self.db = datastore.db

        self.permit = datastore.permit
        self.audit = datastore.audit
        self.resolve = datastore.resolve
        self.log = datastore.log

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

        self.accepted = True
        self.permitted = True
        self.committed = False

        self.uid = self.record.get(self.UID, None)
        self.mci = self.record.get(self.MCI, 2)

        if not self.id:
            self.id = 0
            self.method = permission = self.METHOD.CREATE
            orig = self.datastore.original(self.table, self.record)
            if orig:
                self.id = orig.id
                self.uid = orig.get(self.UID, None)
                self.method = permission = self.METHOD.UPDATE
        else:
            self.method = permission = self.METHOD.UPDATE
            if not self.db(self.table.id == id).count():
                self.id = 0
                self.method = permission = self.METHOD.CREATE

        if self.prefix in self.datastore.PROTECTED:
            self.permitted = False
        elif self.permit and not \
           self.permit(permission, self.tablename, record_id=self.id):
            self.permitted = False

        if self.uid and \
           directory is not None and self.tablename in directory:
            entry = directory[self.tablename].get(self.uid, None)
            if entry:
                entry.update(job=self)


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

        """ Commits the record to the database """

        self.resolve_references()

        xml = self.datastore.xml
        model = self.datastore.model

        skip_components = False

        if not self.committed:
            if self.accepted and self.permitted:
                #print >> sys.stderr, "Committing %s id=%s mtime=%s" % (self.tablename, self.id, self.mtime)

                # Validate
                form = Storage()
                form.method = self.method
                form.vars = self.record
                if self.id:
                    form.vars.id = self.id
                form.errors = Storage()
                if self.onvalidation:
                    self.datastore.callback(self.onvalidation, form, name=self.tablename)
                if form.errors:
                    for k in form.errors:
                        e = self.element.findall("data[@field='%s']" % k)
                        if not e:
                            e = self.element
                            form.errors[k] = "[%s] %s" % (k, form.errors[k])
                        else:
                            e = e[0]
                        e.set(xml.ATTRIBUTE.error,
                              xml.xml_encode(str(form.errors[k])))
                    self.datastore.error = self.datastore.ERROR.VALIDATION_ERROR
                    return False

                # Resolve+Log
                if self.resolve:
                    self.resolve(self)
                if self.log:
                    self.log(self)

                if not isinstance(self.strategy, (list, tuple)):
                    self.strategy = [self.strategy]

                # Skip
                if self.method not in self.strategy:
                    skip_components = True # Skip all components as well

                # Update
                elif self.method == self.METHOD.UPDATE:
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
                        except:
                            self.datastore.error = sys.exc_info()[1]
                            return False
                        if success:
                            self.committed = True
                    else:
                        self.committed = True

                # Create new
                elif self.method == self.METHOD.CREATE:
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
                        except:
                            self.datastore.error = sys.exc_info()[1]
                            return False
                        if success:
                            self.id = success
                            self.committed = True

                # Audit + onaccept on successful commits
                if self.committed:
                    form.vars.id = self.id
                    if self.audit:
                        self.audit(self.method, self.prefix, self.name,
                                   form=form, record=self.id, representation="xml")
                    model.update_super(self.table, form.vars)
                    if self.onaccept:
                        self.datastore.callback(self.onaccept, form, name=self.tablename)

        # Commit components
        if self.id and self.components and not skip_components:
            db_record = self.db(self.table.id == self.id).select(self.table.ALL)
            if db_record:
                db_record = db_record.first()
            for i in xrange(0, len(self.components)):
                component = self.components[i]
                pkey = component.pkey
                fkey = component.fkey
                component.record[fkey] = db_record[pkey]
                component.commit()

        # Update referencing jobs
        if self.update and self.id:
            for u in self.update:
                job = u.get("job", None)
                if job:
                    field = u.get("field", None)
                    job.writeback(field, self.id)

        return True


    # -------------------------------------------------------------------------
    def resolve_references(self):

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
                        job = r.entry.get("job", None)
                        if job:
                            id = job.id
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
                        job.update.append(dict(job=self, field=r.field))


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
class S3QueryBuilder(object):

    """ Query Builder

        @param datastore: the resource controller

    """

    def __init__(self, datastore):

        self.datastore = datastore


    # -------------------------------------------------------------------------
    def parse_url_rlinks(self, resource, vars):

        """ Parse URL resource link queries. Syntax:
            ?linked{.<component>}.<from|to>.<table>={link_class},<ANY|ALL|list_of_ids>

            @param resource: the resource
            @param vars: dict of URL vars

        """

        linker = self.datastore.linker
        q = None

        for k in vars:
            if k[:7] == "linked.":
                link = k.split(".")
                if len(link) < 3:
                    continue
                else:
                    link = link[1:]
                o_tn = link.pop()
                if o_tn in self.datastore.db:
                    link_table = self.datastore.db[o_tn]
                else:
                    continue
                operator = link.pop()
                if not operator in ("from", "to"):
                    continue
                table = resource.table
                join = None
                if link and link[0] in resource.components:
                    component = components[link[0]].component
                    table = component.table
                    pkey, fkey = component.pkey, component.fkey
                    join = (resource.table[pkey] == table[fkey])
                link_class = None
                union = False
                val = vars[k]
                if isinstance(val, (list, tuple)):
                    val = ",".join(val)
                ids = val.split(",")
                if ids:
                    if not ids[0].isdigit() and ids[0] not in ("ANY", "ALL"):
                        link_class = ids.pop(0)
                if ids:
                    if ids.count("ANY"):
                        link_id = None
                        union = True
                    elif ids.count("ALL"):
                        link_id = None
                    else:
                        link_id = filter(str.isdigit, ids)
                if operator == "from":
                    query = linker.get_target_query(link_table, link_id, table,
                                                    link_class=link_class,
                                                    union=union)
                else:
                    query = linker.get_origin_query(table, link_table, link_id,
                                                    link_class=link_class,
                                                    union=union)
                if query is not None:
                    if join is not None:
                        query = (join & query)
                    q = q and (q & query) or query
        return q


    # -------------------------------------------------------------------------
    @staticmethod
    def parse_url_context(resource, vars):

        """ Parse URL context queries

            @param resource: the resource
            @param vars: dict of URL vars

        """

        table = resource.table
        components = resource.components

        c = Storage()
        for k in vars:
            if k[:8] == "context.":
                context_name = k[8:]
                context = vars[k]
                if not isinstance(context, str):
                    continue
                if context.find(".") > 0:
                    rname, field = context.split(".", 1)
                    if rname in components:
                        table = components[rname].component.table
                    else:
                        continue
                else:
                    rname = resource.name
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
                c[context_name] = Storage(rname = rname,
                                          field = field,
                                          table = ktablename,
                                          multiple = multiple)
            else:
                continue
        return c


    # -------------------------------------------------------------------------
    def parse_url_query(self, resource, vars):

        """ Parse URL query

            @param resource: the resource
            @param vars: dict of URL vars

        """

        c = self.parse_url_context(resource, vars)
        q = Storage(context=c)

        for k in vars:
            if k.find(".") > 0:
                rname, field = k.split(".", 1)
                if rname in ("context", "linked"):
                    continue
                elif rname == resource.name:
                    table = resource.table
                elif rname in resource.components:
                    table = resource.components[rname].component.table
                elif rname in c.keys():
                    table = self.db.get(c[rname].table, None)
                    if not table:
                        continue
                else:
                    continue
                if field.find("__") > 0:
                    field, op = field.split("__", 1)
                else:
                    op = "eq"
                if field == "uid":
                    field = self.datastore.UID
                if field not in table.fields:
                    continue
                else:
                    ftype = str(table[field].type)
                    values = vars[k]
                    if op in ("lt", "le", "gt", "ge"):
                        if ftype not in ("integer",
                                         "double",
                                         "date",
                                         "time",
                                         "datetime"):
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
                            tfmt = "%Y-%m-%dT%H:%M:%SZ" # ISO Format
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
    def query(self, resource, id=None, uid=None, filter=None, vars=None):

        """ Query builder

            @param resource: the resource
            @param id: record ID or list of record IDs to include
            @param uid: record UID or list of record UIDs to include
            @param filter: filtering query (DAL only)
            @param vars: dict of URL query variables

        """

        # Initialize
        resource.clear()
        resource.clear_query()

        xml = self.datastore.xml
        deletion_status = self.datastore.DELETED

        if vars:
            url_query = self.parse_url_query(resource, vars)
            url_rlinks = self.parse_url_rlinks(resource, vars)
            if url_query or url_rlinks:
                resource.vars = vars
        else:
            url_query = Storage()
            url_rlinks = None

        resource._multiple = True # multiple results expected by default

        table = resource.table
        name = resource.name

        # Master Query
        if resource.accessible_query is not None:
            mquery = resource.accessible_query("read", table)
        else:
            mquery = (table.id > 0)

        # Deletion status
        if deletion_status in table.fields:
            remaining = (table[deletion_status] == False)
            mquery = remaining & mquery

        # Component Query
        parent = resource.parent
        if parent:

            parent_query = parent.get_query()
            if parent_query:
                mquery = mquery & parent_query

            component = parent.components.get(name, None)
            if component:
                pkey = component.pkey
                fkey = component.fkey
                resource._multiple = component.get("multiple", True)
                join = parent.table[pkey] == table[fkey]
                if str(mquery).find(str(join)) == -1:
                    mquery = mquery & (join)

        # Primary Resource Query
        else:

            if id or uid:
                if name not in url_query:
                    url_query[name] = Storage()

            # Collect IDs
            if id:
                if not isinstance(id, (list, tuple)):
                    resource._multiple = False # single result expected
                    id = [id]
                id_queries = url_query[name].get("id", Storage())

                ne = id_queries.get("ne", [])
                eq = id_queries.get("eq", [])
                eq = eq + [v for v in id if v not in eq]

                if ne and "ne" not in id_queries:
                    id_queries.ne = ne
                if eq and "eq" not in id_queries:
                    id_queries.eq = eq

                if "id" not in url_query[name]:
                    url_query[name]["id"] = id_queries

            # Collect UIDs
            if uid:
                if not isinstance(uid, (list, tuple)):
                    resource._multiple = False # single result expected
                    uid = [uid]
                uid_queries = url_query[name].get(self.datastore.UID, Storage())

                ne = uid_queries.get("ne", [])
                eq = uid_queries.get("eq", [])
                eq = eq + [v for v in uid if v not in eq]

                if ne and "ne" not in uid_queries:
                    uid_queries.ne = ne
                if eq and "eq" not in uid_queries:
                    uid_queries.eq = eq

                if self.datastore.UID not in url_query[name]:
                    url_query[name][self.datastore.__UID] = uid_queries

            # URL Queries
            contexts = url_query.context
            for rname in url_query:

                if rname == "context":
                    continue

                elif contexts and rname in contexts:
                    context = contexts[rname]

                    cname = context.rname
                    if cname != name and \
                        cname in resource.components:
                        component = resource.components[cname]
                        rtable = component.resource.table
                        pkey = component.pkey
                        fkey = component.fkey
                        cjoin = (table[pkey]==rtable[fkey])
                    else:
                        rtable = table
                        cjoin = None

                    _table = resource.db[context.table]
                    if context.multiple:
                        join = (rtable[context.field].contains(table.id))
                    else:
                        join = (rtable[context.field] == table.id)
                    if cjoin:
                        join = (cjoin & join)

                    mquery = mquery & join

                    if deletion_status in table.fields:
                        remaining = (table[deletion_status] == False)
                        mquery = mquery & remaining

                elif rname == name:
                    _table = table

                elif rname in resource.components:
                    component = resource.components[rname]
                    _table = component.resource.table
                    pkey = component.pkey
                    fkey = component.fkey

                    join = (resource.table[pkey]==_table[fkey])
                    mquery = mquery & join

                    if deletion_status in _table.fields:
                        remaining = (_table[deletion_status] == False)
                        mquery = mquery & remaining

                for field in url_query[rname]:
                    if field in _table.fields:
                        for op in url_query[rname][field]:
                            values = url_query[rname][field][op]
                            if field == xml.UID:
                                uids = map(xml.import_uid, values)
                                values = uids
                            f = _table[field]
                            query = None
                            if op == "eq":
                                if len(values) == 1:
                                    if values[0] == "NONE":
                                        query = (f == None)
                                    elif values[0] == "EMPTY":
                                        query = ((f == None) | (f == ""))
                                    else:
                                        query = (f == values[0])
                                elif len(values):
                                    query = (f.belongs(values))
                            elif op == "ne":
                                if len(values) == 1:
                                    if values[0] == "NONE":
                                        query = (f != None)
                                    elif values[0] == "EMPTY":
                                        query = ((f != None) & (f != ""))
                                    else:
                                        query = (f != values[0])
                                elif len(values):
                                    query = (~(f.belongs(values)))
                            elif op == "lt":
                                v = values[-1]
                                query = (f < v)
                            elif op == "le":
                                v = values[-1]
                                query = (f <= v)
                            elif op == "gt":
                                v = values[-1]
                                query = (f > v)
                            elif op == "ge":
                                v = values[-1]
                                query = (f >= v)
                            elif op == "in":
                                for v in values:
                                    if v.find(",") != -1:
                                        q = None
                                        sv = v.split(",")
                                        for s in sv:
                                            sq = (f.contains(s))
                                            q = q is not None and q | sq or sq
                                    else:
                                        q = (f.contains(v))
                                    if query:
                                        query = query & q
                                    else:
                                        query = q
                                query = (query)
                            elif op == "ex":
                                for v in values:
                                    q = (~(f.contains(v)))
                                    if query:
                                        query = query & q
                                    else:
                                        query = q
                                query = (query)
                            elif op == "like":
                                for v in values:
                                    if v.find(",") != -1:
                                        q = None
                                        sv = v.split(",")
                                        for s in sv:
                                            sq = (f.lower().contains(s.lower()))
                                            q = q is not None and q | sq or sq
                                    else:
                                        q = (f.lower().contains(v.lower()))
                                    if query:
                                        query = query & q
                                    else:
                                        query = q
                                query = (query)
                            elif op == "unlike":
                                for v in values:
                                    q = (~(f.lower().contains(v.lower())))
                                    if query:
                                        query = query & q
                                    else:
                                        query = q
                                query = (query)
                            else:
                                continue
                            mquery = mquery & query

            # Filter
            if filter:
                mquery = mquery & filter
            if url_rlinks:
                mquery = mquery & url_rlinks

        resource._query = mquery
        return mquery


# *****************************************************************************
