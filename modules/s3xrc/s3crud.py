# -*- coding: utf-8 -*-

""" S3XRC Resource Framework - CRUD method handlers

    @see: U{B{I{S3XRC-2}} <http://eden.sahanafoundation.org/wiki/S3XRC>} on Eden wiki

    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

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

__all__ = ["S3Audit",
           "S3Exporter",
           "S3Importer",
           "S3MethodHandler",
           "S3CRUDHandler"]

import datetime, re, os

from gluon.storage import Storage
from gluon.html import URL, TABLE, TR, TH, TD, THEAD, TBODY, A
from gluon.http import HTTP, redirect
from gluon.serializers import json
from gluon.sql import Field, Row
from gluon.sqlhtml import SQLTABLE, SQLFORM
from gluon.validators import IS_EMPTY_OR

from lxml import etree

# *****************************************************************************
class S3Audit(object):

    """ Audit Trail Writer Class """

    # -------------------------------------------------------------------------
    def __init__(self, db, session,
                 tablename="s3_audit",
                 migrate=True):

        self.db = db
        self.table = db.get(tablename, None)
        if not self.table:
            self.table = db.define_table(tablename,
                            Field("timestmp", "datetime"),
                            Field("person", "integer"),
                            Field("operation"),
                            Field("tablename"),
                            Field("record", "integer"),
                            Field("representation"),
                            Field("old_value", "text"),
                            Field("new_value", "text"),
                            migrate=migrate)

        self.session = session

        if session.auth and session.auth.user:
            self.user = session.auth.user.id
        else:
            self.user = None


    # -------------------------------------------------------------------------
    def __call__(self, operation, prefix, name,
                 form=None,
                 record=None,
                 representation=None):

        now = datetime.datetime.utcnow()

        audit = self.session.s3
        table = self.table
        db = self.db

        if record:
            if isinstance(record, Row):
                record = record.get("id", None)
                if not record:
                    return True
            try:
                record = int(record)
            except ValueError:
                record = None
        else:
            record = None

        #print "Audit: %s on %s_%s #%s" % (operation, prefix, name, record or 0)

        tablename = "%s_%s" % (prefix, name)

        if operation in ("list", "read"):
            if audit.audit_read:
                table.insert(timestmp = now,
                             person = self.user,
                             operation = operation,
                             tablename = tablename,
                             record = record,
                             representation = representation)

        elif operation in ("create", "update"):
            if audit.audit_write:
                if form:
                    record =  form.vars.id
                    new_value = ["%s:%s" % (var, str(form.vars[var])) for var in form.vars]
                else:
                    new_value = []
                table.insert(timestmp = now,
                             person = self.user,
                             operation = operation,
                             tablename = tablename,
                             record = record,
                             representation = representation,
                             new_value = new_value)

        elif operation == "delete":
            if audit.audit_write:

                row = db(db[tablename].id == record).select(limitby=(0, 1)).first()
                old_value = []
                if row:
                    old_value = ["%s:%s" % (field, row[field]) for field in row]
                table.insert(timestmp = now,
                             person = self.user,
                             operation = operation,
                             tablename = tablename,
                             record = record,
                             representation = representation,
                             old_value = old_value)

        return True


# *****************************************************************************
class S3Exporter(object):

    def __init__(self, manager):

        """ Constructor """

        self.manager = manager

        self.db = self.manager.db
        self.s3 = self.manager.s3


    # -------------------------------------------------------------------------
    def csv(resource, filter=None, request=None, response=None):

        """ Export record(s) as CSV """

        db = self.db

        tablename = resource.tablename
        query = resource.get_query()

        if filter:
            query = query & filter

        if response:
            servername = request and "%s_" % request.env.server_name or ""
            filename = "%s%s.csv" % (servername, tablename)
            from gluon.contenttype import contenttype
            response.headers["Content-Type"] = contenttype(".csv")
            response.headers["Content-disposition"] = "attachment; filename=%s" % filename

        return str(db(query).select())


    # -------------------------------------------------------------------------
    def pdf(resource, filter=None, request=None, response=None, list_fields=None):

        """ Export record(s) as Adobe PDF """

        db = self.db

        # Import ReportLab
        try:
            from reportlab.lib.units import cm
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        except ImportError:
            #session.error = REPORTLAB_ERROR
            redirect(URL(r=request))

        # Import Geraldo
        try:
            from geraldo import Report, ReportBand, Label, ObjectValue, SystemField, landscape, BAND_WIDTH
            from geraldo.generators import PDFGenerator
        except ImportError:
            #session.error = GERALDO_ERROR
            redirect(URL(r=request))

        # Get records
        records = db(query).select(table.ALL)
        if not records:
            #session.warning = T("No data in this table - cannot create PDF!")
            redirect(URL(r=request))

        # Create output stream
        import StringIO
        output = StringIO.StringIO()

        # Find fields
        fields = None
        if list_fields:
            fields = [table[f] for f in list_fields if table[f].readable]
        if fields and len(fields) == 0:
            fields.append(table.id)
        if not fields:
            fields = [table[f] for f in table.fields if table[f].readable]

        # Export
        _elements = [ SystemField(
                            expression = "%(report_title)s",
                            top = 0.1 * cm,
                            left = 0,
                            width = BAND_WIDTH,
                            style = {
                                "fontName": "Helvetica-Bold",
                                "fontSize": 14,
                                "alignment": TA_CENTER
                                }
                            )]
        detailElements = []
        COLWIDTH = 2.5
        LEFTMARGIN = 0.2

        def _represent(field, data):
            if data is None:
                return ""
            represent = table[field].represent
            if not represent:
                represent = lambda v: str(v)
            text = str(represent(data)).decode("utf-8")
            # Filter out markup from text
            if "<" in text:
                try:
                    markup = etree.XML(text)
                    text = markup.xpath(".//text()")
                    if text:
                        text = " ".join(text)
                except etree.XMLSyntaxError:
                    pass
            return s3xrc.xml.xml_encode(text)

        for field in fields:
            _elements.append(Label(text=s3xrc.xml.xml_encode(str(field.label))[:16], top=0.8*cm, left=LEFTMARGIN*cm))
            tab, col = str(field).split(".")
            detailElements.append(ObjectValue(
                attribute_name = col,
                left = LEFTMARGIN * cm,
                width = COLWIDTH * cm,
                # Ensure that col is substituted when lambda defined not evaluated by using the default value
                get_value = lambda instance,
                column = col: _represent(column, instance[column])
                ))
            LEFTMARGIN += COLWIDTH

        mod, res = str(table).split("_", 1)
        try:
            mod_nice = deployment_settings.modules[mod]["name_nice"]
        except:
            mod_nice = mod
        _title = mod_nice + ": " + res.capitalize()

        class MyReport(Report):
            title = _title
            page_size = landscape(A4)
            class band_page_header(ReportBand):
                height = 1.3*cm
                auto_expand_height = True
                elements = _elements
                borders = {"bottom": True}
            class band_page_footer(ReportBand):
                height = 0.5*cm
                elements = [
                    Label(text="%s" % request.utcnow.date(), top=0.1*cm, left=0),
                    SystemField(expression="Page # %(page_number)d of %(page_count)d", top=0.1*cm,
                        width=BAND_WIDTH, style={"alignment": TA_RIGHT}),
                ]
                borders = {"top": True}
            class band_detail(ReportBand):
                height = 0.5*cm
                auto_expand_height = True
                elements = tuple(detailElements)
        report = MyReport(queryset=records)
        report.generate_by(PDFGenerator, filename=output)

        # Set content type and disposition headers
        if response:
            filename = "%s_%s.pdf" % (request.env.server_name, str(table))
            from gluon.contenttype import contenttype
            response.headers["Content-Type"] = contenttype.contenttype(".pdf")
            response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename

        # Return the stream
        output.seek(0)
        return output.read()


    # -------------------------------------------------------------------------
    def xls(resource, filter=None, request=None, response=None, list_fields=None):

        """ Export record(s) as Microsoft XLS """

        db = self.db
        table = resource.table
        query = resource.get_query()

        if filter:
            query = query & filter

        try:
            import xlwt
        except ImportError:
            #session.error = XLWT_ERROR
            redirect(URL(r=request))

        import StringIO
        output = StringIO.StringIO()

        items = db(query).select(table.ALL)

        book = xlwt.Workbook(encoding="utf-8")
        sheet1 = book.add_sheet(str(table))
        # Header row
        row0 = sheet1.row(0)
        cell = 0

        fields = None
        if list_fields:
            fields = [table[f] for f in list_fields if table[f].readable]
        if fields and len(fields) == 0:
            fields.append(table.id)
        if not fields:
            fields = [table[f] for f in table.fields if table[f].readable]

        for field in fields:
            row0.write(cell, str(field.label), xlwt.easyxf("font: bold True;"))
            cell += 1
        row = 1
        style = xlwt.XFStyle()
        for item in items:
            # Item details
            rowx = sheet1.row(row)
            row += 1
            cell1 = 0
            for field in fields:
                tab, col = str(field).split(".")
                # Check for Date formats
                coltype = db[tab][col].type
                if coltype == "date":
                    style.num_format_str = "D-MMM-YY"
                elif coltype == "datetime":
                    style.num_format_str = "M/D/YY h:mm"
                elif coltype == "time":
                    style.num_format_str = "h:mm:ss"

                # Check for a custom.represent (e.g. for ref fields)
                represent = shn_field_represent(field, item, col)
                # Filter out markup from text
                if isinstance(represent, basestring) and "<" in represent:
                    try:
                        markup = etree.XML(represent)
                        represent = markup.xpath(".//text()")
                        if represent:
                            represent = " ".join(represent)
                    except etree.XMLSyntaxError:
                        pass

                rowx.write(cell1, str(represent), style)
                cell1 += 1
        book.save(output)
        output.seek(0)
        import gluon.contenttype
        response.headers["Content-Type"] = gluon.contenttype.contenttype(".xls")
        filename = "%s_%s.xls" % (request.env.server_name, str(table))
        response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
        return output.read()


# *****************************************************************************
class S3Importer(object):


    # -------------------------------------------------------------------------
    def __init__(self, manager):

        """ Constructor

            @param manager: the resource manager (S3ResourceController)

        """

        self.manager = manager
        self.db = self.manager.db


    # -------------------------------------------------------------------------
    def csv(file, table=None):

        """ Import CSV file into database """

        if table:
            table.import_from_csv_file(file)

        else:
            # This is the preferred method as it updates reference fields

            db = self.db

            db.import_from_csv_file(file)
            db.commit()


    # -------------------------------------------------------------------------
    def url(r):

        """ Import data from URL query

            Restriction: can only update single records (no mass-update)

        """

        xml = self.manager.xml

        prefix, name, table, tablename = r.target()

        record = r.record
        resource = r.resource

        # Handle components
        if record and r.component:
            component = resource.components[r.component_name]
            resource = component.resource
            resource.load()
            if len(resource) == 1:
                record = resource.records()[0]
            else:
                record = None
            r.request.vars.update({component.fkey:r.record[component.pkey]})
        elif not record and r.component:
            item = xml.json_message(False, 400, "Invalid Request!")
            return dict(item=item)

        # Check for update
        if record and xml.UID in table.fields:
            r.request.vars.update({xml.UID:record[xml.UID]})

        # Build tree
        element = etree.Element(xml.TAG.resource)
        element.set(xml.ATTRIBUTE.name, resource.tablename)
        for var in r.request.vars:
            if var.find(".") != -1:
                continue
            elif var in table.fields:
                field = table[var]
                value = xml.xml_encode(str(r.request.vars[var]).decode("utf-8"))
                if var in xml.FIELDS_TO_ATTRIBUTES:
                    element.set(var, value)
                else:
                    data = etree.Element(xml.TAG.data)
                    data.set(xml.ATTRIBUTE.field, var)
                    if field.type == "upload":
                        data.set(xml.ATTRIBUTE.filename, value)
                    else:
                        data.text = value
                    element.append(data)
        tree = xml.tree([element], domain=s3xrc.domain)

        # Import data
        result = Storage(committed=False)
        s3xrc.sync_resolve = lambda vector, result=result: result.update(vector=vector)
        try:
            success = resource.import_xml(tree)
        except SyntaxError:
            pass

        # Check result
        if result.vector:
            result = result.vector

        # Build response
        if success and result.committed:
            id = result.id
            method = result.method
            if method == result.METHOD.CREATE:
                item = xml.json_message(True, 201, "Created as %s?%s.id=%s" %
                                        (str(r.there(representation="html", vars=dict())),
                                        result.name, result.id))
            else:
                item = xml.json_message(True, 200, "Record updated")
        else:
            item = xml.json_message(False, 403, "Could not create/update record: %s" %
                                    s3xrc.error or xml.error,
                                    tree=xml.tree2json(tree))

        return dict(item=item)


# *****************************************************************************
class S3SQLTable(SQLTABLE):

    """ Custom version of gluon.sqlhtml.SQLTABLE """

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


# *****************************************************************************
class S3MethodHandler(object):

    """ REST Method Handler Base Class """

    # -------------------------------------------------------------------------
    def __init__(self, db, manager):

        """ Constructor """

        self.db = db
        self.manager = manager

        self.next = None

    # -------------------------------------------------------------------------
    def __call__(self, r, **attr):

        """ Caller, invoked by REST interface """

        # Get the environment
        self.request = r.request
        self.session = r.session
        self.response = r.response

        # Settings
        self.download_url = URL(r=self.request, f="download")

        # Get the right table and method
        self.prefix, self.name, self.table, self.tablename = r.target()
        self.method = r.method
        if r.component:
            self.record = r.component_id
            component = r.resource.components.get(r.component_name, None)
            self.resource = component.resource
            if not self.method:
                if r.multiple and not r.component_id:
                    self.method = "list"
                else:
                    self.method = "read"
        else:
            self.record = r.id
            self.resource = r.resource
            if not self.method:
                if r.id or r.method in ("read", "display"):
                    self.method = "read"
                else:
                    self.method = "list"

        # Invoke the responder
        output = self.respond(r, **attr)

        # Redirection to next
        r.next = self.next

        # Done
        return output


    # -------------------------------------------------------------------------
    def respond(self, r, **attr):

        """ Responder, to be implemented in subclass """

        output = dict()

        return output


    # -------------------------------------------------------------------------
    def readable_fields(self, table, subset=None):

        """ Get a list of all readable fields in a table """

        if subset:
            return [table[f] for f in subset if f in table.fields and table[f].readable]
        else:
            return [table[f] for f in table.fields if table[f].readable]


    # -------------------------------------------------------------------------
    def represent_field(self, field, row, col):

        """ Get the representation for a field value """

        cache = self.manager.cache

        val = row[col]
        try:
            represent = str(cache.ram("%s_repr_%s" % (field, val),
                            lambda: field.represent(val),
                            time_expire=5))
        except:
            if val is None:
                represent = "None"
            else:
                represent = val
                if col == "comments":
                    ur = unicode(represent, "utf8")
                    if len(ur) > 48:
                        represent = ur[:45].encode("utf8") + "..."

        return represent


# *****************************************************************************
class S3CRUDHandler(S3MethodHandler):

    """ Interactive CRUD Method Handler Base Class """

    def respond(self, r, **attr):

        settings = self.manager.s3.crud
        if settings:
            self.formstyle = settings.formstyle
        else:
            self.formstyle = "table3cols"

        self.INTERACTIVE_FORMATS = ("html", "popup", "iframe")

        # Page elements configuration
        self.download_url = None

        vars = self.request.get_vars

        if r.http == "DELETE" or self.method == "delete":
            output = self.delete(r, **attr)

        elif self.method == "create":
            output = self.create(r, **attr)

        elif self.method == "read":
            output = self.read(r, **attr)

        elif self.method == "update":
            output = self.update(r, **attr)

        elif self.method == "list":
            output = self.select(r, **attr)

        #elif self.method == "search":
            #pass

        #elif self.method == "search_simple":
            #pass

        else:
            # Unsupported method
            pass

        representation = r.representation.lower()

        if representation in self.INTERACTIVE_FORMATS and \
           isinstance(output, dict):

            # Resource header
            rheader = attr.get("rheader", None)
            sticky = attr.get("sticky", rheader is not None)

            if rheader and r.id and (r.component or sticky):
                try:
                    rh = rheader(r)
                except TypeError:
                    rh = rheader
                output.update(rheader=rh)

        return output

    # -------------------------------------------------------------------------
    def create(self, r, **attr):

        """ Create new records """

        return dict()

    # -------------------------------------------------------------------------
    def read(self, r, **attr):

        """ Read a single record. """

        return dict()

    # -------------------------------------------------------------------------
    def update(self, r, **attr):

        """ Update a record """

        return dict()

    # -------------------------------------------------------------------------
    def delete(self, r, **attr):

        """ Delete record(s) """

        return dict()

    # -------------------------------------------------------------------------
    def select(self, r, **attr):

        # Initialize output
        output = dict()

        model = self.manager.model
        representation = r.representation.lower()

        # Table specific parameters
        _attr = r.component and r.component.attr or attr
        orderby = _attr.get("orderby", None)
        sortby = _attr.get("sortby", [[1,'asc']])
        linkto = _attr.get("linkto", None)

        # GET vars
        vars = self.request.get_vars

        # Pagination
        if representation == "aadata":
            start = vars.get("iDisplayStart", 0)
            limit = vars.get("iDisplayLength", None)
        else:
            start = vars.get("start", 0)
            limit = vars.get("limit", None)

        if limit is not None:
            try:
                start = int(start)
                limit = int(limit)
            except ValueError:
                start = 0
                limit = None

        # Audit
        audit = self.manager.audit
        audit("list", self.prefix, self.name, representation=representation)

        # Linkto
        if not linkto:
            linkto = self._linkto(r)

        # List fields
        table = self.resource.table
        list_fields = model.get_config(table, "list_fields")
        if not list_fields:
            fields = self.readable_fields(table)
        else:
            fields = self.readable_fields(table, subset=list_fields)
        if not fields:
            fields = [table.id]

        if representation in self.INTERACTIVE_FORMATS:

            # Pagination?
            if self.response.s3.pagination:
                limit = 1

            # Store the query for SSPag
            self.session.s3.filter = self.request.get_vars

            items = self._select(self.resource,
                                 fields=fields,
                                 start=start,
                                 limit=limit,
                                 orderby=orderby,
                                 linkto=linkto,
                                 as_list=False)

            if not items:
                items = "empty set"

            self.response.view = self._view(r, "list.html")
            output.update(items=items)

        elif representation == "aadata":

            # Get the master query for SSPag
            if self.session.s3.filter is not None:
                self.resource.build_query(id=self.record,
                                          url_vars=self.session.s3.filter)

            displayrows = totalrows = self.resource.count()

            # SSPag dynamic filter?
            if vars.sSearch:
                squery = self.ssp_filter(table, fields)
                if squery is not None:
                    self.resource.add_filter(squery)
                    displayrows = self.resource.count()

            # SSPag sorting
            if vars.iSortingCols and orderby is None:
                orderby = self.ssp_orderby(table, fields)

            sEcho = int(vars.sEcho or 0)

            items = self._select(self.resource,
                                 fields=fields,
                                 start=start,
                                 limit=limit,
                                 orderby=orderby,
                                 linkto=linkto,
                                 ssp=True)

            result = dict(sEcho = sEcho,
                          iTotalRecords = totalrows,
                          iTotalDisplayRecords = displayrows,
                          aaData = items)

            output = json(result)


        elif representation == "plain":
            items = self._select(self.resource, fields, as_list=True)
            self.response.view = "plain.html"
            return dict(item=items)

        elif representation == "csv":
            exporter = S3Exporter(self.manager)
            return exporter.csv(self.resource,
                                request=self.request,
                                response=self.response)

        elif representation == "pdf":
            exporter = S3Exporter(self.manager)
            return exporter.pdf(self.resource,
                                request=self.request,
                                response=self.response,
                                list_fields=list_fields)

        elif representation == "xls":
            exporter = S3Exporter(self.manager)
            return exporter.xls(self.resource,
                                request=self.request,
                                response=self.response,
                                list_fields=list_fields)

        else:
            # Unsupported format
            pass

        return output

    # -------------------------------------------------------------------------
    def _create(self, resource):

        """ Provide and process a create form for a resource """

        # Get onvalidation callback
        onvalidation = model.get_config(table, "create_onvalidation")
        if onvalidation is None:
            onvalidation = model.get_config(table, "onvalidation") or []

        # Get onaccept callback
        onaccept = model.get_config(table, "create_onaccept")
        if onaccept is None:
            onaccept =  model.get_config(table, "onaccept") or []

        # Get CRUD message
        #if message == DEFAULT:
            #message = self.messages.record_created
        message = "Record created"

        return self.update(resource, None,
                           onvalidation=onvalidation,
                           onaccept=onaccept,
                           message=message)


    # -------------------------------------------------------------------------
    def _read(self, resource, id):

        """ Provide a read view of a record

            @param resource: the resource
            @param id: the record id

        """

        table = resource.table

        form = SQLFORM(table, id,
                       readonly=True,
                       comments=False,
                       upload=self.download_url,
                       showid=False,
                       formstyle=self.formstyle)

        return form

    # -------------------------------------------------------------------------
    def _update(self, resource, id,
                onvalidation=None,
                onaccept=None,
                message=None):

        table = resource.table
        model = self.manager.model

        if onvalidation is None:
            onvalidation = model.get_config(table, "update_onvalidation")
            if onvalidation is None:
                onvalidation = model.get_config(table, "onvalidation")

        if onaccept is None:
            onaccept = model.get_config(table, "update_onaccept")
            if onaccept is None:
                onaccept = model.get_config(table, "onaccept")

        if not onvalidation:
            onvalidation = None

        # Get environment
        request = self.request
        response = self.response
        session = self.session

        # Get the message
        #if message == DEFAULT:
            #message = self.messages.record_updated
        if message is None:
            message = "Record updated"

        # Get the form
        form = SQLFORM(table, record,
            #hidden=dict(_next=next),

            showid=False,

            submit_button=self.messages.submit_button,
            delete_label=self.messages.delete_label,

            deletable=False,

            upload=self.download_url,
            formstyle=self.formstyle)

        formname = "%s/%s" % (table._tablename, form.record_id)

        keepvalues = self.settings.keepvalues
        if request.vars.delete_this_record:
            keepvalues = False

        # Process the form
        if form.accepts(request.post_vars,
                        session,
                        formname=formname,
                        onvalidation=onvalidation,
                        keepvalues=keepvalues,
                        hideerror=False):

            # Update message
            response.flash = message

            # Audit
            # not implemented yet

            # Execute onaccept
            if onaccept:
                self.callback(onaccept, form, table._tablename)

        return form


    # -------------------------------------------------------------------------
    #def _delete(self, table, record):

    # -------------------------------------------------------------------------
    def _select(self, resource,
                fields=None,
                start=0,
                limit=None,
                orderby=None,
                linkto=None,
                ssp=False,
                as_list=False):

        """ Provide an interactive list of records in the resource """

        table = resource.table
        query = resource.get_query()

        if not fields:
            fields = [table.id]

        if limit is not None:
            limitby = (start, start + limit)
        else:
            limitby = None

        rows = self.db(query).select(*fields, **dict(orderby=orderby,
                                                     limitby=limitby))

        if not rows:
            return None

        if ssp:

            items = [[self.ssp_represent_field(f, row, f.name, linkto=linkto)
                    for f in fields]
                    for row in rows]

        elif as_list:

            items = rows.as_list()

        else:

            headers = dict(map(lambda f: (str(f), f.label), fields))
            items= S3SQLTable(rows,
                              headers=headers,
                              linkto=linkto,
                              upload=self.download_url,
                              _id="list", _class="display")

        return items


    # -------------------------------------------------------------------------
    def _view(self, r, default, format=None):

        """ Get the target view path """

        request = r.request

        folder = request.folder
        prefix = request.controller

        if r.component:

            view = "%s_%s_%s" % (r.name, r.component_name, default)
            path = os.path.join(folder, "views", prefix, view)

            if os.path.exists(path):
                return "%s/%s" % (prefix, view)
            else:
                view = "%s_%s" % (r.name, default)
                path = os.path.join(folder, "views", prefix, view)

        else:
            if format:
                view = "%s_%s_%s" % (r.name, default, format)
            else:
                view = "%s_%s" % (r.name, default)
            path = os.path.join(folder, "views", prefix, view)

        if os.path.exists(path):
            return "%s/%s" % (prefix, view)
        else:
            if format:
                return default.replace(".html", "_%s.html" % format)
            else:
                return default

    # -------------------------------------------------------------------------
    def _linkto(self, r, authorised=None, update=None, native=False):

        """ Linker for the record ID column in lists """

        c = None
        f = None

        permit = self.manager.auth.shn_has_permission
        response = self.response

        if r.component:
            if authorised is None:
                authorised = permit("update", r.component.tablename)
            if authorised and update:
                linkto = r.component.attr.get("linkto_update", None)
            else:
                linkto = r.component.attr.get("linkto", None)
            if native:
                # link to native component controller (be sure that you have one)
                c = r.component.prefix
                f = r.component.name
        else:
            if authorised is None:
                authorised = permit("update", r.tablename)
            if authorised and update:
                linkto = response.s3.get("linkto_update", None)
            else:
                linkto = response.s3.get("linkto", None)

        def list_linkto(record_id, r=r, c=c, f=f, linkto=linkto,
                        update=authorised and update):

            if linkto:
                try:
                    url = str(linkto(record_id))
                except TypeError:
                    url = linkto % record_id
                return url
            else:
                if r.component:
                    if c and f:
                        args = [record_id]
                    else:
                        c = r.request.controller
                        f = r.request.function
                        args = [r.id, r.component_name, record_id]
                    if update:
                        return str(URL(r=r.request, c=c, f=f, args=args + ["update"], vars=r.request.vars))
                    else:
                        return str(URL(r=r.request, c=c, f=f, args=args, vars=r.request.vars))
                else:
                    args = [record_id]
                    if update:
                        return str(URL(r=r.request, c=c, f=f, args=args + ["update"]))
                    else:
                        return str(URL(r=r.request, c=c, f=f, args=args))

        return list_linkto


    # -------------------------------------------------------------------------
    def crud_string(self, tablename, name):

        s3 = self.manager.s3

        crud_strings = s3.crud_strings.get(tablename, s3.crud_strings)
        not_found = s3.crud_strings.get(name, None)

        return crud_strings.get(name, not_found)


    # -------------------------------------------------------------------------
    def ssp_filter(self, table, fields):

        vars = self.request.get_vars

        context = str(vars.sSearch).lower()
        columns = int(vars.iColumns)

        searchq = None

        wildcard = "%%%s%%" % context

        for i in xrange(0, columns):
            field = fields[i]
            query = None
            if str(field.type) == "integer":
                requires = field.requires
                if not isinstance(requires, (list, tuple)):
                    requires = [requires]
                if requires:
                    r = requires[0]
                    if isinstance(r, IS_EMPTY_OR):
                        r = r.other
                    try:
                        options = r.options()
                    except:
                        continue
                    vlist = []
                    for (value, text) in options:
                        if str(text).lower().find(context) != -1:
                            vlist.append(value)
                    if vlist:
                        query = field.belongs(vlist)
                else:
                    continue

            elif str(field.type) in ("string", "text"):
                query = field.lower().like(wildcard)

            if searchq is None and query:
                searchq = query
            elif query:
                searchq = searchq | query

        return searchq


    # -------------------------------------------------------------------------
    def ssp_orderby(self, table, fields):

        vars = self.request.get_vars

        tablename = table._tablename

        iSortingCols = int(vars["iSortingCols"])

        #colname = lambda i: \
                  #"%s.%s" % (tablename,
                  #fields[int(vars["iSortCol_%s" % str(i)])])

        colname = lambda i: fields[int(vars["iSortCol_%s" % str(i)])]

        def direction(i):
            dir = vars["sSortDir_%s" % str(i)]
            return dir and " %s" % dir or ""

        return ", ".join(["%s%s" %
                        (colname(i), direction(i))
                        for i in xrange(iSortingCols)])

    # -------------------------------------------------------------------------
    def ssp_represent_field(self, field, row, col, linkto=None):

        if col == "id" and linkto:
            id = str(row[col])
            # Remove SSPag variables, but keep "next":
            next = self.request.vars.next
            self.request.vars = Storage(next=next)
            # use linkto to produce ID column links:
            try:
                href = linkto(id)
            except TypeError:
                href = linkto % id
            href = str(href).replace(".aadata", "")
            href = str(href).replace(".aaData", "")
            return A(self.represent_field(field, row, col), _href=href).xml()
        else:
            return self.represent_field(field, row, col)


# *****************************************************************************
