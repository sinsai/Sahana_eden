# -*- coding: utf-8 -*-

"""
    SahanaPy XML+JSON Resource Controller

    @version: 1.0-1, 2009-10-27

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
from lxml import etree

#******************************************************************************
# Errors
#
S3XRC_PARSE_ERROR = "XML Parse Error"
S3XRC_TRANFORMATION_ERROR = "XSLT Transformation Error"

# *****************************************************************************
# XRController
#
class XRController(object):

    XRVARS = "xrvars"

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

        property = XRProperty(self.db, prefix, name, **attr)
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

        if self.XRVARS in session and tablename in session[self.XRVARS]:
            return session[self.XRVARS][tablename]

    # -------------------------------------------------------------------------
    def store_session(self, session, prefix, name, id):

        if self.XRVARS not in session:
            session[self.XRVARS] = Storage()

        if self.XRVARS in session:
            tablename = "%s_%s" % (prefix, name)
            session[self.XRVARS][tablename] = id

        return True # always return True to make this chainable

    # -------------------------------------------------------------------------
    def clear_session(self, session, prefix=None, name=None):

        if prefix and name:
            tablename = "%s_%s" % (prefix, name)
            if self.XRVARS in session and tablename in session[self.XRVARS]:
                del session[self.XRVARS][tablename]
        else:
            if self.XRVARS in session:
                del session[self.XRVARS]

        return True # always return True to make this chainable

    # -------------------------------------------------------------------------
    def parse(self, source):

        self.error = None

        try:
            parser = etree.XMLParser(no_network=False)
            result = etree.parse(source, parser)
            return result
        except:
            self.error = S3XRC_PARSE_ERROR
            return None

    # -------------------------------------------------------------------------
    def transform(self, tree, template_path):

        template = self.parse(template_path)
        if template:
            try:
                transformer = etree.XSLT(template)
                result = transformer(tree)
                return result
            except:
                self.error = S3XRC_TRANFORMATION_ERROR
                return None
        else:
            # Error parsing the XSL template
            return None

    # -------------------------------------------------------------------------
    def request(self, prefix, name, request, session=None):

        return XRRequest(self, prefix, name, request, session=session)

# *****************************************************************************
# XRProperty
#
class XRProperty(object):

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
# XRRequest
#
class XRRequest(object):

    DEFAULT_REPRESENTATION = "html"

    def __init__(self, xrc, prefix, name, request, session=None):

        assert xrc is not None, "XRController must not be None."
        self.xrc = xrc

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
        self.table = self.xrc.db[self.tablename]

        self.method = None
        self.id = None

        self.property = None
        self.pkey = self.fkey = None
        self.property_name = None
        self.property_id = None

        if not self.__parse():
            return None

        if not self.__record():
            return None

        # Check for property
        if self.property_name:
            self.property, self.pkey, self.fkey = self.xrc.get_property(self.prefix, self.name, self.property_name)

            if not self.property:
                self.invalid = self.badrequest = True
                return None

            if not self.property_id:
                if self.args[len(self.args)-1].isdigit():
                    self.property_id = self.args[len(self.args)-1]

        # Check for custom action
        self.custom_action = self.xrc.get_method(self.prefix, self.name,
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

        properties = self.xrc.properties

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
            if not self.xrc.db(query).count():
                self.id = None
                self.invalid = self.badrecord = True
                return False

        # Check for ?id_label=
        if not self.id and 'id_label' in self.request.vars:
            id_label = str.strip(self.request.vars.id_label)
            if 'pr_pe_label' in self.table:
                query = (self.table.pr_pe_label==id_label)
                if 'deleted' in self.table:
                    query = ((self.table.deleted==False) | (self.table.deleted==None)) & query
                records = self.xrc.db(query).select(self.table.id, limitby=(0,1))
                if records:
                    self.id = records[0].id
                else:
                    self.id = 0
                    self.invalid = self.badrecord = True
                    return False

        # Retrieve prior selected ID, if any
        if not self.id and len(self.request.args)>0:

            self.id = self.xrc.get_session(self.session, self.prefix, self.name)

            if self.id:
                query = (self.table.id==self.id)
                if 'deleted' in self.table:
                    query = ((self.table.deleted==False) | (self.table.deleted==None)) & query
                if not self.xrc.db(query).count():
                    self.id = None
                    self.xrc.clear_session(self.session, self.prefix, self.name)

        # Remember primary record ID for further requests
        if self.id:
            self.xrc.store_session(self.session, self.prefix, self.name, self.id)

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
