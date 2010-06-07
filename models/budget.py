# -*- coding: utf-8 -*-

"""
    Budgetting module

    @author: Fran Boon
"""

module = "budget"
if deployment_settings.has_module(module):

    # Settings
    resource = 'setting'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                    Field('audit_read', 'boolean'),
                    Field('audit_write', 'boolean'),
                    migrate=migrate)

    # Parameters
    # Only record 1 is used
    resource = 'parameter'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp,
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
                                # default = 1,
                                label = T('Cost Type'),
                                represent = lambda opt: budget_cost_type_opts.get(opt, UNKNOWN_OPT)))
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
                                    # default = 1,
                                    label = T('Category'),
                                    represent = lambda opt: budget_category_type_opts.get(opt, UNKNOWN_OPT)))
    resource = 'item'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
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

    s3xrc.model.configure(table, onaccept=lambda form: item_cascade(form))

    # Kits
    resource = 'kit'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('code', length=128, notnull=True, unique=True),
                    Field('description'),
                    Field('total_unit_cost', 'double', writable=False),
                    Field('total_monthly_cost', 'double', writable=False),
                    Field('total_minute_cost', 'double', writable=False),
                    Field('total_megabyte_cost', 'double', writable=False),
                    Field('comments'),
                    migrate=migrate)

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

    def kit_total(form):
        "Calculate Totals for the Kit specified by Form"
        if 'kit_id' in form.vars:
            # called by kit_item()
            kit = form.vars.kit_id
        else:
            # called by kit()
            kit = form.vars.id
        kit_totals(kit)

    s3xrc.model.configure(table,
                          onaccept=lambda form: kit_total(form))

    # Kit<>Item Many2Many
    resource = 'kit_item'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('kit_id', db.budget_kit),
                    Field('item_id', db.budget_item, ondelete='RESTRICT'),
                    Field('quantity', 'integer', default=1, notnull=True),
                    migrate=migrate)

    # Bundles
    resource = 'bundle'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('name', length=128, notnull=True, unique=True),
                    Field('description'),
                    Field('total_unit_cost', 'double', writable=False),
                    Field('total_monthly_cost', 'double', writable=False),
                    Field('comments'),
                    migrate=migrate)

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

    def bundle_total(form):
        "Calculate Totals for the Bundle specified by Form"
        if 'bundle_id' in form.vars:
            # called by bundle_kit_item()
            bundle = form.vars.bundle_id
        else:
            # called by bundle()
            bundle = form.vars.id
        bundle_totals(bundle)

    s3xrc.model.configure(table,
                          onaccept=lambda form: bundle_total(form))

    # Bundle<>Kit Many2Many
    resource = 'bundle_kit'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, deletion_status,
                    Field('bundle_id', db.budget_bundle),
                    Field('kit_id', db.budget_kit, ondelete='RESTRICT'),
                    Field('quantity', 'integer', default=1, notnull=True),
                    Field('minutes', 'integer', default=0, notnull=True),
                    Field('megabytes', 'integer', default=0, notnull=True),
                    migrate=migrate)

    # Bundle<>Item Many2Many
    resource = 'bundle_item'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, deletion_status,
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
                        Field('currency_type', 'integer', notnull=True,
                        requires = IS_IN_SET(budget_currency_type_opts),
                        # default = 1,
                        label = T('Currency'),
                        represent = lambda opt: budget_currency_type_opts.get(opt, UNKNOWN_OPT)))

    resource = 'staff'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
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
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('code', length=3, notnull=True, unique=True),
                    Field('description'),
                    Field('subsistence', 'double', default=0.00),
                    Field('hazard_pay', 'double', default=0.00),
                    Field('comments'),
                    migrate=migrate)

    # Projects
    resource = 'project'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('code', length=128, notnull=True, unique=True),
                    Field('title'),
                    Field('comments'),
                    migrate=migrate)

    # Budgets
    resource = 'budget'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('name', length=128, notnull=True, unique=True),
                    Field('description'),
                    Field('total_onetime_costs', 'double', writable=False),
                    Field('total_recurring_costs', 'double', writable=False),
                    Field('comments'),
                    migrate=migrate)

    # Budget<>Bundle Many2Many
    resource = 'budget_bundle'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, deletion_status,
                    Field('budget_id', db.budget_budget),
                    Field('project_id', db.budget_project),
                    Field('location_id', db.budget_location),
                    Field('bundle_id', db.budget_bundle, ondelete='RESTRICT'),
                    Field('quantity', 'integer', default=1, notnull=True),
                    Field('months', 'integer', default=3, notnull=True),
                    migrate=migrate)

    # Budget<>Staff Many2Many
    resource = 'budget_staff'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, deletion_status,
                    Field('budget_id', db.budget_budget),
                    Field('project_id', db.budget_project),
                    Field('location_id', db.budget_location),
                    Field('staff_id', db.budget_staff, ondelete='RESTRICT'),
                    Field('quantity', 'integer', default=1, notnull=True),
                    Field('months', 'integer', default=3, notnull=True),
                    migrate=migrate)
