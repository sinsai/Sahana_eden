# -*- coding: utf-8 -*-

module = 'msg'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Admin'), False, URL(r=request, f='admin')],
    [T('Email'), False, URL(r=request, f='email'), [
        [T('Send Email'), False, URL(r=request, f='email_outbox', args='create')],
        [T('View Email InBox'), False, URL(r=request, f='email_inbox')],
        [T('View Email OutBox'), False, URL(r=request, f='email_outbox')],
        [T('View Sent Email'), False, URL(r=request, f='email_sent')],
    ]],
    [T('SMS'), False, URL(r=request, f='sms'), [
        [T('Send SMS'), False, URL(r=request, f='sms_outbox', args='create')],
        [T('View SMS InBox'), False, URL(r=request, f='sms_inbox')],
        [T('View SMS OutBox'), False, URL(r=request, f='sms_outbox')],
        [T('View Sent SMS'), False, URL(r=request, f='sms_sent')],
    ]],
    [T('Distribution Groups'), False, URL(r=request, f='group'), [
    ]],
    #[T('CAP'), False, URL(r=request, f='tbc')]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def tbc():
    "Coming soon..."
    return dict(module_name=module_name)


def admin():
    # This can be set to a MessagingAdmin role, if-desired
    if auth.has_membership(auth.id_group('Administrator')):
        redirect(URL(r=request, f='setting', args=['update', 1]))
    else:
        redirect(URL(r=request, f='setting', args=['read', 1]))
    
def setting():
    " RESTlike CRUD controller "
    if request.args(0) == 'update' or request.args(0) == 'delete':
        if not auth.has_membership(auth.id_group('Administrator')):
            session.error = UNAUTHORISED
            redirect(URL(r=request, f='index'))
    return shn_rest_controller(module, 'setting', listadd=False, deletable=False)
    
# SMS
def sms():
    " Simple page for showing links "
    title = T('SMS')
    return dict(module_name=module_name, title=title)
def sms_inbox():
    " RESTlike CRUD controller "
    return shn_rest_controller(module, 'sms_inbox', listadd=False)
def sms_outbox():
    " RESTlike CRUD controller "
    # Replace dropdown with an INPUT so that we can use the jQuery autocomplete plugin
    db.msg_sms_outbox.group_id.widget = lambda f, v: StringWidget.widget(f, v)
    # Restrict list to just those of type 'sms'
    # tbc
    return shn_rest_controller(module, 'sms_outbox')
def sms_sent():
    " RESTlike CRUD controller "
    return shn_rest_controller(module, 'sms_sent', listadd=False)

# Email
def email():
    " Simple page for showing links "
    title = T('Email')
    return dict(module_name=module_name, title=title)

def email_inbox():
    " RESTlike CRUD controller "
    # Is there an error from the polling script?
    status = db().select(db.msg_email_inbound_status.ALL)
    try:
        response.warning = status[0].status
        # Clear status
        db(db.msg_email_inbound_status.id==status[0].id).delete()
    except:
        pass
    return shn_rest_controller(module, 'email_inbox', listadd=False)

def email_outbox():
    " RESTlike CRUD controller "
    # Replace dropdown with an INPUT so that we can use the jQuery autocomplete plugin
    db.msg_email_outbox.group_id.widget = lambda f, v: StringWidget.widget(f, v)
    # Restrict list to just those of type 'email'
    # tbc
    return shn_rest_controller(module, 'email_outbox', listadd=False)
def email_sent():
    " RESTlike CRUD controller "
    return shn_rest_controller(module, 'email_sent', listadd=False)

def email_send():
    """ Send Pending emails from OutBox.
    If succesful then move from OutBox to Sent.
    Designed to be called from Cron """
    
    # Check database for pending mails
    table = db.msg_email_outbox
    query = table.id > 0
    rows = db(query).select()
    
    for row in rows:
        subject = row.subject
        message = row.body
        # Determine list of users
        group = row.group_id
        table2 = db.msg_group_user
        query = table2.group_id == group
        recipients = db(query).select()
        for recipient in recipients:
            to = db(db.pr_person.id==recipient.person_id).select()[0].email
            # If the user has an email address
            if to:
                # Use Tools API to send mail
                status = mail.send(to, subject, message)
        # We only check status of last recipient
        if status:
            # Add message to Sent
            db.msg_email_sent.insert(created_by=row.created_by, modified_by=row.modified_by, uuid=row.uuid, group_id=group, subject=subject, body=message)
            # Delete from OutBox
            db(table.id==row.id).delete()
            # Explicitly commit DB operations when running from Cron
            db.commit()
    return


# Contacts
def group():
    " RESTlike CRUD controller "
    # If we know which record we're editing
    if len(request.args) == 2:
        crud.settings.update_next = URL(r=request, f='group_user', args=request.args(1))
    return shn_rest_controller(module, 'group')
  
