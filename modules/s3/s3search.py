# -*- coding: utf-8 -*-

""" RESTful Search Methods

    @author: Fran Boon <fran[at]aidiq.com>
    @author: Dominic König <dominic[at]aidiq.com>

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2011 (c) Sahana Software Foundation
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
from gluon.html import *

from s3rest import S3Method
from s3crud import S3CRUD

__all__ = ["S3SearchOption",
           "S3Find",
           "S3Search",
           "S3LocationSearch",
           "S3PersonSearch"]

# *****************************************************************************
class S3SearchWidget(object):
    """
    Search Widget for interactive search (base class)

    """

    def __init__(self, field, **attr):
        """
        Configures the search option

        @param field: name(s) of the fields to search in

        @keyword label: a label for the search widget
        @keyword comment: a comment for the search widget

        """

        self.other = None

        self.fields = fields
        self.attr = Storage(attr)


    def widget(self, table, vars, **attr):
        """
        Returns the widget

        @param table: the table to search in
        @param vars: the URL GET variables as dict
        @param attr: HTML attributes for the widget container

        """
        raise NotImplementedError


    def query(self, table, value):
        """
        Returns a sub-query for this search option

        @param table: the table to search in
        @param value: the value returned from the widget

        """
        raise NotImplementedError


    def __and__(self, other):

        raise NotImplementedError

    def __or__(self, other):

        raise NotImplementedError


# *****************************************************************************
class S3SearchSimple(S3SearchWidget):
    """
    Simple full-text search widget

    """

    def widget(self, table, vars, **attr):
        """
        Returns a widget for this search option

        @param table: the table to search in
        @param vars: the URL GET variables as dict
        @param attr: HTML attributes for the widget container

        """
        raise NotImplementedError


    def query(self, table, value):
        """
        Returns a sub-query for this search option

        @param table: the table to search in
        @param value: the value returned from the widget

        """
        raise NotImplementedError


# *****************************************************************************
class S3SearchMatchWidget(S3SearchWidget):
    """
    String-search widget

    """

    def widget(self, table, vars, **attr):
        """
        Returns a widget for this search option

        @param table: the table to search in
        @param vars: the URL GET variables as dict
        @param attr: HTML attributes for the widget container

        """
        raise NotImplementedError


    def query(self, table, value):
        """
        Returns a sub-query for this search option

        @param table: the table to search in
        @param value: the value returned from the widget

        """
        raise NotImplementedError


# *****************************************************************************
class S3SearchMinMaxWidget(S3SearchWidget):
    """
    Min/Max search widget for numeric fields

    """

    def widget(self, table, vars, **attr):
        """
        Returns a widget for this search option

        @param table: the table to search in
        @param vars: the URL GET variables as dict
        @param attr: HTML attributes for the widget container

        """
        raise NotImplementedError


    def query(self, table, value):
        """
        Returns a sub-query for this search option

        @param table: the table to search in
        @param value: the value returned from the widget

        """
        raise NotImplementedError


# *****************************************************************************
class S3SearchSelectWidget(S3SearchWidget):
    """
    Option select widget for option or boolean fields

    """

    def widget(self, table, vars, **attr):
        """
        Returns a widget for this search option

        @param table: the table to search in
        @param vars: the URL GET variables as dict
        @param attr: HTML attributes for the widget container

        """
        raise NotImplementedError


    def query(self, table, value):
        """
        Returns a sub-query for this search option

        @param table: the table to search in
        @param value: the value returned from the widget

        """
        raise NotImplementedError


# *****************************************************************************
class S3SearchLocationWidget(S3SearchWidget):
    """
    Interactive location search widget

    """

    def widget(self, table, vars, **attr):
        """
        Returns a widget for this search option

        @param table: the table to search in
        @param vars: the URL GET variables as dict
        @param attr: HTML attributes for the widget container

        """
        raise NotImplementedError


    def query(self, table, value):
        """
        Returns a sub-query for this search option

        @param table: the table to search in
        @param value: the value returned from the widget

        """
        raise NotImplementedError


# *****************************************************************************
class S3Find(S3CRUD):
    """
    RESTful Search Method for S3Resources

    """

    def __init__(self, simple=None, advanced=None, any=False):
        """
        Constructor

        @param simple: the widgets for the simple search form as list
        @param advanced: the widgets for the advanced search form as list
        @param any: match "any of" (True) or "all of" (False) the options
                    in advanced search

        """

        S3CRUD.__init__(self)
        self.__simple = simple
        self.__advanced = advanced
        self.__any = any

        if self.__simple or self.__advanced:
            self.__interactive = True
        else:
            self.__interactive = False


    def apply_method(self, r, **attr):
        """
        Entry point to apply search method to S3Requests

        @param r: the S3Request
        @param attr: request attributes

        """

        raise NotImplementedError


# *****************************************************************************
class S3Search(S3CRUD):
    """
    RESTful Search Method for S3Resources

    """

    def __init__(self, label=None, comment=None, fields=None):
        """
        Constructor

        """

        S3CRUD.__init__(self)
        self.__label = label
        self.__comment = comment
        self.__fields = fields

        if self.__fields:
            self.interactive_search = True
        else:
            self.interactive_search = False


    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
        Entry point to apply search method to S3Requests

        @param r: the S3Request
        @param attr: request attributes

        """

        format = r.representation

        if r.interactive and self.__fields:
            return self.search_interactive(r, **attr)
        elif format == "aadata" and self.__fields:
            return self.select(r, **attr)
        elif format == "json":
            return self.search_json(r, **attr)
        else:
            raise HTTP(501, body=self.manager.ERROR.BAD_FORMAT)

        return dict()


    # -------------------------------------------------------------------------
    def search_json(self, r, **attr):
        """
        Legacy JSON search method (for autocomplete-widgets)

        @param r: the S3Request
        @param attr: request attributes

        """

        xml = self.manager.xml

        request = self.request
        response = self.response

        resource = self.resource
        table = self.table

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
                output = xml.json_message(False, 400, "Unsupported filter! Supported filters: ~, =, <, >")
                raise HTTP(400, body=output)

            resource.add_filter(query)
            output = resource.exporter.json(resource, start=0, limit=limit,
                                            fields=fields, orderby=field)
            response.headers["Content-Type"] = "text/json"

        else:
            output = xml.json_message(False, 400, "Missing options! Require: field, filter & value")
            raise HTTP(400, body=output)

        return output


    # -------------------------------------------------------------------------
    def search_interactive(self, r, **attr):
        """
        Simple full-text search method

        @param r: the S3Request
        @param attr: request attributes

        """

        # Get environment
        session = self.session
        request = self.request
        response = self.response
        resource = self.resource
        table = self.table
        tablename = self.tablename
        T = self.manager.T

        # Get representation
        representation = r.representation

        # Initialize output
        output = dict()

        # Get table-specific parameters
        sortby = self._config("sortby", [[1,'asc']])
        orderby = self._config("orderby", None)
        list_fields = self._config("list_fields")

        # GET vars
        vars = request.get_vars

        form = FORM(TABLE(TR("%s: " % self.__label,
                                INPUT(_type="text", _name="label", _size="40"),
                                DIV(DIV(_class="tooltip",
                                        _title="%s|%s" % (self.__label,
                                                        self.__comment)))),
                            TR("", INPUT(_type="submit",
                                        _value=T("Search")))))
        output.update(form=form)

        if form.accepts(request.vars, session, keepvalues=True):
            if form.vars.label == "":
                form.vars.label = "%"
            results = resource.search_simple(fields=self.__fields,
                                             label=form.vars.label,
                                             filterby=response.s3.filter)
            if results:
                linkto = self._linkto(r)
                if not list_fields:
                    fields = resource.readable_fields()
                else:
                    fields = [table[f]
                                for f in list_fields if f in table.fields]
                if not fields:
                    fields = []
                if fields[0].name != table.fields[0]:
                    fields.insert(0, table[table.fields[0]])
                resource.build_query(id=results)
                items = self.sqltable(fields=fields,
                                      orderby=orderby,
                                      linkto=linkto,
                                      download_url=self.download_url,
                                      format=representation)
                if request.post_vars.label:
                    session.s3.filter = {"%s.id" % resource.name:
                                        ",".join(map(str,results))}
                else:
                    session.s3.filter = None
            else:
                items = T("No matching records found.")
            output.update(items=items, sortby=sortby)

            # Add-button
            buttons = self.insert_buttons(r, "add")
            if buttons:
                output.update(buttons)

        # Title and subtitle
        title = self.crud_string(tablename, "title_search")
        subtitle = T("Matching Records")
        output.update(title=title, subtitle=subtitle)

        # View
        response.view = "search.html"
        return output


