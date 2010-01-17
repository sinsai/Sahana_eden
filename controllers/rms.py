# -*- coding: utf-8 -*-

module = 'rms'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Request Aid'), False, URL(r=request, f='request_aid'),[
        [T('Request Aid'), False, URL(r=request, f='request_aid', args='create')],
    ]],
    [T('Pledge Aid'), False, URL(r=request, f='pledge_aid'),[
        [T('Pledge Aid'), False, URL(r=request, f='pledge_aid', args='create')],
    ]]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def request_aid():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'request_aid')

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def pledge_aid():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'pledge_aid')
