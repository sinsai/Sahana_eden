#
# RESTlike CRUD Controller
#

# Data conversions
def import_csv(table, file):
    "Import CSV file into Database. Comes from appadmin.py. Modified to do Validation on UUIDs"
    table.import_from_csv_file(file)

def import_json(table, file):
    "Import JSON into Database."
    import gluon.contrib.simplejson as sj
    reader = sj.loads(file)
    # ToDo
    # Get column names (like for SQLTable.import_from_csv_file() )
    # Insert records (or Update if unique field duplicated)
    #table.insert(**dict(items))
    return

# Authorisation    
def has_permission(name, table_name, record_id = 0):
    """
    S3 framework function to define whether a user can access a record
    Designed to be called from the RESTlike controller
    """
    security = db().select(db.s3_setting.security_policy)[0].security_policy
    if security == 'simple':
        # Anonymous users can Read.
        if name == 'read':
            authorised = True
        else:
            # Authentication required for Create/Update/Delete.
            authorised = auth.is_logged_in()
    else:
        # Administrators are always authorised
        if auth.has_membership(1):
            authorised = True
        else:
            # Require records in auth_permission to specify access
            authorised = auth.has_permission(name, table_name, record_id)
    return authorised

def accessible_query(name, table):
    """
    Returns a query with all accessible records for the current logged in user
    This method does not work on GAE because uses JOIN and IN
    """
    # If using the 'simple' security policy then show all records
    security = db().select(db.s3_setting.security_policy)[0].security_policy
    if security == 'simple':
        return table.id > 0
    # Administrators can see all data
    if auth.has_membership(1):
        return table.id > 0
    # If there is access to the entire table then show all records
    user_id = auth.user.id
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

# Audit
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

    
# Display Representations
# t2.itemize now deprecated
# but still used for t2.search
def shn_represent(table, module, resource, deletable=True, main='name', extra=None):
    "Designed to be called via table.represent to make t2.search() output useful"
    db[table].represent = lambda table:shn_list_item(table, resource, action='display', main=main, extra=shn_represent_extra(table, module, resource, deletable, extra))
    return

def shn_represent_extra(table, module, resource, deletable=True, extra=None):
    "Display more than one extra field (separated by spaces)"
    authorised = has_permission('delete', table)
    item_list = []
    if extra:
        extra_list = extra.split()
        for any_item in extra_list:
            item_list.append("TD(db(db.%s_%s.id==%i).select()[0].%s)" % (module, resource, table.id, any_item))
    if authorised and deletable:
        item_list.append("TD(INPUT(_type='checkbox', _class='delete_row', _name='%s', _id='%i'))" % (resource, table.id))
    return ','.join( item_list )

def shn_list_item(table, resource, action, main='name', extra=None):
    "Display nice names with clickable links & optional extra info"
    item_list = [TD(A(table[main], _href=URL(r=request, f=resource, args=[action, table.id])))]
    if extra:
        item_list.extend(eval(extra))
    items = DIV(TABLE(TR(item_list)))
    return DIV(*items)

