# -*- coding: utf-8 -*-

"""
    CRUD+LS Method Handlers (Frontend for S3REST)

    @author: Fran Boon <fran@aidiq.com>
    @author: nursix

    @see: U{http://eden.sahanafoundation.org/wiki/RESTController}

    HTTP Status Codes: http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
"""

# *****************************************************************************
# Constants to ensure consistency

# XSLT Settings
XSLT_FILE_EXTENSION = "xsl" #: File extension of XSLT templates
XSLT_IMPORT_TEMPLATES = "static/xslt/import" #: Path to XSLT templates for data import
XSLT_EXPORT_TEMPLATES = "static/xslt/export" #: Path to XSLT templates for data export

# XSLT available formats
shn_xml_import_formats = ["xml", "lmx", "osm", "pfif", "ushahidi", "odk", "agasti", "fods"] #: Supported XML import formats
shn_xml_export_formats = dict(
    xml = "application/xml",
    gpx = "application/xml",
    lmx = "application/xml",
    pfif = "application/xml",
    have = "application/xml",
    osm = "application/xml",
    rss = "application/rss+xml",
    georss = "application/rss+xml",
    kml = "application/vnd.google-earth.kml+xml",
    #geojson = "application/xml"
) #: Supported XML output formats and corresponding response headers

shn_json_import_formats = ["json"] #: Supported JSON import formats
shn_json_export_formats = dict(
    json = "text/x-json",
    geojson = "text/x-json"
) #: Supported JSON output formats and corresponding response headers

shn_interactive_view_formats = ("html", "popup", "iframe")

# Error messages
UNAUTHORISED = T("Not authorised!")
BADFORMAT = T("Unsupported data format!")
BADMETHOD = T("Unsupported method!")
BADRECORD = T("Record not found!")
INVALIDREQUEST = T("Invalid request!")
XLWT_ERROR = T("xlwt module not available within the running Python - this needs installing for XLS output!")
GERALDO_ERROR = T("Geraldo module not available within the running Python - this needs installing for PDF output!")
REPORTLAB_ERROR = T("ReportLab module not available within the running Python - this needs installing for PDF output!")

# How many rows to show per page in list outputs
ROWSPERPAGE = 20
PRETTY_PRINT = True

# *****************************************************************************
# Resource Manager
_s3xrc = local_import("s3xrc")

s3xrc = _s3xrc.S3ResourceController(
            #db,
            globals(),
            domain=request.env.server_name,
            base_url="%s/%s" % (deployment_settings.get_base_public_url(),
                                request.application),
            #cache=cache,
            #auth=auth,
            #gis=gis,
            rpp=ROWSPERPAGE,
            xml_import_formats = shn_xml_import_formats,
            xml_export_formats = shn_xml_export_formats,
            json_import_formats = shn_json_import_formats,
            json_export_formats = shn_json_export_formats,
            debug = False)

# *****************************************************************************
def shn_field_represent(field, row, col):

    """
        Representation of a field
        Used by:
         * export_xls()
         * shn_list()
           .aaData representation for dataTables' Server-side pagination
    """

    val = row[col]
    try:
        represent = str(cache.ram("%s_repr_%s" % (field, val),
                                  lambda: field.represent(val),
                                  time_expire=5))
    except:
        if val is None:
            represent = NONE
        else:
            represent = val
            if col == "comments":
                ur = unicode(represent, "utf8")
                if len(ur) > 48:
                    represent = ur[:45].encode("utf8") + "..."

    return represent


def shn_strip_aadata_extension(url):

    """ strip away ".aaData" extension """

    url = str(url).replace(".aaData", "")
    url = str(url).replace(".aadata", "")

    return url


def shn_field_represent_sspage(field, row, col, linkto=None):

    """ Represent columns in SSPage responses """

    # TODO: put this function into XRequest

    if col == "id":
        id = str(row[col])
        # Remove SSPag variables, but keep "next":
        next = request.vars.next
        request.vars = Storage(next=next)
        # use linkto to produce ID column links:
        try:
            href = linkto(id)
        except TypeError:
            href = linkto % id
        href = shn_strip_aadata_extension(href)
        return A(shn_field_represent(field, row, col), _href=href).xml()
    else:
        return shn_field_represent(field, row, col)

# *****************************************************************************
# Exports

#
# export_csv ------------------------------------------------------------------
#
def export_csv(resource, query, record=None):

    """ Export record(s) as CSV """

    import gluon.contenttype
    response.headers["Content-Type"] = gluon.contenttype.contenttype(".csv")
    if record:
        filename = "%s_%s_%d.csv" % (request.env.server_name, resource, record)
    else:
        # List
        filename = "%s_%s_list.csv" % (request.env.server_name, resource)
    response.headers["Content-disposition"] = "attachment; filename=%s" % filename
    return str(db(query).select())

#
# export_pdf ------------------------------------------------------------------
#
def export_pdf(table, query, list_fields=None):

    """ Export record(s) as Adobe PDF """

    try:
        from reportlab.lib.units import cm
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    except ImportError:
        session.error = REPORTLAB_ERROR
        redirect(URL(r=request))
    try:
        from geraldo import Report, ReportBand, Label, ObjectValue, SystemField, landscape, BAND_WIDTH
        from geraldo.generators import PDFGenerator
    except ImportError:
        session.error = GERALDO_ERROR
        redirect(URL(r=request))

    records = db(query).select(table.ALL)
    if not records:
        session.warning = T("No data in this table - cannot create PDF!")
        redirect(URL(r=request))

    import StringIO
    output = StringIO.StringIO()

    fields = None
    if list_fields:
        fields = [table[f] for f in list_fields if table[f].readable]
    if fields and len(fields) == 0:
        fields.append(table.id)
    if not fields:
        fields = [table[f] for f in table.fields if table[f].readable]
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

    output.seek(0)
    import gluon.contenttype
    response.headers["Content-Type"] = gluon.contenttype.contenttype(".pdf")
    filename = "%s_%s.pdf" % (request.env.server_name, str(table))
    response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
    return output.read()

#
# export_xls ------------------------------------------------------------------
#
def export_xls(table, query, list_fields=None):

    """ Export record(s) as XLS """

    # TODO: make this function XRequest-aware

    try:
        import xlwt
    except ImportError:
        session.error = XLWT_ERROR
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
# Imports

#
# import_csv ------------------------------------------------------------------
#
def import_csv(file, table=None):

    """ Import CSV file into Database """

    if table:
        table.import_from_csv_file(file)
    else:
        # This is the preferred method as it updates reference fields
        db.import_from_csv_file(file)
        db.commit()