def group_user():
    "Many to Many CRUD Controller"
    if len(request.args) == 0:
        session.error = T("Need to specify a group!")
        redirect(URL(r=request, f='group'))
    group = request.args[0]
    table = db.msg_group_user
    authorised = shn_has_permission('update', table)
    
    title = db.msg_group[group].name
    group_description = db.msg_group[group].comments
    _group_type = db.msg_group[group].group_type
    group_type = msg_group_type_opts[_group_type]
    query = table.group_id==group
    # Start building the Return with the common items
    output = dict(module_name=module_name, title=title, description=group_description, group_type=group_type)
    # Audit
    shn_audit_read(operation='list', resource='group_user', record=group, representation='html')
    item_list = []
    sqlrows = db(query).select()
    even = True
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, 'group_user', 'html')
        # Display a List_Create page with deletable Rows
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.person_id
            name = db.pr_person[id].first_name + ' ' + db.pr_person[id].last_name
            preferred = db.pr_person[id].preferred_name
            id_link = A(id, _href=URL(r=request, c='pr', f='person', args=['read', id]))
            checkbox = INPUT(_type="checkbox", _value="on", _name=id, _class="remove_item")
            item_list.append(TR(TD(id_link), TD(name, _align='left'), TD(preferred, _align='left'), TD(checkbox, _align='center'), _class=theclass, _align='right'))
            
        table_header = THEAD(TR(TH('ID'), TH(table.person_id.label), TH(T('Preferred Name')), TH(T('Remove'))))
        table_footer = TFOOT(TR(TD('', _colspan=3), TD(INPUT(_id='submit_button', _type='submit', _value=T('Update')))), _align='right')
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name='custom', _method='post', _enctype='multipart/form-data', _action=URL(r=request, f='group_update_users', args=[group])))
        subtitle = T("Contents")
        
        crud.messages.submit_button=T('Add')
        # Do Checks before User is added to Group: Duplicates & Email/SMS fields available
        crud.settings.create_onvalidation = lambda form: group_validation(form)
        crud.messages.record_created = T('Group Updated')
        form = crud.create(table, next=URL(r=request, args=[group]))
        addtitle = T("Add New User to Group")
        response.view = '%s/group_user_list_create.html' % module
        output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form=form, group=group))
    else:
        # Display a simple List page
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.person_id
            name = db.pr_person[id].first_name + ' ' + db.pr_person[id].last_name
            preferred = db.pr_person[id].preferred_name
            id_link = A(id, _href=URL(r=request, c='pr', f='person', args=['read', id]))
            item_list.append(TR(TD(id_link), TD(name, _align='left'), TD(preferred, _align='left'), _class=theclass, _align='right'))
            
        table_header = THEAD(TR(TH('ID'), TH(table.person_id.label), TH(T('Preferred Name'))))
        items = DIV(TABLE(table_header, TBODY(item_list), _id="table-container"))
        add_btn = A(T('Edit Contents'), _href=URL(r=request, c='default', f='user', args='login'), _id='add-btn')
        response.view = '%s/group_user_list.html' % module
        output.update(dict(items=items, add_btn=add_btn))
    return output

def group_validation(form):
    """Do Checks before User added to Group:
    * Not a duplicate
    * User has Email &/or SMS fields available
    """
    group = form.vars.group_id
    user = form.vars.person_id
    # Check for Duplicates
    table = db.msg_group_user
    query = (table.group_id==group) & (table.person_id==user)
    items = db(query).select()
    if items:
        session.error = T("User already in Group!")
        redirect(URL(r=request, args=group))
    else:
        # Which type of Group is this?
        table = db.msg_group
        query = table.id==group
        group_type = db(query).select()[0].group_type
        table = db.pr_person
        query = table.id==user
        email = db(query).select()[0].email
        sms = db(query).select()[0].mobile_phone
        session.warning = ''
        # type 1 = Email
        # type 3 = Both
        if group_type == 1 or group_type == 3:
            # Check that Email field populated
            if not email:
                session.warning += str(T("User has no Email address!"))
        # type 2 = SMS
        if group_type == 2 or group_type == 3:
            # Check that SMS field populated
            if not sms:
                session.warning += str(T("User has no SMS address!"))
        return
    
def group_update_users():
    "Update a Group's members (Delete)"
    if len(request.args) == 0:
        session.error = T("Need to specify a group!")
        redirect(URL(r=request, f='group'))
    group = request.args[0]
    table = db.msg_group_user
    authorised = shn_has_permission('update', table)
    if authorised:
        for var in request.vars:
            user = var
            query = (table.group_id==group) & (table.person_id==user)
            db(query).delete()
        # Audit
        shn_audit_update_m2m(resource='group_user', record=group, representation='html')
        session.flash = T("Group updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(r=request, f='group_user', args=[group]))

def group_search():
    """Do a search of groups which match a type
    Used for auto-completion
    """
    item = ''
    if not 'type' in request.vars:
        item = '{"Status":"failed","Error":{"StatusCode":501,"Message":"Search requires specifying Type!"}}'
    if request.vars.type == 'email':
            # Types 'Email' & 'Both'
            belongs = (1, 3)
    elif request.vars.type == 'sms':
            # Types 'SMS' & 'Both'
            belongs = (2, 3)
    else:
        item = '{"Status":"failed","Error":{"StatusCode":501,"Message":"Unsupported type! Supported types: email, sms"}}'
    if not item:
        table = db.msg_group
        field = 'name'
        # JQuery Autocomplete uses 'q' instead of 'value'
        value = request.vars.q
        # JOIN bad for GAE
        query = (table[field].like('%' + value + '%')) & (table['group_type'].belongs(belongs))
        item = db(query).select().json()
        
    response.view = 'plain.html'
    return dict(item=item)
