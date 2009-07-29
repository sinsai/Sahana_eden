# -*- coding: utf-8 -*-

module = 'hrm'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Find'), False, URL(r=request, f='find'),[
        [T('Add Report'), False, URL(r=request, f='find', args='create')],
        [T('List Reports'), False, URL(r=request, f='find')]
    ]],
    [T('Recovery'), False, URL(r=request, f='recovery'),[
        [T('Add Body'), False, URL(r=request, f='body', args='create')],
        [T('List Bodies'), False, URL(r=request, f='body')]
#        [T('Add Item'), False, URL(r=request, f='item', args='create')],
#        [T('List Items'), False, URL(r=request, f='item')]
    ]]
#    [T('Body Recovery'), False, URL(r=request, f='recovery'),[
#        [T('Add Record'), False, URL(r=request, f='recovery', args='create')],
#        [T('List Records'), False, URL(r=request, f='recovery')],
#        [T('Search Records'), False, URL(r=request, f='recovery', args='search')],
#        [T('Dead Body'), False, URL(r=request, f='dead_body')]
#       [T('Personal Effect'), False, URL(r=request, f='personal_effect')]
#    ]],
#    [T('Storage'), False, URL(r=request, f='storage'),[
#        [T('Add Record'), False, URL(r=request, f='storage', args='create')],
#        [T('List Records'), False, URL(r=request, f='storage')],
#        [T('Search Records'), False, URL(r=request, f='storage', args='search')]
#    ]],
#    [T('Management'),  False, URL(r=request, f='management'),[
#        [T('Movement'), False, URL(r=request, f='movement')],
#        [T('Checklist of Operations'), False, URL(r=request, f='operation_checklist')]
#    ]]    
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def find():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'find')

def body():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'body')

#def storage():
#    "RESTlike CRUD controller"
#    return shn_rest_controller(module, 'storage')

#def dead_body():
#    "RESTlike CRUD controller"
#    return shn_rest_controller(module, 'dead_body')

#def management():
#    "RESTlike CRUD controller"
#    return shn_rest_controller(module, 'management')

#def movement():
#    "RESTlike CRUD controller"
#    return shn_rest_controller(module, 'movement')

#def operation_checklist():
#    "RESTlike CRUD controller"
#    return shn_rest_controller(module, 'operation_checklist')
