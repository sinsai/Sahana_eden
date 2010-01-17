# -*- coding: utf-8 -*-

module = 'vol'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice

# Options Menu (available in all Functions)
response.menu_options = [
#        [T('Index'), False, URL(r=request, f='index')],
        [T('Projects'), False, URL(r=request, f='project'),[
            [T('Add Project'), False, URL(r=request, f='project', args='create')],
        ]],
#        [T('Positions'), False, URL(r=request, f='position'),[
#            [T('Add Position'), False, URL(r=request, f='position', args='create')],
#        ]],
#        [T('Volunteers'), False, URL(r=request, f='volunteer'),[
#            [T('Add Volunteer'), False, URL(r=request, f='volunteer', args='create')],
#        ]],
#        [T('Skills'), False, URL(r=request, f='skills'),[
#            [T('Add Skills'), False, URL(r=request, f='skills', args='create')],
#        ]],
#        [T('Hours'), False, URL(r=request, f='hours'),[
#            [T('Add Hours'), False, URL(r=request, f='hours', args='create')],
#        ]],
]
# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def project():
    return shn_rest_controller( module , 'project')

def position():
    return shn_rest_controller( module , 'position')

def volunteer():
    return shn_rest_controller( module , 'volunteer')

def skills():
    return shn_rest_controller( module , 'skills')

def hours():
    return shn_rest_controller( module , 'hours')
