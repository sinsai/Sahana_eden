# -*- coding: utf-8 -*-

#
# Sahanapy Joined Resources RESTlike controller
#
# created 2009-09-06 by nursix
#

jrlayer = JRLayer(db)

# Make these constants to ensure consistency
UNAUTHORISED = T('Not authorised!')
BADFORMAT = T('Unsupported format!')
BADMETHOD = T('Unsupported method!')
BADRECORD = T('No such record!')

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
        if tablename in session:
            record_id = session[tablename]
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
        session[tablename] = record_id

    return record_id

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

    if not _request:
        session.error = BADMETHOD
        redirect(URL(r=request, c=module, f='index'))

    jmodule = _request['jmodule']
    jresource = _request['jresource']
    jrecord_id = _request['jrecord_id']
    multiple = _request['multiple']

    method = _request['method']

    # Identify main resource record -------------------------------------------

    # Get primary table
    tablename = "%s_%s" % (module,resource)
    table = db[tablename]

    # Check read permission on primary table
    if not shn_has_permission('read', table):
        session.error = UNAUTHORIZED
        redirect(URL(r=request, c='default', f='user', args='login',
            vars={'_next':URL(r=request, c=module, f=resource, args=[record_id, jresource, method])}))

    # Try to identify record
    record_id = shn_jr_identify_precord(module, resource, _request['record_id'], jresource)

    if record_id==0:
        session.error = BADRECORD
        redirect(URL(r=request, c=module, f='index'))

    # Record ID is required in joined-table operations
    if jresource and not record_id:
        # TODO: Cleanup - this is PR specific
        if module=="pr" and resource=="person" and representation=='html':
            # TODO: make this nicer:
            next_args = "[id]/%s" % jresource
            if method:
                next_args="%s/%s" % (next_args, method)
            next = URL(r=request, c=module, f=resource, args=next_args)
            back = { "_next" : next }
            redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=back))
        else:
            session.error = BADRECORD
            redirect(URL(r=request, c=module, f='index'))

    # Append record ID to request
    if record_id and len(request.args)>0:
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

    # Map action --------------------------------------------------------------
    # Available variables beyond this point:
    # request, module, resource, tablename, table, record_id, method, jresource, joinby
    # additionally:
    #  if jresource: jmodule, jtablename, jtable

    if jresource:
        # Action on joined resource

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

        # Get primary table
        tablename = "%s_%s" % (module, resource)
        table = db[tablename]

        # Get primary record
        query = (table.id==record_id)
        if 'deleted' in table:
            query = ((table.deleted==False) | (table.deleted==None)) & query
        try:
            record = db(query).select()[0]
        except:
            session.error = BADRECORD
            redirect(URL(r=request, c=module, f='index'))

        # Get joined table
        jtablename = "%s_%s" % (jmodule, jresource)
        jtable = db[jtablename]

        # TODO: select proper default or custom view
        response.view = 'pr/person.html'

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

    else:
        # Action on main resource

        #TODO: make generic (this here is PR specific) or pluggable
        if method=="search_simple":

            if module=="pr" and resource=="person" and representation=="html":
                return shn_pr_person_search_simple(representation=representation)

            else:
                session.error = BADMETHOD
                redirect(URL(r=request, c=module, f='index'))

        elif method=="clear":

            # TODO: proper cleanup of session_var at login/logout
            session_var = '%s_%s' % (module, resource)

            if session_var in session:
                del session[session_var]

            if '_next' in request.vars:
                request_vars = dict(_next=request.vars._next)
            else:
                request_vars = {}

            # TODO: build a generic search function, this here is PR specific
            if module=="pr" and resource=="person" and representation=="html":
                redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request_vars))
            else:
                redirect(URL(r=request, c='pr', f=resource))

        else:
            return shn_rest_controller(module, resource, main=main, extra=extra, onvalidation=onvalidation, onaccept=onaccept)

# END
# *****************************************************************************
