# -*- coding: utf-8 -*-
#
# LMS Logistics Management System
#
# created 2009-07-08 by ajuonline
#

module = 'lms'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Administration'), False, '#',[
        [T('Warehouse/Sites Registry'), False, '#',[
			[T('Add Site'), False, URL(r=request, f='site', args='create')],
			[T('Search & List Site'), False, URL(r=request, f='site')],
			[T('Advanced Site Search'), False, URL(r=request, f='site', args='search')]
		]],
        [T('Storage Locations'), False, '#',[
			[T('Add Locations'), False, URL(r=request, f='storage_loc', args='create')],
			[T('Search & List Locations'), False, URL(r=request, f='storage_loc')],
			[T('Advanced Location Search'), False, URL(r=request, f='storage_loc', args='search')]
		]],
        [T('Storage Bins'), False, '#',[
			[T('Add Bin Type'), False, URL(r=request, f='storage_bin_type', args='create')],
			[T('Add Bins'), False, URL(r=request, f='storage_bin', args='create')],
			[T('Search & List Bins'), False, URL(r=request, f='storage_bin')],
			[T('Search & List Bin Types'), False, URL(r=request, f='storage_bin_type')],
			[T('Advanced Bin Search'), False, URL(r=request, f='storage_bin', args='search')]
		]],			
        [T('Relief Item Catalogue'), False, '#',[
			[T('Add Category'), False, URL(r=request, f='catalogue_cat', args='create')],
			[T('Search & List Category'), False, URL(r=request, f='catalogue_cat')],
			[T('Advanced Category Search'), False, URL(r=request, f='catalogue_cat', args='search')],
			[T('Add Sub-Category'), False, URL(r=request, f='catalogue_subcat', args='create')],
			[T('Search & List Sub-Category'), False, URL(r=request, f='catalogue_subcat')],
			[T('Advanced Sub-Category Search'), False, URL(r=request, f='catalogue_subcat', args='search')]
		]],
    ]],
    [T('Intake System'), False, '#',[
        [T('Add Item (s)'), False, URL(r=request, f='item', args='create')],
        [T('Advanced Item Search'), False, URL(r=request, f='item', args='search')],
        [T('Search & List Items'), False, URL(r=request, f='item')]
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

'''def site_category():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'site_category')
'''
def storage_loc():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'storage_loc')

def storage_bin_type():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'storage_bin_type')	
	
def storage_bin():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'storage_bin')	

def catalogue_cat():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'catalogue_cat')

def catalogue_subcat():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'catalogue_subcat')
	
def item():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'item')
	
def inventory():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'inventory')
