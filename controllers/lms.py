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
    ]],
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
				[T('Dispose Expired/Unusable Items'), False, URL(r=request, f='item_dispose')],
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
	
def kit():
    "RESTlike CRUD controller"
    response.pdf = URL(r=request, f='kit_export_pdf')
    response.xls = URL(r=request, f='kit_export_xls')
    if len(request.args) == 2:
        crud.settings.update_next = URL(r=request, f='kit_item', args=request.args[1])
    return shn_rest_controller(module, 'kit', main='code', onaccept=lambda form: kit_total(form))
def kit_item():
    "Many to Many CRUD Controller"
    if 'format' in request.vars:
        if request.vars.format == 'xls':
            redirect(URL(r=request, f='kit_export_xls'))
        elif request.vars.format == 'pdf':
            redirect(URL(r=request, f='kit_export_pdf'))
        elif request.vars.format == 'csv':
            if request.args(0):
                if str.lower(request.args(0)) == 'create':
                    return kit_import_csv()
                else:
                    session.error = BADMETHOD
                    redirect(URL(r=request))
            else:
                # List
                redirect(URL(r=request, f='kit_export_csv'))
        else:
            session.error = BADFORMAT
            redirect(URL(r=request))
    if len(request.args) == 0:
        session.error = T("Need to specify a kit!")
        redirect(URL(r=request, f='kit'))
    kit = request.args[0]
    table = db.lms_kit_item
    authorised = shn_has_permission('update', table)
    
    title = db.lms_kit[kit].code
    kit_description = db.lms_kit[kit].description
    kit_total_cost = db.lms_kit[kit].total_unit_cost
    kit_monthly_cost = db.lms_kit[kit].total_monthly_cost
    query = table.kit_id==kit
    # Start building the Return with the common items
    output = dict(module_name=module_name, title=title, description=kit_description, total_cost=kit_total_cost, monthly_cost=kit_monthly_cost)
    # Audit
    shn_audit_read(operation='list', resource='kit_item', record=kit, representation='html')
    item_list = []
    sqlrows = db(query).select()
    even = True
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, 'kit_item', 'html')
        # Display a List_Create page with editable Quantities
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.item_id
            description = db.lms_item[id].description
            id_link = A(id, _href=URL(r=request, f='item', args=['read', id]))
            quantity_box = INPUT(_value=row.quantity, _size=4, _name='qty' + str(id))
            unit_cost = db.lms_item[id].unit_cost
            monthly_cost = db.lms_item[id].monthly_cost
            minute_cost = db.lms_item[id].minute_cost
            megabyte_cost = db.lms_item[id].megabyte_cost
            total_units = unit_cost * row.quantity
            total_monthly = monthly_cost * row.quantity
            checkbox = INPUT(_type="checkbox", _value="on", _name=id, _class="remove_item")
            item_list.append(TR(TD(id_link), TD(description, _align='left'), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(minute_cost), TD(megabyte_cost), TD(total_units), TD(total_monthly), TD(checkbox, _align='center'), _class=theclass, _align='right'))
            
        table_header = THEAD(TR(TH('ID'), TH(table.item_id.label), TH(table.quantity.label), TH(db.lms_item.unit_cost.label), TH(db.lms_item.monthly_cost.label), TH(db.lms_item.minute_cost.label), TH(db.lms_item.megabyte_cost.label), TH(T('Total Units')), TH(T('Total Monthly')), TH(T('Remove'))))
        table_footer = TFOOT(TR(TD(B(T('Totals for Kit:')), _colspan=7), TD(B(kit_total_cost)), TD(B(kit_monthly_cost)), TD(INPUT(_id='submit_button', _type='submit', _value=T('Update')))), _align='right')
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name='custom', _method='post', _enctype='multipart/form-data', _action=URL(r=request, f='kit_update_items', args=[kit])))
        subtitle = T("Contents")
        
        crud.messages.submit_button=T('Add')
        # Check for duplicates before Item is added to DB
        crud.settings.create_onvalidation = lambda form: kit_dupes(form)
        # Calculate Totals for the Kit after Item is added to DB
        crud.settings.create_onaccept = lambda form: kit_total(form)
        crud.messages.record_created = T('Kit Updated')
        form = crud.create(table, next=URL(r=request, args=[kit]))
        addtitle = T("Add New Item to Kit")
        response.view = '%s/kit_item_list_create.html' % module
        output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form=form, kit=kit))
    else:
        # Display a simple List page
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.item_id
            description = db.lms_item[id].description
            id_link = A(id, _href=URL(r=request, f='item', args=['read', id]))
            quantity_box = row.quantity
            unit_cost = db.lms_item[id].unit_cost
            monthly_cost = db.lms_item[id].monthly_cost
            minute_cost = db.lms_item[id].minute_cost
            megabyte_cost = db.lms_item[id].megabyte_cost
            total_units = unit_cost * row.quantity
            total_monthly = monthly_cost * row.quantity
            item_list.append(TR(TD(id_link), TD(description, _align='left'), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(minute_cost), TD(megabyte_cost), TD(total_units), TD(total_monthly), _class=theclass, _align='right'))
            
        table_header = THEAD(TR(TH('ID'), TH(table.item_id.label), TH(table.quantity.label), TH(db.lms_item.unit_cost.label), TH(db.lms_item.monthly_cost.label), TH(db.lms_item.minute_cost.label), TH(db.lms_item.megabyte_cost.label), TH(T('Total Units')), TH(T('Total Monthly'))))
        table_footer = TFOOT(TR(TD(B(T('Totals for Kit:')), _colspan=7), TD(B(kit_total_cost)), TD(B(kit_monthly_cost)), _align='right'))
        items = DIV(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"))
        add_btn = A(T('Edit Contents'), _href=URL(r=request, c='default', f='user', args='login'), _id='add-btn')
        response.view = '%s/kit_item_list.html' % module
        output.update(dict(items=items, add_btn=add_btn))
    return output
	
def kit_dupes(form):
    "Checks for duplicate Item before adding to DB"
    kit = form.vars.kit_id
    item = form.vars.item_id
    table = db.lms_kit_item
    query = (table.kit_id==kit) & (table.item_id==item)
    items = db(query).select()
    if items:
        session.error = T("Item already in Kit!")
        redirect(URL(r=request, args=kit))
    else:
        return
    
def kit_total(form):
    "Calculate Totals for the Kit specified by Form"
    if 'kit_id' in form.vars:
        # called by kit_item()
        kit = form.vars.kit_id
    else:
        # called by kit()
        kit = form.vars.id
    kit_totals(kit)
    
def kit_totals(kit):
    "Calculate Totals for a Kit"
    table = db.lms_kit_item
    query = table.kit_id==kit
    items = db(query).select()
    total_unit_cost = 0
    total_monthly_cost = 0
    total_minute_cost = 0
    total_megabyte_cost = 0
    for item in items:
        query = (table.kit_id==kit) & (table.item_id==item.item_id)
        total_unit_cost += (db(db.lms_item.id==item.item_id).select()[0].unit_cost) * (db(query).select()[0].quantity)
        total_monthly_cost += (db(db.lms_item.id==item.item_id).select()[0].monthly_cost) * (db(query).select()[0].quantity)
        total_minute_cost += (db(db.lms_item.id==item.item_id).select()[0].minute_cost) * (db(query).select()[0].quantity)
        total_megabyte_cost += (db(db.lms_item.id==item.item_id).select()[0].megabyte_cost) * (db(query).select()[0].quantity)
    db(db.lms_kit.id==kit).update(total_unit_cost=total_unit_cost, total_monthly_cost=total_monthly_cost, total_minute_cost=total_minute_cost, total_megabyte_cost=total_megabyte_cost)

def kit_update_items():
    "Update a Kit's items (Quantity & Delete)"
    if len(request.args) == 0:
        session.error = T("Need to specify a kit!")
        redirect(URL(r=request, f='kit'))
    kit = request.args[0]
    table = db.lms_kit_item
    authorised = shn_has_permission('update', table)
    if authorised:
        for var in request.vars:
            if 'qty' in var:
                item = var[3:]
                quantity = request.vars[var]
                query = (table.kit_id==kit) & (table.item_id==item)
                db(query).update(quantity=quantity)
            else:
                # Delete
                item = var
                query = (table.kit_id==kit) & (table.item_id==item)
                db(query).delete()
        # Update the Total values
        kit_totals(kit)
        # Audit
        shn_audit_update_m2m(resource='kit_item', record=kit, representation='html')
        session.flash = T("Kit updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(r=request, f='kit_item', args=[kit]))