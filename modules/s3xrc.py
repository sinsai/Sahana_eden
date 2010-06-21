# -*- coding: utf-8 -*-

"""
    S3XRC Resource Framework

    @version: 1.9
    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

    @author: nursix
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

__name__ = "S3XRC"
__all__ = ["S3RESTController", "S3ResourceController"]

import sys, uuid, datetime, time, urllib
import gluon.contrib.simplejson as json

from gluon.storage import Storage
from gluon.html import URL
from gluon.http import HTTP, redirect
from gluon.validators import IS_NULL_OR, IS_EMPTY_OR
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


# *****************************************************************************
class S3RESTController(object):

    """ RESTful interface for S3 resources """

    # Error messages
    INVALIDREQUEST = "Invalid request."
    UNAUTHORISED = "Not authorised."
    BADFORMAT = "Unsupported data format."
    BADMETHOD = "Unsupported method."
    BADRECORD = "Record not found."


    def __init__(self, rc=None, auth=None, **attr):

        """ Constructor

            @param rc: the resource controller
            @param auth: the auth controller
            @param attr: dict of attributes

        """

        assert rc is not None, "Undefined resource controller"
        self.rc = rc

        assert auth is not None, "Undefined authentication controller"
        self.auth = auth

        if attr is None:
            attr = {}

        self.xml_import_formats = attr.get("xml_import_formats", ["xml"])
        self.xml_export_formats = attr.get("xml_export_formats",
                                           dict(xml="application/xml"))

        self.json_import_formats = attr.get("json_import_formats", ["json"])
        self.json_export_formats = attr.get("json_export_formats",
                                            dict(json="text/x-json"))

        self.debug = attr.get("debug", False)

        self.__handler = Storage()


    def __dbg(self, msg):

        """ Output debug messages

            @param msg: the message

        """

        if self.debug:
            print >> sys.stderr, "S3RESTController: %s" % msg


    # Configuration ===========================================================

    def set_handler(self, method, handler):

        """ Set a method handler

            @param method: the method
            @param handler: the method handler

        """

        self.__handler[method] = handler


    def get_handler(self, method):

        """ Get a method handler

            @param method: the method

        """

        return self.__handler.get(method, None)


    # Helper functions ========================================================

    def __has_permission(self, session, name, table_name, record_id = 0):

        """ Check permissions of the current user for a table

            @param session: the session
            @param name: name of the permission to check
            @param table_name: name of the table to check
            @param record_id: ID of the record to check

        """

        if session.s3.security_policy == 1:
            # Simple policy
            # Anonymous users can Read.
            if name == "read":
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
                    authorised = self.auth.has_permission(name, table_name,
                                                          record_id)
            else:
                # No access for anonymous
                authorised = False

        return authorised

    def __unauthorised(self, jr, session):

        """ Action upon unauthorized access

            @param jr: the REST request
            @param session: the session

        """

        if jr.representation == "html":
            session.error = self.UNAUTHORISED
            login = URL(r=jr.request, c="default", f="user", args="login",
                        vars={"_next": jr.here()})
            redirect(login)
        else:
            raise HTTP(401, body = self.UNAUTHORISED)


    # Main controller function ================================================

    def __call__(self, session, request, response, module, resource, **attr):

        """ REST interface

            @param session: the session
            @param request: the web2py request object
            @param response: the web2py response object
            @param module: name of the module (=prefix of the resource name)
            @param resource: name of the resource (=without prefix)

        """

        self.__dbg("\nS3RESTController: Call\n")

        jr = S3RESTRequest(self.rc, module, resource, request,
                           session=session, debug=self.debug)

        if jr.invalid:
            if jr.badmethod:
                raise HTTP(501, body=self.BADMETHOD)
            elif jr.badrecord:
                raise HTTP(404, body=self.BADRECORD)
            else:
                raise HTTP(400, body=self.INVALIDREQUEST)

        self.__dbg("S3RESTController: processing %s" % jr.here())

        # Initialise
        output = {}
        method = handler = next = None

        # Check read permission on primary table
        if not self.__has_permission(session, "read", jr.table):
            self.__unauthorised(jr, session)

        # Record ID is required in joined-table operations and read action:
        if not jr.id and (jr.component or jr.method == "read") and \
           not jr.method == "options" and not "select" in jr.request.vars:
            # Check for search_simple
            if jr.representation == "html":
                search_simple = self.rc.model.get_method(jr.prefix, jr.name,
                                                        method="search_simple")
                if search_simple:
                    redirect(URL(r=request, f=jr.name, args="search_simple",
                                 vars={"_next": jr.same()}))
                else:
                    session.error = self.BADRECORD
                    redirect(URL(r=jr.request, c=jr.prefix, f=jr.name))
            else:
                raise HTTP(404, body=self.BADRECORD)

        # Pre-process
        if "s3" in response and response.s3.prep is not None:
            prep = response.s3.prep(jr)
            if prep and isinstance(prep, dict):
                bypass = prep.get("bypass", False)
                output = prep.get("output", None)
                if bypass and output is not None:
                    self.__dbg("S3RESTController: got bypass directive - aborting")
                    if isinstance(output, dict):
                        output.update(jr=jr)
                    return output
                success = prep.get("success", True)
                if not success:
                    if jr.representation == "html" and output:
                        if isinstance(output, dict):
                            output.update(jr=jr)
                        self.__dbg("S3RESTController: preprocess failure - aborting")
                        return output
                    status = prep.get("status", 400)
                    message = prep.get("message", self.INVALIDREQUEST)
                    raise HTTP(status, message)
                else:
                    pass
            elif not prep:
                raise HTTP(400, body=self.INVALIDREQUEST)
            else:
                pass

        # Set default view
        if jr.representation <> "html":
            response.view = "plain.html"

        # Analyse request
        if jr.method and jr.custom_action:
            handler = jr.custom_action
        else:
            # Joined Table Operation
            if jr.component:
                # HTTP Multi-Record Operation
                if jr.method == None and jr.multiple and not jr.component_id:
                    # HTTP List/List-add
                    if jr.http == "GET":
                        authorised = self.__has_permission(session, "read",
                                                           jr.component.table)
                        if authorised:
                            method = "list"
                        else:
                            self.__unauthorised(jr, session)
                    # HTTP Create
                    elif jr.http == "PUT" or jr.http == "POST":
                        if jr.representation in self.json_import_formats:
                            method = "import_json"
                        elif jr.representation in self.xml_import_formats:
                            method = "import_xml"
                        elif jr.http == "POST":
                            authorised = self.__has_permission(session, "read",
                                                            jr.component.table)
                            if authorised:
                                method = "list"
                            else:
                                self.__unauthorised(jr, session)
                        else:
                            raise HTTP(501, body=self.BADFORMAT)
                    # HTTP Delete
                    elif jr.http == "DELETE":
                        # Not implemented
                        raise HTTP(501)
                    # Unsupported HTTP method
                    else:
                        # Unsupported HTTP method for this context:
                        # HEAD, OPTIONS, TRACE, CONNECT
                        # Not implemented
                        raise HTTP(501)
                # HTTP Single-Record Operation
                elif jr.method == None and (jr.component_id or not jr.multiple):
                    # HTTP Read/Update
                    if jr.http == "GET":
                        authorised = self.__has_permission(session, "read",
                                                           jr.component.table)
                        if authorised:
                            method = "read"
                        else:
                            self.__unauthorised(jr, session)
                    # HTTP Update
                    elif jr.http == "PUT" or jr.http == "POST":
                        if jr.representation in self.json_import_formats:
                            method = "import_json"
                        elif jr.representation in self.xml_import_formats:
                            method = "import_xml"
                        elif jr.http == "POST":
                            authorised = self.__has_permission(session, "read",
                                                            jr.component.table)
                            if authorised:
                                method = "read"
                            else:
                                self.__unauthorised(jr, session)
                        else:
                            raise HTTP(501, body=self.BADFORMAT)
                    # HTTP Delete
                    elif jr.http == "DELETE":
                        # Not implemented
                        raise HTTP(501)
                    # Unsupported HTTP method
                    else:
                        # Unsupported HTTP method for this context:
                        # POST, HEAD, OPTIONS, TRACE, CONNECT
                        # Not implemented
                        raise HTTP(501)
                # Read (joined table)
                elif jr.method == "read" or jr.method == "display":
                    authorised = self.__has_permission(session, "read",
                                                       jr.component.table)
                    if authorised:
                        if jr.multiple and not jr.component_id:
                            # This is a list action
                            method = "list"
                        else:
                            # This is a read action
                            method = "read"
                    else:
                        self.__unauthorised(jr, session)
                # Create (joined table)
                elif jr.method == "create":
                    authorised = self.__has_permission(session, jr.method,
                                                       jr.component.table)
                    if authorised:
                        method = "create"
                    else:
                        self.__unauthorised(jr, session)
                # Update (joined table)
                elif jr.method == "update":
                    authorised = self.__has_permission(session, jr.method,
                                                       jr.component.table)
                    if authorised:
                        method = "update"
                    else:
                        self.__unauthorised(jr, session)
                # Delete (joined table)
                elif jr.method == "delete":
                    authorised = self.__has_permission(session, jr.method,
                                                       jr.component.table)
                    if authorised:
                        method = "delete"
                        next = jr.there()
                    else:
                        self.__unauthorised(jr, session)
                # Options (joined table)
                elif jr.method == "options":
                    method = "options"
                # Unsupported Method
                else:
                    raise HTTP(501, body=self.BADMETHOD)
            # Single Table Operation
            else:
                # Clear Session
                if jr.method == "clear":
                    # Clear session
                    self.rc.clear_session(session, jr.prefix, jr.name)
                    if "_next" in request.vars:
                        request_vars = dict(_next=request.vars._next)
                    else:
                        request_vars = {}
                    # Check for search_simple
                    if jr.representation == "html":
                        search_simple = \
                            self.rc.model.get_method(jr.prefix, jr.name,
                                                     method="search_simple")
                        if search_simple:
                            next = URL(r=jr.request, f=jr.name,
                                       args="search_simple", vars=request_vars)
                        else:
                            next = URL(r=jr.request, f=jr.name)
                    else:
                        next = URL(r=jr.request, f=jr.name)
                # HTTP Multi-Record Operation
                elif not jr.method and not jr.id:
                    # HTTP List or List-Add
                    if jr.http == "GET":
                        method = "list"
                    # HTTP Create
                    elif jr.http == "PUT" or jr.http == "POST":
                        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6
                        if jr.representation in self.json_import_formats:
                            method = "import_json"
                        elif jr.representation in self.xml_import_formats:
                            method = "import_xml"
                        elif jr.http == "POST":
                            method = "list"
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
                    if jr.http == "GET":
                        method = "read"
                    # HTTP Create/Update (single record)
                    elif jr.http == "PUT" or jr.http == "POST":
                        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6
                        if jr.representation in self.json_import_formats:
                            method = "import_json"
                        elif jr.representation in self.xml_import_formats:
                            method = "import_xml"
                        elif jr.http == "POST":
                            method = "read"
                        else:
                            raise HTTP(501, body=self.BADFORMAT)
                    # HTTP Delete (single record)
                    elif jr.http == "DELETE":
                        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.7
                        if db(db[jr.table].id == jr.id).select():
                            authorised = self.__has_permission(session,
                                                               "delete",
                                                               jr.table,
                                                               jr.id)
                            if authorised:
                                method = "delete"
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
                    method = "read"
                # Create (single table)
                elif jr.method == "create":
                    authorised = self.__has_permission(session, jr.method,
                                                       jr.table)
                    if authorised:
                        method = "create"
                    else:
                        self.__unauthorised(jr, session)
                # Update (single table)
                elif jr.method == "update":
                    authorised = self.__has_permission(session, jr.method,
                                                       jr.table, jr.id)
                    if authorised:
                        method = "update"
                    else:
                        self.__unauthorised(jr, session)
                # Delete (single table)
                elif jr.method == "delete":
                    authorised = self.__has_permission(session, jr.method,
                                                       jr.table, jr.id)
                    if authorised:
                        method = "delete"
                        next = jr.there()
                    else:
                        self.__unauthorised(jr, session)
                # Search (single table)
                elif jr.method == "search":
                    method = "search"
                # Options (single table)
                elif jr.method == "options":
                    method = "options"
                # Unsupported Method
                else:
                    raise HTTP(501, body=self.BADMETHOD)
            # Get handler
            if method is not None:
                self.__dbg("S3RESTController: method=%s" % method)
                handler = self.get_handler(method)

        if handler is not None:
            self.__dbg("S3RESTController: method handler found - executing request")
            output = handler(jr, **attr)
        else:
            self.__dbg("S3RESTController: no method handler - finalizing request")

        # Post-process
        if "s3" in response and response.s3.postp is not None:
            output = response.s3.postp(jr, output)

        # Add S3RESTRequest to output dict (if any)
        if output is not None and isinstance(output, dict):
            output.update(jr=jr)

        # Redirect to next
        if next is not None:
            redirect(next)

        return output


# *****************************************************************************
class S3RESTRequest(object):

    """ Class to represent RESTful requests """

    DEFAULT_REPRESENTATION = "html"


    def __init__(self, rc, prefix, name, request, session=None, debug=False):

        """ Constructor

            @param rc: the resource controller
            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param request: the web2py request object
            @param session: the session store
            @param debug: whether to print debug messages or not

        """

        assert rc is not None, "Resource controller must not be None."
        self.rc = rc

        self.prefix = prefix or request.controller
        self.name = name or request.function

        self.request = request
        if session is not None:
            self.session = session
        else:
            self.session = Storage()

        self.debug = debug
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

        # Parse request
        if not self.__parse():
            self.__dbg("S3RESTRequest: Parsing of request failed.")
            return None

        # Check for component
        if self.component_name:
            self.component, self.pkey, self.fkey = \
                self.rc.model.get_component(self.prefix, self.name,
                                            self.component_name)
            if not self.component:
                self.__dbg("S3RESTRequest: %s not a component of %s" %
                           (self.component_name, self.tablename))
                self.invalid = self.badrequest = True
                return None
            if "multiple" in self.component.attr:
                self.multiple = self.component.attr.multiple

        # Find primary record
        if not self.__record():
            self.__dbg("S3RESTRequest: Primary record identification failed.")
            return None

        # Check for custom action
        self.custom_action = \
            self.rc.model.get_method(self.prefix, self.name,
                                     component_name=self.component_name,
                                     method=self.method)

        # Append record ID to request as necessary
        if self.id:
            if len(self.args) > 0 or \
               len(self.args) == 0 and \
               ("select" in self.request.vars):
                if self.component and not self.args[0].isdigit():
                    self.args.insert(0, str(self.id))
                    if self.representation == self.DEFAULT_REPRESENTATION or \
                       self.extension:
                        self.request.args.insert(0, str(self.id))
                    else:
                        self.request.args.insert(0, "%s.%s" %
                                                (self.id, self.representation))
                elif not self.component and not (str(self.id) in self.args):
                    self.args.append(self.id)
                    if self.representation == self.DEFAULT_REPRESENTATION or \
                       self.extension:
                        self.request.args.append(self.id)
                    else:
                        self.request.args.append("%s.%s" %
                                                (self.id, self.representation))

        self.__dbg("S3RESTRequest: *** Init complete ***")
        self.__dbg("S3RESTRequest: Resource=%s" % self.tablename)
        self.__dbg("S3RESTRequest: ID=%s" % self.id)
        self.__dbg("S3RESTRequest: Component=%s" % self.component_name)
        self.__dbg("S3RESTRequest: ComponentID=%s" % self.component_id)
        self.__dbg("S3RESTRequest: Method=%s" % self.method)
        self.__dbg("S3RESTRequest: Representation=%s" % self.representation)

        return


    def __dbg(self, msg):

        """ Output debug messages

            @param msg: the message

        """

        if self.debug:
            print >> sys.stderr, "S3RESTRequest: %s" % msg


    # Request parser ==========================================================

    def __parse(self):

        """ Parses a web2py request for the REST interface """

        self.args = []

        components = self.rc.model.components

        if len(self.request.args) > 0:
            for i in xrange(0, len(self.request.args)):
                arg = self.request.args[i]
                if "." in arg:
                    arg, ext = arg.rsplit(".", 1)
                    if ext and len(ext) > 0:
                        self.representation = str.lower(ext)
                        self.extension = True
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

        return True


    # Resource finder =========================================================

    def __record(self):

        """ Tries to identify and load the primary record of the resource """

        # TODO: allow SOME result (current options: ALL or ONE)

        uid = self.request.vars.get("%s.uid" % self.name, None)
        if isinstance(uid, list):
            uid = uid[0]
        uids = [uid, None]
        if self.component_name:
            uid = self.request.vars.get("%s.uid" % self.component_name, None)
            if isinstance(uid, list):
                uid = uid[0]
            uids[1] = uid
        if self.rc.xml.domain_mapping:
            uids = map(lambda uid: \
                       uid and self.rc.xml.import_uid(uid) or None, uids)

        if self.id:
            # Primary record ID is specified
            query = (self.table.id == self.id)
            if "deleted" in self.table:
                query = ((self.table.deleted == False) |
                         (self.table.deleted == None)) & query
            records = self.rc.db(query).select(self.table.ALL, limitby=(0, 1))
            if not records:
                self.__dbg("Invalid resource record ID")
                self.id = None
                self.invalid = self.badrecord = True
                return False
            else:
                self.record = records[0]

        elif uids and uids[0] is not None and "uuid" in self.table:
            # Primary record UUID is specified
            query = (self.table.uuid == uids[0])
            if "deleted" in self.table:
                query = ((self.table.deleted == False) |
                         (self.table.deleted == None)) & query
            records = self.rc.db(query).select(self.table.ALL, limitby=(0, 1))
            if not records:
                self.__dbg("Invalid resource record UUID")
                self.id = None
                self.invalid = self.badrecord = True
                return False
            else:
                self.record = records[0]
                self.id = self.record.id

        if self.component and self.component_id:
            # Component record ID is specified
            query = ((self.component.table.id == self.component_id) &
                     (self.table[self.pkey] == self.component.table[self.fkey]))
            if self.id:
                # Must match if a primary record has been found
                query = (self.table.id == self.id) & query
            if "deleted" in self.table:
                query = ((self.table.deleted == False) |
                         (self.table.deleted == None)) & query
            if "deleted" in self.component.table:
                query = ((self.component.table.deleted == False) |
                         (self.component.table.deleted == None)) & query
            records = self.rc.db(query).select(self.table.ALL, limitby=(0, 1))
            if not records:
                self.__dbg("Invalid component record ID or component not matching primary record.")
                self.id = None
                self.invalid = self.badrecord = True
                return False
            else:
                self.record = records[0]
                self.id = self.record.id

        elif self.component and \
             uids and uids[1] is not None and "uuid" in self.component.table:
            # Component record ID is specified
            query = ((self.component.table.uuid == uids[1]) &
                     (self.table[self.pkey] == self.component.table[self.fkey]))
            if self.id:
                # Must match if a primary record has been found
                query = (self.table.id == self.id) & query
            if "deleted" in self.table:
                query = ((self.table.deleted == False) |
                         (self.table.deleted == None)) & query
            if "deleted" in self.component.table:
                query = ((self.component.table.deleted == False) |
                         (self.component.table.deleted == None)) & query
            records = self.rc.db(query).select(
                        self.table.ALL, self.component.table.id, limitby=(0, 1))
            if not records:
                self.__dbg("Invalid component record UUID or component not matching primary record.")
                self.id = None
                self.invalid = self.badrecord = True
                return False
            else:
                self.record = records[0][self.tablename]
                self.id = self.record.id
                self.component_id = records[0][self.component.tablename].id

        # Check for ?select=
        if not self.id and "select" in self.request.vars:
            if self.request.vars["select"] == "ALL":
                return True
            id_label = str.strip(self.request.vars.id_label)
            if "pr_pe_label" in self.table:
                query = (self.table.pr_pe_label == id_label)
                if "deleted" in self.table:
                    query = ((self.table.deleted == False) |
                             (self.table.deleted == None)) & query
                records = self.rc.db(query).select(self.table.ALL,
                                                   limitby=(0, 1))
                if records:
                    self.record = records[0]
                    self.id = self.record.id
                else:
                    self.__dbg("No record with ID label %s" % id_label)
                    self.id = 0
                    self.invalid = self.badrecord = True
                    return False

        # Retrieve prior selected ID, if any
        if not self.id and len(self.request.args) > 0:
            self.id = self.rc.get_session(self.session, self.prefix, self.name)
            if self.id:
                query = (self.table.id == self.id)
                if "deleted" in self.table:
                    query = ((self.table.deleted == False) |
                             (self.table.deleted == None)) & query
                records = self.rc.db(query).select(self.table.ALL,
                                                   limitby=(0, 1))
                if not records:
                    self.id = None
                    self.rc.clear_session(self.session, self.prefix, self.name)
                else:
                    self.record = records[0]

        # Remember primary record ID for further requests
        if self.id:
            self.rc.store_session(self.session,
                                  self.prefix, self.name, self.id)

        return True


    # URL helpers =============================================================

    def __next(self, id=None, method=None, representation=None):

        """ Returns a URL of the current resource

            @param id: the record ID for the URL
            @param method: an explicit method for the URL
            @param representation: the representation for the URL

        """

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
                if len(id) == 0:
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
            if len(args) > 0:
                args[-1] = "%s.%s" % (args[-1], representation)
            else:
                vars = {"format": representation}

        return(URL(r=self.request, c=self.request.controller,
                   f=self.name, args=args, vars=vars))


    def here(self, representation=None):

        """ URL of the current request

            @param representation: the representation for the URL

        """

        return self.__next(id=self.id, representation=representation)


    def other(self, method=None, record_id=None, representation=None):

        """ URL of a request with different method and/or record_id
            of the same resource

            @param method: an explicit method for the URL
            @param record_id: the record ID for the URL
            @param representation: the representation for the URL

        """

        return self.__next(method=method, id=record_id,
                           representation=representation)


    def there(self, representation=None):

        """ URL of a HTTP/list request on the same resource

            @param representation: the representation for the URL

        """

        return self.__next(method="", representation=representation)


    def same(self, representation=None):

        """ URL of the same request with neutralized primary record ID

            @param representation: the representation for the URL

        """

        return self.__next(id="[id]", representation=representation)


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


    # XML+JSON helpers ========================================================

    def export_xml(self,
                   permit=None,
                   audit=None,
                   title=None,
                   template=None,
                   filterby=None,
                   pretty_print=False):

        """ Export the requested resources as XML

            @param permit: permit hook (function to check table permissions)
            @param audit: audit hook (function to audit table access)
            @param template: the XSLT template (filename)
            @param filterby: filter option
            @param pretty_print: provide pretty formatted output

        """

        if self.component:
            joins = [(self.component, self.pkey, self.fkey)]
        else:
            if "components" in self.request.vars:
                joins = []
                if not self.request.vars["components"] == "NONE":
                    components = self.request.vars["components"].split(",")
                    for c in components:
                        component, pkey, fkey = \
                            self.rc.model.get_component(self.prefix,
                                                        self.name, c)
                        if component is not None:
                            joins.append([component, pkey, fkey])
            else:
                joins = self.rc.model.get_components(self.prefix, self.name)

        start = self.request.vars.get("start", None)
        if start is not None:
            try:
                start = int(self.request.vars["start"])
            except ValueError:
                start = None

        limit = self.request.vars.get("limit", None)
        if limit is not None:
            try:
                limit = int(self.request.vars["limit"])
            except ValueError:
                limit = None

        marker = self.request.vars.get("marker", None)

        msince = self.request.vars.get("msince", None)
        if msince is not None:
            tfmt = "%Y-%m-%dT%H:%M:%SZ"
            try:
                (y,m,d,hh,mm,ss,t0,t1,t2) = time.strptime(msince, tfmt)
                msince = datetime.datetime(y,m,d,hh,mm,ss)
            except ValueError:
                msince = None

        tree = self.rc.export_xml(self.prefix, self.name, self.id,
                                  joins=joins,
                                  filterby=filterby,
                                  permit=permit,
                                  audit=audit,
                                  msince=msince,
                                  start=start,
                                  limit=limit,
                                  marker=marker)

        if template is not None:
            tfmt = "%Y-%m-%d %H:%M:%S"
            args = dict(domain=self.rc.domain,
                        base_url=self.rc.base_url,
                        prefix=self.prefix,
                        name=self.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt))
            if title:
                args.update(title=title)
            if self.component:
                args.update(id=self.id, component=self.component.tablename)
            mode = self.request.vars.get("mode", None)
            if mode is not None:
                args.update(mode=mode)
            tree = self.rc.xml.transform(tree, template, **args)
            if not tree:
                self.error = self.rc.error
                return None

        return self.rc.xml.tostring(tree, pretty_print=pretty_print)


    def export_json(self,
                    permit=None,
                    audit=None,
                    title=None,
                    template=None,
                    filterby=None,
                    pretty_print=False):

        """ Export the requested resources as JSON

            @param permit: permit hook (function to check table permissions)
            @param audit: audit hook (function to audit table access)
            @param template: the XSLT template (filename)
            @param filterby: filter option
            @param pretty_print: provide pretty formatted output

        """

        if self.component:
            joins = [(self.component, self.pkey, self.fkey)]
        else:
            if "components" in self.request.vars:
                joins = []
                if not components == "NONE":
                    components = self.request.vars["components"].split(",")
                    for c in components:
                        component, pkey, fkey = \
                            self.model.get_component(self.prefix, self.name, c)
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

        # marker and msince not supported in JSON

        tree = self.rc.export_xml(self.prefix, self.name, self.id,
                               joins=joins,
                               filterby=filterby,
                               permit=permit,
                               audit=audit,
                               start=start,
                               limit=limit,
                               show_urls=False)

        if template is not None:
            tfmt = "%Y-%m-%d %H:%M:%S"
            args = dict(domain=self.rc.domain,
                        base_url=self.rc.base_url,
                        prefix=self.prefix,
                        name=self.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt))
            if title:
                args.update(title=title)
            if self.component:
                args.update(id=self.id, component=self.component.tablename)
            mode = self.request.vars.get("mode", None)
            if mode is not None:
                args.update(mode=mode)
            tree = self.rc.xml.transform(tree, template, **args)
            if not tree:
                self.error = self.rc.error
                return None

        return self.rc.xml.tree2json(tree, pretty_print=pretty_print)


    def import_xml(self, tree, permit=None, audit=None, push_limit=1):

        """ import the requested resources from an element tree

            @param tree: the element tree
            @param permit: permit hook (function to check table permissions)
            @param audit: audit hook (function to audit table access)
            @param push_limit: number of resources allowed in pushes

        """

        if self.http not in ("PUT", "POST"):
            push_limit = None

        if self.component:
            skip_resource = True
            joins = [(self.component, self.pkey, self.fkey)]
        else:
            skip_resource = False
            joins = self.rc.model.get_components(self.prefix, self.name)

        if self.method == "create":
            self.id = None

        # Add "&ignore_errors=True" to the URL to override any import errors:
        # Unsuccessful commits simply get ignored, no error message is
        # returned, invalid records are not imported at all, but all valid
        # records in the source are committed (whereas the standard method
        # stops at any errors).
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
                                  push_limit=push_limit,
                                  ignore_errors=ignore_errors)


    def options_tree(self):

        """ Export field options in the current resource as element tree """

        fields = self.request.vars.get("field", None)
        if fields and not isinstance(fields, list):
            if "," in fields:
                fields = fields.split(",")
            else:
                fields = [fields]

        if not fields:
            if self.component:
                tree = self.rc.options_xml(self.component.prefix,
                                           self.component.name)
            else:
                joins = self.rc.model.get_components(self.prefix, self.name)
                tree = self.rc.options_xml(self.prefix, self.name, joins=joins)
        else:
            if self.component:
                table = self.component.table
            else:
                table = self.table
            tree = etree.Element(self.rc.xml.TAG.options)
            for field in fields:
                opt_list = self.rc.xml.get_field_options(table, field)
                opt_list.set("id", "%s_%s" % (table._tablename, field))
                opt_list.set("name", "%s" % field)
                tree.append(opt_list)
            if len(tree) == 1:
                tree = tree.findall("select")[0]
            else:
                tree.set(self.rc.xml.TAG.resource, table._tablename)
            tree = etree.ElementTree(tree)

        return tree


    def options_xml(self, pretty_print=False):

        """ Export field options in the current resource as XML

            @param pretty_print: provide pretty formatted output

        """

        tree = self.options_tree()
        return self.rc.xml.tostring(tree, pretty_print=pretty_print)


    def options_json(self, pretty_print=False):

        """ Export field options in the current resource as JSON

            @param pretty_print: provide pretty formatted output

        """

        tree = self.options_tree()
        return self.rc.xml.tree2json(tree, pretty_print=pretty_print)


# *****************************************************************************
class S3ResourceComponent(object):

    """ Class to represent component relations between resources """

    def __init__(self, db, prefix, name, **attr):

        """ Constructor

            @param db: the database (DAL)
            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param attr: attributes

        """

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


    # Configuration ===========================================================

    def set_attr(self, name, value):

        """ Sets an attribute for a component

            @param name: attribute name
            @param value: attribute value

        """

        self.attr[name] = value


    def get_attr(self, name):

        """ Reads an attribute of the component

            @param name: attribute name

        """

        if name in self.attr:
            return self.attr[name]
        else:
            return None


    def get_join_keys(self, prefix, name):

        """ Reads the join keys of this component and a resource

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)

        """

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


# *****************************************************************************
class S3ResourceModel(object):


    """ Class to handle the compound resources model """


    def __init__(self, db):

        """ Constructor

            @param db: the database (DAL)

        """

        self.db = db
        self.components = {}
        self.config = Storage()
        self.methods = {}
        self.cmethods = {}


    # Configuration ===========================================================

    def configure(self, table, **attr):

        """ Updates the configuration of a resource

            @param table: the resource DB table
            @param attr: dict of attributes to update

        """

        cfg = self.config.get(table._tablename, Storage())
        cfg.update(attr)
        self.config[table._tablename] = cfg


    def get_config(self, table, key):

        """ Reads a configuration attribute of a resource

            @param table: the resource DB table
            @param key: the key (name) of the attribute

        """

        if table._tablename in self.config.keys():
            return self.config[table._tablename].get(key, None)
        else:
            return None


    def clear_config(self, table, *keys):

        """ Removes configuration attributes of a resource

            @param table: the resource DB table
            @param keys: keys of attributes to remove (maybe multiple)

        """

        if not keys:
            if table._tablename in self.config.keys():
                del self.config[table._tablename]
        else:
            if table._tablename in self.config.keys():
                for k in keys:
                    if k in self.config[table._tablename]:
                        del self.config[table._tablename][k]


    def add_component(self, prefix, name, **attr):

        """ Adds a component to the model

            @param prefix: prefix of the component name (=module name)
            @param name: name of the component (=without prefix)

        """

        assert "joinby" in attr, "Join key(s) must be defined."

        component = S3ResourceComponent(self.db, prefix, name, **attr)
        self.components[name] = component
        return component


    def get_component(self, prefix, name, component_name):

        """ Retrieves a component of a resource

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component (=without prefix)

        """

        if component_name in self.components and \
           not component_name == name:
            component = self.components[component_name]
            pkey, fkey = component.get_join_keys(prefix, name)
            if pkey:
                return (component, pkey, fkey)

        return (None, None, None)


    def get_components(self, prefix, name):

        """ Retrieves all components related to a resource

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)

        """

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

        """ Adds a custom method for a resource or component

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component (=without prefix)
            @param method: name of the method
            @param action: function to invoke for this method

        """

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

        """ Retrieves a custom method for a resource or component

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component (=without prefix)
            @param method: name of the method

        """

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

        """ Sets an attribute for a component

            @param component_name: name of the component (without prefix)
            @param name: name of the attribute
            @param value: value for the attribute

        """

        return self.components[component_name].set_attr(name, value)


    def get_attr(self, component_name, name):

        """ Retrieves an attribute value of a component

            @param component_name: name of the component (without prefix)
            @param name: name of the attribute

        """

        return self.components[component_name].get_attr(name)


# *****************************************************************************
class S3ResourceController(object):

    """ Resource controller class """

    RCVARS = "rcvars"
    ACTION = dict(
        create="create",
        read="read",
        update="update",
        delete="delete"
    )
    ROWSPERPAGE = 10

    MAX_DEPTH = 10


    def __init__(self, db,
                 domain=None,
                 base_url=None,
                 rpp=None,
                 gis=None,
                 messages=None,
                 cache=None):

        """ Constructor

            @param db: the database (DAL)
            @param domain: name of the current domain
            @param base_url: base URL of this instance
            @param rpp: rows-per-page for server-side pagination
            @param gis: the GIS toolkit to use
            @param messages: a function to retrieve message URLs tagged for a resource
            @param cache: the cache object

        """

        assert db is not None, "Database must not be None."
        self.db = db
        self.cache = cache

        self.error = None

        self.domain = domain
        self.base_url = base_url
        self.download_url = "%s/default/download" % base_url

        if rpp:
            self.ROWSPERPAGE = rpp

        self.model = S3ResourceModel(self.db)
        self.xml = S3XML(self.db, domain=domain, base_url=base_url, gis=gis, cache=cache)

        self.sync_resolve = None
        self.sync_log = None
        self.messages = None


    # Session helpers =========================================================

    def get_session(self, session, prefix, name):

        """ Reads the last record ID for a resource from a session

            @param session: the session store
            @param prefix: the prefix of the resource name (=module name)
            @param name: the name of the resource (=without prefix)

        """

        tablename = "%s_%s" % (prefix, name)
        if self.RCVARS in session and tablename in session[self.RCVARS]:
            return session[self.RCVARS][tablename]
        else:
            return None


    def store_session(self, session, prefix, name, id):

        """ Stores a record ID for a resource in a session

            @param session: the session store
            @param prefix: the prefix of the resource name (=module name)
            @param name: the name of the resource (=without prefix)
            @id: the ID to store

        """

        if self.RCVARS not in session:
            session[self.RCVARS] = Storage()
        if self.RCVARS in session:
            tablename = "%s_%s" % (prefix, name)
            session[self.RCVARS][tablename] = id

        return True # always return True to make this chainable


    def clear_session(self, session, prefix=None, name=None):

        """ Clears one or all record IDs stored in a session

            @param session: the session store
            @param prefix: the prefix of the resource name (=module name)
            @param name: the name of the resource (=without prefix)

        """

        if prefix and name:
            tablename = "%s_%s" % (prefix, name)
            if self.RCVARS in session and tablename in session[self.RCVARS]:
                del session[self.RCVARS][tablename]
        else:
            if self.RCVARS in session:
                del session[self.RCVARS]

        return True # always return True to make this chainable


    # Table helpers ===========================================================

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
                c = e.get(i[k], None)
                if c and i[k] in c:
                    continue
                if i[k] in d:
                    if not i[v] in d[i[k]]:
                        d[i[k]].append(i[v])
                else:
                    d[i[k]] = [i[v]]

        return d


    def __fields(self, table, skip=[]):

        """
            Finds all readable fields in a table and splits
            them into reference and non-reference fields

            @param table: the DB table
            @param skip: list of field names to skip

        """

        fields = filter(lambda f:
                        f != self.xml.UID and
                        f not in skip and
                        f not in self.xml.IGNORE_FIELDS,
                        table.fields)

        rfields = filter(lambda f:
                         str(table[f].type).startswith("reference") and
                         f not in self.xml.FIELDS_TO_ATTRIBUTES,
                         fields)

        dfields = filter(lambda f:
                         f not in rfields,
                         fields)

        return (rfields, dfields)

    # XML Export ==============================================================

    def export_xml(self, prefix, name, id,
                   joins=[],
                   filterby=None,
                   skip=[],
                   permit=None,
                   audit=None,
                   start=None,
                   limit=None,
                   marker=None,
                   msince=None,
                   show_urls=True,
                   dereference=True):

        """ Exports data as XML tree

            @param prefix: prefix of the resource name (=module name)
            @param name: resource name (=without prefix)
            @param id: ID of the record to export (may be None, single or list)
            @param joins: list of component joins to include in the export
            @param filterby: filter option
            @param skip: list of field names to skip
            @param permit: permit hook (function to check table permissions)
            @param audit: audit hook (function to audit table access)
            @param start: starting record (for server-side pagination)
            @param limit: page size (for server-side pagination)
            @marker: URL to override map marker URL in location references
            @msince: report only resources which have been modified since that datetime
            @show_urls: show resource URLs in <resource> elements
            @dereference: include referenced resources into the export

        """

        self.error = None

        resources = []
        tablename = "%s_%s" % (prefix, name)

        burl = show_urls and self.base_url or None
        if tablename not in self.db or \
           (permit and not permit(self.ACTION["read"], tablename)):
            return self.xml.root(resources, domain=self.domain, url=burl)

        table = self.db[tablename]
        (rfields, dfields) = self.__fields(table, skip=skip)

        # Master query
        if id and isinstance(id, (list, tuple)):
            query = (table.id.belongs(id))
        elif id is not None:
            query = (table.id == id)
        else:
            query = (table.id > 0)

        if "deleted" in table:
            query = (table.deleted == False) & query
        if filterby:
            query = (filterby) & query

        #results = self.db(query).count()

        # Server-side pagination
        if start is not None: # can't be 'if start': 0 is a valid value
            if not limit:
                limit = self.ROWSPERPAGE
            if limit <= 0:
                limit = 1
            if start < 0:
                start = 0
            limitby = (start, start + limit)
        else:
            limitby = None

        # Load primary records
        results = self.db(query).count()
        records = self.db(query).select(table.ALL, limitby=limitby) or []

        # Filter by permission
        if records and permit:
            records = filter(lambda r: permit(self.ACTION["read"],
                             tablename, record_id=r.id), records)
        if joins and permit:
            joins = filter(lambda j: permit(self.ACTION["read"],
                           j[0].tablename), joins)

        # Load component records
        cdata = {}
        crfields = {}
        cdfields = {}
        if records:
            for i in xrange(0, len(joins)):
                (c, pkey, fkey) = joins[i]
                pkeys = map(lambda r: r[pkey], records)
                cquery = (c.table[fkey].belongs(pkeys))
                if "deleted" in c.table.fields:
                    cquery = (c.table.deleted == False) & cquery
                if msince and "modified_on" in c.table.fields:
                    cquery = (c.table.modified_on >= msince) & cquery
                cdata[c.tablename] = self.db(cquery).select(c.table.ALL) or []
                _skip = [fkey,]
                if skip:
                    _skip.extend(skip)
                cfields = self.__fields(c.table, skip=_skip)
                crfields[c.tablename] = cfields[0]
                cdfields[c.tablename] = cfields[1]

        if self.base_url:
            url = "%s/%s/%s" % (self.base_url, prefix, name)
        else:
            url = "/%s/%s" % (prefix, name)
        exp_map = Storage()
        ref_map = []
        for i in xrange(0, len(records)):

            # Export primary record
            record = records[i]
            if audit:
                audit(self.ACTION["read"], prefix, name,
                      record=record.id, representation="xml")
            if show_urls:
                resource_url = "%s/%s" % (url, record.id)
            else:
                resource_url = None
            rmap = self.xml.rmap(table, record, rfields)
            resource = self.xml.element(table, record,
                                        fields=dfields,
                                        url=resource_url,
                                        download_url=self.download_url,
                                        marker=marker)
            self.xml.add_references(resource, rmap)
            self.xml.gis_encode(rmap,
                                download_url=self.download_url,
                                marker=marker)

            # Export components of this record
            r_url = "%s/%s" % (url, record.id)
            for j in xrange(0, len(joins)):
                (c, pkey, fkey) = joins[j]
                pkey = record[pkey]
                ctablename = c.tablename
                crecords = cdata[ctablename]
                crecords = filter(lambda r: r[fkey] == pkey, crecords)
                c_url = "%s/%s" % (r_url, c.name)
                for k in xrange(0, len(crecords)):
                    crecord = crecords[k]
                    if permit and \
                       not permit(self.ACTION["read"], ctablename, crecord.id):
                        continue
                    if audit:
                        audit(self.ACTION["read"], c.prefix, c.name,
                              record=crecord.id, representation="xml")
                    if show_urls:
                        resource_url = "%s/%s" % (c_url, crecord.id)
                    else:
                        resource_url = None
                    rmap = self.xml.rmap(c.table, crecord,
                                         crfields[ctablename])
                    cresource = self.xml.element(c.table, crecord,
                                                fields=cdfields[ctablename],
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

            if msince and "modified_on" in table.fields:
                mtime = record.get("modified_on", None)
                if mtime and mtime < msince and \
                   not len(resource.findall("resource")):
                    continue

            ref_map.extend(rmap)
            resources.append(resource)
            if exp_map.get(table._tablename, None):
                exp_map[table._tablename].append(record.id)
            else:
                exp_map[table._tablename] = [record.id]

        #results = len(resources)

        # Add referenced resources to the tree
        depth = dereference and self.MAX_DEPTH or 0
        while ref_map and depth:
            depth -= 1
            load_map = self.__directory(None, ref_map, "table", "id", e=exp_map)
            ref_map = []

            for tablename in load_map.keys():
                prefix, name = tablename.split("_", 1)
                if self.base_url:
                    url = "%s/%s/%s" % (self.base_url, prefix, name)
                else:
                    url = "/%s/%s" % (prefix, name)
                load_list = load_map[tablename]
                if permit:
                    if not permit(self.ACTION["read"], tablename):
                        continue
                    load_list = filter(lambda id:
                                permit(self.ACTION["read"], tablename, id),
                                load_list)
                    if not load_list:
                        continue
                table = self.db[tablename]
                (rfields, dfields) = self.__fields(table, skip=skip)
                query = (table.id.belongs(load_list))
                if "deleted" in table:
                    query = (table.deleted == False) & query
                records = self.db(query).select(table.ALL) or []
                for record in records:
                    if audit:
                        audit(self.ACTION["read"], prefix, name,
                              record=record.id, representation="xml")
                    rmap = self.xml.rmap(table, record, rfields)
                    if show_urls:
                        resource_url = "%s/%s" % (url, record.id)
                    else:
                        resource_url = None
                    resource = self.xml.element(table, record,
                                                fields=dfields,
                                                url=resource_url,
                                                download_url=self.download_url,
                                                marker=marker)
                    self.xml.add_references(resource, rmap)
                    self.xml.gis_encode(rmap,
                                        download_url=self.download_url,
                                        marker=marker)
                    resources.append(resource)
                    ref_map.extend(rmap)
                    if exp_map.get(tablename, None):
                        exp_map[tablename].append(record.id)
                    else:
                        exp_map[tablename] = [record.id]

        # Complete the tree
        return self.xml.tree(resources,
                             domain=self.domain,
                             url=burl,
                             results=results,
                             start=start,
                             limit=limit)


    # XML Import ==============================================================

    def vectorize(self, resource, element,
                  id=None,
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
        record = self.xml.record(table, element, validate=validate)

        mtime = element.get(self.xml.MTIME, None)
        if mtime:
            mtime, error = self.validate(table, None, self.xml.MTIME, mtime)
            if error:
                mtime = None

        if not record:
            self.error = S3XRC_VALIDATION_ERROR
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
        vector = S3Vector(self.db, prefix, name, id,
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
            vectors = self.vectorize(entry.get("resource"),
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


    def import_xml(self, prefix, name, id, tree,
                   joins=[],
                   skip_resource=False,
                   permit=None,
                   audit=None,
                   push_limit=None,
                   ignore_errors=False):

        """ Imports data from an element tree

            @param prefix: the prefix of the resource name (=module name)
            @param name: the resource name (=without prefix)
            @param id: the target record ID
            @param tree: the element tree
            @param joins: list of component joins to include
            @param skip_resource: skip the main resource record (currently unused)
            @param permit: permit hook (function to check table permissions)
            @param audit: audit hook (function to audit table access)
            @param ignore_errors: continue at errors (skip invalid elements)

        """

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
                db_record = self.db(table.id == id).select(table.ALL)[0]
            except:
                self.error = S3XRC_BAD_RECORD
                return False
        else:
            db_record = None

        if id and len(elements) > 1:
            if self.xml.UID in table:
                uid = db_record[self.xml.UID]
                for element in elements:
                    xuid = element.get(self.xml.UID)
                    if self.xml.domain_mapping:
                        xuid = self.xml.import_uid(xuid)
                    if xuid == uid:
                        elements = [element]
                        break
            if len(elements) > 1:
                self.error = S3XRC_NO_MATCH
                return False

        if joins is None:
            joins = []

        if push_limit is not None and \
           len(elements) > push_limit:
            self.error = S3XRC_NOT_PERMITTED
            return False

        # Import all matching elements
        imports = []
        directory = {}
        vmap = {} # Element<->Vector Map

        for i in xrange(0, len(elements)):
            element = elements[i]
            vectors = self.vectorize(tablename, element,
                                     id=id,
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

            # Mark as committed if requested
            # TODO: do not create new components if skip_resource
            #if skip_resource:
                #vector.committed = True

            # Import components
            for j in xrange(0, len(joins)):

                component, pkey, fkey = joins[j]
                celements = self.xml.select_resources(element,
                                                      component.tablename)

                if celements:
                    c_id = c_uid = None
                    if not component.attr.multiple:
                        if vector.id:
                            p = self.db(table.id == vector.id).select(
                                table[pkey], limitby=(0,1))
                            if p:
                                p = p[0][pkey]
                                fields = [component.table.id]
                                if self.xml.UID in component.table:
                                    fields.append(
                                        component.table[self.xml.UID])
                                query = (component.table[fkey] == p)
                                orig = self.db(quert).select(limitby=(0,1),
                                                             *fields)
                                if orig:
                                    c_id = orig[0].id
                                    if self.xml.UID in component.table:
                                        c_uid = orig[0][self.UID]

                        celements = [celements[0]]
                        if c_uid:
                            celements[0].set(self.xml.UID, c_uid)

                    for k in xrange(0, len(celements)):
                        celement = celements[k]
                        cvectors = self.vectorize(component.tablename,
                                                  celement,
                                                  validate=self.validate,
                                                  permit=permit,
                                                  audit=audit,
                                                  sync=self.sync_resolve,
                                                  log=self.sync_log,
                                                  tree=tree,
                                                  directory=directory,
                                                  vmap=vmap,
                                                  lookahead=True)
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


    # Model functions =========================================================

    def validate(self, table, record, fieldname, value):

        """ Validates a single value

            @param table: the DB table
            @param record: the existing DB record
            @param fieldname: name of the field
            @param value: value to check

        """

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


    def options_xml(self, prefix, name, joins=[]):

        """ Exports field options in a resource as element tree

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param joins: list of component joins to include

        """

        self.error = None
        options = self.xml.get_options(prefix, name, joins=joins)
        return self.xml.tree([options], domain=self.domain, url=self.base_url)


    # Search Simple ===========================================================

    def search_simple(self, table, fields=None, label=None, filterby=None):

        """ Simple search function for resources

            @param table: the DB table
            @param fields: list of fields to search for the label
            @param label: label to be found
            @param filterby: filter query for results

        """

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


# *****************************************************************************
class S3Vector(object):

    """ Helper class for data imports """

    METHOD = Storage(
        CREATE="create",
        UPDATE="update"
    )

    RESOLUTION = Storage(
        THIS="THIS",        # keep local instance
        OTHER="OTHER",      # import other instance
        NEWER="NEWER",      # import other only if newer
        #vote="VOTE"        # not yet implemented
    )

    UID = "uuid"
    MTIME = "modified_on"


    def __init__(self, db, prefix, name, id,
                 record=None,
                 element=None,
                 mtime=None,
                 rmap=None,
                 directory=None,
                 permit=None,
                 audit=None,
                 sync=None,
                 log=None,
                 onvalidation=None,
                 onaccept=None):

        """ Constructor

            @param db: the database (DAL)
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

        self.db=db
        self.prefix=prefix
        self.name=name

        self.tablename = "%s_%s" % (self.prefix, self.name)
        self.table = self.db[self.tablename]

        self.element=element
        self.record=record
        self.id=id

        if mtime:
            self.mtime = mtime
        else:
            self.mtime = datetime.datetime.utcnow()

        self.rmap=rmap

        self.components = []
        self.references = []
        self.update = []

        self.method = None
        self.strategy = [self.METHOD.CREATE, self.METHOD.UPDATE]

        self.resolution = self.RESOLUTION.OTHER
        self.default_resolution = self.RESOLUTION.THIS

        self.onvalidation=onvalidation
        self.onaccept=onaccept
        self.audit=audit
        self.sync=sync
        self.log=log

        self.accepted=True
        self.permitted=True
        self.committed=False

        uid = self.record.get(self.UID, None)
        if not self.id:
            self.id = 0
            self.method = permission = self.METHOD.CREATE
            if uid and self.UID in self.table:
                query = (self.table[self.UID] == uid)
                orig = self.db(query).select(self.table.id, limitby=(0, 1))
                if orig:
                    self.id = orig.first().id
                    self.method = permission = self.METHOD.UPDATE
        else:
            self.method = permission = self.METHOD.UPDATE
            if not self.db(self.table.id == id).count():
                self.id = 0
                self.method = permission = self.METHOD.CREATE
            # Unclear what this has once been good for, uncomment if necessary:
            #else:
                #if self.UID in self.record:
                    #del self.record[self.UID]

        # Do allow import to tables with these prefixes:
        if self.prefix in ("auth", "admin", "s3"):
            self.permitted=False

        # ...or check permission explicitly:
        elif permit and not \
           permit(permission, self.tablename, record_id=self.id):
            self.permitted=False

        # Once the vector has been created, update the entry in the directory
        uid = self.record.get(self.UID, None)
        if uid and \
           directory is not None and self.tablename in directory:
            entry = directory[self.tablename].get(uid, None)
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


    def commit(self):

        """ Commits the vector to the database """

        self.resolve() # Resolve references

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
                    self.onvalidation(form)
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
                        for f in self.record.keys():
                            r = self.get_resolution(f)
                            if r == self.RESOLUTION.THIS:
                                del self.record[f]
                            elif r == self.RESOLUTION.NEWER:
                                if this_mtime and \
                                   this_mtime > self.mtime:
                                    del self.record[f]

                    if len(self.record):
                        try:
                            self.record.update(deleted=False) # Undelete re-imported records!
                            success = self.db(self.table.id == self.id).update(**dict(self.record))
                        except: # TODO: propagate error to XML importer
                            return False
                        if success:
                            self.committed = True
                    else:
                        self.committed = True

                elif self.method == self.METHOD.CREATE:
                    # Create new record ---------------------------------------

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
                    if self.onaccept:
                        self.onaccept(form)

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


    def resolve(self):

        """ Resolve references of this record """

        if self.rmap:
            for r in self.rmap:
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
                        self.record[r.field] = id
                    else:
                        if r.field in self.record:
                            del self.record[r.field]
                        vector.update.append(dict(vector=self, field=r.field))


    def writeback(self, field, value):

        """ Update a field in the record

            @param field: field name
            @param value: value to write

        """

        if self.id and self.permitted:
            self.db(self.table.id == self.id).update(**{field:value})


