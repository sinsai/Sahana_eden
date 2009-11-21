# -*- coding: utf-8 -*-

"""
    SahanaPy XML+JSON Interface

    @version: 1.3.2-3, 2009-11-21
    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

    @author: nursix
    @copyright: (c) 2009 Dominic König (nursix.org)
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

import sys, uuid
import gluon.contrib.simplejson as json

from gluon.storage import Storage
from gluon.html import URL
from gluon.validators import IS_NULL_OR

#******************************************************************************
# Errors
#
S3XML_BAD_RESOURCE = "Invalid Resource"
S3XML_PARSE_ERROR = "XML Parse Error"
S3XML_TRANFORMATION_ERROR = "XSL Transformation Error"
S3XML_NO_LXML = "lxml not installed"
S3XML_BAD_SOURCE = "Invalid XML Source"
S3XML_BAD_RECORD = "Invalid Record ID"
S3XML_NO_MATCH = "No Matching Element"
S3XML_VALIDATION_ERROR = "Validation Error"
S3XML_DATA_IMPORT_ERROR = "Data Import Error"

S3XRC_NOT_IMPLEMENTED = "Not Implemented"

#******************************************************************************
# lxml
#
NO_LXML=True
try:
    from lxml import etree
    NO_LXML=False
except ImportError:
    try:
        import xml.etree.cElementTree as etree
        print >> sys.stderr, "WARNING: %s: lxml not installed - using cElementTree" % __name__
    except ImportError:
        try:
            import xml.etree.ElementTree as etree
            print >> sys.stderr, "WARNING: %s: lxml not installed - using ElementTree" % __name__
        except ImportError:
            try:
                import cElementTree as etree
                print >> sys.stderr, "WARNING: %s: lxml not installed - using cElementTree" % __name__
            except ImportError:
                # normal ElementTree install
                import elementtree.ElementTree as etree
                print >> sys.stderr, "WARNING: %s: lxml not installed - using ElementTree" % __name__

# *****************************************************************************
# ObjectComponent
#
class ObjectComponent(object):

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

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    def set_attr(self, name, value):

        self.attr[name] = value

    # -------------------------------------------------------------------------
    def get_attr(self, name):

        if name in self.attr:
            return self.attr[name]
        else:
            return None

# *****************************************************************************
# ObjectModel
#
class ObjectModel(object):

    def __init__(self, db):

        self.db = db

        self.components = {}

        self.methods = {}
        self.cmethods = {}

    # -------------------------------------------------------------------------
    def add_component(self, prefix, name, **attr):

        assert "joinby" in attr, "Join key(s) must be defined."

        component = ObjectComponent(self.db, prefix, name, **attr)
        self.components[name] = component
        return component

    # -------------------------------------------------------------------------
    def get_component(self, prefix, name, component_name):

        if component_name in self.components:

            component = self.components[component_name]

            pkey, fkey = component.get_join_keys(prefix, name)
            if pkey is not None:
                return (component, pkey, fkey)

        return (None, None, None)

    # -------------------------------------------------------------------------
    def get_components(self, prefix, name):

        component_list = []

        for component_name in self.components:

            component, pkey, fkey = self.get_component(prefix, name, component_name)
            if component is not None:
                component_list.append((component, pkey, fkey))

        return component_list

    # -------------------------------------------------------------------------
    def set_method(self, prefix, name, component_name=None, method=None, action=None):

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

    # -------------------------------------------------------------------------
    def get_method(self, prefix, name, component_name=None, method=None):

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

    # -------------------------------------------------------------------------
    def set_attr(self, component_name, name, value):

        return self.components[component_name].set_attr(name, value)

    # -------------------------------------------------------------------------
    def get_attr(self, component_name, name):

        return self.components[component_name].get_attr(name)

    # -------------------------------------------------------------------------
    def uuid2id(table, uuid):

        if uuid in table:
            if not isinstance(uuid, (list, tuple)):
                uuid = [uuid]

            rs = self.db(table.uuid.belongs(uuid)).select(table.id, table.uuid)

            result = [(r.id, r.uuid) for r in rs]
            return result
        else:
            return []

    # -------------------------------------------------------------------------
    def id2uuid(table, id):

        if uuid in table:
            if not isinstance(id, (list, tuple)):
                id = [id]

            rs = self.db(table.id.belongs(id)).select(table.id, table.uuid)

            result = [(r.id, r.uuid) for r in rs]
            return result
        else:
            return []

# *****************************************************************************
# ResourceController
#
class ResourceController(object):

    RCVARS = "rcvars"

    ACTION = dict(
        create="create",
        read="read",
        update="update",
        delete="delete"
    )

    def __init__(self, db, domain=None, base_url=None):

        assert db is not None, "Database must not be None."
        self.db = db

        self.error = None

        self.domain = domain
        self.base_url = base_url

        self.model = ObjectModel(self.db)
        self.xml = S3XML(self.db, domain=domain, base_url=base_url)

    # -------------------------------------------------------------------------
    def get_session(self, session, prefix, name):

        tablename = "%s_%s" % (prefix, name)

        if self.RCVARS in session and tablename in session[self.RCVARS]:
            return session[self.RCVARS][tablename]

    # -------------------------------------------------------------------------
    def store_session(self, session, prefix, name, id):

        if self.RCVARS not in session:
            session[self.RCVARS] = Storage()

        if self.RCVARS in session:
            tablename = "%s_%s" % (prefix, name)
            session[self.RCVARS][tablename] = id

        return True # always return True to make this chainable

    # -------------------------------------------------------------------------
    def clear_session(self, session, prefix=None, name=None):

        if prefix and name:
            tablename = "%s_%s" % (prefix, name)
            if self.RCVARS in session and tablename in session[self.RCVARS]:
                del session[self.RCVARS][tablename]
        else:
            if self.RCVARS in session:
                del session[self.RCVARS]

        return True # always return True to make this chainable

    # -------------------------------------------------------------------------
    def request(self, prefix, name, request, session=None):

        self.error = None
        return XRequest(self, prefix, name, request, session=session)

    # -------------------------------------------------------------------------
    def export_xml(self, prefix, name, id, joins=[], skip=[], permit=None, audit=None):

        self.error = None
        resources = []

        _table = "%s_%s" % (prefix, name)

        if _table not in self.db or (permit and not permit(self.ACTION["read"], _table)):
            return self.xml.root(resources, domain=self.domain, url=self.base_url)

        table = self.db[_table]

        if id and isinstance(id, (list, tuple)):
            query = (table.id.belongs(id))
        elif id:
            query = (table.id==id)
        else:
            query = (table.id>0)

        if "deleted" in table:
            query = (table.deleted==False) & query

        if self.base_url:
            url = "%s/%s/%s" % (self.base_url, prefix, name)
        else:
            url = "/%s/%s" % (prefix, name)

        try:
            records = self.db(query).select(table.ALL) or []
        except:
            return None

        if records and permit is not None:
            records = filter(lambda r: permit(self.ACTION["read"], _table, record_id=r.id), records)

        if joins and permit is not None:
            joins = filter(lambda j: permit(self.ACTION["read"], j[0].tablename), joins)

        cdata = {}
        for i in xrange(0,len(joins)):
            (c, pkey, fkey) = joins[i]
            pkeys = map(lambda r: r[pkey], records)

            # TODO: Modify this section for use on GAE:
            cquery = (c.table[fkey].belongs(pkeys))
            if "deleted" in c.table:
                cquery = (c.table.deleted==False) & cquery
            cdata[c.tablename] = self.db(cquery).select(c.table.ALL) or []

        for i in xrange(0, len(records)):
            record = records[i]

            if audit is not None:
                audit(self.ACTION["read"], prefix, name, record=record.id, representation="xml")

            resource_url = "%s/%s" % (url, record.id)
            resource = self.xml.element(table, record, skip=skip, url=resource_url)

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

                    if permit and not permit(self.ACTION["read"], c.tablename, crecord.id):
                        continue
                    if audit is not None:
                        audit(self.ACTION["read"], c.prefix, c.name, record=crecord.id, representation="xml")

                    resource_url = "%s/%s/%s/%s" % (url, record.id, c.name, crecord.id)
                    cresource = self.xml.element(c.table, crecord, skip=_skip, url=resource_url)
                    resource.append(cresource)

            resources.append(resource)

        return self.xml.tree(resources, domain=self.domain, url=self.base_url)

    # -------------------------------------------------------------------------
    def import_xml(self, prefix, name, id, tree, joins=[], join=False,
                   permit=None,
                   audit=None,
                   onvalidation=None,
                   onaccept=None):

        self.error = None

        self.error = S3XRC_NOT_IMPLEMENTED
        return None

    # -------------------------------------------------------------------------
    def options_xml(self, prefix, name, joins=[]):

        self.error = None
        options = self.xml.get_options(prefix, name, joins=joins)

        return self.xml.tree([options], domain=self.domain, url=self.base_url)

        #self.error = S3XRC_NOT_IMPLEMENTED
        #return None

# *****************************************************************************
# XRequest
#
class XRequest(object):

    DEFAULT_REPRESENTATION = "html"

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
            if len(self.args)>0 or len(self.args)==0 and ('id_label' in self.request.vars):
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

    # -------------------------------------------------------------------------
    def __parse(self):

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
        if 'format' in self.request.vars:
            self.representation = str.lower(self.request.vars.format)

        # Representation fallback
        if not self.representation:
            self.representation = self.DEFAULT_REPRESENTATION

        return True

    # -------------------------------------------------------------------------
    def __record(self):

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

        # Check for ?id_label=
        if not self.id and 'id_label' in self.request.vars:
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

    # -------------------------------------------------------------------------
    def here(self, representation=None):
        """
            Backlink producing the same request
        """

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

    # -------------------------------------------------------------------------
    def other(self, method=None, record_id=None, representation=None):
        """
            Backlink to another method+record_id of the same resource
        """

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

    # -------------------------------------------------------------------------
    def there(self, representation=None):
        """
            Backlink producing a HTTP/list request to the same resource
        """
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

    # -------------------------------------------------------------------------
    def same(self, representation=None):
        """
            Backlink producing the same request with neutralized primary record ID
        """

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

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    def export_xml(self, permit=None, audit=None, template=None):

        if self.component:
            joins = [(self.component, self.pkey, self.fkey)]
        else:
            joins = self.rc.model.get_components(self.prefix, self.name)

        output = tree = self.rc.export_xml(self.prefix, self.name, self.id,
                                         joins=joins, permit=permit, audit=audit)

        if template is not None:
            output = self.rc.xml.transform(tree, template)
            if not output:
                if self.representation=="xml":
                    output = tree
                else:
                    self.error = self.rc.error
                    return None

        return self.rc.xml.tostring(output)

    # -------------------------------------------------------------------------
    def export_json(self, permit=None, audit=None):

        if self.component:
            joins = [(self.component, self.pkey, self.fkey)]
        else:
            joins = self.rc.model.get_components(self.prefix, self.name)

        tree = self.rc.export_xml(self.prefix, self.name, self.id,
                               joins=joins, permit=permit, audit=audit)

        return self.rc.xml.tree2json(tree)

    # -------------------------------------------------------------------------
    def import_xml(self):
        return None
    # -------------------------------------------------------------------------
    def import_json(self):
        return None
    # -------------------------------------------------------------------------
    def options_xml(self):

        if self.component:
            joins = [(self.component, self.pkey, self.fkey)]
        else:
            joins = self.rc.model.get_components(self.prefix, self.name)

        tree = self.rc.options_xml(self.prefix, self.name, joins=joins)
        return self.rc.xml.tostring(tree)

    # -------------------------------------------------------------------------
    def options_json(self):

        if self.component:
            joins = [(self.component, self.pkey, self.fkey)]
        else:
            joins = self.rc.model.get_components(self.prefix, self.name)

        tree = self.rc.options_xml(self.prefix, self.name, joins=joins)
        return self.rc.xml.tree2json(tree)

# *****************************************************************************
# S3XML
#
class S3XML(object):

    # *************************************************************************
    # Configuration

    UUID = "uuid"

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
        root="sahanapy",
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
        error="error"
        )

    ACTION = dict(
        create="create",
        read="read",
        update="update",
        delete="delete"
    )

    PREFIX = dict(
        resource="$",
        reference="$k",
        attribute="@",
        text="$"
    )

    PY2XML = [('&', '&amp;'), ('<', '&lt;'), ('>', '&gt;'), ('"', '&quot;'), ("'", '&apos;')]
    XML2PY = [('<', '&lt;'), ('>', '&gt;'), ('"', '&quot;'), ("'", '&apos;'), ('&', '&amp;')]

    # *************************************************************************
    # Constructor

    def __init__(self, db, domain=None, base_url=None):

        self.db = db
        self.error = None

        self.domain = domain
        self.base_url = base_url

    # *************************************************************************
    # XML Helpers

    # -------------------------------------------------------------------------
    def parse(self, source):

        self.error = None

        try:
            parser = etree.XMLParser(no_network=False)
            result = etree.parse(source, parser)
            return result
        except:
            self.error = S3XML_PARSE_ERROR
            return None

    # -------------------------------------------------------------------------
    def transform(self, tree, template_path):

        self.error = None

        if not NO_LXML:
            template = self.parse(template_path)
            if template:
                try:
                    transformer = etree.XSLT(template)
                    result = transformer(tree)
                    return result
                except:
                    self.error = S3XML_TRANFORMATION_ERROR
                    return None
            else:
                # Error parsing the XSL template
                return None
        else:
            self.error = S3XML_NO_LXML
            return None

    # -------------------------------------------------------------------------
    def tostring(self, tree):

        if NO_LXML:
            return etree.tostring(tree.getroot(), encoding="utf-8")
        else:
            return etree.tostring(tree,
                                  xml_declaration=True,
                                  encoding="utf-8",
                                  pretty_print=True)

    # -------------------------------------------------------------------------
    def xml_encode(self, obj):

        if obj:
            for (x,y) in self.PY2XML:
                obj = obj.replace(x, y)
        return obj

    # -------------------------------------------------------------------------
    def xml_decode(self, obj):

        if obj:
            for (x,y) in self.XML2PY:
                obj = obj.replace(y, x)
        return obj

    # *************************************************************************
    # DB->ElementTree

    # -------------------------------------------------------------------------
    def element(self, table, record, skip=[], url=None):

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

        for i in range(0, len(readable)):

            f = readable[i]
            v = record[f]

            text = value = self.xml_encode(str(table[f].formatter(v)).decode('utf-8'))
            if table[f].represent:
                text = self.xml_encode(str(table[f].represent(v)).decode('utf-8'))

            if f in self.FIELDS_TO_ATTRIBUTES:
                resource.set(f, text)

            elif isinstance(table[f].type, str) and \
                table[f].type[:9]=="reference":

                _ktable = table[f].type[10:]
                ktable = self.db[_ktable]

                if self.UUID in ktable.fields:
                    uuid = self.db(ktable.id==value).select(ktable[self.UUID], limitby=(0,1))
                    if uuid:
                        uuid = uuid[0].uuid
                        reference = etree.SubElement(resource, self.TAG["reference"])
                        reference.set(self.ATTRIBUTE["field"], f)
                        reference.set(self.ATTRIBUTE["resource"], _ktable)
                        reference.set(self.UUID, self.xml_encode(str(uuid)))
                        reference.text = text
            else:
                data = etree.SubElement(resource, self.TAG["data"])
                data.set(self.ATTRIBUTE["field"], f)
                if table[f].represent:
                    data.set(self.ATTRIBUTE["value"], value )
                data.text = text

        if url is not None:
            resource.set(self.ATTRIBUTE["url"], url)

        return resource

    # -------------------------------------------------------------------------
    def tree(self, resources, domain=None, url=None):

        root = etree.Element(self.TAG["root"])

        if resources is not None:
            if NO_LXML:
                for r in resources:
                    root.append(r)
            else:
                root.extend(resources)

        if domain is not None:
            root.set(self.ATTRIBUTE["domain"], self.domain)

        if url is not None:
            root.set(self.ATTRIBUTE["url"], self.base_url)

        return etree.ElementTree(root)

    # *************************************************************************
    # Field Options

    # -------------------------------------------------------------------------
    def get_field_options(self, table, fieldname):

        field = table[fieldname]
        requires = field.requires

        if not isinstance(requires, (list, tuple)):
            requires = [requires]

        select = etree.Element(self.TAG["select"])
        select.set(self.TAG["field"], fieldname)

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

    # -------------------------------------------------------------------------
    def get_options(self, prefix, name, joins=[]):

        resource = "%s_%s" % (prefix, name)

        options = etree.Element(self.TAG["options"])
        options.set(self.ATTRIBUTE["resource"], resource)

        if resource in self.db:
            table = self.db[resource]

            for f in table.fields:
                select = self.get_field_options(table, f)
                if select:
                    options.append(select)

            for j in joins:
                component = j[0]
                print "Joined Component: %s" % component.tablename
                coptions = etree.Element(self.TAG["options"])
                coptions.set(self.ATTRIBUTE["resource"], component.tablename)
                for f in component.table.fields:
                    select = self.get_field_options(component.table, f)
                    if select:
                        coptions.append(select)
                options.append(coptions)

        return options

    # *************************************************************************
    # Validation

    # -------------------------------------------------------------------------
    def validate(self, table, record, fieldname, value):

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

    # *************************************************************************
    # ElementTree->DB

    # -------------------------------------------------------------------------
    def record(self, table, element, skip=[]):

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

        for f in self.ATTRIBUTES_TO_FIELDS:
            if f in self.IGNORE_FIELDS or f in skip:
                continue
            if f in table.fields:
                value = self.xml_decode(element.get(f, None))
                if value is not None:
                    (value, error) = self.validate(table, original, f, value)
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

                if value is not None:
                    (value, error) = self.validate(table, original, f, value)
                    if error:
                        child.set(self.ATTRIBUTE["error"], "%s: %s" % (f, error))
                        valid = False
                        continue
                    else:
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

    # -------------------------------------------------------------------------
    def commit(self):

        for r in self.imports:
            r.commit()
        self.imports = []
        return

    # -------------------------------------------------------------------------
    def select_resources(self, tree, tablename):

        resources = []

        if not element:
            return resources

        if isinstance(etree, etree.ElementTree):
            root = element.getroot()
            if not root.tag==self.TAG["root"]:
                return resources
        else:
            root = tree

        expr = './%s[@%s="%s"]' % \
               (self.TAG["resource"], self.ATTRIBUTE["name"], tablename)

        resources = root.xpath(expr)
        return resources

    # -------------------------------------------------------------------------
    # TODO: This to be moved into ResourceController!
    def put(self, prefix, name, id, tree, joins=[], jrequest=False,
            permit=None,
            audit=None,
            onvalidation=None,
            onaccept=None):

        self.error = None

        if NO_LXML:
            self.error = S3XML_NO_LXML
            return False

        self.imports = []

        tablename = "%s_%s" % (prefix, name)
        if tablename in self.db:
            table = self.db[tablename]
        else:
            self.error = S3XML_BAD_RESOURCE
            return False

        elements = self.select_resources(tree, tablename)
        if not elements: # nothing to import
            return True

        if id:
            try:
                db_record = self.db(table.id==id).select(table.ALL)[0]
            except:
                self.error = S3XML_BAD_RECORD
                return False
        else:
            db_record = None

        if id and len(elements)>1:
            # ID given, but multiple elements of that type
            # => try to find UUID match
            if self.UUID in table:
                uuid = db_record[self.UUID]
                for element in elements:
                    if element.get(self.UUID)==uuid:
                        elements = [element]
                        break

            if len(elements)>1:
                # Error: multiple input elements, but only one target record
                self.error = S3XML_NO_MATCH
                return False

        if joins is None:
            joins = []

        for i in xrange(0, len(elements)):
            element = elements[i]

            if not jrequest:

                record = self.record(table, element)
                if not record:
                    self.error = S3XML_VALIDATION_ERROR
                    continue

                xml_import = XMLImport(self.db, prefix, name, id, record,
                    permit=permit,
                    onvalidation=onvalidation,
                    onaccept=onaccept)
                if not xml_import.method:
                    # possibly unnecessary to check here
                    self.error = S3XML_DATA_IMPORT_ERROR
                    continue

                xml_import.commit()
                record_id = xml_import.id
                if not record_id:
                    self.error = S3XML_DATA_IMPORT_ERROR
                    continue

                db_record = self.db(table.id==record_id).select(table.ALL)[0]

            else:
                record_id = db_record.id

            for join in joins:
                property, pkey, fkey = join

                jelements = self.select_resources(element, property.tablename)

                for jelement in jelements:
                    jrecord = self.record(property.prefix, property.name, jelement)
                    if not jrecord:
                        self.error = S3XML_VALIDATION_ERROR
                        continue
                    xml_import = XMLImport(self.db, property.prefix, property.name,
                                        None, jrecord, permit=permit)
                    if xml_import.method:
                        xml_import.record[fkey]=db_record[pkey]
                        self.imports.append(xml_import)
                    else:
                        self.error = S3XML_DATA_IMPORT_ERROR
                        continue

        return True

    # *************************************************************************
    # JSON->ElementTree

    # -------------------------------------------------------------------------
    def __json2element(self, key, value, native=False):

        if isinstance(value, dict):
            return self.__obj2element(key, value, native=native)

        elif isinstance(value, (list, tuple)):
            _list = etree.Element(self.TAG["list"])
            for obj in value:
                item = self.__json2element(self.TAG["item"], obj, native=native)
                _list.append(item)
            return _list

        else:
            element = etree.Element(key)
            element.text = self.xml_encode(value)
            return element

    # -------------------------------------------------------------------------
    def __obj2element(self, tag, obj, native=False):

        prefix = name = resource = field = None

        if tag is None:
            tag = self.TAG["object"]
        elif native:
            if tag.startswith(self.PREFIX["reference"]):
                field = tag[len(self.PREFIX["reference"])+1:]
                tag = self.TAG["reference"]
            elif tag.startswith(self.PREFIX["resource"]):
                resource = tag[len(self.PREFIX["resource"])+1:]
                tag = self.TAG["resource"]

        element = etree.Element(tag)

        if native:
            if resource:
                element.set(self.ATTRIBUTE["name"], resource)
            if field:
                element.set(self.ATTRIBUTE["field"], field)

        for k in obj.keys():
            m = obj[k]

            if isinstance(m, dict):
                child = self.__obj2element(k, m, native=native)
                element.append(child)

            elif isinstance(m, (list, tuple)):
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

    # -------------------------------------------------------------------------
    def json2tree(self, source, format=None):

        root_dict = json.load(source)

        native=False

        if not format:
            format=self.TAG["root"]
            native=True

        if root_dict and isinstance(root_dict, dict):
            root = self.__obj2element(format, root_dict, native=native)
            if root is not None:
                return etree.ElementTree(root)

        return None

    # *************************************************************************
    # ElementTree->JSON

    # -------------------------------------------------------------------------
    def __element2json(self, element, native=False):

        obj = {}

        for child in element:
            tag_name = child.tag
            if native:
                if tag_name==self.TAG["resource"]:
                    resource = child.get(self.ATTRIBUTE["name"])
                    tag_name = "%s_%s" % (self.PREFIX["resource"], resource)
                elif tag_name==self.TAG["reference"]:
                    tag_name = "%s_%s" % \
                               (self.PREFIX["reference"], child.get(self.ATTRIBUTE["field"]))
                elif tag_name==self.TAG["data"]:
                    tag_name = child.get(self.ATTRIBUTE["field"])

            if tag_name[0]=="{":
                tag_name = tag_name.rsplit("}",1)[1]

            if not tag_name in obj:
                obj[tag_name] = []

            child_obj = self.__element2json(child, native=native)
            if child_obj:
                obj[tag_name].append(child_obj)

        attributes = element.attrib
        for a in attributes:
            if native:
                if a==self.ATTRIBUTE["name"] and element.tag==self.TAG["resource"]:
                    continue
                if a==self.ATTRIBUTE["field"] and \
                   element.tag in (self.TAG["data"], self.TAG["reference"]):
                    continue
            obj[self.PREFIX["attribute"] + a] = self.xml_decode(attributes[a])

        if element.text:
            obj[self.PREFIX["text"]] = self.xml_decode(element.text)

        for key in obj.keys():
            if isinstance(obj[key], (list, tuple, dict)):
                if len(obj[key])==0:
                    del obj[key]
                elif len(obj[key])==1:
                    obj[key] = obj[key][0]

        if len(obj)==1 and obj.keys()[0]==self.PREFIX["text"]:
            obj = obj[obj.keys()[0]]

        return obj

    # -------------------------------------------------------------------------
    def tree2json(self, tree):

        root = tree.getroot()

        if root.tag==self.TAG["root"]:
            native = True
        else:
            native = False

        root_dict = self.__element2json(root, native=native)

        return json.dumps(root_dict)

# *****************************************************************************
# XMLImport
#
class XMLImport(object):

    PERMISSION = dict(create="create", update="update")

    def __init__(self,
                 db=None,
                 prefix=None,
                 name=None,
                 id=None,
                 record=None,
                 permit=None,
                 onvalidation=None,
                 onaccept=None):

        self.db=db
        self.prefix=prefix
        self.name=name
        self.id=id

        self.tablename = "%s_%s" % (self.prefix, self.name)
        self.table = self.db[self.tablename]

        self.method=None
        self.record=record

        self.onvalidation=onvalidation
        self.onaccept=onaccept

        self.accepted=True
        self.permitted=True
        self.committed=False

        self.UUID = "uuid"

        if not self.id:
            self.method = "create"
            permission = self.PERMISSION["create"]
            self.id = 0

            _uuid = self.record.get(self.UUID, None)
            if _uuid is not None:
                if self.db(self.table.uuid==_uuid).count():
                    del self.record[self.UUID]
                    self.method = "update"
                    permission = self.PERMISSION["update"]
                    self.id = self.db(self.table.uuid==_uuid).select(self.table.id)[0].id
        else:
            self.method = "update"
            permission = self.PERMISSION["update"]

            if self.UUID in record:
                del self.record[self.UUID]

            if not self.db(self.table.id==id).count():
                self.method = None
                self.id = 0

        if permit and not \
           permit(permission, self.tablename, record_id=self.id):
            self.permitted=False

    # -------------------------------------------------------------------------
    def commit(self):

        if self.committed:
            return True

        if self.accepted and self.permitted:
            form = Storage() # PseudoForm for callbacks
            form.method = self.method
            form.vars = self.record
            form.vars.id = self.id

            if self.onvalidation:
                self.onvalidation(form)

            try:
                if self.method == "update":
                    self.db(self.table.id==self.id).update(**dict(self.record))
                elif self.method == "create":
                    self.id = self.table.insert(**dict(self.record))

                self.committed=True

            except:
                self.id=0
                self.method=None
                self.accepted=False
                self.committed=False
                return False

            form.vars.id = self.id

            if self.onaccept:
                self.onaccept(form)

            return True

        else:
            return False

