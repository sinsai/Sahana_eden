# -*- coding: utf-8 -*-

#
# RESTlike CRUD controller
#
# created by Fran Boon
# extended by nursix
# http://trac.sahanapy.org/wiki/JoinedResourceController
#

exec('from applications.%s.modules.s3xml import S3XML' % request.application)

# *****************************************************************************
# Joint Resource Layer
jrlayer = JRLayer(db)

# *****************************************************************************
# Constants to ensure consistency

# XSL Settings
XSL_FILE_EXTENSION = 'xslt'
XSL_IMPORT_TEMPLATES = 'static/xsl/import'
XSL_EXPORT_TEMPLATES = 'static/xsl/export'

# Error messages
UNAUTHORISED = T('Not authorised!')
BADFORMAT = T('Unsupported data format!')
BADMETHOD = T('Unsupported method!')
BADRECORD = T('No such record!')
INVALIDREQUEST = T('Invalid request!')

# How many rows to show per page in list outputs
ROWSPERPAGE = 20

shn_xml_import_formats = ["xml", "pfif"] # TODO: replace by auto-detection
shn_xml_export_formats = ["xml", "pfif"] # TODO: replace by auto-detection

# *****************************************************************************
# Data conversion

#
# export_csv ------------------------------------------------------------------
#
def export_csv(resource, query, record=None):
    "Export record(s) as CSV"
    import gluon.contenttype
    response.headers['Content-Type'] = gluon.contenttype.contenttype('.csv')
    if record:
        filename = "%s_%s_%d.csv" % (request.env.server_name, resource, record)
    else:
        # List
        filename = "%s_%s_list.csv" % (request.env.server_name, resource)
    response.headers['Content-disposition'] = "attachment; filename=%s" % filename
    return str(db(query).select())

#
# export_json -----------------------------------------------------------------
#
def export_json(table, query):
    "Export record(s) as JSON"
    response.headers['Content-Type'] = 'text/x-json'
    return db(query).select(table.ALL).json()

#
# export_pdf ------------------------------------------------------------------
#
def export_pdf(table, query):
    "Export record(s) as Adobe PDF"
    try:
        from reportlab.lib.units import cm
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    except ImportError:
        session.error = T('ReportLab module not available within the running Python - this needs installing for PDF output!')
        redirect(URL(r=request))
    try:
        from geraldo import Report, ReportBand, Label, ObjectValue, SystemField, landscape, BAND_WIDTH
        from geraldo.generators import PDFGenerator
    except ImportError:
        session.error = T('Geraldo module not available within the running Python - this needs installing for PDF output!')
        redirect(URL(r=request))

    objects_list = db(query).select(table.ALL)
    if not objects_list:
        session.warning = T('No data in this table - cannot create PDF!')
        redirect(URL(r=request))

    import StringIO
    output = StringIO.StringIO()

    fields = [table[f] for f in table.fields if table[f].readable]
    _elements = [SystemField(expression='%(report_title)s', top=0.1*cm,
                    left=0, width=BAND_WIDTH, style={'fontName': 'Helvetica-Bold',
                    'fontSize': 14, 'alignment': TA_CENTER})]
    detailElements = []
    COLWIDTH = 2.5
    LEFTMARGIN = 0.2
    for field in fields:
        _elements.append(Label(text=str(field.label)[:16], top=0.8*cm, left=LEFTMARGIN*cm))
        tab, col = str(field).split('.')
        #db[table][col].represent = 'foo'
        detailElements.append(ObjectValue(
            attribute_name=col,
            left=LEFTMARGIN*cm, width=COLWIDTH*cm,
            get_value=lambda instance: str(instance).decode('utf-8')))
        LEFTMARGIN += COLWIDTH

    mod, res = str(table).split('_', 1)
    mod_nice = db(db.s3_module.name==mod).select()[0].name_nice
    _title = mod_nice + ': ' + res.capitalize()

    class MyReport(Report):
        title = _title
        page_size = landscape(A4)
        class band_page_header(ReportBand):
            height = 1.3*cm
            auto_expand_height = True
            elements = _elements
            borders = {'bottom': True}
        class band_page_footer(ReportBand):
            height = 0.5*cm
            elements = [
                Label(text='%s' % request.utcnow.date(), top=0.1*cm, left=0),
                SystemField(expression='Page # %(page_number)d of %(page_count)d', top=0.1*cm,
                    width=BAND_WIDTH, style={'alignment': TA_RIGHT}),
            ]
            borders = {'top': True}
        class band_detail(ReportBand):
            height = 0.5*cm
            auto_expand_height = True
            elements = tuple(detailElements)
    report = MyReport(queryset=objects_list)
    report.generate_by(PDFGenerator, filename=output)

    output.seek(0)
    import gluon.contenttype
    response.headers['Content-Type'] = gluon.contenttype.contenttype('.pdf')
    filename = "%s_%s.pdf" % (request.env.server_name, str(table))
    response.headers['Content-disposition'] = "attachment; filename=\"%s\"" % filename
    return output.read()

#
# export_rss ------------------------------------------------------------------
#
def export_rss(module, resource, query, rss=None, linkto=None):
    """
        Export record(s) as RSS feed
    """

    # This can not work when proxied through Apache (since it's always a local request):
    #if request.env.remote_addr == '127.0.0.1':
        #server = 'http://127.0.0.1:' + request.env.server_port
    #else:
        #server = 'http://' + request.env.server_name + ':' + request.env.server_port

    server = S3_PUBLIC_URL

    tablename = "%s_%s" % (module, resource)
    try:
        title_list = s3.crud_strings[tablename].subtitle_list
    except:
        title_list =  s3.crud_strings.subtitle_list

    if not linkto:
        link = '/%s/%s/%s' % (request.application, module, resource)
    else:
        link = linkto

    entries = []
    rows = db(query).select()
    if rows:
        for row in rows:
            if rss and 'title' in rss:
                try:
                    title = rss.get('title')(row)
                except TypeError:
                    title = rss.get('title') % row
            else:
                title = row['id']

            if rss and 'description' in rss:
                try:
                    description = rss.get('description')(row)
                except TypeError:
                    description = rss.get('description') % row
            else:
                description = ''

            entries.append(dict(
                title=str(title).decode('utf-8'),
                link=server + link + '/%d' % row.id,
                description=str(description).decode('utf-8'),
                created_on=row.created_on))

    import gluon.contrib.rss2 as rss2

    items = [rss2.RSSItem(
        title = entry['title'],
        link = entry['link'],
        description = entry['description'],
        pubDate = entry['created_on']) for entry in entries]

    rss = rss2.RSS2(
        title = str(title_list).decode('utf-8'),
        link = server + link,
        description = '',
        lastBuildDate = request.utcnow,
        items = items)

    response.headers['Content-Type'] = 'application/rss+xml'
    return rss2.dumps(rss)

#
# export_xls ------------------------------------------------------------------
#
def export_xls(table, query):
    "Export record(s) as XLS"
    try:
        import xlwt
    except ImportError:
        session.error = T('xlwt module not available within the running Python - this needs installing for XLS output!')
        redirect(URL(r=request))

    import StringIO
    output = StringIO.StringIO()

    items = db(query).select(table.ALL)

    book = xlwt.Workbook()
    sheet1 = book.add_sheet(str(table))
    # Header row
    row0 = sheet1.row(0)
    cell = 0
    fields = [table[f] for f in table.fields if table[f].readable]
    for field in fields:
        row0.write(cell, str(field.label), xlwt.easyxf('font: bold True;'))
        cell += 1
    row = 1
    for item in items:
        # Item details
        rowx = sheet1.row(row)
        row += 1
        cell1 = 0
        for field in fields:
            tab, col = str(field).split('.')
            rowx.write(cell1, item[col])
            cell1 += 1
    book.save(output)
    output.seek(0)
    import gluon.contenttype
    response.headers['Content-Type'] = gluon.contenttype.contenttype('.xls')
    filename = "%s_%s.xls" % (request.env.server_name, str(table))
    response.headers['Content-disposition'] = "attachment; filename=\"%s\"" % filename
    return output.read()

