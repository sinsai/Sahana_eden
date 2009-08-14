# -*- coding: utf-8 -*-

#
# MPR Missing Person Registry (Sahana Legacy)
#
# created 2009-08-06 by nursix
#
module = 'mpr'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Search for a Person'), False,  URL(r=request, f='person_search')],
    [T('Report a Missing Person'), False,  URL(r=request, f='report_missing')],
    [T('Edit a Missing Person'), False,  URL(r=request, f='edit_missing')],
    [T('Report a Found Person'), False,  URL(r=request, f='report_found')],
    [T('Reports'), False,  URL(r=request, f='missing_persons'),[
        [T('List Missing People'), False, URL(r=request, f='missing_persons')],
        [T('List Found People'), False, URL(r=request, f='found_persons')]
    ]]
]

        [T('List Locations'), False, URL(r=request, f='presence_body')]


def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def person_search():
    "Module's Home Page"
    return dict(module_name=module_name)

def report_missing():
    "Module's Home Page"
    return dict(module_name=module_name)

def edit_missing():
    "Module's Home Page"
    return dict(module_name=module_name)

def report_found():
    "Module's Home Page"
    return dict(module_name=module_name)

def missing_persons():
    "Module's Home Page"
    return dict(module_name=module_name)
def found_persons():
    "Module's Home Page"
    return dict(module_name=module_name)
