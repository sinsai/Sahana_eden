# -*- coding: utf-8 -*-

"""
    S3REST SahanaPy REST Controller

    @version: 1.1.1

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

__name__ = "S3REST"

__all__ = ['S3RESTController', 'S3RESTRequest']

import sys, uuid

from gluon.storage import Storage
from gluon.html import URL
from gluon.http import HTTP, redirect

from xml.etree.cElementTree import ElementTree
from lxml import etree

# *****************************************************************************
class S3RESTController(object):

    # Error messages
    INVALIDREQUEST = 'Invalid request.'
    UNAUTHORISED = 'Not authorised.'
    BADFORMAT = 'Unsupported data format.'
    BADMETHOD = 'Unsupported method.'
    BADRECORD = 'Record not found.'

    def __init__(self, rc=None, auth=None, **attr):

        assert rc is not None, "Undefined resource controller"
        self.rc = rc

        assert auth is not None, "Undefined authentication controller"
        self.auth = auth

        if attr is None:
            attr = {}

        self.xml_import_formats = attr.get('xml_import_formats', ['xml'])
        self.xml_export_formats = attr.get('xml_export_formats', dict(xml="application/xml"))

        self.json_import_formats = attr.get('json_import_formats', ['json'])
        self.json_export_formats = attr.get('json_export_formats', dict(json="text/x-json"))

        self.debug = attr.get('debug', False)

        self.__handler = Storage()

    #--------------------------------------------------------------------------
    def set_handler(self, method, handler):

        self.__handler[method] = handler


    #--------------------------------------------------------------------------
    def get_handler(self, method):

        return self.__handler.get(method, None)


    #--------------------------------------------------------------------------
    def __has_permission(self, session, name, table_name, record_id = 0):

        if session.s3.security_policy == 1:
            # Simple policy
            # Anonymous users can Read.
            if name == 'read':
                authorised = True
            else:
                # Authentication required for Create/Update/Delete.
                authorised = self.auth.is_logged_in() or self.auth.basic()
        else:
            # Full policy
            if self.auth.is_logged_in() or self.auth.basic():
                # Administrators are always authorised
                if self.auth.has_membership(1):
                    authorised = True
                else:
                    # Require records in auth_permission to specify access
                    authorised = self.auth.has_permission(name, table_name, record_id)
            else:
                # No access for anonymous
                authorised = False

        return authorised

    #--------------------------------------------------------------------------
    def __unauthorised(self, jr, session):

        if jr.representation == "html":
            session.error = self.UNAUTHORISED
            login = URL(r=jr.request, c='default', f='user', args='login', vars={'_next': jr.here()})
            redirect(login)
        else:
            raise HTTP(401, body = self.UNAUTHORISED)

    #--------------------------------------------------------------------------
    def __call__(self, session, request, response, module, resource, **attr):

        if self.debug:
            print >> sys.stderr, "\nS3RESTController: Call\n"

        jr = S3RESTRequest(self.rc, module, resource, request,
                           session=session, debug=self.debug)

        if jr.invalid:
            if jr.badmethod:
                raise HTTP(501, body=self.BADMETHOD)
            elif jr.badrecord:
                raise HTTP(404, body=self.BADRECORD)
            else:
                raise HTTP(400, body=self.INVALIDREQUEST)

        if self.debug:
            print >> sys.stderr, "S3RESTController: processing %s" % jr.here()

        # Initialise
        output = {}
        method = handler = next = None

        # Check read permission on primary table
        if not self.__has_permission(session, 'read', jr.table):
            self.__unauthorised(jr, session)

        # Record ID is required in joined-table operations and read action:
        if not jr.id and (jr.component or jr.method=="read") and \
           not jr.method=="options" and not "select" in jr.request.vars:

            # Check for search_simple
            if jr.representation == 'html':
                search_simple = self.rc.model.get_method(jr.prefix, jr.name, method="search_simple")
                if search_simple:
                    redirect(URL(r=request, f=jr.name, args='search_simple', vars={"_next": jr.same()}))
                else:
                    session.error = self.BADRECORD
                    redirect(URL(r=jr.request, c=jr.prefix, f=jr.name))
            else:
                raise HTTP(404, body=self.BADRECORD)

        # Pre-process
        if 's3' in response and response.s3.prep is not None:
            prep = response.s3.prep(jr)
            if prep and isinstance(prep, dict):
                bypass = prep.get('bypass', False)
                output = prep.get('output', None)
                if bypass and output is not None:
                    if self.debug:
                        print >> sys.stderr, "S3RESTController: got bypass directive - aborting"
                    if isinstance(output, dict):
                        output.update(jr=jr)
                    return output
                success = prep.get('success', True)
                if not success:
                    if jr.representation=='html' and output:
                        if isinstance(output, dict):
                            output.update(jr=jr)
                        if self.debug:
                            print >> sys.stderr, "S3RESTController: preprocess failure - aborting"
                        return output
                    status = prep.get('status', 400)
                    message = prep.get('message', self.INVALIDREQUEST)
                    raise HTTP(status, message)
                else:
                    pass
            elif not prep:
                raise HTTP(400, body=self.INVALIDREQUEST)
            else:
                pass

        # Set default view
        if jr.representation <> "html":
            response.view = 'plain.html'

        # Analyse request
        if jr.method and jr.custom_action:
            handler = jr.custom_action
        else:
            # Joined Table Operation
            if jr.component:

                # HTTP Multi-Record Operation
                if jr.method==None and jr.multiple and not jr.component_id:

                    # HTTP List/List-add
                    if jr.http=='GET':
                        authorised = self.__has_permission(session, 'read', jr.component.table)
                        if authorised:
                            method = 'list'
                        else:
                            self.__unauthorised(jr, session)

                    # HTTP Create
                    elif jr.http=='PUT' or jr.http=='POST':
                        if jr.representation in self.json_import_formats:
                            method = 'import_json'
                        elif jr.representation in self.xml_import_formats:
                            method = 'import_xml'
                        elif jr.http == "POST":
                            authorised = self.__has_permission(session, 'read', jr.component.table)
                            if authorised:
                                method = 'list'
                            else:
                                self.__unauthorised(jr, session)
                        else:
                            raise HTTP(501, body=self.BADFORMAT)

                    # HTTP Delete
                    elif jr.http=='DELETE':
                        # Not implemented
                        raise HTTP(501)

                    # Unsupported HTTP method
                    else:
                        # Unsupported HTTP method for this context:
                        # HEAD, OPTIONS, TRACE, CONNECT
                        # Not implemented
                        raise HTTP(501)

                # HTTP Single-Record Operation
                elif jr.method==None and (jr.component_id or not jr.multiple):

                    # HTTP Read/Update
                    if jr.http=='GET':
                        authorised = self.__has_permission(session, 'read', jr.component.table)
                        if authorised:
                            method = 'read'
                        else:
                            self.__unauthorised(jr, session)

                    # HTTP Update
                    elif jr.http=='PUT' or jr.http == "POST":
                        if jr.representation in self.json_import_formats:
                            method = 'import_json'
                        elif jr.representation in self.xml_import_formats:
                            method = 'import_xml'
                        elif jr.http == "POST":
                            authorised = self.__has_permission(session, 'read', jr.component.table)
                            if authorised:
                                method = 'read'
                            else:
                                self.__unauthorised(jr, session)
                        else:
                            raise HTTP(501, body=self.BADFORMAT)

                    # HTTP Delete
                    elif jr.http=='DELETE':
                        # Not implemented
                        raise HTTP(501)

                    # Unsupported HTTP method
                    else:
                        # Unsupported HTTP method for this context:
                        # POST, HEAD, OPTIONS, TRACE, CONNECT
                        # Not implemented
                        raise HTTP(501)

                # Read (joined table)
                elif jr.method=="read" or jr.method=="display":
                    authorised = self.__has_permission(session, 'read', jr.component.table)
                    if authorised:
                        if jr.multiple and not jr.component_id:
                            # This is a list action
                            method = 'list'
                        else:
                            # This is a read action
                            method = 'read'
                    else:
                        self.__unauthorised(jr, session)

                # Create (joined table)
                elif jr.method=="create":
                    authorised = self.__has_permission(session, jr.method, jr.component.table)
                    if authorised:
                        method = 'create'
                    else:
                        self.__unauthorised(jr, session)

                # Update (joined table)
                elif jr.method=="update":
                    authorised = self.__has_permission(session, jr.method, jr.component.table)
                    if authorised:
                        method = 'update'
                    else:
                        self.__unauthorised(jr, session)

                # Delete (joined table)
                elif jr.method=="delete":
                    authorised = self.__has_permission(session, jr.method, jr.component.table)
                    if authorised:
                        method = 'delete'
                        next = jr.there()
                    else:
                        self.__unauthorised(jr, session)

                # Options (joined table)
                elif jr.method=="options":
                    method = 'options'

                # Unsupported Method
                else:
                    raise HTTP(501, body=self.BADMETHOD)

            # Single Table Operation
            else:

                # Clear Session
                if jr.method=="clear":

                    # Clear session
                    self.rc.clear_session(session, jr.prefix, jr.name)

                    if '_next' in request.vars:
                        request_vars = dict(_next=request.vars._next)
                    else:
                        request_vars = {}

                    # Check for search_simple
                    if jr.representation == 'html':
                        search_simple = self.rc.model.get_method(jr.prefix, jr.name, method="search_simple")
                        if search_simple:
                            next = URL(r=jr.request, f=jr.name, args='search_simple', vars=request_vars)
                        else:
                            next = URL(r=jr.request, f=jr.name)
                    else:
                        next = URL(r=jr.request, f=jr.name)

                # HTTP Multi-Record Operation
                elif not jr.method and not jr.id:

                    # HTTP List or List-Add
                    if jr.http == 'GET':
                        method = 'list'

                    # HTTP Create
                    elif jr.http == 'PUT' or jr.http == "POST":
                        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6
                        if jr.representation in self.json_import_formats:
                            method = 'import_json'
                        elif jr.representation in self.xml_import_formats:
                            method = 'import_xml'
                        elif jr.http == "POST":
                            method = 'list'
                        else:
                            raise HTTP(501, body=self.BADFORMAT)

                    # Unsupported HTTP method
                    else:
                        # Unsupported HTTP method for this context:
                        # DELETE, HEAD, OPTIONS, TRACE, CONNECT
                        # Not implemented
                        raise HTTP(501)

                # HTTP Single Record Operation
                elif jr.id and not jr.method:

                    # HTTP Read (single record)
                    if jr.http == 'GET':
                        method = 'read'

                    # HTTP Create/Update (single record)
                    elif jr.http == 'PUT' or jr.http == "POST":
                        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6
                        if jr.representation in self.json_import_formats:
                            method = 'import_json'
                        elif jr.representation in self.xml_import_formats:
                            method = 'import_xml'
                        elif jr.http == "POST":
                            method = 'read'
                        else:
                            raise HTTP(501, body=self.BADFORMAT)

                    # HTTP Delete (single record)
                    elif jr.http == 'DELETE':
                        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.7
                        if db(db[jr.table].id == jr.id).select():
                            authorised = self.__has_permission(session, 'delete', jr.table, jr.id)
                            if authorised:
                                method = 'delete'
                            else:
                                # Unauthorised
                                raise HTTP(401)
                        else:
                            # Not found
                            raise HTTP(404)

                    # Unsupported HTTP method
                    else:
                        # Unsupported HTTP method for this context:
                        # POST, HEAD, OPTIONS, TRACE, CONNECT
                        # Not implemented
                        raise HTTP(501)

                # Read (single table)
                elif jr.method == "read" or jr.method == "display":
                    # do not redirect here: redirection takes up to 450ms!
                    method = 'read'
                    #request.args.remove(jr.method)
                    #next = URL(r=request, args=request.args, vars=request.vars)

                # Create (single table)
                elif jr.method == "create":
                    authorised = self.__has_permission(session, jr.method, jr.table)
                    if authorised:
                        method = 'create'
                    else:
                        self.__unauthorised(jr, session)

                # Update (single table)
                elif jr.method == "update":
                    authorised = self.__has_permission(session, jr.method, jr.table, jr.id)
                    if authorised:
                        method = 'update'
                    else:
                        self.__unauthorised(jr, session)

                # Delete (single table)
                elif jr.method == "delete":
                    authorised = self.__has_permission(session, jr.method, jr.table, jr.id)
                    if authorised:
                        method = 'delete'
                        next = jr.there()
                    else:
                        self.__unauthorised(jr, session)

                # Search (single table)
                elif jr.method == "search":
                    method = 'search'

                # Options (single table)
                elif jr.method=="options":
                    method = 'options'

                # Unsupported Method
                else:
                    raise HTTP(501, body=self.BADMETHOD)

            # Get handler
            if method is not None:
                if self.debug:
                    print >> sys.stderr, "S3RESTController: method=%s" % method
                handler = self.get_handler(method)

        if handler is not None:
            if self.debug:
                print >> sys.stderr, "S3RESTController: method handler found - executing request"
            output = handler(jr, **attr)
        elif self.debug:
            print >> sys.stderr, "S3RESTController: no method handler - finalizing request"

        # Post-process
        if 's3' in response and response.s3.postp is not None:
            output = response.s3.postp(jr, output)

        # Add XRequest to output dict (if any)
        if output is not None and isinstance(output, dict):
            output.update(jr=jr)

        # Redirect to next
        if next is not None:
            redirect(next)

        return output

# *****************************************************************************
class S3RESTRequest(object):

    """ S3 REST Request """

    DEFAULT_REPRESENTATION = "html"

    #--------------------------------------------------------------------------
    def __init__(self, rc, prefix, name, request, session=None, debug=False):

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
        self.debug = debug

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

        # Parse request
        if not self.__parse():
            if self.debug:
                print >> sys.stderr, \
                    "S3RESTRequest: Parsing of request failed."
            return None

        # Check for component
        if self.component_name:
            self.component, self.pkey, self.fkey = \
                self.rc.model.get_component(self.prefix, self.name, self.component_name)

            if not self.component:
                if self.debug:
                    print >> sys.stderr, \
                        "S3RESTRequest: %s not a component of %s" % \
                        self.component_name, self.tablename
                self.invalid = self.badrequest = True
                return None

            if "multiple" in self.component.attr:
                self.multiple = self.component.attr.multiple

        # Find primary record
        if not self.__record():
            if self.debug:
                print >> sys.stderr, \
                    "S3RESTRequest: Primary record identification failed."
            return None

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

        if self.debug:
            print >> sys.stderr, "S3RESTRequest: *** Init complete ***"
            print >> sys.stderr, "S3RESTRequest: Resource=%s" % self.tablename
            print >> sys.stderr, "S3RESTRequest: ID=%s" % self.id
            print >> sys.stderr, "S3RESTRequest: Component=%s" % self.component_name
            print >> sys.stderr, "S3RESTRequest: ComponentID=%s" % self.component_id
            print >> sys.stderr, "S3RESTRequest: Method=%s" % self.method
            print >> sys.stderr, "S3RESTRequest: Representation=%s" % self.representation

        return

    #--------------------------------------------------------------------------
    def __parse(self):

        """ Parses a web2py request for the REST interface """

        self.args = []

        components = self.rc.model.components

        if len(self.request.args)>0:

            # Check for extensions, turn all arguments lowercase
            for i in xrange(0, len(self.request.args)):
                arg = self.request.args[i]
                if '.' in arg:
                    arg, ext = arg.rsplit('.', 1)
                    if ext and len(ext) > 0:
                        self.representation = str.lower(ext)
                        self.extension = True
                self.args.append(str.lower(arg))

            # Parse arguments after /application/prefix/name...
            if self.args[0].isdigit():
                # .../id...
                self.id = self.args[0]
                if len(self.args)>1:
                    if self.args[1] in components:
                        # .../component...
                        self.component_name = self.args[1]
                        if len(self.args)>2:
                            if self.args[2].isdigit():
                                # ../id...
                                self.component_id = self.args[2]
                                if len(self.args)>3:
                                    # .../method
                                    self.method = self.args[3]
                            else:
                                # .../method
                                self.method = self.args[2]
                                if len(self.args)>3 and self.args[3].isdigit():
                                    # for backward compatibility: .../id
                                    self.component_id = self.args[3]
                    else:
                        # .../method
                        self.method = self.args[1]
            else:
                if self.args[0] in components:
                    # .../component...
                    self.component_name = self.args[0]
                    if len(self.args)>1:
                        if self.args[1].isdigit():
                            # .../id...
                            self.component_id = self.args[1]
                            if len(self.args)>2:
                                # .../method
                                self.method = self.args[2]
                        else:
                            # .../method
                            self.method = self.args[1]
                            if len(self.args)>2 and self.args[2].isdigit():
                                # for backward compatibility: .../id
                                self.component_id = self.args[2]
                else:
                    # .../method
                    self.method = self.args[0]
                    if len(self.args)>1 and self.args[1].isdigit():
                        # for backward compatibility: .../id
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

        """
            Tries to identify and load the primary record of the resource
        """

        uids = None
        if 'uid' in self.request.vars:
            uids = self.request.vars.uid.split(",")
            if len(uids)<2:
                uids.append(None)
            uids = map(lambda uid: \
                       uid and self.rc.xml.import_uid(uid) or None, uids)

        if self.id:
            # Primary record ID is specified
            query = (self.table.id==self.id)
            if 'deleted' in self.table:
                query = ((self.table.deleted==False) | (self.table.deleted==None)) & query
            records = self.rc.db(query).select(self.table.ALL, limitby=(0,1))
            if not records:
                if self.debug:
                    print >> sys.stderr, "Invalid resource record ID"
                self.id = None
                self.invalid = self.badrecord = True
                return False
            else:
                self.record = records[0]

        elif uids and uids[0] is not None and "uuid" in self.table:
            # Primary record UUID is specified
            query = (self.table.uuid==uids[0])
            if 'deleted' in self.table:
                query = ((self.table.deleted==False) | (self.table.deleted==None)) & query
            records = self.rc.db(query).select(self.table.ALL, limitby=(0,1))
            if not records:
                if self.debug:
                    print >> sys.stderr, "Invalid resource record UUID"
                self.id = None
                self.invalid = self.badrecord = True
                return False
            else:
                self.record = records[0]
                self.id = self.record.id

        if self.component and self.component_id:
            # Component record ID is specified
            query = ((self.component.table.id==self.component_id) &
                     (self.table[self.pkey]==self.component.table[self.fkey]))
            if self.id:
                # Must match if a primary record has been found
                query = (self.table.id==self.id) & query
            if 'deleted' in self.table:
                query = ((self.table.deleted==False) |
                         (self.table.deleted==None)) & query
            if 'deleted' in self.component.table:
                query = ((self.component.table.deleted==False) |
                         (self.component.table.deleted==None)) & query
            records = self.rc.db(query).select(self.table.ALL, limitby=(0,1))
            if not records:
                if self.debug:
                    print >> sys.stderr, \
                        "Invalid component record ID or component not matching primary record."
                self.id = None
                self.invalid = self.badrecord = True
                return False
            else:
                self.record = records[0]
                self.id = self.record.id

        elif self.component and \
             uids and uids[1] is not None and "uuid" in self.component.table:
            # Component record ID is specified
            query = ((self.component.table.uuid==uids[1]) &
                     (self.table[self.pkey]==self.component.table[self.fkey]))
            if self.id:
                # Must match if a primary record has been found
                query = (self.table.id==self.id) & query
            if 'deleted' in self.table:
                query = ((self.table.deleted==False) |
                         (self.table.deleted==None)) & query
            if 'deleted' in self.component.table:
                query = ((self.component.table.deleted==False) |
                         (self.component.table.deleted==None)) & query
            records = self.rc.db(query).select(
                        self.table.ALL, self.component.table.id, limitby=(0,1))
            if not records:
                if self.debug:
                    print >> sys.stderr, \
                        "Invalid component record UUID or component not matching primary record."
                self.id = None
                self.invalid = self.badrecord = True
                return False
            else:
                self.record = records[0][self.tablename]
                self.id = self.record.id
                self.component_id = records[0][self.component.tablename].id

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
                    if self.debug:
                        print >> sys.stderr, "No record with ID label %s" % id_label
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
    def __next(self, id=None, method=None, representation=None):

        """ Returns a URL of the current resource """

        args = []
        vars = {}

        component_id = self.component_id

        if not representation:
            representation = self.representation

        if method is None:
            method = self.method
        elif method=="":
            method = None
            if self.component:
                component_id = None
            else:
                id = None
        else:
            if id is None:
                id = self.id
            else:
                id = str(id)
                if len(id)==0:
                    id = "[id]"
                if self.component:
                    component_id = None
                    method = None

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

        if not representation==self.DEFAULT_REPRESENTATION:
            if len(args)>0:
                args[-1] = '%s.%s' % (args[-1], representation)
            else:
                vars = {'format': representation}

        return(URL(r=self.request, c=self.request.controller, f=self.name, args=args, vars=vars))


    #--------------------------------------------------------------------------
    def here(self, representation=None):

        """ URL of the current request """

        return self.__next(id=self.id, representation=representation)


    #--------------------------------------------------------------------------
    def other(self, method=None, record_id=None, representation=None):

        """ URL of a request with different method and/or record_id of the same resource """

        return self.__next(method=method, id=record_id, representation=representation)


    #--------------------------------------------------------------------------
    def there(self, representation=None):

        """ URL of a HTTP/list request on the same resource """

        return self.__next(method="", representation=representation)


    #--------------------------------------------------------------------------
    def same(self, representation=None):

        """ URL of the same request with neutralized primary record ID """

        return self.__next(id="[id]", representation=representation)


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

        if "marker" in self.request.vars:
            # Override marker for displaying KML feeds
            marker = self.request.vars["marker"]
        else:
            marker = None
            
        tree = self.rc.export_xml(self.prefix, self.name, self.id,
                                  joins=joins,
                                  filterby=filterby,
                                  permit=permit,
                                  audit=audit,
                                  start=start,
                                  limit=limit,
                                  marker=marker)

        if template is not None:
            args = dict(domain=self.rc.domain, base_url=self.rc.base_url)
            mode = self.request.vars.get('mode', None)
            if mode is not None:
                args.update(mode=mode)
            tree = self.rc.xml.transform(tree, template, **args)
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
            args = dict(domain=self.rc.domain, base_url=self.rc.base_url)
            mode = self.request.vars.get('mode', None)
            if mode is not None:
                args.update(mode=mode)
            tree = self.rc.xml.transform(tree, template, **args)
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
