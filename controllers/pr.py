# -*- coding: utf-8 -*-

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
    [T('Persons'), False, '#',[
        [T('Add Person'), False, URL(r=request, f='person', args='create')],
        [T('List People'), False, URL(r=request, f='person')],
        [T('Search People'), False, URL(r=request, f='person', args='search')]
    ]],
    [T('Groups'), False, '#',[
        [T('Add Group'), False, URL(r=request, f='group', args='create')],
        [T('List Groups'), False, URL(r=request, f='group')],
        [T('Search Group'), False, URL(r=request, f='group', args='search')],
        [T('Add Persons to Groups'), False, URL(r=request, f='group_member', args='create')],
        [T('List Group Members'), False, URL(r=request, f='group_member')]
    ]],
#    [T('Contacts'), False, '#',[
#        [T('Add Contact'), False, URL(r=request, f='contact', args='create')],
#        [T('List Contacts'), False, URL(r=request, f='contact')],
#        [T('Search Contacts'), False, URL(r=request, f='contact', args='search')],
#        [T('Add Contacts to Persons'), False, URL(r=request, f='contact_to_person', args='create')],
#        [T('List Contacts of Persons'), False, URL(r=request, f='contact_to_person')]
#    ]],
    [T('Identities'), False, '#',[
        [T('Add Identity'), False, URL(r=request, f='identity', args='create')],
        [T('List Identites'), False, URL(r=request, f='identity')]
    ]]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

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
def group_member():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'group_member')
def identity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'identity')
def contact():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'contact')
def contact_to_person():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'contact_to_person')
