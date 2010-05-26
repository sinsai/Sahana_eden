# -*- coding: utf-8 -*-

"""
    S3XRC SahanaPy XML+JSON Resource Controller

    @version: 1.6
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

__all__ = ["S3ResourceController"]

import sys, uuid
import gluon.contrib.simplejson as json

from gluon.storage import Storage
from gluon.html import URL
from gluon.http import HTTP
from gluon.validators import IS_NULL_OR
from xml.etree.cElementTree import ElementTree
from lxml import etree

# Error messages
S3XRC_BAD_RESOURCE = "Invalid Resource"
S3XRC_PARSE_ERROR = "XML Parse Error"
S3XRC_TRANSFORMATION_ERROR = "XSLT Transformation Error"
S3XRC_BAD_SOURCE = "Invalid XML Source"
S3XRC_BAD_RECORD = "Record Not Found"
S3XRC_NO_MATCH = "No Matching Element"
S3XRC_VALIDATION_ERROR = "Validation Error"
S3XRC_DATA_IMPORT_ERROR = "Data Import Error"
S3XRC_NOT_PERMITTED = "Operation Not Permitted"
S3XRC_NOT_IMPLEMENTED = "Not Implemented"


class S3ObjectComponent(object):

    """
        Class to represent component relations between resources.
    """

    def __init__(self, db, prefix, name, **attr):

        """ Constructor """

        self.db = db
        self.prefix = prefix
        self.name = name
        self.tablename = "%s_%s" % (prefix, name)
        assert self.tablename in self.db, "Table must exist in the database."
        self.table = self.db[self.tablename]

        self.attr = Storage(attr)
        if not "multiple" in self.attr:
            self.attr.multiple = True
        if not "deletable" in self.attr:
            self.attr.deletable = True
        if not "editable" in self.attr:
            self.attr.editable = True


    def get_join_keys(self, prefix, name):

        """ Reads the join keys of this component and a resource """

        if "joinby" in self.attr:
            joinby = self.attr.joinby
            tablename = "%s_%s" % (prefix, name)
            if tablename in self.db:
                table = self.db[tablename]
                if isinstance(joinby, str):
                    if joinby in table and joinby in self.table:
                        return (joinby, joinby)
                elif isinstance(joinby, dict):
                    if tablename in joinby and \
                       joinby[tablename] in self.table:
                        return ("id", joinby[tablename])

        return (None, None)


    def set_attr(self, name, value):

        """ Sets an attribute for a component """

        self.attr[name] = value


    def get_attr(self, name):

        """ Reads an attribute of the component """

        if name in self.attr:
            return self.attr[name]
        else:
            return None


class S3ObjectModel(object):


    """
        Class to handle the joined resources model

        @param db: the database abstraction layer
        @type db: DAL

    """


    def __init__(self, db):

        """ Constructor """

        self.db = db
        self.components = {}
        self.config = Storage()
        self.methods = {}
        self.cmethods = {}


    def configure(self, table, **attr):

        """ Updates the configuration of a resource """

        cfg = self.config.get(table._tablename, Storage())
        cfg.update(attr)
        self.config[table._tablename] = cfg


    def get_config(self, table, key):

        """ Reads a configuration setting of a resource """

        if table._tablename in self.config.keys():
            return self.config[table._tablename].get(key, None)
        else:
            return None


    def clear_config(self, table, *keys):

        """ Removes configuration settings of a resource """

        if not keys:
            if table._tablename in self.config.keys():
                del self.config[table._tablename]
        else:
            if table._tablename in self.config.keys():
                for k in keys:
                    if k in self.config[table._tablename]:
                        del self.config[table._tablename][k]


    def add_component(self, prefix, name, **attr):

        """ Adds a component to the model """

        assert "joinby" in attr, "Join key(s) must be defined."

        component = S3ObjectComponent(self.db, prefix, name, **attr)
        self.components[name] = component
        return component


    def get_component(self, prefix, name, component_name):

        """ Retrieves a component of a resource """

        if component_name in self.components and \
           not component_name == name:
            component = self.components[component_name]
            pkey, fkey = component.get_join_keys(prefix, name)
            if pkey:
                return (component, pkey, fkey)

        return (None, None, None)


    def get_components(self, prefix, name):

        """ Retrieves all components related to a resource """

        component_list = []
        for component_name in self.components:
            component, pkey, fkey = self.get_component(prefix, name,
                                                       component_name)
            if component:
                component_list.append((component, pkey, fkey))

        return component_list


    def set_method(self, prefix, name,
                   component_name=None,
                   method=None,
                   action=None):

        """ Adds a custom method for a resource or component """

        assert method is not None, "Method must be specified."
        tablename = "%s_%s" % (prefix, name)

        if not component_name:
            if method not in self.methods:
                self.methods[method] = {}
            self.methods[method][tablename] = action
        else:
            component = self.get_component(prefix, name, component_name)[0]
            if component:
                if method not in self.cmethods:
                    self.cmethods[method] = {}
                if component.tablename not in self.cmethods[method]:
                    self.cmethods[method][component.tablename] = {}
                self.cmethods[method][component.tablename][tablename] = action

        return True


    def get_method(self, prefix, name, component_name=None, method=None):

        """ Retrieves a custom method for a resource or component """

        if not method:
            return None

        tablename = "%s_%s" % (prefix, name)

        if not component_name:
            if method in self.methods and tablename in self.methods[method]:
                return self.methods[method][tablename]
            else:
                return None
        else:
            component = self.get_component(prefix, name, component_name)[0]
            if component and \
               method in self.cmethods and \
               component.tablename in self.cmethods[method] and \
               tablename in self.cmethods[method][component.tablename]:
                return self.cmethods[method][component.tablename][tablename]
            else:
                return None


    def set_attr(self, component_name, name, value):

        """ Sets an attribute for a component """

        return self.components[component_name].set_attr(name, value)


    def get_attr(self, component_name, name):

        """ Retrieves an attribute value of a component """

        return self.components[component_name].get_attr(name)


class S3ResourceController(object):

    """
        Resource controller class for S3.

    """

    RCVARS = "rcvars"
    ACTION = dict(
        create="create",
        read="read",
        update="update",
        delete="delete"
    )
    ROWSPERPAGE = 10

    MAX_DEPTH = 10


    def __init__(self, db, domain=None, base_url=None, rpp=None, gis=None):

        """ Constructor """

        assert db is not None, "Database must not be None."
        self.db = db

        self.error = None

        self.domain = domain
        self.base_url = base_url
        self.download_url = "%s/default/download" % base_url

        if rpp:
            self.ROWSPERPAGE = rpp

        self.model = S3ObjectModel(self.db)
        self.xml = S3XML(self.db, domain=domain, base_url=base_url, gis=gis)

        self.sync_resolve = None
        self.sync_log = None

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


    def search_simple(self, table, fields=None, label=None, filterby=None):

        """ Simple search function for resources """

        search_fields = []
        if fields and isinstance(fields, (list,tuple)):
            for f in fields:
                if table.has_key(f):
                    search_fields.append(f)
        if not search_fields:
            return None

        if label and isinstance(label,str):
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
                query = (table.deleted == False) & (query)
                # restrict to prior results (AND)
                if results:
                    query = (table.id.belongs(results)) & query
                if filterby:
                    query = (filterby) & (query)
                records = self.db(query).select(table.id)
                # rebuild result list
                results = [r.id for r in records]
                # any results left?
                if not results:
                    return None
            return results
        else:
            # no label given or wrong parameter type
            return None


    def export_xml(self, prefix, name, id,
                   joins=[],
                   filterby=None,
                   skip=[],
                   permit=None,
                   audit=None,
                   start=None,  # starting record
                   limit=None,  # pagesize
                   marker=None, # override marker to display KML feeds
                   show_urls=True, # Show URL's in <resource> elements
                   export_refs=False): # export referenced objects

        """ Exports data as XML tree """

        self.error = None

        resources = []
        _table = "%s_%s" % (prefix, name)

        if show_urls:
            burl = self.base_url
        else:
            burl = None

        if _table not in self.db or \
           (permit and not permit(self.ACTION["read"], _table)):
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
        if filterby:
            query = query & (filterby)

        if self.base_url:
            url = "%s/%s/%s" % (self.base_url, prefix, name)
        else:
            url = "/%s/%s" % (prefix, name)

        # Not GAE-compatible: .count()
        results = self.db(query).count()

        # Server-side pagination
        if start is not None: # not 'if start' as 0 is a valid value
            if not limit:
                limit = self.ROWSPERPAGE
            if limit <= 0:
                limit = 1
            if start < 0:
                start = 0
            limitby = (start, start + limit)
        else:
            limitby = None

        # Read records
        try:
            records = self.db(query).select(table.ALL, limitby=limitby) or []
        except:
            return None

        # Filter out unpermitted records
        if records and permit:
            records = filter(lambda r: permit(self.ACTION["read"],
                                              _table, record_id=r.id), records)

        # Filter out unpermitted joins
        if joins and permit:
            joins = filter(lambda j: permit(self.ACTION["read"],
                                            j[0].tablename), joins)

        # Read component records
        cdata = {}
        if records:
            for i in xrange(0, len(joins)):
                (c, pkey, fkey) = joins[i]
                pkeys = map(lambda r: r[pkey], records)
                # Not GAE-compatible: .belongs()
                cquery = (c.table[fkey].belongs(pkeys))
                if "deleted" in c.table:
                    cquery = (c.table.deleted == False) & cquery
                cdata[c.tablename] = self.db(cquery).select(c.table.ALL) or []

        # Export records
        exp_map = Storage()
        ref_map = []
        for i in xrange(0, len(records)):
            record = records[i]
            if audit:
                audit(self.ACTION["read"], prefix, name,
                      record=record.id, representation="xml")
            if show_urls:
                resource_url = "%s/%s" % (url, record.id)
            else:
                resource_url = None

            rmap = self.xml.rmap(table, record, skip=skip)
            resource = self.xml.element(table, record,
                                        skip=skip,
                                        url=resource_url,
                                        download_url=self.download_url,
                                        marker=marker)

            self.xml.add_references(resource, rmap)
            self.xml.gis_encode(rmap,
                                download_url=self.download_url,
                                marker=marker)

            ref_map.extend(rmap)
            resources.append(resource)

            if exp_map.get(table._tablename, None):
                exp_map[table._tablename].append(record.id)
            else:
                exp_map[table._tablename] = [record.id]

            # Export components of this record
            for j in xrange(0, len(joins)):
                (c, pkey, fkey) = joins[j]
                pkey = record[pkey]
                crecords = cdata[c.tablename]
                crecords = filter(lambda r: r[fkey] == pkey, crecords)
                _skip = [fkey,]
                if skip:
                    _skip.extend(skip)
                for k in xrange(0, len(crecords)):
                    crecord = crecords[k]
                    if permit and not permit(self.ACTION["read"],
                                             c.tablename, crecord.id):
                        continue
                    if audit:
                        audit(self.ACTION["read"], c.prefix, c.name,
                              record=crecord.id, representation="xml")
                    if show_urls:
                        resource_url = "%s/%s/%s/%s" % \
                                       (url, record.id, c.name, crecord.id)
                    else:
                        resource_url = None

                    rmap = self.xml.rmap(c.table, crecord, skip=_skip)
                    cresource = self.xml.element(c.table, crecord,
                                                 skip=_skip,
                                                 url=resource_url,
                                                 download_url=self.download_url,
                                                 marker=marker)

                    self.xml.add_references(cresource, rmap)
                    self.xml.gis_encode(rmap,
                                        download_url=self.download_url,
                                        marker=marker)

                    resource.append(cresource)
                    ref_map.extend(rmap)

                    if exp_map.get(c.tablename, None):
                        exp_map[c.tablename].append(crecord.id)
                    else:
                        exp_map[c.tablename] = [crecord.id]

        # Add referenced resources as required
        # TODO: URL's!
        depth = export_refs and self.MAX_DEPTH or 0
        while ref_map and depth:
            depth -= 1

            # Re-order reference map
            load_map = Storage()
            for i in xrange(0, len(ref_map)):
                r = ref_map[i]
                if r.uid:
                    exp_list = exp_map.get(r.table, None)
                    if exp_list and r.id in exp_list:
                        continue
                    else:
                        load_list = load_map.get(r.table, None)
                        if not load_list:
                            load_list = [r.id]
                            load_map[r.table] = load_list
                        else:
                            load_list.append(r.id)

            ref_map = []

            # Load referenced records
            for tablename in load_map.keys():
                prefix, name = tablename.split("_", 1)
                load_list = load_map[tablename]
                if permit:
                    if not permit(self.ACTION["read"], tablename):
                        continue
                    load_list = filter(lambda id:
                                       permit(self.ACTION["read"],
                                              tablename, id),
                                       load_list)
                    if not load_list:
                        continue
                table = self.db[tablename]
                query = (table.id.belongs(load_list))
                if "deleted" in table:
                    query = (table.deleted == False) & query
                records = self.db(query).select(table.ALL) or []
                for record in records:
                    if audit:
                        audit(self.ACTION["read"], prefix, name,
                              record=record.id, representation="xml")
                    rmap = self.xml.rmap(table, record, skip=skip)
                    resource = self.xml.element(table, record,
                                                skip=skip,
                                                #url=resource_url,
                                                download_url=self.download_url,
                                                marker=marker)

                    self.xml.add_references(resource, rmap)
                    self.xml.gis_encode(rmap,
                                        download_url=self.download_url,
                                        marker=marker)

                    resources.append(resource)
                    if exp_map.get(tablename, None):
                        exp_map[tablename].append(record.id)
                    else:
                        exp_map[tablename] = [record.id]
                    ref_map.extend(rmap)

        # Complete the tree
        return self.xml.tree(resources,
                             domain=self.domain,
                             url=burl,
                             results=results,
                             start=start,
                             limit=limit)


    def import_xml(self, prefix, name, id, tree,
                   joins=[],
                   skip_resource=False,
                   permit=None,
                   audit=None,
                   ignore_errors=False):

        """ Imports data from an XML tree """

        self.error = None

        tablename = "%s_%s" % (prefix, name)
        if tablename in self.db:
            table = self.db[tablename]
        else:
            self.error = S3XRC_BAD_RESOURCE
            return False

        onvalidation = self.model.get_config(table, "onvalidation")
        onaccept = self.model.get_config(table, "onaccept")

        elements = self.xml.select_resources(tree, tablename)
        if not elements: # nothing to import
            return True
        if id:
            try:
                db_record = self.db(table.id == id).select(table.ALL)[0]
            except:
                self.error = S3XRC_BAD_RECORD
                return False
        else:
            db_record = None
        if id and len(elements) > 1:
            # ID given, but multiple elements of that type
            # => try to find UUID match
            if self.xml.UID in table:
                uid = db_record[self.xml.UID]
                for element in elements:
                    if element.get(self.xml.UID) == uid:
                        elements = [element]
                        break
            if len(elements) > 1:
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
            vector = S3Vector(self.db, prefix, name, id,
                             record=record,
                             element=element,
                             permit=permit,
                             audit=audit,
                             sync=self.sync_resolve,
                             log=self.sync_log,
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
                            cvector = S3Vector(self.db,
                                               component.prefix,
                                               component.name, None,
                                               record=crecord,
                                               element=celement,
                                               permit=permit,
                                               audit=audit,
                                               sync=self.sync_resolve,
                                               log=self.sync_log,
                                               onvalidation=self.model.get_config(
                                                    component.table, "onvalidation"),
                                               onaccept=self.model.get_config(
                                                    component.table, "onaccept"))
                            cvector.pkey = pkey
                            cvector.fkey = fkey
                            vector.components.append(cvector)
                    else:
                        c_id = c_uid = None
                        if vector.id:
                            p = self.db(table.id == vector.id).select(table[pkey],
                                                                    limitby=(0,1))
                            if p:
                                p = p[0][pkey]
                                fields = [component.table.id]
                                if self.xml.UID in component.table:
                                    fields.append(component.table[self.xml.UID])
                                orig = self.db(component.table[fkey] == p).select(
                                        limitby=(0,1), *fields)
                                if orig:
                                    c_id = orig[0].id
                                    if self.xml.UID in component.table:
                                        c_uid = orig[0][self.UID]
                        celement = celements[0]
                        if c_uid:
                            celement.set(self.xml.UID, c_uid)
                        crecord = self.xml.record(component.table, celement)
                        if not crecord:
                            self.error = S3XRC_VALIDATION_ERROR
                            continue
                        cvector = S3Vector(self.db,
                                           component.prefix,
                                           component.name, c_id,
                                           element=celement,
                                           record=crecord,
                                           permit=permit,
                                           audit=audit,
                                           sync=self.sync_resolve,
                                           log=self.sync_log,
                                           onvalidation=self.model.get_config(
                                                component.table, "onvalidation"),
                                           onaccept=self.model.get_config(
                                                component.table, "onaccept"))
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

        return ignore_errors or not self.error


    def options_xml(self, prefix, name, joins=[]):

        """ Exports options for select fields """

        self.error = None
        options = self.xml.get_options(prefix, name, joins=joins)
        return self.xml.tree([options], domain=self.domain, url=self.base_url)


class S3Vector(object):

    """ Helper class for database commits """

    ACTION = dict(create="create", update="update")
    UID = "uuid"

    def __init__(self, db, prefix, name, id,
                 record=None,
                 element=None,
                 permit=None,
                 audit=None,
                 sync=None,
                 log=None,
                 onvalidation=None,
                 onaccept=None):

        """ Constructor """

        self.db=db
        self.prefix=prefix
        self.name=name

        self.tablename = "%s_%s" % (self.prefix, self.name)
        self.table = self.db[self.tablename]

        self.element=element
        self.record=record
        self.id=id

        self.components = []
        self.references = []

        self.method=None
        self.resolution=None

        self.onvalidation=onvalidation
        self.onaccept=onaccept
        self.audit=audit
        self.sync=sync
        self.log=log

        self.accepted=True
        self.permitted=True
        self.committed=False

        if not self.id:
            self.id = 0
            self.method = permission = self.ACTION["create"]
            if self.UID in self.table:
                uid = self.record.get(self.UID, None)
                if uid:
                    orig = self.db(self.table[self.UID] == uid).select(self.table.id,
                                                                       limitby=(0,1))
                    if orig:
                        self.id = orig[0].id
                        self.method = permission = self.ACTION["update"]

        else:
            self.method = permission = self.ACTION["update"]
            if not self.db(self.table.id == id).count():
                self.id = 0
                self.method = permission = self.ACTION["create"]
            else:
                if self.UID in self.record:
                    del self.record[self.UID]

        if permit and not \
           permit(permission, self.tablename, record_id=self.id):
            self.permitted=False

        if self.prefix == "auth" or \
           self.prefix == "admin" or \
           self.prefix == "s3":
            self.permitted=False


    def commit(self):

        """ Commits the vector to the database """

        if not self.committed:
            if self.accepted and self.permitted:
                form = Storage() # PseudoForm for callbacks
                form.method = self.method
                form.vars = self.record
                form.vars.id = self.id
                if self.onvalidation:
                    self.onvalidation(form)
                if form.errors:
                    if self.element:
                        #TODO: propagate errors to element
                        pass
                    return False
                if self.sync:
                    self.sync(self)
                if self.log:
                    self.log(self)
                if self.method == self.ACTION["update"]:
                    try:
                        self.record.update(deleted=False) # Undelete re-imported records!
                        success = self.db(self.table.id == self.id).update(
                                    **dict(self.record))
                        if self.components:
                            db_record = self.db(self.table.id == self.id).select(
                                            self.table.ALL)[0]
                    except:
                        return False
                    if success:
                        self.committed = True
                elif self.method == self.ACTION["create"]:
                    try:
                        success = self.table.insert(**dict(self.record))
                        if self.components:
                            db_record = self.db(self.table.id == success).select(
                                            self.table.ALL)[0]
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


class S3XML(object):

    """ XML toolkit for S3 """

    S3XRC_NAMESPACE = "http://eden.sahanafoundation.org/wiki/S3XRC"
    S3XRC = "{%s}" % S3XRC_NAMESPACE #: LXML namespace prefix
    NSMAP = {None: S3XRC_NAMESPACE} #: LXML default namespace

    UID = "uuid"
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

    PY2XML = [("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"),
              ('"', "&quot;"), ("'", "&apos;")]

    XML2PY = [("<", "&lt;"), (">", "&gt;"), ('"', "&quot;"),
              ("'", "&apos;"), ("&", "&amp;")]


    def __init__(self, db, domain=None, base_url=None, gis=None):

        """ Constructor """

        self.db = db
        self.error = None
        self.domain = domain
        self.base_url = base_url
        self.domain_mapping = True
        self.gis = gis


    def parse(self, source):

        """ Parse an XML source into an element tree """

        self.error = None

        try:
            parser = etree.XMLParser(no_network=False)
            result = etree.parse(source, parser)
            return result
        except:
            self.error = S3XRC_PARSE_ERROR
            return None


    def transform(self, tree, template_path, **args):

        """ Transform an element tree with XSLT """

        self.error = None

        if args:
            _args = [(k, "'%s'" % args[k]) for k in args.keys()]
            _args = dict(_args)
        else:
            _args = None
        ac = etree.XSLTAccessControl(read_file=True, read_network=True)
        template = self.parse(template_path)

        if template:
            try:
                transformer = etree.XSLT(template, access_control=ac)
                if _args:
                    result = transformer(tree, **_args)
                else:
                    result = transformer(tree)
                return result
            except:
                self.error = S3XRC_TRANSFORMATION_ERROR
                return None
        else:
            # Error parsing the XSL template
            return None


    def tostring(self, tree, pretty_print=False):

        """ Convert an element tree into XML as string """

        return etree.tostring(tree,
                                xml_declaration=True,
                                encoding="utf-8",
                                pretty_print=pretty_print)


    def json_message(self, success=True, status_code="200", message=None, tree=None):

        """
            Provide a nicely-formatted JSON Message.

            @param success: whether the request was successful
            @type success: boolean
            @param status_code: the HTTP status code
            @type status_code: string
            @param message: the message to send
            @type message: string
            @param tree: the element tree of the request in JSON
                         containing error annotations
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


    def xml_encode(self, obj):

        """ Encodes a Python string into an XML text node """

        if obj:
            for (x,y) in self.PY2XML:
                obj = obj.replace(x, y)
        return obj


    def xml_decode(self, obj):

        """ Decodes an XML text node into a Python string """

        if obj:
            for (x,y) in self.XML2PY:
                obj = obj.replace(y, x)
        return obj


    def export_uid(self, uid):

        """ Maps internal UUIDs to export format """

        if not self.domain:
            return uid
        x = uid.find("/")
        if x < 1 or x == len(uid)-1:
            return "%s/%s" % (self.domain, uid)
        else:
            return uid


    def import_uid(self, uid):

        """ Maps imported UUIDs to internal format """

        if not self.domain:
            return uid
        x = uid.find("/")
        if x < 1 or x == len(uid)-1:
            return uid
        else:
            (_domain, _uid) = uid.split("/", 1)
            if _domain == self.domain:
                return _uid
            else:
                return uid


    def rmap_old(self, element):

        """ Resolves references in an element (export) """

        reference_map = []

        references = element.xpath("./%s" % self.TAG["reference"])
        for r in references:
            id = r.get("id", None)
            field = r.get(self.ATTRIBUTE["field"], None)
            ktablename = r.get(self.ATTRIBUTE["resource"], None)
            ktable = self.db[ktablename]

            if id:
                if self.UID in ktable.fields:
                    query = (ktable.id == id)
                    if "deleted" in ktable:
                        query = (ktable.deleted == False) & query
                    krecord = self.db(query).select(ktable[self.UID], limitby=(0, 1))
                    if krecord:
                        uid = krecord[0][self.UID]
                        if self.domain_mapping:
                            uid = self.export_uid(uid)
                        r.set(self.UID, self.xml_encode(uid))
                        del r.attrib["id"]
                    else:
                        element.remove(r)
                        continue
                else:
                    query = (ktable.id == id)
                    if "deleted" in ktable:
                        query = (ktable.deleted == False) & query
                    if not self.db(query).count():
                        element.remove(r)
                        continue
            else:
                element.remove(r)
                continue

            reference_map.append(dict(field = field,
                                      table = ktablename,
                                      id = id,
                                      uid = uid,
                                      element = r))

        return reference_map


    def rmap(self, table, record, skip=[]):

        reference_map = []

        fields = filter(lambda f: \
                        f not in skip and \
                        f not in self.IGNORE_FIELDS and \
                        f not in self.FIELDS_TO_ATTRIBUTES and \
                        str(table[f].type).startswith("reference") and \
                        f in record.keys(),
                        table.fields)

        for f in fields:

            id = record.get(f, None)
            uid = None

            ktablename = str(table[f].type)[10:]
            ktable = self.db[ktablename]

            if self.UID in ktable.fields:
                query = (ktable.id == id)
                if "deleted" in ktable:
                    query = (ktable.deleted == False) & query
                krecord = self.db(query).select(ktable[self.UID], limitby=(0, 1))
                if krecord:
                    uid = krecord[0][self.UID]
                    if self.domain_mapping:
                        uid = self.export_uid(uid)
                else:
                    continue
            else:
                query = (ktable.id == id)
                if "deleted" in ktable:
                    query = (ktable.deleted == False) & query
                if not self.db(query).count():
                    continue

            value = record[f]
            value = text = self.xml_encode(str(table[f].formatter(value)).decode("utf-8"))
            if table[f].represent:
                text = str(table[f].represent(value)).decode("utf-8")
                # Filter out markup from text
                try:
                    markup = etree.XML(text)
                    text = markup.xpath(".//text()")
                    if text:
                        text = " ".join(text)
                except etree.XMLSyntaxError:
                    pass
                text = self.xml_encode(text)

            reference_map.append(Storage(field=f, table=ktablename, id=id, uid=uid, text=text, value=value))

        return reference_map


    def add_references(self, element, rmap):

        for r in rmap:
            reference = etree.SubElement(element, self.TAG["reference"])
            reference.set(self.ATTRIBUTE["field"], r.field)
            reference.set(self.ATTRIBUTE["resource"], r.table)
            if r.uid:
                reference.set(self.UID, r.uid )
                reference.text = r.text
            else:
                reference.set(self.ATTRIBUTE["value"], r.text)
            r.element=reference


    def gis_encode(self, rmap, download_url="", marker=None):

        for r in rmap:
            if r.element is None:
                continue
            ktable = self.db[r.table]
            if self.Lat in ktable.fields and self.Lon in ktable.fields:
                LatLon = self.db(ktable.id == r.id).select(ktable[self.Lat], ktable[self.Lon], limitby=(0, 1))
                if LatLon:
                    LatLon = LatLon[0]
                    if LatLon[self.Lat] and LatLon[self.Lon]:
                        r.element.set(self.ATTRIBUTE["lat"], self.xml_encode("%.6f" % LatLon[self.Lat]))
                        r.element.set(self.ATTRIBUTE["lon"], self.xml_encode("%.6f" % LatLon[self.Lon]))
                        if self.gis:
                            if marker:
                                marker_url = "%s/gis_marker.image.%s.png" % (download_url, marker)
                            else:
                                marker = self.gis.get_marker(r.value)
                                marker_url = "%s/%s" % (download_url, marker)
                            r.element.set(self.ATTRIBUTE["marker"], self.xml_encode(marker_url))


    def element(self, table, record, skip=[],
                url=None, download_url=None, marker=None):

        """ Creates an element from a Storage() record """

        if not download_url:
            download_url = ""

        resource= etree.Element(self.TAG["resource"])
        resource.set(self.ATTRIBUTE["name"], table._tablename)

        if self.UID in table.fields and self.UID in record:
            _value = str(table[self.UID].formatter(record[self.UID]))
            if self.domain_mapping:
                value = self.export_uid(_value)
            resource.set(self.UID, self.xml_encode(value))
            #if table._tablename == "gis_location":
                ## Look up the marker to display
                #if self.gis:
                    #marker = self.gis.get_marker(_value)
                    #marker_url = "%s/%s" % (download_url, marker)
                    #resource.set(self.ATTRIBUTE["marker"],
                                 #self.xml_encode(marker_url))

        readable = filter( lambda key: \
                        key not in self.IGNORE_FIELDS and \
                        key not in skip and \
                        record[key] is not None and \
                        key in table.fields and \
                        not(key == self.UID),
                        record.keys())

        for i in xrange(0, len(readable)):
            f = readable[i]
            v = record[f]
            text = value = self.xml_encode(str(table[f].formatter(v)).decode("utf-8"))

            if table[f].represent:
                text = str(table[f].represent(v)).decode("utf-8")
                # Filter out markup from text
                try:
                    markup = etree.XML(text)
                    text = markup.xpath(".//text()")
                    if text:
                        text = " ".join(text)
                except etree.XMLSyntaxError:
                    pass
                text = self.xml_encode(text)

            fieldtype = str(table[f].type)

            if f in self.FIELDS_TO_ATTRIBUTES:
                resource.set(f, text)

            elif fieldtype.startswith("reference"):
                continue
                #ktable = fieldtype[10:]
                #reference = etree.SubElement(resource, self.TAG["reference"])
                #reference.set(self.ATTRIBUTE["field"], f)
                #reference.set(self.ATTRIBUTE["resource"], ktable)
                #reference.set("id", value )
                #reference.text = text

            elif fieldtype == "upload":
                data = etree.SubElement(resource, self.TAG["data"])
                data.set(self.ATTRIBUTE["field"], f)
                data.text = "%s/%s" % (download_url, value)

            elif fieldtype == "password":
                # Do not export password fields
                continue

            elif fieldtype == "blob":
                # Not implemented yet
                continue

            else:
                data = etree.SubElement(resource, self.TAG["data"])
                data.set(self.ATTRIBUTE["field"], f)
                if table[f].represent:
                    data.set(self.ATTRIBUTE["value"], value )
                data.text = text

        if url:
            resource.set(self.ATTRIBUTE["url"], url)

        return resource


    def tree(self, resources, domain=None, url=None,
             start=None, limit=None, results=None):

        """ Builds a tree from a list of elements """

        # For now we do not nsmap, because the default namespace cannot be
        # matched in XSLT templates (need explicit prefix) and thus this
        # would require a rework of all existing templates (which is however useful)
        root = etree.Element(self.TAG["root"]) #, nsmap=self.NSMAP)

        root.set(self.ATTRIBUTE["success"], str(False))

        if resources is not None:
            if resources:
                root.set(self.ATTRIBUTE["success"], str(True))
            if start is not None:
                root.set(self.ATTRIBUTE["start"], str(start))
            if limit is not None:
                root.set(self.ATTRIBUTE["limit"], str(limit))
            if results is not None:
                root.set(self.ATTRIBUTE["results"], str(results))
            root.extend(resources)

        if domain:
            root.set(self.ATTRIBUTE["domain"], self.domain)

        if url:
            root.set(self.ATTRIBUTE["url"], self.base_url)

        root.set(self.ATTRIBUTE["latmin"], str(self.gis.get_bounds()["min_lat"]))
        root.set(self.ATTRIBUTE["latmax"], str(self.gis.get_bounds()["max_lat"]))
        root.set(self.ATTRIBUTE["lonmin"], str(self.gis.get_bounds()["min_lon"]))
        root.set(self.ATTRIBUTE["lonmax"], str(self.gis.get_bounds()["max_lon"]))

        return etree.ElementTree(root)


    def get_field_options(self, table, fieldname):

        """ Reads all options for a field """

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
            if isinstance(r, IS_NULL_OR) and hasattr(r.other, "options"):
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


    def get_options(self, prefix, name, joins=[]):

        """ Gets all field options for a resource """

        resource = "%s_%s" % (prefix, name)

        options = etree.Element(self.TAG["options"])
        options.set(self.ATTRIBUTE["resource"], resource)

        if resource in self.db:
            table = self.db[resource]
            for f in table.fields:
                select = self.get_field_options(table, f)
                if select is not None:
                    options.append(select)
            for j in joins:
                component = j[0]
                coptions = etree.Element(self.TAG["options"])
                coptions.set(self.ATTRIBUTE["resource"], component.tablename)
                for f in component.table.fields:
                    select = self.get_field_options(component.table, f)
                    if select is not None:
                        coptions.append(select)
                options.append(coptions)

        return options


    def validate(self, table, record, fieldname, value):

        """ Validates a single value """

        requires = table[fieldname].requires

        if not requires:
            return (value, None)
        else:
            if record:
                v = record.get(fieldname, None)
                if v:
                    if v == value:
                        return (value, None)
            if not isinstance(requires, (list, tuple)):
                requires = [requires]
            for validator in requires:
                (value, error) = validator(value)
                if error:
                    return (value, error)
            return(value, None)


    def record(self, table, element, skip=[]):

        """ Creates a Storage() record from an element and validates it """

        valid = True
        record = Storage()
        original = None
        if self.UID in table.fields and self.UID not in skip:
            uid = element.get(self.UID, None)
            if uid:
                if self.domain_mapping:
                    record[self.UID] = self.import_uid(uid)
                else:
                    record[self.UID] = uid
                original = self.db(table[self.UID] == uid).select(table.ALL,
                                                              limitby=(0,1))
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
                        element.set(self.ATTRIBUTE["error"],
                                    "%s: %s" % (f, error))
                        valid = False
                        continue
                    else:
                        record[f]=value

        for child in element:
            if child.tag == self.TAG["data"]:
                f = child.get(self.ATTRIBUTE["field"], None)
                if not f or f not in table.fields:
                    continue
                if f in self.IGNORE_FIELDS or f in skip:
                    continue

                field_type = str(table[f].type)

                if field_type == "id":
                    continue
                elif field_type.startswith("reference"):
                    continue
                elif field_type in ("upload", "blob", "password"):
                    continue

                value = self.xml_decode(child.get(self.ATTRIBUTE["value"], None))
                if value is None:
                    value = self.xml_decode(child.text)

                if value == "" and not field_type == "string":
                    value = None

                if field_type == 'boolean':
                    if value and value in ["True", "true"]:
                        value = True
                    else:
                        value = False
                elif value is not None:
                    if field_type == "integer":
                        try:
                            value = int(value)
                        except ValueError:
                            #TODO: propagate error to element?
                            continue
                    elif field_type == "double":
                        try:
                            value = float(value)
                        except ValueError:
                            #TODO: propagate error to element?
                            continue
                else:
                    value = table[f].default

                if value is None and field_type == "string":
                    value = ""

                if value is not None:
                    if not isinstance(value, basestring):
                        v = str(value)
                    (value, error) = self.validate(table, original, f, v)
                    child.set(self.ATTRIBUTE["value"], v)
                    if error:
                        child.set(self.ATTRIBUTE["error"], "%s: %s" % (f, error))
                        valid = False
                        continue
                    else:
                        record[f] = value

            elif child.tag == self.TAG["reference"]:
                f = child.get(self.ATTRIBUTE["field"], None)
                if not f or f not in table.fields:
                    continue
                if f in self.IGNORE_FIELDS or f in skip:
                    continue
                ktablename =  child.get(self.ATTRIBUTE["resource"], None)
                uid = child.get(self.UID, None)
                if uid and self.domain_mapping:
                    uid = self.import_uid(uid)
                if not (ktablename and uid):
                    continue
                if ktablename in self.db and self.UID in self.db[ktablename]:
                    ktable = self.db[ktablename]
                    krecord = self.db(ktable[self.UID] == uid).select(ktable.id,
                                                                  limitby=(0,1))
                    if krecord:
                        record[f] = krecord[0].id
                else:
                    continue

        if valid:
            return record
        else:
            return None


    def select_resources(self, tree, tablename):

        """ Selects resources from an element tree """

        resources = []

        if not tree:
            return resources

        if isinstance(tree, ElementTree):
            root = tree.getroot()
            if not root.tag == self.TAG["root"]:
                return resources
        else:
            root = tree

        expr = './%s[@%s="%s"]' % \
               (self.TAG["resource"], self.ATTRIBUTE["name"], tablename)
        resources = root.xpath(expr)

        return resources


    def __json2element(self, key, value, native=False):

        """ Converts JSON objects into elements """

        if isinstance(value, dict):
            return self.__obj2element(key, value, native=native)

        elif isinstance(value, (list, tuple)):
            if not key == self.TAG["item"]:
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


    def __obj2element(self, tag, obj, native=False):

        """ Converts a JSON object into an element """

        prefix = name = resource = field = None

        if not tag:
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
            elif not tag == self.TAG["root"]:
                field = tag
                tag = self.TAG["data"]

        element = etree.Element(tag)

        if native:
            if resource:
                if tag == self.TAG["resource"]:
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


    def json2tree(self, source, format=None):

        """ Converts JSON into an element tree """

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
            if root:
                return etree.ElementTree(root)

        return None


    def __element2json(self, element, native=False):

        """ Converts an element into JSON """

        if element.tag == self.TAG["list"]:
            obj = []
            for child in element:
                tag = child.tag
                if tag[0] == "{":
                    tag = tag.rsplit("}",1)[1]
                child_obj = self.__element2json(child, native=native)
                if child_obj:
                    obj.append(child_obj)
            return obj

        else:
            obj = {}
            for child in element:
                tag = child.tag
                if tag[0] == "{":
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
                        tag = "%s_%s" % (self.PREFIX["reference"],
                                         child.get(self.ATTRIBUTE["field"]))
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
                    if a == self.ATTRIBUTE["name"] and \
                       element.tag == self.TAG["resource"]:
                        continue
                    if a == self.ATTRIBUTE["resource"] and \
                       element.tag == self.TAG["options"]:
                        continue
                    if a == self.ATTRIBUTE["field"] and \
                    element.tag in (self.TAG["data"], self.TAG["reference"]):
                        continue
                obj[self.PREFIX["attribute"] + a] = self.xml_decode(attributes[a])

            if element.text:
                obj[self.PREFIX["text"]] = self.xml_decode(element.text)

            if len(obj) == 1 and obj.keys()[0] in \
               (self.PREFIX["text"], self.TAG["item"], self.TAG["list"]):
                obj = obj[obj.keys()[0]]

            return obj


    def tree2json(self, tree, pretty_print=False):

        """ Converts an element tree into JSON """

        root = tree.getroot()

        if root.tag == self.TAG["root"]:
            native = True
        else:
            native = False

        root_dict = self.__element2json(root, native=native)

        if pretty_print:
            js = json.dumps(root_dict, indent=4)
            return "\n".join([l.rstrip() for l in js.splitlines()])
        else:
            return json.dumps(root_dict)