#
# export_xml ------------------------------------------------------------------
#
def export_xml(jr):
    """
        Export data as XML
    """
    s3xml = S3XML(db)

    if jr.jresource:
        joins = [dict(prefix=jr.jmodule, name=jr.jresource, pkey=jr.pkey, fkey=jr.fkey, id=jr.jrecord_id)]
    else:
        joins = jrlayer.get_joins(jr.module, jr.resource)

    response.headers['Content-Type'] = 'text/xml'
    tree = s3xml.get(jr.module, jr.resource, jr.record_id, joins=joins, permit=shn_has_permission)

    # Audit
    for e in s3xml.exports:
        shn_audit_read('read', e["prefix"], e["name"], e["id"], representation=jr.representation)

    # XSL Transformation
    template_name = "%s.%s" % (jr.representation, XSL_FILE_EXTENSION)
    template_file = os.path.join(request.folder, XSL_EXPORT_TEMPLATES, template_name)
    if os.path.exists(template_file):
        output = s3xml.transform(tree, template_file)
        if not tree:
            if jr.representation=="xml":
                output=tree
            else:
                session.error = str(T("XSL Transformation Error: ")) + s3xml.error
                redirect(URL(r=request, f="index"))
    else:
        session.error = str(T("XSL Template Not Found: ")) + XSL_EXPORT_TEMPLATES + "/" + template_name
        redirect(URL(r=request, f="index"))

    # Serialize
    output_str = s3xml.tostring(output)

    # Done
    return output_str

#
# import_csv ------------------------------------------------------------------
#
def import_csv(file, table=None):
    "Import CSV file into Database"
    if table:
        table.import_from_csv_file(file)
    else:
        # This is the preferred method as it updates reference fields
        db.import_from_csv_file(file)

#
# import_json -----------------------------------------------------------------
#
def import_json(method):
    """Import GET vars into Database & respond in JSON
    Supported methods: 'create' & 'update'
    """
    record = Storage()
    uuid = False
    for var in request.vars:
        # Skip the Representation
        if var == 'format':
            pass
        if var == 'uuid' and method == 'update':
            uuid = True
        else:
            record[var] = request.vars[var]
    if method == 'update' and not uuid:
        item = '{"Status":"failed","Error":{"StatusCode":400,"Message":"UUID required!"}}'
    else:
        item = ''
        for var in record:
            # Validate request manually
            # TODO: this is wrong - requires can be (uses to be) a list,
            #                       and validators can manipulate values
            if table[var].requires(record[var])[1]:
                item += '{"Status":"failed","Error":{"StatusCode":403,"Message":"' + var + ' invalid: ' + table[var].requires(record[var])[1] + '"}}'
        if item:
            # Don't import if validation failed
            pass
        else:
            try:
                if method == 'create':
                    id = table.insert(**dict (record))
                    item = '{"Status":"success","Error":{"StatusCode":201,"Message":"Created as ' + URL(r=request, c=module, f=resource, args=id) + '"}}'
                elif method == 'update':
                    result = db(table.uuid==request.vars.uuid).update(**dict (record))
                    if result:
                        item = '{"Status":"success","Error":{"StatusCode":200,"Message":"Record updated."}}'
                    else:
                        item = '{"Status":"failed","Error":{"StatusCode":404,"Message":"Record ' + request.vars.uuid + ' does not exist."}}'
                else:
                    item = '{"Status":"failed","Error":{"StatusCode":400,"Message":"Unsupported Method!"}}'
            except:
                item = '{"Status":"failed","Error":{"StatusCode":400,"Message":"Invalid request!"}}'
    response.headers['Content-Type'] = 'text/x-json'
    return item

#
# import_xml ------------------------------------------------------------------
#
def import_xml(jr, onvalidation=None, onaccept=None):
    """
        Import XML data
    """
    s3xml = S3XML(db)

    http_put = False
    if "filename" in jr.request.vars:
        source = jr.request.vars["filename"]
    elif "fetchurl" in jr.request.vars:
        source = jr.request.vars["fetchurl"]
    else:
        http_put = True
        source = jr.request.body

    _tree = s3xml.parse(source)

    # XSL Transformation
    template_name = "%s.%s" % (jr.representation, XSL_FILE_EXTENSION)
    template_file = os.path.join(request.folder, XSL_IMPORT_TEMPLATES, template_name)
    if os.path.exists(template_file):
        tree = s3xml.transform(_tree, template_file)
        if not tree:
            session.error = str(T("XSL Transformation Error: ")) + s3xml.error
            redirect(URL(r=request, f="index"))
    else:
        session.error = str(T("XSL Template Not Found: ")) + XSL_IMPORT_TEMPLATES + "/" + template_name
        redirect(URL(r=request, f="index"))

    if jr.jresource:
        jrequest = True
        joins = [dict(prefix=jr.jmodule, name=jr.jresource, pkey=jr.pkey, fkey=jr.fkey, id=jr.jrecord_id)]
    else:
        jrequest = False
        joins = jrlayer.get_joins(jr.module, jr.resource)

    if onaccept:
        _onaccept = lambda form: shn_audit_update(form, jr.module, jr.resource, jr.representation) and onaccept(form)
    else:
        _onaccept = lambda form: shn_audit_update(form, jr.module, jr.resource, jr.representation)

    if jr.method=="create":
        jr.record_id=None

    success = s3xml.put(jr.module, jr.resource, jr.record_id, tree,
        joins=joins,
        jrequest=jrequest,
        onvalidation=onvalidation,
        onaccept=_onaccept)

    if success:
        for i in s3xml.imports:
            if not i.committed:
                i.onvalidation = jrlayer.get_attr(i.name, "onvalidation")
                if i.method=="create":
                    i.onaccept = lambda form: \
                        shn_audit_create(form, i.prefix, i.name, jr.representation) and \
                        jrlayer.get_attr(i.name, "onaccept")
                else:
                    i.onaccept = lambda form: \
                        shn_audit_update(form, i.prefix, i.name, jr.representation) and \
                        jrlayer.get_attr(i.name, "onaccept")
        s3xml.commit()
        item = '{"Status":"OK","Error":{"StatusCode":200}}'
    else:
        item = '{"Status":"failed","Error":{"StatusCode":501,"Message":"%s"}}' % s3xml.error

    # Q: Is it correct to respond in JSON, and if so - why use plain.html then?
    return dict(item=item)

# *****************************************************************************
# Authorisation

#
# shn_has_permission ----------------------------------------------------------
#
def shn_has_permission(name, table_name, record_id = 0):
    """
    S3 framework function to define whether a user can access a record
    Designed to be called from the RESTlike controller
    """
    if session.s3.security_policy == 1:
        # Simple policy
        # Anonymous users can Read.
        if name == 'read':
            authorised = True
        else:
            # Authentication required for Create/Update/Delete.
            authorised = auth.is_logged_in() or auth.basic()
    else:
        # Full policy
        if auth.is_logged_in() or auth.basic():
            # Administrators are always authorised
            if auth.has_membership(1):
                authorised = True
            else:
                # Require records in auth_permission to specify access
                authorised = auth.has_permission(name, table_name, record_id)
        else:
            # No access for anonymous
            authorised = False
    return authorised

