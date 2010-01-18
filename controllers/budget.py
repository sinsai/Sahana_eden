# -*- coding: utf-8 -*-

module = 'budget'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select().first().name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Parameters'), False, URL(r=request, f='parameters')],
    [T('Items'), False, URL(r=request, f='item')],
    [T('Kits'), False, URL(r=request, f='kit')],
    [T('Bundles'), False, URL(r=request, f='bundle')],
    [T('Staff'), False, URL(r=request, f='staff')],
    [T('Locations'), False, URL(r=request, f='location')],
    [T('Projects'), False, URL(r=request, f='project')],
    [T('Budgets'), False, URL(r=request, f='budget')]
]

# Options used in multiple functions
table = 'budget_item'
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.label = T('Code')
db[table].code.comment = SPAN("*", _class="req")
db[table].description.requires = IS_NOT_EMPTY()
db[table].description.label = T('Description')
db[table].description.comment = SPAN("*", _class="req")
db[table].unit_cost.label = T('Unit Cost')
db[table].monthly_cost.label = T('Monthly Cost')
db[table].minute_cost.label = T('Cost per Minute')
db[table].megabyte_cost.label = T('Cost per Megabyte')
db[table].comments.label = T('Comments')

table = 'budget_kit'
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.label = T('Code')
db[table].code.comment = SPAN("*", _class="req")
db[table].description.label = T('Description')
db[table].total_unit_cost.label = T('Total Unit Cost')
db[table].total_monthly_cost.label = T('Total Monthly Cost')
db[table].total_minute_cost.label = T('Total Cost per Minute')
db[table].total_megabyte_cost.label = T('Total Cost per Megabyte')
db[table].comments.label = T('Comments')

table = 'budget_kit_item'
db[table].kit_id.requires = IS_ONE_OF(db, 'budget_kit.id', '%(code)s')
db[table].kit_id.label = T('Kit')
db[table].kit_id.represent = lambda kit_id: db(db.budget_kit.id==kit_id).select().first().code
db[table].item_id.requires = IS_ONE_OF(db, 'budget_item.id', '%(description)s')
db[table].item_id.label = T('Item')
db[table].item_id.represent = lambda item_id: db(db.budget_item.id==item_id).select().first().description
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")

table = 'budget_bundle'
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].description.label = T('Description')
db[table].total_unit_cost.label = T('One time cost')
db[table].total_monthly_cost.label = T('Recurring cost')
db[table].comments.label = T('Comments')

table = 'budget_bundle_kit'
db[table].bundle_id.requires = IS_ONE_OF(db, 'budget_bundle.id', '%(description)s')
db[table].bundle_id.label = T('Bundle')
db[table].bundle_id.represent = lambda bundle_id: db(db.budget_bundle.id==bundle_id).select().first().description
db[table].kit_id.requires = IS_ONE_OF(db, 'budget_kit.id', '%(code)s')
db[table].kit_id.label = T('Kit')
db[table].kit_id.represent = lambda kit_id: db(db.budget_kit.id==kit_id).select().first().code
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")
db[table].minutes.requires = IS_NOT_EMPTY()
db[table].minutes.label = T('Minutes per Month')
db[table].minutes.comment = SPAN("*", _class="req")
db[table].megabytes.requires = IS_NOT_EMPTY()
db[table].megabytes.label = T('Megabytes per Month')
db[table].megabytes.comment = SPAN("*", _class="req")

table = 'budget_bundle_item'
db[table].bundle_id.requires = IS_ONE_OF(db, 'budget_bundle.id', '%(description)s')
db[table].bundle_id.label = T('Bundle')
db[table].bundle_id.represent = lambda bundle_id: db(db.budget_bundle.id==bundle_id).select().first().description
db[table].item_id.requires = IS_ONE_OF(db, 'budget_item.id', '%(description)s')
db[table].item_id.label = T('Item')
db[table].item_id.represent = lambda item_id: db(db.budget_item.id==item_id).select().first().description
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")
db[table].minutes.requires = IS_NOT_EMPTY()
db[table].minutes.label = T('Minutes per Month')
db[table].minutes.comment = SPAN("*", _class="req")
db[table].megabytes.requires = IS_NOT_EMPTY()
db[table].megabytes.label = T('Megabytes per Month')
db[table].megabytes.comment = SPAN("*", _class="req")

