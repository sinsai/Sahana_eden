# -*- coding: utf-8 -*-

"""
    S3XCR SahanaPy XML+JSON Resource Controller

    @version: 1.5.0
    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

    @author: nursix
    @copyright: 2010 (c) Sahana Software Foundation
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

__name__ = "S3XRC"

__all__ = ['ResourceController', 'json_message']


# *****************************************************************************
import sys, uuid
import gluon.contrib.simplejson as json

from gluon.storage import Storage
from gluon.html import URL
from gluon.http import HTTP
from gluon.validators import IS_NULL_OR

from xml.etree.cElementTree import ElementTree
from lxml import etree

# *****************************************************************************
# Error messages
S3XRC_BAD_RESOURCE = "Invalid Resource"
S3XRC_PARSE_ERROR = "XML Parse Error"
S3XRC_TRANSFORMATION_ERROR = "XSLT Transformation Error"
S3XRC_BAD_SOURCE = "Invalid XML Source"
S3XRC_BAD_RECORD = "Invalid Record ID"
S3XRC_NO_MATCH = "No Matching Element"
S3XRC_VALIDATION_ERROR = "Validation Error"
S3XRC_DATA_IMPORT_ERROR = "Data Import Error"
S3XRC_NOT_PERMITTED = "Operation Not Permitted"
S3XRC_NOT_IMPLEMENTED = "Not Implemented"

# *****************************************************************************
#exec('from applications.%s.modules.s3xrc import json_message' % request.application)
#from applications.sahana.modules.s3xrc import json_message
#
def json_message(success=True, status_code="200", message=None, tree=None):

    """
        Provide a nicely-formatted JSON Message.

        @param success: whether the request was successful
        @type success: boolean
        @param status_code: the HTTP status code
        @type status_code: string
        @param message: the message to send
        @type message: string
        @param tree: the element tree of the request in JSON containing error annotations
        @type tree: string

    """

    if success:
        status="success"
    else:
        status="failed"

    if not success:
        if message:
            return '{"status": "%s", "statuscode": "%s", "message": "%s", "tree": %s }' % \
                   (status, status_code, message, tree)
        else:
            return '{"status": "%s", "statuscode": "%s", "tree": %s }' % \
                   (status, status_code, tree)
    else:
        if message:
            return '{"status": "%s", "statuscode": "%s", "message": "%s"}' % \
                   (status, status_code, message)
        else:
            return '{"status": "%s", "statuscode": "%s"}' % \
                   (status, status_code)

# *****************************************************************************
class ObjectComponent(object):

    """
        Class to represent component relations between resources.

        @param db: the database abstraction layer
        @type db: DAL
        @param prefix: the module prefix of the component resource
        @type prefix: string
        @param name: the name of the component resource (without prefix)
        @type name: string
        @param attr: dictionary of attributes of the component relation
        @type attr: **dict

    """

    #--------------------------------------------------------------------------
    def __init__(self, db, prefix, name, **attr):

        self.db = db

        self.prefix = prefix
        self.name = name
        self.tablename = "%s_%s" % (prefix, name)

        assert self.tablename in self.db, "Table must exist in the database."
        self.table = self.db[self.tablename]

        self.attr = Storage(attr)

        if not 'multiple' in self.attr:
            self.attr.multiple = True

        if not 'deletable' in self.attr:
            self.attr.deletable = True

        if not 'editable' in self.attr:
            self.attr.editable = True


    #--------------------------------------------------------------------------
    def get_join_keys(self, prefix, name):

        if "joinby" in self.attr:

            joinby = self.attr.joinby

            tablename = "%s_%s" % (prefix, name)
            if tablename in self.db:

                table = self.db[tablename]

                if isinstance(joinby, str):
                    if joinby in table and joinby in self.table:
                        return (joinby, joinby)

                elif isinstance(joinby, dict):
                    if tablename in joinby and joinby[tablename] in self.table:
                        return ('id', joinby[tablename])

        return (None, None)


    #--------------------------------------------------------------------------
    def set_attr(self, name, value):

        self.attr[name] = value


    #--------------------------------------------------------------------------
    def get_attr(self, name):

        if name in self.attr:
            return self.attr[name]
        else:
            return None


# *****************************************************************************
class ObjectModel(object):


    """
        Class to handle the joined resources model

        @param db: the database abstraction layer
        @type db: DAL

    """

    #--------------------------------------------------------------------------
    def __init__(self, db):

        self.db = db

        self.components = {}

        self.methods = {}
        self.cmethods = {}


    #--------------------------------------------------------------------------
    def add_component(self, prefix, name, **attr):

        """ Adds a component to the model """

        assert "joinby" in attr, "Join key(s) must be defined."

        component = ObjectComponent(self.db, prefix, name, **attr)
        self.components[name] = component
        return component


    #--------------------------------------------------------------------------
    def get_component(self, prefix, name, component_name):

        """ Retrieves a component of a resource """

        if component_name in self.components:

            component = self.components[component_name]

            pkey, fkey = component.get_join_keys(prefix, name)
            if pkey is not None:
                return (component, pkey, fkey)

        return (None, None, None)


    #--------------------------------------------------------------------------
    def get_components(self, prefix, name):

        """ Retrieves all components related to a resource """

        component_list = []

        for component_name in self.components:

            component, pkey, fkey = self.get_component(prefix, name, component_name)
            if component is not None:
                component_list.append((component, pkey, fkey))

        return component_list


    #--------------------------------------------------------------------------
    def set_method(self, prefix, name, component_name=None, method=None, action=None):

        """ Adds a custom method for a resource or component """

        assert method is not None, "Method must be specified."

        tablename = "%s_%s" % (prefix, name)

        if component_name is None:

            if method not in self.methods:
                self.methods[method] = {}
            self.methods[method][tablename] = action

        else:

            component = self.get_component(prefix, name, component_name)[0]
            if component is not None:

                if method not in self.cmethods:
                    self.cmethods[method] = {}

                if component.tablename not in self.cmethods[method]:
                    self.cmethods[method][component.tablename] = {}

                self.cmethods[method][component.tablename][tablename] = action

        return True


    #--------------------------------------------------------------------------
    def get_method(self, prefix, name, component_name=None, method=None):

        """ Retrieves a custom method for a resource or component """

        if not method:
            return None

        tablename = "%s_%s" % (prefix, name)

        if component_name is None:

            if method in self.methods and tablename in self.methods[method]:
                return self.methods[method][tablename]
            else:
                return None

        else:

            component = self.get_component(prefix, name, component_name)[0]
            if component is not None and \
               method in self.cmethods and \
               component.tablename in self.cmethods[method] and \
               tablename in self.cmethods[method][component.tablename]:
                return self.cmethods[method][component.tablename][tablename]
            else:
                return None


    #--------------------------------------------------------------------------
    def set_attr(self, component_name, name, value):

        """ Sets an attribute for a component """

        return self.components[component_name].set_attr(name, value)


    #--------------------------------------------------------------------------
    def get_attr(self, component_name, name):

        """ Retrieves an attribute value of a component """

        return self.components[component_name].get_attr(name)


    #--------------------------------------------------------------------------
    def uuid2id(table, uuid):

        """ Maps UUID's to record ID's for a table """

        if uuid in table:
            if not isinstance(uuid, (list, tuple)):
                uuid = [uuid]

            rs = self.db(table.uuid.belongs(uuid)).select(table.id, table.uuid)

            result = [(r.id, r.uuid) for r in rs]
            return result
        else:
            return []


    #--------------------------------------------------------------------------
    def id2uuid(table, id):

        """ Maps record ID's to UUID's for a table """

        if uuid in table:
            if not isinstance(id, (list, tuple)):
                id = [id]

            rs = self.db(table.id.belongs(id)).select(table.id, table.uuid)

            result = [(r.id, r.uuid) for r in rs]
            return result
        else:
            return []


# *****************************************************************************
class ResourceController(object):

    """
        Controller class for joined resources

        @param db: the database abstraction layer
        @param domain:
            the domain name of the instance, used to identify the origin of data
        @param base_url: the base URL of the instance
        @param rpp: default number of rows per page in server-side pagination
        @param gis: the geospatial information handler

        @type db: DAL
        @type domain: string
        @type base_url: string
        @type rpp: int
        @type gis: GIS

    """

    RCVARS = "rcvars"

    ACTION = dict(
        create="create",
        read="read",
        update="update",
        delete="delete"
    )

    ROWSPERPAGE = 10

    #--------------------------------------------------------------------------
    def __init__(self, db, domain=None, base_url=None, rpp=None, gis=None):

        assert db is not None, "Database must not be None."
        self.db = db

        self.error = None

        self.domain = domain
        self.base_url = base_url

        self.download_url = "%s/default/download" % base_url

        if rpp:
            self.ROWSPERPAGE = rpp

        self.model = ObjectModel(self.db)
        self.xml = S3XML(self.db, domain=domain, base_url=base_url, gis=gis)


    #--------------------------------------------------------------------------
    def get_session(self, session, prefix, name):

        """
            Reads the last record ID for a resource from a session

            @param session: the session
            @param prefix: module prefix of the resource name
            @param name: the resource name

            @type session: Storage
            @type prefix: string
            @type name: string

        """

        tablename = "%s_%s" % (prefix, name)

        if self.RCVARS in session and tablename in session[self.RCVARS]:
            return session[self.RCVARS][tablename]


    #--------------------------------------------------------------------------
    def store_session(self, session, prefix, name, id):

        """
            Stores a record ID for a resource in a session

            @param session: the session
            @param prefix: module prefix of the resource name
            @param name: the resource name
            @param id: the record ID to store

            @type session: Storage
            @type prefix: string
            @type name: string

        """

        if self.RCVARS not in session:
            session[self.RCVARS] = Storage()

        if self.RCVARS in session:
            tablename = "%s_%s" % (prefix, name)
            session[self.RCVARS][tablename] = id

        return True # always return True to make this chainable


    #--------------------------------------------------------------------------
    def clear_session(self, session, prefix=None, name=None):

        """ Clears record ID's stored in a session """

        if prefix and name:
            tablename = "%s_%s" % (prefix, name)
            if self.RCVARS in session and tablename in session[self.RCVARS]:
                del session[self.RCVARS][tablename]
        else:
            if self.RCVARS in session:
                del session[self.RCVARS]

        return True # always return True to make this chainable


    #--------------------------------------------------------------------------
    def request(self, prefix, name, request, session=None):

        """
            Wrapper function to generate an XRequest

            @param prefix: the module prefix of the requested resource
            @param name: the name of the requested resource
            @param request: the original request
            @param session: the session storage

            @type prefix: string
            @type name: string
            @type request: Storage
            @type session: Storage

        """

        self.error = None
        return XRequest(self, prefix, name, request, session=session)


    #--------------------------------------------------------------------------
    def search_simple(self, table, fields=None, label=None, filterby=None):

        search_fields = []
        if fields and isinstance(fields, (list,tuple)):
            for f in fields:
                if table.has_key(f):
                    search_fields.append(f)

        if not len(search_fields):
            return None

        if label is not None and isinstance(label,str):
            labels = label.split()
            results = []
            query = None
            for l in labels:

                # add wildcards
                wc = "%"
                _l = "%s%s%s" % (wc, l, wc)
                for f in search_fields:
                    if query:
                        query = (table[f].like(_l)) | query
                    else:
                        query = (table[f].like(_l))

                # undeleted records only
                query = (table.deleted==False) & (query)

                # restrict to prior results (AND)
                if len(results):
                    query = (table.id.belongs(results)) & query
                if filterby:
                    query = (filterby) & (query)
                records = self.db(query).select(table.id)
                # rebuild result list
                results = [r.id for r in records]
                # any results left?
                if not len(results):
                    return None
            return results
        else:
            # no label given or wrong parameter type
            return None


    #--------------------------------------------------------------------------
    def export_xml(self, prefix, name, id,
                   joins=[],
                   filterby=None,
                   skip=[],
                   permit=None,
                   audit=None,
                   start=None,  # starting record
                   limit=None,  # pagesize
                   show_urls=True):

        """ Exports data as XML tree """

        self.error = None
        resources = []

        _table = "%s_%s" % (prefix, name)

        if show_urls:
            burl = self.base_url
        else:
            burl = None

        if _table not in self.db or (permit and not permit(self.ACTION["read"], _table)):
            return self.xml.root(resources, domain=self.domain, url=burl)

        table = self.db[_table]

        if id and isinstance(id, (list, tuple)):
            query = (table.id.belongs(id))
        elif id:
            query = (table.id == id)
        else:
            query = (table.id > 0)

        # Filter out deleted records
        if "deleted" in table:
            query = (table.deleted == False) & query

        # Optional Filter
        if filterby is not None:
            query = query & (filterby)

        if self.base_url:
            url = "%s/%s/%s" % (self.base_url, prefix, name)
        else:
            url = "/%s/%s" % (prefix, name)

        # Not GAE-compatible: .count()
        results = self.db(query).count()

        # Server-side pagination
        if start != None:   # Can't just use 'if start' as 0 is a valid value for start
            if not limit:
                limit = self.ROWSPERPAGE
            if limit <= 0:
                limit = 1
            if start < 0:
                start = 0
            limitby = (start, start + limit)
        else:
            limitby = None

        try:
            records = self.db(query).select(table.ALL, limitby=limitby) or []
        except:
            return None

        if records and permit is not None:
            records = filter(lambda r: permit(self.ACTION["read"], _table, record_id=r.id), records)

        if joins and permit is not None:
            joins = filter(lambda j: permit(self.ACTION["read"], j[0].tablename), joins)

        cdata = {}
        if records:
            for i in xrange(0, len(joins)):
                (c, pkey, fkey) = joins[i]
                pkeys = map(lambda r: r[pkey], records)

                # Not GAE-compatible: .belongs()
                cquery = (c.table[fkey].belongs(pkeys))
                if "deleted" in c.table:
                    cquery = (c.table.deleted==False) & cquery
                cdata[c.tablename] = self.db(cquery).select(c.table.ALL) or []

        for i in xrange(0, len(records)):
            record = records[i]

            if audit is not None:
                audit(self.ACTION["read"], prefix, name, record=record.id, representation="xml")

            if show_urls:
                resource_url = "%s/%s" % (url, record.id)
            else:
                resource_url = None
            resource = self.xml.element(table, record, skip=skip, url=resource_url, download_url=self.download_url)

            for j in xrange(0, len(joins)):
                (c, pkey, fkey) = joins[j]
                pkey = record[pkey]
                crecords = cdata[c.tablename]
                crecords = filter(lambda r: r[fkey]==pkey, crecords)

                _skip = [fkey,]
                if skip:
                    _skip.extend(skip)

                for k in xrange(0, len(crecords)):
                    crecord = crecords[k]

                    if permit and not permit(self.ACTION["read"],
                                             c.tablename, crecord.id):
                        continue
                    if audit is not None:
                        audit(self.ACTION["read"], c.prefix, c.name,
                              record=crecord.id, representation="xml")

                    if show_urls:
                        resource_url = "%s/%s/%s/%s" % \
                                    (url, record.id, c.name, crecord.id)
                    else:
                        resource_url = None

                    cresource = self.xml.element(c.table, crecord,
                                                 skip=_skip, url=resource_url, download_url=self.download_url)
                    resource.append(cresource)

            resources.append(resource)

        return self.xml.tree(resources,
                             domain=self.domain,
                             url=burl,
                             results=results,
                             start=start,
                             limit=limit)


    #--------------------------------------------------------------------------
    def import_xml(self, prefix, name, id, tree,
                   joins=[],
                   skip_resource=False,
                   permit=None,
                   audit=None,
                   onvalidation=None,
                   onaccept=None,
                   ignore_errors=False):

        """ Imports data from an XML tree """

        self.error = None

        tablename = "%s_%s" % (prefix, name)
        if tablename in self.db:
            table = self.db[tablename]
        else:
            self.error = S3XRC_BAD_RESOURCE
            return False

        elements = self.xml.select_resources(tree, tablename)
        if not elements: # nothing to import
            return True

        if id:
            try:
                db_record = self.db(table.id==id).select(table.ALL)[0]
            except:
                self.error = S3XRC_BAD_RECORD
                return False
        else:
            db_record = None

        if id and len(elements)>1:
            # ID given, but multiple elements of that type
            # => try to find UUID match
            if self.xml.UUID in table:
                uuid = db_record[self.xml.UUID]
                for element in elements:
                    if element.get(self.xml.UUID)==uuid:
                        elements = [element]
                        break

            if len(elements)>1:
                # Error: multiple input elements, but only one target record
                self.error = S3XRC_NO_MATCH
                return False

        if joins is None:
            joins = []

        imports = []

        for i in xrange(0, len(elements)):
            element = elements[i]

            record = self.xml.record(table, element)
            if not record:
                self.error = S3XRC_VALIDATION_ERROR
                continue

            vector = XVector(self.db, prefix, name, id,
                             record=record,
                             permit=permit,
                             audit=audit,
                             onvalidation=onvalidation,
                             onaccept=onaccept)

            if skip_resource:
                vector.committed = True

            for j in xrange(0, len(joins)):
                component, pkey, fkey = joins[j]

                celements = self.xml.select_resources(element, component.tablename)

                if celements:
                    if component.attr.multiple:

                        for k in xrange(0, len(celements)):
                            celement = celements[k]

                            crecord = self.xml.record(component.table, celement)
                            if not crecord:
                                self.error = S3XRC_VALIDATION_ERROR
                                continue

                            cvector = XVector(self.db, component.prefix, component.name, None,
                                              record=crecord,
                                              permit=permit,
                                              audit=audit,
                                              onvalidation=component.get_attr("onvalidation"),
                                              onaccept=component.get_attr("onaccept"))

                            cvector.pkey = pkey
                            cvector.fkey = fkey

                            vector.components.append(cvector)
                    else:
                        c_id = c_uuid = None
                        if vector.id:
                            p = self.db(table.id==vector.id).select(table[pkey], limitby=(0,1))
                            if p:
                                p = p[0][pkey]
                                fields = [component.table.id]
                                if self.xml.UUID in component.table:
                                    fields.append(component.table[self.xml.UUID])
                                orig = self.db(component.table[fkey]==p).select(limitby=(0,1), *fields)
                                if orig:
                                    c_id = orig[0].id
                                    if self.xml.UUID in component.table:
                                        c_uuid = orig[0].uuid

                        celement = celements[0]
                        if c_uuid is not None:
                            celement.set(self.xml.UUID, c_uuid)

                        crecord = self.xml.record(component.table, celement)
                        if not crecord:
                            self.error = S3XRC_VALIDATION_ERROR
                            continue

                        cvector = XVector(self.db, component.prefix, component.name, c_id,
                                          record=crecord,
                                          permit=permit,
                                          audit=audit,
                                          onvalidation=component.get_attr("onvalidation"),
                                          onaccept=component.get_attr("onaccept"))

                        cvector.pkey = pkey
                        cvector.fkey = fkey

                        vector.components.append(cvector)

            if self.error is None:
                imports.append(vector)

        if self.error is None or ignore_errors:
            for i in xrange(0, len(imports)):
                vector = imports[i]

                success = vector.commit()
                if not success and not vector.permitted:
                    self.error = S3XRC_NOT_PERMITTED
                    continue
                elif not success:
                    self.error = S3XRC_DATA_IMPORT_ERROR
                    continue

        return (self.error is None) or ignore_errors


    #--------------------------------------------------------------------------
    def options_xml(self, prefix, name, joins=[]):

        """ Exports options for select fields """

        self.error = None
        options = self.xml.get_options(prefix, name, joins=joins)

        return self.xml.tree([options], domain=self.domain, url=self.base_url)


