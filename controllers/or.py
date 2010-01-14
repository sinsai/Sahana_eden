# -*- coding: utf-8 -*-

module = 'or'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Organisations'), False, URL(r=request, f='organisation'),[
        [T('Add Organisation'), False, URL(r=request, f='organisation', args='create')],
        #[T('List Organisations'), False, URL(r=request, f='organisation')],
        #[T('Search Organisations'), False, URL(r=request, f='organisation', args='search')]
    ]],
    [T('Offices'), False, URL(r=request, f='office'),[
        [T('Add Office'), False, URL(r=request, f='office', args='create')],
        #[T('List Offices'), False, URL(r=request, f='office')],
        #[T('Search Offices'), False, URL(r=request, f='office', args='search')]
    ]]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def sector():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'sector')

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
