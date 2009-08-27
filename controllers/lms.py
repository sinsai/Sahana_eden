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
	[T('Procurements'), False, URL(r=request, f='#')],
	[T('Shipments'), False, URL(r=request, f='#')],
    [T('Warehouse Management'), False, URL(r=request, f='#'), [
		[T('Intake System'), False, 'intake',[
			[T('Add Item (s)'), False, URL(r=request, f='item', args='create')],
			[T('Search & List Items'), False, URL(r=request, f='item')],
			[T('Advanced Item Search'), False, URL(r=request, f='item', args='search')]
		]],
		[T('Warehouse Management'), False, '#',[
				[T('Adjust Item(s) Quantity'), False, URL(r=request, f='item_adjust')],
				[T('Manage Kits'), False, URL(r=request, f='kit')],
				[T('Aggregate Items'), False, URL(r=request, f='item_aggregate')],
				[T('Assign Storage Location'), False, URL(r=request, f='item_assign_storage')],
				[T('Add to Catalogue'), False, URL(r=request, f='item_assign_catalogue')],
				[T('Adjust Items due to Theft/Loss'), False, URL(r=request, f='item_adjust_theft')],
				[T('Dispatch Items'), False, URL(r=request, f='item_dispatch')],
				[T('Dispose Expired/Unusable Items'), False, URL(r=request, f='item_dispose')]
    ]]
	]],
	[T('Fleet Management'), False, URL(r=request, f='#')],
	    [T('Administration'), False, URL(r=request, f='admin'), [
        [T('Units of Measure'), False, 'unit',[
			[T('Add Unit'), False, URL(r=request, f='unit', args='create')],
			[T('Search & List Unit'), False, URL(r=request, f='unit')],
			[T('Advanced Unit Search'), False, URL(r=request, f='unit', args='search')]
		]],	
        [T('Warehouse/Sites Registry'), False, 'site',[
			[T('Add Site'), False, URL(r=request, f='site', args='create')],
			[T('Search & List Site'), False, URL(r=request, f='site')],
			[T('Advanced Site Search'), False, URL(r=request, f='site', args='search')]
		]],
        [T('Storage Locations'), False, 'storage_loc',[
			[T('Add Locations'), False, URL(r=request, f='storage_loc', args='create')],
			[T('Search & List Locations'), False, URL(r=request, f='storage_loc')],
			[T('Advanced Location Search'), False, URL(r=request, f='storage_loc', args='search')]
		]],
        [T('Storage Bins'), False, 'storage_bin',[
			[T('Add Bin Type'), False, URL(r=request, f='storage_bin_type', args='create')],
			[T('Add Bins'), False, URL(r=request, f='storage_bin', args='create')],
			[T('Search & List Bins'), False, URL(r=request, f='storage_bin')],
			[T('Search & List Bin Types'), False, URL(r=request, f='storage_bin_type')],
			[T('Advanced Bin Search'), False, URL(r=request, f='storage_bin', args='search')]
		]],			
        [T('Relief Item Catalogue'), False, 'catalogue',[
			[T('Manage Item Catalogue'), False, '#',[
				[T('Add Catalogue'), False, URL(r=request, f='catalogue', args='create')],
				[T('Search & List Catalogue'), False, URL(r=request, f='catalogue')],
				[T('Advanced Catalogue Search'), False, URL(r=request, f='catalogue', args='search')]
			]],
			[T('Manage Category'), False, '#',[
				[T('Add Category'), False, URL(r=request, f='catalogue_cat', args='create')],
				[T('Search & List Category'), False, URL(r=request, f='catalogue_cat')],
				[T('Advanced Category Search'), False, URL(r=request, f='catalogue_cat', args='search')]
			]],
			[T('Manage Sub-Category'), False, '#',[
				[T('Add Sub-Category'), False, URL(r=request, f='catalogue_subcat', args='create')],
				[T('Search & List Sub-Category'), False, URL(r=request, f='catalogue_subcat')],
				[T('Advanced Sub-Category Search'), False, URL(r=request, f='catalogue_subcat', args='search')]
			]]
		]],
    ]]
]

def index():
    "Module's Home Page"
    return dict(module_name=module_name)
	
# Administration Index Page
def admin():
    " Simple page for showing links "
    title = T('LMS Administration')
    return dict(module_name=module_name, title=title)	

def unit():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'unit')
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

def catalogue():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'catalogue')

def catalogue_cat():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'catalogue_cat')

def catalogue_subcat():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'catalogue_subcat')
	
def item():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'item', main='ordered_list_item', extra='description', onaccept=lambda form: item_cascade(form))

def item_cascade(form):
    """
    When an Item is updated, then also need to update all Kits, Bundles & Budgets which contain this item
    Called as an onaccept from the RESTlike controller
    """
    # Check if we're an update form
    if form.vars.id:
        item = form.vars.id
        # Update Kits containing this Item
        table = db.lms_kit_item
        query = table.item_id==item
        rows = db(query).select()
    return
	
def inventory():
    " Simple page for showing links "
    title = T('Inventory Management')
    return dict(module_name=module_name, title=title)