#
# shn_accessible_query --------------------------------------------------------
#
def shn_accessible_query(name, table):
    """
    Returns a query with all accessible records for the current logged in user
    This method does not work on GAE because uses JOIN and IN
    """
    # If using the 'simple' security policy then show all records
    if session.s3.security_policy == 1:
        # simple
        return table.id > 0
    # Administrators can see all data
    if auth.has_membership(1):
        return table.id > 0
    # If there is access to the entire table then show all records
    try:
        user_id = auth.user.id
    except:
        user_id = 0
    if auth.has_permission(name, table, 0, user_id):
        return table.id > 0
    # Filter Records to show only those to which the user has access
    session.warning = T("Only showing accessible records!")
    membership = auth.settings.table_membership
    permission = auth.settings.table_permission
    return table.id.belongs(db(membership.user_id == user_id)\
                       (membership.group_id == permission.group_id)\
                       (permission.name == name)\
                       (permission.table_name == table)\
                       ._select(permission.record_id))

# *****************************************************************************
# Audit
#
# These functions should always return True in order to be chainable
# by 'and' for lambda's as onaccept-callbacks. -- nursix --

#
# shn_audit_read --------------------------------------------------------------
#
def shn_audit_read(operation, module, resource, record=None, representation=None):
    "Called during Read operations to enable optional Auditing"
    if session.s3.audit_read:
        db.s3_audit.insert(
                person = auth.user.id if session.auth else 0,
                operation = operation,
                module = module,
                resource = resource,
                record = record,
                representation = representation,
            )
    return True

#
# shn_audit_create ------------------------------------------------------------
#
def shn_audit_create(form, module, resource, representation=None):
    """
        Called during Create operations to enable optional Auditing
        Called as an onaccept so that it only takes effect when
        saved & can read the new values in:
        onaccept = lambda form: shn_audit_create(form, module, resource, representation)
    """
    if session.s3.audit_write:
        record =  form.vars.id
        new_value = []
        for var in form.vars:
            new_value.append(var + ':' + str(form.vars[var]))
        db.s3_audit.insert(
                person = auth.user.id if session.auth else 0,
                operation = 'create',
                module = module,
                resource = resource,
                record = record,
                representation = representation,
                new_value = new_value
            )
    return True

#
# shn_audit_update ------------------------------------------------------------
#
def shn_audit_update(form, module, resource, representation=None):
    """
        Called during Create operations to enable optional Auditing
        Called as an onaccept so that it only takes effect when
        saved & can read the new values in:
        onaccept = lambda form: shn_audit_update(form, module, resource, representation)
    """
    if session.s3.audit_write:
        record =  form.vars.id
        new_value = []
        for var in form.vars:
            new_value.append(var + ':' + str(form.vars[var]))
        db.s3_audit.insert(
                person = auth.user.id if session.auth else 0,
                operation = 'update',
                module = module,
                resource = resource,
                record = record,
                representation = representation,
                #old_value = old_value, # Need to store these beforehand if we want them
                new_value = new_value
            )
    return True

#
# shn_audit_update_m2m --------------------------------------------------------
#
def shn_audit_update_m2m(module, resource, record, representation=None):
    """
    Called during Update operations to enable optional Auditing
    Designed for use in M2M 'Update Qty/Delete' (which can't use crud.settings.update_onaccept)
    shn_audit_update_m2m(resource, record, representation)
    """
    if session.s3.audit_write:
        db.s3_audit.insert(
                person = auth.user.id if session.auth else 0,
                operation = 'update',
                module = module,
                resource = resource,
                record = record,
                representation = representation,
                #old_value = old_value, # Need to store these beforehand if we want them
                #new_value = new_value  # Various changes can happen, so would need to store dict of {item_id: qty}
            )
    return True

#
# shn_audit_delete ------------------------------------------------------------
#
def shn_audit_delete(module, resource, record, representation=None):
    """
        Called during Delete operations to enable optional Auditing
    """
    if session.s3.audit_write:
        module = module
        table = '%s_%s' % (module, resource)
        old_value = []
        _old_value = db(db[table].id==record).select()[0]
        for field in _old_value:
            old_value.append(field + ':' + str(_old_value[field]))
        db.s3_audit.insert(
                person = auth.user.id if session.auth else 0,
                operation = 'delete',
                module = module,
                resource = resource,
                record = record,
                representation = representation,
                old_value = old_value
            )
    return True

# *****************************************************************************
# Display Representations

# t2.itemize now deprecated
# but still used for t2.search

#
# shn_represent ---------------------------------------------------------------
#
def shn_represent(table, module, resource, deletable=True, main='name', extra=None):
    "Designed to be called via table.represent to make t2.search() output useful"
    db[table].represent = lambda table:shn_list_item(table, resource, action='display', main=main, extra=shn_represent_extra(table, module, resource, deletable, extra))
    return

#
# shn_represent_extra ---------------------------------------------------------
#
def shn_represent_extra(table, module, resource, deletable=True, extra=None):
    "Display more than one extra field (separated by spaces)"
    authorised = shn_has_permission('delete', table)
    item_list = []
    if extra:
        extra_list = extra.split()
        for any_item in extra_list:
            item_list.append("TD(db(db.%s_%s.id==%i).select()[0].%s)" % (module, resource, table.id, any_item))
    if authorised and deletable:
        item_list.append("TD(INPUT(_type='checkbox', _class='delete_row', _name='%s', _id='%i'))" % (resource, table.id))
    return ','.join( item_list )

#
# shn_list_item ---------------------------------------------------------------
#
def shn_list_item(table, resource, action, main='name', extra=None):
    "Display nice names with clickable links & optional extra info"
    item_list = [TD(A(table[main], _href=URL(r=request, f=resource, args=[action, table.id])))]
    if extra:
        item_list.extend(eval(extra))
    items = DIV(TABLE(TR(item_list)))
    return DIV(*items)

#
# pagenav ---------------------------------------------------------------------
#
def pagenav(page=1, totalpages=None, first='1', prev='<', next='>', last='last', pagenums=10):
    '''
      Generate a page navigator around current record number, eg 1 < 3 4 5 > 36
      Derived from: http://99babysteps.appspot.com/how2/default/article_read/2
    '''
    if not totalpages:
        maxpages = page + 1
    else:
        maxpages = totalpages
        page = min(page, totalpages)
    pagerange = pagenums / 2 # half the page numbers will be below the startpage, half above
    # create page selector list eg 1 2 3
    pagelinks = [i for i in range(max(1, page - pagerange), min(page + pagerange, maxpages) + 1)]
    startpagepos = pagelinks.index(page)
    # make pagelist into hyperlinks:
    pagelinks = [A(str(pagelink), _href=URL(r=request, vars={'page':pagelink})) for pagelink in pagelinks]
    # remove link to current page & make text emphasised:
    pagelinks[startpagepos] = B(str(page))
    if page < maxpages:
        nextlink = A(next, _href=URL(r=request, vars={'page':page + 1}))
    else:
        # no link if no next
        nextlink = next
    if page > 1:
        prevlink = A(prev, _href=URL(r=request, vars={'page':page - 1}))
        firstlink = A(first, _href=URL(r=request, vars={'page':1}))
    else:
        # no links if no prev
        prevlink = prev
        firstlink = DIV(first)
    if last <> '':
        if totalpages > 0:
            lasttext = last + '(' + str(totalpages) + ')'
        else:
            lasttext = last + '...'
    lastlink = A(lasttext, _href=URL(r=request, vars={'page':maxpages}))
    delim = XML('&nbsp;') # nonbreaking delim
    pagenav = firstlink
    pagenav.append(delim)
    pagenav.append(prevlink)
    pagenav.append(delim)
    for pageref in pagelinks:
        pagenav.append(pageref)
        pagenav.append(delim)
    pagenav.append(nextlink)
    pagenav.append(delim)
    pagenav.append(lastlink)
    return pagenav

