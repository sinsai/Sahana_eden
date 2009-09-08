# -*- coding: utf-8 -*-

#
# Sahanapy Joined Resources RESTlike controller
#
# created 2009-09-06 by nursix
#

# *****************************************************************************
# Joint Resource Layer
jrlayer = JRLayer(db)

# *****************************************************************************
# Error messages
#   - make these constants to ensure consistency
UNAUTHORISED = T('Not authorised!')
BADFORMAT = T('Unsupported format!')
BADMETHOD = T('Unsupported method!')
BADRECORD = T('No such record!')

# *****************************************************************************
# Helper functions

#
# shn_jr_identify_precord -----------------------------------------------------
#
def shn_jr_identify_precord(module, resource, _id, jresource):
    """
        Helper function for shn_jr_rest_controller:
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

    if not record_id: # TODO: make this more generic! (e.g. replace pr_pe_label by id_label)
        if 'id_label' in request.vars:
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

    if not record_id:
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

        try:
            shn_audit_read(operation='read', resource=resource, record=target_record.id, representation=representation)
            items = crud.read(table, target_record.id)
        except:
            items = msg_empty

    output.update(items=items,subtitle=subtitle)
    return output

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
# shn_jr_rest_controller ------------------------------------------------------
#
def shn_jr_rest_controller(module, resource,
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

    if request.vars.format:
        representation = str.lower(request.vars.format)
    else:
        representation = "html"

    # Identify action ---------------------------------------------------------

    _request = jrlayer.parse_request(request)

    # Invalid request?
    if not _request:
        session.error = BADMETHOD
        redirect(URL(r=request, c=module, f='index'))

    # Get method
    method = _request['method']

    # Get joined resource parameters
    jmodule = _request['jmodule']
    jresource = _request['jresource']
    jrecord_id = _request['jrecord_id']
    multiple = _request['multiple']

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
    record_id = shn_jr_identify_precord(module, resource, _request['record_id'], jresource)

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
                if multiple and not jrecord_id:
                    if 'list_btn' in output: # this is already a list action, so forget about list_btn
                        del output['list_btn']
                    if representation=="html" and shn_has_permission('create', jtable):
                        _output = shn_jr_create(jmodule, jresource, jtable, joinby, record, pkey,
                            representation=representation, multiple=multiple, next=there)
                        if _output:
                            output.update(_output)
                    _output = shn_jr_select(jmodule, jresource, jtable, joinby, record, pkey,
                            representation=representation, multiple=multiple, next=here)
                    if _output:
                        output.update(_output)
                else:
                    if representation=="html" and shn_has_permission('update', jtable):
                        _output = shn_jr_update(jmodule, jresource, jtable, joinby, record, pkey,
                            representation=representation, multiple=multiple, next=there, jrecord=jrecord_id)
                    else:
                        _output = shn_jr_select(jmodule, jresource, jtable, joinby, record, pkey,
                            representation=representation, multiple=multiple, next=here, jrecord=jrecord_id)
                    if _output:
                        output.update(_output)
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

                # default to List, TODO: DRY

                # Query
                # Filter Search list to just those records which user can read
                # Filter Search List to remove entries which have been deleted
                # Filter Search List for custom query
                query = shn_accessible_query('read', table)

                if 'deleted' in table:
                    query = ((table.deleted == False) | (table.deleted == None)) & query # includes None for backward compatability

                if request.filter:
                    query = request.filter & query

                # list_create if have permissions
                authorised = shn_has_permission('create', table)

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
                    fields = [table[f] for f in table.fields if table[f].readable]

                    # Column labels
                    headers = {}
                    for field in fields:
                        # Use custom or prettified label
                        headers[str(field)] = field.label

                    items = crud.select(table, query=query, fields=fields, limitby=limitby, orderby=orderby, headers=headers, truncate=48, _id='list', _class='display')

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

                        # Display the Add form below List
                        form = crud.create(table, onvalidation=onvalidation, onaccept=onaccept)
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
                    items = crud.select(table, query, truncate=24)
                    response.view = 'plain.html'
                    return dict(item=items)

                elif representation == "csv":
                    return export_csv(resource, query)

                elif representation == "json":
                    return export_json(table, query)

                elif representation == "pdf":
                    return export_pdf(table, query)

                elif representation == "rss":
                    return export_rss(module, resource, query, main, extra)

                elif representation == "xls":
                    return export_xls(table, query)

                elif representation == "xml":
                    return export_xml(table, query)

                else:
                    session.error = BADFORMAT
                    redirect(URL(r=request))

            # HTTP Create -----------------------------------------------------
            elif request.env.request_method == 'PUT':
                # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6
                # We don't yet implement PUT for create/update, although Web2Py does now support it
                # resource doesn't exist: Create using next available ID
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
                # DELETE, HEAD, OPTIONS, TRACE, CONNECT
                # Not implemented
                raise HTTP(501)

        # HTTP Single Record Operation ****************************************
        elif record_id and not method:

            # HTTP Read (single record) ---------------------------------------
            if request.env.request_method == 'GET':
                return shn_read(module, table, resource, record_id, representation, deletable, editable)

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

        # --------------------------------- old: ------------------------------
        #else:

            # Forward to single-table REST controller
            #return shn_rest_controller(module, resource,
            #    deletable=deletable,
            #    editable=editable,
            #    listadd=listadd,
            #    main=main,
            #    extra=extra,
            #    orderby=orderby,
            #    sortby=sortby,
            #    onvalidation=onvalidation,
            #    onaccept=onaccept)

# END
# *****************************************************************************
