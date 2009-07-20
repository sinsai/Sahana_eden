# -*- coding: utf-8 -*-

module = 'budget'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Parameters'), False, URL(r=request, f='parameters')],
    [T('Items'), False, URL(r=request, f='item')],
    [T('Kits'), False, URL(r=request, f='kit')],
    [T('Bundles'), False, URL(r=request, f='bundle')],
    [T('Staff'), False, URL(r=request, f='staff')],
    [T('Locations'), False, URL(r=request, f='location')],
    [T('Projects'), False, URL(r=request, f='project')],
    [T('Budgets'), False, URL(r=request, f='budget')]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)


def parameters():
    "Select which page to go to depending on login status"
    table = db.budget_parameter
    authorised = has_permission('update', table)
    if authorised:
        redirect (URL(r=request, f='parameter', args=['update', 1]))
    else:
        redirect (URL(r=request, f='parameter', args=['read', 1]))

def parameter():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'parameter', deletable=False)
    
def item():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'item', main='code', extra='description', onaccept=lambda form: item_cascade(form))

def item_cascade(form):
    """
    When an Item is updated, then also need to update all Kits, Bundles & Budgets which contain this item
    Called as an onaccept from the RESTlike controller
    """
    # Check if we're an update form
    if form.vars.id:
        item = form.vars.id
        # Update Kits containing this Item
        table = db.budget_kit_item
        query = table.item_id==item
        rows = db(query).select()
        for row in rows:
            kit = row.kit_id
            kit_totals(kit)
            # Update Bundles containing this Kit
            table = db.budget_bundle_kit
            query = table.kit_id==kit
            rows = db(query).select()
            for row in rows:
                bundle = row.bundle_id
                bundle_totals(bundle)
                # Update Budgets containing this Bundle (tbc)
        # Update Bundles containing this Item
        table = db.budget_bundle_item
        query = table.item_id==item
        rows = db(query).select()
        for row in rows:
            bundle = row.bundle_id
            bundle_totals(bundle)
            # Update Budgets containing this Bundle (tbc)
    return

def kit():
    "RESTlike CRUD controller"
    if len(request.args) == 2:
        crud.settings.update_next = URL(r=request, f='kit_item', args=request.args[1])
    return shn_rest_controller(module, 'kit', main='code', onaccept=lambda form: kit_total(form))

def kit_item():
    "Many to Many CRUD Controller"
    if len(request.args) == 0:
        session.error = T("Need to specify a kit!")
        redirect(URL(r=request, f='kit'))
    kit = request.args[0]
    table = db.budget_kit_item
    authorised = shn_has_permission('update', table)
    
    title = db.budget_kit[kit].code
    kit_description = db.budget_kit[kit].description
    kit_total_cost = db.budget_kit[kit].total_unit_cost
    kit_monthly_cost = db.budget_kit[kit].total_monthly_cost
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
            description = db.budget_item[id].description
            id_link = A(id, _href=URL(r=request, f='item', args=['read', id]))
            quantity_box = INPUT(_value=row.quantity, _size=4, _name='qty' + str(id))
            unit_cost = db.budget_item[id].unit_cost
            monthly_cost = db.budget_item[id].monthly_cost
            minute_cost = db.budget_item[id].minute_cost
            megabyte_cost = db.budget_item[id].megabyte_cost
            total_units = unit_cost * row.quantity
            total_monthly = monthly_cost * row.quantity
            checkbox = INPUT(_type="checkbox", _value="on", _name=id, _class="remove_item")
            item_list.append(TR(TD(id_link), TD(description, _align='left'), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(minute_cost), TD(megabyte_cost), TD(total_units), TD(total_monthly), TD(checkbox, _align='center'), _class=theclass, _align='right'))
            
        table_header = THEAD(TR(TH('ID'), TH(table.item_id.label), TH(table.quantity.label), TH(db.budget_item.unit_cost.label), TH(db.budget_item.monthly_cost.label), TH(db.budget_item.minute_cost.label), TH(db.budget_item.megabyte_cost.label), TH(T('Total Units')), TH(T('Total Monthly')), TH(T('Remove'))))
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
            description = db.budget_item[id].description
            id_link = A(id, _href=URL(r=request, f='item', args=['read', id]))
            quantity_box = row.quantity
            unit_cost = db.budget_item[id].unit_cost
            monthly_cost = db.budget_item[id].monthly_cost
            minute_cost = db.budget_item[id].minute_cost
            megabyte_cost = db.budget_item[id].megabyte_cost
            total_units = unit_cost * row.quantity
            total_monthly = monthly_cost * row.quantity
            item_list.append(TR(TD(id_link), TD(description, _align='left'), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(minute_cost), TD(megabyte_cost), TD(total_units), TD(total_monthly), _class=theclass, _align='right'))
            
        table_header = THEAD(TR(TH('ID'), TH(table.item_id.label), TH(table.quantity.label), TH(db.budget_item.unit_cost.label), TH(db.budget_item.monthly_cost.label), TH(db.budget_item.minute_cost.label), TH(db.budget_item.megabyte_cost.label), TH(T('Total Units')), TH(T('Total Monthly'))))
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
    table = db.budget_kit_item
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
    table = db.budget_kit_item
    query = table.kit_id==kit
    items = db(query).select()
    total_unit_cost = 0
    total_monthly_cost = 0
    total_minute_cost = 0
    total_megabyte_cost = 0
    for item in items:
        query = (table.kit_id==kit) & (table.item_id==item.item_id)
        total_unit_cost += (db(db.budget_item.id==item.item_id).select()[0].unit_cost) * (db(query).select()[0].quantity)
        total_monthly_cost += (db(db.budget_item.id==item.item_id).select()[0].monthly_cost) * (db(query).select()[0].quantity)
        total_minute_cost += (db(db.budget_item.id==item.item_id).select()[0].minute_cost) * (db(query).select()[0].quantity)
        total_megabyte_cost += (db(db.budget_item.id==item.item_id).select()[0].megabyte_cost) * (db(query).select()[0].quantity)
    db(db.budget_kit.id==kit).update(total_unit_cost=total_unit_cost, total_monthly_cost=total_monthly_cost, total_minute_cost=total_minute_cost, total_megabyte_cost=total_megabyte_cost)

