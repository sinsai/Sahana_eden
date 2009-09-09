# -*- coding: utf-8 -*-

#
# RESTlike CRUD controller
#
# created by Fran Boon, amendments by nursix
#

# *****************************************************************************
# Joint Resource Layer
jrlayer = JRLayer(db)

# *****************************************************************************
# Constants to ensure consistency

# Error messages
UNAUTHORISED = T('Not authorised!')
BADFORMAT = T('Unsupported format!')
BADMETHOD = T('Unsupported method!')
BADRECORD = T('No such record!')

# How many rows to show per page in list outputs
ROWSPERPAGE = 20

# *****************************************************************************
# DB helper functions

#
# shn_jr_identify_precord -----------------------------------------------------
#
def shn_jr_identify_precord(module, resource, _id, jresource):
    """
        Helper function for shn_rest_controller:
        Identifies the record_id of the main resource
    """

    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    record_id = _id

    if record_id:
        query = (table.id==record_id)
        if 'deleted' in table:
            query = ((table.deleted==False) | (table.deleted==None)) & query
        records = db(query).select(table.id)
        if records:
            record_id = records[0].id
        else:
            # Error: NO SUCH RECORD
            return 0

    if not record_id and 'id_label' in request.vars:
        id_label = str.strip(request.vars.id_label)
        if 'pr_pe_label' in table:
            query = (table.pr_pe_label==id_label)
            if 'deleted' in table:
                query = ((table.deleted==False) | (table.deleted==None)) & query
            records = db(query).select(table.id)
            if records:
                record_id = records[0].id
            else:
                # Error: NO SUCH RECORD
                return 0

    if not record_id and len(request.args)>0:
        if session.jrvars and tablename in session.jrvars:
            record_id = session.jrvars[tablename]
            query = (table.id==record_id)
            if 'deleted' in table:
                query = ((table.deleted==False) | (table.deleted==None)) & query
            records = db(query).select(table.id)
            if records:
                record_id = records[0].id
            else:
                record_id = None
                session[tablename] = None

    if record_id:
        if not session.jrvars:
            session.jrvars = Storage()

        if not tablename in session.jrvars:
            session.jrvars[tablename] = record_id

    return record_id

#
# shn_jr_clear_session --------------------------------------------------------
#
def shn_jr_clear_session(session_var):

    if session_var and session.jrvars:
        if session_var and session_var in session.jrvars:
            del session.jrvars[session_var]
    elif session.jrvars:
        del session['jrvars']
        #session.jrvars = Storage()

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
        detailElements.append(ObjectValue(attribute_name=col, left=LEFTMARGIN*cm, width=COLWIDTH*cm))
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
def export_rss(module, resource, query, main='name', extra='description'):
    """Export record(s) as RSS feed
    main='field': the field used for the title
    extra='field': the field used for the description
    """
    if request.env.remote_addr == '127.0.0.1':
        server = 'http://127.0.0.1:' + request.env.server_port
    else:
        server = 'http://' + request.env.server_name + ':' + request.env.server_port
    link = '/%s/%s/%s' % (request.application, module, resource)
    entries = []
    rows = db(query).select()
    try:
        for row in rows:
            entries.append(dict(title=row[main], link=server + link + '/%d' % row.id, description=row[extra], created_on=row.created_on))
    except:
        for row in rows:
            entries.append(dict(title=row[main], link=server + link + '/%d' % row.id, description='', created_on=row.created_on))
    import gluon.contrib.rss2 as rss2
    items = [ rss2.RSSItem(title = entry['title'], link = entry['link'], description = entry['description'], pubDate = entry['created_on']) for entry in entries]
    rss = rss2.RSS2(title = str(s3.crud_strings.subtitle_list), link = server + link + '/%d' % row.id, description = '', lastBuildDate = request.utcnow, items = items)
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
def export_xml(table, query):
    "Export record(s) as XML"
    import gluon.serializers
    items = db(query).select(table.ALL).as_list()
    response.headers['Content-Type'] = 'text/xml'
    return str(gluon.serializers.xml(items))
    
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
    if not uuid:
        item = '{"Status":"failed","Error":{"StatusCode":400,"Message":"UUID required!"}}'
    else:
        item = ''
        for var in record:
            # Validate request manually
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
# shn_audit_read --------------------------------------------------------------
#
def shn_audit_read(operation, resource, record=None, representation=None):
    "Called during Read operations to enable optional Auditing"
    if session.s3.audit_read:
        db.s3_audit.insert(
                person = auth.user.id if session.auth else 0,
                operation = operation,
                module = request.controller,
                resource = resource,
                record = record,
                representation = representation,
            )
    return

#
# shn_audit_create ------------------------------------------------------------
#
def shn_audit_create(form, resource, representation=None):
    """
    Called during Create operations to enable optional Auditing
    Called as an onaccept so that it only takes effect when saved & can read the new values in:
    crud.settings.create_onaccept = lambda form: shn_audit_create(form, resource, representation)
    """
    if session.s3.audit_write:
        record =  form.vars.id
        new_value = []
        for var in form.vars:
            new_value.append(var + ':' + str(form.vars[var]))
        db.s3_audit.insert(
                person = auth.user.id if session.auth else 0,
                operation = 'create',
                module = request.controller,
                resource = resource,
                record = record,
                representation = representation,
                new_value = new_value
            )
    return