table = 'budget_staff'
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].grade.requires = IS_NOT_EMPTY()
db[table].grade.label = T('Grade')
db[table].grade.comment = SPAN("*", _class="req")
db[table].salary.requires = IS_NOT_EMPTY()
db[table].salary.label = T('Monthly Salary')
db[table].salary.comment = SPAN("*", _class="req")
db[table].travel.label = T('Travel Cost')
db[table].comments.label = T('Comments')

table = 'budget_location'
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.label = T('Code')
db[table].code.comment = SPAN("*", _class="req")
db[table].description.label = T('Description')
db[table].subsistence.label = T('Subsistence Cost')
# UN terminology
#db[table].subsistence.label = "DSA"
db[table].hazard_pay.label = T('Hazard Pay')
db[table].comments.label = T('Comments')

table = 'budget_project'
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.label = T('Code')
db[table].code.comment = SPAN("*", _class="req")
db[table].title.label = T('Title')
db[table].comments.label = T('Comments')

table = 'budget_budget'
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].description.label = T('Description')
db[table].total_onetime_costs.label = T('Total One-time Costs')
db[table].total_recurring_costs.label = T('Total Recurring Costs')
db[table].comments.label = T('Comments')

table = 'budget_budget_bundle'
db[table].budget_id.requires = IS_ONE_OF(db, 'budget_budget.id', '%(name)s')
db[table].budget_id.label = T('Budget')
db[table].budget_id.represent = lambda budget_id: db(db.budget_budget.id==budget_id).select().first().name
db[table].project_id.requires = IS_ONE_OF(db,'budget_project.id', '%(code)s')
db[table].project_id.label = T('Project')
db[table].project_id.represent = lambda project_id: db(db.budget_project.id==project_id).select().first().code
db[table].location_id.requires = IS_ONE_OF(db, 'budget_location.id', '%(code)s')
db[table].location_id.label = T('Location')
db[table].location_id.represent = lambda location_id: db(db.budget_location.id==location_id).select().first().code
db[table].bundle_id.requires = IS_ONE_OF(db, 'budget_bundle.id', '%(name)s')
db[table].bundle_id.label = T('Bundle')
db[table].bundle_id.represent = lambda bundle_id: db(db.budget_bundle.id==bundle_id).select().first().name
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")
db[table].months.requires = IS_NOT_EMPTY()
db[table].months.label = T('Months')
db[table].months.comment = SPAN("*", _class="req")

table = 'budget_budget_staff'
db[table].budget_id.requires = IS_ONE_OF(db, 'budget_budget.id', '%(name)s')
db[table].budget_id.label = T('Budget')
db[table].budget_id.represent = lambda budget_id: db(db.budget_budget.id==budget_id).select().first().name
db[table].project_id.requires = IS_ONE_OF(db,'budget_project.id', '%(code)s')
db[table].project_id.label = T('Project')
db[table].project_id.represent = lambda project_id: db(db.budget_project.id==project_id).select().first().code
db[table].location_id.requires = IS_ONE_OF(db, 'budget_location.id', '%(code)s')
db[table].location_id.label = T('Location')
db[table].location_id.represent = lambda location_id: db(db.budget_location.id==location_id).select().first().code
db[table].staff_id.requires = IS_ONE_OF(db, 'budget_staff.id', '%(name)s')
db[table].staff_id.label = T('Staff')
db[table].staff_id.represent = lambda bundle_id: db(db.budget_staff.id==staff_id).select().first().description
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")
db[table].months.requires = IS_NOT_EMPTY()
db[table].months.label = T('Months')
db[table].months.comment = SPAN("*", _class="req")

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
    resource = 'parameter'
    table = module + '_' + resource
    
    # Model Options
    db[table].shipping.requires = IS_FLOAT_IN_RANGE(0, 100)
    db[table].shipping.label = "Shipping cost"
    db[table].logistics.requires = IS_FLOAT_IN_RANGE(0, 100)
    db[table].logistics.label = "Procurement & Logistics cost"
    db[table].admin.requires = IS_FLOAT_IN_RANGE(0, 100)
    db[table].admin.label = "Administrative support cost"
    db[table].indirect.requires = IS_FLOAT_IN_RANGE(0, 100)
    db[table].indirect.label = "Indirect support cost HQ"

    # CRUD Strings
    title_update = T('Edit Parameters')
    s3.crud_strings[table] = Storage(title_update=title_update)

    return shn_rest_controller(module, resource, deletable=False)
    
