# -*- coding: utf-8 -*-

""" S3XRC Resource Framework - Resource Export Toolkit

    @version: 2.2.1

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>} on Eden wiki

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

__all__ = ["S3Exporter"]

import StringIO, datetime

from gluon.http import HTTP, redirect
from gluon.html import URL
from gluon.storage import Storage
from gluon.contenttype import contenttype

from lxml import etree

# *****************************************************************************
class S3Exporter(object):

    """ Exporter toolkit """

    def __init__(self, manager):

        """ Constructor

            @param manager: the resource controller

            @todo 2.2: error message completion

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
            template=None,
            pretty_print=False, **args):

        """ Export a resource as XML

            @param resource: the resource
            @param start: index of the first record to export (slicing)
            @param limit: maximum number of records to export (slicing)
            @param marker: URL of the default map marker
            @param msince: export only records which have been modified
                           after this datetime
            @param show_urls: add the resource URLs as attribute to
                              <resource> elements
            @param dereference: include referenced resources
            @param template: path to the XSLT stylesheet (if required)
            @param pretty_print: insert newlines/indentation in the output
            @param args: dict of arguments to pass to the XSLT stylesheet

        """

        args = Storage(args)

        tree = self.manager.export_tree(resource,
                                        audit=self.manager.audit,
                                        start=start,
                                        limit=limit,
                                        marker=marker,
                                        msince=msince,
                                        show_urls=show_urls,
                                        dereference=dereference)

        if tree and template is not None:
            tfmt = "%Y-%m-%d %H:%M:%S"
            args.update(domain=self.manager.domain,
                        base_url=self.manager.base_url,
                        prefix=resource.prefix,
                        name=resource.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt))

            tree = self.manager.xml.transform(tree, template, **args)

        if tree:
            return self.manager.xml.tostring(tree, pretty_print=pretty_print)
        else:
            return None


    # -------------------------------------------------------------------------
    def json(self, resource,
             start=None,
             limit=None,
             marker=None,
             msince=None,
             show_urls=True,
             dereference=True,
             template=None,
             pretty_print=False, **args):

        """ Export a resource as JSON

            @param resource: the resource
            @param start: index of the first record to export (slicing)
            @param limit: maximum number of records to export (slicing)
            @param marker: URL of the default map marker
            @param msince: export only records which have been modified
                           after this datetime
            @param show_urls: add the resource URLs as attribute to
                              <resource> elements
            @param dereference: include referenced resources
            @param template: path to the XSLT stylesheet (if required)
            @param pretty_print: insert newlines/indentation in the output
            @param args: dict of arguments to pass to the XSLT stylesheet

        """

        args = Storage(args)

        tree = self.manager.export_tree(resource,
                                        audit=self.manager.audit,
                                        start=start,
                                        limit=limit,
                                        marker=marker,
                                        msince=msince,
                                        show_urls=show_urls,
                                        dereference=dereference)

        if tree and template is not None:
            tfmt = "%Y-%m-%d %H:%M:%S"
            args.update(domain=self.manager.domain,
                        base_url=self.manager.base_url,
                        prefix=resource.prefix,
                        name=resource.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt))

            tree = self.manager.xml.transform(tree, template, **args)

        if tree:
            return self.manager.xml.tree2json(tree, pretty_print=pretty_print)
        else:
            return None


    # -------------------------------------------------------------------------
    def csv(self, resource):

        """ Export resource as CSV (does not include components)

            @param resource: the resource to export

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

        return str(db(query).select())


    # -------------------------------------------------------------------------
    def pdf(self, resource, list_fields=None):

        """ Export resource as Adobe PDF (does not include components)

            @param resource: the resource
            @param list_fields: fields to include in list views

            @todo 2.2: fix error messages
            @todo 2.2: do not redirect
            @todo 2.2: PEP-8
            @todo 2.2: test this!

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
        except ImportError:
            session.error = self.ERROR.REPORTLAB_ERROR
            redirect(URL(r=request, f="index", extension=""))

        # Import Geraldo
        try:
            from geraldo import Report, ReportBand, Label, ObjectValue, SystemField, landscape, BAND_WIDTH
            from geraldo.generators import PDFGenerator
        except ImportError:
            session.error = self. ERROR.GERALDO_ERROR
            redirect(URL(r=request, f="index", extension=""))

        # Get records
        query = resource.get_query()
        records = db(query).select(table.ALL)
        if not records:
            session.warning = self.ERROR.NO_RECORDS
            redirect(URL(r=request, f="index", extension=""))

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

        represent = self.manager.represent

        _represent = lambda field, value, table=table: \
                     represent(table[field],
                               value=value,
                               strip_markup=True,
                               xml_escape=True)

        for field in fields:
            # Append label
            label = Label(text=xml.xml_encode(str(field.label))[:16].decode("utf-8"),
                          top=0.8*cm, left=LEFTMARGIN*cm)
            _elements.append(label)

            # Append value
            value = ObjectValue(attribute_name = field.name,
                                left = LEFTMARGIN * cm,
                                width = COLWIDTH * cm,
                                get_value = lambda instance, column = field.name: \
                                            _represent(column, instance[column]))
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

        """ Export record(s) as Microsoft Excel spreadsheet

            @param resource: the resource
            @param list_fields: fields to include in list views

            @todo 2.2: PEP-8
            @todo 2.2: use S3Resource.readable_fields
            @todo: implement audit

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
            redirect(URL(r=request))

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

                represent = self.manager.represent(field,
                                                   record=item,
                                                   strip_markup=True,
                                                   xml_escape=True)
                ## Check for a custom.represent (e.g. for ref fields)
                #represent = resource._represent(item, field.name)
                ## Filter out markup from text
                #if isinstance(represent, basestring) and "<" in represent:
                    #try:
                        #markup = etree.XML(represent)
                        #represent = markup.xpath(".//text()")
                        #if represent:
                            #represent = " ".join(represent)
                    #except etree.XMLSyntaxError:
                        #pass

                rowx.write(cell1, str(represent), style)
                cell1 += 1
        book.save(output)
        output.seek(0)
        response.headers["Content-Type"] = contenttype(".xls")
        filename = "%s_%s.xls" % (request.env.server_name, str(table))
        response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
        return output.read()


# *****************************************************************************