#
# shn_audit_update ------------------------------------------------------------
#
def shn_audit_update(form, resource, representation=None):
    """
    Called during Update operations to enable optional Auditing
    Called as an onaccept so that it only takes effect when saved & can read the new values in:
    crud.settings.update_onaccept = lambda form: shn_audit_update(form, resource, representation)
    """
    if session.s3.audit_write:
        record =  form.vars.id
        new_value = []
        for var in form.vars:
            new_value.append(var + ':' + str(form.vars[var]))
        db.s3_audit.insert(
                person = auth.user.id if session.auth else 0,
                operation = 'update',
                module = request.controller,
                resource = resource,
                record = record,
                representation = representation,
                #old_value = old_value, # Need to store these beforehand if we want them
                new_value = new_value
            )
    return

#
# shn_audit_update_m2m --------------------------------------------------------
#
def shn_audit_update_m2m(resource, record, representation=None):
    """
    Called during Update operations to enable optional Auditing
    Designed for use in M2M 'Update Qty/Delete' (which can't use crud.settings.update_onaccept)
    shn_audit_update_m2m(resource, record, representation)
    """
    if session.s3.audit_write:
        db.s3_audit.insert(
                person = auth.user.id if session.auth else 0,
                operation = 'update',
                module = request.controller,
                resource = resource,
                record = record,
                representation = representation,
                #old_value = old_value, # Need to store these beforehand if we want them
                #new_value = new_value  # Various changes can happen, so would need to store dict of {item_id: qty}
            )
    return

#
# shn_audit_delete ------------------------------------------------------------
#
def shn_audit_delete(resource, record, representation=None):
    "Called during Delete operations to enable optional Auditing"
    if session.s3.audit_write:
        module = request.controller
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
    return

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

# *****************************************************************************
# CRUD Functions

