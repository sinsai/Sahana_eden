# -*- coding: utf-8 -*-

module = 'budget'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read = False,
        audit_write = False
    )

# Parameters
# Only record 1 is used
resource = 'parameter'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('shipping', 'double', default=15.00, notnull=True),
                Field('logistics', 'double', default=0.00, notnull=True),
                Field('admin', 'double', default=0.00, notnull=True),
                Field('indirect', 'double', default=7.00, notnull=True),
                migrate=migrate)
db[table].shipping.requires = IS_FLOAT_IN_RANGE(0, 100)
db[table].shipping.label = "Shipping cost"
db[table].logistics.requires = IS_FLOAT_IN_RANGE(0, 100)
db[table].logistics.label = "Procurement & Logistics cost"
db[table].admin.requires = IS_FLOAT_IN_RANGE(0, 100)
db[table].admin.label = "Administrative support cost"
db[table].indirect.requires = IS_FLOAT_IN_RANGE(0, 100)
db[table].indirect.label = "Indirect support cost HQ"
title_update = T('Edit Parameters')
s3.crud_strings[table] = Storage(title_update=title_update)

# Items
budget_cost_type_opts = {
    1:T('One-time'),
    2:T('Recurring')
    }
opt_budget_cost_type = SQLTable(None, 'budget_cost_type',
                        Field('cost_type', 'integer', notnull=True,
                            requires = IS_IN_SET(budget_cost_type_opts),
                            default = 1,
                            label = T('Cost Type'),
                            represent = lambda opt: opt and budget_cost_type_opts[opt]))
budget_category_type_opts = {
    1:T('Consumable'),
    2:T('Satellite'),
    3:T('HF'),
    4:T('VHF'),
    5:T('Telephony'),
    6:T('W-LAN'),
    7:T('Network'),
    8:T('Generator'),
    9:T('Electrical'),
    10:T('Vehicle'),
    11:T('GPS'),
    12:T('Tools'),
    13:T('IT'),
    14:T('ICT'),
    15:T('TC'),
    16:T('Stationery'),
    17:T('Relief'),
    18:T('Miscellaneous'),
    19:T('Running Cost')
    }
opt_budget_category_type = SQLTable(None, 'budget_category_type',
                            Field('category_type', 'integer', notnull=True,
                                requires = IS_IN_SET(budget_category_type_opts),
                                default = 1,
                                label = T('Category'),
                                represent = lambda opt: opt and budget_category_type_opts[opt]))
resource = 'item'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('code', notnull=True, unique=True),
                Field('description', length=256, notnull=True),
                opt_budget_cost_type,
                opt_budget_category_type,
                Field('unit_cost', 'double', default=0.00),
                Field('monthly_cost', 'double', default=0.00),
                Field('minute_cost', 'double', default=0.00),
                Field('megabyte_cost', 'double', default=0.00),
                Field('comments', length=256),
                migrate=migrate)
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

# Kits
resource = 'kit'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('code', notnull=True, unique=True),
                Field('description', length=256),
                Field('total_unit_cost', 'double', writable=False),
                Field('total_monthly_cost', 'double', writable=False),
                Field('total_minute_cost', 'double', writable=False),
                Field('total_megabyte_cost', 'double', writable=False),
                Field('comments', length=256),
                migrate=migrate)
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.label = T('Code')
db[table].code.comment = SPAN("*", _class="req")
db[table].description.label = T('Description')
db[table].total_unit_cost.label = T('Total Unit Cost')
db[table].total_monthly_cost.label = T('Total Monthly Cost')
db[table].total_minute_cost.label = T('Total Cost per Minute')
db[table].total_megabyte_cost.label = T('Total Cost per Megabyte')
db[table].comments.label = T('Comments')
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

# Kit<>Item Many2Many
resource = 'kit_item'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('kit_id', db.budget_kit),
                Field('item_id', db.budget_item, ondelete='RESTRICT'),
                Field('quantity', 'integer', default=1, notnull=True),
                migrate=migrate)
db[table].kit_id.requires = IS_IN_DB(db, 'budget_kit.id', 'budget_kit.code')
db[table].kit_id.label = T('Kit')
db[table].kit_id.represent = lambda kit_id: db(db.budget_kit.id==kit_id).select()[0].code
db[table].item_id.requires = IS_IN_DB(db, 'budget_item.id', 'budget_item.description')
db[table].item_id.label = T('Item')
db[table].item_id.represent = lambda item_id: db(db.budget_item.id==item_id).select()[0].description
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")

