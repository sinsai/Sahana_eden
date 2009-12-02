# -*- coding: utf-8 -*-

module = 'budget'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)

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

# Items
budget_cost_type_opts = {
    1:T('One-time'),
    2:T('Recurring')
    }
opt_budget_cost_type = db.Table(None, 'budget_cost_type',
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
opt_budget_category_type = db.Table(None, 'budget_category_type',
                            Field('category_type', 'integer', notnull=True,
                                requires = IS_IN_SET(budget_category_type_opts),
                                default = 1,
                                label = T('Category'),
                                represent = lambda opt: opt and budget_category_type_opts[opt]))
resource = 'item'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                opt_budget_category_type,
                Field('code', length=128, notnull=True, unique=True),
                Field('description', notnull=True),
                opt_budget_cost_type,
                Field('unit_cost', 'double', default=0.00),
                Field('monthly_cost', 'double', default=0.00),
                Field('minute_cost', 'double', default=0.00),
                Field('megabyte_cost', 'double', default=0.00),
                Field('comments'),
                migrate=migrate)

# Kits
resource = 'kit'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('code', length=128, notnull=True, unique=True),
                Field('description'),
                Field('total_unit_cost', 'double', writable=False),
                Field('total_monthly_cost', 'double', writable=False),
                Field('total_minute_cost', 'double', writable=False),
                Field('total_megabyte_cost', 'double', writable=False),
                Field('comments'),
                migrate=migrate)

# Kit<>Item Many2Many
resource = 'kit_item'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('kit_id', db.budget_kit),
                Field('item_id', db.budget_item, ondelete='RESTRICT'),
                Field('quantity', 'integer', default=1, notnull=True),
                migrate=migrate)

# Bundles
resource = 'bundle'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', length=128, notnull=True, unique=True),
                Field('description'),
                Field('total_unit_cost', 'double', writable=False),
                Field('total_monthly_cost', 'double', writable=False),
                Field('comments'),
                migrate=migrate)

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

# Staff Types
budget_currency_type_opts = {
    1:T('Dollars'),
    2:T('Euros'),
    3:T('Pounds')
    }
opt_budget_currency_type = db.Table(None, 'budget_currency_type',
                    db.Field('currency_type', 'integer', notnull=True,
                    requires = IS_IN_SET(budget_currency_type_opts),
                    default = 1,
                    label = T('Currency'),
                    represent = lambda opt: opt and budget_currency_type_opts[opt]))

resource = 'staff'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', length=128, notnull=True, unique=True),
                Field('grade', notnull=True),
                Field('salary', 'integer', notnull=True),
                opt_budget_currency_type,
                Field('travel', 'integer', default=0),
                # Shouldn't be grade-dependent, but purely location-dependent
                #Field('subsistence', 'double', default=0.00),
                # Location-dependent
                #Field('hazard_pay', 'double', default=0.00),
                Field('comments'),
                migrate=migrate)

# Locations
resource = 'location'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('code', length=3, notnull=True, unique=True),
                Field('description'),
                Field('subsistence', 'double', default=0.00),
                Field('hazard_pay', 'double', default=0.00),
                Field('comments'),
                migrate=migrate)

# Projects
resource = 'project'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('code', length=128, notnull=True, unique=True),
                Field('title'),
                Field('comments'),
                migrate=migrate)

# Budgets
resource = 'budget'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', length=128, notnull=True, unique=True),
                Field('description'),
                Field('total_onetime_costs', 'double', writable=False),
                Field('total_recurring_costs', 'double', writable=False),
                Field('comments'),
                migrate=migrate)

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
