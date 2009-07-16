# -*- coding: utf-8 -*-

module = 'vita'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Items'), False, '#',[
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

def pitem():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'pitem', main='tag_label', extra='description')

def presence():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'presence')
