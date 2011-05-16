# -*- coding: utf-8 -*-

""" Resource Export Tools

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{gluon}} <http://web2py.com>}
    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}
    @requires: U{B{I{ReportLab}} <http://www.reportlab.com/software/opensource>}
    @requires: U{B{I{Geraldo}} <http://www.geraldoreports.org>}
    @requires: U{B{I{Xlwt}} <http://pypi.python.org/pypi/xlwt>}

    @author: Dominic König <dominic[at]aidiq.com>

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

__all__ = ["S3Exporter"]

import StringIO, datetime

from gluon.http import HTTP, redirect
from gluon.html import URL
from gluon.storage import Storage
from gluon.contenttype import contenttype

from lxml import etree

# *****************************************************************************
class S3Exporter(object):

    """
    Exporter toolkit

    """

    def __init__(self, manager):
        """
        Constructor

        @param manager: the S3ResourceController

        @todo 2.3: error message completion

        """

        self.manager = manager

        T = manager.T

        self.db = self.manager.db
        self.s3 = self.manager.s3

        self.ERROR = Storage(
            REPORTLAB_ERROR = T("ReportLab not installed"),
            GERALDO_ERROR = T("Geraldo not installed"),
            NO_RECORDS = T("No records in this resource"),
            XLWT_ERROR = T("Xlwt not installed"),
        )

    # -------------------------------------------------------------------------
    def xml(self, resource,
            start=None,
            limit=None,
            marker=None,
            msince=None,
            show_urls=True,
            dereference=True,
            stylesheet=None,
            as_json=False,
            pretty_print=False,
            allow_all=False, **args):
        """
        Export a resource as S3XML

        @param resource: the resource
        @param start: index of the first record to export (slicing)
        @param limit: maximum number of records to export (slicing)
        @param marker: URL of the default map marker
        @param msince: export only records which have been modified
                        after this datetime
        @param show_urls: add the resource URLs as attribute to
                            <resource> elements
        @param dereference: include referenced resources
        @param stylesheet: path to the XSLT stylesheet (if required)
        @param as_json: represent the XML tree as JSON
        @param pretty_print: insert newlines/indentation in the output
        @param allow_all: bool: allow to return all records even if
                          number of records is over limiting value
        @param args: dict of arguments to pass to the XSLT stylesheet

        """

        output = None

        args = Storage(args)
        xml = self.manager.xml

        if not allow_all:
            limit = self._overwrite_limit(start, limit)

        # Export as element tree
        tree = self.manager.export_tree(resource,
                                        audit=self.manager.audit,
                                        start=start,
                                        limit=limit,
                                        marker=marker,
                                        msince=msince,
                                        show_urls=show_urls,
                                        dereference=dereference)

        # XSLT transformation
        if tree and stylesheet is not None:
            tfmt = xml.ISOFORMAT
            args.update(domain=self.manager.domain,
                        base_url=self.manager.s3.base_url,
                        prefix=resource.prefix,
                        name=resource.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt))

            # @todo 2.3: catch transformation errors!
            tree = xml.transform(tree, stylesheet, **args)

        # Convert into string
        # (Content Headers are set by the calling function)
        if tree:
            if as_json:
                output = xml.tree2json(tree, pretty_print=pretty_print)
            else:
                output = xml.tostring(tree, pretty_print=pretty_print)

        return output

    # -------------------------------------------------------------------------
    def csv(self, resource):
        """
        Export resource as CSV (does not include components)

        @param resource: the resource to export

        @note: export does not include components!

        @todo: implement audit

        """

        db = self.db

        request = self.manager.request
        response = self.manager.response

        tablename = resource.tablename
        query = resource.get_query()

        if response:
            servername = request and "%s_" % request.env.server_name or ""
            filename = "%s%s.csv" % (servername, tablename)
            response.headers["Content-Type"] = contenttype(".csv")
            response.headers["Content-disposition"] = "attachment; filename=%s" % filename

        limit = self._overwrite_limit()
        if limit is None:
            rows = db(query).select()
        else:
            rows = db(query).select(resource.table.ALL, limitby=(0, limit))

        return str(rows)


    # -------------------------------------------------------------------------
    def pdf(self, resource, list_fields=None):
        """
        Export a resource as Adobe PDF (does not include components!)

        @param resource: the resource
        @param list_fields: fields to include in list views

        @note: export does not include components!

        @todo 2.3: fix error messages
        @todo 2.3: do not redirect
        @todo 2.3: PEP-8
        @todo 2.3: test this!

        @todo: implement audit

        """

        db = self.db
        table = resource.table

        session = self.manager.session
        request = self.manager.request
        response = self.manager.response

        xml = self.manager.xml

        # Import ReportLab
        try:
            from reportlab.lib.units import cm
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT
            from reportlab.pdfbase import pdfmetrics
        except ImportError:
            session.error = self.ERROR.REPORTLAB_ERROR
            redirect(URL(r=request, extension=""))

        # Import Geraldo
        try:
            from geraldo import Report, ReportBand, Label, ObjectValue, SystemField, landscape, BAND_WIDTH
            from geraldo.generators import PDFGenerator
        except ImportError:
            session.error = self.ERROR.GERALDO_ERROR
            redirect(URL(r=request, extension=""))

        # Get records
        query = resource.get_query()
        records = db(query).select(table.ALL)
        if not records:
            session.warning = self.ERROR.NO_RECORDS
            redirect(URL(r=request, extension=""))

        # Create output stream
        output = StringIO.StringIO()

        # Find fields
        fields = None
        table = resource.table
        if not list_fields:
            fields = resource.readable_fields()
        else:
            fields = resource.readable_fields(subset=list_fields)
        if not fields:
            fields = [table.id]

        if "SazanamiGothic" in pdfmetrics.getRegisteredFontNames():
            font_name = "SazanamiGothic"
            widget_style = {"fontName": "SazanamiGothic"}
        else:
            font_name = "Helvetica-Bold"
            widget_style = {}

        # Export
        _elements = [ SystemField(
                            expression = "%(report_title)s",
                            top = 0.1 * cm,
                            left = 0,
                            width = BAND_WIDTH,
                            style = {
                                "fontName": font_name,
                                "fontSize": 14,
                                "alignment": TA_CENTER
                                }
                            )]
        detailElements = []
        COLWIDTH = 2.5
        LEFTMARGIN = 0.2

        represent = self.manager.represent

        _represent = lambda field, value, table=table: \
                     represent(table[field],
                               value=value,
                               strip_markup=True,
                               xml_escape=True)

        for field in fields:
            # Append label
            label = Label(text = xml.xml_encode(str(field.label)).decode("utf-8")[:16],
                          top = 0.8 * cm,
                          left = LEFTMARGIN * cm,
                          style = widget_style
                          )
            _elements.append(label)

            # Append value
            value = ObjectValue(attribute_name = field.name,
                                left = LEFTMARGIN * cm,
                                width = COLWIDTH * cm,
                                get_value = lambda instance, column = field.name: \
                                            _represent(column, instance[column]),
                                style = widget_style
                                )
            detailElements.append(value)

            # Increase left margin
            LEFTMARGIN += COLWIDTH

        #mod, res = str(table).split("_", 1)
        mod = resource.prefix
        res = resource.name
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
            response.headers["Content-Type"] = contenttype(".pdf")
            response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename

        # Return the stream
        output.seek(0)
        return output.read()


    # -------------------------------------------------------------------------
    def xls(self, resource, list_fields=None):
        """
        Export a resource as Microsoft Excel spreadsheet

        @param resource: the resource
        @param list_fields: fields to include in list views

        @note: export does not include components!

        @todo 2.3: PEP-8
        @todo 2.3: implement audit
        @todo 2.3: use S3Resource.readable_fields
        @todo 2.3: use separate export_fields instead of list_fields

        """

        db = self.db

        session = self.manager.session
        request = self.manager.request
        response = self.manager.response

        table = resource.table
        query = resource.get_query()

        try:
            import xlwt
        except ImportError:
            session.error = self.ERROR.XLWT_ERROR
            #redirect(r.there(representation="html"))
            redirect(URL(r=request, extension=""))

        output = StringIO.StringIO()

        # items = db(query).select(table.ALL)

        fields = None
        if list_fields:
            # AT:
            fields = []
            for f in list_fields:
                if '.' in f:
                    tab, col = f.split('.')
                    fields.append(self.db.get(tab,None)[col])
                elif f in table.fields:
                    fields.append(table[f])
        if fields and len(fields) == 0:
            fields.append(table.id)
        if not fields:
            fields = [table[f] for f in table.fields if table[f].readable]

        items = db(query).select(*fields)

        book = xlwt.Workbook(encoding="utf-8")
        sheet1 = book.add_sheet(str(table))
        # Header row
        row0 = sheet1.row(0)
        cell = 0

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
                represent = self.manager.represent(field,
                                                   record=item,
                                                   strip_markup=True,
                                                   xml_escape=True)
                rowx.write(cell1, unicode(represent), style)
                cell1 += 1
        book.save(output)
        output.seek(0)
        response.headers["Content-Type"] = contenttype(".xls")
        filename = "%s_%s.xls" % (request.env.server_name, str(table))
        response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
        return output.read()


    # -------------------------------------------------------------------------
    def json(self, resource,
             start=None,
             limit=None,
             fields=None,
             orderby=None):
        """
        Export a resource as JSON

        @note: export does not include components!

        @param resource: the resource to export
        @param start: index of the first record to export (for slicing)
        @param limit: maximum number of records to export (for slicing)
        @param fields: fields to include in the export (None for all fields)

        """

        response = self.manager.response

        if fields is None:
            fields = [f for f in resource.table if f.readable]

        attributes = dict()

        if orderby is not None:
            attributes.update(orderby=orderby)

        limit = self._overwrite_limit(start, limit)
        limitby = resource.limitby(start=start, limit=limit)
        if limitby is not None:
            attributes.update(limitby=limitby)

        # Get the rows and return as json
        rows = resource.select(*fields, **attributes)

        if response:
            response.headers["Content-Type"] = "application/json"

        return rows.json()


    # -------------------------------------------------------------------------
    def _overwrite_limit(self, start=None, limit=None):
        max_results = self.manager.auth.deployment_settings.get_limiter('exporter')

        if max_results is None \
          or (limit and limit <= max_results) \
          or (not limit and start is not None) \
          or self.manager.auth.s3_has_role(1):
            return limit

        return max_results

# *****************************************************************************