# *****************************************************************************
class XVector(object):

    """ Helper class for database commits """

    ACTION = dict(create="create", update="update")

    UUID = "uuid"

    #--------------------------------------------------------------------------
    def __init__(self, db, prefix, name, id,
                 record=None,
                 permit=None,
                 audit=None,
                 onvalidation=None,
                 onaccept=None):

        self.db=db

        self.prefix=prefix
        self.name=name
        self.tablename = "%s_%s" % (self.prefix, self.name)
        self.table = self.db[self.tablename]

        self.id=id

        self.method=None
        self.record=record

        self.onvalidation=onvalidation
        self.onaccept=onaccept
        self.audit=audit

        self.components = []

        self.accepted=True
        self.permitted=True
        self.committed=False

        if not self.id:
            self.id = 0
            self.method = permission = self.ACTION["create"]

            if self.UUID in self.table:
                uuid = self.record.get(self.UUID, None)
                if uuid is not None:
                    orig = self.db(self.table[self.UUID]==uuid).select(self.table.id, limitby=(0,1))
                    if len(orig):
                        self.id = orig[0].id
                        self.method = permission = self.ACTION["update"]

        else:
            self.method = permission = self.ACTION["update"]

            if not self.db(self.table.id==id).count():
                self.id = 0
                self.method = permission = self.ACTION["create"]
            else:
                if self.UUID in self.record:
                    del self.record[self.UUID]

        if permit and not \
           permit(permission, self.tablename, record_id=self.id):
            self.permitted=False


    #--------------------------------------------------------------------------
    def commit(self):

        if not self.committed:

            if self.accepted and self.permitted:
                form = Storage() # PseudoForm for callbacks
                form.method = self.method
                form.vars = self.record
                form.vars.id = self.id

                if self.onvalidation:
                    self.onvalidation(form)

                if self.method == self.ACTION["update"]:
                    try:
                        success = self.db(self.table.id==self.id).update(**dict(self.record))
                        if len(self.components):
                            db_record = self.db(self.table.id==self.id).select(self.table.ALL)[0]
                    except:
                        return False
                    if success:
                        self.committed = True
                elif self.method == self.ACTION["create"]:
                    try:
                        success = self.table.insert(**dict(self.record))
                        if len(self.components):
                            db_record = self.db(self.table.id==success).select(self.table.ALL)[0]
                    except:
                        return False
                    if success:
                        self.id = success
                        self.committed = True

                if self.committed:
                    form.vars.id = self.id
                    if self.audit:
                        self.audit(self.method, self.prefix, self.name,
                                   form=form, record=self.id, representation="xml")
                    if self.onaccept:
                        self.onaccept(form)
                else:
                    return False

        for i in xrange(0, len(self.components)):
            component = self.components[i]

            pkey = component.pkey
            fkey = component.fkey

            component.record[fkey] = db_record[pkey]
            component.commit()

        return True