def item():
    "RESTlike CRUD controller"
    resource = 'item'
    table = module + '_' + resource

    # Model options used in multiple controllers so defined at the top of the file
    
    # CRUD Strings
    title_create = T('Add Item')
    title_display = T('Item Details')
    title_list = T('List Items')
    title_update = T('Edit Item')
    title_search = T('Search Items')
    subtitle_create = T('Add New Item')
    subtitle_list = T('Items')
    label_list_button = T('List Items')
    label_create_button = T('Add Item')
    label_search_button = T('Search Items')
    msg_record_created = T('Item added')
    msg_record_modified = T('Item updated')
    msg_record_deleted = T('Item deleted')
    msg_list_empty = T('No Items currently registered')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

    response.s3.pdf = URL(r=request, f='item_export_pdf')
    
    return shn_rest_controller(module, resource, main='code', extra='description', orderby=db.budget_item.category_type, sortby=[[1, "asc"]], onaccept=lambda form: item_cascade(form))
    #return shn_rest_controller(module, resource, main='code', extra='description', orderby=db.budget_item.category_type, onaccept=lambda form: item_cascade(form))

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

def item_export_pdf():
    """
    Export a list of Items in Adobe PDF format
    Uses Geraldo Grouping Report
    """
    try:
        from reportlab.lib.units import cm
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    except ImportError:
        session.error = T('ReportLab module not available within the running Python - this needs installing to do PDF Reporting!')
        redirect(URL(r=request, c='item'))
    try:
        from geraldo import Report, ReportBand, ReportGroup, Label, ObjectValue, SystemField, landscape, BAND_WIDTH
        from geraldo.generators import PDFGenerator
    except ImportError:
        session.error = T('Geraldo module not available within the running Python - this needs installing to do PDF Reporting!')
        redirect(URL(r=request, c='item'))

    table = db.budget_item
    objects_list = db(table.id > 0).select(orderby=table.category_type)
    if not objects_list:
        session.warning = T('No data in this table - cannot create PDF!')
        redirect(URL(r=request, f='item'))
    
    import StringIO
    output = StringIO.StringIO()
    
    class MyReport(Report):
        def __init__(self, queryset=None, T=None):
            " Initialise parent class & make any necessary modifications "
            Report.__init__(self, queryset)
            self.T = T
        def _T(self, rawstring):
            return self.T(rawstring)
        # can't use T() here!
        #title = _T("Items")
        title = "Items"
        page_size = landscape(A4)
        class band_page_header(ReportBand):
            height = 1.3*cm
            elements = [
                SystemField(expression='%(report_title)s', top=0.1*cm,
                    left=0, width=BAND_WIDTH, style={'fontName': 'Helvetica-Bold',
                    'fontSize': 14, 'alignment': TA_CENTER}
                    ),
                Label(text="Code", top=0.8*cm, left=0.2*cm),
                Label(text="Description", top=0.8*cm, left=3*cm),
                Label(text="Unit Cost", top=0.8*cm, left=13*cm),
                Label(text="per Month", top=0.8*cm, left=15*cm),
                Label(text="per Minute", top=0.8*cm, left=17*cm),
                Label(text="per Megabyte", top=0.8*cm, left=19*cm),
                Label(text="Comments", top=0.8*cm, left=21*cm),
            ]
            borders = {'bottom': True}
        class band_page_footer(ReportBand):
            height = 0.5*cm
            elements = [
                Label(text='%s' % request.utcnow.date(), top=0.1*cm, left=0),
                SystemField(expression='Page # %(page_number)d of %(page_count)d', top=0.1*cm,
                    width=BAND_WIDTH, style={'alignment': TA_RIGHT}),
            ]
            borders = {'top': True}
        class band_detail(ReportBand):
            height = 0.5*cm
            auto_expand_height = True
            elements = (
                    ObjectValue(attribute_name='code', left=0.2*cm, width=2.8*cm),
                    ObjectValue(attribute_name='description', left=3*cm, width=10*cm),
                    ObjectValue(attribute_name='unit_cost', left=13*cm, width=2*cm),
                    ObjectValue(attribute_name='monthly_cost', left=15*cm, width=2*cm),
                    ObjectValue(attribute_name='minute_cost', left=17*cm, width=2*cm),
                    ObjectValue(attribute_name='megabyte_cost', left=19*cm, width=2*cm),
                    ObjectValue(attribute_name='comments', left=21*cm, width=6*cm),
                    )
        groups = [
        ReportGroup(attribute_name='category_type',
            band_header=ReportBand(
                height=0.7*cm,
                elements=[
                    ObjectValue(attribute_name='category_type', left=0, top=0.1*cm,
                        get_value=lambda instance: instance.category_type and budget_category_type_opts[instance.category_type],
                        style={'fontName': 'Helvetica-Bold', 'fontSize': 12})
                ],
                borders={'bottom': True},
            ),
        ),
    ]

    #report = MyReport(queryset=objects_list)
    report = MyReport(queryset=objects_list, T=T)
    report.generate_by(PDFGenerator, filename=output)

    output.seek(0)
    import gluon.contenttype
    response.headers['Content-Type'] = gluon.contenttype.contenttype('.pdf')
    filename = "%s_items.pdf" % (request.env.server_name)
    response.headers['Content-disposition'] = "attachment; filename=\"%s\"" % filename
    return output.read()
    