# *****************************************************************************
class S3LocationSearch(S3Search):
    """
    Search method with specifics for location records (hierarchy search)

    """

    def search_json(self, r, **attr):
        """
        Legacy JSON search method (for autocomplete-widgets)

        @param r: the S3Request
        @param attr: request attributes

        """

        xml = self.manager.xml
        gis = self.manager.gis

        output = None
        request = self.request
        response = self.response
        resource = self.resource
        table = self.table

        # Query comes in pre-filtered to accessible & deletion_status
        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        _vars = request.vars

        # JQueryUI Autocomplete uses "term" instead of "value"
        # (old JQuery Autocomplete uses "q" instead of "value")
        value = _vars.value or _vars.term or _vars.q or None

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        value = value.lower()

        if _vars.field and _vars.filter and value:
            fieldname = str.lower(_vars.field)
            field = table[fieldname]

            # Default fields to return
            fields = [table.id, table.name, table.level, table.path]

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

            filter = _vars.filter
            if filter == "~":
                if parent:
                    # gis_location hierarchical search
                    # NB Currently not used - we allow people to search freely across all the hierarchy
                    # SQL Filter is immediate children only so need slow lookup
                    #query = query & (table.parent == parent) & \
                    #                (field.like("%" + value + "%"))
                    children = gis.get_children(parent) # does not check for deletion_status!
                    children = children.find(lambda row: value in str.lower(row.name))
                    output = children.json()
                    response.headers["Content-Type"] = "text/json"
                    return output

                elif exclude_field and exclude_value:
                    # gis_location hierarchical search
                    # Filter out poor-quality data, such as from Ushahidi
                    query = (field.lower().like("%" + value + "%")) & \
                            ((table[exclude_field].lower() != exclude_value) | \
                                (table[exclude_field] == None))

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

                fields = [table.id,
                          table.name,
                          table.level,
                          table.uuid,
                          table.parent,
                          table.lat,
                          table.lon,
                          table.addr_street]
            else:
                output = xml.json_message(False, 400, "Unsupported filter! Supported filters: ~, =")
                raise HTTP(400, body=output)

        resource.add_filter(query)

        limit = _vars.limit
        if limit:
            output = resource.exporter.json(resource, start=0, limit=int(limit),
                                            fields=fields, orderby=field)
        else:
            output = resource.exporter.json(resource,
                                            fields=fields, orderby=field)

        response.headers["Content-Type"] = "text/json"
        return output


