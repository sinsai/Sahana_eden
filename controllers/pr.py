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
    [T('Search for a Person'), False, URL(r=request, f='person', args='search_simple')],
    [T('View/Edit Person Details'), False, URL(r=request, f='person', args='read'),[
#        [T('Basic Details'), False, URL(r=request, f='person', args='view')],
        [T('Images'), False, URL(r=request, f='person', args='image')],
        [T('Identity'), False, URL(r=request, f='person', args='identity')],
        [T('Address'), False, URL(r=request, f='person', args='address')],
        [T('Contact Data'), False, URL(r=request, f='person', args='contact')],
        [T('Presence Log'), False, URL(r=request, f='person', args='presence')],
#        [T('Roles'), False, URL(r=request, f='person', args='role')],
#        [T('Status'), False, URL(r=request, f='person', args='status')],
        [T('Group Memberships'), False, URL(r=request, f='person', args='group_membership')],
    ]],
    [T('Add Person'), False, URL(r=request, f='person', args='create')],
    [T('Add Group'), False, URL(r=request, f='group', args='create')],
    [T('List Persons'), False, URL(r=request, f='person')],
    [T('List Groups'), False, URL(r=request, f='group')]
]

# S3 framework functions
def index():
    "Module's Home Page"
    gender = []
    for g_opt in pr_person_gender_opts:
        count = db((db.pr_person.deleted==False) & (db.pr_person.opt_pr_gender==g_opt)).count()
        gender.append([str(pr_person_gender_opts[g_opt]),count])
    age = []
    for a_opt in pr_person_age_group_opts:
        count = db((db.pr_person.deleted==False) & (db.pr_person.opt_pr_age_group==a_opt)).count()
        age.append([str(pr_person_age_group_opts[a_opt]),count])
    total = db(db.pr_person.deleted==False).count()
    return dict(module_name=module_name, gender=gender, age=age, total=total)

# Main controller functions
def person():
    crud.settings.delete_onvalidation=shn_pentity_ondelete
    return shn_jr_rest_controller(module, 'person', main='first_name', extra='last_name',
        pheader=shn_pr_pheader,
        onvalidation=lambda form: shn_pentity_onvalidation(form, table='pr_person', entity_class=1))

def group():
    request.filter = (db.pr_group.system==False) # do not show system groups
    crud.settings.delete_onvalidation=shn_pentity_ondelete
    "RESTlike CRUD controller"
    return shn_jr_rest_controller(module, 'group', main='group_name', extra='group_description',
        pheader=shn_pr_pheader,
        onvalidation=lambda form: shn_pentity_onvalidation(form, table='pr_group', entity_class=2), deletable=False)

def person_details():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'person_details')

def image():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'image')
def image_person():
    db.pr_image.pr_pe_id.requires = IS_NULL_OR(IS_ONE_OF(db,'pr_pentity.id',shn_pentity_represent,filterby='opt_pr_pentity_class',filter_opts=(1,)))
    request.filter=(db.pr_image.pr_pe_id==db.pr_pentity.id)&(db.pr_pentity.opt_pr_pentity_class==1)
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'image')

def identity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'identity')

def contact():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'contact')

def address():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'address')

def pentity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'pentity')

def presence():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'presence')
def presence_person():
    db.pr_presence.pr_pe_id.requires = IS_NULL_OR(IS_ONE_OF(db,'pr_pentity.id',shn_pentity_represent,filterby='opt_pr_pentity_class',filter_opts=(1,)))
    request.filter=(db.pr_presence.pr_pe_id==db.pr_pentity.id)&(db.pr_pentity.opt_pr_pentity_class==1)
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'presence')

def group_membership():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'group_membership')

#def image():
#    "RESTlike CRUD controller"
#    return shn_rest_controller(module, 'image')
#def presence():
#    "RESTlike CRUD controller"
#    return shn_rest_controller(module, 'presence')
#def pentity():
#    "RESTlike CRUD controller"
#    return shn_rest_controller(module, 'pentity', main='tag_label', listadd=False, deletable=False, editable=False)

#
# Interactive functions -------------------------------------------------------
#
def download():
    "Download a file."
    return response.download(request, db) 