#
# shn_custom_view -------------------------------------------------------------
#
def shn_custom_view(jr, default_name):

    if jr.jresource:

        custom_view = '%s_%s_%s' % (jr.resource, jr.jresource, default_name)
        _custom_view = os.path.join(request.folder, 'views', jr.module, custom_view)

        if not os.path.exists(_custom_view):
            custom_view = '%s_%s' % (jr.resource, default_name)
            _custom_view = os.path.join(request.folder, 'views', jr.module, custom_view)

    else:
        custom_view = '%s_%s' % (jr.resource, default_name)
        _custom_view = os.path.join(request.folder, 'views', jr.module, custom_view)


    if os.path.exists(_custom_view):
        response.view = jr.module + '/' + custom_view
    else:
        response.view = default_name

# *****************************************************************************
# CRUD Functions

#
# shn_read --------------------------------------------------------------------
#
def shn_read(jr, pheader=None, editable=True, deletable=True, rss=None):
    """
        Read a single record
    """

    if jr.jresource:
        module = jr.jmodule
        resource = jr.jresource
        table = jr.jtable
        tablename = jr.jtablename

        query = (table[jr.fkey]==jr.record[jr.pkey])
        if jr.jrecord_id:
            query = (table.id==jr.jrecord_id) & query
        if 'deleted' in table:
            query = ((table.deleted==False) | (table.deleted==None)) & query

        try:
            record_id = db(query).select(table.id)[0].id
            href_delete = URL(r=jr.request, f=jr.resource, args=[jr.record_id, resource, 'delete', record_id])
            href_edit = URL(r=jr.request, f=jr.resource, args=[jr.record_id, resource, 'update', record_id])
        except:
            if not jr.multiple:
                redirect(URL(r=jr.request, f=jr.resource, args=[jr.record_id, resource, 'create']))
            else:
                record_id = None
                href_delete = None
                href_edit = None
                session.error = BADRECORD
                redirect(jr.there()) # TODO: this is wrong when no records exist!

        editable = jrlayer.get_attr(resource, 'editable')
        deletable = jrlayer.get_attr(resource, 'deletable')

        rss = jrlayer.rss(resource)

    else:
        module = jr.module
        resource = jr.resource
        table = jr.table
        tablename = jr.tablename

        record_id = jr.record_id
        href_delete = URL(r=jr.request, f=jr.resource, args=['delete', record_id])
        href_edit = URL(r=jr.request, f=jr.resource, args=['update', record_id])

    authorised = shn_has_permission('read', table, record_id)
    if authorised:

        shn_audit_read(operation='read', module=module, resource=resource, record=record_id, representation=jr.representation)

        if jr.representation=="html":
            shn_custom_view(jr, 'display.html')
            try:
                title = s3.crud_strings[jr.tablename].title_display
            except:
                title = s3.crud_strings.title_display
            output = dict(title=title)
            if jr.jresource:
                try:
                    subtitle = s3.crud_strings[tablename].title_display
                except:
                    subtitle = s3.crud_strings.title_display
                output.update(subtitle=subtitle)
                if pheader:
                    try:
                        _pheader = pheader(jr.resource, jr.record_id, jr.representation, next=jr.there(), same=jr.same())
                    except:
                        _pheader = pheader
                    if _pheader:
                        output.update(pheader=_pheader)
            item = crud.read(table, record_id)
            if href_edit and editable:
                edit = A(T("Edit"), _href=href_edit, _id='edit-btn')
            else:
                edit = ''
            if href_delete and deletable:
                delete = A(T("Delete"), _href=href_delete, _id='delete-btn')
            else:
                delete = ''
            try:
                label_list_button = s3.crud_strings[tablename].label_list_button
            except:
                label_list_button = s3.crud_strings.label_list_button
            list_btn = A(label_list_button, _href=jr.there(), _id='list-btn')

            output.update(module_name=module_name, item=item, title=title, edit=edit, delete=delete, list_btn=list_btn)

            if jr.jresource and not jr.multiple:
                del output["list_btn"]

            return(output)

        elif jr.representation == "plain":
            item = crud.read(table, record_id)
            response.view = 'plain.html'
            return dict(item=item)

        elif jr.representation == "csv":
            query = db[table].id == record_id
            return export_csv(resource, query)

        elif jr.representation == "json": # TODO: encoding problems, output contains Python-strings
            query = db[table].id == record_id
            return export_json(table, query)

        elif jr.representation == "pdf": # TODO: encoding problems, doesn't quite work
            query = db[table].id == record_id
            return export_pdf(table, query)

        elif jr.representation == "xls":
            query = db[table].id == record_id
            return export_xls(table, query)

        elif jr.representation in shn_xml_export_formats:
            return export_xml(jr)

        elif jr.representation == "rss": # TODO: replace by XML export
            query = db[table].id == record_id
            return export_rss(module, resource, query, rss=rss, linkto=jr.here('html'))

        else:
            session.error = BADFORMAT
            redirect(URL(r=request, f='index'))
    else:
        session.error = UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': jr.here()}))
#
# shn_list --------------------------------------------------------------------
#
def shn_list_linkto(field):
    return URL(r=request, args=[field],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})

def shn_list_jlinkto(field):
    return URL(r=request, args=[request.args[0], request.args[1], field],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})

