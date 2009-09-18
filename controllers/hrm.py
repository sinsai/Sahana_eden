# -*- coding: utf-8 -*-

module = 'hrm'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Find'), False, URL(r=request, f='find'),[
        [T('Add Report'), False, URL(r=request, f='find', args='create')],
        [T('List Reports'), False, URL(r=request, f='find')]
    ]],
    [T('Recovery'), False, URL(r=request, f='recovery'),[
        [T('Add Body'), False, URL(r=request, f='body', args='create')],
        [T('Add Image'), False, URL(r=request, f='image_body', args='create')],
        [T('Register to Location'), False, URL(r=request, f='presence_body', args='create')],
        [T('List Bodies'), False, URL(r=request, f='body')],
        [T('List Images'), False, URL(r=request, f='image_body')],
        [T('List Locations'), False, URL(r=request, f='presence_body')]
    ]]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def find():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'find')

def body():
    crud.settings.delete_onvalidation=shn_pentity_ondelete
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'body', onvalidation=lambda form: shn_pentity_onvalidation(form, table='hrm_body', entity_class=3))

def image_body():
    db.pr_image.pr_pe_id.requires = IS_NULL_OR(IS_ONE_OF(db,'pr_pentity.id',shn_pentity_represent,filterby='opt_pr_entity_type',filter_opts=(3,)))
    request.filter=(db.pr_image.pr_pe_id==db.pr_pentity.id)&(db.pr_pentity.opt_pr_entity_type==3)
    "RESTlike CRUD controller"
    return shn_rest_controller('pr', 'image')

def presence_body():
    db.pr_presence.pr_pe_id.requires =  IS_NULL_OR(IS_ONE_OF(db,'pr_pentity.id',shn_pentity_represent,filterby='opt_pr_entity_type',filter_opts=(3,)))
    request.filter=(db.pr_presence.pr_pe_id==db.pr_pentity.id)&(db.pr_pentity.opt_pr_entity_type==3)
    "RESTlike CRUD controller"
    return shn_rest_controller('pr', 'presence')