def kit():
    "RESTlike CRUD controller"
    resource = 'kit'
    table = module + '_' + resource

    # Model options used in multiple controllers so defined at the top of the file
    
    # CRUD Strings
    title_create = T('Add Kit')
    title_display = T('Kit Details')
    title_list = T('List Kits')
    title_update = T('Edit Kit')
    title_search = T('Search Kits')
    subtitle_create = T('Add New Kit')
    subtitle_list = T('Kits')
    label_list_button = T('List Kits')
    label_create_button = T('Add Kit')
    msg_record_created = T('Kit added')
    msg_record_modified = T('Kit updated')
    msg_record_deleted = T('Kit deleted')
    msg_list_empty = T('No Kits currently registered')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

    response.s3.pdf = URL(r=request, f='kit_export_pdf')
    response.s3.xls = URL(r=request, f='kit_export_xls')
    if len(request.args) == 2:
        crud.settings.update_next = URL(r=request, f='kit_item', args=request.args[1])

    return shn_rest_controller(module, resource, main='code', onaccept=lambda form: kit_total(form))

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
    kit = request.args(0)
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
    shn_audit_read(operation='list', module=module, resource='kit_item', record=kit, representation='html')
    item_list = []
    sqlrows = db(query).select()
    even = True
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, module, 'kit_item', 'html')
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
        total_unit_cost += (db(db.budget_item.id==item.item_id).select().first().unit_cost) * (db(query).select().first().quantity)
        total_monthly_cost += (db(db.budget_item.id==item.item_id).select().first().monthly_cost) * (db(query).select().first().quantity)
        total_minute_cost += (db(db.budget_item.id==item.item_id).select().first().minute_cost) * (db(query).select().first().quantity)
        total_megabyte_cost += (db(db.budget_item.id==item.item_id).select().first().megabyte_cost) * (db(query).select().first().quantity)
    db(db.budget_kit.id==kit).update(total_unit_cost=total_unit_cost, total_monthly_cost=total_monthly_cost, total_minute_cost=total_minute_cost, total_megabyte_cost=total_megabyte_cost)

def kit_update_items():
    "Update a Kit's items (Quantity & Delete)"
    if len(request.args) == 0:
        session.error = T("Need to specify a kit!")
        redirect(URL(r=request, f='kit'))
    kit = request.args(0)
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

