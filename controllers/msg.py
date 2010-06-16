# -*- coding: utf-8 -*-

"""
    Messaging Module - Controllers
"""

module = "msg"

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
	[T("Compose"), False, URL(r=request, f="outbox", args='create')],
	[T("Outbox"), False, URL(r=request, f="outbox")],
	[T('Distribution groups'), False, URL(r=request, f='group'), [
		[T('List/Add'), False, URL(r=request, f='group')],
		[T('Group Memberships'), False, URL(r=request, f='group_membership')],
	]],
    #[T('CAP'), False, URL(r=request, f='tbc')]
]

# S3 framework functions
def index():
    "Module's Home Page"

    module_name = s3.modules[module]["name_nice"]

    return dict(module_name=module_name)

def tbc():
    "Coming soon..."
    return dict()

def email_settings():
    " RESTlike CRUD controller for email settings - appears in the administration menu "
    module = 'msg'
    resource = 'email_settings'
    tablename = module + '_' + resource
    table = db[tablename]
    if not auth.has_membership(auth.id_group('Administrator')):
		session.error = UNAUTHORISED
		redirect(URL(r=request, f='index'))
    # CRUD Strings
    ADD_SETTING = T('Add Setting')
    VIEW_SETTINGS = T('View Settings')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SETTING,
        title_display = T('Setting Details'),
        title_list = VIEW_SETTINGS,
        title_update = T('Edit Email Settings'),
        title_search = T('Search Settings'),
        subtitle_list = T('Settings'),
        label_list_button = VIEW_SETTINGS,
        label_create_button = ADD_SETTING,
        msg_record_created = T('Setting added'),
        msg_record_modified = T('Email settings updated'),
        msg_record_deleted = T('Setting deleted'),
        msg_list_empty = T('No Settings currently defined'))
    response.menu_options = admin_menu_options
    return shn_rest_controller(module, 'email_settings', listadd=False, deletable=False)

#--------------------------------------------------------------------------------------------------

# The following 2 functions hook into the pr functions
# -----------------------------------------------------------------------------
def group():
    response.s3.filter = (db.pr_group.system == False) # do not show system groups
    response.s3.pagination = True
    "RESTlike CRUD controller"
    return shn_rest_controller('pr', "group",
                               main="group_name",
                               extra="group_description",
                               rheader=shn_pr_rheader,
                               deletable=False)
# -----------------------------------------------------------------------------
def group_membership():
    "RESTlike CRUD controller"
    return shn_rest_controller('pr', "group_membership")

#-------------------------------------------------------------------------------

def pe_contact():
    """ Allows the user to add,update and delete his contacts"""
    if auth.is_logged_in() or auth.basic():
        person = (db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.pr_pe_id)).first().pr_pe_id
        response.s3.filter = (db.pr_pe_contact.pr_pe_id == person)
    else:
        redirect(URL(r=request, c='default', f='user', args='login',
            vars={'_next':URL(r=request, c='msg', f='pe_contact')}))

    db.pr_pe_contact.name.writable = False
    db.pr_pe_contact.name.readable = False
    db.pr_pe_contact.id.writable = False
#   db.pr_pe_contact.id.readable = False
    db.pr_pe_contact.pr_pe_id.writable = False
    db.pr_pe_contact.pr_pe_id.readable = False
    db.pr_pe_contact.person_name.writable = False
    db.pr_pe_contact.person_name.readable = False
    def msg_pe_contact_onvalidation(form):
        """This onvalidation method adds the person id to the record"""
        person = (db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.pr_pe_id)).first().pr_pe_id
        form.vars.pr_pe_id = person
    def msg_pe_contact_restrict_access(jr):
        """The following restricts update and delete access to contacts not
        owned by the user"""
        if jr.id :
            person = (db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.pr_pe_id)).first().pr_pe_id
            if person == (db(db.pr_pe_contact.id == jr.id).select(db.pr_pe_contact.pr_pe_id)).first().pr_pe_id :
                return True
            else:
                session.error = T("Access denied")
                return dict(bypass = True, output = redirect(URL(r=request)))
        else:
            return True
    s3xrc.model.configure(db.pr_pe_contact,
            onvalidation=lambda form: msg_pe_contact_onvalidation(form))
    response.s3.prep = msg_pe_contact_restrict_access
    response.menu_options = []
    return shn_rest_controller('pr', 'pe_contact', listadd=True)

#-------------------------------------------------------------------------------

