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
    table=db.budget_parameter
    authorised = has_permission('update', table)
    if authorised:
        redirect (URL(r=request, f='parameter', args=['update',1]))
    else:
        redirect (URL(r=request, f='parameter', args=['read',1]))
def parameter():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'parameter', deletable=False)
def item():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'item', main='code', format='table')
def kit():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'kit', main='code', format='table')

def kit_item():
    "Many to Many CRUD Controller"
    if len(request.args) == 0:
        session.error = T("Need to specify a kit!")
        redirect(URL(r=request, f='kit'))
    kit = request.args[0]
    table = db.budget_kit_item
    
    # Is user authorised to Update?
    authorised = has_permission('update', table)
    
    title = db.budget_kit[kit].code
    description = db.budget_kit[kit].description
    total_cost = db.budget_kit[kit].total_unit_cost
    monthly_cost = db.budget_kit[kit].total_monthly_cost
    query = table.kit_id==kit
    # Start building the Return with the common items
    output = dict(module_name=module_name, title=title, description=description, total_cost=total_cost, monthly_cost=monthly_cost)
    if session.s3.audit_read:
            db.s3_audit.insert(
                person = auth.user.id if session.auth else 0,
                operation = 'list',
                module = module,
                resource = 'kit_item',
                record = kit
            )
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, 'kit_item', 'html')
        # Display a List_Create page with editable Quantities
        item_list = []
        sqlrows = db(query).select()
        forms = Storage()
        even = True
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.item_id
            item_description = db.budget_item[id].description
            id_link = A(id, _href=URL(r=request, f='item', args=['read', id]))
            quantity_box = INPUT(_value=row.quantity, _size=4, _name='qty'+str(id))
            checkbox = INPUT(_type="checkbox", _value="on", _name=id, _class="remove_item")
            item_list.append(TR(TD(id_link), TD(item_description), TD(quantity_box), TD(checkbox), _class=theclass))
            
        table_header = THEAD(TR(TH('ID'), TH(table.item_id.label), TH(table.quantity.label), TH(T('Delete'))))
        table_footer = TFOOT(TR(TD(_colspan=3), TD(INPUT(_id='submit_button', _type='submit', _value=T('Update')))))
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name='custom', _method='post', _enctype='multipart/form-data', _action=URL(r=request, f='kit_update_items', args=[kit])))
        subtitle = T("Contents")
        
        crud.messages.submit_button=T('Add')
        # Calculate Totals for the Kit after Item is added
        crud.settings.create_onaccept = lambda form: kit_total(form)
        crud.messages.record_created = T('Kit Updated')
        form = crud.create(table,next=URL(r=request, args=[kit]))
        addtitle = T("Add New Item to Kit")
        response.view = '%s/kit_item_list_create.html' % module
        output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form=form, kit=kit))
        return output
    else:
        # Audit
        shn_audit_read(operation='list', resource='kit_item', representation='html')
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

def kit_total(form):
    "Calculate Totals for the Kit specified by Form"
    kit = form.vars.kit_id
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
    authorised = has_permission('update', table)
    if authorised:
        for var in request.vars:
            if 'qty' in var:
                item = var[3:]
                quantity = request.vars[var]
                query = (table.kit_id==kit) & (table.item_id==item)
                db(query).update(quantity=quantity)
            else:
                item = var
                query = (table.kit_id==kit) & (table.item_id==item)
                db(query).delete()
        # Update the Total values
        kit_totals(kit)
        # Audit
        #crud.settings.update_onaccept = lambda form: shn_audit_update(form, 'kit_item', 'html')
        session.flash = T("Kit updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(r=request, f='kit_item', args=[kit]))

def bundle():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'bundle')
def staff_type():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'staff_type')
def location():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'location', main='code')
def project():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'project', main='code', extra='title')
def budget():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'budget')
def budget_equipment():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'budget_equipment')
def budget_staff():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'budget_staff')