def kit_export_xls():
    """
    Export a list of Kits in Excel XLS format
    Sheet 1 is a list of Kits
    Then there is a separate sheet per kit, listing it's component items
    """
    try:
        import xlwt
    except ImportError:
        session.error = T('xlwt module not available within the running Python - this needs installing to do XLS Reporting!')
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
        # Replace characters which are illegal in sheetnames
        sheetname = kit.code.replace("/","_")
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
            item = db(table.id == content.item_id).select().first()
            rowx = sheet.row(rowy)
            rowy += 1
            cell = 0
            for field_item in fields_items:
                tab, col = str(field_item).split('.')
                # Do lookups for option fields
                if col == 'cost_type':
                    opt = item[col]
                    value = str(budget_cost_type_opts[opt])
                elif col == 'category_type':
                    opt = item[col]
                    value = str(budget_category_type_opts[opt])
                else:
                    value = item[col]
                rowx.write(cell, value)
                cell += 1
    
    book.save(output)

    output.seek(0)
    import gluon.contenttype
    response.headers['Content-Type'] = gluon.contenttype.contenttype('.xls')
    filename = "%s_kits.xls" % (request.env.server_name)
    response.headers['Content-disposition'] = "attachment; filename=\"%s\"" % filename
    return output.read()
    
def kit_export_pdf():
    """
    Export a list of Kits in Adobe PDF format
    Uses Geraldo SubReport
    """
    try:
        from reportlab.lib.units import cm
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    except ImportError:
        session.error = T('ReportLab module not available within the running Python - this needs installing to do PDF Reporting!')
        redirect(URL(r=request, c='kit'))
    try:
        from geraldo import Report, ReportBand, SubReport, Label, ObjectValue, SystemField, landscape, BAND_WIDTH
        from geraldo.generators import PDFGenerator
    except ImportError:
        session.error = T('Geraldo module not available within the running Python - this needs installing to do PDF Reporting!')
        redirect(URL(r=request, c='kit'))

    table = db.budget_kit
    objects_list = db(table.id > 0).select()
    if not objects_list:
        session.warning = T('No data in this table - cannot create PDF!')
        redirect(URL(r=request))
    
    import StringIO
    output = StringIO.StringIO()
    
    #class MySubReport(SubReport):
    #    def __init__(self, db=None, **kwargs):
    #        " Initialise parent class & make any necessary modifications "
    #        self.db = db
    #        SubReport.__init__(self, **kwargs)

    class MyReport(Report):
        def __init__(self, queryset=None, db=None):
            " Initialise parent class & make any necessary modifications "
            Report.__init__(self, queryset)
            self.db = db
        # can't use T() here!
        title = "Kits"
        page_size = landscape(A4)
        class band_page_header(ReportBand):
            height = 1.3*cm
            elements = [
                SystemField(expression='%(report_title)s', top=0.1*cm,
                    left=0, width=BAND_WIDTH, style={'fontName': 'Helvetica-Bold',
                    'fontSize': 14, 'alignment': TA_CENTER}
                    ),
                Label(text="Code", top=0.8*cm, left=0.2*cm),
                Label(text="Description", top=0.8*cm, left=2*cm),
                Label(text="Cost", top=0.8*cm, left=10*cm),
                Label(text="Monthly", top=0.8*cm, left=12*cm),
                Label(text="per Minute", top=0.8*cm, left=14*cm),
                Label(text="per Megabyte", top=0.8*cm, left=16*cm),
                Label(text="Comments", top=0.8*cm, left=18*cm),
            ]
            borders = {'bottom': True}
        class band_page_footer(ReportBand):
            height = 0.5*cm
            elements = [
                Label(text='%s' % request.utcnow.date(), top=0.1*cm, left=0),
                SystemField(expression='Page # %(page_number)d of %(page_count)d', top=0.1*cm,
                    width=BAND_WIDTH, style={'alignment': TA_RIGHT}),
            ]
            borders = {'top': True}
        class band_detail(ReportBand):
            height = 0.5*cm
            auto_expand_height = True
            elements = (
                    ObjectValue(attribute_name='code', left=0.2*cm, width=1.8*cm),
                    ObjectValue(attribute_name='description', left=2*cm, width=8*cm),
                    ObjectValue(attribute_name='total_unit_cost', left=10*cm, width=2*cm),
                    ObjectValue(attribute_name='total_monthly_cost', left=12*cm, width=2*cm),
                    ObjectValue(attribute_name='total_minute_cost', left=14*cm, width=2*cm),
                    ObjectValue(attribute_name='total_megabyte_cost', left=16*cm, width=2*cm),
                    ObjectValue(attribute_name='comments', left=18*cm, width=6*cm),
                    )
        subreports = [
            SubReport(
                #queryset_string = 'db((db.budget_kit_item.kit_id==%(object)s.id)&(db.budget_item.id==db.budget_kit_item.item_id)).select(db.budget_item.code, db.budget_item.description, db.budget_item.unit_cost)',
                #queryset_string = 'db(db.budget_kit_item.kit_id==%(object)s.id).select()',
                band_header = ReportBand(
                        height=0.5*cm,
                        elements=[
                            Label(text='Item ID', top=0, left=0.2*cm, style={'fontName': 'Helvetica-Bold'}),
                            Label(text='Quantity', top=0, left=2*cm, style={'fontName': 'Helvetica-Bold'}),
                            #Label(text='Unit Cost', top=0, left=4*cm, style={'fontName': 'Helvetica-Bold'}),
                            ],
                        borders={'top': True, 'left': True, 'right': True},
                        ),
                detail_band = ReportBand(
                        height=0.5*cm,
                        elements=[
                            ObjectValue(attribute_name='item_id', top=0, left=0.2*cm),
                            ObjectValue(attribute_name='quantity', top=0, left=2*cm),
                            #ObjectValue(attribute_name='unit_cost', top=0, left=4*cm),
                            ]
                        ),
                ),
            ]

        
    #report = MyReport(queryset=objects_list)
    report = MyReport(queryset=objects_list, db=db)
    report.generate_by(PDFGenerator, filename=output)

    output.seek(0)
    import gluon.contenttype
    response.headers['Content-Type'] = gluon.contenttype.contenttype('.pdf')
    filename = "%s_kits.pdf" % (request.env.server_name)
    response.headers['Content-disposition'] = "attachment; filename=\"%s\"" % filename
    return output.read()
    
