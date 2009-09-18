# -*- coding: utf-8 -*-

#
# DVR Disaster Victim Registry (Sahana Legacy)
#
# created 2009-08-06 by nursix
#

module = 'dvr'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [module_name, False, URL(r=request, f='index')],
    [T('Add Disaster Victims'), False,  URL(r=request, f='index'),[
        [T('Add new Group'), False, URL(r=request, f='index')],
        [T('Add new Individual'), False, URL(r=request, f='index')]
    ]],
    [T('Edit Disaster Victims'), False,  URL(r=request, f='index'),[
        [T('Search and Edit Group'), False, URL(r=request, f='index')],
        [T('Search and Edit Individual'), False, URL(r=request, f='index')]
    ]],
    [T('List Groups'), False,  URL(r=request, f='index'),[
        [T('List Groups/View Members'), False, URL(r=request, f='index')]
    ]],
    [T('Reports'), False,  URL(r=request, f='index'),[
        [T('Drill Down by Group'), False, URL(r=request, f='index')],
        [T('Drill Down by Shelter'), False, URL(r=request, f='index')],
        [T('Drill Down by Incident'), False, URL(r=request, f='index')]
    ]],
]

def index():
    "Module's Home Page"
    return dict(module_name=module_name)