# Main controller function
def shn_rest_controller(module, resource, deletable=True, listadd=True, main='name', onvalidation=None):
    """
    RESTlike controller function.
    
    Provides CRUD operations for the given module/resource.
    Optional parameters:
    deletable=False: don't provide visible options for deletion
    listadd=False: don't provide an add form in the list view
    
    Customisable Security Policy

    Auditing options for Read &/or Write.
    
    Supported Representations:
        HTML is the default (including full Layout)
        PLAIN is HTML with no layout
         - can be inserted into DIVs via AJAX calls
         - can be useful for clients on low-bandwidth or small screen sizes
        JSON (designed to be accessed via JavaScript)
         - responses in JSON format
         - create/update/delete done via simple GET vars (no form displayed)
        CSV (useful for synchronization)
         - List/Display/Create for now
        RSS (list only)
        XML (list/read only)
        AJAX (designed to be run asynchronously to refresh page elements)
        POPUP
    ToDo:
        Alternate Representations
            CSV update
            SMS,PDF,LDIF
    """
    
    _table = '%s_%s' % (module, resource)
    table = db[_table]
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

    # Which representation should output be in?
    if request.vars.format:
        representation = str.lower(request.vars.format)
    else:
        # Default to HTML
        representation = "html"
    
    if len(request.args) == 0:
        # No arguments => default to List
        authorised = has_permission('read', table)
        if authorised:
            # Filter Search list to just those records which user can read
            query = accessible_query('read', table)
            # list_create if have permissions
            authorised = has_permission('create', table)
            # Audit
            shn_audit_read(operation='list', resource=resource, representation=representation)
            if representation == "html":
                fields = [table[f] for f in table.fields if table[f].readable]
                headers = {}
                for field in fields:
                   # Use custom or prettified label
                   headers[str(field)] = field.label
                items=crud.select(table, query=query, fields=fields, headers=headers)
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
                if authorised and listadd:
                    # Audit
                    crud.settings.create_onaccept = lambda form: shn_audit_create(form, resource, representation)
                    # Display the Add form below List
                    form = crud.create(table, onvalidation=onvalidation)
                    # Check for presence of Custom View
                    custom_view = '%s_list_create.html' % resource
                    _custom_view = os.path.join(request.folder, 'views', module, custom_view)
                    if os.path.exists(_custom_view):
                        response.view = module + '/' + custom_view
                    else:
                        response.view = 'list_create.html'
                    try:
                        addtitle = s3.crud_strings.subtitle_create
                    except:
                        addtitle = T('Add New')
                    return dict(module_name=module_name, items=items, form=form, title=title, subtitle=subtitle, addtitle=addtitle)
                else:
                    # List only
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
                    return dict(module_name=module_name, items=items, title=title, subtitle=subtitle, add_btn=add_btn)
            elif representation == "ajax":
                #shn_represent(table, module, resource, deletable, main, extra)
                #items = t2.itemize(table, query)
                fields = [table[f] for f in table.fields if table[f].readable]
                headers = {}
                for field in fields:
                   # Use custom or prettified label
                   headers[str(field)] = field.label
                items=crud.select(table, query=query, fields=fields, headers=headers)
                if not items:
                    try:
                        items = s3.crud_strings.msg_list_empty
                    except:
                        items = T('None')
                response.view = 'plain.html'
                return dict(item=items)
            elif representation == "plain":
                items = crud.select(table, query)
                response.view = 'plain.html'
                return dict(item=items)
            elif representation == "json":
                items = db(query).select(table.ALL).json()
                response.headers['Content-Type'] = 'text/x-json'
                return items
            elif representation == "xml":
                items = db(query).select(table.ALL).as_list()
                response.headers['Content-Type'] = 'text/xml'
                return str(service.xml_serializer(items))
            elif representation == "csv":
                import gluon.contenttype
                response.headers['Content-Type'] = gluon.contenttype.contenttype('.csv')
                #query=db[table].id>0
                response.headers['Content-disposition'] = "attachment; filename=%s_%s_list.csv" % (request.env.server_name, resource)
                return str(db(query).select())
            elif representation == "rss":
                if request.env.remote_addr == '127.0.0.1':
                    server = 'http://127.0.0.1:' + request.env.server_port
                else:
                    server = 'http://' + request.env.server_name + ':' + request.env.server_port
                link = '/%s/%s/%s' % (request.application, module, resource)
                entries = []
                rows = db(query).select()
                for row in rows:
                    entries.append(dict(title=row.name, link=server+link+'/%d' % row.id, description=row.description or '', created_on=row.created_on))
                import gluon.contrib.rss2 as rss2
                items = [ rss2.RSSItem(title = entry['title'], link = entry['link'], description = entry['description'], pubDate = entry['created_on']) for entry in entries]
                rss = rss2.RSS2(title = str(s3.crud_strings.subtitle_list), link = server+link+'/%d' % row.id, description = '', lastBuildDate = request.now, items = items)
                response.headers['Content-Type'] = 'application/rss+xml'
                return rss2.dumps(rss)
            else:
                session.error = T("Unsupported format!")
                redirect(URL(r=request))
        else:
            session.error = T("Not authorised!")
            redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, c=module, f=resource)}))
    else:
        if request.args[0].isdigit():
            # 1st argument is ID not method => Read.
            record = request.args[0]
            authorised = has_permission('read', table, record)
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
                    edit = A(T("Edit"), _href=URL(r=request, f=resource, args=['update', record]), _id='edit-btn')
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
                elif representation == "json":
                    item = db(table.id==record).select(table.ALL).json()
                    response.view = 'plain.html'
                    return dict(item=item)
                elif representation == "xml":
                    item = db(table.id==record).select(table.ALL).as_list()
                    response.headers['Content-Type'] = 'text/xml'
                    return str(service.xml_serializer(item))
                elif representation == "csv":
                    import gluon.contenttype
                    response.headers['Content-Type'] = gluon.contenttype.contenttype('.csv')
                    query = db[table].id == record
                    response.headers['Content-disposition'] = "attachment; filename=%s_%s_%d.csv" % (request.env.server_name, resource, record)
                    return str(db(query).select())
                elif representation == "rss":
                    #if request.args and request.args[0] in settings.rss_procedures:
                    #   feed = eval('%s(*request.args[1:],**dict(request.vars))' % request.args[0])
                    #else:
                    #   t2._error()
                    #import gluon.contrib.rss2 as rss2
                    #rss = rss2.RSS2(
                    #   title = feed['title'],
                    #   link = feed['link'],
                    #   description = feed['description'],
                    #   lastBuildDate = feed['created_on'],
                    #   items = [
                    #      rss2.RSSItem(
                    #        title = entry['title'],
                    #        link = entry['link'],
                    #        description = entry['description'],
                    #        pubDate = entry['created_on']) for entry in feed['entries']]
                    #   )
                    #response.headers['Content-Type'] = 'application/rss+xml'
                    #return rss2.dumps(rss)
                    entries[0] = dict(title=table.name, link=URL(r=request, c='module', f='resource', args=[table.id]), description=table.description, created_on=table.created_on)
                    item = service.rss(entries=entries)
                    response.view = 'plain.html'
                    return dict(item=item)
                else:
                    session.error = T("Unsupported format!")
                    redirect(URL(r=request))
            else:
                session.error = T("Not authorised!")
                redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, c=module, f=resource, args=['read', record])}))
        else:
            method = str.lower(request.args[0])
            try:
                record = request.args[1]
            except:
                pass
            if method == "create":
                authorised = has_permission(method, table)
                if authorised:
                    # Audit
                    crud.settings.create_onaccept = lambda form: shn_audit_create(form, resource, representation)
                    if representation == "html":
                        form = crud.create(table, onvalidation=onvalidation)
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
                        form = crud.create(table, onvalidation=onvalidation)
                        response.view = 'plain.html'
                        return dict(item=form)
                    elif representation == "popup":
                        form = crud.create(table, onvalidation=onvalidation)
                        response.view = 'popup.html'
                        return dict(module_name=module_name, form=form, module=module, resource=resource, main=main, caller=request.vars.caller)
                    elif representation == "json":
                        record = Storage()
                        for var in request.vars:
                            if var == 'format':
                                pass
                            else:
                                record[var] = request.vars[var]
                        item = ''
                        for var in record:
                            # Validate request manually
                            if table[var].requires(record[var])[1]:
                                item += '{"Status":"failed","Error":{"StatusCode":403,"Message":"' + var + ' invalid: ' + table[var].requires(record[var])[1] + '"}}'
                        if item:
                            pass
                        else:
                            try:
                                id = table.insert(**dict (record))
                                item = '{"Status":"success","Error":{"StatusCode":201,"Message":"Created as ' + URL(r=request, c=module, f=resource, args=id) + '"}}'
                            except:
                                item = '{"Status":"failed","Error":{"StatusCode":400,"Message":"Invalid request!"}}'
                        response.view = 'plain.html'
                        return dict(item=item)
                    elif representation == "csv":
                        # Read in POST
                        file = request.vars.filename.file
                        try:
                            import_csv(table, file)
                            session.flash = T('Data uploaded')
                        except: 
                            session.error = T('Unable to parse CSV file!')
                        redirect(URL(r=request))
                    else:
                        session.error = T("Unsupported format!")
                        redirect(URL(r=request))
                else:
                    session.error = T("Not authorised!")
                    redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, c=module, f=resource, args='create')}))
            elif method == "display" or method == "read":
                redirect(URL(r=request, args=record))
            elif method == "update":
                authorised = has_permission(method, table, record)
                if authorised:
                    # Audit
                    crud.settings.update_onaccept = lambda form: shn_audit_update(form, resource, representation)
                    crud.settings.update_deletable = deletable
                    if representation == "html":
                        form = crud.update(table, record, onvalidation=onvalidation)
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
                        if s3.crud_strings.label_list_button:
                            list_btn = A(s3.crud_strings.label_list_button, _href=URL(r=request, f=resource),_id='list-btn')
                            return dict(module_name=module_name, form=form, title=title, list_btn=list_btn)
                        else:
                            return dict(module_name=module_name, form=form, title=title)
                    elif representation == "plain":
                        form = crud.update(table, record, onvalidation=onvalidation)
                        response.view = 'plain.html'
                        return dict(item=form)
                    elif representation == "json":
                        record = Storage()
                        uuid = 0
                        for var in request.vars:
                            if var == 'format':
                                pass
                            elif var == 'uuid':
                                uuid = 1
                            else:
                                record[var] = request.vars[var]
                        if uuid:
                            item = ''
                            for var in record:
                                # Validate request manually
                                if table[var].requires(record[var])[1]:
                                    item += '{"Status":"failed","Error":{"StatusCode":403,"Message":"' + var + ' invalid: ' + table[var].requires(record[var])[1] + '"}}'
                            if item:
                                pass
                            else:
                                try:
                                    result = db(table.uuid==request.vars.uuid).update(**dict (record))
                                    if result:
                                        item = '{"Status":"success","Error":{"StatusCode":200,"Message":"Record updated."}}'
                                    else:
                                        item = '{"Status":"failed","Error":{"StatusCode":404,"Message":"Record ' + request.vars.uuid + ' does not exist."}}'
                                except:
                                    item = '{"Status":"failed","Error":{"StatusCode":400,"Message":"Invalid request!"}}'
                        else:
                            item = '{"Status":"failed","Error":{"StatusCode":400,"Message":"UUID required!"}}'
                        response.view = 'plain.html'
                        return dict(item=item)
                    else:
                        session.error = T("Unsupported format!")
                        redirect(URL(r=request))
                else:
                    session.error = T("Not authorised!")
                    redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, c=module, f=resource, args=['update', record])}))
            elif method == "delete":
                authorised = has_permission(method, table, record)
                if authorised:
                    # Audit
                    shn_audit_delete(resource, record, representation)
                    if representation == "ajax":
                        #crud.delete(table, record, next='%s?format=ajax' % resource)
                        t2.delete(table, next='%s?format=ajax' % resource)
                    else:
                        crud.delete(table, record)
                else:
                    session.error = T("Not authorised!")
                    redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, c=module, f=resource, args=['delete', record])}))
            elif method == "search":
                authorised = has_permission('read', table)
                if authorised:
                    # Filter Search list to just those records which user can read
                    #query = accessible_query('read', table)
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
                        title = s3.crud_strings.title_search
                        return dict(module_name=module_name, search=search, title=title)
                    if representation == "json":
                        if request.vars.field and request.vars.filter and request.vars.value:
                            field = str.lower(request.vars.field)
                            filter = str.lower(request.vars.filter)
                            if filter == '=':
                                query = (table['%s' % field]==request.vars.value)
                                item = db(query).select().json()
                            else:
                                item = '{"Status":"failed","Error":{"StatusCode":501,"Message":"Unsupported filter! Supported filters: ="}}'
                        else:
                            item = '{"Status":"failed","Error":{"StatusCode":501,"Message":"Search requires specifying Field, Filter & Value!"}}'
                        response.view = 'plain.html'
                        return dict(item=item)
                    else:
                        session.error = T("Unsupported format!")
                        redirect(URL(r=request))
                else:
                    session.error = T("Unsupported method!")
                    redirect(URL(r=request))
            else:
                session.error = T("Not authorised!")
                redirect(URL(r=request, c='default', f='user', args='login' ,vars={'_next':URL(r=request, c=module, f=resource, args=['search'])}))