def shn_list(jr, pheader=None, list_fields=None, listadd=True, main=None, extra=None, orderby=None, sortby=None, onvalidation=None, onaccept=None, rss=None):
    """
        List records matching the request
    """

    if jr.jresource:
        module = jr.jmodule
        resource = jr.jresource
        table = jr.jtable
        tablename = jr.jtablename

        listadd = jrlayer.get_attr(resource, 'listadd')
        if listadd==None:
            listadd=True

        main, extra = jrlayer.head_fields(resource)
        orderby = jrlayer.get_attr(resource, 'orderby')
        sortby = jrlayer.get_attr(resource, 'sortby')
        onvalidation = jrlayer.get_attr(resource, 'onvalidation')
        onaccept =  jrlayer.get_attr(resource, 'onaccept')
        rss = jrlayer.rss(resource)

        query = shn_accessible_query('read', table)
        query = (table[jr.fkey]==jr.record[jr.pkey]) & query

        if jr.jrecord_id:
            query = (table.id==jr.jrecord_id) & query

        href_add = URL(r=jr.request, f=jr.resource, args=[jr.record_id, resource, 'create'])

    else:
        module = jr.module
        resource = jr.resource
        table = jr.table
        tablename = jr.tablename

        query = shn_accessible_query('read', table)

        if response.s3.filter:
            query = response.s3.filter & query

        href_add = URL(r=jr.request, f=jr.resource, args=['create'])

    if 'deleted' in table:
        query = ((table.deleted == False) | (table.deleted == None)) & query

    shn_audit_read(operation='list', module=module, resource=resource, representation=jr.representation)

    if jr.representation=="html":
        output = dict(module_name=module_name, main=main, extra=extra, sortby=sortby)

        if jr.jresource:
            try:
                title = s3.crud_strings[jr.tablename].title_display
            except:
                title = s3.crud_strings.title_display
            try:
                subtitle = s3.crud_strings[tablename].subtitle_list
            except:
                subtitle = s3.crud_strings.subtitle_list

            if pheader:
                try:
                    _pheader = pheader(jr.resource, jr.record_id, jr.representation, next=jr.there(), same=jr.same())
                except:
                    _pheader = pheader
                if _pheader:
                    output.update(pheader=_pheader)
        else:
            try:
                title = s3.crud_strings[tablename].title_list
            except:
                title = s3.crud_strings.title_list
            try:
                subtitle = s3.crud_strings[tablename].subtitle_list
            except:
                subtitle = s3.crud_strings.subtitle_list

        output.update(title=title, subtitle=subtitle)

        # Which fields do we display?
        fields = None

        if jr.jresource:
            _fields = jrlayer.get_list_fields(resource)
            if _fields:
                fields = [f for f in _fields if f.readable]
            else:
                fields = None
        elif list_fields:
            fields = [table[f] for f in list_fields if table[f].readable]

        if fields and len(fields)==0:
            fields.append(table.id)

        if not fields:
            fields = [table[f] for f in table.fields if table[f].readable]

        # Column labels
        headers = {}
        for field in fields:
            # Use custom or prettified label
            headers[str(field)] = field.label

        if jr.jresource:
            linkto = shn_list_jlinkto
        else:
            linkto = shn_list_linkto

        items = crud.select(table, query=query,
            fields=fields,
            orderby=orderby,
            headers=headers,
            linkto=linkto,
            truncate=48, _id='list', _class='display')

        if not items:
            try:
                items = s3.crud_strings[tablename].msg_list_empty
            except:
                items = s3.crud_strings.msg_list_empty

        # Update the Return with common items
        output.update(dict(items=items))

        authorised = shn_has_permission('create', table)
        if authorised and listadd:

            # Block join field
            if jr.jresource:
                _comment = table[jr.fkey].comment
                table[jr.fkey].comment = None
                table[jr.fkey].default = jr.record[jr.pkey]
                table[jr.fkey].writable = False

            if onaccept:
                _onaccept = lambda form: shn_audit_create(form, module, resource, jr.representation) and jrlayer.store_session(session,module,resource,form.vars.id) and onaccept(form)
            else:
                _onaccept = lambda form: shn_audit_create(form, module, resource, jr.representation) and jrlayer.store_session(session,module,resource,form.vars.id)

            try:
                message = s3.crud_strings[tablename].msg_record_created
            except:
                message = s3.crud_strings.msg_record_created

            # Display the Add form below List
            form = crud.create(table, onvalidation=onvalidation, onaccept=_onaccept, message=message, next=jr.there())
            #form[0].append(TR(TD(), TD(INPUT(_type="reset", _value="Reset form"))))

            if jr.jresource:
                table[jr.fkey].comment = _comment

            try:
                addtitle = s3.crud_strings[tablename].subtitle_create
            except:
                addtitle = s3.crud_strings.subtitle_create

            # Check for presence of Custom View
            shn_custom_view(jr, 'list_create.html')

            # Add specificities to Return
            output.update(dict(form=form, addtitle=addtitle))

        else:
            # List only with create button below
            if listadd:
                try:
                    label_create_button = s3.crud_strings[tablename].label_create_button
                except:
                    label_create_button = s3.crud_strings.label_create_button
                add_btn = A(label_create_button, _href=href_add, _id='add-btn')
            else:
                add_btn = ''

            # Check for presence of Custom View
            shn_custom_view(jr, 'list.html')

            # Add specificities to Return
            output.update(dict(add_btn=add_btn))

        return output

    elif jr.representation == "plain":
        items = crud.select(table, query, truncate=24)
        response.view = 'plain.html'
        return dict(item=items)

    elif jr.representation == "csv":
        return export_csv(resource, query)

    elif jr.representation == "json":
        return export_json(table, query)

    elif jr.representation == "pdf":
        return export_pdf(table, query)

    elif jr.representation == "xls":
        return export_xls(table, query)

    elif jr.representation in shn_xml_export_formats:
        return export_xml(jr)

    elif jr.representation == "rss":
        return export_rss(module, resource, query, rss=rss, linkto=jr.there('html'))

    else:
        session.error = BADFORMAT
        redirect(URL(r=request, f='index'))

#
# shn_create ------------------------------------------------------------------
#
def shn_create(jr, pheader=None, onvalidation=None, onaccept=None, main=None):
    """
        Create a new record
    """
    if jr.jresource:
        module = jr.jmodule
        resource = jr.jresource
        table = jr.jtable
        tablename = jr.jtablename

        onvalidation = jrlayer.get_attr(resource, 'create_onvalidation')
        onaccept = jrlayer.get_attr(resource, 'create_onaccept')
        main, extra = jrlayer.head_fields(resource)

    else:
        module = jr.module
        resource = jr.resource
        table = jr.table
        tablename = jr.tablename

    if jr.representation == "html":

        # Check for presence of Custom View
        shn_custom_view(jr, 'create.html')

        output = dict(module_name=module_name, module=module, resource=resource, main=main)

        if jr.jresource:
            try:
                title = s3.crud_strings[jr.tablename].title_display
            except:
                title = s3.crud_strings.title_display
            try:
                subtitle = s3.crud_strings[tablename].subtitle_create
            except:
                subtitle = s3.crud_strings.subtitle_create
            output.update(subtitle=subtitle)

            if pheader:
                try:
                    _pheader = pheader(jr.resource, jr.record_id, jr.representation, next=jr.there(), same=jr.same())
                except:
                    _pheader = pheader
                if _pheader:
                    output.update(pheader=_pheader)
        else:
            try:
                title = s3.crud_strings[tablename].title_create
            except:
                title = s3.crud_strings.title_create

        try:
            label_list_button = s3.crud_strings[tablename].label_list_button
        except:
            label_list_button = s3.crud_strings.label_list_button
        list_btn = A(label_list_button, _href=jr.there(), _id='list-btn')

        output.update(title=title, list_btn=list_btn)

        if jr.jresource:
            # Block join field
            _comment = table[jr.fkey].comment
            table[jr.fkey].comment = None
            table[jr.fkey].default = jr.record[jr.pkey]
            table[jr.fkey].writable = False
            # Save callbacks
            create_onvalidation = crud.settings.create_onvalidation
            create_onaccept = crud.settings.create_onaccept
            create_next = crud.settings.create_next
            # Neutralize callbacks
            crud.settings.create_onvalidation = None
            crud.settings.create_onaccept = None
            crud.settings.create_next = jrlayer.get_attr(jr.jresource, 'create_next') or jr.there()

        if onaccept:
            _onaccept = lambda form: \
                shn_audit_create(form, module, resource, jr.representation) and \
                jrlayer.store_session(session,module,resource,form.vars.id) and \
                onaccept(form)
        else:
            _onaccept = lambda form: \
                shn_audit_create(form, module, resource, jr.representation) and \
                jrlayer.store_session(session,module,resource,form.vars.id)

        try:
            message = s3.crud_strings[tablename].msg_record_created
        except:
            message = s3.crud_strings.msg_record_created

        form = crud.create(table, message=message, onvalidation=onvalidation, onaccept=_onaccept)
        #form[0].append(TR(TD(), TD(INPUT(_type="reset", _value="Reset form"))))

        if jr.jresource:
            # Restore comment
            table[jr.fkey].comment = _comment
            # Restore callbacks
            crud.settings.create_onvalidation = create_onvalidation
            crud.settings.create_onaccept = create_onaccept
            crud.settings.create_next = create_next

        output.update(form=form)

        if jr.jresource and not jr.multiple:
            del output["list_btn"]

        return output

    elif jr.representation == "plain":
        if onaccept:
            _onaccept = lambda form: shn_audit_create(form, module, resource, jr.representation) and onaccept(form)
        else:
            _onaccept = lambda form: shn_audit_create(form, module, resource, jr.representation)

        form = crud.create(table, onvalidation=onvalidation, onaccept=_onaccept)
        response.view = 'plain.html'
        return dict(item=form)

    elif jr.representation == "popup":
        if onaccept:
            _onaccept = lambda form: shn_audit_create(form, module, resource, jr.representation) and onaccept(form)
        else:
            _onaccept = lambda form: shn_audit_create(form, module, resource, jr.representation)

        form = crud.create(table, onvalidation=onvalidation, onaccept=_onaccept)
        # Check for presence of Custom View
        shn_custom_view(jr, 'popup.html')
        return dict(module_name=module_name, form=form, module=module, resource=resource, main=main, caller=request.vars.caller)

    elif jr.representation == "json":
        return import_json(method='create')

    elif jr.representation == "csv":
        # Read in POST
        file = request.vars.filename.file
        try:
            import_csv(file, table)
            session.flash = T('Data uploaded')
        except:
            session.error = T('Unable to parse CSV file!')
        redirect(jr.there())

    elif jr.representation in shn_xml_import_formats:
        response.view = 'plain.html'
        return import_xml(jr, onvalidation=onvalidation, onaccept=onaccept)

    else:
        session.error = BADFORMAT
        redirect(URL(r=request, f='index'))