def kit_update_items():
    "Update a Kit's items (Quantity & Delete)"
    if len(request.args) == 0:
        session.error = T("Need to specify a kit!")
        redirect(URL(r=request, f='kit'))
    kit = request.args[0]
    table = db.budget_kit_item
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

def kit_export():
    """
    Export a list of Kits in Excel XLS format
    Sheet 1 is a list of Kits
    Then there is a separate sheet per kit, listing it's component items
    """
    try:
        import xlwt
    except ImportError:
        session.error = T('xlwt module not available within the running Python  - this needs installing to do XLS Reporting!')
        redirect(URL(r=request, c='kit'))
    
    import StringIO
    output = StringIO.StringIO()
    
    book = xlwt.Workbook()
    # List of Kits
    sheet1 = book.add_sheet('Kits')
    # Header row for Kits sheet
    row0 = sheet1.row(0)
    cell = 0
    table = db.budget_kit
    kits = db(table.id > 0).select()
    fields = [table[f] for f in table.fields if table[f].readable]
    for field in fields:
        row0.write(cell, field.label, xlwt.easyxf('font: bold True;'))
        cell += 1
    
    # For Header row on Items sheets
    table = db.budget_item
    fields_items = [table[f] for f in table.fields if table[f].readable]
    
    row = 1
    for kit in kits:
        # The Kit details on Sheet 1
        rowx = sheet1.row(row)
        row += 1
        cell1 = 0
        for field in fields:
            tab, col = str(field).split('.')
            rowx.write(cell1, kit[col])
            cell1 += 1
        # Sheet per Kit detailing constituent Items
        sheetname = kit.code.replace("\\","")
        sheet = book.add_sheet(sheetname)
        # Header row for Items sheet
        row0 = sheet.row(0)
        cell = 0
        for field_item in fields_items:
            row0.write(cell, field_item.label, xlwt.easyxf('font: bold True;'))
            cell += 1
        # List Items in each Kit
        table = db.budget_kit_item
        contents = db(table.kit_id == kit.id).select()
        rowy = 1
        for content in contents:
            table = db.budget_item
            item = db(table.id == content.item_id).select()[0]
            rowx = sheet.row(rowy)
            rowy += 1
            cell = 0
            for field_item in fields_items:
                tab, col = str(field_item).split('.')
                # Do lookups for option fields
                if col == 'cost_type':
                    table = db.budget_cost_type
                    value = db(table.id == item[col]).select()[0].name
                elif col == 'category_type':
                    table = db.budget_category_type
                    value = db(table.id == item[col]).select()[0].name
                else:
                    value = item[col]
                rowx.write(cell, value)
                cell += 1
    
    book.save(output)
    output.seek(0)

    import gluon.contenttype
    response.headers['Content-Type'] = gluon.contenttype.contenttype('.xls')
    filename = "%s_kits.xls" % (request.env.server_name)
    response.headers['Content-disposition'] = "attachment; filename=%s" % filename
    
    return output.read()
    
def bundle():
    "RESTlike CRUD controller"
    if len(request.args) == 2:
        crud.settings.update_next = URL(r=request, f='bundle_kit_item', args=request.args[1])
    return shn_rest_controller(module, 'bundle', onaccept=lambda form: bundle_total(form))

