# -*- coding: utf-8 -*-

""" S3XRC Resource Framework - Search Extensions

    @version: 2.2.9

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}
    @requires: U{B{I{ReportLab}} <http://www.reportlab.com/software/opensource>}
    @requires: U{B{I{Geraldo}} <http://www.geraldoreports.org>}
    @requires: U{B{I{Xlwt}} <http://pypi.python.org/pypi/xlwt>}

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

from gluon.http import HTTP

from s3crud import S3MethodHandler

# *****************************************************************************
class S3Search(S3MethodHandler):
    """
        Search MethodHandler for S3CRUD

        @ToDo: Support components
    """

    def respond(self, r, **attr):

        """
            Responder

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @returns: output object to send to the view
        """

        # Get environment
        db = self.db
        request = self.request
        response = self.response

        s3xrc = self.manager
        resource = self.resource
        table = self.table
        representation = r.representation

        # Query comes in pre-filtered to accessible & deletion_status

        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        if representation == "json":

            _vars = request.vars

            output = None

            # JQueryUI Autocomplete uses "term" instead of "value"
            # (old JQuery Autocomplete uses "q" instead of "value")
            value = _vars.value or _vars.term or _vars.q or None

            # We want to do case-insensitive searches
            # (default anyway on MySQL/SQLite, but not PostgreSQL)
            value = value.lower()

            limit = int(_vars.limit or 0)

            if _vars.field and _vars.filter and value:
                fieldname = str.lower(_vars.field)
                field = table[fieldname]

                # Default fields to return
                fields = [table.id, field]

                filter = _vars.filter
                if filter == "~":
                    # Normal single-field Autocomplete
                    query = (field.lower().like("%" + value + "%"))

                elif filter == "=":
                    if field.type.split(" ")[0] in ["reference", "id", "float", "integer"]:
                        # Numeric, e.g. Organisations' offices_by_org
                        query = (field == value)
                    else:
                        # Text
                        query = (field.lower() == value)

                elif filter == "<":
                    query = (field < value)

                elif filter == ">":
                    query = (field > value)

                else:
                    output = s3xrc.xml.json_message(False, 400, "Unsupported filter! Supported filters: ~, =, <, >")
                    raise HTTP(400, body=output)

                resource.add_filter(query)
                resource.load(start=0, limit=limit)
                output = resource.exporter.sjson(resource, fields=fields)

                response.headers["Content-Type"] = "text/json"
                return output

            else:
                output = s3xrc.xml.json_message(False, 400, "Missing options! Require: field, filter & value")
                raise HTTP(400, body=output)

        #elif r.interactive:
            # @ToDo: merge with search_simple

        else:
            # Only JSON supported
            raise HTTP(501, body=BADFORMAT)

# *****************************************************************************
class S3LocationSearch(S3Search):
    """
        Location-Specific Searches
        - just supports JSON format

        @ToDo: Support Components
    """

    def respond(self, r, **attr):
        """
            Responder

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @returns: output object to send to the view
        """

        # Get environment
        db = self.db
        request = self.request
        response = self.response

        s3xrc = self.manager
        gis = s3xrc.gis
        resource = self.resource
        table = self.table
        representation = r.representation

        # Query comes in pre-filtered to accessible & deletion_status

        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        if representation == "json":

            _vars = request.vars

            output = None

            # JQueryUI Autocomplete uses "term" instead of "value"
            # (old JQuery Autocomplete uses "q" instead of "value")
            value = _vars.value or _vars.term or _vars.q or None

            # We want to do case-insensitive searches
            # (default anyway on MySQL/SQLite, but not PostgreSQL)
            value = value.lower()

            limit = int(_vars.limit or 0)

            if _vars.field and _vars.filter and value:
                fieldname = str.lower(_vars.field)
                field = table[fieldname]

                # Default fields to return
                fields = [table.id, table.name, table.level]

                # Optional fields
                if "parent" in _vars and _vars.parent:
                    if _vars.parent == "null":
                        parent = None
                    else:
                        parent = int(_vars.parent)
                else:
                    parent = None

                if "exclude_field" in _vars:
                    exclude_field = str.lower(_vars.exclude_field)
                    if "exclude_value" in _vars:
                        exclude_value = str.lower(_vars.exclude_value)
                    else:
                        exclude_value = None
                else:
                    exclude_field = None
                    exclude_value = None

                limit = int(_vars.limit or 0)

                filter = _vars.filter
                if filter == "~":
                    if parent:
                        # gis_location hierarchical search
                        # NB Currently not used - we allow people to search freely across all the hierarchy
                        # SQL Filter is immediate children only so need slow lookup
                        #query = query & (table.parent == parent) & \
                        #                (field.like("%" + value + "%"))
                        children = gis.get_children(parent)
                        children = children.find(lambda row: value in str.lower(row.name))
                        output = children.json()
                        response.headers["Content-Type"] = "text/json"
                        return output

                    elif exclude_field and exclude_value:
                        # gis_location hierarchical search
                        # Filter out poor-quality data, such as from Ushahidi
                        query = (field.lower().like("%" + value + "%")) & \
                                (table[exclude_field].lower() != exclude_value)

                    else:
                        # Normal single-field
                        query = (field.lower().like("%" + value + "%"))

                elif filter == "=":
                    if field.type.split(" ")[0] in ["reference", "id", "float", "integer"]:
                        # Numeric, e.g. Organisations' offices_by_org
                        query = (field == value)
                    else:
                        # Text
                        if value == "nullnone":
                            # i.e. Location Selector
                            query = (field == None)
                        else:
                            query = (field.lower() == value)

                    if parent:
                        # i.e. gis_location hierarchical search
                        resource.add_filter(query)
                        query = (table.parent == parent)

                    fields = [table.id, table.name, table.level, table.uuid, table.parent, table.lat, table.lon, table.addr_street]

                elif filter == "<":
                    query = (field < value)

                elif filter == ">":
                    query = (field > value)

                else:
                    output = s3xrc.xml.json_message(False, 400, "Unsupported filter! Supported filters: ~, =, <, >")
                    raise HTTP(400, body=output)

            resource.add_filter(query)
            resource.load(start=0, limit=limit)
            output = resource.exporter.sjson(resource, fields=fields)

            response.headers["Content-Type"] = "text/json"
            return output

        #elif r.interactive:
            # @ToDo: merge with search_simple

        else:
            # Only JSON supported
            raise HTTP(501, body=BADFORMAT)

# *****************************************************************************
class S3PersonSearch(S3Search):
    """
        Person-Specific Searches
        - just supports JSON format

        @ToDo: Support components
    """

    def respond(self, r, **attr):

        """
            Responder

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @returns: output object to send to the view
        """

        # Get environment
        db = self.db
        request = self.request
        response = self.response

        s3xrc = self.manager
        resource = self.resource
        table = self.table
        representation = r.representation

        # Query comes in pre-filtered to accessible & deletion_status

        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        if representation == "json":

            _vars = request.vars

            output = None

            # JQueryUI Autocomplete uses "term" instead of "value"
            # (old JQuery Autocomplete uses "q" instead of "value")
            value = _vars.value or _vars.term or _vars.q or None

            # We want to do case-insensitive searches
            # (default anyway on MySQL/SQLite, but not PostgreSQL)
            value = value.lower()

            limit = int(_vars.limit or 0)

            if _vars.field and _vars.filter and value:
                fieldname = str.lower(_vars.field)
                field = table[fieldname]

                # Default fields to return
                fields = [table.id, field]

                # Optional fields (PR only)
                if "field2" in _vars:
                    fieldname2 = str.lower(_vars.field2)
                else:
                    fieldname2 = None
                if "field3" in _vars:
                    fieldname3 = str.lower(_vars.field3)
                else:
                    fieldname3 = None

                limit = int(_vars.limit or 0)

                filter = _vars.filter
                if filter == "~":
                    if fieldname2 and fieldname3:
                        # pr_person Autocomplete
                        if " " in value:
                            value1, value2 = value.split(" ", 1)
                            query = (field.lower().like("%" + value1 + "%")) & \
                                    (table[fieldname2].lower().like("%" + value2 + "%")) | \
                                    (table[fieldname3].lower().like("%" + value2 + "%"))
                        else:
                            query = ((field.lower().like("%" + value + "%")) | \
                                    (table[fieldname2].lower().like("%" + value + "%")) | \
                                    (table[fieldname3].lower().like("%" + value + "%")))

                        fields = [table.id, field, table[fieldname2], table[fieldname3]]

                    else:
                        # Normal single-field Autocomplete
                        query = (field.lower().like("%" + value + "%"))

                elif filter == "=":
                    if field.type.split(" ")[0] in ["reference", "id", "float", "integer"]:
                        # Numeric, e.g. Organisations' offices_by_org
                        query = (field == value)
                    else:
                        # Text
                        query = (field.lower() == value)

                elif filter == "<":
                    query = (field < value)

                elif filter == ">":
                    query = (field > value)

                else:
                    output = s3xrc.xml.json_message(False, 400, "Unsupported filter! Supported filters: ~, =, <, >")
                    raise HTTP(400, body=output)

            resource.add_filter(query)
            resource.load(start=0, limit=limit)
            output = resource.exporter.sjson(resource, fields=fields)

            response.headers["Content-Type"] = "text/json"
            return output

        #elif r.interactive:
            # @ToDo: merge with search_simple

        else:
            # Only JSON supported
            raise HTTP(501, body=BADFORMAT)

