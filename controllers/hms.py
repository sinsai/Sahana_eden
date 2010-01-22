# -*- coding: utf-8 -*-

module = 'hms'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Hospitals'), False, URL(r=request, f='hospital'), [
        [T('List All'), False, URL(r=request, f='hospital')],
        [T('List by Location'), False, URL(r=request, f='hospital', args='search_location')],
        [T('Find by Name'), False, URL(r=request, f='hospital', args='search_simple')],
        [T('Add Hospital'), False, URL(r=request, f='hospital', args='create')],
    ]]
]

def shn_hms_menu_ext():
    menu = [
        [T('Hospitals'), False, URL(r=request, f='hospital'), [
            [T('List All'), False, URL(r=request, f='hospital')],
            [T('List by Location'), False, URL(r=request, f='hospital', args='search_location')],
            [T('Find by Name'), False, URL(r=request, f='hospital', args='search_simple')],
            [T('Add Hospital'), False, URL(r=request, f='hospital', args='create')],
        ]]
    ]
    if session.rcvars and 'hms_hospital' in session.rcvars:
        selection = db.hms_hospital[session.rcvars['hms_hospital']]
        if selection:
            menu_hospital = [
                    [selection.name, False, URL(r=request, f='hospital', args=['read', selection.id]), [
                        [T('Contacts'), False, URL(r=request, f='hospital', args=[selection.id, 'contact'])],
                        [T('Shortages'), False, URL(r=request, f='hospital', args=[selection.id, 'shortage'])],
                    ]]
            ]
            menu.extend(menu_hospital)
    response.menu_options = menu

shn_hms_menu_ext()

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def hospital():
    output = shn_rest_controller( module , 'hospital', listadd=False,
        pheader = shn_hms_hospital_pheader,
        list_fields=['id', 'name', 'location_id', 'phone1', 'fax', 'status', 'total_beds', 'available_beds'])
    shn_hms_menu_ext()
    return output