#
# shn_update ------------------------------------------------------------------
#
def shn_update(jr, pheader=None, deletable=True, onvalidation=None, onaccept=None):
    """
        Update an existing record
    """
    if jr.jresource:

        if jr.multiple and not jr.jrecord_id:
            return shn_create(jr, pheader)

        module = jr.jmodule
        resource = jr.jresource
        table = jr.jtable
        tablename = jr.jtablename

        query = (table[jr.fkey]==jr.record[jr.pkey])
        if jr.jrecord_id:
            query = (table.id==jr.jrecord_id) & query
        if 'deleted' in table:
            query = ((table.deleted==False) | (table.deleted==None)) & query

        try:
            record_id = db(query).select(table.id)[0].id
        except:
            record_id = None
            href_delete = None
            href_edit = None
            session.error = BADRECORD
            redirect(jr.there())

        onvalidation = jrlayer.get_attr(resource, 'update_onvalidation')
        onaccept = jrlayer.get_attr(resource, 'update_onaccept')
        deletable = jrlayer.get_attr(resource, 'deletable')

    else:

        module = jr.module
        resource = jr.resource
        table = jr.table
        tablename = jr.tablename

        record_id = jr.record_id

    authorised = shn_has_permission('delete', table, record_id)
    if not authorised:
        deletable = False

    authorised = shn_has_permission('update', table, record_id)
    if authorised:

        crud.settings.update_deletable = deletable

        if jr.representation == "html":

            shn_custom_view(jr, 'update.html')

            output = dict(module_name=module_name)

            if jr.jresource:
                try:
                    title = s3.crud_strings[jr.tablename].title_display
                except:
                    title = s3.crud_strings.title_display
                try:
                    subtitle = s3.crud_strings[tablename].title_update
                except:
                    subtitle = s3.crud_strings.title_update
                output.update(subtitle=subtitle)

                if pheader:
                    try:
                        _pheader = pheader(jr.resource, jr.record_id, jr.representation, next=jr.there(), same=jr.same())
                    except:
                        _pheader = pheader
                    if _pheader:
                        output.update(pheader=_pheader)
            else:
                try:
                    title = s3.crud_strings[tablename].title_update
                except:
                    title = s3.crud_strings.title_update

            try:
                label_list_button = s3.crud_strings[tablename].label_list_button
            except:
                label_list_button = s3.crud_strings.label_list_button
            list_btn = A(label_list_button, _href=jr.there(), _id='list-btn')

            output.update(title=title, list_btn=list_btn)

            if jr.jresource:
                # Block join field
                _comment = table[jr.fkey].comment
                table[jr.fkey].comment = None
                table[jr.fkey].default = jr.record[jr.pkey]
                table[jr.fkey].writable = False
                # Save callbacks
                update_onvalidation = crud.settings.update_onvalidation
                update_onaccept = crud.settings.update_onaccept
                update_next = crud.settings.update_next
                # Neutralize callbacks
                crud.settings.update_onvalidation = None
                crud.settings.update_onaccept = None
                crud.settings.update_next = jrlayer.get_attr(jr.jresource, 'update_next') or jr.there()

            try:
                message = s3.crud_strings[tablename].msg_record_modified
            except:
                message = s3.crud_strings.msg_record_modified

            if onaccept:
                _onaccept = lambda form: \
                    shn_audit_update(form, module, resource, jr.representation) and \
                    jrlayer.store_session(session, module, resource, form.vars.id) and \
                    onaccept(form)
            else:
                _onaccept = lambda form: \
                    shn_audit_update(form, module, resource, jr.representation) and \
                    jrlayer.store_session(session, module, resource, form.vars.id)

            form = crud.update(table, record_id, message=message, onvalidation=onvalidation, onaccept=_onaccept)
            #form[0].append(TR(TD(), TD(INPUT(_type="reset", _value="Reset form"))))

            if jr.jresource:
                # Restore comment
                table[jr.fkey].comment = _comment
                # Restore callbacks
                crud.settings.update_onvalidation = update_onvalidation
                crud.settings.update_onaccept = update_onaccept
                crud.settings.update_next = update_next

            output.update(form=form)

            if jr.jresource and not jr.multiple:
                del output["list_btn"]

            return(output)

        elif jr.representation == "plain":
            if onaccept:
                _onaccept = lambda form: shn_audit_update(form, module, resource, jr.representation) and onaccept(form)
            else:
                _onaccept = lambda form: shn_audit_update(form, module, resource, jr.representation)

            form = crud.update(table, record_id, onvalidation=onvalidation, onaccept=_onaccept)
            response.view = 'plain.html'
            return dict(item=form)

        elif jr.representation == "json":
            return import_json(method='update')

        elif jr.representation in shn_xml_import_formats:
            response.view = 'plain.html'
            return import_xml(jr, onvalidation=onvalidation, onaccept=onaccept)

        else:
            session.error = BADFORMAT
            redirect(URL(r=request, f='index'))

    else:
        session.error = UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': jr.here()}))