# *****************************************************************************
class S3PersonSearch(S3Search):
    """
    Search method with specifics for person records (full name search)

    """

    def search_json(self, r, **attr):
        """
        Legacy JSON search method (for autocomplete-widgets)

        @param r: the S3Request
        @param attr: request attributes

        """

        xml = self.manager.xml

        output = None
        request = self.request
        response = self.response
        resource = self.resource
        table = self.table

        # Query comes in pre-filtered to accessible & deletion_status
        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        _vars = request.vars # should be request.get_vars?

        # JQueryUI Autocomplete uses "term" instead of "value"
        # (old JQuery Autocomplete uses "q" instead of "value")
        value = _vars.value or _vars.term or _vars.q or None

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        value = value.lower()

        filter = _vars.filter
        limit = int(_vars.limit or 0)

        if filter and value:

            field = table.first_name
            field2 = table.middle_name
            field3 = table.last_name

            # Fields to return
            fields = [table.id, field, field2, field3]

            if filter == "~":
                # pr_person Autocomplete
                if " " in value:
                    value1, value2 = value.split(" ", 1)
                    query = (field.lower().like("%" + value1 + "%")) & \
                            (field2.lower().like("%" + value2 + "%")) | \
                            (field3.lower().like("%" + value2 + "%"))
                else:
                    query = ((field.lower().like("%" + value + "%")) | \
                            (field2.lower().like("%" + value + "%")) | \
                            (field3.lower().like("%" + value + "%")))

            else:
                output = xml.json_message(False, 400, "Unsupported filter! Supported filters: ~")
                raise HTTP(400, body=output)

        resource.add_filter(query)
        output = resource.exporter.json(resource, start=0, limit=limit,
                                        fields=fields, orderby=field)

        response.headers["Content-Type"] = "text/json"
        return output


# *****************************************************************************
