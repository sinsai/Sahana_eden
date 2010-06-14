# -*- coding: utf-8 -*-

"""
    Synchronization
"""

module = 'sync'

sync_policy_opts = {
    0:T('No Sync'),
    1:T('Keep Local'),
    2:T('Keep Remote'),
    3:T('Newer Timestamp'),
    4:T('Role-based'),
    5:T('Choose Manually')
}

# Sync Policy
opt_sync_policy = db.Table(None, 'sync_policy',
                        Field('policy', 'integer', notnull=True,
                            requires = IS_IN_SET(sync_policy_opts),
                            default = 3,
                            represent = lambda opt: sync_policy_opts.get(opt, UNKNOWN_OPT)))

# Settings
resource = 'setting'
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field('uuid', length=36),   # Our UUID for sync purposes
                Field('instance_url'), # URL our sahana instance is accessible on
                Field('peer_description', length=128, default = "This is a SahanaEden instance, see http://eden.sahanafoundation.org" ),
                Field('beacon_service_url', default = "http://sync.eden.sahanafoundation.org/sync/beacon"), # URL of beacon service that our sahana instance is configured to work with
                Field('sync_pools'),        # Comma-separated list of sync pools we've subscribed to
                migrate=migrate)

# Custom settings for sync partners
resource = 'partner'
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field('uuid', length=36),   # uuid of this partner
                Field('instance_url', default = "http://eden.sahanafoundation.org/"), # URL of their instance
                Field('instance_type'),     # the type of instance => "SahanaEden", "SahanaAgasti", "Ushahidi", etc.
                Field('username'),          # login username for this partner
                Field('password'),          # login password for this partner
                Field('peer_description', length=64),
                Field('sync_pools'),        # Comma-separated list of sync pools they're subscribed to
                opt_sync_policy,            # sync_policy for this partner
                Field('last_sync_on', 'datetime'), # the last time we sync-ed with this partner
                migrate=migrate)

                # Sync Log / Keeps log of all webservices calls. Used to view sync history
resource = 'log'
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field('uuid', length=36), # different from reusable uuidstamp: uuid of remote system we synced with
                Field('function', 'string'),
                Field('timestamp', 'datetime'), # different from reusable timestamp
                Field('format', 'string'),
                migrate=migrate)