# *****************************************************************************
class S3XML(object):

    """ XML+JSON toolkit for S3XRC """

    S3XRC_NAMESPACE = "http://eden.sahanafoundation.org/wiki/S3XRC"
    S3XRC = "{%s}" % S3XRC_NAMESPACE #: LXML namespace prefix
    NSMAP = {None: S3XRC_NAMESPACE} #: LXML default namespace

    CACHE_TTL = 5 # time-to-live of RAM cache for field representations

    UID = "uuid"
    MTIME = "modified_on"

    # GIS field names
    Lat = "lat"
    Lon = "lon"
    FeatureClass = "feature_class_id"
    #Marker = "marker_id"

    IGNORE_FIELDS = ["deleted", "id"]

    FIELDS_TO_ATTRIBUTES = [
            "created_on",
            "modified_on",
            "created_by",
            "modified_by",
            "uuid",
            "admin"]

    ATTRIBUTES_TO_FIELDS = ["admin"]

    TAG = Storage(
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

    ATTRIBUTE = Storage(
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
        marker="marker",
        sym="sym"
    )

    ACTION = Storage(
        create="create",
        read="read",
        update="update",
        delete="delete"
    )

    PREFIX = Storage(
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


    def __init__(self, db, domain=None, base_url=None, gis=None, cache=None):

        """ Constructor

            @param db: the database (DAL)
            @param domain: name of the current domain
            @param base_url: base URL of the current instance
            @param gis: GIS toolkit to use

        """

        self.db = db
        self.error = None
        self.domain = domain
        self.base_url = base_url
        self.domain_mapping = True
        self.gis = gis
        self.cache = cache

    # XML+XSLT tools ==========================================================

    def parse(self, source):

        """ Parse an XML source into an element tree

            @param source: the XML source

        """

        self.error = None

        try:
            parser = etree.XMLParser(no_network=False)
            result = etree.parse(source, parser)
            return result
        except:
            e = sys.exc_info()[1]
            self.error = e
            return None


    def transform(self, tree, template_path, **args):

        """ Transform an element tree with XSLT

            @param tree: the element tree
            @param template_path: pathname of the XSLT stylesheet
            @param args: dict of arguments to pass to the transformer

        """

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
                e = sys.exc_info()[1]
                self.error = e
                return None
        else:
            # Error parsing the XSL template
            return None


    def tostring(self, tree, pretty_print=False):

        """ Convert an element tree into XML as string

            @param tree: the element tree
            @param pretty_print: provide pretty formatted output

        """

        return etree.tostring(tree,
                              xml_declaration=True,
                              encoding="utf-8",
                              pretty_print=pretty_print)


    def tree(self, resources, domain=None, url=None,
             start=None, limit=None, results=None):

        """ Builds a tree from a list of elements

            @param resources: list of <resource> elements
            @param domain: name of the current domain
            @param url: url of the request
            @param start: the start record (in server-side pagination)
            @param limit: the page size (in server-side pagination)
            @param results: number of total available results

        """

        # For now we do not nsmap, because the default namespace cannot be
        # matched in XSLT templates (need explicit prefix) and thus this
        # would require a rework of all existing templates (which is
        # however useful)
        root = etree.Element(self.TAG.root) #, nsmap=self.NSMAP)

        root.set(self.ATTRIBUTE.success, str(False))

        if resources is not None:
            if resources:
                root.set(self.ATTRIBUTE.success, str(True))
            if start is not None:
                root.set(self.ATTRIBUTE.start, str(start))
            if limit is not None:
                root.set(self.ATTRIBUTE.limit, str(limit))
            if results is not None:
                root.set(self.ATTRIBUTE.results, str(results))
            root.extend(resources)

        if domain:
            root.set(self.ATTRIBUTE.domain, self.domain)

        if url:
            root.set(self.ATTRIBUTE.url, self.base_url)

        root.set(self.ATTRIBUTE.latmin,
                 str(self.gis.get_bounds()["min_lat"]))
        root.set(self.ATTRIBUTE.latmax,
                 str(self.gis.get_bounds()["max_lat"]))
        root.set(self.ATTRIBUTE.lonmin,
                 str(self.gis.get_bounds()["min_lon"]))
        root.set(self.ATTRIBUTE.lonmax,
                 str(self.gis.get_bounds()["max_lon"]))

        return etree.ElementTree(root)


    def xml_encode(self, obj):

        """ Encodes a Python string into an XML text node

            @param obj: string to encode

        """

        if obj:
            for (x,y) in self.PY2XML:
                obj = obj.replace(x, y)
        return obj


    def xml_decode(self, obj):

        """ Decodes an XML text node into a Python string

            @param obj: string to decode

        """

        if obj:
            for (x,y) in self.XML2PY:
                obj = obj.replace(y, x)
        return obj


    def export_uid(self, uid):

        """ Maps internal UUIDs to export format

            @param uid: the (internally used) UUID

        """

        if not self.domain:
            return uid
        x = uid.find("/")
        if x < 1 or x == len(uid)-1:
            return "%s/%s" % (self.domain, uid)
        else:
            return uid


    def import_uid(self, uid):

        """ Maps imported UUIDs to internal format

            @param uid: the (externally used) UUID

        """

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


    # Data export =============================================================

    def represent(self, table, f, v):

        """ Get the representation of a field value

            @param table: the database table
            @param f: the field name
            @param v: the value

        """

        text = str(table[f].represent(v)).decode("utf-8")
        # Filter out markup from text
        if "<" in text:
            try:
                markup = etree.XML(text)
                text = markup.xpath(".//text()")
                if text:
                    text = " ".join(text)
            except etree.XMLSyntaxError:
                pass
        text = self.xml_encode(text)
        return text


    def rmap(self, table, record, fields):

        """ Generates a reference map for a record

            @param table: the database table
            @param record: the record
            @param fields: list of reference field names in this table

        """

        reference_map = []

        for f in fields:
            id = record.get(f, None)
            if not id:
                continue
            uid = None

            ktablename = str(table[f].type)[10:]
            ktable = self.db[ktablename]

            if self.UID in ktable.fields:
                query = (ktable.id == id)
                if "deleted" in ktable:
                    query = (ktable.deleted == False) & query
                krecord = self.db(query).select(ktable[self.UID],
                                                limitby=(0, 1))
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
            value = text = self.xml_encode(str(
                           table[f].formatter(value)).decode("utf-8"))
            if table[f].represent:
                text = self.represent(table, f, value)

            reference_map.append(Storage(field=f,
                                         table=ktablename,
                                         id=id,
                                         uid=uid,
                                         text=text,
                                         value=value))

        return reference_map


    def add_references(self, element, rmap):

        """ Adds <reference> elements to a <resource>

            @param element: the <resource> element
            @param rmap: the reference map for the corresponding record

        """

        for i in xrange(0, len(rmap)):
            r = rmap[i]
            reference = etree.SubElement(element, self.TAG.reference)
            reference.set(self.ATTRIBUTE.field, r.field)
            reference.set(self.ATTRIBUTE.resource, r.table)
            if r.uid:
                reference.set(self.UID, r.uid )
                reference.text = r.text
            else:
                reference.set(self.ATTRIBUTE.value, r.value)
                # TODO: add in-line resource
            r.element = reference


    def gis_encode(self, rmap, download_url="", marker=None):

        """ GIS-encodes location references

            @param rmap: list of references to encode
            @param download_url: download URL of this instance
            @param marker: filename to override filenames in marker URLs

        """

        if not self.gis:
            return

        db = self.db

        references = filter(lambda r:
                            r.element is not None and \
                            self.Lat in self.db[r.table].fields and \
                            self.Lon in self.db[r.table].fields,
                            rmap)

        for i in xrange(0, len(references)):
            r = references[i]
            ktable = db[r.table]
            LatLon = db(ktable.id == r.id).select(ktable[self.Lat],
                                                  ktable[self.Lon],
                                                  ktable[self.FeatureClass],
                                                  limitby=(0, 1))
            if LatLon:
                LatLon = LatLon.first()
                if LatLon[self.Lat] is not None and \
                   LatLon[self.Lon] is not None:
                    r.element.set(self.ATTRIBUTE.lat,
                                  self.xml_encode("%.6f" % LatLon[self.Lat]))
                    r.element.set(self.ATTRIBUTE.lon,
                                  self.xml_encode("%.6f" % LatLon[self.Lon]))
                    # Lookup Marker (Icon)
                    if marker:
                        marker_url = "%s/gis_marker.image.%s.png" % \
                                     (download_url, marker)
                    else:
                        marker = self.gis.get_marker(r.value)
                        marker_url = "%s/%s" % (download_url, marker)
                    r.element.set(self.ATTRIBUTE.marker,
                                  self.xml_encode(marker_url))
                    # Lookup GPS Marker
                    symbol = None
                    fctbl = db.gis_feature_class
                    query = (fctbl.id == str(LatLon[self.FeatureClass]))
                    try:
                        symbol = db(query).select(fctbl.gps_marker,
                                                  limitby=(0, 1)).first().gps_marker
                    except:
                        # No Feature Class
                        pass
                    if not symbol:
                        symbol = "White Dot"
                    r.element.set(self.ATTRIBUTE.sym,
                                  self.xml_encode(symbol))

    def element(self, table, record,
                fields=[],
                url=None,
                download_url=None,
                marker=None):

        """ Creates an element from a Storage() record

            @param table: the database table
            @param record: the record
            @param fields: list of field names to include
            @param url: URL of the record
            @param download_url: download URL of the current instance
            @param marker: filename of the marker to override
                marker URLs in location references

        """

        if not download_url:
            download_url = ""

        resource = etree.Element(self.TAG.resource)
        resource.set(self.ATTRIBUTE.name, table._tablename)

        if self.UID in table.fields and self.UID in record:
            _value = str(table[self.UID].formatter(record[self.UID]))
            if self.domain_mapping:
                value = self.export_uid(_value)
            resource.set(self.UID, self.xml_encode(value))
            if table._tablename == "gis_location" and self.gis:
                # Look up the marker to display
                marker = self.gis.get_marker(_value)
                marker_url = "%s/%s" % (download_url, marker)
                resource.set(self.ATTRIBUTE.marker,
                                self.xml_encode(marker_url))
                # Look up the GPS Marker
                symbol = None
                try:
                    db = self.db
                    query = (db.gis_feature_class.id == record.feature_class_id)
                    symbol = db(query).select(limitby=(0, 1)).first().gps_marker
                except:
                    # No Feature Class
                    pass
                if not symbol:
                    symbol = "White Dot"
                resource.set(self.ATTRIBUTE.sym, self.xml_encode(symbol))

        for i in xrange(0, len(fields)):
            f = fields[i]
            v = record.get(f, None)
            if f not in table.fields or v is None:
                continue

            text = value = self.xml_encode(
                           str(table[f].formatter(v)).decode("utf-8"))

            if table[f].represent:
                text = self.represent(table, f, v)

            fieldtype = str(table[f].type)

            if f in self.FIELDS_TO_ATTRIBUTES:
                resource.set(f, text)

            elif fieldtype == "upload":
                data = etree.SubElement(resource, self.TAG.data)
                data.set(self.ATTRIBUTE.field, f)
                data.text = "%s/%s" % (download_url, value)

            elif fieldtype == "password":
                # Do not export password fields
                continue

            elif fieldtype == "blob":
                # Not implemented yet
                continue

            else:
                data = etree.SubElement(resource, self.TAG.data)
                data.set(self.ATTRIBUTE.field, f)
                if table[f].represent:
                    data.set(self.ATTRIBUTE.value, value )
                data.text = text

        if url:
            resource.set(self.ATTRIBUTE.url, url)

        return resource


    # Data import =============================================================

    def select_resources(self, tree, tablename):

        """ Selects resources from an element tree

            @param tree: the element tree
            @param tablename: table name to search for

        """

        resources = []

        if isinstance(tree, etree._ElementTree):
            root = tree.getroot()
            if not root.tag == self.TAG.root:
                return resources
        else:
            root = tree

        if root is None or not len(root):
            return resources

        expr = './%s[@%s="%s"]' % (
               self.TAG.resource,
               self.ATTRIBUTE.name,
               tablename)

        resources = root.xpath(expr)
        return resources


    def lookahead(self, table, element, fields, tree=None, directory=None):

        """ Resolves references in XML resources

            @param table: the database table
            @param element: the element to resolve
            @param fields: fields to check for references
            @param tree: the element tree of the input source
            @param directory: the resource directory of the input tree

        """

        reference_list = []
        references = element.findall("reference")

        for r in references:
            field = r.get(self.ATTRIBUTE.field, None)
            if field and field in fields:
                resource = r.get(self.ATTRIBUTE.resource, None)
                if not resource:
                    continue
                table = self.db.get(resource, None)
                if not table:
                    continue

                id = None
                _uid = uid = r.get(self.UID, None)
                entry = None

                # If no UUID, try to find the reference in-line
                relement = None
                if not uid:
                    expr = './/%s[@%s="%s"]' % (
                        self.TAG.resource,
                        self.ATTRIBUTE.name, resource)
                    relements = r.xpath(expr)
                    if relements:
                        relement = relements[0]
                        _uid = uid = r.get(self.UID, None)

                if uid:
                    if self.domain_mapping:
                        uid = self.import_uid(uid)

                    # Check if this resource is already in the directory:
                    entry = None
                    if directory is not None and resource in directory:
                        entry = directory[resource].get(uid, None)

                    # Otherwise:
                    if not entry:
                        # Find the corresponding element in the tree
                        if tree and not relement:
                            expr = './/%s[@%s="%s" and @%s="%s"]' % (
                                   self.TAG.resource,
                                   self.ATTRIBUTE.name, resource,
                                   self.UID, _uid)
                            relements = tree.getroot().xpath(expr)
                            if relements:
                                relement = relements[0]

                        # Find the corresponding table record
                        if self.UID in table:
                            set = self.db(table[self.UID] == uid)
                            record = set.select(table.id, limitby=(0, 1)).first()
                            if record:
                                id = record.id

                # Update the entry
                if not entry:
                    entry = dict(vector=None)
                entry.update(resource=resource, element=relement, uid=uid, id=id)

                if uid:
                    # Add this entry to the directory
                    if directory is not None:
                        if resource not in directory:
                            directory[resource] = {}
                        if _uid not in directory[resource]:
                            directory[resource][uid] = entry

                # Add this entry to the reference list
                reference_list.append(Storage(field=field, entry=entry))

        return reference_list


    def record(self, table, element, validate=None, skip=[]):

        """ Creates a Storage() record from an element and validates it

            @param table: the database table
            @param element: the element
            @param validate: validate hook (function to validate fields)
            @param skip: fields to skip

        """

        valid = True
        record = Storage()
        original = None

        if self.UID in table.fields and self.UID not in skip:
            uid = element.get(self.UID, None)
            if uid:
                if self.domain_mapping:
                    uid = self.import_uid(uid)
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
                v = value = self.xml_decode(element.get(f, None))
                if value is not None:
                    if validate is not None:
                        if not isinstance(value, (str, unicode)):
                            v = str(value)
                        (value, error) = validate(table, original, f, v)
                        if error:
                            element.set(self.ATTRIBUTE.error,
                                        "%s: %s" % (f, error))
                            valid = False
                            continue
                    record[f]=value

        for child in element:
            if child.tag == self.TAG.data:
                f = child.get(self.ATTRIBUTE.field, None)
                if not f or f not in table.fields:
                    continue
                if f in self.IGNORE_FIELDS or f in skip:
                    continue

                field_type = str(table[f].type)
                if field_type in ("id", "upload", "blob", "password") or \
                   field_type.startswith("reference"):
                    continue

                value = child.get(self.ATTRIBUTE.value, None)
                value = self.xml_decode(value)

                if field_type == 'boolean':
                    if value and value in ["True", "true"]:
                        value = True
                    else:
                        value = False
                if value is None:
                    value = self.xml_decode(child.text)
                if value == "" and not field_type == "string":
                    value = None
                if value is None:
                    value = table[f].default
                if value is None and field_type == "string":
                    value = ""

                if value is not None:
                    if validate is not None:
                        if not isinstance(value, basestring):
                            v = str(value)
                        else:
                            v = value
                        (value, error) = validate(table, original, f, v)
                        child.set(self.ATTRIBUTE.value, v)
                        if error:
                            child.set(self.ATTRIBUTE.error, "%s: %s" % (f, error))
                            valid = False
                            continue
                    record[f] = value

        if valid:
            return record
        else:
            return None


    # Data model helpers ======================================================

    def get_field_options(self, table, fieldname):

        """ Reads all options for a field

            @param table: the database table
            @param fieldname: the name of the field

        """

        select = etree.Element(self.TAG.select)

        if fieldname in table.fields:
            field = table[fieldname]
        else:
            return select

        requires = field.requires
        select.set(self.TAG.field, fieldname)
        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        if requires:
            r = requires[0]
            options = []
            if isinstance(r, (IS_NULL_OR, IS_EMPTY_OR)) and hasattr(r.other, "options"):
                #null = etree.SubElement(select, self.TAG.option)
                #null.set(self.ATTRIBUTE.value, "")
                #null.text = ""
                options = r.other.options()
            elif hasattr(r, "options"):
                options = r.options()
            for (value, text) in options:
                value = self.xml_encode(str(value).decode("utf-8"))
                text = self.xml_encode(str(text).decode("utf-8"))
                option = etree.SubElement(select, self.TAG.option)
                option.set(self.ATTRIBUTE.value, value)
                option.text = text

        return select


    def get_options(self, prefix, name, joins=[]):

        """ Gets all field options for a resource

            @param prefix: prefix of the resource name (=module name)
            @param name: the resource name (=without prefix)
            @param joins: list of component joins to include

        """

        resource = "%s_%s" % (prefix, name)

        options = etree.Element(self.TAG.options)
        options.set(self.ATTRIBUTE.resource, resource)

        if resource in self.db:
            table = self.db[resource]
            for f in table.fields:
                select = self.get_field_options(table, f)
                if select is not None and len(select):
                    options.append(select)
            for j in joins:
                component = j[0]
                coptions = etree.Element(self.TAG.options)
                coptions.set(self.ATTRIBUTE.resource, component.tablename)
                for f in component.table.fields:
                    select = self.get_field_options(component.table, f)
                    if select is not None and len(select):
                        coptions.append(select)
                options.append(coptions)

        return options


    # JSON toolkit ============================================================

    def __json2element(self, key, value, native=False):

        """ Converts a data field from JSON into an element

            @param key: key (field name)
            @param name: value for the field

        """

        if isinstance(value, dict):
            return self.__obj2element(key, value, native=native)

        elif isinstance(value, (list, tuple)):
            if not key == self.TAG.item:
                _list = etree.Element(key)
            else:
                _list = etree.Element(self.TAG.list)
            for obj in value:
                item = self.__json2element(self.TAG.item, obj,
                                           native=native)
                _list.append(item)
            return _list

        else:
            if native:
                element = etree.Element(self.TAG.data)
                element.set(self.ATTRIBUTE.field, key)
            else:
                element = etree.Element(key)
            if not isinstance(value, (str, unicode)):
                value = str(value)
            element.text = self.xml_encode(value)
            return element


    def __obj2element(self, tag, obj, native=False):

        """ Converts a JSON object into an element

            @param tag: tag name for the element
            @param obj: the JSON object
            @param native: use native mode for attributes

        """

        prefix = name = resource = field = None

        if not tag:
            tag = self.TAG.object

        elif native:
            if tag.startswith(self.PREFIX.reference):
                field = tag[len(self.PREFIX.reference) + 1:]
                tag = self.TAG.reference
            elif tag.startswith(self.PREFIX.options):
                resource = tag[len(self.PREFIX.options) + 1:]
                tag = self.TAG.options
            elif tag.startswith(self.PREFIX.resource):
                resource = tag[len(self.PREFIX.resource) + 1:]
                tag = self.TAG.resource
            elif not tag == self.TAG.root:
                field = tag
                tag = self.TAG.data

        element = etree.Element(tag)

        if native:
            if resource:
                if tag == self.TAG.resource:
                    element.set(self.ATTRIBUTE.name, resource)
                else:
                    element.set(self.ATTRIBUTE.resource, resource)
            if field:
                element.set(self.ATTRIBUTE.field, field)

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
                if k == self.PREFIX.text:
                    element.text = self.xml_encode(m)
                elif k.startswith(self.PREFIX.attribute):
                    a = k[len(self.PREFIX.attribute):]
                    element.set(a, self.xml_encode(m))
                else:
                    child = self.__json2element(k, m, native=native)
                    element.append(child)

        return element


    def json2tree(self, source, format=None):

        """ Converts JSON into an element tree

            @param source: the JSON source
            @param format: name of the XML root element

        """

        try:
            root_dict = json.load(source)
        except (ValueError,):
            e = sys.exc_info()[1]
            raise HTTP(400, body=self.json_message(False, 400, e))

        native=False

        if not format:
            format=self.TAG.root
            native=True

        if root_dict and isinstance(root_dict, dict):
            root = self.__obj2element(format, root_dict, native=native)
            if root:
                return etree.ElementTree(root)

        return None


    def __element2json(self, element, native=False):

        """ Converts an element into JSON

            @param element: the element
            @param native: use native mode for attributes

        """

        if element.tag == self.TAG.list:
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
                    if tag == self.TAG.resource:
                        resource = child.get(self.ATTRIBUTE.name)
                        tag = "%s_%s" % (self.PREFIX.resource, resource)
                        collapse = False
                    elif tag == self.TAG.options:
                        resource = child.get(self.ATTRIBUTE.resource)
                        tag = "%s_%s" % (self.PREFIX.options, resource)
                    elif tag == self.TAG.reference:
                        tag = "%s_%s" % (self.PREFIX.reference,
                                         child.get(self.ATTRIBUTE.field))
                    elif tag == self.TAG.data:
                        tag = child.get(self.ATTRIBUTE.field)
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
                    if a == self.ATTRIBUTE.name and \
                       element.tag == self.TAG.resource:
                        continue
                    if a == self.ATTRIBUTE.resource and \
                       element.tag == self.TAG.options:
                        continue
                    if a == self.ATTRIBUTE.field and \
                    element.tag in (self.TAG.data, self.TAG.reference):
                        continue
                obj[self.PREFIX.attribute + a] = \
                    self.xml_decode(attributes[a])

            if element.text:
                obj[self.PREFIX.text] = self.xml_decode(element.text)

            if len(obj) == 1 and obj.keys()[0] in \
               (self.PREFIX.text, self.TAG.item, self.TAG.list):
                obj = obj[obj.keys()[0]]

            return obj


    def tree2json(self, tree, pretty_print=False):

        """ Converts an element tree into JSON

            @param tree: the element tree
            @param pretty_print: provide pretty formatted output

        """

        root = tree.getroot()

        if root.tag == self.TAG.root:
            native = True
        else:
            native = False

        root_dict = self.__element2json(root, native=native)

        if pretty_print:
            js = json.dumps(root_dict, indent=4)
            return "\n".join([l.rstrip() for l in js.splitlines()])
        else:
            return json.dumps(root_dict)


    def json_message(self,
                     success=True,
                     status_code="200",
                     message=None,
                     tree=None):

        """ Provide a nicely-formatted JSON Message

            @param success: action succeeded or failed
            @param status_code: the HTTP status code
            @param message: the message text
            @param tree: result tree to enclose

        """

        if success:
            status='"status": "success"'
        else:
            status='"status": "failed"'

        code = '"statuscode": "%s"' % status_code

        if not success:
            if message:
                return '{%s, %s, "message": "%s", "tree": %s }' % \
                       (status, code, message, tree)
            else:
                return '{%s, %s, "tree": %s }' % \
                       (status, code, tree)
        else:
            if message:
                return '{%s, %s, "message": "%s"}' % \
                       (status, code, message)
            else:
                return '{%s, %s}' % \
                       (status, code)

# *****************************************************************************
