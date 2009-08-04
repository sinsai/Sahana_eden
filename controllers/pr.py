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
        [T('Persons'), False, URL(r=request, f='person'),[
            [T('Add Person'), False, URL(r=request, f='person', args='create')],
            [T('List Persons'), False, URL(r=request, f='person')]
        ]],
        [T('Images'), False, URL(r=request, f='image_person'),[
            [T('Add Image'), False, URL(r=request, f='image_person', args='create')],
            [T('List Images'), False, URL(r=request, f='image_person')]
        ]],
        [T('Identities'), False, URL(r=request, f='identity'),[
            [T('Add Identity'), False, URL(r=request, f='identity', args='create')],
            [T('List Identities'), False, URL(r=request, f='identities')]
        ]],
#        [T('Add Image'), False, URL(r=request, f='image_person', args='create')],
#        [T('Add Identity'), False, URL(r=request, f='identity', args='create')],
#        [T('List Persons'), False, URL(r=request, f='person')],
#        [T('List Images'), False, URL(r=request, f='image_person')],
#        [T('List Identities'), False, URL(r=request, f='identity')]
    ]],
    [T('Groups'), False, URL(r=request, f='group'),[
        [T('Add Group'), False, URL(r=request, f='group', args='create')],
        [T('List Groups'), False, URL(r=request, f='group')],
        [T('Add Group Membership'), False, URL(r=request, f='group_membership', args='create')],
        [T('List Group Memberships'), False, URL(r=request, f='group_membership')]
    ]],
    [T('Person Entities'), False, '#',[
        [T('List Entities'), False, URL(r=request, f='pentity')],
#        [T('Add Image To Entity'), False, URL(r=request, f='image', args='create')],
#        [T('List Images'), False, URL(r=request, f='image')],
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
    return shn_rest_controller(module, 'person', main='first_name', extra='last_name', onvalidation=lambda form: shn_pentity_onvalidation(form, table='pr_person', entity_class=1))
def identity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'identity')
def group():
    crud.settings.delete_onvalidation=shn_pentity_ondelete
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'group', main='group_name', extra='group_description', onvalidation=lambda form: shn_pentity_onvalidation(form, table='pr_group', entity_class=2))
def group_membership():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'group_membership')
def image():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'image')
def image_person():
    db.pr_image.pr_pe_id.requires = IS_NULL_OR(IS_PE_ID(db, pr_pentity_class_opts, filter_opts=(1,)))
    request.filter=(db.pr_image.pr_pe_id==db.pr_pentity.id)&(db.pr_pentity.opt_pr_pentity_class==1)
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'image')
def presence():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'presence')
def pentity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'pentity', main='tag_label', listadd=False, deletable=False, editable=False)

#
# Interactive functions -------------------------------------------------------
#
def download():
    "Download a file."
    return response.download(request, db) 

