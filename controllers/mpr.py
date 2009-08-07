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
    [T('Search for a Person'), False,  URL(r=request, f='index')],
    [T('Report a Missing Person'), False,  URL(r=request, f='index')],
    [T('Edit a Missing Person'), False,  URL(r=request, f='index')],
    [T('Report a Found Person'), False,  URL(r=request, f='index')],
    [T('Reports'), False,  URL(r=request, f='index'),[
        [T('List Missing People'), False, URL(r=request, f='index')],
        [T('List Found People'), False, URL(r=request, f='index')]
    ]]
]

def index():
    "Module's Home Page"
    return dict(module_name=module_name)
