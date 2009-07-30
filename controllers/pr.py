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
#    [T('Person Entity'), False, '#',[
#        [T('Add Pentity'), False, URL(r=request, f='pentity', args='create')],
#        [T('List Pentity'), False, URL(r=request, f='pentity')]
#    ]],
    [T('Persons'), False, URL(r=request, f='person'),[
        [T('Add Person'), False, URL(r=request, f='person', args='create')],
        [T('List Persons'), False, URL(r=request, f='person')],
        [T('Search Persons'), False, URL(r=request, f='person', args='search')]
    ]],
    [T('Groups'), False, URL(r=request, f='group'),[
        [T('Add Group'), False, URL(r=request, f='group', args='create')],
        [T('List Groups'), False, URL(r=request, f='group')],
        [T('Search Group'), False, URL(r=request, f='group', args='search')],
        [T('Add Persons to Groups'), False, URL(r=request, f='group_member', args='create')],
        [T('List Group Members'), False, URL(r=request, f='group_member')]
    ]],
    [T('Cases'), False, URL(r=request, f='index'),[
        [T('My Cases'), False, URL(r=request, f='cases', args='my')],
        [T('All Cases'), False, URL(r=request, f='cases', args='all')],
        [T('Find Case'), False, URL(r=request, f='cases', args='find')],
        [T('New Case'), False, URL(r=request, f='cases', args='new')]
    ]],
#    [T('Contacts'), False, '#',[
#        [T('Add Contact'), False, URL(r=request, f='contact', args='create')],
#        [T('List Contacts'), False, URL(r=request, f='contact')],
#        [T('Search Contacts'), False, URL(r=request, f='contact', args='search')],
#        [T('Add Contacts to Persons'), False, URL(r=request, f='contact_to_person', args='create')],
#        [T('List Contacts of Persons'), False, URL(r=request, f='contact_to_person')]
#    ]],
#    [T('Identities'), False, '#',[
#        [T('Add Identity'), False, URL(r=request, f='identity', args='create')],
#        [T('List Identites'), False, URL(r=request, f='identity')]
#    ]],
    [T('Status'), False, '#',[
        [T('Add Status To Person'), False, URL(r=request, f='pentity_status', args='create')],
        [T('List Status'), False, URL(r=request, f='pentity_status')]
    ]],
    [T('Findings'), False, '#',[
        [T('Add Finding'), False, URL(r=request, f='finding', args='create')],
        [T('List Findings'), False, URL(r=request, f='finding')]
    ]],
    [T('Tracking and Tracing'), False, '#',[
        [T('List Items'), False, URL(r=request, f='pitem')],
        [T('Add Presence'), False, URL(r=request, f='presence', args='create')],
        [T('List Presences'), False, URL(r=request, f='presence')]
    ]],
    [T('Images'), False, URL(r=request, f='images'),[
        [T('Add Image'), False, URL(r=request, f='image', args='create')],
        [T('List Images'), False, URL(r=request, f='image')]
    ]],
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

# RESTlike CRUD functions
def pentity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'pentity')
def person():
    crud.settings.delete_onvalidation=shn_pentity_ondelete
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'person', main='first_name', extra='last_name', onvalidation=lambda form: shn_pentity_onvalidation(form, is_group=False))
def group():
    crud.settings.delete_onvalidation=shn_pentity_ondelete
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'group', main='group_name', extra='group_description', onvalidation=lambda form: shn_pentity_onvalidation(form, is_group=True))

def pentity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'pentity')

def finding():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'finding')

def image():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'image')

def group_member():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'group_member')

def identity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'identity')
def pentity_status():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'pentity_status')
def contact():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'contact')
def contact_to_person():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'contact_to_person')
def pitem():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'pitem', main='tag_label', extra='description', listadd=False, deletable=False)
def presence():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'presence')
def case():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'case')

#
# Interactive functions -------------------------------------------------------
#

def update_presence():


    
    return dict(module_name=module_name)

#
# Case Management
#
def cases():
    custom_view='index.html'
    
    if len(request.args) == 0:
        # No arguments => defaults to my
        pass
    else:
        method = str.lower(request.args[0])
        if method == 'my':
            #  session.auth.user.id
            pass
        elif method == 'all':
            pass
        elif method == 'find':
            pass
        elif method == 'new':
            pass
        else:
            pass
    pass
    
    response.view = module + '/' + custom_view
    return dict(module_name=module_name)

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
        print 'No person currently selected'
        person_name="No person selected"
    else:
        print 'Person ' + str(session.pr.current_person) + ' currently selected'
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
        print form.vars
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

#
# Update presence
#
def update_presence():
    return dict(module_name=module_name)
