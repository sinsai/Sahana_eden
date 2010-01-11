# -*- coding: utf-8 -*-

module = 'vol'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice

# Options Menu (available in all Functions)
response.menu_options = [
        [T('Projects'), False, URL(r=request, f='projects'),[
        [T('Add Project'), False, URL(r=request, f='projects', args='create')],]],
        [T('Details'), False, URL(r=request, f='details'),[
        [T('Add Details'), False, URL(r=request, f='details', args='create')],
        #[T('List Organisations'), False, URL(r=request, f='organisation')],
        #[T('Search Organisations'), False, URL(r=request, f='organisation', args='search')]
   ]]

]
# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

@service.jsonrpc
@service.xmlrpc
@service.amfrpc    
def projects():
    return shn_rest_controller( module , 'projects')
    
def details():
    return shn_rest_controller( module , 'details')

def access_constraint_to_request():
    return shn_rest_controller( module , 'access_constraint_to_request')

def access_request():
    return shn_rest_controller( module , 'access_request')

def access_constraint():
    return shn_rest_controller( module , 'access_constraint')