def shn_select(jrequest,
    table,
    fields=None,
    main=None,
    extra=None,
    listadd=False,
    deletable=False,
    editable=False,
    orderby=None,
    sortby=None,
    onvalidation=None,
    onaccept=None,
    record=None,
    jtable=None,
    pkey=None,
    fkey=None):

    _fields = fields
    _main = main
    _extra = extra
    _listadd = listadd
    _onvalidation = onvalidation
    _onaccept = onaccept
    _deletable = deletable
    _editable = editable

    # Joined table operation **************************************************
    if jrequest.jresource:

        module = jrequest.jmodule
        resource = jrequest.jresource

        _table = jtable

        #TODO:
        #_main = jrlayer.get_main(resource)
        #_extra = jrlayer.get_extra(resource)

        # List (Joined Table) -------------------------------------------------
        if jrequest.multiple and not jrequest.jrecord_id:

            list_action = True

            _fields = jrlayer.list_fields(resource)

            query = shn_accessible_query('read', jtable)
            query = (jtable[fkey]==record[pkey]) & query

            if 'deleted' in jtable:
                query = ((jtable.deleted==False) | (jtable.deleted==None)) & query

            #TODO:
            #_listadd = jrlayer.listadd(resource)
            #_onvalidation = jrlayer.onvalidation(resource)
            #_onaccept = jrlayer.onaccept(resource)

            #TODO:
            #fix subtitle for add form in view and pheader

        # Read (Joined Table) -------------------------------------------------
        else:

            list_action = False

            record_id = jrequest.jrecord_id

            #TODO:
            #_deletable=jrlayer.deletable(resource)
            #_editable=jrlayer.editable(resource)

    # Single table operation **************************************************
    else:

        module = jrequest.module
        resource = jrequest.resource

        _table = table

        # Read (Single Table) -------------------------------------------------
        if jrequest.record_id:

            list_action = False

            record_id = jrequest.record_id

        # List (Single Table) -------------------------------------------------
        else:

            list_action = True

            # Query
            # Filter Search list to just those records which user can read
            query = shn_accessible_query('read', table)

            # Filter Search List to remove entries which have been deleted
            if 'deleted' in table:
                query = ((table.deleted == False) | (table.deleted == None)) & query # includes None for backward compatability

            # Filter Search List for custom query
            if request.filter:
                query = request.filter & query

    # Common actions **********************************************************

    # Get representation
    representation = jrequest.representation

    # List Action *************************************************************
    if list_action:

        # list_create if have permissions
        authorised = shn_has_permission('create', _table)

        # Audit
        shn_audit_read(operation='list', resource=resource, representation=representation)

        if representation == "html":
            # Start building the Return
            output = dict(module_name=module_name, main=main, extra=extra)

            # TODO: DRY
            if 'page' in request.vars:
                # Pagination at server-side (since no JS available)
                page = int(request.vars.page)
                start_record = (page - 1) * ROWSPERPAGE
                end_record = start_record + ROWSPERPAGE
                limitby = start_record, end_record
                totalpages = (db(query).count() / ROWSPERPAGE) + 1 # Fails on GAE
                label_search_button = T('Search')
                search_btn = A(label_search_button, _href=URL(r=request, f=resource, args='search'), _id='search-btn')
                output.update(dict(page=page, totalpages=totalpages, search_btn=search_btn))
            else:
                # No Pagination server-side (to allow it to be done client-side)
                limitby = None
                orderby = None
                # Redirect to a paginated version if JS not-enabled
                request.vars['page'] = 1
                response.refresh = '<noscript><meta http-equiv="refresh" content="0; url=' + URL(r=request, args=request.args, vars=request.vars) + '" /></noscript>'
                output.update(dict(sortby=sortby))

            # Which fields do we display?
            if not _fields:
                _fields = [_table[f] for f in _table.fields if _table[f].readable]

            # Column labels
            headers = {}
            for field in _fields:
                # Use custom or prettified label
                headers[str(field)] = field.label

            items = crud.select(_table, query=query, fields=_fields, limitby=limitby, orderby=orderby, headers=headers, truncate=48, _id='list', _class='display')

            # Additional CRUD strings?
            if not items:
                try:
                    items = s3.crud_strings.msg_list_empty
                except:
                    items = T('None')

            try:
                title = s3.crud_strings.title_list
            except:
                title = T('List')

            try:
                subtitle = s3.crud_strings.subtitle_list
            except:
                subtitle = ''

            # Update the Return with common items
            output.update(dict(items=items, title=title, subtitle=subtitle))

            if authorised and listadd:
                # Audit
                crud.settings.create_onaccept = lambda form: shn_audit_create(form, resource, representation)

                # TODO: Lock join field, if given
                # TODO: Fix _next in CRUD.create form

                # Display the Add form below List
                form = crud.create(_table, onvalidation=onvalidation, onaccept=onaccept)
                try:
                    addtitle = s3.crud_strings.subtitle_create
                except:
                    addtitle = T('Add New')

                # Check for presence of Custom View
                custom_view = '%s_list_create.html' % resource
                _custom_view = os.path.join(request.folder, 'views', module, custom_view)
                if os.path.exists(_custom_view):
                    response.view = module + '/' + custom_view
                else:
                    response.view = 'list_create.html'

                # Add specificities to Return
                output.update(dict(form=form, addtitle=addtitle))

            else:
                # List only with create button below
                if listadd:
                    try:
                        label_create_button = s3.crud_strings.label_create_button
                    except:
                        label_create_button = T('Add')
                    add_btn = A(label_create_button, _href=URL(r=request, f=resource, args='create'), _id='add-btn')
                else:
                    add_btn = ''

                # Check for presence of Custom View
                custom_view = '%s_list.html' % resource
                _custom_view = os.path.join(request.folder, 'views', module, custom_view)
                if os.path.exists(_custom_view):
                    response.view = module + '/' + custom_view
                else:
                    response.view = 'list.html'

                # Add specificities to Return
                output.update(dict(add_btn=add_btn))

            return output

        elif representation == "plain":
            items = crud.select(_table, query, truncate=24)
            response.view = 'plain.html'
            return dict(item=items)

        elif representation == "csv":
            return export_csv(resource, query)

        elif representation == "json":
            return export_json(_table, query)

        elif representation == "pdf":
            return export_pdf(_table, query)

        elif representation == "rss":
            return export_rss(module, resource, query, main, extra)

        elif representation == "xls":
            return export_xls(_table, query)

        elif representation == "xml":
            return export_xml(_table, query)

        else:
            session.error = BADFORMAT
            redirect(URL(r=request))

    # Read Action *************************************************************
    else:

        authorised = shn_has_permission('read', _table, record_id)

        if authorised:
            # Audit
            shn_audit_read(operation='read', resource=resource, record=record_id, representation=representation)
            if representation == "html":
                item = crud.read(_table, record_id)
                # Check for presence of Custom View
                custom_view = '%s_display.html' % resource
                _custom_view = os.path.join(request.folder, 'views', module, custom_view)
                if os.path.exists(_custom_view):
                    response.view = module + '/' + custom_view
                else:
                    response.view = 'display.html'
                try:
                    title = s3.crud_strings.title_display
                except:
                    title = T('Details')
                if editable:
                    # TODO: Fix edit link
                    edit = A(T("Edit"), _href=URL(r=request, f=resource, args=['update', record_id]), _id='edit-btn')
                else:
                    edit = ''
                if deletable:
                    # TODO: Fix delete link
                    delete = A(T("Delete"), _href=URL(r=request, f=resource, args=['delete', record_id]), _id='delete-btn')
                else:
                    delete = ''
                try:
                    label_list_button = s3.crud_strings.label_list_button
                except:
                    label_list_button = T('List All')
                # TODO: fix List link
                list_btn = A(label_list_button, _href=URL(r=request, f=resource), _id='list-btn')
                return dict(module_name=module_name, item=item, title=title, edit=edit, delete=delete, list_btn=list_btn)

            elif representation == "plain":
                item = crud.read(_table, record_id)
                response.view = 'plain.html'
                return dict(item=item)
            elif representation == "csv":
                query = db[_table].id == record_id
                return export_csv(resource, query)
            elif representation == "json":
                query = db[_table].id == record_id
                return export_json(_table, query)
            elif representation == "pdf":
                query = db[_table].id == record_id
                return export_pdf(_table, query)
            elif representation == "rss":
                query = db[_table].id == record_id
                # TODO: check for module
                return export_rss(module, resource, query, main, extra)
            elif representation == "xls":
                query = db[_table].id == record_id
                return export_xls(_table, query)
            elif representation == "xml":
                query = db[_table].id == record_id
                return export_xml(_table, query)
            else:
                session.error = BADFORMAT
                redirect(URL(r=request))
        else:
            session.error = UNAUTHORISED
            # TODO: Fix backlink
            redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, c=module, f=resource, args=['read', record])}))

