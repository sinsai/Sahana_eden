# -*- coding: utf-8 -*-

"""
    Messaging Module - Controllers
"""

module = 'msg'

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
if auth.has_membership(auth.id_group('Administrator')):
	response.menu_options.append([T('Admin'), False, URL(r=request, f='admin')])
# S3 framework functions
def index():
    "Module's Home Page"
    module_name = db(db.s3_module.name == module).select().first().name_nice
    return dict(module_name=module_name)

def tbc():
    "Coming soon..."
    return dict()

def admin():
	redirect(URL(r=request, f='setting', args=[1, 'update']))

def setting():
    " RESTlike CRUD controller "
    if not auth.has_membership(auth.id_group('Administrator')):
		session.error = UNAUTHORISED
		redirect(URL(r=request, f='index'))
    return shn_rest_controller(module, 'setting', listadd=False, deletable=False)

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
                               pheader=shn_pr_pheader,
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
    import json as original_json #get the json lib
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
		item = original_json.dumps(item)
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
            vars={'_next':URL(r=request, c='msg', f='pe_contact')}))

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
