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
        [T('List People'), False, URL(r=request, f='person')],
        [T('Search People'), False, URL(r=request, f='person', args='search')]
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
    [T('Tracking and Tracing'), False, '#',[
        [T('Add Item'), False, URL(r=request, f='pitem', args='create')],
        [T('List Items'), False, URL(r=request, f='pitem')],
        [T('Add Presence'), False, URL(r=request, f='presence', args='create')],
        [T('List Presences'), False, URL(r=request, f='presence')]
    ]]
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
    return shn_rest_controller(module, 'pitem', main='tag_label', extra='description')
def presence():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'presence')
def case():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'case')

#
# Interactive functions -------------------------------------------------------
#

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

    form=FORM(TABLE(TR("ID, Name or Label:",INPUT(_type="text",_name="label",requires=IS_NOT_EMPTY())),
            TR("",INPUT(_type="submit",_value="Search"))))

    items=None

    if form.accepts(request.vars,session):
        items = crud.select(db.pr_person, db.pr_pitem.tag_label.like(form.vars.label), truncate=48, _id='list', _class='display')

    return dict(request, title="Test", form=form, items=items)
