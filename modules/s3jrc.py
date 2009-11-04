# -*- coding: utf-8 -*-

"""
    SahanaPy Joined Resources Controller

    @version: 1.0-1, 2009-10-26

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

__name__ = "S3JRC"

from gluon.storage import Storage
from gluon.html import URL

# *****************************************************************************
# Joined Resource
#
class JoinedResource(object):

    def __init__(self, prefix, name, joinby=None, multiple=True, list_fields=None, rss=None, attr=None):

        self.prefix = prefix
        self.name = name
        self.joinby = joinby
        self.multiple = multiple
        self.list_fields = list_fields
        self.rss = rss
        if attr:
            self.attr = attr
        else:
            self.attr = {}

        if not 'deletable' in self.attr:
            self.set_attr('deletable', True)

        if not 'editable' in self.attr:
            self.set_attr('editable', True)

    # get_prefix --------------------------------------------------------------
    def get_prefix(self):
        return self.prefix

    # is_multiple -------------------------------------------------------------
    def is_multiple(self):
        return self.multiple

    # get_list_fields ---------------------------------------------------------
    def get_list_fields(self):
        return self.list_fields

    # rss ---------------------------------------------------------------------
    def _rss(self):
        return self.rss

    # head_fields -------------------------------------------------------------
    def head_fields(self):
        if 'main' in self.attr:
            main = self.attr['main']
        else:
            main = 'id'

        if 'extra' in self.attr:
            extra = self.attr['extra']
        else:
            extra = main

        return (main, extra)

    # set_attr ----------------------------------------------------------------
    def set_attr(self, name, value):
        self.attr.update(name, value)

    # get_attr ----------------------------------------------------------------
    def get_attr(self, name):
        if name in self.attr:
            return self.attr[name]
        else:
            return None

    # get_join_key ------------------------------------------------------------
    def get_join_key(self, db, module, resource):

        tablename = "%s_%s" % (module, resource)
        table = db[tablename]

        if self.joinby:
            if isinstance(self.joinby, str):
                # natural join
                if self.joinby in table:
                    return (self.joinby, self.joinby)
                else:
                    # Not joined with this table
                    return None

            elif isinstance(self.joinby, dict):
                # primary/foreign key join
                if tablename in self.joinby:
                    return ('id', self.joinby[tablename])
                else:
                    # Not joined with this table
                    return None
            else:
                # Invalid definition
                return None
        else:
            # No join_key defined
            return None

# *****************************************************************************
# JRLayer
#
class JRLayer(object):

    jresources = {}
    settings = {}
    methods = {}
    jmethods = {}

    def __init__(self, db):

        self.db = db
        self.jresources = {}
        self.settings = {}

    # add_jresource -----------------------------------------------------------
    def add_jresource(self, prefix, name, joinby=None, multiple=True, rss=None, list_fields=None, **attr):

        _fields = None

        _table = "%s_%s" % (prefix, name)

        if list_fields:
            _fields = [self.db[_table][f] for f in list_fields]

        jr = JoinedResource(prefix, name, joinby=joinby, multiple=multiple, rss=rss, list_fields=_fields, attr=attr)
        self.jresources[name] = jr

    # get_joins ---------------------------------------------------------------
    def get_joins(self, prefix, name):
        """
            Get all jresources that can be linked to the given resource
        """
        joins = []

        _table = "%s_%s" % (prefix, name)
        if _table in self.db:
            table = self.db[_table]
        else:
            return joins
        
        for _jresource in self.jresources:
            jresource = self.jresources[_jresource]
            join_keys = jresource.get_join_key(self.db, prefix, name)
            if join_keys and join_keys[0] in table:
                # resource is linked
                joins.append(dict(
                    prefix=jresource.prefix,
                    name=jresource.name,
                    pkey=join_keys[0],
                    fkey=join_keys[1]))

        return joins

    # get_prefix --------------------------------------------------------------
    def get_prefix(self, name):

        if name in self.jresources:
            return self.jresources[name].get_prefix()
        else:
            return None

    # is_multiple -------------------------------------------------------------
    def is_multiple(self, name):

        if name in self.jresources:
            return self.jresources[name].is_multiple()
        else:
            return True

    # get_join_key ------------------------------------------------------------
    def get_join_key(self, name, module, resource):

        if name in self.jresources:
            return self.jresources[name].get_join_key(self.db, module, resource)
        else:
            return None

    # get_list_fields ---------------------------------------------------------
    def get_list_fields(self, name):

        if name in self.jresources:
            return self.jresources[name].get_list_fields()
        else:
            return None

    # rss ---------------------------------------------------------------------
    def rss(self, name):

        if name in self.jresources:
            return self.jresources[name]._rss()
        else:
            return None

    # head_fields -------------------------------------------------------------
    def head_fields(self, resource):

        if resource in self.jresources:
            return self.jresources[resource].head_fields()
        else:
            return (None, None)

    # set_attr ----------------------------------------------------------------
    def set_attr(self, resource, name, value):

        if resource in self.jresources:
            self.jresources[resource].set_attr(name, value)

    # get_attr ----------------------------------------------------------------
    def get_attr(self, resource, name):

        if resource in self.jresources:
            return self.jresources[resource].get_attr(name)
        else:
            return None

    # set_method --------------------------------------------------------------
    def set_method(self, prefix, resource, jprefix, jresource, method, action):

        if not method:
            return None

        if prefix and resource:
            tablename = "%s_%s" % (prefix, resource)

            if jprefix and jresource:
                jtablename = "%s_%s" % (jprefix, jresource)
                if not (method in self.jmethods):
                    self.jmethods[method] = {}
                if not (jtablename in self.jmethods[method]):
                    self.jmethods[method][jtablename] = {}
                self.jmethods[method][jtablename][tablename] = action
                return action
            else:
                if not (method in self.methods):
                    self.methods[method] = {}
                self.methods[method][tablename] = action
                return action

        else:
            return None

    # get_method --------------------------------------------------------------
    def get_method(self, prefix, resource, jprefix, jresource, method):

        if not method:
            return None

        if prefix and resource:
            tablename = "%s_%s" % (prefix, resource)

            if jprefix and jresource:
                jtablename = "%s_%s" % (jprefix, jresource)
                if method in self.jmethods and \
                    jtablename in self.jmethods[method] and \
                    tablename in self.jmethods[method][jtablename]:
                    return self.jmethods[method][jtablename][tablename]
                else:
                    return None
            else:
                if method in self.methods and tablename in self.methods[method]:
                    return self.methods[method][tablename]
                else:
                    return None
        else:
            return None

    # store_session -----------------------------------------------------------
    def store_session(self, session, module, resource, record_id):

        if session and not ('jrvars' in session):
            session.jrvars = Storage()

        if session and 'jrvars' in session:
            tablename = "%s_%s" % (module, resource)
            session.jrvars[tablename] = record_id

        return True # always return True to make this chainable

    # clear_session -----------------------------------------------------------
    def clear_session(self, session, module=None, resource=None):

        if session:

            if module and resource:
                tablename = "%s_%s" % (module, resource)
                if ('jrvars' in session) and (tablename in session.jrvars):
                    del session.jrvars[tablename]

            else:
                if 'jrvars' in session:
                    del session['jrvars']

        return True # always return True to make this chainable

# *****************************************************************************
# JRequest
#
class JRequest(object):
    """
        Class handling requests to joined resources REST controller.
    """

    def __init__(self, jrlayer, module, resource, request, session=None):

        self.default_representation = 'html'
        self.request = request
        self.jrlayer = jrlayer
        self.session = session

        self.invalid = False
        self.badmethod = False
        self.badrecord = False
        self.badrequest = False

        self.representation = request.extension
        self.http = request.env.request_method
        self.extension = False

        self.module = module or request.controller
        self.resource = resource or request.function
        self.method = None
        self.record_id = None
        self.jresource = None

        # Parse original request
        if not self.__parse():
            return None

        self.tablename = None
        self.table = None
        self.record = None

        # Check for primary record
        if not self.__record():
            return None

        self.jmodule = None
        self.jtablename = None
        self.jtable = None
        self.jrecord_id = None
        self.pkey = None
        self.fkey = None
        self.multiple = True

        #  Get Joined Resource parameters (if any)
        if self.jresource:
            self.jmodule = self.jrlayer.get_prefix(self.jresource)
            self.multiple = self.jrlayer.is_multiple(self.jresource)
            if not self.jrecord_id:
                if self.args[len(self.args)-1].isdigit():
                    self.jrecord_id = self.args[len(self.args)-1]
            self.jtablename = "%s_%s" % (self.jmodule, self.jresource)
            self.jtable = self.jrlayer.db[self.jtablename]

            # Get join key
            join_keys = self.jrlayer.get_join_key(self.jresource, self.module, self.resource)
            if not join_keys:
                self.badmethod = True
                self.invalid = True
                return self
            else:
                self.pkey, self.fkey = join_keys

        # Get custom action (if any)
        self.custom_action = self.jrlayer.get_method(
            self.module,
            self.resource,
            self.jmodule,
            self.jresource,
            self.method)

        # Append record ID to request as necessary
        if self.record_id:
            if len(self.args)>0 or len(self.args)==0 and ('id_label' in self.request.vars):
                if self.jresource and not self.args[0].isdigit():
                    self.args.insert(0, str(self.record_id))
                    if self.representation==self.default_representation or self.extension:
                        self.request.args.insert(0, str(self.record_id))
                    else:
                        self.request.args.insert(0, '%s.%s' % (self.record_id, self.representation))
                elif not self.jresource and not (str(self.record_id) in self.args):
                    self.args.append(self.record_id)
                    if self.representation==self.default_representation or self.extension:
                        self.request.args.append(self.record_id)
                    else:
                        self.request.args.append('%s.%s' % (self.record_id, self.representation))
    # -------------------------------------------------------------------------
    def __parse(self):
        """
            Parse the original request
        """

        self.args = []

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
                self.record_id = self.args[0]
                if len(self.args)>1:
                    self.jresource = self.args[1]
                    if self.jresource in self.jrlayer.jresources:
                        if len(self.args)>2:
                            if self.args[2].isdigit():
                                self.jrecord_id = self.args[2]
                            else:
                                self.method = self.args[2]
                        else:
                            self.method = None
                    else:
                        # Error: BAD REQUEST
                        self.badrequest = True
                        self.invalid = True
                        return False
                else:
                    self.jresource = None
                    self.method = None
            else:
                if self.args[0] in self.jrlayer.jresources:
                    self.jresource = self.args[0]
                    self.record_id = None
                    if len(self.args)>1:
                        if self.args[1].isdigit():
                            self.jrecord_id = self.args[1]
                        else:
                            self.method = self.args[1]
                    else:
                        self.method = None
                else:
                    self.method = self.args[0]
                    self.jresource = None
                    if len(self.args)>1 and self.args[1].isdigit():
                        self.record_id = self.args[1]
                    else:
                        self.record_id = None

        # Check format option
        if 'format' in self.request.vars:
            self.representation = str.lower(self.request.vars.format)

        # Representation fallback
        if not self.representation:
            self.representation = self.default_representation

        return True

    # -------------------------------------------------------------------------
    def __record(self):
        """
            Check primary record ID
        """

        # Get primary table
        self.tablename = "%s_%s" % (self.module, self.resource)
        self.table = self.jrlayer.db[self.tablename]

        # Check record ID passed in the request
        if self.record_id:
            query = (self.table.id==self.record_id)
            if 'deleted' in self.table:
                query = ((self.table.deleted==False) | (self.table.deleted==None)) & query
            records = self.jrlayer.db(query).select(self.table.ALL)
            if records:
                self.record = records[0]
                self.record_id = self.record.id
            else:
                # Error: NO SUCH RECORD
                self.record_id = 0
                self.badrecord = True
                self.invalid = True
                return False

        # Check for ?id_label=
        if not self.record_id and 'id_label' in self.request.vars:
            id_label = str.strip(self.request.vars.id_label)
            if 'pr_pe_label' in self.table:
                query = (self.table.pr_pe_label==id_label)
                if 'deleted' in self.table:
                    query = ((self.table.deleted==False) | (self.table.deleted==None)) & query
                records = self.jrlayer.db(query).select(self.table.ALL)
                if records:
                    self.record = records[0]
                    self.record_id = self.record.id
                else:
                    # Error: NO SUCH RECORD
                    self.record_id = 0
                    self.badrecord = True
                    self.invalid = True
                    return False

        # Retrieve prior selected ID, if any
        if not self.record_id and len(self.request.args)>0:
            if self.session and self.session.jrvars and self.tablename in self.session.jrvars:
                self.record_id = self.session.jrvars[self.tablename]
                query = (self.table.id==self.record_id)
                if 'deleted' in self.table:
                    query = ((self.table.deleted==False) | (self.table.deleted==None)) & query
                records = self.jrlayer.db(query).select(self.table.ALL)
                if records:
                    self.record = records[0]
                    self.record_id = self.record.id
                else:
                    self.record_id = None
                    self.session.jrvars[self.tablename] = None

        # Remember primary record ID for further requests
        if self.record_id and self.session:
            self.jrlayer.store_session(self.session, self.module, self.resource, self.record_id)

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

        if self.jresource:
            args = [self.record_id]
            if not representation==self.default_representation:
                args.append('%s.%s' % (self.jresource, representation))
            else:
                args.append(self.jresource)
            if self.method:
                args.append(self.method)
                if self.jrecord_id:
                    args.append(self.jrecord_id)
        else:
            if self.method:
                args.append(self.method)
            if self.record_id:
                if not representation==self.default_representation:
                    args.append('%s.%s' % (self.record_id, representation))
                else:
                    args.append(self.record_id)
            else:
                if not representation==self.default_representation:
                    vars = {'format': representation}

        return(URL(r=self.request, c=self.request.controller, f=self.resource, args=args, vars=vars))

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
            record_id = self.record_id

        if self.jresource:
            args = [record_id]
            if not representation==self.default_representation:
                args.append('%s.%s' % (self.jresource, representation))
            else:
                args.append(self.jresource)
            if method:
                args.append(method)
                if self.jrecord_id:
                    args.append(self.jrecord_id)
        else:
            if method:
                args.append(method)
            if record_id:
                if not representation==self.default_representation:
                    args.append('%s.%s' % (record_id, representation))
                else:
                    args.append(record_id)
            else:
                if not representation==self.default_representation:
                    vars = {'format': representation}

        return(URL(r=self.request, c=self.request.controller, f=self.resource, args=args, vars=vars))

    # -------------------------------------------------------------------------
    def there(self, representation=None):
        """
            Backlink producing a HTTP/list request to the same resource
        """
        args = []
        vars = {}

        if not representation:
            representation = self.representation

        if self.jresource:
            args = [self.record_id]
            if not representation==self.default_representation:
                args.append('%s.%s' % (self.jresource, representation))
            else:
                args.append(self.jresource)
        else:
            if not representation==self.default_representation:
                vars = {'format': representation}

        return(URL(r=self.request, c=self.request.controller, f=self.resource, args=args, vars=vars))

    # -------------------------------------------------------------------------
    def same(self, representation=None):
        """
            Backlink producing the same request with neutralized primary record ID
        """

        args = []
        vars = {}

        if not representation:
            representation = self.representation

        if self.jresource:
            args = ['[id]']
            if not representation==self.default_representation:
                args.append('%s.%s' % (self.jresource, representation))
            else:
                args.append(self.jresource)
            if self.method:
                args.append(self.method)
        else:
            if self.method:
                args.append(self.method)
            if self.record_id or self.method=="read":
                if not representation==self.default_representation:
                    args.append('[id].%s' % representation)
                else:
                    args.append('[id]')
            else:
                if not representation==self.default_representation:
                    vars = {'format': representation}

        return(URL(r=self.request, c=self.request.controller, f=self.resource, args=args, vars=vars))
