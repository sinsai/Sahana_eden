# -*- coding: utf-8 -*-

module = 'rms'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Request Aid'), False, URL(r=request, f='organisation'),[
        [T('Request Aid'), False, URL(r=request, f='organisation', args='create')],
    ]],
    [T('Pledge Aid'), False, URL(r=request, f='office'),[
        [T('Pledge Aid'), False, URL(r=request, f='office', args='create')],
    ]]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def organisation():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'organisation')

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def office():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'office')

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def contact():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'contact')
