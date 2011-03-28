# -*- coding: utf-8 -*-

""" RESTful Search Methods

    @author: Fran Boon <fran[at]aidiq.com>
    @author: Dominic König <dominic[at]aidiq.com>

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2011 (c) Sahana Software Foundation
    @license: MIT

    @status: work in progress

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

import re

from gluon.storage import Storage
from gluon.http import HTTP
from gluon.html import *
from gluon.sqlhtml import CheckboxesWidget, MultipleOptionsWidget, RadioWidget
from gluon.validators import *
from gluon.serializers import json

from s3crud import S3CRUD
from s3validators import *

__all__ = ["S3SearchWidget",
           "S3SearchSimpleWidget",
           "S3SearchMatchWidget",
           "S3SearchMinMaxWidget",
           "S3SearchSelectWidget",
           "S3SearchLocationWidget",
           "S3Search",
           "S3LocationSearch",
           "S3PersonSearch"]

# *****************************************************************************
class S3SearchWidget(object):
    """
        Search Widget for interactive search (base class)
    """

    def __init__(self, field=None, name=None, **attr):
        """
            Configures the search option

            @param field: name(s) of the fields to search in

            @keyword label: a label for the search widget
            @keyword comment: a comment for the search widget
        """

        self.other = None

        self.field = field
        if not self.field:
            raise SyntaxError("No search field specified.")

        self.attr = Storage(attr)
        if name is not None:
            self.attr["_name"] = name

        self.master_query = None
        self.search_field = None


    def widget(self, resource, vars):
        """
            Returns the widget

            @param resource: the resource to search in
            @param vars: the URL GET variables as dict
        """

        self.attr = Storage(attr)

        raise NotImplementedError


    def query(self, resource, value):
        """
            Returns a sub-query for this search option

            @param resource: the resource to search in
            @param value: the value returned from the widget
        """
        raise NotImplementedError


    def build_master_query(self, resource):
        """
            Get the master query for the specified field(s)
        """

        db = resource.db
        table = resource.table

        master_query = Storage()
        search_field = Storage()

        fields = self.field
        if fields and not isinstance(fields, (list, tuple)):
            fields = [fields]

        # Find the tables, joins and fields to search in
        for f in fields:
            ktable = None
            rtable = None
            component = None
            reference = None
            multiple = False

            if f.find(".") != -1: # Component
                cname, f = f.split(".", 1)
                component = resource.components.get(cname, None)
                if not component:
                    continue
                ktable = component.resource.table
                tablename = component.resource.tablename
                pkey = component.pkey
                fkey = component.fkey
                # Do not add queries for empty tables
                if not db(ktable.id>0).select(ktable.id,
                                              limitby=(0, 1)).first():
                    continue
            else: # this resource
                ktable = table
                ktablename = table._tablename

            if f.find("$") != -1: # Referenced object
                rkey, f = f.split("$", 1)
                if not rkey in ktable.fields:
                    continue
                ftype = str(ktable[rkey].type)
                if ftype[:9] == "reference":
                    reference = ftype[10:]
                elif ftype[:14] == "list:reference":
                    reference = ftype[15:]
                    multiple = True
                else:
                    continue
                rtable = ktable
                rtablename = ktablename
                ktable = db[reference]
                ktablename = reference
                # Do not add queries for empty tables
                if not db(ktable.id>0).select(ktable.id,
                                              limitby=(0, 1)).first():
                    continue

            # Master queries
            if ktable and ktablename not in master_query:
                query = (resource.accessible_query("read", ktable))
                if "deleted" in ktable.fields:
                    query = (query & (ktable.deleted == "False"))
                join = None
                if reference:
                    if ktablename != rtablename:
                        q = (resource.accessible_query("read", rtable))
                        if "deleted" in rtable.fields:
                            q = (q & (rtable.deleted == "False"))
                    else:
                        q = None
                    if multiple:
                        j = (rtable[rkey].contains(ktable.id))
                    else:
                        j = (rtable[rkey] == ktable.id)
                    if q is not None:
                        join = q & j
                    else:
                        join = j
                j = None
                if component:
                    if reference:
                        q = (resource.accessible_query("read", table))
                        if "deleted" in table.fields:
                            q = (q & (table.deleted == "False"))
                        j = (q & (table[pkey] == rtable[fkey]))
                    else:
                        j = (table[pkey] == ktable[fkey])
                if j is not None and join is not None:
                    join = (join & j)
                elif j:
                    join = j
                if join is not None:
                    query = (query & join)
                master_query[ktable._tablename] = query

            # Search fields
            if ktable and f in ktable.fields:
                if ktable._tablename not in search_field:
                    search_field[ktablename] = [ktable[f]]
                else:
                    search_field[ktablename].append(ktable[f])

        self.master_query = master_query
        self.search_field = search_field


# *****************************************************************************
class S3SearchSimpleWidget(S3SearchWidget):
    """
        Simple full-text search widget
    """

    def widget(self, resource, vars):
        """
            Returns the widget

            @param resource: the resource to search in
            @param vars: the URL GET variables as dict
        """

        if "_size" not in self.attr:
            self.attr.update(_size="40")
        if "_name" not in self.attr:
            self.attr.update(_name="%s_search_simple" % resource.name)
        self.attr.update(_type="text")

        self.name = self.attr._name
        return INPUT(**self.attr)


    def query(self, resource, value):
        """
            Returns a sub-query for this search option

            @param resource: the resource to search in
            @param value: the value returned from the widget
        """

        prefix = resource.prefix
        name = resource.name

        table = resource.table
        db = resource.db
        model = resource.manager.model

        DEFAULT = (table.id == None)

        # Get master query and search fields
        self.build_master_query(resource)
        master_query = self.master_query
        search_field = self.search_field

        # No search fields?
        if not search_field:
            return DEFAULT

        # Default search (wildcard)
        if value == "":
            value = "%"

        # Build search query
        if value and isinstance(value,str):
            values = value.split()
            squery = None

            for v in values:
                wc = "%"
                _v = "%s%s%s" % (wc, v.lower(), wc)
                query = None
                for tablename in search_field:
                    hq = master_query[tablename]
                    fq = None
                    fields = search_field[tablename]
                    for f in fields:
                        if fq:
                            fq = (f.lower().like(_v)) | fq
                        else:
                            fq = (f.lower().like(_v))
                    q = hq & fq
                    if query is None:
                        query = q
                    else:
                        query = query | q
                if squery is not None:
                    squery = squery & query
                else:
                    squery = query

            return squery
        else:
            return DEFAULT


# *****************************************************************************
class S3SearchMatchWidget(S3SearchWidget):
    """
    String-search widget

    """

    def widget(self, resource, vars):
        """
            Returns the widget

            @param resource: the resource to search in
            @param vars: the URL GET variables as dict
        """

        raise NotImplementedError


    def query(self, resource, value):
        """
            Returns a sub-query for this search option

            @param resource: the resource to search in
            @param value: the value returned from the widget
        """
        raise NotImplementedError


# *****************************************************************************
class S3SearchMinMaxWidget(S3SearchWidget):
    """
    Min/Max search widget for numeric fields

    """

    def widget(self, resource, vars):
        """
            Returns the widget

            @param resource: the resource to search in
            @param vars: the URL GET variables as dict
        """

        self.names = []

        T = resource.manager.T

        self.method = self.attr.get("method", "range")
        select_min = self.method in ("min", "range")
        select_max = self.method in ("max", "range")

        if len(self.field) > 1:
            raise SyntaxError("Only one search field allowed")

        if not self.search_field:
            self.build_master_query(resource)

        search_field = self.search_field.values()
        if not search_field:
            raise SyntaxError("No valid search field specified")

        search_field = search_field[0][0]

        ftype = str(search_field.type)
        input_min = input_max = None
        if ftype == "integer":
            requires = IS_EMPTY_OR(IS_INT_IN_RANGE())
        elif ftype == "date":
            self.attr.update(_class="date")
            requires = IS_EMPTY_OR(IS_DATE())
        elif ftype == "time":
            self.attr.update(_class="time")
            requires = IS_EMPTY_OR(IS_TIME())
        elif ftype == "datetime":
            self.attr.update(_class="datetime")
            requires = IS_EMPTY_OR(IS_DATETIME())
        else:
            raise SyntaxError("Unsupported search field type")

        self.attr.update(_type="text")
        if select_min:
            name = "min_%s" % search_field.name
            self.attr.update(_name=name, _id=name)
            self.names.append(name)
            input_min = INPUT(requires=requires, **self.attr)
        if select_max:
            name = "max_%s" % search_field.name
            self.attr.update(_name=name, _id=name)
            self.names.append(name)
            input_max = INPUT(requires=requires, **self.attr)
        trl = TR(_class="sublabels")
        tri = TR()
        if input_min is not None:
            trl.append(T("min"))
            tri.append(input_min)
        if input_max is not None:
            trl.append(T("max"))
            tri.append(input_max)
        w = DIV(TABLE(trl, tri))
        return w


    def validate(self, resource, value):
        """
            Validate the input values of the widget
        """

        errors = dict()

        T = resource.manager.T

        tablename = self.search_field.keys()[0]
        search_field = self.search_field[tablename][0]
        select_min = self.method in ("min", "range")
        select_max = self.method in ("max", "range")

        if select_min and select_max:
            vmin = value.get("min_%s" % search_field.name, None)
            vmax = value.get("max_%s" % search_field.name, None)
            if vmax is not None and vmin > vmax:
                errors["max_%s" % search_field.name] = \
                     T("Maximum must be greater than minimum")

        return errors or None


    def query(self, resource, value):
        """
            Returns a sub-query for this search option

            @param resource: the resource to search in
            @param value: the value returned from the widget
        """

        db = resource.db

        tablename = self.search_field.keys()[0]
        search_field = self.search_field[tablename][0]

        select_min = self.method in ("min", "range")
        select_max = self.method in ("max", "range")

        min_query = max_query = None
        if select_min:
            v = value.get("min_%s" % search_field.name, None)
            if v is not None and str(v):
                min_query = (search_field >= v)
        if select_max:
            v = value.get("max_%s" % search_field.name, None)
            if v is not None and str(v):
                max_query = (search_field <= v)
        query = self.master_query[tablename]
        if min_query is not None or max_query is not None:
            if min_query is not None:
                query = query & min_query
            if max_query is not None:
                query = query & max_query
        else:
            query = None
        return (query)
        raise NotImplementedError


# *****************************************************************************
class S3SearchSelectWidget(S3SearchWidget):
    """
        Option select widget for option or boolean fields

        Displays a search widget which allows the user to search for records
        with fields matching a certain criteria.

        Field must be a integer or reference
    """

    def widget(self, resource, vars):
        """
        Returns the widget

        @param resource: the resource to search in
        @param vars: the URL GET variables as dict
        """

        field = self.field[0]

        if "_name" not in self.attr:
            self.attr.update(_name="%s_search_select_%s" % (resource.name, field))
        self.name = self.attr._name

        field_type = str(resource.table[field].type)
        if field_type == "boolean":
            opt_keys = (True, False)
        else:
            # Find unique values of options for that field
            rows = resource.select(field, groupby=resource.table[field])
            opt_keys = [row[field] for row in rows if row[field] != None]

        # Always use the represent of the widget, of present
        represent = self.attr.represent
        # Fallback to the field's represent
        if not represent:
            represent = resource.table[field].represent
        # Execute, if callable
        if callable(represent):
            opt_list = [(opt_key, represent(opt_key)) for opt_key in opt_keys]
        # Otherwise, feed the format string
        elif isinstance(represent, str) and field_type[:9] == "reference":
            # Use the represent string to reduce db calls
            # Find the fields which are needed to represent:
            db = resource.db
            ktable = db[field_type[10:]]
            fieldnames = re.findall("%\(([a-zA-Z0-9_]*)\)s", represent)
            fieldnames += ["id"]
            represent_fields = [ktable[fieldname] for fieldname in fieldnames]
            query = (ktable.id.belongs(opt_keys)) & (ktable.deleted == False)
            represent_rows = db(query).select(*represent_fields).as_dict()
            opt_list = []
            for opt_key in opt_keys:
                opt_list.append([opt_key, represent % represent_rows[opt_key]])
        else:
            opt_list = [(opt_key, "%s" % opt_key) for opt_key in opt_keys]

        # Alphabetise (this will not work as it is converted to a dict),
        # look at IS_IN_SET validator or CheckboxesWidget to ensure that the list
        #opt_list.sort()

        options = dict(opt_list)
        #for opt in opt_list:
        #    options[opt[1]] = opt[0]

        T = resource.manager.T

        # Dummy field
        field = Storage(name = self.name,
                        requires = IS_IN_SET(options,
                                            multiple=True)
                        )

        if len(opt_list) > 50:
            # Collapse into a list widget if there are too many options
            widget = MultipleOptionsWidget().widget(field, None)
        else:
            if self.attr.cols:
                widget = CheckboxesWidget().widget(field, None,
                                                    cols=self.attr.cols)
            else:
                widget = CheckboxesWidget().widget(field, None)
        return widget

        return ""


    def query(self, resource, value):
        """
        Returns a sub-query for this search option

        @param resource: the resource to search in
        @param value: the value returned from the widget

        """

        if value:
            return (resource.table[self.field[0]].belongs(value))
        else:
            return None


# *****************************************************************************
class S3SearchLocationWidget(S3SearchWidget):
    """
        Interactive location search widget
    """

    def widget(self, resource, vars):
        """
        Returns the widget

        @param resource: the resource to search in
        @param vars: the URL GET variables as dict

        """

        self.attr = Storage(attr)

        raise NotImplementedError


    def query(self, resource, value):
        """
        Returns a sub-query for this search option

        @param resource: the resource to search in
        @param value: the value returned from the widget

        """
        raise NotImplementedError


# *****************************************************************************
class S3Search(S3CRUD):
    """
    RESTful Search Method for S3Resources

    """

    def __init__(self, simple=None, advanced=None, any=False, **args):
        """
            Constructor

            @param simple: the widgets for the simple search form as list
            @param advanced: the widgets for the advanced search form as list
            @param any: match "any of" (True) or "all of" (False) the options
                        in advanced search
        """

        S3CRUD.__init__(self)

        args = Storage(args)
        if simple is None:
            if "field" in args:
                if "name" in args:
                    name = args.name
                elif "_name" in args:
                    name = args._name
                else:
                    name = "search_simple"
                simple = S3SearchSimpleWidget(field=args.field,
                                              name=name,
                                              label=args.label,
                                              comment=args.comment)
        names = []
        self.__simple = []
        if not isinstance(simple, (list, tuple)):
            simple = [simple]
        for widget in simple:
            if widget is not None:
                name = widget.attr._name
                if name in names:
                    raise SyntaxError("Duplicate widget: %s") % name
                elif not name:
                    raise SyntaxError("Widget with no name")
                else:
                    self.__simple.append((name, widget))
                    names.append(name)

        names = []
        self.__advanced = []
        if not isinstance(advanced, (list, tuple)):
            advanced = [advanced]
        for widget in advanced:
            if widget is not None:
                name = widget.attr._name
                if name in names:
                    raise SyntaxError("Duplicate widget: %s") % name
                elif not name:
                    raise SyntaxError("Widget with no name")
                else:
                    self.__advanced.append((name, widget))
                    names.append(name)

        self.__any = any

        if self.__simple or self.__advanced:
            self.__interactive = True
        else:
            self.__interactive = False


    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point to apply search method to S3Requests

            @param r: the S3Request
            @param attr: request attributes
        """

        format = r.representation

        if r.component and self != self.resource.search:
            return self.resource.search(r, **attr)

        if r.interactive and self.__interactive:
            return self.search_interactive(r, **attr)
        elif format == "aadata" and self.__interactive:
            return self.select(r, **attr)
        elif format == "json":
            return self.search_json(r, **attr)
        else:
            r.error(501, self.manager.ERROR.BAD_FORMAT)

        return dict()


    # -------------------------------------------------------------------------
    def search_interactive(self, r, **attr):
        """
            Interactive search

            @param r: the S3Request instance
            @param attr: request parameters
        """

        # Get environment
        session = self.session
        request = self.request
        response = self.response
        resource = self.resource
        table = self.table
        tablename = self.tablename
        T = self.manager.T

        vars = request.get_vars

        # Get representation
        representation = r.representation

        # Initialize output
        output = dict()
        simple = False

        # Get table-specific parameters
        sortby = self._config("sortby", [[1,'asc']])
        orderby = self._config("orderby", None)
        list_fields = self._config("list_fields")
        insertable = self._config("insertable", True)

        # Initialize the form
        form = DIV(_id="search_form", _class="form-container")

        # Add-link (common to all forms)
        ADD = self.crud_string(tablename, "label_create_button")
        href_add = r.other(method="create", representation=representation)
        authorised = self.permit("create", tablename)
        if authorised and insertable:
            add_link = self.crud_button(ADD, _href=href_add,
                                        _id="add-btn", _class="action-lnk")
        else:
            add_link = ""

        # Append the simple search form
        if self.__simple:
            simple = True
            trows = []
            for name, widget in self.__simple:
                label = widget.field
                if isinstance(label, (list, tuple)) and len(label):
                    label = label[0]
                comment = ""
                if hasattr(widget, "attr"):
                    label = widget.attr.get("label", label)
                    comment = widget.attr.get("comment", comment)
                tr = TR(TD("%s: " % label, _class="w2p_fl"),
                        widget.widget(resource, vars))
                if comment:
                    tr.append(DIV(DIV(_class="tooltip",
                                      _title="%s|%s" % (label, comment))))
                trows.append(tr)
            if self.__advanced:
                switch_link = A(T("Advanced Search"), _href="#",
                                _class="action-lnk", _id="advanced-lnk")
            else:
                switch_link = ""
            trows.append(TR("", TD(INPUT(_type="submit", _value=T("Search")),
                                   switch_link, add_link)))
            simple_form = FORM(TABLE(trows), _id="simple-form")
            form.append(simple_form)

        # Append the advanced search form
        if self.__advanced:
            trows = []
            for name, widget in self.__advanced:
                label = widget.field
                if isinstance(label, (list, tuple)) and len(label):
                    label = label[0]
                comment = ""
                if hasattr(widget, "attr"):
                    label = widget.attr.get("label", label)
                    comment = widget.attr.get("comment", comment)
                #use = isinstance(widget, S3SearchSimpleWidget) and \
                      #"hidden" or "checkbox"
                #on = use == "hidden" and 'on' or ''
                tr = TR(
                        #TD(INPUT(_type=use,
                                 #_name="use_%s" % name,
                                 #_class="use_widget",
                                 #_value=on)
                        #),
                        TD("%s: " % label, _class="w2p_fl"),
                        widget.widget(resource, vars)
                       )
                if comment:
                    tr.append(DIV(DIV(_class="tooltip",
                                      _title="%s|%s" % (label, comment))))
                trows.append(tr)
            if self.__simple:
                switch_link = A(T("Simple Search"), _href="#",
                                _class="action-lnk", _id="simple-lnk")
            else:
                switch_link = ""
            trows.append(TR("",# "",
                            TD(INPUT(_type="submit", _value=T("Search")),
                               switch_link,
                               add_link
                              )
                           )
                        )
            if simple:
                _class = "hide"
            else:
                _class = None
            advanced_form = FORM(TABLE(trows), _id="advanced-form", _class=_class)
            form.append(advanced_form)

        output.update(form=form)

        query = None

        # Process the simple search form:
        if self.__simple and \
           simple_form.accepts(request.vars, session,
                               formname="search_simple",
                               keepvalues=True):
            errors = None
            for name, widget in self.__simple:
                if hasattr(widget, "names"):
                    value = Storage([(name, advanced_form.vars[name])
                                     for name in widget.names
                                     if name in advanced_form.vars])
                elif name in simple_form.vars:
                    value = simple_form.vars[name]
                else:
                    value = None
                if hasattr(widget, "validate"):
                    errors = widget.validate(resource, value)
                if errors:
                    simple_form.errors.update(errors)
                else:
                    q = widget.query(resource, value)
                    if q is not None:
                        if query is None:
                            query = q
                        else:
                            query = query & q

        # Process the simple search form:
        if self.__advanced and \
           advanced_form.accepts(request.vars, session,
                                 formname="search_advanced",
                                 keepvalues=True):
            simple = False
            errors = None
            for name, widget in self.__advanced:
                #use_widget = advanced_form.vars.get("use_%s" % name, False)
                #if not use_widget:
                    #continue
                if hasattr(widget, "names"):
                    value = Storage([(name, advanced_form.vars[name])
                                     for name in widget.names
                                     if name in advanced_form.vars])
                elif name in advanced_form.vars:
                    value = advanced_form.vars[name]
                else:
                    continue
                if hasattr(widget, "validate"):
                    errors = widget.validate(resource, value)
                if errors:
                    advanced_form.errors.update(errors)
                else:
                    q = widget.query(resource, value)
                    if q is not None:
                        if query is None:
                            query = q
                        elif self.__any:
                            query = query | q
                        else:
                            query = query & q
        elif self.__advanced and advanced_form.errors:
            simple = False

        output.update(simple=simple)
        errors = simple and self.__simple and simple_form.errors or \
                 self.__advanced and advanced_form.errors or \
                 None

        if query is not None and not errors:
            # Build query
            resource.add_filter(query)

            # Build session filter (for SSPag)
            if not response.s3.no_sspag:
                limit = 1
                ids = resource.get_id()
                if ids:
                    if not isinstance(ids, list):
                        ids = str(ids)
                    else:
                        ids = ",".join([str(i) for i in ids])
                    session.s3.filter = {"%s.id" % resource.name: ids}
            else:
                limit = None

            # Linkto and list_fields
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

            # Get the result table
            items = self.sqltable(fields=fields,
                                  limit=limit,
                                  orderby=orderby,
                                  linkto=linkto,
                                  download_url=self.download_url,
                                  format=representation)

            if items and not response.s3.no_sspag:
                # Pre-populate SSPag cache (avoids the 1st Ajax request)
                totalrows = self.resource.count()
                if totalrows:
                    aadata = dict(aaData =
                                self.sqltable(fields=fields,
                                              start=0,
                                              limit=20,
                                              orderby=orderby,
                                              linkto=linkto,
                                              download_url=self.download_url,
                                              as_page=True,
                                              format=representation) or [])
                    aadata.update(iTotalRecords=totalrows,
                                  iTotalDisplayRecords=totalrows)
                    response.aadata = json(aadata)
                    response.s3.start = 0
                    response.s3.limit = 20

            elif not items:
                items = self.crud_string(tablename, "msg_no_match")

            output.update(items=items, sortby=sortby)

        # Title and subtitle
        title = self.crud_string(tablename, "title_search")
        subtitle = self.crud_string(tablename, "msg_match")
        output.update(title=title, subtitle=subtitle)

        # View
        response.view = "search.html"
        return output


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
                if field.type.split(" ")[0] in \
                    ["reference", "id", "float", "integer"]:
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
            response.headers["Content-Type"] = "application/json"

        else:
            output = xml.json_message(False, 400, "Missing options! Require: field, filter & value")
            raise HTTP(400, body=output)

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
        if value:
            value = value.lower()

        query = None
        fields = []
        field = table.id

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
                    # NB Currently not used - we allow people to search
                    # freely across all the hierarchy,
                    # SQL Filter is immediate children only so need slow lookup
                    # query = query & (table.parent == parent) & \
                    #                 (field.like("%" + value + "%"))
                    # @todo: does currently not check deletion_status!
                    children = gis.get_children(parent)
                    children = children.find(lambda row: \
                                             value in str.lower(row.name))
                    output = children.json()
                    response.headers["Content-Type"] = "application/json"
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
                if field.type.split(" ")[0] in \
                   ["reference", "id", "float", "integer"]:
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
                          table.addr_street,
                          table.addr_postcode]
            else:
                output = xml.json_message(False, 400, "Unsupported filter! Supported filters: ~, =")
                raise HTTP(400, body=output)


        if not fields:
            for field in table.fields:
                fields.append(table[field])

        resource.add_filter(query)

        limit = _vars.limit
        if limit:
            output = resource.exporter.json(resource, start=0, limit=int(limit),
                                            fields=fields, orderby=field)
        else:
            output = resource.exporter.json(resource,
                                            fields=fields, orderby=field)

        response.headers["Content-Type"] = "application/json"
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

        response.headers["Content-Type"] = "application/json"
        return output


# *****************************************************************************