def bundle_kit_item():
    "Many to Many CRUD Controller"
    if len(request.args) == 0:
        session.error = T("Need to specify a bundle!")
        redirect(URL(r=request, f='bundle'))
    bundle = request.args[0]
    tables = [db.budget_bundle_kit, db.budget_bundle_item]
    authorised = shn_has_permission('update', tables[0]) and shn_has_permission('update', tables[1])
    
    title = db.budget_bundle[bundle].name
    bundle_description = db.budget_bundle[bundle].description
    bundle_total_cost = db.budget_bundle[bundle].total_unit_cost
    bundle_monthly_cost = db.budget_bundle[bundle].total_monthly_cost
    # Start building the Return with the common items
    output = dict(module_name=module_name, title=title, description=bundle_description, total_cost=bundle_total_cost, monthly_cost=bundle_monthly_cost)
    # Audit
    shn_audit_read(operation='list', resource='bundle_kit_item', record=bundle, representation='html')
    item_list = []
    even = True
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, 'bundle_kit_item', 'html')
        # Display a List_Create page with editable Quantities, Minutes & Megabytes
        
        # Kits
        query = tables[0].bundle_id==bundle
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.kit_id
            description = db.budget_kit[id].description
            id_link = A(id, _href=URL(r=request, f='kit', args=['read', id]))
            quantity_box = INPUT(_value=row.quantity, _size=4, _name='kit_qty_' + str(id))
            minute_cost = db.budget_kit[id].total_minute_cost
            if minute_cost:
                minutes_box = INPUT(_value=row.minutes, _size=4, _name='kit_mins_' + str(id))
            else:
                minutes_box = INPUT(_value=0, _size=4, _name='kit_mins_' + str(id), _disabled='disabled')
            megabyte_cost = db.budget_kit[id].total_megabyte_cost
            if megabyte_cost:
                megabytes_box = INPUT(_value=row.megabytes, _size=4, _name='kit_mbytes_' + str(id))
            else:
                megabytes_box = INPUT(_value=0, _size=4, _name='kit_mbytes_' + str(id), _disabled='disabled')
            unit_cost = db.budget_kit[id].total_unit_cost
            monthly_cost = db.budget_kit[id].total_monthly_cost
            minute_cost = db.budget_kit[id].total_minute_cost
            megabyte_cost = db.budget_kit[id].total_megabyte_cost
            total_units = unit_cost * row.quantity
            total_monthly = monthly_cost * row.quantity
            checkbox = INPUT(_type="checkbox", _value="on", _name='kit_' + str(id), _class="remove_item")
            item_list.append(TR(TD(id_link), TD(description, _align='left'), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(minutes_box), TD(minute_cost), TD(megabytes_box), TD(megabyte_cost), TD(total_units), TD(total_monthly), TD(checkbox, _align='center'), _class=theclass, _align='right'))
            
        # Items
        query = tables[1].bundle_id==bundle
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.item_id
            description = db.budget_item[id].description
            id_link = A(id, _href=URL(r=request, f='item', args=['read', id]))
            quantity_box = INPUT(_value=row.quantity, _size=4, _name='item_qty_' + str(id))
            minute_cost = db.budget_item[id].minute_cost
            if minute_cost:
                minutes_box = INPUT(_value=row.minutes, _size=4, _name='item_mins_' + str(id))
            else:
                minutes_box = INPUT(_value=0, _size=4, _name='item_mins_' + str(id), _disabled='disabled')
            megabyte_cost = db.budget_item[id].megabyte_cost
            if megabyte_cost:
                megabytes_box = INPUT(_value=row.megabytes, _size=4, _name='item_mbytes_' + str(id))
            else:
                megabytes_box = INPUT(_value=0, _size=4, _name='item_mbytes_' + str(id), _disabled='disabled')
            unit_cost = db.budget_item[id].unit_cost
            monthly_cost = db.budget_item[id].monthly_cost
            minute_cost = db.budget_item[id].minute_cost
            megabyte_cost = db.budget_item[id].megabyte_cost
            total_units = unit_cost * row.quantity
            total_monthly = monthly_cost * row.quantity
            checkbox = INPUT(_type="checkbox", _value="on", _name='item_' + str(id), _class="remove_item")
            item_list.append(TR(TD(id_link), TD(description, _align='left'), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(minutes_box), TD(minute_cost), TD(megabytes_box), TD(megabyte_cost), TD(total_units), TD(total_monthly), TD(checkbox, _align='center'), _class=theclass, _align='right'))
        
        table_header = THEAD(TR(TH('ID'), TH(T('Description')), TH(tables[0].quantity.label), TH(db.budget_item.unit_cost.label), TH(db.budget_item.monthly_cost.label), TH(tables[0].minutes.label), TH(db.budget_item.minute_cost.label), TH(tables[0].megabytes.label), TH(db.budget_item.megabyte_cost.label), TH(T('Total Units')), TH(T('Total Monthly')), TH(T('Remove'))))
        table_footer = TFOOT(TR(TD(B(T('Totals for Bundle:')), _colspan=9), TD(B(bundle_total_cost)), TD(B(bundle_monthly_cost)), TD(INPUT(_id='submit_button', _type='submit', _value=T('Update')))), _align='right')
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name='custom', _method='post', _enctype='multipart/form-data', _action=URL(r=request, f='bundle_update_items', args=[bundle])))
        subtitle = T("Contents")
        
        crud.messages.submit_button=T('Add')
        # Check for duplicates before Item is added to DB
        crud.settings.create_onvalidation = lambda form: bundle_dupes(form)
        # Calculate Totals for the Bundle after Item is added to DB
        crud.settings.create_onaccept = lambda form: bundle_total(form)
        crud.messages.record_created = T('Bundle Updated')
        form1 = crud.create(tables[0], next=URL(r=request, args=[bundle]))
        form1[0][0].append(TR(TD(T('Type:')), TD(LABEL(T('Kit'), INPUT(_type="radio", _name="kit_item1", _value="Kit", value="Kit")), LABEL(T('Item'), INPUT(_type="radio", _name="kit_item1", _value="Item", value="Kit")))))
        form2 = crud.create(tables[1], next=URL(r=request, args=[bundle]))
        form2[0][0].append(TR(TD(T('Type:')), TD(LABEL(T('Kit'), INPUT(_type="radio", _name="kit_item2", _value="Kit", value="Item")), LABEL(T('Item'), INPUT(_type="radio", _name="kit_item2", _value="Item", value="Item")))))
        addtitle = T("Add to Bundle")
        response.view = '%s/bundle_kit_item_list_create.html' % module
        output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form1=form1, form2=form2, bundle=bundle))
    else:
        # Display a simple List page
        # Kits
        query = tables[0].bundle_id==bundle
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.kit_id
            description = db.budget_kit[id].description
            id_link = A(id, _href=URL(r=request, f='kit', args=['read', id]))
            quantity_box = INPUT(_value=row.quantity, _size=4, _name='kit_qty_' + str(id))
            minute_cost = db.budget_kit[id].total_minute_cost
            if minute_cost:
                minutes_box = INPUT(_value=row.minutes, _size=4, _name='kit_mins_' + str(id))
            else:
                minutes_box = INPUT(_value=0, _size=4, _name='kit_mins_' + str(id), _disabled='disabled')
            megabyte_cost = db.budget_kit[id].total_megabyte_cost
            if megabyte_cost:
                megabytes_box = INPUT(_value=row.megabytes, _size=4, _name='kit_mbytes_' + str(id))
            else:
                megabytes_box = INPUT(_value=0, _size=4, _name='kit_mbytes_' + str(id), _disabled='disabled')
            unit_cost = db.budget_kit[id].total_unit_cost
            monthly_cost = db.budget_kit[id].total_monthly_cost
            minute_cost = db.budget_kit[id].total_minute_cost
            megabyte_cost = db.budget_kit[id].total_megabyte_cost
            total_units = unit_cost * row.quantity
            total_monthly = monthly_cost * row.quantity
            checkbox = INPUT(_type="checkbox", _value="on", _name='kit_' + str(id), _class="remove_item")
            item_list.append(TR(TD(id_link), TD(description, _align='left'), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(minutes_box), TD(minute_cost), TD(megabytes_box), TD(megabyte_cost), TD(total_units), TD(total_monthly), _class=theclass, _align='right'))
            
        # Items
        query = tables[1].bundle_id==bundle
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.item_id
            description = db.budget_item[id].description
            id_link = A(id, _href=URL(r=request, f='item', args=['read', id]))
            quantity_box = row.quantity
            minute_cost = db.budget_item[id].minute_cost
            minutes_box = row.minutes
            megabyte_cost = db.budget_item[id].megabyte_cost
            megabytes_box = row.megabytes
            unit_cost = db.budget_item[id].unit_cost
            monthly_cost = db.budget_item[id].monthly_cost
            minute_cost = db.budget_item[id].minute_cost
            megabyte_cost = db.budget_item[id].megabyte_cost
            total_units = unit_cost * row.quantity
            total_monthly = monthly_cost * row.quantity
            item_list.append(TR(TD(id_link), TD(description, _align='left'), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(minutes_box), TD(minute_cost), TD(megabytes_box), TD(megabyte_cost), TD(total_units), TD(total_monthly), _class=theclass, _align='right'))
        
        table_header = THEAD(TR(TH('ID'), TH(T('Description')), TH(tables[0].quantity.label), TH(db.budget_item.unit_cost.label), TH(db.budget_item.monthly_cost.label), TH(tables[0].minutes.label), TH(db.budget_item.minute_cost.label), TH(tables[0].megabytes.label), TH(db.budget_item.megabyte_cost.label), TH(T('Total Units')), TH(T('Total Monthly'))))
        table_footer = TFOOT(TR(TD(B(T('Totals for Bundle:')), _colspan=9), TD(B(bundle_total_cost)), TD(B(bundle_monthly_cost))), _align='right')
        items = DIV(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"))
        
        add_btn = A(T('Edit Contents'), _href=URL(r=request, c='default', f='user', args='login'), _id='add-btn')
        response.view = '%s/bundle_kit_item_list.html' % module
        output.update(dict(items=items, add_btn=add_btn))
    return output

def bundle_dupes(form):
    "Checks for duplicate Kit/Item before adding to DB"
    bundle = form.vars.bundle_id
    if 'kit_id' in form.vars:
        kit = form.vars.kit_id
        table = db.budget_bundle_kit
        query = (table.bundle_id==bundle) & (table.kit_id==kit)
    elif 'item_id' in form.vars:
        item = form.vars.item_id
        table = db.budget_bundle_item
        query = (table.bundle_id==bundle) & (table.item_id==item)
    else:
        # Something went wrong!
        return
    items = db(query).select()
    if items:
        session.error = T("Item already in Bundle!")
        redirect(URL(r=request, args=bundle))
    else:
        return
    
def bundle_total(form):
    "Calculate Totals for the Bundle specified by Form"
    if 'bundle_id' in form.vars:
        # called by bundle_kit_item()
        bundle = form.vars.bundle_id
    else:
        # called by bundle()
        bundle = form.vars.id
    bundle_totals(bundle)
    
def bundle_totals(bundle):
    "Calculate Totals for a Bundle"
    total_unit_cost = 0
    total_monthly_cost = 0
    
    table = db.budget_bundle_kit
    query = table.bundle_id==bundle
    kits = db(query).select()
    for kit in kits:
        query = (table.bundle_id==bundle) & (table.kit_id==kit.kit_id)
        total_unit_cost += (db(db.budget_kit.id==kit.kit_id).select()[0].total_unit_cost) * (db(query).select()[0].quantity)
        total_monthly_cost += (db(db.budget_kit.id==kit.kit_id).select()[0].total_monthly_cost) * (db(query).select()[0].quantity)
        total_monthly_cost += (db(db.budget_kit.id==kit.kit_id).select()[0].total_minute_cost) * (db(query).select()[0].quantity) * (db(query).select()[0].minutes)
        total_monthly_cost += (db(db.budget_kit.id==kit.kit_id).select()[0].total_megabyte_cost) * (db(query).select()[0].quantity) * (db(query).select()[0].megabytes)
    
    table = db.budget_bundle_item
    query = table.bundle_id==bundle
    items = db(query).select()
    for item in items:
        query = (table.bundle_id==bundle) & (table.item_id==item.item_id)
        total_unit_cost += (db(db.budget_item.id==item.item_id).select()[0].unit_cost) * (db(query).select()[0].quantity)
        total_monthly_cost += (db(db.budget_item.id==item.item_id).select()[0].monthly_cost) * (db(query).select()[0].quantity)
        total_monthly_cost += (db(db.budget_item.id==item.item_id).select()[0].minute_cost) * (db(query).select()[0].quantity) * (db(query).select()[0].minutes)
        total_monthly_cost += (db(db.budget_item.id==item.item_id).select()[0].megabyte_cost) * (db(query).select()[0].quantity) * (db(query).select()[0].megabytes)
    
    db(db.budget_bundle.id==bundle).update(total_unit_cost=total_unit_cost, total_monthly_cost=total_monthly_cost)

def bundle_update_items():
    "Update a Bundle's items (Quantity, Minutes, Megabytes & Delete)"
    if len(request.args) == 0:
        session.error = T("Need to specify a bundle!")
        redirect(URL(r=request, f='bundle'))
    bundle = request.args[0]
    tables = [db.budget_bundle_kit, db.budget_bundle_item]
    authorised = shn_has_permission('update', tables[0]) and shn_has_permission('update', tables[1])
    if authorised:
        for var in request.vars:
            if 'kit' in var:
                if 'qty' in var:
                    kit = var[8:]
                    quantity = request.vars[var]
                    query = (tables[0].bundle_id==bundle) & (tables[0].kit_id==kit)
                    db(query).update(quantity=quantity)
                elif 'mins' in var:
                    kit = var[9:]
                    minutes = request.vars[var]
                    query = (tables[0].bundle_id==bundle) & (tables[0].kit_id==kit)
                    db(query).update(minutes=minutes)
                elif 'mbytes' in var:
                    kit = var[11:]
                    megabytes = request.vars[var]
                    query = (tables[0].bundle_id==bundle) & (tables[0].kit_id==kit)
                    db(query).update(megabytes=megabytes)
                else:
                    # Delete
                    kit = var[4:]
                    query = (tables[0].bundle_id==bundle) & (tables[0].kit_id==kit)
                    db(query).delete()
            if 'item' in var:
                if 'qty' in var:
                    item = var[9:]
                    quantity = request.vars[var]
                    query = (tables[1].bundle_id==bundle) & (tables[1].item_id==item)
                    db(query).update(quantity=quantity)
                elif 'mins' in var:
                    item = var[10:]
                    minutes = request.vars[var]
                    query = (tables[1].bundle_id==bundle) & (tables[1].item_id==item)
                    db(query).update(minutes=minutes)
                elif 'mbytes' in var:
                    item = var[12:]
                    megabytes = request.vars[var]
                    query = (tables[1].bundle_id==bundle) & (tables[1].item_id==item)
                    db(query).update(megabytes=megabytes)
                else:
                    # Delete
                    item = var[5:]
                    query = (tables[1].bundle_id==bundle) & (tables[1].item_id==item)
                    db(query).delete()
        # Update the Total values
        bundle_totals(bundle)
        # Audit
        shn_audit_update_m2m(resource='bundle_kit_item', record=bundle, representation='html')
        session.flash = T("Bundle updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(r=request, f='bundle_kit_item', args=[bundle]))

def staff():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'staff')
def location():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'location', main='code')
def project():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'project', main='code')
def budget():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'budget')