#
# shn_read --------------------------------------------------------------------
#
def shn_read(module, table, resource, record, representation, deletable, editable, main='id', extra='id'):
    authorised = shn_has_permission('read', table, record)
    if authorised:
        # Audit
        shn_audit_read(operation='read', resource=resource, record=record, representation=representation)
        if representation == "html":
            item = crud.read(table, record)
            # Check for presence of Custom View
            custom_view = '%s_display.html' % resource
            _custom_view = os.path.join(request.folder, 'views', module, custom_view)
            if os.path.exists(_custom_view):
                response.view = module + '/' + custom_view
            else:
                response.view = 'display.html'
            try:
                title = s3.crud_strings.title_display
            except:
                title = T('Details')
            if editable:
                edit = A(T("Edit"), _href=URL(r=request, f=resource, args=['update', record]), _id='edit-btn')
            else:
                edit = ''
            if deletable:
                delete = A(T("Delete"), _href=URL(r=request, f=resource, args=['delete', record]), _id='delete-btn')
            else:
                delete = ''
            try:
                label_list_button = s3.crud_strings.label_list_button
            except:
                label_list_button = T('List All')
            list_btn = A(label_list_button, _href=URL(r=request, f=resource), _id='list-btn')
            return dict(module_name=module_name, item=item, title=title, edit=edit, delete=delete, list_btn=list_btn)
        elif representation == "plain":
            item = crud.read(table, record)
            response.view = 'plain.html'
            return dict(item=item)
        elif representation == "csv":
            query = db[table].id == record
            return export_csv(resource, query)
        elif representation == "json":
            query = db[table].id == record
            return export_json(table, query)
        elif representation == "pdf":
            query = db[table].id == record
            return export_pdf(table, query)
        elif representation == "rss":
            query = db[table].id == record
            return export_rss(module, resource, query, main, extra)
        elif representation == "xls":
            query = db[table].id == record
            return export_xls(table, query)
        elif representation == "xml":
            query = db[table].id == record
            return export_xml(table, query)
        else:
            session.error = BADFORMAT
            redirect(URL(r=request))
    else:
        session.error = UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, c=module, f=resource, args=['read', record])}))

#
# shn_jr_select ---------------------------------------------------------------
#
def shn_jr_select_linkto(field):
    return URL(r=request, args=[request.args[0], request.args[1], 'read', field],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})

def shn_jr_select(module, resource, table, joinby, record, pkey, representation="html", multiple=True, next=None, jrecord=None):

    # IMPORTANT: Never redirect from here!

    # Get fields to include in the list view
    fields = jrlayer.list_fields(resource)

    _table = "%s_%s" % (module, resource)

    # Get CRUD Strings, TODO: optimize!
    try:
        title_display =  s3.crud_strings[_table].title_display
        title_list =  s3.crud_strings[_table].subtitle_list
        msg_empty = s3.crud_strings[_table].msg_list_empty
    except:
        title_display =  s3.crud_strings.title_display
        title_list =  s3.crud_strings.title_list
        msg_empty = s3.crud_strings.msg_list_empty

    output = {}

    # Query
    query = (table[joinby]==record[pkey])

    if jrecord:
        query = (table.id==jrecord) & query

    if 'deleted' in table:
        query = ((table.deleted==False) | (table.deleted==None)) & query

    if multiple and not jrecord: # multiple records of that type allowed

        subtitle = title_list

        # Pagination
        if 'page' in request.vars:
            # Pagination at server-side (since no JS available)
            page = int(request.vars.page)
            start_record = (page - 1) * ROWSPERPAGE
            end_record = start_record + ROWSPERPAGE
            limitby = start_record, end_record
            totalpages = (db(query).count() / ROWSPERPAGE) + 1 # Fails on GAE
            label_search_button = T('Search')
            search_btn = A(label_search_button, _href=URL(r=request, f=resource, args='search'), _id='search-btn')
            output.update(dict(page=page, totalpages=totalpages, search_btn=search_btn))
        else:
            # No Pagination server-side (to allow it to be done client-side)
            limitby = ''
            # Redirect to a paginated version if JS not-enabled
            request.vars['page'] = 1
            response.refresh = '<noscript><meta http-equiv="refresh" content="0; url=' + URL(r=request, args=request.args, vars=request.vars) + '" /></noscript>'

        if not fields:
            fields = [table[f] for f in table.fields if table[f].readable]

        # Column labels
        headers = {}
        for field in fields:
            # Use custom or prettified label
            headers[str(field)] = field.label

        # Audit
        shn_audit_read(operation='list', resource=resource, representation=representation)

        # Get List
        items = crud.select(
            table,
            query=query,
            fields=fields,
            limitby=limitby,
            headers=headers,
            truncate=48,
            linkto=shn_jr_select_linkto,
#            orderby=orderby,
            _id='list', _class='display')

        if not items:
            items = msg_empty

    else: # only one record of that type per entity ID

        subtitle = title_display

        try:
            target_record = db(query).select(table.id)[0]
        except:
            target_record = None

        _output = shn_read(module, table, resource, target_record.id)

        if _output:
            output.update(_output)
        return output

    output.update(items=items,subtitle=subtitle)
    return output

#
# shn_create ------------------------------------------------------------------
#
def shn_create(module, table, resource, representation, main, onvalidation, onaccept):
    # Audit
    crud.settings.create_onaccept = lambda form: shn_audit_create(form, resource, representation)
    if representation == "html":
        form = crud.create(table, onvalidation=onvalidation, onaccept=onaccept)
        #form[0].append(TR(TD(), TD(INPUT(_type="reset", _value="Reset form"))))
        # Check for presence of Custom View
        custom_view = '%s_create.html' % resource
        _custom_view = os.path.join(request.folder, 'views', module, custom_view)
        if os.path.exists(_custom_view):
            response.view = module + '/' + custom_view
        else:
            response.view = 'create.html'
        try:
            title = s3.crud_strings.title_create
        except:
            title = T('Add')
        try:
            label_list_button = s3.crud_strings.label_list_button
        except:
            label_list_button = T('List All')
        list_btn = A(label_list_button, _href=URL(r=request, f=resource), _id='list-btn')
        return dict(module_name=module_name, form=form, title=title, list_btn=list_btn)
    elif representation == "plain":
        form = crud.create(table, onvalidation=onvalidation, onaccept=onaccept)
        response.view = 'plain.html'
        return dict(item=form)
    elif representation == "popup":
        form = crud.create(table, onvalidation=onvalidation, onaccept=onaccept)
        response.view = 'popup.html'
        return dict(module_name=module_name, form=form, module=module, resource=resource, main=main, caller=request.vars.caller)
    elif representation == "json":
        return import_json(method='create')
    elif representation == "csv":
        # Read in POST
        file = request.vars.filename.file
        try:
            import_csv(file, table)
            session.flash = T('Data uploaded')
        except: 
            session.error = T('Unable to parse CSV file!')
        redirect(URL(r=request))
    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

