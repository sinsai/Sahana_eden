# -*- coding: utf-8 -*-

"""
    SahanaPy XML+JSON Interface

    @version: 1.2-1, 2009-11-09
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
# JRController
#
class JRController(object):

    JRVARS = "jrvars"

    def __init__(self, db, domain=None, base_url=None):

        assert db is not None, "Database must not be None."
        self.db = db

        self.domain = domain
        self.base_url = base_url

        self.error = None

        self.properties = {}

        self.methods = {}
        self.pmethods = {}

    # -------------------------------------------------------------------------
    def set_property(self, prefix, name, **attr):

        assert "joinby" in attr, "Join key(s) must be defined."

        property = StructuredProperty(self.db, prefix, name, **attr)
        self.properties[name] = property
        return property

    # -------------------------------------------------------------------------
    def get_property(self, prefix, name, property_name):

        if property_name in self.properties:

            property = self.properties[property_name]

            pkey, fkey = property.get_join_keys(prefix, name)
            if pkey is not None:
                return (property, pkey, fkey)

        return (None, None, None)

    # -------------------------------------------------------------------------
    def get_properties(self, prefix, name):

        plist = []

        for property_name in self.properties:

            property, pkey, fkey = self.get_property(prefix, name, property_name)
            if property is not None:
                plist.append((property, pkey, fkey))

        return plist

    # -------------------------------------------------------------------------
    def set_method(self, prefix, name, property_name=None, method=None, action=None):

        assert method is not None, "Method must be specified."

        tablename = "%s_%s" % (prefix, name)

        if property_name is None:

            if method not in self.methods:
                self.methods[method] = {}
            self.methods[method][tablename] = action

        else:

            property = self.get_property(prefix, name, property_name)[0]
            if property is not None:

                if method not in self.pmethods:
                    self.pmethods[method] = {}

                if property.tablename not in self.pmethods[method]:
                    self.pmethods[method][property.tablename] = {}

                self.pmethods[method][property.tablename][tablename] = action

        return

    # -------------------------------------------------------------------------
    def get_method(self, prefix, name, property_name=None, method=None):

        if not method:
            return None

        tablename = "%s_%s" % (prefix, name)

        if property_name is None:

            if method in self.methods and tablename in self.methods[method]:
                return self.methods[method][tablename]
            else:
                return None

        else:

            property = self.get_property(prefix, name, property_name)[0]
            if property is not None and \
               method in self.pmethods and \
               property.tablename in self.pmethods[method] and \
               tablename in self.pmethods[method][property.tablename]:
                return self.pmethods[method][property.tablename][tablename]
            else:
                return None

    # -------------------------------------------------------------------------
    def get_session(self, session, prefix, name):

        tablename = "%s_%s" % (prefix, name)

        if self.JRVARS in session and tablename in session[self.JRVARS]:
            return session[self.JRVARS][tablename]

    # -------------------------------------------------------------------------
    def store_session(self, session, prefix, name, id):

        if self.JRVARS not in session:
            session[self.JRVARS] = Storage()

        if self.JRVARS in session:
            tablename = "%s_%s" % (prefix, name)
            session[self.JRVARS][tablename] = id

        return True # always return True to make this chainable

    # -------------------------------------------------------------------------
    def clear_session(self, session, prefix=None, name=None):

        if prefix and name:
            tablename = "%s_%s" % (prefix, name)
            if self.JRVARS in session and tablename in session[self.JRVARS]:
                del session[self.JRVARS][tablename]
        else:
            if self.JRVARS in session:
                del session[self.JRVARS]

        return True # always return True to make this chainable

    # -------------------------------------------------------------------------
    def request(self, prefix, name, request, session=None):

        return JoinedRequest(self, prefix, name, request, session=session)

# *****************************************************************************
# StructuredProperty
#
class StructuredProperty(object):

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
# JoinedRequest
#
class JoinedRequest(object):

    DEFAULT_REPRESENTATION = "html"

    def __init__(self, jrc, prefix, name, request, session=None):

        assert jrc is not None, "JRController must not be None."
        self.jrc = jrc

        self.prefix = prefix or request.controller
        self.name = name or request.function

        self.request = request
        if session is not None:
            self.session = session
        else:
            self.session = Storage()

        self.invalid = False
        self.badmethod = False
        self.badrecord = False
        self.badrequest = False

        self.representation = request.extension
        self.http = request.env.request_method
        self.extension = False

        self.tablename = "%s_%s" % (self.prefix, self.name)
        self.table = self.jrc.db[self.tablename]

        self.method = None
        self.id = None
        self.record = None

        self.property = None
        self.pkey = self.fkey = None
        self.property_name = None
        self.property_id = None
        self.multiple = True

        if not self.__parse():
            return None

        if not self.__record():
            return None

        # Check for property
        if self.property_name:
            self.property, self.pkey, self.fkey = self.jrc.get_property(self.prefix, self.name, self.property_name)

            if not self.property:
                self.invalid = self.badrequest = True
                return None

            if "multiple" in self.property.attr:
                self.multiple = self.property.attr.multiple

            if not self.property_id:
                if self.args[len(self.args)-1].isdigit():
                    self.property_id = self.args[len(self.args)-1]

        # Check for custom action
        self.custom_action = self.jrc.get_method(self.prefix, self.name,
                                                 property_name=self.property_name,
                                                 method=self.method)

        # Append record ID to request as necessary
        if self.id:
            if len(self.args)>0 or len(self.args)==0 and ('id_label' in self.request.vars):
                if self.property and not self.args[0].isdigit():
                    self.args.insert(0, str(self.id))
                    if self.representation==self.DEFAULT_REPRESENTATION or self.extension:
                        self.request.args.insert(0, str(self.id))
                    else:
                        self.request.args.insert(0, '%s.%s' % (self.id, self.representation))
                elif not self.property and not (str(self.id) in self.args):
                    self.args.append(self.id)
                    if self.representation==self.DEFAULT_REPRESENTATION or self.extension:
                        self.request.args.append(self.id)
                    else:
                        self.request.args.append('%s.%s' % (self.id, self.representation))

    # -------------------------------------------------------------------------
    def __parse(self):

        self.args = []

        properties = self.jrc.properties

        if len(self.request.args)>0:

            # Check for extensions
            for arg in self.request.args:
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
                    self.property_name = self.args[1]
                    if self.property_name in properties:
                        if len(self.args)>2:
                            if self.args[2].isdigit():
                                self.property_id = self.args[2]
                            else:
                                self.method = self.args[2]
                    else:
                        self.invalid = self.badrequest = True
                        return False
            else:
                if self.args[0] in properties:
                    self.property_name = self.args[0]
                    if len(self.args)>1:
                        if self.args[1].isdigit():
                            self.property_id = self.args[1]
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
            fields = [self.table[f] for f in self.table.fields]
            records = self.jrc.db(query).select(*fields, limitby=(0,1))
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
                fields = [self.table[f] for f in self.table.fields]
                records = self.jrc.db(query).select(*fields, limitby=(0,1))
                if records:
                    self.record = records[0]
                    self.id = self.record.id
                else:
                    self.id = 0
                    self.invalid = self.badrecord = True
                    return False

        # Retrieve prior selected ID, if any
        if not self.id and len(self.request.args)>0:

            self.id = self.jrc.get_session(self.session, self.prefix, self.name)

            if self.id:
                query = (self.table.id==self.id)
                if 'deleted' in self.table:
                    query = ((self.table.deleted==False) | (self.table.deleted==None)) & query
                fields = [self.table[f] for f in self.table.fields]
                records = self.jrc.db(query).select(*fields, limitby=(0,1))
                if not records:
                    self.id = None
                    self.jrc.clear_session(self.session, self.prefix, self.name)
                else:
                    self.record = records[0]

        # Remember primary record ID for further requests
        if self.id:
            self.jrc.store_session(self.session, self.prefix, self.name, self.id)

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

        if self.property:
            args = [self.id]
            if not representation==self.DEFAULT_REPRESENTATION:
                args.append('%s.%s' % (self.property_name, representation))
            else:
                args.append(self.property_name)
            if self.method:
                args.append(self.method)
                if self.property_id:
                    args.append(self.property_id)
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
            property_id = self.property_id
        else:
            property_id = None

        if self.property:
            args = [record_id]
            if not representation==self.DEFAULT_REPRESENTATION:
                args.append('%s.%s' % (self.property_name, representation))
            else:
                args.append(self.property_name)
            if method:
                args.append(method)
                if property_id:
                    args.append(property_id)
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

        if self.property:
            args = [self.id]
            if not representation==self.DEFAULT_REPRESENTATION:
                args.append('%s.%s' % (self.property_name, representation))
            else:
                args.append(self.property_name)
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

        if self.property:
            args = ['[id]']
            if not representation==self.DEFAULT_REPRESENTATION:
                args.append('%s.%s' % (self.property_name, representation))
            else:
                args.append(self.property_name)
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

        if self.property is not None:
            return (
                self.property.prefix,
                self.property.name,
                self.property.table,
                self.property.tablename
            )
        else:
            return (
                self.prefix,
                self.name,
                self.table,
                self.tablename
            )

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

# *****************************************************************************
# S3XML
#
class S3XML(object):

    UUID = "uuid"

    IGNORE_FIELDS = ["deleted", "id"]

    FIELDS_TO_ATTRIBUTES = [
            "created_on",
            "modified_on",
            "created_by",
            "modified_by",
            "uuid",
            "admin"]

    ATTRIBUTES_TO_FIELDS = ("admin",)

    TAG = dict(
        root="sahanapy",
        resource="resource",
        reference="reference",
        data="data",
        list="list",
        item="item",
        object="object"
        )

    ATTRIBUTE = dict(
        name="name",
        table="table",
        field="field",
        value="value",
        resource="resource",
        domain="domain",
        url="url"
        )

    # JSON Prefixes
    PREFIX = dict(
        resource="$r",
        reference="$k",
        attribute="@",
        text="$"
    )

    ACTION = dict(
        create="create",
        read="read",
        update="update",
        delete="delete"
    )

    def __init__(self, db, domain=None, base_url=None):

        self.db = db
        self.error = None

        self.imports = []
        self.exports = []

        self.domain = domain
        self.base_url = base_url

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

        if obj is None:
            return None

        encode = {'<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;'}
        obj = obj.replace('&', '&amp;')
        for c in encode.keys():
            obj = obj.replace(c, encode[c])
        return obj

    # -------------------------------------------------------------------------
    def xml_decode(self, obj):

        if obj is None:
            return None

        decode = {'&lt;': '<', '&gt;': '>', '&quot;': '"', '&apos;': "'" }
        for c in decode.keys():
            obj = obj.replace(c, decode[c])
        return obj.replace('&amp;', '&')

    # -------------------------------------------------------------------------
    def __element(self, table, record, skip=[]):

        element = etree.Element(self.TAG["resource"])

        for f in record.keys():

            if f in skip or \
               f in self.IGNORE_FIELDS or \
               f not in table:
                continue

            if f == self.UUID:
                if record[f] is None:
                    element.set(f, "")
                else:
                    value = table[f].formatter(record[f])
                    element.set(f, self.xml_encode(str(value)))

            elif f in self.FIELDS_TO_ATTRIBUTES:
                if record[f] is None:
                    element.set(f, "")
                elif table[f].represent:
                    element.set(f, self.xml_encode(str(table[f].represent(record[f])).decode('utf-8')))
                else:
                    element.set(f, self.xml_encode(str(table[f].formatter(record[f])).decode('utf-8')))

            elif table[f].type.startswith("reference"):

                _rtable = table[f].type.split()[1]

                if _rtable in self.db and self.UUID in self.db[_rtable]:
                    rtable = self.db[_rtable]
                    try:
                        _uuid = self.db(rtable.id==record[f]).select(rtable.uuid)[0].uuid
                    except:
                        continue
                    reference = etree.SubElement(element, self.TAG["reference"])
                    reference.set(self.ATTRIBUTE["field"], self.xml_encode(f))
                    reference.set(self.ATTRIBUTE["resource"], self.xml_encode(_rtable))
                    reference.set(self.UUID, self.xml_encode(str(_uuid)))
                    value = table[f].formatter(record[f])
                    if table[f].represent:
                        reference.text = self.xml_encode(str(table[f].represent(record[f])).decode('utf-8'))
                    else:
                        reference.text = self.xml_encode(str(value).decode('utf-8'))
                else:
                    continue

            else:
                if record[f] is None:
                    continue
                else:
                    data = etree.SubElement(element, self.TAG["data"])
                    data.set(self.ATTRIBUTE["field"], self.xml_encode(f))
                    value = table[f].formatter(record[f])
                    if table[f].represent:
                        data.set(self.ATTRIBUTE["value"], self.xml_encode(str(value).decode('utf-8')))
                        data.text = self.xml_encode(str(table[f].represent(record[f])).decode('utf-8'))
                    else:
                        data.text = self.xml_encode(str(value).decode('utf-8'))

        return element

    # -------------------------------------------------------------------------
    def __export(self, table, query, joins=[], skip=[], permit=None, audit=None, url=None):

        _table = table._tablename
        prefix, name = _table.split("_", 1)

        if self.base_url and not url:
            url = "%s/%s" % (self.base_url, prefix)

        try:
            if permit and not permit(self.ACTION["read"], _table):
                return None

            fields = [table[f] for f in table.fields]
            records = self.db(query).select(*fields) or []
            resources = []

            for record in records:
                if permit and not \
                   permit(self.ACTION["read"], _table, record_id=record.id):
                    continue

                if audit is not None:
                    audit(self.ACTION["read"], prefix, name, record=record.id, representation="xml")

                resource = self.__element(table, record, skip=skip)
                resource.set(self.ATTRIBUTE["name"], _table)

                if url:
                    resource_url = "%s/%s/%s" % (url, name, record.id)
                    resource.set(self.ATTRIBUTE["url"], resource_url)
                else:
                    resource_url = None

                for join in joins:
                    property, pkey, fkey = join

                    _query = (property.table[fkey]==record[pkey])
                    if "deleted" in property.table:
                        _query = ((property.table.deleted==False) |
                                  (property.table.deleted==None)) & _query

                    jresources = self.__export(property.table, _query,
                                               skip=[fkey],
                                               permit=permit,
                                               audit=audit,
                                               url=resource_url)

                    if jresources:
                        if NO_LXML:
                            for r in jresources:
                                resource.append(r)
                        else:
                            resource.extend(jresources)

                resources.append(resource)

            return resources

        except:
            return None

    # -------------------------------------------------------------------------
    def get(self, prefix, name, id, joins=[], permit=None, audit=None):

        self.error = None

        _table = "%s_%s" % (prefix, name)
        root = etree.Element(self.TAG["root"])

        if _table in self.db:
            table = self.db[_table]

            if id and isinstance(id, (list, tuple)):
                query = (table.id.belongs(id))
            elif id:
                query = (table.id==id)
            else:
                query = (table.id>0)

            if "deleted" in table:
                query = ((table.deleted==False) | (table.deleted==None)) & query

            resources = self.__export(table, query, joins=joins, permit=permit, audit=audit)

            if resources:
                if NO_LXML:
                    for r in resources:
                        root.append(r)
                else:
                    root.extend(resources)

        if self.domain:
            root.set(self.ATTRIBUTE["domain"], self.domain)

        if self.base_url:
            root.set(self.ATTRIBUTE["url"], self.base_url)

        tree = etree.ElementTree(root)
        return tree

    # -------------------------------------------------------------------------
    def record(self, table, element, skip=[]):

        record = Storage()
        original = None

        if self.UUID in table.fields and self.UUID not in skip:
            _uuid = element.get(self.UUID, None)
            if _uuid and len(_uuid)>0:
                record[self.UUID] = _uuid
                try:
                    original = self.db(table.uuid==_uuid).select(table.ALL)[0]
                except:
                    original = None

        for child in element:
            if child.tag==self.TAG["data"]:
                fieldname = child.get(self.ATTRIBUTE["field"], None)
                if not fieldname or fieldname not in table.fields:
                    continue
                if fieldname in self.IGNORE_FIELDS or fieldname in skip:
                    continue
                if table[fieldname].type.startswith('reference'):
                    continue
                value = self.xml_decode(child.get(self.ATTRIBUTE["value"], None))
                if value is None:
                    value = self.xml_decode(child.text)
                if value is None:
                    value = table[fieldname].default
                if value is None and table[fieldname].type == "string":
                    value = ''

                if value is not None:
                    (value, error) = self.validate(table, original, fieldname, value)
                    if error:
                        self.error = error
                        return None
                    else:
                        record[fieldname]=value

            elif child.tag==self.TAG["reference"]:
                fieldname = child.get(self.ATTRIBUTE["field"], None)
                if not fieldname or fieldname not in table.fields:
                    continue
                _rtable =  child.get(self.ATTRIBUTE["resource"], None)
                _uuid = child.get(self.UUID, None)
                if not (_rtable and _uuid):
                    continue
                if _rtable in self.db and self.UUID in self.db[_rtable]:
                    rtable = self.db[_rtable]
                    try:
                        rid = self.db(rtable.uuid==_uuid).select(rtable.id)[0].id
                    except:
                        continue
                    record[fieldname] = rid
                else:
                    continue

            else:
                continue

        for f in self.ATTRIBUTES_TO_FIELDS:
            if f in skip:
                continue
            if f in table.fields:
                value = element.get(f, None)
                if value is not None:
                    (value, error) = self.validate(table, original, f, value)
                    if error:
                        self.error = error
                        return None
                    else:
                        record[f]=value

        return record

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

    # -------------------------------------------------------------------------
    def commit(self):

        for r in self.imports:
            r.commit()
        return

    # -------------------------------------------------------------------------
    def put(self,
            prefix,
            name,
            id,
            tree,
            joins=[],
            jrequest=False,
            permit=None,
            onvalidation=None,
            onaccept=None):

        if NO_LXML:
            self.error = S3XML_NO_LXML
            return False

        if not tree: # nothing to import actually
            return True

        if joins is None:
            joins = []

        self.error = None
        self.imports = []

        root = tree.getroot()
        if not root.tag==self.TAG["root"]:
            self.error = S3XML_BAD_SOURCE
            return False

        _table = "%s_%s" % (prefix, name)
        expr = './/resource[@%s="%s"]' % (self.ATTRIBUTE["name"], _table)
        elements = root.xpath(expr)

        if not len(elements): # still nothing to import
            return True

        if _table in self.db:
            table = self.db[_table]
        else:
            self.error = S3XML_BAD_RESOURCE
            return False

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
                _uuid = db_record[self.UUID]
                for element in elements:
                    if element.get(self.UUID)==_uuid:
                        elements = [element]
                        break

            if len(elements)>1:
                # Error: multiple input elements, but only one target record
                self.error = S3XML_NO_MATCH
                return False

        for element in elements:

            if not jrequest:

                record = self.record(prefix, name, element)
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

                expr = './resource[@%s="%s"]' % (self.ATTRIBUTE["name"], property.tablename)

                jelements = element.xpath(expr)
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
            element.text = value
            return element

    # -------------------------------------------------------------------------
    def __obj2element(self, key, obj, native=False):

        if key is None:
            tag = self.tag["object"]
        else:
            tag = key

        prefix = name = field = None

        if native:
            if key.startswith(self.PREFIX["resource"]):
                tag = self.TAG["resource"]
                resource = key[len(self.PREFIX["resource"])+1:]
            elif key.startswith(self.PREFIX["reference"]):
                tag = self.TAG["reference"]
                field = key[len(self.PREFIX["reference"])+1:]

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
                    element.text = m
                elif k.startswith(self.PREFIX["attribute"]):
                    attribute = k[len(self.PREFIX["attribute"]):]
                    element.set(attribute, m)
                else:
                    child = self.__json2element(k, m, native=native)
                    element.append(child)

        return element

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

            if tag_name.startswith("{"):
                ns, tag_name = tag_name.rsplit("}",1)

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

    # -------------------------------------------------------------------------
    def json2tree(self, source, format=None):

        root_dict = json.loads(source)

        native=False

        if not format:
            format=self.TAG["root"]
            native=True

        if root_dict and isinstance(root_dict, dict):
            root = self.__obj2element(format, root_dict, native=native)
            if root is not None:
                return etree.ElementTree(root)

        return None

