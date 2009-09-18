# -*- coding: utf-8 -*-

module = 'dvi'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [module_name, False, URL(r=request, f='index')],
    [T('Checklist Of Operations'), False, URL(r=request, f='operation_checklist'),[
        [T('Personal Effects'), False, URL(r=request, f='personal_effects')],
        [T('Radiology'), False, URL(r=request, f='radiology')],
        [T('Fingerprints'), False, URL(r=request, f='fingerprints')],
        [T('Anthropology'), False, URL(r=request, f='anthropology')],
        [T('Pathology'), False, URL(r=request, f='pathology')],
        [T('DNA'), False, URL(r=request, f='dna')],
        [T('Dental'), False, URL(r=request, f='dental')],
        [T('Identification'), False, URL(r=request, f='identification')]
    ]]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)
def personal_effects():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'personal_effects')

def case():

    "Restlike CRUD controller"
    return shn_rest_controller(module, 'case')

def radiology():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'radiology')

def fingerprints():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'fingerprints')

def anthropology():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'anthropology')

def pathology():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'pathology')

def dna():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'dna')

def dental():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'dental')


def operation_checklist():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'operation_checklist')

def identification():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'identification')