def search():
    """Do a search of groups which match a type
    Used for auto-completion
    """
    import gluon.contrib.simplejson as sj
    table1 = db.pr_group
    field1 = 'group_name'
    table2 = db.pr_person
    field21 = 'first_name'
    field22 = 'middle_name'
    field23 = 'last_name'
    # JQuery Autocomplete uses 'q' instead of 'value'
    value = request.vars.q
    if value:
		item = []
		query = db((table1[field1].like('%' + value + '%'))).select(db.pr_group.pr_pe_id)
		for row in query:
			item.append({'id':row.pr_pe_id,'name':shn_pentity_represent(row.pr_pe_id, default_label = '')})
		query = db((table2[field21].like('%' + value + '%'))).select(db.pr_person.pr_pe_id)
		for row in query:
			item.append({'id':row.pr_pe_id,'name':shn_pentity_represent(row.pr_pe_id, default_label = '')})
		query = db((table2[field22].like('%' + value + '%'))).select(db.pr_person.pr_pe_id)
		for row in query:
			item.append({'id':row.pr_pe_id,'name':shn_pentity_represent(row.pr_pe_id, default_label = '')})
		query = db((table2[field23].like('%' + value + '%'))).select(db.pr_person.pr_pe_id)
		for row in query:
			item.append({'id':row.pr_pe_id,'name':shn_pentity_represent(row.pr_pe_id, default_label = '')})
		item = sj.dumps(item)
		response.view = 'plain.html'
		return dict(item=item)
    return
#-------------------------------------------------------------------------------
def outbox():
    "RESTlike CRUD controller"
    if auth.is_logged_in() or auth.basic():
        if auth.has_membership(1):
            pass
        else:
            person = (db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.id)).first().id
            db.msg_outbox.id.readable = False
            response.s3.filter = (db.msg_outbox.person_id == person)
    else:
        redirect(URL(r=request, c='default', f='user', args='login',
            vars={'_next':URL(r=request, c='msg', f='outbox')}))

    def restrict_methods(jr):
		if jr.method == 'create':
			db.msg_outbox.pr_pe_id.widget = lambda f, v: StringWidget.widget(f, v)
			return True
		if jr.method == 'delete' or jr.method == 'update':
			if auth.has_membership(1):
				return True
			else:
				session.error = T('Restricted method')
				return dict(bypass = True, output = redirect(URL(r=request)))
		else:
			return True
    def msg_outbox_onvalidation(form):
        """This onvalidation method adds the person id to the record"""
        person = (db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.id)).first().id
        form.vars.person_id = person
        if not form.vars.pr_pe_id:
			session.error = T('Empty Recipients')
			redirect(URL(r=request,c='msg', f='outbox', args='create'))
    db.msg_outbox.status.writable = False
    db.msg_outbox.status.readable = True
    db.msg_outbox.person_id.readable = False
    db.msg_outbox.person_id.writable = False
    response.s3.prep = restrict_methods
    s3xrc.model.configure(db.msg_outbox,
            onvalidation=lambda form: msg_outbox_onvalidation(form))
    return shn_rest_controller('msg', "outbox", listadd=False)

#-------------------------------------------------------------------------------
def process_sms_via_api():
	"Controller for SMS api processing - to be called via cron"
	msg.process_outbox(contact_method = 2)
	return

def process_email_via_api():
	"Controller for Email api processing - to be called via cron"
	msg.process_outbox(contact_method = 1)
	return

#-------------------------------------------------------------------------------

@auth.requires_membership('Administrator')
def modem_settings():
    "Modem settings"
    try:
        import serial
    except ImportError:
        session.error = T('Python Serial module not available within the\
        Python - this needs installing to activate the Modem')
        redirect(URL(r=request, c='admin', f='index'))
    resource = 'modem_settings'
    tablename = module + '_' + resource
    table = db[tablename]
    # CRUD Strings
    ADD_SETTING = T('Add Setting')
    VIEW_SETTINGS = T('View Settings')
    s3.crud_strings[tablename] = Storage(
    title_create = ADD_SETTING,
    title_display = T('Setting Details'),
    title_list = VIEW_SETTINGS,
    title_update = T('Edit Modem Settings'),
    title_search = T('Search Settings'),
    subtitle_list = T('Settings'),
    label_list_button = VIEW_SETTINGS,
    label_create_button = ADD_SETTING,
    msg_record_created = T('Setting added'),
    msg_record_modified = T('Modem settings updated'),
    msg_record_deleted = T('Setting deleted'),
    msg_list_empty = T('No Settings currently defined'))

    crud.settings.update_next = URL(r=request, args=[1, 'update'])
    response.menu_options = admin_menu_options
    return shn_rest_controller(module, resource, deletable=False,
    listadd=False)

@auth.requires_membership('Administrator')
def gateway_settings():
    "Gateway settings"
    resource = 'gateway_settings'
    tablename = module + '_' + resource
    table = db[tablename]
    # CRUD Strings
    ADD_SETTING = T('Add Setting')
    VIEW_SETTINGS = T('View Settings')
    s3.crud_strings[tablename] = Storage(
    title_create = ADD_SETTING,
    title_display = T('Setting Details'),
    title_list = VIEW_SETTINGS,
    title_update = T('Edit Gateway Settings'),
    title_search = T('Search Settings'),
    subtitle_list = T('Settings'),
    label_list_button = VIEW_SETTINGS,
    label_create_button = ADD_SETTING,
    msg_record_created = T('Setting added'),
    msg_record_modified = T('Gateway settings updated'),
    msg_record_deleted = T('Setting deleted'),
    msg_list_empty = T('No Settings currently defined'))

    crud.settings.update_next = URL(r=request, args=[1, 'update'])
    response.menu_options = admin_menu_options
    return shn_rest_controller(module, resource, deletable=False,
    listadd=False)