#
# import_url ------------------------------------------------------------------
#
def import_url(r):

    """ Import data from URL query

        Restriction: can only update single records (no mass-update)

    """

    xml = s3xrc.xml

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
# Audit
#
# These functions should always return True in order to be chainable
# by "and" for lambda's as onaccept-callbacks. -- nursix --

s3_audit = _s3xrc.S3Audit(db, session, migrate=migrate)
s3xrc.audit = s3_audit

# *****************************************************************************
# Display Representations

# t2.itemize now deprecated
# but still used for t2.search

#
# shn_represent ---------------------------------------------------------------
#
def shn_represent(table, module, resource, deletable=True, main="name", extra=None):

    """ Designed to be called via table.represent to make t2.search() output useful """

    db[table].represent = lambda table: \
                          shn_list_item(table, resource,
                                        action="display",
                                        main=main,
                                        extra=shn_represent_extra(table,
                                                                  module,
                                                                  resource,
                                                                  deletable,
                                                                  extra))
    return

#
# shn_represent_extra ---------------------------------------------------------
#
def shn_represent_extra(table, module, resource, deletable=True, extra=None):

    """ Display more than one extra field (separated by spaces)"""

    authorised = shn_has_permission("delete", table._tablename)
    item_list = []
    if extra:
        extra_list = extra.split()
        for any_item in extra_list:
            item_list.append("TD(db(db.%s_%s.id==%i).select()[0].%s)" % \
                             (module, resource, table.id, any_item))
    if authorised and deletable:
        item_list.append("TD(INPUT(_type='checkbox', _class='delete_row', _name='%s', _id='%i'))" % \
                         (resource, table.id))
    return ",".join( item_list )

#
# shn_list_item ---------------------------------------------------------------
#
def shn_list_item(table, resource, action, main="name", extra=None):

    """ Display nice names with clickable links & optional extra info """

    item_list = [TD(A(table[main], _href=URL(r=request, f=resource, args=[table.id, action])))]
    if extra:
        item_list.extend(eval(extra))
    items = DIV(TABLE(TR(item_list)))
    return DIV(*items)

#
# shn_custom_view -------------------------------------------------------------
#
def shn_custom_view(r, default_name, format=None):

    """ Check for custom view """

    prefix = r.request.controller

    if r.component:

        custom_view = "%s_%s_%s" % (r.name, r.component_name, default_name)

        _custom_view = os.path.join(request.folder, "views", prefix, custom_view)

        if not os.path.exists(_custom_view):
            custom_view = "%s_%s" % (r.name, default_name)
            _custom_view = os.path.join(request.folder, "views", prefix, custom_view)

    else:
        if format:
            custom_view = "%s_%s_%s" % (r.name, default_name, format)
        else:
            custom_view = "%s_%s" % (r.name, default_name)
        _custom_view = os.path.join(request.folder, "views", prefix, custom_view)

    if os.path.exists(_custom_view):
        response.view = "%s/%s" % (prefix, custom_view)
    else:
        if format:
            response.view = default_name.replace(".html", "_%s.html" % format)
        else:
            response.view = default_name

#
# shn_convert_orderby ----------------------------------------------------------
#
def shn_get_columns(table):
    return [f for f in table.fields if table[f].readable]

def shn_convert_orderby(table, request, fields=None):

    tablename = table._tablename

    cols = fields or shn_get_columns(table)
    iSortingCols = int(request.vars["iSortingCols"])

    colname = lambda i: \
              "%s.%s" % (tablename,
              cols[int(request.vars["iSortCol_%s" % str(i)])])

    def direction(i):
        dir = request.vars["sSortDir_%s" % str(i)]
        return dir and " %s" % dir or ""

    return ", ".join(["%s%s" %
                     (colname(i), direction(i))
                     for i in xrange(iSortingCols)])

#
# shn_build_ssp_filter --------------------------------------------------------
#
def shn_build_ssp_filter(table, request, fields=None):

    cols = fields or shn_get_columns(table)
    searchq = None

    context = str(request.vars.sSearch).lower()
    wildcard = "%%%s%%" % context

    # TODO: use FieldS3 (with representation_field)
    for i in xrange(0, int(request.vars.iColumns)):
        field = table[cols[i]]
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
            query = table[cols[i]].lower().like(wildcard)

        if searchq is None and query:
            searchq = query
        elif query:
            searchq = searchq | query

    return searchq

# *****************************************************************************
# REST Method Handlers
#
# These functions are to handle REST methods.
# Currently implemented methods are:
#
#   - list
#   - read
#   - create
#   - update
#   - delete
#   - search
#
# Handlers must be implemented as:
#
#   def method_handler(r, **attr)
#
# where:
#
#   r - is the S3Request
#   attr - attributes of the call, passed through
#

#
# shn_read --------------------------------------------------------------------
#
def shn_read(r, **attr):

    """ Read a single record. """

    prefix, name, table, tablename = r.target()
    representation = r.representation.lower()

    # Get the callbacks of the target table
    onvalidation = s3xrc.model.get_config(table, "onvalidation")
    onaccept = s3xrc.model.get_config(table, "onaccept")
    list_fields = s3xrc.model.get_config(table, "list_fields")

    # Get the controller attributes
    rheader = attr.get("rheader", None)
    sticky = attr.get("sticky", rheader is not None)

    # Get the table-specific attributes
    _attr = r.component and r.component.attr or attr
    main = _attr.get("main", None)
    extra = _attr.get("extra", None)
    caller = _attr.get("caller", None)
    editable = _attr.get("editable", True)
    deletable = _attr.get("deletable", True)

    # Delete & Update links
    href_delete = r.other(method="delete", representation=representation)
    href_edit = r.other(method="update", representation=representation)

    # Get the correct record ID
    if r.component:
        resource = r.resource.components.get(r.component_name).resource
        resource.load(start=0, limit=1)
        if not len(resource):
            if not r.multiple:
                r.component_id = None
                if shn_has_permission("create", tablename):
                    redirect(r.other(method="create", representation=representation))
                else:
                    record_id = None
            else:
                session.error = BADRECORD
                redirect(r.there())
        else:
            record_id = resource.records().first().id
    else:
        record_id = r.id

    # Redirect to update if user has permission unless URL method specified
    if not r.method:
        authorised = shn_has_permission("update", tablename, record_id)
        if authorised and representation == "html" and editable:
            return shn_update(r, **attr)

    # Check for read permission
    authorised = shn_has_permission("read", tablename, record_id)
    if not authorised:
        r.unauthorised()

    # Audit
    s3xrc.audit("read", prefix, name,
                record=record_id, representation=representation)

    if r.representation in shn_interactive_view_formats:

        # Title and subtitle
        title = shn_get_crud_string(r.tablename, "title_display")
        output = dict(title=title)
        if r.component:
            subtitle = shn_get_crud_string(tablename, "title_display")
            output.update(subtitle=subtitle)

        # Resource header
        if rheader and r.id and (r.component or sticky):
            try:
                rh = rheader(r)
            except TypeError:
                rh = rheader
            output.update(rheader=rh)

        # Item
        if record_id:
            item = crud.read(table, record_id)
            subheadings = attr.get("subheadings", None)
            if subheadings:
                shn_insert_subheadings(item, tablename, subheadings)
        else:
            item = shn_get_crud_string(tablename, "msg_list_empty")

        # Put into view
        if representation == "html":
            shn_custom_view(r, "display.html")
            output.update(item=item)
        elif representation in ("popup", "iframe"):
            shn_custom_view(r, "popup.html")
            output.update(form=item, main=main, extra=extra, caller=caller)

        # Add edit and delete buttons as appropriate
        authorised = shn_has_permission("update", tablename, record_id)
        if authorised and href_edit and editable and r.method <> "update":
            edit = A(T("Edit"), _href=href_edit, _class="action-btn")
            output.update(edit=edit)
        authorised = shn_has_permission("delete", tablename)
        if authorised and href_delete and deletable:
            delete = A(T("Delete"), _href=href_delete, _id="delete-btn", _class="action-btn")
            output.update(delete=delete)

        # Add a list button if appropriate
        if not r.component or r.multiple:
            label_list_button = shn_get_crud_string(tablename, "label_list_button")
            if label_list_button:
                list_btn = A(label_list_button, _href=r.there(), _class="action-btn")
                output.update(list_btn=list_btn)

        return output

    elif representation == "plain":
        item = crud.read(table, record_id)
        response.view = "plain.html"
        return dict(item=item)

    elif representation == "csv":
        query = db[table].id == record_id
        return export_csv(tablename, query)

    elif representation == "pdf":
        query = db[table].id == record_id
        return export_pdf(table, query, list_fields)

    elif representation == "xls":
        query = db[table].id == record_id
        return export_xls(table, query, list_fields)

    else:
        session.error = BADFORMAT
        redirect(URL(r=request, f="index"))

