# -*- coding: utf-8 -*-

module = 'pe'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)

response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Individual'), False,URL(r=request, f='individual')],
    [T('Group'), False, URL(r=request, f='group')]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def individual():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'individual')


def individual():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'individual')

def name():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'individual_name')

def identity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'individual_identity')

def contact():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'contact')