#
# shn_delete ------------------------------------------------------------------
#
def shn_delete(jr):
    """
        Delete record(s)
    """

    if jr.jresource:
        module = jr.jmodule
        resource = jr.jresource
        table = jr.jtable
        tablename = jr.jtablename

        onvalidation = jrlayer.get_attr(resource, 'delete_onvalidation')
        onaccept = jrlayer.get_attr(resource, 'delete_onaccept')

        query = (table[jr.fkey]==jr.record[jr.pkey])
        if jr.jrecord_id:
            query = (table.id==jr.jrecord_id) & query
        if 'deleted' in table:
            query = ((table.deleted==False) | (table.deleted==None)) & query

    else:
        module = jr.module
        resource = jr.resource
        table = jr.table
        tablename = jr.tablename

        query = (table.id==jr.record_id)
        if 'deleted' in table:
            query = ((table.deleted==False) | (table.deleted==None)) & query

    # Get target records
    rows = db(query).select(table.ALL)

    # Nothing to do? Return here!
    if not rows or len(rows)==0:
        session.confirmation = T('No records to delete')
        return

    try:
        message = s3.crud_strings[tablename].msg_record_deleted
    except:
        message = s3.crud_strings.msg_record_deleted

    if jr.jresource:
        # Save callback settings
        delete_onvalidation = crud.settings.delete_onvalidation
        delete_onaccept = crud.settings.delete_onaccept
        delete_next = crud.settings.delete_next

        # Set resource specific callbacks, if any
        crud.settings.delete_onvalidation = onvalidation
        crud.settings.delete_onaccept = onaccept
        crud.settings.delete_next = None # do not set here!

    # Delete all accessible records
    numrows = 0
    for row in rows:
        if shn_has_permission('delete', table, row.id):
            numrows += 1
            shn_audit_delete(module, resource, row.id, jr.representation)
            if "deleted" in db[table] and db(db.s3_setting.id==1).select()[0].archive_not_delete:
                if crud.settings.delete_onvalidation:
                    crud.settings.delete_onvalidation(row)
                db(db[table].id == row.id).update(deleted = True)
                if crud.settings.delete_onaccept:
                    crud.settings.delete_onaccept(row)
            else:
                if jr.representation == "ajax":
                    crud.settings.delete_next = jr.there(representation=jr.representation)
                crud.delete(table, row.id)
        else:
            continue

    if jr.jresource:
        # Restore callback settings
        crud.settings.delete_onvalidation = delete_onvalidation
        crud.settings.delete_onaccept = delete_onaccept
        crud.settings.delete_next = delete_next

        delete_next =  jrlayer.get_attr(resource, 'delete_next')

    # Confirm and return
    if numrows > 1:
        session.confirmation = "%s %s" % ( numrows, T('records deleted'))
    else:
        session.confirmation = message

    if jr.jresource and delete_next: # but redirect here!
        redirect(delete_next)

    return

# *****************************************************************************
# Main controller function