# Bundles
resource = 'bundle'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', notnull=True, unique=True),
                Field('description', length=256),
                Field('total_unit_cost', 'double', writable=False),
                Field('total_monthly_cost', 'double', writable=False),
                Field('comments', length=256),
                migrate=migrate)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].description.label = T('Description')
db[table].total_unit_cost.label = T('One time cost')
db[table].total_monthly_cost.label = T('Recurring cost')
db[table].comments.label = T('Comments')
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

# Bundle<>Kit Many2Many
resource = 'bundle_kit'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                Field('bundle_id', db.budget_bundle),
                Field('kit_id', db.budget_kit, ondelete='RESTRICT'),
                Field('quantity', 'integer', default=1, notnull=True),
                Field('minutes', 'integer', default=0, notnull=True),
                Field('megabytes', 'integer', default=0, notnull=True),
                migrate=migrate)
db[table].bundle_id.requires = IS_IN_DB(db, 'budget_bundle.id', 'budget_bundle.description')
db[table].bundle_id.label = T('Bundle')
db[table].bundle_id.represent = lambda bundle_id: db(db.budget_bundle.id==bundle_id).select()[0].description
db[table].kit_id.requires = IS_IN_DB(db, 'budget_kit.id', 'budget_kit.code')
db[table].kit_id.label = T('Kit')
db[table].kit_id.represent = lambda kit_id: db(db.budget_kit.id==kit_id).select()[0].code
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")
db[table].minutes.requires = IS_NOT_EMPTY()
db[table].minutes.label = T('Minutes per Month')
db[table].minutes.comment = SPAN("*", _class="req")
db[table].megabytes.requires = IS_NOT_EMPTY()
db[table].megabytes.label = T('Megabytes per Month')
db[table].megabytes.comment = SPAN("*", _class="req")

# Bundle<>Item Many2Many
resource = 'bundle_item'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                Field('bundle_id', db.budget_bundle),
                Field('item_id', db.budget_item, ondelete='RESTRICT'),
                Field('quantity', 'integer', default=1, notnull=True),
                Field('minutes', 'integer', default=0, notnull=True),
                Field('megabytes', 'integer', default=0, notnull=True),
                migrate=migrate)
db[table].bundle_id.requires = IS_IN_DB(db, 'budget_bundle.id', 'budget_bundle.description')
db[table].bundle_id.label = T('Bundle')
db[table].bundle_id.represent = lambda bundle_id: db(db.budget_bundle.id==bundle_id).select()[0].description
db[table].item_id.requires = IS_IN_DB(db, 'budget_item.id', 'budget_item.description')
db[table].item_id.label = T('Item')
db[table].item_id.represent = lambda item_id: db(db.budget_item.id==item_id).select()[0].description
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")
db[table].minutes.requires = IS_NOT_EMPTY()
db[table].minutes.label = T('Minutes per Month')
db[table].minutes.comment = SPAN("*", _class="req")
db[table].megabytes.requires = IS_NOT_EMPTY()
db[table].megabytes.label = T('Megabytes per Month')
db[table].megabytes.comment = SPAN("*", _class="req")

# Staff Types
budget_currency_type_opts = {
    1:T('Dollars'),
    2:T('Euros'),
    3:T('Pounds')
    }
opt_budget_currency_type = SQLTable(None, 'budget_currency_type',
                    db.Field('currency_type', 'integer', notnull=True,
                    requires = IS_IN_SET(budget_currency_type_opts),
                    default = 1,
                    label = T('Currency'),
                    represent = lambda opt: opt and budget_currency_type_opts[opt]))

resource = 'staff'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', notnull=True, unique=True),
                Field('grade', notnull=True),
                Field('salary', 'integer', notnull=True),
                opt_budget_currency_type,
                Field('travel', 'integer', default=0),
                # Shouldn't be grade-dependent, but purely location-dependent
                #Field('subsistence', 'double', default=0.00),
                # Location-dependent
                #Field('hazard_pay', 'double', default=0.00),
                Field('comments', length=256),
                migrate=migrate)
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

