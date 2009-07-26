# -*- coding: utf-8 -*-

module = 'vtt'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Items'), False, URL(r=request, f='vtt_item')],
    [T('Tags'), False, URL(r=request, f='tag')],
    [T('Observer'), False, URL(r=request, f='observer')],
    [T('Reporter'), False, URL(r=request, f='reporter')],
    [T('Presence'), False, URL(r=request, f='presence')],
    [T('Process'), False, URL(r=request, f='process')],
    [T('Role'), False, URL(r=request, f='role')],
    [T('Status Transitions'), False, URL(r=request, f='status_transition')]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def vtt_item():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'item', deletable=False)
    
def tag():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'tag', main='code', extra='description', onaccept=lambda form: item_cascade(form))

def observer():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'observer', deletable=False)
    
def reporter():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'reporter', main='code', extra='description', onaccept=lambda form: item_cascade(form))

def presence():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'presence', deletable=False)
    
def process():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'process', main='code', extra='description', onaccept=lambda form: item_cascade(form))

def role():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'role', deletable=False)
    
def status_transition():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'status_transition', main='code', extra='description', onaccept=lambda form: item_cascade(form))