#
# shn_rest_controller ---------------------------------------------------------
#
def shn_rest_controller(module, resource,
    deletable=True,
    editable=True,
    listadd=True,
    list_fields=None,
    main='name',
    extra=None,
    orderby=None,
    sortby=None,
    pheader=None,
    rss=None,
    onvalidation=None,
    onaccept=None):
    """
    RESTlike controller function.

    Provides CRUD operations for the given module/resource.

    Optional parameters:
        deletable=False                 don't provide visible options for deletion
        editable=False                  don't provide visible options for editing
        listadd=False                   don't provide an add form in the list view
        main='field'                    the field used for the title in RSS output
        extra='field'                   the field used for the description in RSS output & in Search AutoComplete
        orderby=expression              the sort order for server-side paginated list views e.g: db.mytable.myfield1|db.mytable.myfield2
        sortby=list                     the sort order for client-side paginated list views e.g: [[1, "asc"], [2, "desc"]]
            see: http://datatables.net/examples/basic_init/table_sorting.html

        onvalidation=lambda form: function(form)    callback processed *before* DB IO
        onaccept=lambda form: function(form)        callback processed *after* DB IO

        pheader=function(resource, record_id, representation, next=there, same=same)
                                        function to produce a page header for the primary resource

    Request options:

        response.s3.filter              contains custom query to filter list views

    Customisable Security Policy
    Auditing options for Read &/or Write.

    Representation is recognized from the extension of the target resource.
    You can still pass a "?format=" to override this.

    Supported Representations:
        HTML                        is the default (including full Layout)
        PLAIN                       is HTML with no layout
                                        - can be inserted into DIVs via AJAX calls
                                        - can be useful for clients on low-bandwidth or small screen sizes
        JSON                        designed to be accessed via JavaScript
                                        - responses in JSON format
                                        - create/update/delete done via simple GET vars (no form displayed)
        CSV                         useful for synchronization / database migration
                                        - List/Display/Create for now
        RSS (list only)
        XML (list/read only)
        AJAX (designed to be run asynchronously to refresh page elements)
        POPUP
        XLS (list/read only)
        PDF (list/read only)

    ToDo:
        Alternate Representations
            CSV update
            SMS, LDIF
    """

    # Parse original request --------------------------------------------------

    jr = JRequest(jrlayer, module, resource, request, session=session)

    # Invalid request?
    if jr.invalid:
        if jr.badmethod:
            session.error = BADMETHOD
        elif jr.badrecord:
            session.error = BADRECORD
        else:
            session.error = INVALIDREQUEST
        redirect(URL(r=request, c=request.controller, f='index'))

    # Get backlinks
    here = jr.here()
    there = jr.there()
    same = jr.same()

    # Check read permission on primary table
    if not shn_has_permission('read', jr.table):
        session.error = UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': here}))

    # Record ID is required in joined-table operations and read action:
    if not jr.record_id and (jr.jresource or jr.method=="read"):

        # TODO: Cleanup - this is PR specific
        if jr.module=="pr" and jr.resource=="person" and jr.representation=='html':
            redirect(URL(r=request, f='person', args='search_simple', vars={"_next": same}))

        else:
            session.error = BADRECORD
            redirect(URL(r=request, f='index'))

    # *************************************************************************
    # Joined Table Operation

    if jr.jresource:
        if jr.method and jr.custom_action:
            try:
                return(jr.custom_action(
                    jr.module,
                    jr.resource,
                    jr.record_id,
                    jr.method,
                    jmodule=jr.jmodule,
                    jresource=jr.jresource,
                    jrecord_id=jr.jrecord_id,
                    joinby=jr.fkey,
                    multiple=jr.multiple,
                    representation=jr.representation,
                    onvalidation=None,
                    onaccept=None))
            except:
                raise HTTP(501)

        # HTTP Multi-Record Operation *****************************************
        if jr.method==None and jr.multiple and not jr.jrecord_id:

            # HTTP List/List-add ----------------------------------------------
            if jr.http=='GET' or jr.http=='POST':
                authorised = shn_has_permission('read', jr.jtable)
                if authorised:
                    return shn_list(jr, pheader, rss=rss)
                else:
                    session.error = UNAUTHORISED
                    redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': here }))

            # HTTP Create -----------------------------------------------------
            elif jr.http=='PUT':
                # Not implemented
                raise HTTP(501)

            # HTTP Delete -----------------------------------------------------
            elif jr.http=='DELETE':
                # Not implemented
                raise HTTP(501)

            # Unsupported HTTP method -----------------------------------------
            else:
                # Unsupported HTTP method for this context:
                # HEAD, OPTIONS, TRACE, CONNECT
                # Not implemented
                raise HTTP(501)

        # HTTP Single-Record Operation ****************************************
        elif jr.method==None and (jr.jrecord_id or not jr.multiple):

            # HTTP Read/Update ------------------------------------------------
            if jr.http=='GET':
                authorised = shn_has_permission('read', jr.jtable)
                if authorised:
                    return shn_read(jr, pheader=pheader, rss=rss)
                else:
                    session.error = UNAUTHORISED
                    redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': here }))

            # HTTP Update -----------------------------------------------------
            elif jr.http=='PUT':
                response.view = 'plain.html'
                return import_xml(jr, onvalidation=onvalidation, onaccept=onaccept)
                # Not implemented
                # raise HTTP(501)

            # HTTP Delete -----------------------------------------------------
            elif jr.http=='DELETE':
                # Not implemented
                raise HTTP(501)

            # Unsupported HTTP method -----------------------------------------
            else:
                # Unsupported HTTP method for this context:
                # POST, HEAD, OPTIONS, TRACE, CONNECT
                # Not implemented
                raise HTTP(501)

        # Create (joined table) ************************************************
        elif jr.method=="create":
            authorised = shn_has_permission(jr.method, jr.jtable)
            if authorised:
                return shn_create(jr, pheader)
            else:
                session.error = UNAUTHORISED
                redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': here}))

        # Read (joined table) *************************************************
        elif jr.method=="read" or jr.method=="display":
            authorised = shn_has_permission('read', jr.jtable)
            if authorised:
                if jr.multiple and not jr.jrecord_id:
                    # This is a list action
                    return shn_list(jr, pheader, rss=rss)
                else:
                    # This is a read action
                    return shn_read(jr, pheader, rss=rss)
            else:
                session.error = UNAUTHORISED
                redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': here }))

        # Update (joined table) ***********************************************
        elif jr.method=="update":
            authorised = shn_has_permission(jr.method, jr.jtable)
            if authorised:
                return shn_update(jr, pheader)
            else:
                session.error = UNAUTHORISED
                redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': here}))

        # Delete (joined table) ***********************************************
        elif jr.method=="delete":
            authorised = shn_has_permission(jr.method, jr.jtable)
            if authorised:
                shn_delete(jr)
                redirect(there)
            else:
                session.error = UNAUTHORISED
                redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': here}))

        # Unsupported Method **************************************************
        else:
            session.error = BADMETHOD
            redirect(URL(r=request, f='index'))

    # *************************************************************************
    # Single Table Operation
    #
    else:

        # Custom Method *******************************************************
        if jr.method and jr.custom_action:
            try:
                return(jr.custom_action(
                    jr.module,
                    jr.resource,
                    jr.record_id,
                    jr.method,
                    jmodule=None,
                    jresource=None,
                    jrecord_id=None,
                    joinby=None,
                    multiple=True,
                    representation=jr.representation,
                    onvalidation=onvalidation,
                    onaccept=onaccept))
            except:
                raise HTTP(501)

        # Clear Session *******************************************************
        elif jr.method=="clear":

            # Clear session
            jrlayer.clear_session(session, jr.module, jr.resource)

            if '_next' in request.vars:
                request_vars = dict(_next=request.vars._next)
            else:
                request_vars = {}

            # Redirect to search
            # TODO: build a generic search function, this here is PR specific
            if jr.module=="pr" and jr.resource=="person" and jr.representation=="html":
                redirect(URL(r=request, f='person', args='search_simple', vars=request_vars))
            else:
                redirect(URL(r=request, c='pr', f=jr.resource))

        # HTTP Multi-Record Operation *****************************************
        elif not jr.method and not jr.record_id:

            # HTTP List or List-Add -------------------------------------------
            if jr.http == 'GET' or request.env.request_method == 'POST':
                return shn_list(jr, pheader, list_fields=list_fields, listadd=listadd, main=main, extra=extra,
                    orderby=orderby, sortby=sortby, onvalidation=onvalidation, onaccept=onaccept, rss=rss)
            # HTTP Create -----------------------------------------------------
            elif jr.http == 'PUT':
                # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6
                response.view = 'plain.html'
                return import_xml(jr, onvalidation=onvalidation, onaccept=onaccept)

            # Unsupported HTTP method -----------------------------------------
            else:
                # Unsupported HTTP method for this context:
                # DELETE, HEAD, OPTIONS, TRACE, CONNECT
                # Not implemented
                raise HTTP(501)

        # HTTP Single Record Operation ****************************************
        elif jr.record_id and not jr.method:

            # HTTP Read (single record) ---------------------------------------
            if jr.http == 'GET':
                return shn_read(jr, pheader=pheader, editable=editable, deletable=deletable, rss=rss)

            # HTTP Delete (single record) -------------------------------------
            elif jr.http == 'DELETE':
                # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.7
                if db(db[jr.table].id == jr.record_id).select():
                    authorised = shn_has_permission('delete', jr.table, jr.record_id)
                    if authorised:
                        shn_delete(jr)
                        item = '{"Status":"OK","Error":{"StatusCode":200}}'
                        response.view = 'plain.html'
                        return dict(item=item)
                    else:
                        # Unauthorised
                        raise HTTP(401)
                else:
                    # Not found
                    raise HTTP(404)

            # HTTP Create/Update (single record) ------------------------------
            elif jr.http == 'PUT':
                # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6
                # We don't yet implement PUT for create/update, although Web2Py does now support it
                # Not implemented
                response.view = 'plain.html'
                return import_xml(jr, onvalidation=onvalidation, onaccept=onaccept)

            # Unsupported HTTP method -----------------------------------------
            else:
                # Unsupported HTTP method for this context:
                # POST, HEAD, OPTIONS, TRACE, CONNECT
                # Not implemented
                raise HTTP(501)

        # Create (single table) ***********************************************
        elif jr.method == "create":
            authorised = shn_has_permission(jr.method, jr.table)
            if authorised:
                return shn_create(jr, pheader, onvalidation=onvalidation, onaccept=onaccept, main=main)
            else:
                session.error = UNAUTHORISED
                redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': here}))

        # Read (single table) *************************************************
        elif jr.method == "read" or jr.method == "display":
            request.args.remove(jr.method)
            redirect(URL(r=request, args=request.args, vars=request.vars))

        # Update (single table) ***********************************************
        elif jr.method == "update":
            authorised = shn_has_permission(jr.method, jr.table, jr.record_id)
            if authorised:
                return shn_update(jr, pheader, deletable=deletable, onvalidation=onvalidation, onaccept=onaccept)
            else:
                session.error = UNAUTHORISED
                redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': here}))

        # Delete (single table) ***********************************************
        elif jr.method == "delete":
            authorised = shn_has_permission(jr.method, jr.table, jr.record_id)
            if authorised:
                shn_delete(jr)
                redirect(there)
            else:
                session.error = UNAUTHORISED
                redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': here}))

        # Search (single table) ***********************************************
        elif jr.method == "search":
            authorised = shn_has_permission('read', jr.table)
            if authorised:
                # Filter Search list to just those records which user can read
                # query = shn_accessible_query('read', table)
                # Fails on t2's line 739: AttributeError: 'SQLQuery' object has no attribute 'get'

                # Audit
                shn_audit_read(operation='search', module=jr.module, resource=jr.resource, representation=jr.representation)

                if jr.representation == "html":

                    shn_represent(jr.table, jr.module, jr.resource, deletable, main, extra)
                    #search = t2.search(table, query)
                    search = t2.search(jr.table)

                    # Check for presence of Custom View
                    shn_custom_view(jr, 'search.html')

                    # CRUD Strings
                    title = s3.crud_strings.title_search

                    return dict(module_name=module_name, search=search, title=title)

                if jr.representation == "json":
                    # JQuery Autocomplete uses 'q' instead of 'value'
                    value = request.vars.value or request.vars.q or None
                    if request.vars.field and request.vars.filter and value:
                        field = str.lower(request.vars.field)
                        filter = request.vars.filter
                        if filter == '=':
                            query = (jr.table[field]==value)
                            item = db(query).select().json()
                        elif filter == '~':
                            query = (jr.table[field].like('%' + value + '%'))
                            limit = int(request.vars.limit) or None
                            if limit:
                                item = db(query).select(limitby=(0, limit)).json()
                            else:
                                item = db(query).select().json()
                        else:
                            item = '{"Status":"failed","Error":{"StatusCode":501,"Message":"Unsupported filter! Supported filters: =, ~"}}'
                    else:
                        item = '{"Status":"failed","Error":{"StatusCode":501,"Message":"Search requires specifying Field, Filter & Value!"}}'
                    response.view = 'plain.html'
                    return dict(item=item)

                else:
                    session.error = BADFORMAT
                    redirect(URL(r=request))
            else:
                session.error = UNAUTHORISED
                redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': here}))

        # Unsupported Method **************************************************
        else:
            session.error = BADMETHOD
            redirect(URL(r=request))

# END
# *****************************************************************************
