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
    [T('Staff Types'), False, URL(r=request, f='staff_type')],
    [T('Locations'), False, URL(r=request, f='location')],
    [T('Projects'), False, URL(r=request, f='project')],
    [T('Budgets'), False, URL(r=request, f='budget')],
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
    return shn_rest_controller(module, 'item', main='code')

def kit():
    "RESTlike CRUD controller"
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
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, 'kit_item', 'html')
        # Display a List_Create page with editable Quantities
        item_list = []
        sqlrows = db(query).select()
        even = True
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
        return output
    else:
        # Display a simple List page
        table.kit_id.readable = False
        fields = [table[f] for f in table.fields if table[f].readable]
        headers = {}
        for field in fields:
            # Use custom or prettified label
            headers[str(field)] = field.label
        linkto = URL(r=request, f='item', args='read')
        id = 'item_id'
        items = crud.select(table, query=query, fields=fields, headers=headers, linkto=linkto, id=id)
        response.view = '%s/kit_item_list.html' % module
        output.update(dict(items=items))
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

def bundle():
    "RESTlike CRUD controller"
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
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, 'bundle_kit_item', 'html')
        # Display a List_Create page with editable Quantities, Minutes & Megabytes
        item_list = []
        
        # Kits
        query = tables[0].bundle_id==bundle
        sqlrows = db(query).select()
        even = True
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
        form1[0][0].append(TR(TD(T('Type:')),TD(SELECT(OPTION(T('Kit')), OPTION(T('Item')), _id="kit_item1"))))
        form2 = crud.create(tables[1], next=URL(r=request, args=[bundle]))
        form2[0][0].append(TR(TD(T('Type:')),TD(SELECT(OPTION(T('Kit')), OPTION(T('Item')), _id="kit_item2"))))
        addtitle = T("Add to Bundle")
        response.view = '%s/bundle_kit_item_list_create.html' % module
        output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form1=form1, form2=form2, bundle=bundle))
        return output
    else:
        # Display a simple List page
        table = tables[0]
        query = table.bundle_id==bundle
        table.bundle_id.readable = False
        fields = [table[f] for f in table.fields if table[f].readable]
        headers = {}
        for field in fields:
            # Use custom or prettified label
            headers[str(field)] = field.label
        linkto = URL(r=request, f='kit', args='read')
        id = 'kit_id'
        items1 = crud.select(table, query=query, fields=fields, headers=headers, linkto=linkto, id=id)
        
        table = tables[1]
        query = table.bundle_id==bundle
        table.bundle_id.readable = False
        fields = [table[f] for f in table.fields if table[f].readable]
        headers = {}
        for field in fields:
            # Use custom or prettified label
            headers[str(field)] = field.label
        linkto = URL(r=request, f='item', args='read')
        id = 'item_id'
        items2 = crud.select(table, query=query, fields=fields, headers=headers, linkto=linkto, id=id)
        
        response.view = '%s/bundle_kit_item_list.html' % module
        output.update(dict(items1=items1, items2=items2))
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
                    item = var[4:]
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

def staff_type():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'staff_type')
def location():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'location', main='code')
def project():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'project', main='code')
def budget():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'budget')
def budget_equipment():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'budget_equipment')
def budget_staff():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'budget_staff')
