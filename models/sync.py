# -*- coding: utf-8 -*-

module = 'sync'

sync_policy_opts = {
    1:T('No Sync'),
    2:T('Newer Timestamp'),
    3:T('Keep All'),
    4:T('Replace All')
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
                Field('uuid', length=36),   # Our UUID for sync purposes
                opt_sync_policy,            # Default sync_policy for new partners
                Field('username'),          # Default login username for new partners
                Field('password'),          # Default login password for new partners
                Field('webservice_port', 'integer', default = 8000), # Port which our webservice is accessible on
                Field('rpc_service_url', default = "/sync/call/jsonrpc"), # URL our webservice is accessible on
                Field('zeroconf_description', length=64, default = "This is a SahanaPy instance, see http://www.sahanapy.org" ),
                migrate=migrate)
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        uuid = uuid.uuid4()
    )

# Custom settings for sync partners
resource = 'partner'
table = module + '_' + resource
db.define_table(table,
                Field('uuid', length=36), # uuid of this partner
                opt_sync_policy,    # sync_policy for this partner
                Field('username'),  # login username for this partner
                Field('password'),  # login password for this partner
                Field('webservice_port', 'integer', default = 8000), # Port which their webservice is accessible on
                Field('rpc_service_url', default = "/sync/call/jsonrpc"), # URL their webservice is accessible on
                Field('description', length=64),
                migrate=migrate)

# Sync Log / Keeps log of all webservices calls. Used to view sync history
resource = 'log'
table = module + '_' + resource
db.define_table(table,
                Field('uuid', length=36), # different from reusable uuidstamp: uuid of remote system we synced with
                Field('function', 'string'),
                Field('timestamp', 'datetime'), # different from reusable timestamp
                Field('format', 'string'),
                migrate=migrate)