#
# shn_linkto ------------------------------------------------------------------
#
def shn_linkto(r, sticky=None, authorised=None, update=None, native=False):

    """ Return a function that translates record IDs into links to open the
        respective record for read or update.

        @param r:       the current S3Request
        @param update:  render update URLs rather than read URLs if user is permitted

    """

    c = None
    f = None

    if r.component:
        if authorised is None:
            authorised = shn_has_permission("update", r.component.tablename)
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
            authorised = shn_has_permission("update", r.tablename)
        if authorised and update:
            linkto = response.s3.get("linkto_update", None)
        else:
            linkto = response.s3.get("linkto", None)

    def shn_list_linkto(record_id,
                        r=r,
                        c=c,
                        f=f,
                        linkto=linkto,
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
                    c = request.controller
                    f = request.function
                    args = [r.id, r.component_name, record_id]
                if update:
                    return str(URL(r=request, c=c, f=f, args=args + ["update"], vars=request.vars))
                else:
                    return str(URL(r=request, c=c, f=f, args=args, vars=request.vars))
            else:
                args = [record_id]
                if update:
                    return str(URL(r=request, c=c, f=f, args=args + ["update"]))
                else:
                    return str(URL(r=request, c=c, f=f, args=args))

    return shn_list_linkto


#
# shn_list --------------------------------------------------------------------
#
def shn_list(r, **attr):

    """ List records matching the request """

    prefix, name, table, tablename = r.target()
    vars = r.request.get_vars
    representation = r.representation.lower()

    # Get callbacks and list fields
    onvalidation = s3xrc.model.get_config(table, "onvalidation")
    onaccept = s3xrc.model.get_config(table, "onaccept")
    list_fields = s3xrc.model.get_config(table, "list_fields")

    # Get controller attributes
    rheader = attr.get("rheader", None)
    sticky = attr.get("sticky", rheader is not None)

    # Table-specific controller attributes
    _attr = r.component and r.component.attr or attr
    editable = _attr.get("editable", True)
    deletable = _attr.get("deletable", True)
    listadd = _attr.get("listadd", True)
    main = _attr.get("main", None)
    extra = _attr.get("extra", None)
    orderby = _attr.get("orderby", None)
    sortby = _attr.get("sortby", [[1,'asc']])
    linkto = _attr.get("linkto", None)
    create_next = _attr.get("create_next")

    # Provide the ability to get a subset of records
    start = vars.get("start", 0)
    limit = vars.get("limit", None)
    if limit is not None:
        try:
            start = int(start)
            limit = int(limit)
        except ValueError:
            limitby = None
        else:
            # disable Server-Side Pagination
            response.s3.pagination = False
            limitby = (start, start + limit)
    else:
        limitby = None

    # Get the initial query
    if r.component:
        resource = r.resource.components.get(r.component_name).resource
        href_add = URL(r=r.request, f=r.name, args=[r.id, name, "create"])
    else:
        resource = r.resource
        href_add = URL(r=r.request, f=r.name, args=["create"])
    query = resource.get_query()

    # SSPag filter handling
    if r.representation == "html":
        session.s3.filter = query
    elif r.representation.lower() == "aadata":
        if session.s3.filter is not None:
            query = session.s3.filter

    s3xrc.audit("list", prefix, name, representation=r.representation)

    # Which fields do we display?
    fields = None
    if list_fields:
        fkey = r.fkey or None
        fields = [f for f in list_fields if table[f].readable and f != fkey]
    if fields and len(fields) == 0:
        fields.append("id")
    if not fields:
        fields = [f for f in table.fields if table[f].readable]

    # Where to link the ID column?
    if not linkto:
        linkto = shn_linkto(r, sticky)
    # At this point, linkto is either a fixed url, or is a function that
    # takes an id and produces an url.

    if representation == "aadata":

        iDisplayStart = vars.get("iDisplayStart", 0)
        iDisplayLength = vars.get("iDisplayLength", None)

        if iDisplayLength is not None:
            try:
                start = int(iDisplayStart)
                limit = int(iDisplayLength)
            except ValueError:
                start = 0
                limit = None

        iSortingCols = vars.get("iSortingCols", None)
        if iSortingCols and orderby is None:
            orderby = shn_convert_orderby(table, request, fields=fields)

        if vars.sSearch:
            squery = shn_build_ssp_filter(table, request, fields=fields)
            if squery is not None:
                query = squery & query

        sEcho = int(vars.sEcho or 0)
        totalrows = resource.count()
        if limit:
            rows = db(query).select(table.ALL,
                                    limitby = (start, start + limit),
                                    orderby = orderby)
        else:
            rows = db(query).select(table.ALL,
                                    orderby = orderby)

        aaData = [[shn_field_represent_sspage(table[f], row, f, linkto=linkto)
                   for f in fields]
                   for row in rows]

        result = dict(sEcho = sEcho,
                      iTotalRecords = totalrows,
                      iTotalDisplayRecords = len(rows),
                      aaData = aaData)

        from gluon.serializers import json
        return json(result)

    elif representation in shn_interactive_view_formats:

        output = dict(main=main, extra=extra, sortby=sortby)

        if r.component:
            title = shn_get_crud_string(r.tablename, "title_display")
            if rheader:
                try:
                    rh = rheader(r)
                except TypeError:
                    rh = rheader
                output.update(rheader=rh)
        else:
            title = shn_get_crud_string(tablename, "title_list")

        subtitle = shn_get_crud_string(tablename, "subtitle_list")
        output.update(title=title, subtitle=subtitle)

        # Column labels: use custom or prettified label
        fields = [table[f] for f in fields]
        headers = dict(map(lambda f: (str(f), f.label), fields))

        # SSPag: only download 1 record initially & let
        # the view request what it wants via AJAX
        if response.s3.pagination and not limitby:
            limitby = (0, 1)

        # Get the items
        items = crud.select(table,
                            query=query,
                            fields=fields,
                            orderby=orderby,
                            limitby=limitby,
                            headers=headers,
                            linkto=linkto,
                            truncate=48, _id="list", _class="display")

        if not items:
            if db(table.id > 0).count():
                items = shn_get_crud_string(tablename, "msg_no_match")
            else:
                items = shn_get_crud_string(tablename, "msg_list_empty")
        output.update(items=items)

        authorised = shn_has_permission("create", tablename)
        if authorised and listadd:

            # @ToDo: This should share a subroutine with shn_create()
            if r.component:
                # Block join field
                _comment = table[r.fkey].comment
                table[r.fkey].comment = None
                table[r.fkey].default = r.record[r.pkey]
                # Fix for #447:
                if r.http == "POST":
                    table[r.fkey].writable = True
                    request.post_vars.update({r.fkey: str(r.record[r.pkey])})
                else:
                    table[r.fkey].writable = False

                # Neutralize callbacks
                crud.settings.create_onvalidation = None
                crud.settings.create_onaccept = None
                crud.settings.create_next = None
                r.next = create_next or r.there()
            else:
                r.next = crud.settings.create_next or r.there()
                crud.settings.create_next = None
                if not onvalidation:
                    onvalidation = crud.settings.create_onvalidation
                if not onaccept:
                    onaccept = crud.settings.create_onaccept

            if onaccept:
                _onaccept = lambda form: \
                            s3xrc.audit("create", prefix, name, form=form,
                                        representation=representation) and \
                            s3xrc.store_session(session, prefix, name, form.vars.id) and \
                            onaccept(form)
            else:
                _onaccept = lambda form: \
                            s3xrc.audit("create", prefix, name, form=form,
                                        representation=representation) and \
                            s3xrc.store_session(session, prefix, name, form.vars.id)

            message = shn_get_crud_string(tablename, "msg_record_created")

            # Display the Add form above List
            form = crud.create(table,
                               onvalidation=onvalidation,
                               onaccept=_onaccept,
                               message=message,
                               # Return to normal list view after creation
                               #next=r.there() # Better to use r.next
                              )

            # Cancel button?
            #form[0].append(TR(TD(), TD(INPUT(_type="reset", _value=T("Reset form")))))
            if response.s3.cancel:
                form[0][-1][1].append(INPUT(_type="button",
                                            _value=T("Cancel"),
                                            _onclick="window.location='%s';" %
                                                     response.s3.cancel))

            if "location_id" in db[tablename].fields and db[tablename].location_id.writable:
                # Allow the Location Selector to take effect
                _gis.location_id = True
                if response.s3.gis.map_selector:
                    # Include a map
                    _map = shn_map(r, method="create")
                    output.update(_map=_map)

            if r.component:
                table[r.fkey].comment = _comment

            addtitle = shn_get_crud_string(tablename, "subtitle_create")

            label_create_button = shn_get_crud_string(tablename, "label_create_button")
            showaddbtn = A(label_create_button,
                           _id = "show-add-btn",
                           _class="action-btn")
            output.update(showaddbtn=showaddbtn)

            shn_custom_view(r, "list_create.html")

            if deployment_settings.get_ui_navigate_away_confirm():
                form.append( SCRIPT ("EnableNavigateAwayConfirm();") )

            output.update(form=form, addtitle=addtitle)

        else:
            # List only
            add_btn = ""
            if authorised and editable:
                label_create_button = shn_get_crud_string(tablename, "label_create_button")
                if label_create_button:
                    add_btn = A(label_create_button, _href=href_add, _class="action-btn")


            shn_custom_view(r, "list.html")
            output.update(add_btn=add_btn)

        return output

    elif representation == "plain":
        items = crud.select(table, query, truncate=24)
        response.view = "plain.html"
        return dict(item=items)

    elif representation == "csv":
        return export_csv(tablename, query)

    elif representation == "pdf":
        return export_pdf(table, query, list_fields)

    elif representation == "xls":
        return export_xls(table, query, list_fields)

    else:
        session.error = BADFORMAT
        redirect(URL(r=request, f="index"))

#
# shn_create ------------------------------------------------------------------
#
def shn_create(r, **attr):

    """ Create new records """

    prefix, name, table, tablename = r.target()
    representation = r.representation.lower()

    # Callbacks
    onvalidation = s3xrc.model.get_config(table, "onvalidation")
    onaccept = s3xrc.model.get_config(table, "onaccept")

    # Controller attributes
    rheader = attr.get("rheader", None)
    sticky = attr.get("sticky", rheader is not None)

    # Table-specific controller attributes
    _attr = r.component and r.component.attr or attr
    main = _attr.get("main", None)
    extra = _attr.get("extra", None)
    create_next = _attr.get("create_next")

    if representation in shn_interactive_view_formats:

        # Copy from a previous record?
        from_record = r.request.get_vars.get("from_record", None)
        from_fields = r.request.get_vars.get("from_fields", None)
        original = None
        if from_record:
            del r.request.get_vars["from_record"] # forget it
            if from_record.find(".") != -1:
                source_name, from_record = from_record.split(".", 1)
                source = db.get(source_name, None)
            else:
                source = table
            if from_fields:
                del r.request.get_vars["from_fields"] # forget it
                from_fields = from_fields.split(",")
            else:
                from_fields = [f for f in table.fields if f in source.fields and f != "id"]
            if source and from_record:
                copy_fields = [source[f] for f in from_fields if
                                    f in source.fields and
                                    f in table.fields and
                                    table[f].type == source[f].type and
                                    table[f].readable and table[f].writable]
                if shn_has_permission("read", source._tablename, from_record):
                    original = db(source.id == from_record).select(limitby=(0, 1), *copy_fields).first()
                if original:
                    missing_fields = Storage()
                    for f in table.fields:
                        if f not in original and \
                           table[f].readable and table[f].writable:
                            missing_fields[f] = table[f].default
                    original.update(missing_fields)

        # Default components
        output = dict(module=prefix, resource=name, main=main, extra=extra)

        if "location_id" in db[tablename].fields and db[tablename].location_id.writable:
            # Allow the Location Selector to take effect
            _gis.location_id = True
            if response.s3.gis.map_selector:
                # Include a map
                _map = shn_map(r, method="create")
                output.update(_map=_map)

        # Title, subtitle and resource header
        if r.component:
            title = shn_get_crud_string(r.tablename, "title_display")
            subtitle = shn_get_crud_string(tablename, "subtitle_create")
            output.update(subtitle=subtitle)
            if rheader and r.id:
                try:
                    rh = rheader(r)
                except TypeError:
                    rh = rheader
                output.update(rheader=rh)
        else:
            title = shn_get_crud_string(tablename, "title_create")
        output.update(title=title)

        if r.component:
            # Block join field
            _comment = table[r.fkey].comment
            table[r.fkey].comment = None
            table[r.fkey].default = r.record[r.pkey]
            if r.http == "POST":
                table[r.fkey].writable = True
                request.post_vars.update({r.fkey: str(r.record[r.pkey])})
            else:
                table[r.fkey].writable = False

            # Neutralize callbacks
            crud.settings.create_onvalidation = None
            crud.settings.create_onaccept = None
            crud.settings.create_next = None
            r.next = create_next or r.there()
        else:
            r.next = crud.settings.create_next or r.there()
            crud.settings.create_next = None
            if not onvalidation:
                onvalidation = crud.settings.create_onvalidation
            if not onaccept:
                onaccept = crud.settings.create_onaccept

        if onaccept:
            _onaccept = lambda form: \
                        s3xrc.audit("create", prefix, name, form=form,
                                    representation=representation) and \
                        s3xrc.store_session(session,
                                            prefix, name, form.vars.id) and \
                        onaccept(form)

        else:
            _onaccept = lambda form: \
                        s3xrc.audit("create", prefix, name, form=form,
                                    representation=representation) and \
                        s3xrc.store_session(session,
                                            prefix, name, form.vars.id)

        # Get the form
        message = shn_get_crud_string(tablename, "msg_record_created")
        if "id" in r.request.post_vars:
            original = r.request.post_vars.id
            r.request.post_vars.id = str(original)
            formname = "%s/%s" % (tablename, original)
            old_form = "%s/None" % (tablename)
            session["_formkey[%s]" % formname] = session.get("_formkey[%s]" % old_form)
            if "deleted" in table: # undelete
                table.deleted.writable = True
                r.request.post_vars.update(deleted=False)
            r.request.post_vars.update(_formname = formname, id=r.request.post_vars.id)
            r.request.vars.update(**r.request.post_vars)
        elif original:
            original.id = None
        else:
            original = None

        form = crud.update(table,
                           original,
                           message=message,
                           next=crud.settings.create_next,
                           deletable=False,
                           onvalidation=onvalidation,
                           onaccept=_onaccept)

        subheadings = attr.get("subheadings", None)
        if subheadings:
            shn_insert_subheadings(form, tablename, subheadings)

        # Cancel button?
        #form[0].append(TR(TD(), TD(INPUT(_type="reset", _value=T("Reset form")))))
        if response.s3.cancel:
            form[0][-1][1].append(INPUT(_type="button",
                                        _value=T("Cancel"),
                                        _onclick="window.location='%s';" %
                                                 response.s3.cancel))

        if deployment_settings.get_ui_navigate_away_confirm():
            form.append( SCRIPT ("EnableNavigateAwayConfirm();") )

        # Put the form into output
        output.update(form=form)

        # Restore comment
        if r.component:
            table[r.fkey].comment = _comment

        # Add a list button if appropriate
        if not r.component or r.multiple:
            label_list_button = shn_get_crud_string(tablename, "label_list_button")
            if label_list_button:
                list_btn = A(label_list_button, _href=r.there(), _class="action-btn")
                output.update(list_btn=list_btn)

        # Custom view
        if representation in ("popup", "iframe"):
            shn_custom_view(r, "popup.html")
            output.update(caller=r.request.vars.caller)
            r.next = None
        else:
            shn_custom_view(r, "create.html")

        return output

    elif representation == "plain":
        if onaccept:
            _onaccept = lambda form: \
                        s3xrc.audit("create", prefix, name, form=form,
                                    representation=representation) and \
                        onaccept(form)
        else:
            _onaccept = lambda form: \
                        s3xrc.audit("create", prefix, name, form=form,
                                    representation=representation)

        form = crud.create(table,
                           onvalidation=onvalidation, onaccept=_onaccept)

        if deployment_settings.get_ui_navigate_away_confirm():
            form.append( SCRIPT ("EnableNavigateAwayConfirm();") )

        response.view = "plain.html"
        return dict(item=form)

    elif representation == "url":
        return import_url(r)

    elif representation == "csv":
        # Read in POST
        import csv
        csv.field_size_limit(1000000000)
        #infile = open(request.vars.filename, "rb")
        infile = r.request.vars.filename.file
        try:
            import_csv(infile, table)
            session.flash = T("Data uploaded")
        except:
            session.error = T("Unable to parse CSV file!")
        redirect(r.there())

    else:
        session.error = BADFORMAT
        redirect(URL(r=request, f="index"))

#
# shn_update ------------------------------------------------------------------
#
def shn_update(r, **attr):

    """ Update an existing record """

    prefix, name, table, tablename = r.target()
    representation = r.representation.lower()

    # Get callbacks
    onvalidation = s3xrc.model.get_config(table, "onvalidation")
    onaccept = s3xrc.model.get_config(table, "onaccept")

    # Get controller attributes
    rheader = attr.get("rheader", None)
    sticky = attr.get("sticky", rheader is not None)

    # Table-specific controller attributes
    _attr = r.component and r.component.attr or attr
    editable = _attr.get("editable", True)
    deletable = _attr.get("deletable", True)
    update_next = _attr.get("update_next", None)

    # Find the correct record ID
    if r.component:
        resource = r.resource.components.get(r.component_name).resource
        resource.load(start=0, limit=1)
        if not len(resource):
            if not r.multiple:
                r.component_id = None
                redirect(r.other(method="create", representation=representation))
            else:
                session.error = BADRECORD
                redirect(r.there())
        else:
            record_id = resource.records().first().id
    else:
        record_id = r.id

    # Redirect to read view if not editable
    if not editable and representation == "html":
        return shn_read(r, **attr)

    # Check authorisation
    authorised = shn_has_permission("update", tablename, record_id)
    if not authorised:
        r.unauthorised()

    # Audit read
    s3xrc.audit("read", prefix, name,
                record=record_id, representation=representation)

    if r.representation in shn_interactive_view_formats:

        # Custom view
        if r.representation == "html":
            shn_custom_view(r, "update.html")
        elif r.representation in ("popup", "iframe"):
            shn_custom_view(r, "popup.html")

        # Title and subtitle
        if r.component:
            title = shn_get_crud_string(r.tablename, "title_display")
            subtitle = shn_get_crud_string(tablename, "title_update")
            output = dict(title=title, subtitle=subtitle)
        else:
            title = shn_get_crud_string(tablename, "title_update")
            output = dict(title=title)

        # Resource header
        if rheader and r.id and (r.component or sticky):
            try:
                rh = rheader(r)
            except TypeError:
                rh = rheader
            output.update(rheader=rh)

        # Add delete button
        if deletable:
            href_delete = r.other(method="delete", representation=representation)
            label_del_button = shn_get_crud_string(tablename, "label_delete_button")
            del_btn = A(label_del_button,
                        _href=href_delete,
                        _id="delete-btn",
                        _class="action-btn")
            output.update(del_btn=del_btn)

        if r.component:
            _comment = table[r.fkey].comment
            table[r.fkey].comment = None
            table[r.fkey].default = r.record[r.pkey]
            # Fix for #447:
            if r.http == "POST":
                table[r.fkey].writable = True
                request.post_vars.update({r.fkey: str(r.record[r.pkey])})
            else:
                table[r.fkey].writable = False
            crud.settings.update_onvalidation = None
            crud.settings.update_onaccept = None
            if not representation in ("popup", "iframe"):
                crud.settings.update_next = update_next or r.there()
        else:
            if not representation in ("popup", "iframe") and \
               not crud.settings.update_next:
                crud.settings.update_next = update_next or r.here()
            if not onvalidation:
                onvalidation = crud.settings.update_onvalidation
            if not onaccept:
                onaccept = crud.settings.update_onaccept

        if onaccept:
            _onaccept = lambda form: \
                        s3xrc.audit("update", prefix, name, form=form,
                                    representation=representation) and \
                        s3xrc.store_session(session, prefix, name, form.vars.id) and \
                        onaccept(form)
        else:
            _onaccept = lambda form: \
                        s3xrc.audit("update", prefix, name, form=form,
                                    representation=representation) and \
                        s3xrc.store_session(session, prefix, name, form.vars.id)

        crud.settings.update_deletable = deletable
        message = shn_get_crud_string(tablename, "msg_record_modified")

        form = crud.update(table, record_id,
                            message=message,
                            onvalidation=onvalidation,
                            onaccept=_onaccept,
                            deletable=False) # TODO: add extra delete button to form

        subheadings = attr.get("subheadings", None)
        if subheadings:
            shn_insert_subheadings(form, tablename, subheadings)

        # Cancel button?
        #form[0].append(TR(TD(), TD(INPUT(_type="reset", _value=T("Reset form")))))
        if response.s3.cancel:
            form[0][-1][1].append(INPUT(_type="button",
                                        _value=T("Cancel"),
                                        _onclick="window.location='%s';" %
                                                 response.s3.cancel))

        if deployment_settings.get_ui_navigate_away_confirm():
            form.append( SCRIPT ("EnableNavigateAwayConfirm();") )

        output.update(form=form)

        # Restore comment
        if r.component:
            table[r.fkey].comment = _comment

        # Add a list button if appropriate
        if not r.component or r.multiple:
            label_list_button = shn_get_crud_string(tablename, "label_list_button")
            if label_list_button:
                list_btn = A(label_list_button, _href=r.there(), _class="action-btn")
                output.update(list_btn=list_btn)

        if "location_id" in db[tablename].fields and db[tablename].location_id.writable:
            # Allow the Location Selector to take effect
            _gis.location_id = True
            if response.s3.gis.map_selector:
                # Include a map
                _map = shn_map(r, method="update", tablename=tablename, prefix=prefix, name=name)
                oldlocation = _map["oldlocation"]
                _map = _map["_map"]
                output.update(_map=_map, oldlocation=oldlocation)

        return output

    elif representation == "plain":
        if onaccept:
            _onaccept = lambda form: \
                        s3xrc.audit("update", prefix, name, form=form,
                                    representation=representation) and \
                        onaccept(form)
        else:
            _onaccept = lambda form: \
                        s3xrc.audit("update", prefix, name, form=form,
                                    representation=representation)

        form = crud.update(table, record_id,
                           onvalidation=onvalidation,
                           onaccept=_onaccept,
                           deletable=False)

        response.view = "plain.html"

        if deployment_settings.get_ui_navigate_away_confirm():
            form.append( SCRIPT ("EnableNavigateAwayConfirm();") )

        return dict(item=form)

    elif r.representation == "url":
        return import_url(r)

    else:
        session.error = BADFORMAT
        redirect(URL(r=request, f="index"))


#
# shn_delete ------------------------------------------------------------------
#
def shn_delete(r, **attr):

    """ Delete record(s) """

    prefix, name, table, tablename = r.target()
    representation = r.representation.lower()

    # Get callbacks
    onvalidation = s3xrc.model.get_config(table, "delete_onvalidation")
    onaccept = s3xrc.model.get_config(table, "delete_onaccept")

    # Table-specific controller attributes
    _attr = r.component and r.component.attr or attr
    deletable = _attr.get("deletable", True)

    # custom delete_next?
    delete_next = _attr.get("delete_next", None)
    if delete_next:
        r.next = delete_next

    if r.component:
        query = ((table[r.fkey] == r.table[r.pkey]) & \
                 (table[r.fkey] == r.record[r.pkey]))
        if r.component_id:
            query = (table.id == r.component_id) & query
    else:
        query = (table.id == r.id)

    if "deleted" in table:
        query = (table.deleted == False) & query

    # Get target records
    rows = db(query).select(table.ALL)

    # Nothing to do? Return here!
    if not rows:
        session.confirmation = T("No records to delete")
        return {}

    message = shn_get_crud_string(tablename, "msg_record_deleted")

    # Delete all accessible records
    numrows = 0
    for row in rows:
        if shn_has_permission("delete", tablename, row.id):
            numrows += 1
            if s3xrc.get_session(session, prefix=prefix, name=name) == row.id:
                s3xrc.clear_session(session, prefix=prefix, name=name)
            try:
                s3xrc.audit("delete", prefix, name, record=row.id, representation=representation)
                # Reset session vars if necessary
                if "deleted" in db[table] and deployment_settings.get_security_archive_not_delete():
                    if onvalidation:
                        onvalidation(row)
                    deleted = dict(deleted=True)
                    db(db[table].id == row.id).update(**deleted)
                    if onaccept:
                        onaccept(row)
                else:
                    # Do not CRUD.delete! (it never returns, but redirects)
                    if onvalidation:
                        onvalidation(row)
                    del db[table][row.id]
                    if onaccept:
                        onaccept(row)

            # Would prefer to import sqlite3 & catch specific error, but
            # this isn't generalisable to other DBs...we need a DB config to pull in.
            #except sqlite3.IntegrityError:
            except:
                session.error = T("Cannot delete whilst there are linked records. Please delete linked records first.")
        else:
            continue

    if not session.error:
        if numrows > 1:
            response.confirmation = "%s %s" % ( numrows, T("records deleted"))
        else:
            response.confirmation = message

    item = s3xrc.xml.json_message()
    response.view = "plain.html"
    output = dict(item=item)

    return output

#
# shn_copy ------------------------------------------------------------------
#
def shn_copy(r, **attr):
    redirect(URL(r=request, args="create", vars={"from_record":r.id}))

#
# shn_map ------------------------------------------------------------------
#
def shn_map(r, method="create", tablename=None, prefix=None, name=None):
    """ Prepare a Map to include in forms"""

    if method == "create":
        _map = gis.show_map(add_feature = True,
                            add_feature_active = True,
                            toolbar = True,
                            collapsed = True,
                            window = True,
                            window_hide = True)
        return _map

    elif method == "update" and tablename and prefix and name:
        config = gis.get_config()
        zoom = config.zoom
        _locations = db.gis_location
        fields = [_locations.id, _locations.uuid, _locations.name, _locations.lat, _locations.lon, _locations.level, _locations.parent, _locations.addr_street]
        location = db((db[tablename].id == r.id) & (_locations.id == db[tablename].location_id)).select(limitby=(0, 1), *fields).first()
        if location and location.lat is not None and location.lon is not None:
            lat = location.lat
            lon = location.lon
        else:
            lat = config.lat
            lon = config.lon
        layername = T("Location")
        popup_label = ""
        filter = Storage(tablename = tablename,
                         id = r.id
                        )
        layer = gis.get_feature_layer(prefix, name, layername, popup_label, filter=filter)
        feature_queries = [layer]
        _map = gis.show_map(lat = lat,
                            lon = lon,
                            # Same as a single zoom on a cluster
                            zoom = zoom + 2,
                            feature_queries = feature_queries,
                            add_feature = True,
                            add_feature_active = False,
                            toolbar = True,
                            collapsed = True,
                            window = True,
                            window_hide = True)
        if location and location.id:
            _location = Storage(id = location.id,
                                uuid = location.uuid,
                                name = location.name,
                                lat = location.lat,
                                lon = location.lon,
                                level = location.level,
                                parent = location.parent,
                                addr_street = location.addr_street
                                )
        else:
            _location = None
        return dict(_map=_map, oldlocation=_location)

    return dict(None, None)

#
# shn_search ------------------------------------------------------------------
#
def shn_search(r, **attr):

    """
        Search function
        Mostly used with the JSON representation
    """

    deletable = attr.get("deletable", True)
    main = attr.get("main", None)
    extra = attr.get("extra", None)

    request = r.request

    # Filter Search list to just those records which user can read
    query = shn_accessible_query("read", r.table)

    # Filter search to items which aren't deleted
    if "deleted" in r.table:
        query = (r.table.deleted == False) & query

    # Respect response.s3.filter
    if response.s3.filter:
        query = response.s3.filter & query

    if r.representation in shn_interactive_view_formats:

        shn_represent(r.table, r.prefix, r.name, deletable, main, extra)
        search = t2.search(r.table, query=query)
        #search = crud.search(r.table, query=query)[0]

        # Check for presence of Custom View
        shn_custom_view(r, "search.html")

        # CRUD Strings
        title = s3.crud_strings.title_search

        output = dict(search=search, title=title)

    elif r.representation == "json":

        _vars = request.vars
        _table = r.table

        # JQuery Autocomplete uses "q" instead of "value"
        value = _vars.value or _vars.q or None

        if _vars.field and _vars.filter and value:
            field = str.lower(_vars.field)
            _field = _table[field]

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
                        query = query & ((_field.like("%" + value1 + "%")) & \
                                        (_table[field2].like("%" + value2 + "%")) | \
                                        (_table[field3].like("%" + value2 + "%")))
                    else:
                        query = query & ((_field.like("%" + value + "%")) | \
                                        (_table[field2].like("%" + value + "%")) | \
                                        (_table[field3].like("%" + value + "%")))

                elif exclude_field and exclude_value:
                    # gis_location hierarchical search
                    # Filter out poor-quality data, such as from Ushahidi
                    query = query & (_field.like("%" + value + "%")) & \
                                    (_table[exclude_field] != exclude_value)

                elif parent:
                    # gis_location hierarchical search
                    # NB Currently not used - we allow people to search freely across all the hierarchy
                    # SQL Filter is immediate children only so need slow lookup
                    #query = query & (_table.parent == parent) & \
                    #                (_field.like("%" + value + "%"))
                    children = gis.get_children(parent)
                    children = children.find(lambda row: value in str.lower(row.name))
                    item = children.json()
                    query = None

                else:
                    # Normal single-field
                    query = query & (_field.like("%" + value + "%"))

                if query:
                    if limit:
                        item = db(query).select(limitby=(0, limit)).json()
                    else:
                        item = db(query).select().json()

            elif filter == "=":
                query = query & (_field == value)
                if parent:
                    # e.g. gis_location hierarchical search
                    query = query & (_table.parent == parent)

                if _table == db.gis_location:
                    # Don't return unnecessary fields (WKT is large!)
                    item = db(query).select(_table.id, _table.uuid, _table.parent, _table.name, _table.level, _table.lat, _table.lon, _table.addr_street).json()
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
            if _table == db.gis_location:
                # Don't return unnecessary fields (WKT is large!)
                item = db(query).select(_table.id, _table.name, _table.level).json()
            else:
                item = db(query).select().json()

        response.view = "xml.html"
        output = dict(item=item)

    else:
        raise HTTP(501, body=BADFORMAT)

    return output


def shn_barchart (r, **attr):
    """
        Provide simple barcharts for resource attributes
        SVG representation uses the SaVaGe library
        Need to request a specific value to graph in request.vars
    """

    import gluon.contrib.simplejson as json

    # Get all the variables and format them if needed
    valKey = r.request.vars.get("value")

    nameKey = r.request.vars.get("name")
    if not nameKey and r.table.get("name"):
        # Try defaulting to the most-commonly used:
        nameKey = "name"

    # The parameter value is required; it must be provided
    # The parameter name is optional; it is useful, but we don't need it
    # Here we check to make sure we can find value in the table,
    # and name (if it was provided)
    if not r.table.get(valKey):
        raise HTTP (400, s3xrc.xml.json_message(success=False, status_code="400", message="Need a Value for the Y axis"))
    elif nameKey and not r.table.get(nameKey):
        raise HTTP (400, s3xrc.xml.json_message(success=False, status_code="400", message=nameKey + " attribute not found in this resource."))

    start = request.vars.get("start")
    if start:
        start = int(start)

    limit = r.request.vars.get("limit")
    if limit:
        limit = int(limit)

    settings = r.request.vars.get("settings")
    if settings:
        settings = json.loads(settings)
    else:
        settings = {}

    if r.representation.lower() == "svg":
        r.response.headers["Content-Type"] = "image/svg+xml"

        graph = local_import("savage.graph")
        bar = graph.BarGraph(settings=settings)

        title = deployment_settings.modules.get(module).name_nice
        bar.setTitle(title)

        if nameKey:
            xlabel = r.table.get(nameKey).label
            if xlabel:
                bar.setXLabel(str(xlabel))
            else:
                bar.setXLabel(nameKey)

        ylabel = r.table.get(valKey).label
        if ylabel:
            bar.setYLabel(str(ylabel))
        else:
            bar.setYLabel(valKey)

        try:
            records = r.resource.load(start, limit)
            for entry in r.resource:
                val = entry[valKey]

                # Can't graph None type
                if not val is None:
                    if nameKey:
                        name = entry[nameKey]
                    else:
                        name = None
                    bar.addBar(name, val)
            return bar.save()
        # If the field that was provided was not numeric, we have problems
        except ValueError:
            raise HTTP(400, "Bad Request")
    else:
        raise HTTP(501, body=BADFORMAT)

# *****************************************************************************
# Main controller function

#
# shn_rest_controller ---------------------------------------------------------
#
def shn_rest_controller(module, resource, **attr):

    """
        RESTlike controller function
        ============================

        Provides CRUD operations for the given module/resource.

        Supported Representations:
        ==========================

        Representation is recognized from the extension of the target resource.
        You can still pass a "?format=" to override this.

            - B{html}: is the default (including full layout)
            - B{plain}: is HTML with no layout
                - can be inserted into DIVs via AJAX calls
                - can be useful for clients on low-bandwidth or small screen sizes
                - used for the Map popups
            - B{ext}: is Ext layouts (experimental)
            - B{json}: JSON export/import using XSLT
            - B{xml}: XML export/import using XSLT
            - B{csv}: useful for synchronization/database migration
                - List/Display/Create for now
            - B{pdf}: list/read only
            - B{rss}: list only
            - B{svg}: barchart method only
            - B{xls}: list/read only
            - B{ajax}: designed to be run asynchronously to refresh page elements
            - B{url}: designed to be accessed via JavaScript
                - responses in JSON format
                - create/update/delete done via simple GET vars (no form displayed)
            - B{popup}: designed to be used inside colorbox popups
            - B{iframe}: designed to be used inside iframes
            - B{aaData}: used by dataTables for server-side pagination

        Request options:
        ================

            - B{response.s3.filter}: contains custom query to filter list views (primary resources)
            - B{response.s3.jfilter}: contains custom query to filter list views (joined resources)
            - B{response.s3.cancel}: adds a cancel button to forms & provides a location to direct to upon pressing
            - B{response.s3.pagination}: enables server-side pagination (detected by view which then calls REST via AJAX)

        Description:
        ============

        @param deletable: provide visible options for deletion (optional, default=True)
        @param editable: provide visible options for editing (optional, default=True)
        @param listadd: provide an add form in the list view (optional, default=True)

        @param main:
            the field used for the title in RSS output (optional, default="name")
        @param extra:
            the field used for the description in RSS output & in Search AutoComplete
            (optional, default=None)

        @param orderby:
            the sort order for server-side paginated list views (optional, default=None), e.g.::
                db.mytable.myfield1|db.mytable.myfield2

        @param sortby:
            the sort order for client-side paginated list views (optional, default=None), e.g.::
                [[1, "asc"], [2, "desc"]]

            see: U{http://datatables.net/examples/basic_init/table_sorting.html}

        @param rheader: function to produce a page header for the primary resource
        @type rheader:
            function(resource, record_id, representation, next=None, same=None)

        @author: Fran Boon
        @author: nursix

        @todo:
            - Alternate Representations
            - CSV update
            - SMS, LDIF

    """

    s3xrc.set_handler("list", shn_list)
    s3xrc.set_handler("read", shn_read)
    s3xrc.set_handler("create", shn_create)
    s3xrc.set_handler("update", shn_update)
    s3xrc.set_handler("delete", shn_delete)
    s3xrc.set_handler("search", shn_search)
    s3xrc.set_handler("copy", shn_copy)
    s3xrc.set_handler("barchart", shn_barchart)

    res, r = s3xrc.parse_request(module, resource, session, request, response)
    output = res.execute_request(r, **attr)

    # Add default action buttons in list views:
    if isinstance(output, dict) and not r.method:
        c = r.component
        if response.s3.actions is None:
            native = False
            if c:
                _attr = c.attr
                authorised = shn_has_permission("update", c.tablename)
                if s3xrc.model.has_components(c.prefix, c.name):
                    # Use the component's native controller for CRU(D), need
                    # to make sure you have one, or override by native=False
                    native = attr.get("native", True)
            else:
                _attr = attr
                authorised = shn_has_permission("update", r.tablename)

            listadd = _attr.get("listadd", True)
            editable = _attr.get("editable", True)
            deletable = _attr.get("deletable", True)
            copyable = _attr.get("copyable", False)

            # URL to open the resource
            open_url = shn_linkto(r,
                                  authorised=authorised,
                                  update=editable,
                                  native=native)("[id]")

            # Add action buttons for Open/Delete/Copy as appropriate
            shn_action_buttons(r,
                               deletable=deletable,
                               copyable=copyable,
                               read_url=open_url,
                               update_url=open_url)

            # Override add button for native controller use (+automatic linking)
            if native and not listadd:
                if shn_has_permission("create", c.tablename):
                    label = shn_get_crud_string(c.tablename,
                                                "label_create_button")
                    hook = r.resource.components[c.name]
                    fkey = "%s.%s" % (c.name, hook.fkey)
                    vars = request.vars.copy()
                    vars.update({fkey: r.id})
                    url = str(URL(r=request, c=c.prefix, f=c.name,
                                  args=["create"], vars=vars))
                    add_btn = A(label, _href=url, _class="action-btn")
                    output.update(add_btn=add_btn)

    return output

# END
# *****************************************************************************