#
# shn_jr_create ---------------------------------------------------------------
#
def shn_jr_create(module, resource, table, joinby, record, pkey, representation="html", multiple=True, next=None, jrecord=None):

    # IMPORTANT: Never redirect from here!

    # In 1:1 relations, create=update
    if not jrecord==0:
        if not multiple:
            return shn_jr_update(module, resource, table, joinby, record, pkey,
                representation=representation, multiple=multiple, next=next)

    output = {}

    if representation == "html":

        # Get CRUD Strings
        try:
            _table = "%s_%s" % (module, resource)
            formtitle = s3.crud_strings[_table].subtitle_create
        except:
            formtitle = s3.crud_strings.subtitle_create

        # Lock join field
        table[joinby].default = record[pkey]
        table[joinby].writable = False

        # Audit
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, resource, representation)

        # Get form
        # TODO: fix callbacks
        #form = crud.create(table, onvalidation=onvalidation, onaccept=onaccept)
        form = crud.create(table, next=next)

        output = dict(form=form, formtitle=formtitle)

    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

    return output

#
# shn_update ------------------------------------------------------------------
#
def shn_update(module, table, resource, record, representation, deletable, onvalidation, onaccept):
    # Audit
    crud.settings.update_onaccept = lambda form: shn_audit_update(form, resource, representation)
    crud.settings.update_deletable = deletable
    if representation == "html":
        form = crud.update(table, record, onvalidation=onvalidation, onaccept=onaccept)
        # Check for presence of Custom View
        custom_view = '%s_update.html' % resource
        _custom_view = os.path.join(request.folder, 'views', module, custom_view)
        if os.path.exists(_custom_view):
            response.view = module + '/' + custom_view
        else:
            response.view = 'update.html'
        try:
            title = s3.crud_strings.title_update
        except:
            title = T('Edit')
        if s3.crud_strings and s3.crud_strings.label_list_button:
            list_btn = A(s3.crud_strings.label_list_button, _href=URL(r=request, f=resource), _id='list-btn')
            return dict(module_name=module_name, form=form, title=title, list_btn=list_btn)
        else:
            return dict(module_name=module_name, form=form, title=title)
    elif representation == "plain":
        form = crud.update(table, record, onvalidation=onvalidation, onaccept=onaccept)
        response.view = 'plain.html'
        return dict(item=form)
    elif representation == "json":
        return import_json(method='update')
    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

#
# shn_jr_update ---------------------------------------------------------------
#
def shn_jr_update(module, resource, table, joinby, record, pkey, representation="html", multiple=True, next=None, jrecord=None):

    # IMPORTANT: Never redirect from here!

    # In 1:N relations and without target ID: update=create
    if multiple and not jrecord:
        return shn_jr_create(module, resource, table, joinby, record, pkey,
            representation=representation, multiple=multiple, next=next)

    # Query for target record
    query = (table[joinby]==record[pkey])

    if multiple:
        query = (table.id==jrecord) & query

    if 'deleted' in table:
        query = ((table.deleted==False) | (table.deleted==None)) & query

    # Get target record, or create one
    try:
        target_record = db(query).select(table.ALL)[0]
    except:
        return shn_jr_create(module, resource, table, joinby, record, pkey,
            representation=representation, multiple=multiple, next=next, jrecord=0)

    output = {}

    # Audit
    crud.settings.update_onaccept = lambda form: shn_audit_update(form, resource, representation)

    # TODO: is this correct?
    if shn_has_permission('delete', table):
        crud.settings.update_deletable = True

    if representation == "html":

        # Get CRUD strings
        _table = "%s_%s" % (module, resource)
        try:
            formtitle = s3.crud_strings[_table].title_update
        except:
            formtitle = s3.crud_strings.title_update

        # TODO: fix callbacks
        #form = crud.update(table, record, onvalidation=onvalidation, onaccept=onaccept)

        # Lock join field
        table[joinby].default = target_record[joinby]
        table[joinby].writable = False

        form = crud.update(table, target_record.id, next=next)
        output = dict(form=form, formtitle=formtitle)

    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

    return output

#
# shn_delete ------------------------------------------------------------------
#
def shn_delete(table, resource, record, representation):
    # Audit
    shn_audit_delete(resource, record, representation)
    if "deleted" in db[table] and db(db.s3_setting.id==1).select()[0].archive_not_delete:
        # Mark as deleted rather than really deleting
        db(db[table].id == record).update(deleted = True)
        # Nevertheless: call crud.delete_onvalidation if set
        if crud.settings.delete_onvalidation:
            crud.settings.delete_onvalidation(db(db[table].id == record).select()[0])
        session.confirmation = s3.crud_strings.msg_record_deleted
        redirect(URL(r=request))
    else:
        # Delete properly
        if representation == "ajax":
            crud.settings.delete_next = URL(r=request, c=module, f=resource, vars={'format':'ajax'})
        crud.delete(table, record)

