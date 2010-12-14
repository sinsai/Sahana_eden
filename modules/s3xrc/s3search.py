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
    """

    def respond(r, **attr):

        """
            Responder

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @returns: output object to send to the view
            
            @ToDo: Complete this!
        """

        s3xrc = self.manager
        db = self.db
        request = self.request
        response = self.response
        table = self.table
        tablename = self.tablename
        representation = r.representation

        deletable = attr.get("deletable", True)
        main = attr.get("main", None)
        extra = attr.get("extra", None)

        # Filter Search list to just those records which user can read
        # @ToDo: replace shn_accessible_query with self.permit()
        query = shn_accessible_query("read", table)

        # Filter search to items which aren't deleted
        if "deleted" in table:
            query = (table.deleted == False) & query

        # Respect response.s3.filter
        if response.s3.filter:
            query = response.s3.filter & query

        if representation == "json":

            _vars = request.vars

            # JQueryUI Autocomplete uses "term" instead of "value"
            # (old JQuery Autocomplete uses "q" instead of "value")
            value = _vars.value or _vars.term or _vars.q or None

            # We want to do case-insensitive searches
            # (default anyway on MySQL/SQLite, but not PostgreSQL)
            value = value.lower()

            if _vars.field and _vars.filter and value:
                field = str.lower(_vars.field)
                _field = table[field]

                # Optional fields
                if "field2" in _vars:
                    field2 = str.lower(_vars.field2)
                else:
                    field2 = None
                if "field3" in _vars:
                    field3 = str.lower(_vars.field3)
                else:
                    field3 = None
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
                    if field2 and field3:
                        # pr_person name search
                        if " " in value:
                            value1, value2 = value.split(" ", 1)
                            query = query & ((_field.lower().like("%" + value1 + "%")) & \
                                            (table[field2].lower().like("%" + value2 + "%")) | \
                                            (table[field3].lower().like("%" + value2 + "%")))
                        else:
                            query = query & ((_field.lower().like("%" + value + "%")) | \
                                            (table[field2].lower().like("%" + value + "%")) | \
                                            (table[field3].lower().like("%" + value + "%")))

                    elif exclude_field and exclude_value:
                        # gis_location hierarchical search
                        # Filter out poor-quality data, such as from Ushahidi
                        query = query & (_field.lower().like("%" + value + "%")) & \
                                        (table[exclude_field] != exclude_value)

                    elif parent:
                        # gis_location hierarchical search
                        # NB Currently not used - we allow people to search freely across all the hierarchy
                        # SQL Filter is immediate children only so need slow lookup
                        #query = query & (table.parent == parent) & \
                        #                (_field.like("%" + value + "%"))
                        children = gis.get_children(parent)
                        children = children.find(lambda row: value in str.lower(row.name))
                        item = children.json()
                        query = None

                    else:
                        # Normal single-field
                        query = query & (_field.lower().like("%" + value + "%"))

                    if query:
                        if limit:
                            item = db(query).select(limitby=(0, limit)).json()
                        else:
                            item = db(query).select().json()

                elif filter == "=":
                    if _field.type.split(" ")[0] in ["reference", "id", "float", "integer"]:
                        # Numeric, e.g. Organisations' offices_by_org
                        query = query & (_field == value)
                    else:
                        # Text
                        if value == "nullnone":
                            # i.e. Location Selector
                            query = query & (_field == None)
                        else:
                            query = query & (_field.lower() == value)

                    if parent:
                        # i.e. gis_location hierarchical search
                        query = query & (table.parent == parent)

                    if tablename == "gis_location":
                        # Don't return unnecessary fields (WKT is large!)
                        item = db(query).select(table.id, table.uuid, table.parent, table.name, table.level, table.lat, table.lon, table.addr_street).json()
                    else:
                        item = db(query).select().json()

                elif filter == "<":
                    query = query & (_field < value)
                    item = db(query).select().json()

                elif filter == ">":
                    query = query & (_field > value)
                    item = db(query).select().json()

                else:
                    item = s3xrc.xml.json_message(False, 400, "Unsupported filter! Supported filters: ~, =, <, >")
                    raise HTTP(400, body=item)

            else:
                #item = s3xrc.xml.json_message(False, 400, "Search requires specifying Field, Filter & Value!")
                #raise HTTP(400, body=item)
                # Provide a simplified JSON output which is in the same format as the Search one
                # (easier to parse than S3XRC & means no need for different parser for filtered/unfiltered)
                if tablename == "gis_location":
                    # Don't return unnecessary fields (WKT is large!)
                    item = db(query).select(table.id, table.name, table.level).json()
                else:
                    item = db(query).select().json()

            response.view = "xml.html"
            output = dict(item=item)

        #elif representation in shn_interactive_view_formats:

            # @ToDo: we don't yet use HTML representation live & it should be changed when we do.
            # Q: Why not just use/extend search_simple for this?

            # None of these are visible as-is inside the module:
            # shn_interactive_view_formats
            # shn_represent
            # t2.search / crud.search
            # s3.crud_strings

        #    if (self.resource.parent is not None):
                # @ToDo: Make component-aware
        #        pass

        #    else:
                # Not a component
        #        shn_represent(table, r.prefix, r.name, deletable, main, extra)
        #        search = t2.search(table, query=query)
                #search = crud.search(table, query=query)[0]

                # Check for presence of Custom View
        #        self._view(r, "search.html", format=None)

                # CRUD Strings
        #        title = s3.crud_strings.title_search

        #        output = dict(search=search, title=title)

        else:
            raise HTTP(501, body=BADFORMAT)

        return output
        
# *****************************************************************************
class S3LocationSearch(S3Search):
    """
        Location-Specific Searches
        
        @ToDo: Move location-specific parts into this class instead
    """

    def respond(r, **attr):
        pass