def kit_export_csv():
    """
    Export kits in CSV format
    Concatenates: kits, items & kit_item
    """
    output = ''
    
    for resource in ['kit', 'item', 'kit_item']:
        _table = module + '_' + resource
        table = db[_table]
        # Filter Search list to just those records which user can read
        query = shn_accessible_query('read', table)
        # Filter Search List to remove entries which have been deleted
        if 'deleted' in table:
            query = ((table.deleted == False) | (table.deleted == None)) & query # includes None for backward compatability
        output += 'TABLE ' + _table + '\n'
        output += str(db(query).select())
        output += '\n\n'
        
    import gluon.contenttype
    response.headers['Content-Type'] = gluon.contenttype.contenttype('.csv')
    filename = "%s_kits.csv" % (request.env.server_name)
    response.headers['Content-disposition'] = "attachment; filename=%s" % filename
    return output
    
def kit_import_csv():
    """
    Import kits in CSV format
    Assumes concatenated: kits, items & kit_item
    """
    # Read in POST
    file = request.vars.filename.file
    try:
        # Assumes that it is a concatenation of tables
        import_csv(file)
        session.flash = T('Data uploaded')
    except: 
        session.error = T('Unable to parse CSV file!')
    redirect(URL(r=request, f='kit'))
    
def bundle():
    "RESTlike CRUD controller"
    resource = 'bundle'
    table = module + '_' + resource

    # Model options used in multiple controllers so defined at the top of the file
    
    # CRUD Strings
    title_create = T('Add Bundle')
    title_display = T('Bundle Details')
    title_list = T('List Bundles')
    title_update = T('Edit Bundle')
    title_search = T('Search Bundles')
    subtitle_create = T('Add New Bundle')
    subtitle_list = T('Bundles')
    label_list_button = T('List Bundles')
    label_create_button = T('Add Bundle')
    msg_record_created = T('Bundle added')
    msg_record_modified = T('Bundle updated')
    msg_record_deleted = T('Bundle deleted')
    msg_list_empty = T('No Bundles currently registered')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

    if len(request.args) == 2:
        crud.settings.update_next = URL(r=request, f='bundle_kit_item', args=request.args[1])

    return shn_rest_controller(module, resource, onaccept=lambda form: bundle_total(form))

