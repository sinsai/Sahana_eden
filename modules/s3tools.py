# -*- coding: utf-8 -*-

""" Sahana Eden Tools Module

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @author: Fran Boon <francisboon@gmail.com>
    @author: Dominic König <dominic@aidiq.com>
    @author: sunneach
    @copyright: (c) 2010 Sahana Software Foundation
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

__name__ = "S3TOOLS"

__all__ = ["SQLTABLES3",
           "MENUS3",
           "QueryS3",
           "FieldS3",
           "CrudS3",
           "S3ReusableField"]

import sys
import datetime
import re
import urllib
import uuid
import warnings

from gluon.html import *
from gluon.http import HTTP, redirect
from gluon.storage import Storage, Messages
from gluon.validators import *
#try:
#    from gluon.contrib.gql import Field, Row, Query
#except ImportError:
from gluon.sql import Field, Row, Query
from gluon.sqlhtml import SQLFORM, SQLTABLE
from gluon.tools import Auth
from gluon.tools import Crud

DEFAULT = lambda: None
table_field = re.compile("[\w_]+\.[\w_]+")

# *****************************************************************************
class SQLTABLES3(SQLTABLE):

    """
    S3 custom version of gluon.sqlhtml.SQLTABLE

    given a SQLRows object, as returned by a db().select(), generates
    an html table with the rows.
    - we need a different linkto construction for our CRUD controller
    - we need to specify a different ID field to direct to for the M2M controller
    - used by S3XRC

    optional arguments:

    @param linkto: URL (or lambda to generate a URL) to edit individual records
    @param upload: URL to download uploaded files
    @param orderby: Add an orderby link to column headers.
    @param headers: dictionary of headers to headers redefinions
    @param truncate: length at which to truncate text in table cells.
        Defaults to 16 characters.

    optional names attributes for passed to the <table> tag

    Simple linkto example::

        rows = db.select(db.sometable.ALL)
        table = SQLTABLES3(rows, linkto="someurl")

    This will link rows[id] to .../sometable/value_of_id

    More advanced linkto example::

        def mylink(field):
            return URL(r=request, args=[field])

        rows = db.select(db.sometable.ALL)
        table = SQLTABLES3(rows, linkto=mylink)

    This will link rows[id] to
        current_app/current_controller/current_function/value_of_id

    """

    def __init__(self, sqlrows,
                 linkto=None,
                 upload=None,
                 orderby=None,
                 headers={},
                 truncate=16,
                 columns=None,
                 th_link='',
                 **attributes):

        table_field = re.compile('[\w_]+\.[\w_]+')

        TABLE.__init__(self, **attributes)
        self.components = []
        self.attributes = attributes
        self.sqlrows = sqlrows
        (components, row) = (self.components, [])
        if not columns:
            columns = sqlrows.colnames
        if headers=="fieldname:capitalize":
            headers = {}
            for c in columns:
                headers[c] = " ".join([w.capitalize() for w in c.split(".")[-1].split("_")])

        for c in columns:
            if orderby:
                row.append(TH(A(headers.get(c, c),
                                _href=th_link+"?orderby=" + c)))
            else:
                row.append(TH(headers.get(c, c)))

        components.append(THEAD(TR(*row)))
        tbody = []
        for (rc, record) in enumerate(sqlrows):
            row = []
            if rc % 2 == 0:
                _class = "even"
            else:
                _class = "odd"
            for colname in columns:
                if not table_field.match(colname):
                    r = record._extra[colname]
                    row.append(TD(r))
                    continue
                (tablename, fieldname) = colname.split(".")
                field = sqlrows.db[tablename][fieldname]
                if tablename in record \
                        and isinstance(record,Row) \
                        and isinstance(record[tablename],Row):
                    r = record[tablename][fieldname]
                elif fieldname in record:
                    r = record[fieldname]
                else:
                    raise SyntaxError, "something wrong in Rows object"
                r_old = r
                if field.represent:
                    r = field.represent(r)
                elif field.type == "blob" and r:
                    r = "DATA"
                elif field.type == "upload":
                    if upload and r:
                        r = A("file", _href="%s/%s" % (upload, r))
                    elif r:
                        r = "file"
                    else:
                        r = ""
                elif field.type in ["string","text"]:
                    r = str(field.formatter(r))
                    ur = unicode(r, "utf8")
                    if truncate!=None and len(ur) > truncate:
                        r = ur[:truncate - 3].encode("utf8") + "..."
                elif linkto and field.type == "id":
                    #try:
                        #href = linkto(r, "table", tablename)
                    #except TypeError:
                        #href = "%s/%s/%s" % (linkto, tablename, r_old)
                    #r = A(r, _href=href)
                    try:
                        href = linkto(r)
                    except TypeError:
                        href = "%s/%s" % (linkto, r)
                    r = A(r, _href=href)
                #elif linkto and str(field.type).startswith("reference"):
                    #ref = field.type[10:]
                    #try:
                        #href = linkto(r, "reference", ref)
                    #except TypeError:
                        #href = "%s/%s/%s" % (linkto, ref, r_old)
                        #if ref.find(".") >= 0:
                            #tref,fref = ref.split(".")
                            #if hasattr(sqlrows.db[tref],"_primarykey"):
                                #href = "%s/%s?%s" % (linkto, tref, urllib.urlencode({fref:ur}))
                    #r = A(r, _href=href)
                elif linkto and hasattr(field._table,"_primarykey") and fieldname in field._table._primarykey:
                    # have to test this with multi-key tables
                    key = urllib.urlencode(dict( [ \
                                ((tablename in record \
                                      and isinstance(record, Row) \
                                      and isinstance(record[tablename], Row)) and
                                 (k, record[tablename][k])) or (k, record[k]) \
                                    for k in field._table._primarykey ] ))
                    r = A(r, _href="%s/%s?%s" % (linkto, tablename, key))
                row.append(TD(r))
            tbody.append(TR(_class=_class, *row))
        components.append(TBODY(*tbody))


# =============================================================================
class MENUS3(DIV):

    """
    S3 extensions of the gluon.html.MENU class

    Used to build modules menu
    Each list has 3 options: Name, Right & Link
    (NB In Web2Py's MENU, the 2nd option is 'Active')
    Right=True means that menu item floats right

    Optional arguments
        _class: defaults to 'S3menuInner'
        ul_main_class: defaults to 'S3menuUL'
        ul_sub_class: defaults to 'S3menuSub'
        li_class: defaults to 'S3menuLI'
        a_class: defaults to 'S3menuA'

    Example:
        menu = MENUS3([["name", False, URL(...), [submenu]], ...])
        {{=menu}}

    @author: Fran Boon

    """

    tag = "div"

    def __init__(self, data, **args):
        self.data = data
        self.attributes = args

    def serialize(self, data, level=0):
        if level == 0:
            # Top-level menu
            div = UL(**self.attributes)
            for i in range(len(data)):
                (name, right, link) = data[i][:3]
                if not link:
                        link = "#null"
                if right:
                    style = "float: right;"
                else:
                    style = "float: left;"
                if len(data[i]) > 3 and data[i][3]:
                    # Submenu
                    ul_inner = self.serialize(data[i][3], level+1)
                    in_ul = LI(DIV(A(name, _href=link), _class="hoverable"), ul_inner, _style=style)
                else:
                    if (i == 0) and (self.attributes["_id"] == "modulenav"):
                        # 1st item, so display logo
                        in_ul = LI(DIV(A(SPAN(_class="S3menulogo"), _href=link),
                                    SPAN(A(name, _href=link, _class="S3menuHome")),_class="hoverable"), _style=style )
                    else:
                        in_ul = LI(DIV(A(name, _href=link), _class="hoverable"), _style=style)
                div.append(in_ul)
        else:
            # Submenu
            div = UL()
            for item in data:
                (name, right, link) = item[:3]
                li = LI(A(name, _href=link))
                div.append(li)
        return div

    def xml(self):
        return self.serialize(self.data, 0).xml()


# =============================================================================
class QueryS3(Query):

    """
    S3 extensions of the gluon.sql.Query class

    If Server Side Pagination is on, the proper CAST is needed to match
    the string-typed id to lookup table id

    @author: sunneach

    """

    def __init__(self,
                 left,
                 op=None,
                 right=None,
                ):

        if op <> "join_via":
            Query.__init__(self, left, op, right)
        else:
            self.sql = "CAST(TRIM(%s,"|") AS INTEGER)=%s" % (left, right)


# =============================================================================
class FieldS3(Field):

    """
    S3 extensions of the gluon.sql.Field clas

    If Server Side Pagination is on, the proper CAST is needed to
    match the lookup table id

    @author: sunneach

    """

    def __init__(
        self,
        fieldname,
        type="string",
        length=None,
        default=None,
        required=False,
        requires="<default>",
        ondelete="CASCADE",
        notnull=False,
        unique=False,
        uploadfield=True,
        widget=None,
        label=None,
        comment=None,
        writable=True,
        readable=True,
        update=None,
        authorize=None,
        autodelete=False,
        represent=None,
        uploadfolder=None,
        compute=None,
        sortby=None,
        ):

        self.sortby = sortby

        Field.__init__(self,
                       fieldname,
                       type,
                       length,
                       default,
                       required,
                       requires,
                       ondelete,
                       notnull,
                       unique,
                       uploadfield,
                       widget,
                       label,
                       comment,
                       writable,
                       readable,
                       update,
                       authorize,
                       autodelete,
                       represent,
                       uploadfolder,
                       compute)

    def join_via(self, value):
        if self.type.find("reference") == 0:
            return Query(self, "=", value)
        else:
            return QueryS3(self, "join_via", value)


# =============================================================================
class CrudS3(Crud):

    """
    S3 extension of the gluon.tools.Crud class

    - select() uses SQLTABLES3 (to allow different linkto construction)

    """

    def __init__(self, environment, db=None):
        """ Initialise parent class & make any necessary modifications """
        Crud.__init__(self, environment, db)

    def select(
        self,
        table,
        query=None,
        fields=None,
        orderby=None,
        limitby=None,
        headers={},
        **attr
        ):
        request = self.environment.request
        if not (isinstance(table, self.db.Table) or table in self.db.tables):
            raise HTTP(404)
        if not self.has_permission("select", table):
            redirect(self.settings.auth.settings.on_failed_authorization)
        #if record_id and not self.has_permission("select", table):
        #    redirect(self.settings.auth.settings.on_failed_authorization)
        if not isinstance(table, self.db.Table):
            table = self.db[table]
        if not query:
            query = table.id > 0
        if not fields:
            fields = [table.ALL]
        rows = self.db(query).select(*fields, **dict(orderby=orderby,
            limitby=limitby))
        if not rows:
            return None # Nicer than an empty table.
        if not "linkto" in attr:
            attr["linkto"] = self.url(args="read")
        if not "upload" in attr:
            attr["upload"] = self.url("download")
        if request.extension != "html":
            return rows.as_list()
        return SQLTABLES3(rows, headers=headers, **attr)


# =============================================================================
class S3ReusableField(object):

    """
    DRY Helper for reusable fields:

    This creates neither a Table nor a Field, but just
    an argument store. The field is created with the __call__
    method, which is faster than copying an existing field.

    @author: Dominic König <dominic@aidiq.com>

    """

    def __init__(self, name, type="string", **attr):

        self.name = name
        self.__type = type
        self.attr = Storage(attr)

    def __call__(self, name=None, **attr):

        if not name:
            name = self.name

        ia = Storage(self.attr)

        if attr:
            if not attr.get("empty", True):
                requires = ia.requires
                if requires:
                    if not isinstance(requires, (list, tuple)):
                        requires = [requires]
                    if requires:
                        r = requires[0]
                        if isinstance(r, IS_EMPTY_OR):
                            requires = r.other
                            ia.update(requires=requires)
            if "empty" in attr:
                del attr["empty"]
            ia.update(**attr)

        if ia.sortby is not None:
            return FieldS3(name, self.__type, **ia)
        else:
            return Field(name, self.__type, **ia)


# =============================================================================
