module = 'budget'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                db.Field('audit_read', 'boolean'),
                db.Field('audit_write', 'boolean'),
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
db.define_table(table,timestamp,uuidstamp,
                db.Field('shipping', 'double', default=15.00, notnull=True),
                db.Field('logistics', 'double', default=0.00, notnull=True),
                db.Field('admin', 'double', default=0.00, notnull=True),
                db.Field('indirect', 'double', default=7.00, notnull=True),
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
resource = 'item'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                db.Field('code', notnull=True, unique=True),
                db.Field('description', length=256, notnull=True),
                db.Field('cost_type', notnull=True),
                db.Field('category'),
                #db.Field('sub_category'),
                db.Field('unit_cost', 'double', default=0.00),
                db.Field('monthly_cost', 'double', default=0.00),
                db.Field('minute_cost', 'double', default=0.00),
                db.Field('megabyte_cost', 'double', default=0.00),
                db.Field('comments', length=256),
                migrate=migrate)
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.comment = SPAN("*", _class="req")
db[table].description.requires = IS_NOT_EMPTY()
db[table].description.comment = SPAN("*", _class="req")
db[table].cost_type.requires = IS_IN_SET(['One-time', 'Recurring'])
db[table].category.requires = IS_IN_SET(['Consumable', 'Satellite', 'HF', 'VHF', 'Telephony', 'W-LAN', 'Network', 'Generator', 'Electrical', 'Vehicle', 'GPS', 'Tools', 'IT', 'ICT', 'TC', 'Stationery', 'Relief', 'Miscellaneous', 'Running Cost'])
#db[table].sub_category.requires = IS_IN_SET(['Satellite', 'VHF', 'UHF', 'HF', 'Airband', 'Telephony', 'GPS'])
title_create = T('Add Item')
title_display = T('Item Details')
title_list = T('List Items')
title_update = T('Edit Item')
title_search = T('Search Items')
subtitle_create = T('Add New Item')
subtitle_list = T('Items')
label_list_button = T('List Items')
label_create_button = T('Add Item')
msg_record_created = T('Item added')
msg_record_modified = T('Item updated')
msg_record_deleted = T('Item deleted')
msg_list_empty = T('No Items currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Kits
resource = 'kit'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                db.Field('code', notnull=True, unique=True),
                db.Field('description', length=256),
                db.Field('total_unit_cost', 'double', writable=False),
                db.Field('total_monthly_cost', 'double', writable=False),
                db.Field('total_minute_cost', 'double', writable=False),
                db.Field('total_megabyte_cost', 'double', writable=False),
                db.Field('comments', length=256),
                migrate=migrate)
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.comment = SPAN("*", _class="req")
db[table].total_minute_cost.label = "Total cost per minute"
db[table].total_megabyte_cost.label = "Total cost per Mbyte"
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
db.define_table(table, timestamp,
                db.Field('kit_id', db.budget_kit),
                db.Field('item_id', db.budget_item, ondelete='RESTRICT'),
                db.Field('quantity', 'integer', default=1, notnull=True),
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
db.define_table(table, timestamp, uuidstamp,
                db.Field('name', notnull=True, unique=True),
                db.Field('description', length=256),
                db.Field('total_unit_cost', writable=False),
                db.Field('total_monthly_cost', writable=False),
                db.Field('comments', length=256),
                migrate=migrate)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.comment = SPAN("*", _class="req")
db[table].total_unit_cost.label = T('One time cost')
db[table].total_monthly_cost.label = T('Recurring cost')
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
db.define_table(table, timestamp,
                db.Field('bundle_id', db.budget_bundle),
                db.Field('kit_id', db.budget_kit, ondelete='RESTRICT'),
                db.Field('quantity', 'integer', default=1, notnull=True),
                db.Field('minutes', 'integer', default=0, notnull=True),
                db.Field('megabytes', 'integer', default=0, notnull=True),
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
db.define_table(table, timestamp,
                db.Field('bundle_id', db.budget_bundle),
                db.Field('item_id', db.budget_item, ondelete='RESTRICT'),
                db.Field('quantity', 'integer', default=1, notnull=True),
                db.Field('minutes', 'integer', default=0, notnull=True),
                db.Field('megabytes', 'integer', default=0, notnull=True),
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
resource = 'staff_type'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                db.Field('name', notnull=True, unique=True),
                db.Field('grade', notnull=True),
                db.Field('salary', 'integer', notnull=True),
                db.Field('travel', 'integer'),
                db.Field('subsistence', 'double', default=0.00),
                db.Field('hazard_pay', 'double', default=0.00),
                db.Field('comments', length=256),
                migrate=migrate)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.comment = SPAN("*", _class="req")
db[table].grade.requires = IS_NOT_EMPTY()
db[table].grade.comment = SPAN("*", _class="req")
db[table].salary.requires = IS_NOT_EMPTY()
db[table].salary.comment = SPAN("*", _class="req")
db[table].subsistence.label = "DSA"
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
db.define_table(table, timestamp, uuidstamp,
                db.Field('code', length=3, notnull=True, unique=True),
                db.Field('description'),
                db.Field('subsistence', 'double', default=0.00),
                db.Field('hazard_pay', 'double', default=0.00),
                db.Field('comments', length=256),
                migrate=migrate)
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.comment = SPAN("*", _class="req")
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
db.define_table(table, timestamp, uuidstamp,
                db.Field('code', notnull=True, unique=True),
                db.Field('title'),
                db.Field('comments', length=256),
                migrate=migrate)
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.comment = SPAN("*", _class="req")
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
resource = 'budget_equipment'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                db.Field('location', 'reference %s_location' % module, ondelete='RESTRICT'),
                db.Field('project', 'reference %s_project' % module, ondelete='RESTRICT'),
                db.Field('bundle', 'reference %s_bundle' % module, ondelete='RESTRICT'),
                db.Field('quantity', 'integer'),
                db.Field('unit_cost', 'double', writable=False),
                db.Field('months', 'integer'),
                db.Field('monthly_cost', 'double', writable=False),
                db.Field('total_unit_cost', writable=False),
                db.Field('total_monthly_cost', writable=False),
                db.Field('comments', length=256),
                migrate=migrate)
db[table].location.requires = IS_IN_DB(db, '%s_location.id' % module, '%s_location.name' % module)
db[table].location.comment = SPAN("*", _class="req")
db[table].project.requires = IS_IN_DB(db,'%s_project.id' % module, '%s_project.code' % module)
db[table].project.comment = SPAN("*",_class="req")
db[table].bundle.requires = IS_IN_DB(db, '%s_bundle.id' % module, '%s_bundle.name' % module)
db[table].bundle.comment = SPAN("*", _class="req")
title_create = T('Add Equipment Budget')
title_display = T('Equipment Budget Details')
title_list = T('List Equipment Budgets')
title_update = T('Edit Equipment Budget')
title_search = T('Search Equipment Budgets')
subtitle_create = T('Add New Equipment Budget')
subtitle_list = T('Equipment Budgets')
label_list_button = T('List Equipment Budgets')
label_create_button = T('Add Equipment Budget')
msg_record_created = T('Equipment Budget added')
msg_record_modified = T('Equipment Budget updated')
msg_record_deleted = T('Equipment Budget deleted')
msg_list_empty = T('No Equipment Budgets currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

resource = 'budget_staff'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                db.Field('location', 'reference %s_location' % module, ondelete='RESTRICT'),
                db.Field('project', 'reference %s_project' % module, ondelete='RESTRICT'),
                db.Field('job_title', 'reference %s_staff_type' % module, ondelete='RESTRICT'),
                db.Field('grade', writable=False),
                db.Field('type'),
                db.Field('headcount', 'integer'),
                db.Field('months', 'integer'),
                db.Field('salary', writable=False),
                db.Field('travel', writable=False),
                db.Field('subsistence', 'double', writable=False),
                db.Field('hazard_pay', 'double', writable=False),
                db.Field('total', 'double', writable=False),
                db.Field('comments', length=256),
                migrate=migrate)
db[table].location.requires = IS_IN_DB(db, '%s_location.id' % module, '%s_location.name' % module)
db[table].location.comment = SPAN("*", _class="req")
db[table].project.requires = IS_IN_DB(db, '%s_project.id' % module, '%s_project.code' % module)
db[table].job_title.requires = IS_IN_DB(db, '%s_staff_type.id' % module, '%s_staff_type.name' % module)
db[table].job_title.comment = SPAN("*", _class="req")
db[table].project.comment = SPAN("*", _class="req")
db[table].type.requires = IS_IN_SET(['Staff', 'Consultant'])
title_create = T('Add Staff Budget')
title_display = T('Staff Budget Details')
title_list = T('List Staff Budgets')
title_update = T('Edit Staff Budget')
title_search = T('Search Staff Budgets')
subtitle_create = T('Add New Staff Budget')
subtitle_list = T('Staff Budgets')
label_list_button = T('List Staff Budgets')
label_create_button = T('Add Staff Budget')
msg_record_created = T('Staff Budget added')
msg_record_modified = T('Staff Budget updated')
msg_record_deleted = T('Staff Budget deleted')
msg_list_empty = T('No Staff Budgets currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

resource = 'budget'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                db.Field('name', notnull=True, unique=True),
                db.Field('equipment', 'reference %s_budget_equipment' % module, ondelete='RESTRICT'),
                db.Field('staff', 'reference %s_budget_staff' % module, ondelete='RESTRICT'),
                db.Field('comments', length=256),
                migrate=migrate)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.comment = SPAN("*", _class="req")
db[table].equipment.requires = IS_IN_DB(db, '%s_budget_equipment.id' % module)
db[table].equipment.comment = SPAN("*", _class="req")
db[table].staff.requires = IS_IN_DB(db, '%s_budget_staff.id' % module)
db[table].staff.comment = SPAN("*", _class="req")
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