# *****************************************************************************
class XRequest(object):

    DEFAULT_REPRESENTATION = "html"

    #--------------------------------------------------------------------------
    def __init__(self, rc, prefix, name, request, session=None):

        assert rc is not None, "Resource controller must not be None."
        self.rc = rc

        self.prefix = prefix or request.controller
        self.name = name or request.function

        self.request = request
        if session is not None:
            self.session = session
        else:
            self.session = Storage()

        self.error = None
        self.invalid = False
        self.badmethod = False
        self.badrecord = False
        self.badrequest = False

        self.representation = request.extension
        self.http = request.env.request_method
        self.extension = False

        self.tablename = "%s_%s" % (self.prefix, self.name)
        self.table = self.rc.db[self.tablename]

        self.method = None
        self.id = None
        self.record = None

        self.component = None
        self.pkey = self.fkey = None
        self.component_name = None
        self.component_id = None
        self.multiple = True

        if not self.__parse():
            return None

        if not self.__record():
            return None

        # Check for component
        if self.component_name:
            self.component, self.pkey, self.fkey = self.rc.model.get_component(self.prefix, self.name, self.component_name)

            if not self.component:
                self.invalid = self.badrequest = True
                return None

            if "multiple" in self.component.attr:
                self.multiple = self.component.attr.multiple

            if not self.component_id:
                if self.args[len(self.args)-1].isdigit():
                    self.component_id = self.args[len(self.args)-1]

        # Check for custom action
        self.custom_action = self.rc.model.get_method(self.prefix, self.name,
                                                 component_name=self.component_name,
                                                 method=self.method)

        # Append record ID to request as necessary
        if self.id:
            if len(self.args)>0 or len(self.args)==0 and ('select' in self.request.vars):
                if self.component and not self.args[0].isdigit():
                    self.args.insert(0, str(self.id))
                    if self.representation==self.DEFAULT_REPRESENTATION or self.extension:
                        self.request.args.insert(0, str(self.id))
                    else:
                        self.request.args.insert(0, '%s.%s' % (self.id, self.representation))
                elif not self.component and not (str(self.id) in self.args):
                    self.args.append(self.id)
                    if self.representation==self.DEFAULT_REPRESENTATION or self.extension:
                        self.request.args.append(self.id)
                    else:
                        self.request.args.append('%s.%s' % (self.id, self.representation))


    #--------------------------------------------------------------------------
    def __parse(self):

        """ Parses a web2py request for the REST interface """

        self.args = []

        components = self.rc.model.components

        if len(self.request.args)>0:

            # Check for extensions

            for i in range(0, len(self.request.args)):
                arg = self.request.args[i]
                if '.' in arg:
                    arg, ext = arg.rsplit('.',1)
                    if ext and len(ext)>0:
                        self.representation = str.lower(ext)
                        self.extension = True
                self.args.append(str.lower(arg))

            # Parse arguments
            if self.args[0].isdigit():
                self.id = self.args[0]
                if len(self.args)>1:
                    self.component_name = self.args[1]
                    if self.component_name in components:
                        if len(self.args)>2:
                            if self.args[2].isdigit():
                                self.component_id = self.args[2]
                            else:
                                self.method = self.args[2]
                    else:
                        self.invalid = self.badrequest = True
                        return False
            else:
                if self.args[0] in components:
                    self.component_name = self.args[0]
                    if len(self.args)>1:
                        if self.args[1].isdigit():
                            self.component_id = self.args[1]
                        else:
                            self.method = self.args[1]
                else:
                    self.method = self.args[0]
                    if len(self.args)>1 and self.args[1].isdigit():
                        self.id = self.args[1]

        # Check format option
        if 'format' in self.request.get_vars:
            self.representation = str.lower(self.request.get_vars.format)

        # Representation fallback
        if not self.representation:
            self.representation = self.DEFAULT_REPRESENTATION

        return True


    #--------------------------------------------------------------------------
    def __record(self):

        """ Tries to find the primary resource record in a request """

        # Check record ID passed in the request
        if self.id:
            query = (self.table.id==self.id)
            if 'deleted' in self.table:
                query = ((self.table.deleted==False) | (self.table.deleted==None)) & query
            records = self.rc.db(query).select(self.table.ALL, limitby=(0,1))
            if not records:
                self.id = None
                self.invalid = self.badrecord = True
                return False
            else:
                self.record = records[0]

        # Check for ?select=
        if not self.id and 'select' in self.request.vars:
            if self.request.vars["select"] == "ALL":
                return True
            id_label = str.strip(self.request.vars.id_label)
            if 'pr_pe_label' in self.table:
                query = (self.table.pr_pe_label==id_label)
                if 'deleted' in self.table:
                    query = ((self.table.deleted==False) | (self.table.deleted==None)) & query
                records = self.rc.db(query).select(self.table.ALL, limitby=(0,1))
                if records:
                    self.record = records[0]
                    self.id = self.record.id
                else:
                    self.id = 0
                    self.invalid = self.badrecord = True
                    return False

        # Retrieve prior selected ID, if any
        if not self.id and len(self.request.args)>0:

            self.id = self.rc.get_session(self.session, self.prefix, self.name)

            if self.id:
                query = (self.table.id==self.id)
                if 'deleted' in self.table:
                    query = ((self.table.deleted==False) | (self.table.deleted==None)) & query
                records = self.rc.db(query).select(self.table.ALL, limitby=(0,1))
                if not records:
                    self.id = None
                    self.rc.clear_session(self.session, self.prefix, self.name)
                else:
                    self.record = records[0]

        # Remember primary record ID for further requests
        if self.id:
            self.rc.store_session(self.session, self.prefix, self.name, self.id)

        return True


    #--------------------------------------------------------------------------
    def here(self, representation=None):

        """ Backlink producing the same request """

        args = []
        vars = {}

        if not representation:
            representation = self.representation

        if self.component:
            args = [self.id]
            if not representation==self.DEFAULT_REPRESENTATION:
                args.append('%s.%s' % (self.component_name, representation))
            else:
                args.append(self.component_name)
            if self.method:
                args.append(self.method)
                if self.component_id:
                    args.append(self.component_id)
        else:
            if self.method:
                args.append(self.method)
            if self.id:
                if not representation==self.DEFAULT_REPRESENTATION:
                    args.append('%s.%s' % (self.id, representation))
                else:
                    args.append(self.id)
            else:
                if not representation==self.DEFAULT_REPRESENTATION:
                    vars = {'format': representation}

        return(URL(r=self.request, c=self.request.controller, f=self.name, args=args, vars=vars))


    #--------------------------------------------------------------------------
    def other(self, method=None, record_id=None, representation=None):

        """ Backlink to another method+record_id of the same resource """

        args = []
        vars = {}

        if not representation:
            representation = self.representation

        if not record_id:
            record_id = self.id
            component_id = self.component_id
        else:
            component_id = None

        if self.component:
            args = [record_id]
            if not representation==self.DEFAULT_REPRESENTATION:
                args.append('%s.%s' % (self.component_name, representation))
            else:
                args.append(self.component_name)
            if method:
                args.append(method)
                if component_id:
                    args.append(component_id)
        else:
            if method:
                args.append(method)
            if record_id:
                if not representation==self.DEFAULT_REPRESENTATION:
                    args.append('%s.%s' % (record_id, representation))
                else:
                    args.append(record_id)
            else:
                if not representation==self.DEFAULT_REPRESENTATION:
                    vars = {'format': representation}

        return(URL(r=self.request, c=self.request.controller, f=self.name, args=args, vars=vars))


    #--------------------------------------------------------------------------
    def there(self, representation=None):

        """ Backlink producing a HTTP/list request to the same resource """

        args = []
        vars = {}

        if not representation:
            representation = self.representation

        if self.component:
            args = [self.id]
            if not representation==self.DEFAULT_REPRESENTATION:
                args.append('%s.%s' % (self.component_name, representation))
            else:
                args.append(self.component_name)
        else:
            if not representation==self.DEFAULT_REPRESENTATION:
                vars = {'format': representation}

        return(URL(r=self.request, c=self.request.controller, f=self.name, args=args, vars=vars))


    #--------------------------------------------------------------------------
    def same(self, representation=None):

        """ Backlink producing the same request with neutralized primary record ID """

        args = []
        vars = {}

        if not representation:
            representation = self.representation

        if self.component:
            args = ['[id]']
            if not representation==self.DEFAULT_REPRESENTATION:
                args.append('%s.%s' % (self.component_name, representation))
            else:
                args.append(self.component_name)
            if self.method:
                args.append(self.method)
        else:
            if self.method:
                args.append(self.method)
            if self.id or self.method=="read":
                if not representation==self.DEFAULT_REPRESENTATION:
                    args.append('[id].%s' % representation)
                else:
                    args.append('[id]')
            else:
                if not representation==self.DEFAULT_REPRESENTATION:
                    vars = {'format': representation}

        return(URL(r=self.request, c=self.request.controller, f=self.name, args=args, vars=vars))


    #--------------------------------------------------------------------------
    def target(self):

        if self.component is not None:
            return (
                self.component.prefix,
                self.component.name,
                self.component.table,
                self.component.tablename
            )
        else:
            return (
                self.prefix,
                self.name,
                self.table,
                self.tablename
            )


    #--------------------------------------------------------------------------
    def export_xml(self, permit=None, audit=None, template=None, filterby=None, pretty_print=False):

        """ Export the requested resources as XML """

        if self.component:
            joins = [(self.component, self.pkey, self.fkey)]
        else:
            if "components" in self.request.vars:
                joins = []
                if not self.request.vars["components"]=="NONE":
                    components = self.request.vars["components"].split(",")
                    for c in components:
                        component, pkey, fkey = self.rc.model.get_component(self.prefix, self.name, c)
                        if component is not None:
                            joins.append([component, pkey, fkey])
            else:
                joins = self.rc.model.get_components(self.prefix, self.name)

        if "start" in self.request.vars:
            start = int(self.request.vars["start"])
        else:
            start = None

        if "limit" in self.request.vars:
            limit = int(self.request.vars["limit"])
        else:
            limit = None

        tree = self.rc.export_xml(self.prefix, self.name, self.id,
                                  joins=joins,
                                  filterby=filterby,
                                  permit=permit,
                                  audit=audit,
                                  start=start,
                                  limit=limit)

        if template is not None:
            tree = self.rc.xml.transform(tree, template, domain=self.rc.domain, base_url=self.rc.base_url)
            if not tree:
                self.error = self.rc.error
                return None

        return self.rc.xml.tostring(tree, pretty_print=pretty_print)


    #--------------------------------------------------------------------------
    def export_json(self, permit=None, audit=None, template=None, filterby=None, pretty_print=False):

        """ Export the requested resources as JSON """

        if self.component:
            joins = [(self.component, self.pkey, self.fkey)]
        else:
            if "components" in self.request.vars:
                joins = []
                if not components=="NONE":
                    components = self.request.vars["components"].split(",")
                    for c in components:
                        component, pkey, fkey = self.model.get_component(self.prefix, self.name, c)
                        if component is not None:
                            joins.append(component, pkey, fkey)
            else:
                joins = self.rc.model.get_components(self.prefix, self.name)

        if "start" in self.request.vars:
            start = int(self.request.vars["start"])
        else:
            start = None

        if "limit" in self.request.vars:
            limit = int(self.request.vars["limit"])
        else:
            limit = None

        tree = self.rc.export_xml(self.prefix, self.name, self.id,
                               joins=joins,
                               filterby=filterby,
                               permit=permit,
                               audit=audit,
                               start=start,
                               limit=limit,
                               show_urls=False)

        if template is not None:
            tree = self.rc.xml.transform(tree, template, domain=self.rc.domain, base_url=self.rc.base_url)
            if not tree:
                self.error = self.rc.error
                return None

        return self.rc.xml.tree2json(tree, pretty_print=pretty_print)


    #--------------------------------------------------------------------------
    def import_xml(self, tree, permit=None, audit=None, onvalidation=None, onaccept=None):

        """ import the requested resources from XML """

        if self.component:
            skip_resource = True
            joins = [(self.component, self.pkey, self.fkey)]
        else:
            skip_resource = False
            joins = self.rc.model.get_components(self.prefix, self.name)

        if self.method=="create":
            self.id=None

        # Add "&ignore_errors=True" to the URL to override any import errors:
        # Unsuccessful commits simply get ignored, no error message is returned,
        # invalid records are not imported at all, but all valid records in the
        # source are committed (whereas the standard method stops at any errors).
        # This is a backdoor for experts who exactly know what they're doing,
        # it's not recommended for general use, and should not be represented
        # in the UI!
        # Also note that this option is subject to change in future versions!
        if "ignore_errors" in self.request.vars:
            ignore_errors = True
        else:
            ignore_errors = False

        return self.rc.import_xml(self.prefix, self.name, self.id, tree,
                                  joins=joins,
                                  skip_resource=skip_resource,
                                  permit=permit,
                                  audit=audit,
                                  onvalidation=onvalidation,
                                  onaccept=onaccept,
                                  ignore_errors=ignore_errors)


    #--------------------------------------------------------------------------
    def options_xml(self, pretty_print=False):

        """ Export the options of a field in the resource as XML """

        if "field" in self.request.vars:
            field = self.request.vars["field"]
        else:
            field = None

        if field is None:
            if self.component:
                tree = self.rc.options_xml(self.component.prefix, self.component.name)
            else:
                joins = self.rc.model.get_components(self.prefix, self.name)
                tree = self.rc.options_xml(self.prefix, self.name, joins=joins)

            return self.rc.xml.tostring(tree, pretty_print=pretty_print)
        else:
            if self.component:
                tree = self.rc.xml.get_field_options(self.component.table, field)
            else:
                tree = self.rc.xml.get_field_options(self.table, field)

            tree.set("id", "%s_%s_%s" % (self.prefix, self.name, field))
            tree.set("name", "%s" % field)

            return self.rc.xml.tostring(tree, pretty_print=pretty_print)


    #--------------------------------------------------------------------------
    def options_json(self, pretty_print=False):

        """ Export the options of a field in the resource as JSON """

        if "field" in self.request.vars:
            field = self.request.vars["field"]
        else:
            field = None

        if field is None:
            if self.component:
                tree = self.rc.options_xml(self.component.prefix, self.component.name)
            else:
                joins = self.rc.model.get_components(self.prefix, self.name)
                tree = self.rc.options_xml(self.prefix, self.name, joins=joins)

            return self.rc.xml.tree2json(tree, pretty_print=pretty_print)
        else:
            if self.component:
                tree = self.rc.xml.get_field_options(self.component.table, field)
            else:
                tree = self.rc.xml.get_field_options(self.table, field)

            tree = etree.ElementTree(tree)

            return self.rc.xml.tree2json(tree, pretty_print=pretty_print)