#
# shn_jr_delete ---------------------------------------------------------------
#
def shn_jr_delete(resource, table, joinby, record, pkey, representation, jrecord=None):
    """
        Deletes matching records in the joined resource.

        resource:           the name of the joined resource
        table:              the table of the joined resource
        joinby:             name of the join key
        record:             record of the primary resource to join to
        representation:     data format
        jrecord:            target record ID or list of ID's to delete
    """

    # IMPORTANT: Never redirect from here!

    output = {}

    # Query
    query = (table[joinby]==record[pkey])

    # One or all records?
    if jrecord:
        query = (table.id==jrecord) & query

    # TODO:
    # Attempt to even delete previously archived records, if archive_not_delete is not set?
    if 'deleted' in table:
        query = ((table.deleted==False) | (table.deleted==None)) & query

    # Get target records
    rows = db(query).select(table.ALL)

    # Nothing to do? Return here!
    if not rows or len(rows)==0:
        session.confirmation = T('No records to delete')
        return output

    # Save callback settings
    delete_onvalidation = crud.settings.delete_onvalidation
    delete_onaccept = crud.settings.delete_onaccept

    # Set resource specific callbacks, if any
    crud.settings.delete_onvalidation = jrlayer.delete_onvalidation(resource)
    crud.settings.delete_onaccept = jrlayer.delete_onaccept(resource)

    # Delete all accessible records
    numrows = 0
    for row in rows:
        if shn_has_permission('delete', table, row.id):
            numrows += 1
            shn_audit_delete(resource, row.id, representation)
            if "deleted" in db[table] and db(db.s3_setting.id==1).select()[0].archive_not_delete:
                if crud.settings.delete_onvalidation:
                    crud.settings.delete_onvalidation(row)
                db(db[table].id == row.id).update(deleted = True)
                if crud.settings.delete_onaccept:
                    crud.settings.delete_onaccept(row)
            else:
                crud.delete(table, row.id)
        else:
            continue

    # Restore callback settings
    crud.settings.delete_onvalidation = delete_onvalidation
    crud.settings.delete_onaccept = delete_onaccept

    # Confirm and return
    session.confirmation = "%s %s" % ( numrows, T('records deleted'))
    return output

# *****************************************************************************
# Main controller function

