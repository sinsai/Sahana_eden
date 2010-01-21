# -*- coding: utf-8 -*-

module = 'hms'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Hospitals'), False, URL(r=request, f='hospital'), [
        [T('Search by Name'), False, URL(r=request, f='hospital', args='search_simple')],
        [T('Search by Location'), False, URL(r=request, f='hospital', args='search_location')]
    ]]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def hospital():
    output = shn_rest_controller( module , 'hospital',
        list_fields=['name', 'location_id', 'phone1', 'fax', 'status', 'total_beds', 'available_beds'])
    return output