# *****************************************************************************
class S3XML(object):

    """
        XML interface for S3XRC

        @param db: the database abstraction layer
        @type db: DAL
        @param domain:
            the domain name of the application instance, used to identify the origin of data
        @type domain: string
        @param base_url: the base URL of the instance
        @type base_url: string
        @param gis: the geospatial information handler of the application
        @type gis: GIS

    """

    S3XRC_NAMESPACE = "http://www.sahanapy.org/wiki/S3XRC" #: The S3XRC namespace URI
    S3XRC = "{%s}" % S3XRC_NAMESPACE #: LXML namespace prefix
    NSMAP = {None: S3XRC_NAMESPACE} #: LXML default namespace

    UUID = "uuid"
    Lat = "lat"
    Lon = "lon"
    Marker = "marker_id"
    FeatureClass = "feature_class_id"

    IGNORE_FIELDS = ["deleted", "id"]

    FIELDS_TO_ATTRIBUTES = [
            "created_on",
            "modified_on",
            "created_by",
            "modified_by",
            "uuid",
            "admin"]

    ATTRIBUTES_TO_FIELDS = ["admin"]

    TAG = dict(
        root="s3xrc",
        resource="resource",
        reference="reference",
        data="data",
        list="list",
        item="item",
        object="object",
        select="select",
        field="field",
        option="option",
        options="options"
        )

    ATTRIBUTE = dict(
        name="name",
        table="table",
        field="field",
        value="value",
        resource="resource",
        domain="domain",
        url="url",
        error="error",
        start="start",
        limit="limit",
        success="success",
        results="results",
        lat="lat",
        latmin="latmin",
        latmax="latmax",
        lon="lon",
        lonmin="lonmin",
        lonmax="lonmax",
        marker="marker"
        )

    ACTION = dict(
        create="create",
        read="read",
        update="update",
        delete="delete"
    )

    PREFIX = dict(
        resource="$",
        options="$o",
        reference="$k",
        attribute="@",
        text="$"
    )

    PY2XML = [('&', '&amp;'), ('<', '&lt;'), ('>', '&gt;'), ('"', '&quot;'), ("'", '&apos;')]
    XML2PY = [('<', '&lt;'), ('>', '&gt;'), ('"', '&quot;'), ("'", '&apos;'), ('&', '&amp;')]


    #--------------------------------------------------------------------------
    def __init__(self, db, domain=None, base_url=None, gis=None):

        self.db = db
        self.error = None

        self.domain = domain
        self.base_url = base_url

        self.gis = gis


    #--------------------------------------------------------------------------
    def parse(self, source):

        self.error = None

        try:
            parser = etree.XMLParser(no_network=False)
            result = etree.parse(source, parser)
            return result
        except:
            self.error = S3XRC_PARSE_ERROR
            return None


    #--------------------------------------------------------------------------
    def transform(self, tree, template_path, domain=None, base_url=None):

        self.error = None

        ac = etree.XSLTAccessControl(read_file=True, read_network=True)

        template = self.parse(template_path)
        if template:
            try:
                transformer = etree.XSLT(template, access_control=ac)
                if domain is not None:
                    domain = "'%s'" % domain
                    if base_url is not None:
                        base_url = "'%s'" % base_url
                        result = transformer(tree, domain=domain, base_url=base_url)
                    else:
                        result = transformer(tree, domain=domain)
                else:
                    result = transformer(tree)
                return result
            except:
                self.error = S3XRC_TRANSFORMATION_ERROR
                return None
        else:
            # Error parsing the XSL template
            return None


    #--------------------------------------------------------------------------
    def tostring(self, tree, pretty_print=False):

        return etree.tostring(tree,
                                xml_declaration=True,
                                encoding="utf-8",
                                pretty_print=pretty_print)


    #--------------------------------------------------------------------------
    def xml_encode(self, obj):

        if obj:
            for (x,y) in self.PY2XML:
                obj = obj.replace(x, y)
        return obj


    #--------------------------------------------------------------------------
    def xml_decode(self, obj):

        if obj:
            for (x,y) in self.XML2PY:
                obj = obj.replace(y, x)
        return obj


    #--------------------------------------------------------------------------
    def element(self, table, record, skip=[], url=None, download_url=None):

        """ Creates an element from a Storage() record """

        if not download_url:
            download_url = ""

        resource= etree.Element(self.TAG["resource"])
        resource.set(self.ATTRIBUTE["name"], table._tablename)

        if self.UUID in table.fields and self.UUID in record:
            value = str(table[self.UUID].formatter(record[self.UUID]))
            resource.set(self.UUID, self.xml_encode(value))

        readable = filter( lambda key: \
                        key not in self.IGNORE_FIELDS and \
                        key not in skip and \
                        record[key] is not None and \
                        key in table.fields and \
                        not(key==self.UUID),
                        record.keys())

        for i in xrange(0, len(readable)):

            f = readable[i]
            v = record[f]

            text = value = self.xml_encode(str(table[f].formatter(v)).decode('utf-8'))
            if table[f].represent:
                text = str(table[f].represent(v)).decode('utf-8')
                # Filter out markup from text
                try:
                    markup = etree.XML(text)
                    text = markup.xpath(".//text()")
                    if text:
                        text = " ".join(text)
                except etree.XMLSyntaxError:
                    pass
                text = self.xml_encode(text)

            if f in self.FIELDS_TO_ATTRIBUTES:
                resource.set(f, text)

            elif isinstance(table[f].type, str) and \
                table[f].type[:9] == "reference":

                _ktable = table[f].type[10:]
                ktable = self.db[_ktable]

                if self.UUID in ktable.fields:
                    uuid = self.db(ktable.id==value).select(ktable[self.UUID], limitby=(0, 1))
                    if uuid:
                        uuid = uuid[0].uuid
                        reference = etree.SubElement(resource, self.TAG["reference"])
                        reference.set(self.ATTRIBUTE["field"], f)
                        reference.set(self.ATTRIBUTE["resource"], _ktable)
                        reference.set(self.UUID, self.xml_encode(str(uuid)))
                        reference.text = text

                        if self.Lat in ktable.fields and self.Lon in ktable.fields:
                            LatLon = self.db(ktable.id == value).select(ktable[self.Lat], ktable[self.Lon], limitby=(0, 1))
                            if LatLon:
                                LatLon = LatLon[0]
                                reference.set(self.ATTRIBUTE["lat"], self.xml_encode("%.6f" % LatLon[self.Lat]))
                                reference.set(self.ATTRIBUTE["lon"], self.xml_encode("%.6f" % LatLon[self.Lon]))
                                # Look up the marker to display
                                if self.gis is not None:
                                    marker = self.gis.get_marker(value)
                                    marker_url = "%s/%s" % (download_url, marker)
                                    reference.set(self.ATTRIBUTE["marker"], self.xml_encode(marker_url))


            elif isinstance(table[f].type, str) and \
                table[f].type[:6] == "upload":

                data = etree.SubElement(resource, self.TAG["data"])
                data.set(self.ATTRIBUTE["field"], f)
                data.text = "%s/%s" % (download_url, value)

            else:
                data = etree.SubElement(resource, self.TAG["data"])
                data.set(self.ATTRIBUTE["field"], f)
                if table[f].represent:
                    data.set(self.ATTRIBUTE["value"], value )
                data.text = text

        if url is not None:
            resource.set(self.ATTRIBUTE["url"], url)

        return resource


    #--------------------------------------------------------------------------
    def tree(self, resources, domain=None, url=None, start=None, limit=None, results=None):

        """ Builds a tree from a list of elements """

        # For now we do not nsmap, because the default namespace cannot be
        # matched in XSLT templates (need explicit prefix) and thus this
        # would require a rework of all existing templates (which is however useful)
        root = etree.Element(self.TAG["root"]) #, nsmap=self.NSMAP)

        root.set(self.ATTRIBUTE["success"], str(False))

        if resources is not None:

            if len(resources):
                root.set(self.ATTRIBUTE["success"], str(True))

            if start is not None:
                root.set(self.ATTRIBUTE["start"], str(start))
            if limit is not None:
                root.set(self.ATTRIBUTE["limit"], str(limit))
            if results is not None:
                root.set(self.ATTRIBUTE["results"], str(results))

            root.extend(resources)

        if domain is not None:
            root.set(self.ATTRIBUTE["domain"], self.domain)

        if url is not None:
            root.set(self.ATTRIBUTE["url"], self.base_url)

        root.set(self.ATTRIBUTE["latmin"], str(self.gis.get_bounds()['min_lat']))
        root.set(self.ATTRIBUTE["latmax"], str(self.gis.get_bounds()['max_lat']))
        root.set(self.ATTRIBUTE["lonmin"], str(self.gis.get_bounds()['min_lon']))
        root.set(self.ATTRIBUTE["lonmax"], str(self.gis.get_bounds()['max_lon']))

        return etree.ElementTree(root)


    #--------------------------------------------------------------------------
    def get_field_options(self, table, fieldname):

        select = etree.Element(self.TAG["select"])

        if fieldname in table.fields:
            field = table[fieldname]
        else:
            return select

        requires = field.requires

        select.set(self.TAG["field"], fieldname)

        if not isinstance(requires, (list, tuple)):
            requires = [requires]

        if requires:
            r = requires[0]
            options = []
            if isinstance(r, IS_NULL_OR) and hasattr(r.other, 'options'):
                null = etree.SubElement(select, self.TAG["option"])
                null.set(self.ATTRIBUTE["value"], "")
                null.text = ""
                options = r.other.options()
            elif hasattr(r, "options"):
                options = r.options()

            for (value, text) in options:
                value = self.xml_encode(str(value).decode("utf-8"))
                text = self.xml_encode(str(text).decode("utf-8"))

                option = etree.SubElement(select, self.TAG["option"])
                option.set(self.ATTRIBUTE["value"], value)
                option.text = text

        return select


    #--------------------------------------------------------------------------
    def get_options(self, prefix, name, joins=[]):

        resource = "%s_%s" % (prefix, name)

        options = etree.Element(self.TAG["options"])
        options.set(self.ATTRIBUTE["resource"], resource)

        if resource in self.db:
            table = self.db[resource]

            for f in table.fields:
                select = self.get_field_options(table, f)
                if len(select):
                    options.append(select)

            for j in joins:
                component = j[0]
                coptions = etree.Element(self.TAG["options"])
                coptions.set(self.ATTRIBUTE["resource"], component.tablename)
                for f in component.table.fields:
                    select = self.get_field_options(component.table, f)
                    if select:
                        coptions.append(select)
                options.append(coptions)

        return options


    #--------------------------------------------------------------------------
    def validate(self, table, record, fieldname, value):

        """ Validates a single value """

        requires = table[fieldname].requires

        if not requires:
            return (value, None)
        else:
            if record is not None:
                # Skip validation of unchanged values on update
                if record[fieldname] is not None and record[fieldname]==value:
                    return (value, None)

            if not isinstance(requires, (list, tuple)):
                requires = [requires]

            for validator in requires:
                (value, error) = validator(value)
                if error:
                    return (value, error)

            return(value, None)


    #--------------------------------------------------------------------------
    def record(self, table, element, skip=[]):

        """ Creates a Storage() record from an element and validates it """

        valid = True

        record = Storage()
        original = None

        if self.UUID in table.fields and self.UUID not in skip:
            uuid = element.get(self.UUID, None)
            if uuid:
                record[self.UUID] = uuid
                original = self.db(table.uuid==uuid).select(table.ALL, limitby=(0,1))
                if original:
                    original = original[0]
                else:
                    original = None

        for f in self.ATTRIBUTES_TO_FIELDS:
            if f in self.IGNORE_FIELDS or f in skip:
                continue
            if f in table.fields:
                v= value = self.xml_decode(element.get(f, None))
                if value is not None:
                    if not isinstance(value, (str, unicode)):
                        v = str(value)
                    (value, error) = self.validate(table, original, f, v)
                    if error:
                        element.set(self.ATTRIBUTE["error"], "%s: %s" % (f, error))
                        valid = False
                        continue
                    else:
                        record[f]=value

        for child in element:
            if child.tag==self.TAG["data"]:
                f = child.get(self.ATTRIBUTE["field"], None)
                if not f or f not in table.fields:
                    continue
                if f in self.IGNORE_FIELDS or f in skip:
                    continue
                if table[f].type.startswith('reference'):
                    continue
                value = self.xml_decode(child.get(self.ATTRIBUTE["value"], None))
                if value is None:
                    value = self.xml_decode(child.text)
                if value is None:
                    value = table[f].default
                if value is None and table[f].type == "string":
                    value = ''
                if value == '' and not table[f].type == "string":
                    value = table[f].default

                if value is not None:
                    v = value
                    if not isinstance(value, (str, unicode)):
                        v = str(value)
                    (value, error) = self.validate(table, original, f, v)
                    if error:
                        child.set(self.ATTRIBUTE["error"], "%s: %s" % (f, error))
                        valid = False
                        continue
                    else:
                        child.set(self.ATTRIBUTE["value"], v)
                        record[f]=value

            elif child.tag==self.TAG["reference"]:
                f = child.get(self.ATTRIBUTE["field"], None)
                if not f or f not in table.fields:
                    continue
                if f in self.IGNORE_FIELDS or f in skip:
                    continue
                ktablename =  child.get(self.ATTRIBUTE["resource"], None)
                uuid = child.get(self.UUID, None)
                if not (ktablename and uuid):
                    continue
                if ktablename in self.db and self.UUID in self.db[ktablename]:
                    ktable = self.db[ktablename]
                    krecord = self.db(ktable.uuid==uuid).select(ktable.id, limitby=(0,1))
                    if krecord:
                        record[f] = krecord[0].id
                else:
                    continue

        if valid:
            return record
        else:
            return None


    #--------------------------------------------------------------------------
    def select_resources(self, tree, tablename):

        resources = []

        if not tree:
            return resources

        if isinstance(tree, ElementTree):
            root = tree.getroot()
            if not root.tag==self.TAG["root"]:
                return resources
        else:
            root = tree

        expr = './%s[@%s="%s"]' % \
               (self.TAG["resource"], self.ATTRIBUTE["name"], tablename)

        resources = root.xpath(expr)
        return resources


    #--------------------------------------------------------------------------
    def __json2element(self, key, value, native=False):

        if isinstance(value, dict):
            return self.__obj2element(key, value, native=native)

        elif isinstance(value, (list, tuple)):
            if not key==self.TAG["item"]:
                _list = etree.Element(key)
            else:
                _list = etree.Element(self.TAG["list"])
            for obj in value:
                item = self.__json2element(self.TAG["item"], obj, native=native)
                _list.append(item)
            return _list

        else:
            if native:
                element = etree.Element(self.TAG["data"])
                element.set(self.ATTRIBUTE["field"], key)
            else:
                element = etree.Element(key)
            if not isinstance(value, (str, unicode)):
                value = str(value)
            element.text = self.xml_encode(value)
            return element


    #--------------------------------------------------------------------------
    def __obj2element(self, tag, obj, native=False):

        prefix = name = resource = field = None

        if tag is None:
            tag = self.TAG["object"]
        elif native:
            if tag.startswith(self.PREFIX["reference"]):
                field = tag[len(self.PREFIX["reference"])+1:]
                tag = self.TAG["reference"]
            elif tag.startswith(self.PREFIX["options"]):
                resource = tag[len(self.PREFIX["options"])+1:]
                tag = self.TAG["options"]
            elif tag.startswith(self.PREFIX["resource"]):
                resource = tag[len(self.PREFIX["resource"])+1:]
                tag = self.TAG["resource"]
            elif not tag==self.TAG["root"]:
                field = tag
                tag = self.TAG["data"]

        element = etree.Element(tag)

        if native:
            if resource:
                if tag==self.TAG["resource"]:
                    element.set(self.ATTRIBUTE["name"], resource)
                else:
                    element.set(self.ATTRIBUTE["resource"], resource)
            if field:
                element.set(self.ATTRIBUTE["field"], field)

        for k in obj.keys():
            m = obj[k]

            if isinstance(m, dict):
                child = self.__obj2element(k, m, native=native)
                element.append(child)

            elif isinstance(m, (list, tuple)):
                #l = etree.SubElement(element, k)
                for _obj in m:
                    child = self.__json2element(k, _obj, native=native)
                    element.append(child)

            else:
                if k == self.PREFIX["text"]:
                    element.text = self.xml_encode(m)

                elif k.startswith(self.PREFIX["attribute"]):
                    a = k[len(self.PREFIX["attribute"]):]
                    element.set(a, self.xml_encode(m))

                else:
                    child = self.__json2element(k, m, native=native)
                    element.append(child)

        return element


    #--------------------------------------------------------------------------
    def json2tree(self, source, format=None):

        try:
            root_dict = json.load(source)
        except ValueError, e:
            raise HTTP(400, body=json_message(False, 400, e.message))

        native=False

        if not format:
            format=self.TAG["root"]
            native=True

        if root_dict and isinstance(root_dict, dict):
            root = self.__obj2element(format, root_dict, native=native)
            if root is not None:
                return etree.ElementTree(root)

        return None


    #--------------------------------------------------------------------------
    def __element2json(self, element, native=False):

        if element.tag == self.TAG["list"]:

            obj = []

            for child in element:

                tag = child.tag

                if tag[0]=="{":
                    tag = tag.rsplit("}",1)[1]

                child_obj = self.__element2json(child, native=native)

                if child_obj:
                    obj.append(child_obj)

            return obj

        else:

            obj = {}

            for child in element:

                tag = child.tag

                if tag[0]=="{":
                    tag = tag.rsplit("}",1)[1]

                collapse = True

                if native:

                    if tag == self.TAG["resource"]:
                        resource = child.get(self.ATTRIBUTE["name"])
                        tag = "%s_%s" % (self.PREFIX["resource"], resource)
                        collapse = False

                    elif tag == self.TAG["options"]:
                        resource = child.get(self.ATTRIBUTE["resource"])
                        tag = "%s_%s" % (self.PREFIX["options"], resource)

                    elif tag == self.TAG["reference"]:
                        tag = "%s_%s" % (self.PREFIX["reference"], child.get(self.ATTRIBUTE["field"]))

                    elif tag == self.TAG["data"]:
                        tag = child.get(self.ATTRIBUTE["field"])

                child_obj = self.__element2json(child, native=native)

                if child_obj:
                    if not tag in obj:
                        if isinstance(child_obj, list) or not collapse:
                            obj[tag] = [child_obj]
                        else:
                            obj[tag] = child_obj
                    else:
                        if not isinstance(obj[tag], list):
                            obj[tag] = [obj[tag]]
                        obj[tag].append(child_obj)


            attributes = element.attrib
            for a in attributes:
                if native:
                    if a==self.ATTRIBUTE["name"] and element.tag==self.TAG["resource"]:
                        continue
                    if a==self.ATTRIBUTE["resource"] and element.tag==self.TAG["options"]:
                        continue
                    if a==self.ATTRIBUTE["field"] and \
                    element.tag in (self.TAG["data"], self.TAG["reference"]):
                        continue

                obj[self.PREFIX["attribute"] + a] = self.xml_decode(attributes[a])

            if element.text:
                obj[self.PREFIX["text"]] = self.xml_decode(element.text)

            if len(obj)==1 and obj.keys()[0] in (self.PREFIX["text"], self.TAG["item"], self.TAG["list"]):
                obj = obj[obj.keys()[0]]

            return obj


    #--------------------------------------------------------------------------
    def tree2json(self, tree, pretty_print=False):

        root = tree.getroot()

        if root.tag==self.TAG["root"]:
            native = True
        else:
            native = False

        root_dict = self.__element2json(root, native=native)

        if pretty_print:
            js = json.dumps(root_dict, indent=4)
            return '\n'.join([l.rstrip() for l in js.splitlines()])
        else:
            return json.dumps(root_dict)

# *****************************************************************************
