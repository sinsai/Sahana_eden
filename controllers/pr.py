# -*- coding: utf-8 -*-

#
# VITA - Person Registry, Identification, Tracking and Tracing system
#
# created 2009-07-24 by nursix
#

module = 'pr'

# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Persons'), False, URL(r=request, f='person'),[
        [T('Add Person'), False, URL(r=request, f='person', args='create')],
        [T('List Persons'), False, URL(r=request, f='person')],
        [T('Add Identity'), False, URL(r=request, f='identity', args='create')],
        [T('List Identities'), False, URL(r=request, f='identity')]
    ]],
    [T('Groups'), False, URL(r=request, f='group'),[
        [T('Add Group'), False, URL(r=request, f='group', args='create')],
        [T('List Groups'), False, URL(r=request, f='group')],
        [T('Add Group Membership'), False, URL(r=request, f='group_membership', args='create')],
        [T('List Group Memberships'), False, URL(r=request, f='group_membership')]
    ]],
    [T('Person Entities'), False, '#',[
        [T('List Entities'), False, URL(r=request, f='pentity')],
        [T('Add Image'), False, URL(r=request, f='image', args='create')],
        [T('List Images'), False, URL(r=request, f='image')],
        [T('Add Presence Record'), False, URL(r=request, f='presence', args='create')],
        [T('List Presence Records'), False, URL(r=request, f='presence')]
    ]]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

# RESTlike CRUD functions
def person():
    crud.settings.delete_onvalidation=shn_pentity_ondelete
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'person', main='first_name', extra='last_name', onvalidation=lambda form: shn_pentity_onvalidation(form, resource='pr_person', entity_class=1))
def identity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'identity')
def group():
    crud.settings.delete_onvalidation=shn_pentity_ondelete
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'group', main='group_name', extra='group_description', onvalidation=lambda form: shn_pentity_onvalidation(form, resource='pr_person', entity_class=2))
def group_membership():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'group_membership')
def image():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'image')
def presence():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'presence')
def pentity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'pentity', main='tag_label', listadd=False, deletable=False)

#
# Interactive functions -------------------------------------------------------
#
def download():
    "Download a file."
    return response.download(request, db) 

#
# Person Selector
#
def select():

    if not session.pr:
        session.pr = Storage()

    if request.vars.person_id:
        record = db.pr_person[request.vars.person_id]
        if record:
            session.pr.current_person = record.id
        del request.vars['person_id']
        redirect( URL( r=request ))

    if not session.pr.current_person:
        person_name="No person selected"
    else:
        person_name=db.pr_person[session.pr.current_person]['first_name']+' '+db.pr_person[session.pr.current_person]['last_name']

    form=FORM(TABLE(
            TR("", person_name,
                INPUT(_name="clr_btn", _type="submit", _value='Clear')
            ),
            TR("ID, Name or Label:",
                INPUT(_type="text",_name="label"),
                INPUT(_name="sbm_btn", _type="submit",_value='Search')
                )))

    items=None

    if form.accepts(request.vars,session):
        if form.vars.clr_btn=='':
            session.pr.current_person = db.pr_person[1].id
            redirect( URL( r=request ))
        else:
            if session.pr.current_person:
                del session.pr['current_person']
            redirect( URL( r=request ))

    if session.pr.current_person:
        items=TABLE(
                TR('Currently selected: '),
                TR(db.pr_person[session.pr.current_person]['first_name'],
                    db.pr_person[session.pr.current_person]['last_name']))

    return dict(request, title="Test", form=form, items=items)