# Locations
resource = 'location'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('code', length=3, notnull=True, unique=True),
                Field('description'),
                Field('subsistence', 'double', default=0.00),
                Field('hazard_pay', 'double', default=0.00),
                Field('comments', length=256),
                migrate=migrate)
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.label = T('Code')
db[table].code.comment = SPAN("*", _class="req")
db[table].description.label = T('Description')
db[table].subsistence.label = T('Subsistence Cost')
# UN terminology
#db[table].subsistence.label = "DSA"
db[table].hazard_pay.label = T('Hazard Pay')
db[table].comments.label = T('Comments')
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

# Projects
resource = 'project'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('code', notnull=True, unique=True),
                Field('title'),
                Field('comments', length=256),
                migrate=migrate)
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.label = T('Code')
db[table].code.comment = SPAN("*", _class="req")
db[table].title.label = T('Title')
db[table].comments.label = T('Comments')
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

# Budgets
resource = 'budget'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', notnull=True, unique=True),
                Field('description', length=256),
                Field('total_onetime_costs', 'double', writable=False),
                Field('total_recurring_costs', 'double', writable=False),
                Field('comments', length=256),
                migrate=migrate)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].description.label = T('Description')
db[table].total_onetime_costs.label = T('Total One-time Costs')
db[table].total_recurring_costs.label = T('Total Recurring Costs')
db[table].comments.label = T('Comments')
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

# Budget<>Bundle Many2Many
resource = 'budget_bundle'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                Field('budget_id', db.budget_budget),
                Field('project_id', db.budget_project),
                Field('location_id', db.budget_location),
                Field('bundle_id', db.budget_bundle, ondelete='RESTRICT'),
                Field('quantity', 'integer', default=1, notnull=True),
                Field('months', 'integer', default=3, notnull=True),
                migrate=migrate)
db[table].budget_id.requires = IS_IN_DB(db, 'budget_budget.id', 'budget_budget.name')
db[table].budget_id.label = T('Budget')
db[table].budget_id.represent = lambda budget_id: db(db.budget_budget.id==budget_id).select()[0].name
db[table].project_id.requires = IS_IN_DB(db,'budget_project.id', 'budget_project.code')
db[table].project_id.label = T('Project')
db[table].project_id.represent = lambda project_id: db(db.budget_project.id==project_id).select()[0].code
db[table].location_id.requires = IS_IN_DB(db, 'budget_location.id', 'budget_location.code')
db[table].location_id.label = T('Location')
db[table].location_id.represent = lambda location_id: db(db.budget_location.id==location_id).select()[0].code
db[table].bundle_id.requires = IS_IN_DB(db, 'budget_bundle.id', 'budget_bundle.name')
db[table].bundle_id.label = T('Bundle')
db[table].bundle_id.represent = lambda bundle_id: db(db.budget_bundle.id==bundle_id).select()[0].name
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")
db[table].months.requires = IS_NOT_EMPTY()
db[table].months.label = T('Months')
db[table].months.comment = SPAN("*", _class="req")

# Budget<>Staff Many2Many
resource = 'budget_staff'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                Field('budget_id', db.budget_budget),
                Field('project_id', db.budget_project),
                Field('location_id', db.budget_location),
                Field('staff_id', db.budget_staff, ondelete='RESTRICT'),
                Field('quantity', 'integer', default=1, notnull=True),
                Field('months', 'integer', default=3, notnull=True),
                migrate=migrate)
db[table].budget_id.requires = IS_IN_DB(db, 'budget_budget.id', 'budget_budget.name')
db[table].budget_id.label = T('Budget')
db[table].budget_id.represent = lambda budget_id: db(db.budget_budget.id==budget_id).select()[0].name
db[table].project_id.requires = IS_IN_DB(db,'budget_project.id', 'budget_project.code')
db[table].project_id.label = T('Project')
db[table].project_id.represent = lambda project_id: db(db.budget_project.id==project_id).select()[0].code
db[table].location_id.requires = IS_IN_DB(db, 'budget_location.id', 'budget_location.code')
db[table].location_id.label = T('Location')
db[table].location_id.represent = lambda location_id: db(db.budget_location.id==location_id).select()[0].code
db[table].staff_id.requires = IS_IN_DB(db, 'budget_staff.id', 'budget_staff.name')
db[table].staff_id.label = T('Staff')
db[table].staff_id.represent = lambda bundle_id: db(db.budget_staff.id==staff_id).select()[0].description
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")
db[table].months.requires = IS_NOT_EMPTY()
db[table].months.label = T('Months')
db[table].months.comment = SPAN("*", _class="req")
