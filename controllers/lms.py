# -*- coding: utf-8 -*-

module = 'lms'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Administration'), False, '#',[
        [T('Warehouse/Sites Registry'), False, '#',[
			[T('Add Site'), False, URL(r=request, f='site', args='create')],
			[T('List Site'), False, URL(r=request, f='site')],
			[T('Search Site'), False, URL(r=request, f='site', args='search')]
		]],
        [T('Warehouse/Sites Category'), False, '#',[
			[T('Add Category'), False, URL(r=request, f='category', args='create')],
			[T('List Categories'), False, URL(r=request, f='category')],
			[T('Search Categories'), False, URL(r=request, f='category', args='search')]
		]],
        [T('Storage Locations'), False, '#',[
			[T('Add Locations'), False, URL(r=request, f='storage_loc', args='create')],
			[T('List Locations'), False, URL(r=request, f='storage_loc')],
			[T('Search Locations'), False, URL(r=request, f='storage_loc', args='search')]
		]],		
        [T('Relief Item Catalogue'), False, URL(r=request, f='catalogue', args='create')],             
    ]],
    [T('Intake System'), False, '#',[
        [T('Add Item (s)'), False, URL(r=request, f='item', args='create')],
        [T('Search & Edit Item (s)'), False, URL(r=request, f='item', args='search')],
        [T('List Items (Reports)'), False, URL(r=request, f='item', args='list')]
    ]],
    [T('Inventory Management'), False, '#',[
        [T('Adjust Item(s) Quantity'), False, URL(r=request, f='inventory', args='adjust')],
        [T('Kitting of Items'), False, URL(r=request, f='inventory', args='kitting')],
        [T('De-kitting of Items'), False, URL(r=request, f='inventory', args='dekitting')],
        [T('Aggregate Items'), False, URL(r=request, f='inventory', args='aggregate')]        
    ]]
]

def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def site():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'site')

def category():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'category')

def storage_loc():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'storage_loc')	

def catalogue():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'item')


def inventory():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'inventory')