def bundle_kit_item():
    "Many to Many CRUD Controller"
    if len(request.args) == 0:
        session.error = T("Need to specify a bundle!")
        redirect(URL(r=request, f='bundle'))
    bundle = request.args(0)
    tables = [db.budget_bundle_kit, db.budget_bundle_item]
    authorised = shn_has_permission('update', tables[0]) and shn_has_permission('update', tables[1])
    
    title = db.budget_bundle[bundle].name
    bundle_description = db.budget_bundle[bundle].description
    bundle_total_cost = db.budget_bundle[bundle].total_unit_cost
    bundle_monthly_cost = db.budget_bundle[bundle].total_monthly_cost
    # Start building the Return with the common items
    output = dict(module_name=module_name, title=title, description=bundle_description, total_cost=bundle_total_cost, monthly_cost=bundle_monthly_cost)
    # Audit
    shn_audit_read(operation='list', module=module, resource='bundle_kit_item', record=bundle, representation='html')
    item_list = []
    even = True
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, module, 'bundle_kit_item', 'html')
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
        total_unit_cost += (db(db.budget_kit.id==kit.kit_id).select().first().total_unit_cost) * (db(query).select().first().quantity)
        total_monthly_cost += (db(db.budget_kit.id==kit.kit_id).select().first().total_monthly_cost) * (db(query).select().first().quantity)
        total_monthly_cost += (db(db.budget_kit.id==kit.kit_id).select().first().total_minute_cost) * (db(query).select().first().quantity) * (db(query).select().first().minutes)
        total_monthly_cost += (db(db.budget_kit.id==kit.kit_id).select().first().total_megabyte_cost) * (db(query).select().first().quantity) * (db(query).select().first().megabytes)
    
    table = db.budget_bundle_item
    query = table.bundle_id==bundle
    items = db(query).select()
    for item in items:
        query = (table.bundle_id==bundle) & (table.item_id==item.item_id)
        total_unit_cost += (db(db.budget_item.id==item.item_id).select().first().unit_cost) * (db(query).select().first().quantity)
        total_monthly_cost += (db(db.budget_item.id==item.item_id).select().first().monthly_cost) * (db(query).select().first().quantity)
        total_monthly_cost += (db(db.budget_item.id==item.item_id).select().first().minute_cost) * (db(query).select().first().quantity) * (db(query).select().first().minutes)
        total_monthly_cost += (db(db.budget_item.id==item.item_id).select().first().megabyte_cost) * (db(query).select().first().quantity) * (db(query).select().first().megabytes)
    
    db(db.budget_bundle.id==bundle).update(total_unit_cost=total_unit_cost, total_monthly_cost=total_monthly_cost)

def bundle_update_items():
    "Update a Bundle's items (Quantity, Minutes, Megabytes & Delete)"
    if len(request.args) == 0:
        session.error = T("Need to specify a bundle!")
        redirect(URL(r=request, f='bundle'))
    bundle = request.args(0)
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
    resource = 'staff'
    table = module + '_' + resource

    # Model options used in multiple controllers so defined at the top of the file
    
    # CRUD Strings
    title_create = T('Add Staff Type')
    title_display = T('Staff Type Details')
    title_list = T('List Staff Types')
    title_update = T('Edit Staff Type')
    title_search = T('Search Staff Types')
    subtitle_create = T('Add New Staff Type')
    subtitle_list = T('Staff Types')
    label_list_button = T('List Staff Types')
    label_create_button = T('Add Staff Type')
    msg_record_created = T('Staff Type added')
    msg_record_modified = T('Staff Type updated')
    msg_record_deleted = T('Staff Type deleted')
    msg_list_empty = T('No Staff Types currently registered')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

    return shn_rest_controller(module, resource)

def location():
    "RESTlike CRUD controller"
    resource = 'location'
    table = module + '_' + resource

    # Model options used in multiple controllers so defined at the top of the file
    
    # CRUD Strings
    title_create = T('Add Location')
    title_display = T('Location Details')
    title_list = T('List Locations')
    title_update = T('Edit Location')
    title_search = T('Search Locations')
    subtitle_create = T('Add New Location')
    subtitle_list = T('Locations')
    label_list_button = T('List Locations')
    label_create_button = T('Add Location')
    msg_record_created = T('Location added')
    msg_record_modified = T('Location updated')
    msg_record_deleted = T('Location deleted')
    msg_list_empty = T('No Locations currently registered')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

    return shn_rest_controller(module, resource, main='code')

