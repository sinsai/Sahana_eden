# -*- coding: utf-8 -*-

module = 'sync'

sync_policy_opts = {
    1:T('Newer Timestamp'),
    2:T('Keep All'),
    3:T('Replace All')
    }
opt_sync_policy = SQLTable(None, 'sync_policy',
                        Field('policy', 'integer', notnull=True,
                            requires = IS_IN_SET(sync_policy_opts),
                            default = 1,
                            represent = lambda opt: opt and sync_policy_opts[opt]))
# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                Field('uuid'),      # Our UUID for sync purposes
                opt_sync_policy,    # Default sync_policy for new partners
                Field('username'),  # Default login username for new partners
                Field('password'),  # Default login password for new partners
                migrate=migrate)
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read = False,
        audit_write = False
    )

# Custom settings for sync partners
resource = 'partner'
table = module + '_' + resource
db.define_table(table,
                Field('uuid'),
                opt_sync_policy,    # sync_policy for this partner
                Field('username'),  # login username for this partner
                Field('password'),  # login password for this partner
                migrate=migrate)

# Sync Log / Keeps log of all webservices calls. Used to view sync history
resource = 'log'
table = module + '_' + resource
db.define_table(table,
                db.Field('uuid'), # different from reusable uuidstamp: uuid of remote system we synced with
                db.Field('function', 'string'),
                db.Field('timestamp', 'datetime'), # different from reusable timestamp
                db.Field('format', 'string'),
                migrate=migrate)