def budget_staff_bundle():
    "Many to Many CRUD Controller"
    if len(request.args) == 0:
        session.error = T("Need to specify a Budget!")
        redirect(URL(r=request, f='budget'))
    budget = request.args[0]
    tables = [db.budget_budget_staff, db.budget_budget_bundle]
    authorised = shn_has_permission('update', tables[0]) and shn_has_permission('update', tables[1])
    
    title = db.budget_budget[budget].name
    budget_description = db.budget_budget[budget].description
    budget_onetime_cost = db.budget_budget[budget].total_onetime_costs
    budget_recurring_cost = db.budget_budget[budget].total_recurring_costs
    # Start building the Return with the common items
    output = dict(module_name=module_name, title=title, description=budget_description, onetime_cost=budget_onetime_cost, recurring_cost=budget_recurring_cost)
    # Audit
    shn_audit_read(operation='list', resource='budget_staff_bundle', record=budget, representation='html')
    item_list = []
    even = True
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, 'budget_staff_bundle', 'html')
        # Display a List_Create page with editable Quantities & Months
        
        # Staff
        query = tables[0].budget_id==budget
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.staff_id
            name = db.budget_staff[id].name
            id_link = A(name, _href=URL(r=request, f='staff', args=['read', id]))
            location = db.budget_location[row.location_id].code
            location_link = A(location, _href=URL(r=request, f='location', args=['read', row.location_id]))
            project = db.budget_project[row.project_id].code
            project_link = A(project, _href=URL(r=request, f='project', args=['read', row.project_id]))
            description = db.budget_staff[id].comments
            quantity_box = INPUT(_value=row.quantity, _size=4, _name='staff_qty_' + str(id))
            months_box = INPUT(_value=row.months, _size=4, _name='staff_months_' + str(id))
            salary = db.budget_staff[id].salary
            travel = db.budget_staff[id].travel
            onetime = travel * row.quantity
            recurring = salary * row.quantity
            checkbox = INPUT(_type="checkbox", _value="on", _name='staff_' + str(id), _class="remove_item")
            item_list.append(TR(TD(location_link), TD(project_link), TD(id_link), TD(description, _align='left'), TD(quantity_box), TD(travel), TD(salary), TD(months_box), TD(onetime), TD(recurring), TD(checkbox, _align='center'), _class=theclass, _align='right'))
            
        # Bundles
        query = tables[1].budget_id==budget
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.bundle_id
            name = db.budget_bundle[id].name
            id_link = A(name, _href=URL(r=request, f='bundle', args=['read', id]))
            location = db.budget_location[row.location_id].code
            location_link = A(location, _href=URL(r=request, f='location', args=['read', row.location_id]))
            project = db.budget_project[row.project_id].code
            project_link = A(project, _href=URL(r=request, f='project', args=['read', row.project_id]))
            description = db.budget_bundle[id].description
            quantity_box = INPUT(_value=row.quantity, _size=4, _name='bundle_qty_' + str(id))
            months_box = INPUT(_value=row.months, _size=4, _name='bundle_months_' + str(id))
            unit_cost = db.budget_bundle[id].total_unit_cost
            monthly_cost = db.budget_bundle[id].total_monthly_cost
            onetime = unit_cost * row.quantity
            recurring = monthly_cost * row.months
            checkbox = INPUT(_type="checkbox", _value="on", _name='bundle_' + str(id), _class="remove_item")
            item_list.append(TR(TD(location_link), TD(project_link), TD(id_link), TD(description, _align='left'), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(months_box), TD(onetime), TD(recurring), TD(checkbox, _align='center'), _class=theclass, _align='right'))
        
        table_header = THEAD(TR(TH('Location'), TH('Project'), TH('Item'), TH(T('Description')), TH(tables[0].quantity.label), TH(T('One-time costs')), TH(T('Recurring costs')), TH(tables[0].months.label), TH(db.budget_budget.total_onetime_costs.label), TH(db.budget_budget.total_recurring_costs.label), TH(T('Remove'))))
        table_footer = TFOOT(TR(TD(B(T('Totals for Budget:')), _colspan=8), TD(B(budget_onetime_cost)), TD(B(budget_recurring_cost)), TD(INPUT(_id='submit_button', _type='submit', _value=T('Update')))), _align='right')
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name='custom', _method='post', _enctype='multipart/form-data', _action=URL(r=request, f='budget_update_items', args=[budget])))
        subtitle = T("Contents")
        
        crud.messages.submit_button=T('Add')
        # Check for duplicates before Item is added to DB
        crud.settings.create_onvalidation = lambda form: budget_dupes(form)
        # Calculate Totals for the budget after Item is added to DB
        crud.settings.create_onaccept = lambda form: budget_total(form)
        crud.messages.record_created = T('Budget Updated')
        form1 = crud.create(tables[0], next=URL(r=request, args=[budget]))
        form1[0][0].append(TR(TD(T('Type:')), TD(LABEL(T('Staff'), INPUT(_type="radio", _name="staff_bundle1", _value="Staff", value="Staff")), LABEL(T('Bundle'), INPUT(_type="radio", _name="staff_bundle1", _value="Bundle", value="Staff")))))
        form2 = crud.create(tables[1], next=URL(r=request, args=[budget]))
        form2[0][0].append(TR(TD(T('Type:')), TD(LABEL(T('Staff'), INPUT(_type="radio", _name="staff_bundle2", _value="Staff", value="Bundle")), LABEL(T('Bundle'), INPUT(_type="radio", _name="staff_bundle2", _value="Bundle", value="Bundle")))))
        addtitle = T("Add to budget")
        response.view = '%s/budget_staff_bundle_list_create.html' % module
        output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form1=form1, form2=form2, budget=budget))
    else:
        # Display a simple List page
        # Staff
        query = tables[0].budget_id==budget
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.staff_id
            name = db.budget_staff[id].name
            id_link = A(name, _href=URL(r=request, f='staff', args=['read', id]))
            location = db.budget_location[row.location_id].code
            location_link = A(location, _href=URL(r=request, f='location', args=['read', row.location_id]))
            project = db.budget_project[row.project_id].code
            project_link = A(project, _href=URL(r=request, f='project', args=['read', row.project_id]))
            description = db.budget_staff[id].comments
            quantity_box = INPUT(_value=row.quantity, _size=4, _name='staff_qty_' + str(id))
            months_box = INPUT(_value=row.months, _size=4, _name='staff_mins_' + str(id))
            salary = db.budget_staff[id].salary
            travel = db.budget_staff[id].travel
            onetime = travel * row.quantity
            recurring = salary * row.quantity
            checkbox = INPUT(_type="checkbox", _value="on", _name='staff_' + str(id), _class="remove_item")
            item_list.append(TR(TD(location_link), TD(project_link), TD(id_link), TD(description, _align='left'), TD(quantity_box), TD(travel), TD(salary), TD(months_box), TD(onetime), TD(recurring), _class=theclass, _align='right'))
            
        # Bundles
        query = tables[1].budget_id==budget
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.bundle_id
            name = db.budget_bundle[id].name
            id_link = A(name, _href=URL(r=request, f='bundle', args=['read', id]))
            location = db.budget_location[row.location_id].code
            location_link = A(location, _href=URL(r=request, f='location', args=['read', row.location_id]))
            project = db.budget_project[row.project_id].code
            project_link = A(project, _href=URL(r=request, f='project', args=['read', row.project_id]))
            description = db.budget_bundle[id].description
            quantity_box = row.quantity
            months_box = row.months
            unit_cost = db.budget_bundle[id].total_unit_cost
            monthly_cost = db.budget_bundle[id].total_monthly_cost
            onetime = unit_cost * row.quantity
            recurring = monthly_cost * row.months
            item_list.append(TR(TD(location_link), TD(project_link), TD(id_link), TD(description, _align='left'), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(months_box), TD(onetime), TD(recurring), _class=theclass, _align='right'))
        
        table_header = THEAD(TR(TH('Location'), TH('Project'), TH('Item'), TH(T('Description')), TH(tables[0].quantity.label), TH(T('One-time costs')), TH(T('Recurring costs')), TH(tables[0].months.label), TH(db.budget_budget.total_onetime_costs.label), TH(db.budget_budget.total_recurring_costs.label)))
        table_footer = TFOOT(TR(TD(B(T('Totals for Budget:')), _colspan=8), TD(B(budget_onetime_cost)), TD(B(budget_recurring_cost))), _align='right')
        items = DIV(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"))
        
        add_btn = A(T('Edit Contents'), _href=URL(r=request, c='default', f='user', args='login'), _id='add-btn')
        response.view = '%s/budget_staff_bundle_list.html' % module
        output.update(dict(items=items, add_btn=add_btn))
    return output

def budget_dupes(form):
    "Checks for duplicate staff/bundle before adding to DB"
    budget = form.vars.budget_id
    if 'staff_id' in form.vars:
        staff = form.vars.staff_id
        table = db.budget_budget_staff
        query = (table.budget_id==budget) & (table.staff_id==staff)
    elif 'bundle_id' in form.vars:
        bundle = form.vars.bundle_id
        table = db.budget_budget_bundle
        query = (table.budget_id==budget) & (table.bundle_id==bundle)
    else:
        # Something went wrong!
        return
    items = db(query).select()
    if items:
        session.error = T("Item already in budget!")
        redirect(URL(r=request, args=budget))
    else:
        return
    
def budget_total(form):
    "Calculate Totals for the budget specified by Form"
    if 'budget_id' in form.vars:
        # called by budget_staff_bundle()
        budget = form.vars.budget_id
    else:
        # called by budget()
        budget = form.vars.id
    budget_totals(budget)
    
def budget_totals(budget):
    "Calculate Totals for a budget"
    total_onetime_cost = 0
    total_recurring_cost = 0
    
    table = db.budget_budget_staff
    query = table.budget_id==budget
    staffs = db(query).select()
    for staff in staffs:
        query = (table.budget_id==budget) & (table.staff_id==staff.staff_id)
        total_onetime_cost += (db(db.budget_staff.id==staff.staff_id).select()[0].travel) * (db(query).select()[0].quantity)
        total_recurring_cost += (db(db.budget_staff.id==staff.staff_id).select()[0].salary) * (db(query).select()[0].quantity) * (db(query).select()[0].months)
        total_recurring_cost += (db(db.budget_location.id==staff.location_id).select()[0].subsistence) * (db(query).select()[0].quantity) * (db(query).select()[0].months)
        total_recurring_cost += (db(db.budget_location.id==staff.location_id).select()[0].hazard_pay) * (db(query).select()[0].quantity) * (db(query).select()[0].months)
        
    table = db.budget_budget_bundle
    query = table.budget_id==budget
    bundles = db(query).select()
    for bundle in bundles:
        query = (table.budget_id==budget) & (table.bundle_id==bundle.bundle_id)
        total_onetime_cost += (db(db.budget_bundle.id==bundle.bundle_id).select()[0].total_unit_cost) * (db(query).select()[0].quantity)
        total_recurring_cost += (db(db.budget_bundle.id==bundle.bundle_id).select()[0].total_monthly_cost) * (db(query).select()[0].quantity) * (db(query).select()[0].months)
        
    db(db.budget_budget.id==budget).update(total_onetime_costs=total_onetime_cost, total_recurring_costs=total_recurring_cost)

def budget_update_items():
    "Update a Budget's items (Quantity, Months & Delete)"
    if len(request.args) == 0:
        session.error = T("Need to specify a budget!")
        redirect(URL(r=request, f='budget'))
    budget = request.args[0]
    tables = [db.budget_budget_staff, db.budget_budget_bundle]
    authorised = shn_has_permission('update', tables[0]) and shn_has_permission('update', tables[1])
    if authorised:
        for var in request.vars:
            if 'staff' in var:
                if 'qty' in var:
                    staff = var[10:]
                    quantity = request.vars[var]
                    query = (tables[0].budget_id==budget) & (tables[0].staff_id==staff)
                    db(query).update(quantity=quantity)
                elif 'months' in var:
                    staff = var[13:]
                    months = request.vars[var]
                    query = (tables[0].budget_id==budget) & (tables[0].staff_id==staff)
                    db(query).update(months=months)
                else:
                    # Delete
                    staff = var[6:]
                    query = (tables[0].budget_id==budget) & (tables[0].staff_id==staff)
                    db(query).delete()
            if 'bundle' in var:
                if 'qty' in var:
                    bundle = var[11:]
                    quantity = request.vars[var]
                    query = (tables[1].budget_id==budget) & (tables[1].bundle_id==bundle)
                    db(query).update(quantity=quantity)
                elif 'months' in var:
                    bundle = var[14:]
                    months = request.vars[var]
                    query = (tables[1].budget_id==budget) & (tables[1].bundle_id==bundle)
                    db(query).update(months=months)
                else:
                    # Delete
                    bundle = var[7:]
                    query = (tables[1].budget_id==budget) & (tables[1].bundle_id==bundle)
                    db(query).delete()
        # Update the Total values
        budget_totals(budget)
        # Audit
        shn_audit_update_m2m(resource='budget_staff_bundle', record=budget, representation='html')
        session.flash = T("Budget updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(r=request, f='budget_staff_bundle', args=[budget]))