def project():
    "RESTlike CRUD controller"
    resource = 'project'
    table = module + '_' + resource

    # Model options used in multiple controllers so defined at the top of the file
    
    # CRUD Strings
    title_create = T('Add Project')
    title_display = T('Project Details')
    title_list = T('List Projects')
    title_update = T('Edit Project')
    title_search = T('Search Projects')
    subtitle_create = T('Add New Project')
    subtitle_list = T('Projects')
    label_list_button = T('List Projects')
    label_create_button = T('Add Project')
    msg_record_created = T('Project added')
    msg_record_modified = T('Project updated')
    msg_record_deleted = T('Project deleted')
    msg_list_empty = T('No Projects currently registered')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

    return shn_rest_controller(module, resource, main='code')

def budget():
    "RESTlike CRUD controller"
    resource = 'budget'
    table = module + '_' + resource

    # Model options used in multiple controllers so defined at the top of the file
    
    # CRUD Strings
    title_create = T('Add Budget')
    title_display = T('Budget Details')
    title_list = T('List Budgets')
    title_update = T('Edit Budget')
    title_search = T('Search Budgets')
    subtitle_create = T('Add New Budget')
    subtitle_list = T('Budgets')
    label_list_button = T('List Budgets')
    label_create_button = T('Add Budget')
    msg_record_created = T('Budget added')
    msg_record_modified = T('Budget updated')
    msg_record_deleted = T('Budget deleted')
    msg_list_empty = T('No Budgets currently registered')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

    return shn_rest_controller(module, resource)

def budget_staff_bundle():
    "Many to Many CRUD Controller"
    if len(request.args) == 0:
        session.error = T("Need to specify a Budget!")
        redirect(URL(r=request, f='budget'))
    budget = request.args(0)
    tables = [db.budget_budget_staff, db.budget_budget_bundle]
    authorised = shn_has_permission('update', tables[0]) and shn_has_permission('update', tables[1])
    
    title = db.budget_budget[budget].name
    budget_description = db.budget_budget[budget].description
    budget_onetime_cost = db.budget_budget[budget].total_onetime_costs
    budget_recurring_cost = db.budget_budget[budget].total_recurring_costs
    # Start building the Return with the common items
    output = dict(module_name=module_name, title=title, description=budget_description, onetime_cost=budget_onetime_cost, recurring_cost=budget_recurring_cost)
    # Audit
    shn_audit_read(operation='list', module=module, resource='budget_staff_bundle', record=budget, representation='html')
    item_list = []
    even = True
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, module, 'budget_staff_bundle', 'html')
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
        total_onetime_cost += (db(db.budget_staff.id==staff.staff_id).select().first().travel) * (db(query).select().first().quantity)
        total_recurring_cost += (db(db.budget_staff.id==staff.staff_id).select().first().salary) * (db(query).select().first().quantity) * (db(query).select().first().months)
        total_recurring_cost += (db(db.budget_location.id==staff.location_id).select().first().subsistence) * (db(query).select().first().quantity) * (db(query).select().first().months)
        total_recurring_cost += (db(db.budget_location.id==staff.location_id).select().first().hazard_pay) * (db(query).select().first().quantity) * (db(query).select().first().months)
        
    table = db.budget_budget_bundle
    query = table.budget_id==budget
    bundles = db(query).select()
    for bundle in bundles:
        query = (table.budget_id==budget) & (table.bundle_id==bundle.bundle_id)
        total_onetime_cost += (db(db.budget_bundle.id==bundle.bundle_id).select().first().total_unit_cost) * (db(query).select().first().quantity)
        total_recurring_cost += (db(db.budget_bundle.id==bundle.bundle_id).select().first().total_monthly_cost) * (db(query).select().first().quantity) * (db(query).select().first().months)
        
    db(db.budget_budget.id==budget).update(total_onetime_costs=total_onetime_cost, total_recurring_costs=total_recurring_cost)

def budget_update_items():
    "Update a Budget's items (Quantity, Months & Delete)"
    if len(request.args) == 0:
        session.error = T("Need to specify a budget!")
        redirect(URL(r=request, f='budget'))
    budget = request.args(0)
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