#
# shn_rest_controller ---------------------------------------------------------
#
def shn_rest_controller(module, resource,
    deletable=True,
    editable=True,
    listadd=True,
    main='name',
    extra=None,
    orderby=None,
    sortby=None,
    pheader=None,
    onvalidation=None,
    onaccept=None):
    """
        Extension to the standard REST controller to add capability
        to handle joined resources.
    """

    # Get representation ------------------------------------------------------

    #if request.vars.format:
    #    representation = str.lower(request.vars.format)
    #else:
    #    representation = "html"

    # Identify action ---------------------------------------------------------

    _request = JRequest(jrlayer, request)

    # Invalid request?
    if _request.invalid:
        session.error = BADMETHOD
        redirect(URL(r=request, c=module, f='index'))

    # Get method
    method = _request.method
    representation = _request.representation

    # Get joined resource parameters
    jmodule = _request.jmodule
    jresource = _request.jresource
    jrecord_id = _request.jrecord_id
    multiple = _request.multiple

    # Identify main resource record -------------------------------------------

    # Get primary table
    tablename = "%s_%s" % (module,resource)
    table = db[tablename]

    # Check read permission on primary table
    if not shn_has_permission('read', table):
        session.error = UNAUTHORIZED
        redirect(URL(r=request, c='default', f='user', args='login',
            vars={'_next':URL(r=request, c=module, f=resource, args=request.args)}))

    # Try to identify record
    record_id = shn_jr_identify_precord(module, resource, _request.record_id, jresource)

    # Returns 0 if the specified record doesn't exist (anymore)
    if record_id==0:
        session.error = BADRECORD
        redirect(URL(r=request, c=module, f='index'))

    # Record ID is required in joined-table operations and read action:
    if not record_id and (jresource or method=="read"):

        # TODO: Cleanup - this is PR specific
        if module=="pr" and resource=="person" and representation=='html':
            if jresource:
                _args = ['[id]', jresource]
                if method:
                    _args.append(method)
            else:
                _args = [method, '[id]']
            same = URL(r=request, c=module, f=resource, args=_args)
            redirect(URL(r=request, c='pr', f='person', args='search_simple', vars={"_next":same}))

        else:
            session.error = BADRECORD
            redirect(URL(r=request, c=module, f='index'))

    # Append record ID to request as necessary
    if record_id:
        if len(request.args)>0 or len(request.args)==0 and ('id_label' in request.vars):
            if jresource and not request.args[0].isdigit():
                request.args.insert(0, str(record_id))
            elif not jresource and not (str(record_id) in request.args):
                request.args.append(str(record_id))

    # Identify join field -----------------------------------------------------

    if jresource:

        # Get joined table
        jtablename = "%s_%s" % (jmodule, jresource)
        jtable = db[jtablename]

        # Get join key
        join_keys = jrlayer.get_join_key(jresource, module, resource)
        if not join_keys:
            session.error = BADMETHOD
            redirect(URL(r=request, c=module, f='index'))
        else:
            pkey, joinby = join_keys

    else:
        pkey = None
        joinby = None

    # Arrange action ----------------------------------------------------------

    # Get custom action (if any)
    custom_action = jrlayer.get_method(module, resource, jmodule, jresource, method)

    # *************************************************************************
    # Joined Table Operation
    #
    if jresource:

        output = {}

        # Get page title from CRUD strings
        try:
            page_title = s3.crud_strings[tablename].title_display
        except:
            page_title = s3.crud_strings.title_display

        output.update(title=page_title)

        # Backlinks TODO: make this nicer!
        if method:
            if jrecord_id:
                here = URL(r=request, f=resource, args=[record_id, jresource, method, jrecord_id])
            else:
                here = URL(r=request, f=resource, args=[record_id, jresource, method])
        else:
            here = URL(r=request, f=resource, args=[record_id, jresource])

        there = URL(r=request, f=resource, args=[record_id, jresource])
        same = URL(r=request, f=resource, args=['[id]', jresource])

        # Get pageheader (if any)
        shn_audit_read(operation='read', resource=resource, record=record_id, representation=representation)

        if pheader:
            try:
                _pheader = pheader(resource, record_id, representation, next=there, same=same)
            except:
                _pheader = pheader

        if _pheader:
            output.update(pheader=_pheader)

        # List-All button?
        try:
            label_list_button = s3.crud_strings[jtablename].label_list_button
        except:
            label_list_button = s3.crud_strings.label_list_button

        list_btn = A(label_list_button, _href=there, _id='list-btn')
        output.update(list_btn=list_btn)

        # Get primary record
        query = (table.id==record_id)

        if request.filter:
            query = request.filter & query

        if 'deleted' in table:
            query = ((table.deleted==False) | (table.deleted==None)) & query
        try:
            record = db(query).select()[0]
        except:
            session.error = BADRECORD
            redirect(URL(r=request, c=module, f='index'))

        # TODO: select proper default or custom view
        response.view = 'pr/person.html'

        if method and custom_action:
            try:
                return(custom_action(module, resource, record_id, method,
                    jmodule=jmodule,
                    jresource=jresource,
                    jrecord_id=jrecord_id,
                    joinby=joinby,
                    multiple=multiple,
                    representation=representation,
                    onvalidation=None,
                    onaccept=None))
            except:
                raise HTTP(501)

        if method==None and request.env.request_method=='PUT':
            # Not implemented
            raise HTTP(501)

        elif method==None and request.env.request_method=='DELETE':
            # Not implemented
            raise HTTP(501)

        elif (method==None and request.env.request_method=='GET') or \
            (method==None and request.env.request_method=='POST') or \
            method=="list" or method=="read" or method=="display":

            if shn_has_permission('read', jtable):
                _output=shn_select(_request, table, record=record, jtable=jtable, pkey=pkey, fkey=joinby, listadd=True)

                if _output:
                    output.update(_output)

                # TODO: fix view
                response.view = 'pr/person.html'
                return output

            else:
                session.error = UNAUTHORIZED
                redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': here }))

        elif method=="create":
            authorized = shn_has_permission(method, jtable)
            if authorized:
                _output = shn_jr_create(jmodule, jresource, jtable, joinby, record, pkey,
                                representation=representation, multiple=multiple, next=there)
                if _output:
                    output.update(_output)
                return output
            else:
                session.error = UNAUTHORIZED
                redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': here}))

        elif method=="update":
            authorized = shn_has_permission(method, jtable)
            if authorized:
                _output = shn_jr_update(jmodule, jresource, jtable, joinby, record, pkey,
                                representation=representation, multiple=multiple, next=there, jrecord=jrecord_id)
                if _output:
                    output.update(_output)
                return output
            else:
                session.error = UNAUTHORIZED
                redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': here}))

        elif method=="delete":
            authorized = shn_has_permission(method, jtable)
            if authorized:
                shn_jr_delete(jresource, jtable, joinby, record, pkey, representation, jrecord=jrecord_id)
                redirect(there)
            else:
                session.error = UNAUTHORIZED
                redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': here}))

        else:
            session.error = BADMETHOD
            redirect(URL(r=request, c=module, f='index'))

    # *************************************************************************
    # Single Table Operation
    #
    else:

        # from shn_rest_controller:
        # Look up CRUD strings for a given resource based on the definitions in models/module.py
        if resource == 'setting':
            s3.crud_strings = getattr(s3.crud_strings, resource)
        else:
            s3.crud_strings = getattr(s3.crud_strings, str(table))

        try:
            crud.messages.record_created = s3.crud_strings.msg_record_created
            crud.messages.record_updated = s3.crud_strings.msg_record_modified
            crud.messages.record_deleted = s3.crud_strings.msg_record_deleted
        except:
            pass

        # Custom Method *******************************************************
        if method and custom_action:
            try:
                return(custom_action(module, resource, record_id, method,
                    jmodule=None,
                    jresource=None,
                    jrecord_id=None,
                    joinby=None,
                    multiple=True,
                    representation=representation,
                    onvalidation=onvalidation,
                    onaccept=onaccept))
            except:
                raise HTTP(501)

        # Clear Session *******************************************************
        elif method=="clear":

            # Clear session
            shn_jr_clear_session('%s_%s' % (module, resource))

            if '_next' in request.vars:
                request_vars = dict(_next=request.vars._next)
            else:
                request_vars = {}

            # Redirect to search
            # TODO: build a generic search function, this here is PR specific
            if module=="pr" and resource=="person" and representation=="html":
                redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request_vars))
            else:
                redirect(URL(r=request, c='pr', f=resource))

        # HTTP Multi-Record Operation *****************************************
        elif not method and not record_id:

            # HTTP List or List-Add -------------------------------------------
            if request.env.request_method == 'GET' or request.env.request_method == 'POST':

                return shn_select(_request, table,
                    main=main,
                    extra=extra,
                    listadd=listadd,
                    deletable=deletable,
                    editable=editable,
                    orderby=orderby,
                    sortby=sortby,
                    onvalidation=onvalidation,
                    onaccept=onaccept)

            # HTTP Create -----------------------------------------------------
            elif request.env.request_method == 'PUT':
                # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6
                # We don't yet implement PUT for create/update, although Web2Py does now support it
                # resource doesn't exist: Create using next available ID
                # Not implemented
                raise HTTP(501)

            # Unsupported HTTP method -----------------------------------------
            else:
                # Unsupported HTTP method for this context:
                # DELETE, HEAD, OPTIONS, TRACE, CONNECT
                # Not implemented
                raise HTTP(501)

        # HTTP Single Record Operation ****************************************
        elif record_id and not method:

            # HTTP Read (single record) ---------------------------------------
            if request.env.request_method == 'GET':

                return shn_select(_request, table,
                    main=main,
                    extra=extra,
                    listadd=listadd,
                    deletable=deletable,
                    editable=editable,
                    orderby=orderby,
                    sortby=sortby,
                    onvalidation=onvalidation,
                    onaccept=onaccept)

                #return shn_read(module, table, resource, record_id, representation, deletable, editable)

            # HTTP Delete (single record) -------------------------------------
            elif request.env.request_method == 'DELETE':
                # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.7
                if db(db[table].id == record_id).select():
                    authorised = shn_has_permission('delete', table, record_id)
                    if authorised:
                        shn_delete(table, resource, record_id, representation)
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
            elif request.env.request_method == 'PUT':
                # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6
                # We don't yet implement PUT for create/update, although Web2Py does now support it

                # HTTP Update (single record) ---------------------------------
                if db(db[table].id == record_id).select():
                    # resource exists: Update
                    # Not implemented
                    raise HTTP(501)
                    authorised = shn_has_permission('update', table, record_id)
                    if authorised:
                        #return shn_update(module, table, resource, record_id, representation, deletable, onvalidation, onaccept)
                        # need to parse entity: http://www.w3.org/Protocols/rfc2616/rfc2616-sec7.html#sec7
                        pass
                    else:
                        # Unauthorised
                        raise HTTP(401)

                # HTTP Create (single record) ---------------------------------
                else:
                    # resource doesn't exist: Create at this ID
                    # Not implemented
                    raise HTTP(501)
                    authorised = shn_has_permission('create', table)
                    if authorised:
                        #return shn_create(module, table, resource, representation, main, onvalidation, onaccept)
                        # need to parse entity: http://www.w3.org/Protocols/rfc2616/rfc2616-sec7.html#sec7
                        pass
                    else:
                        # Unauthorised
                        raise HTTP(401)

            # Unsupported HTTP method -----------------------------------------
            else:
                # Unsupported HTTP method for this context:
                # POST, HEAD, OPTIONS, TRACE, CONNECT
                # Not implemented
                raise HTTP(501)

        # Create (single table) ***********************************************
        elif method == "create":
            authorised = shn_has_permission(method, table)
            if authorised:
                return shn_create(module, table, resource, representation, main, onvalidation, onaccept)
            else:
                session.error = UNAUTHORISED
                redirect(URL(r=request, c='default', f='user', args='login',
                    vars={'_next':URL(r=request, c=module, f=resource, args='create')}))

        # Read (single table) *************************************************
        elif method == "read" or method == "display":
            redirect(URL(r=request, args=record_id))

        # Update (single table) ***********************************************
        elif method == "update":
            authorised = shn_has_permission(method, table, record_id)
            if authorised:
                return shn_update(module, table, resource, record_id, representation, deletable, onvalidation, onaccept)
            else:
                session.error = UNAUTHORISED
                redirect(URL(r=request, c='default', f='user', args='login',
                    vars={'_next':URL(r=request, c=module, f=resource, args=['update', record_id])}))

        # Delete (single table) ***********************************************
        elif method == "delete":
            authorised = shn_has_permission(method, table, record_id)
            if authorised:
                return shn_delete(table, resource, record_id, representation)
            else:
                session.error = UNAUTHORISED
                redirect(URL(r=request, c='default', f='user', args='login',
                    vars={'_next':URL(r=request, c=module, f=resource, args=['delete', record_id])}))

        # Search (single table) ***********************************************
        elif method == "search":
            authorised = shn_has_permission('read', table)
            if authorised:
                # Filter Search list to just those records which user can read
                #query = shn_accessible_query('read', table)
                # Fails on t2's line 739: AttributeError: 'SQLQuery' object has no attribute 'get'

                # Audit
                shn_audit_read(operation='search', resource=resource, representation=representation)

                if representation == "html":

                    shn_represent(table, module, resource, deletable, main, extra)
                    #search = t2.search(table, query)
                    search = t2.search(table)

                    # Check for presence of Custom View
                    custom_view = '%s_search.html' % resource
                    _custom_view = os.path.join(request.folder, 'views', module, custom_view)
                    if os.path.exists(_custom_view):
                        response.view = module + '/' + custom_view
                    else:
                        response.view = 'search.html'

                    # CRUD Strings
                    title = s3.crud_strings.title_search

                    return dict(module_name=module_name, search=search, title=title)

                if representation == "json":
                    # JQuery Autocomplete uses 'q' instead of 'value'
                    value = request.vars.value or request.vars.q or None
                    if request.vars.field and request.vars.filter and value:
                        field = str.lower(request.vars.field)
                        filter = request.vars.filter
                        if filter == '=':
                            query = (table[field]==value)
                            item = db(query).select().json()
                        elif filter == '~':
                            query = (table[field].like('%' + value + '%'))
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
                redirect(URL(r=request, c='default', f='user', args='login',
                    vars={'_next':URL(r=request, c=module, f=resource, args=['search'])}))

        # Unsupported Method **************************************************
        else:
            session.error = BADMETHOD
            redirect(URL(r=request))

# END
# *****************************************************************************
