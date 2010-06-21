# -*- coding: utf-8 -*-

"""
    Synchronization
"""

module = "sync"

sync_policy_opts = {
    0:T("No Sync"),
    1:T("Keep Local"),
    2:T("Replace with Remote"),
    3:T("Newer Timestamp"),
    4:T("Role-based"),
    5:T("Choose Manually")
}

# Sync Policy
opt_sync_policy = db.Table(None, "sync_policy",
                        Field("policy", "integer", notnull=True,
                            requires = IS_IN_SET(sync_policy_opts),
                            default = 3,
                            represent = lambda opt: sync_policy_opts.get(opt, UNKNOWN_OPT)))

# Settings
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("uuid", length=36),   # Our UUID for sync purposes
                Field("instance_url"),      # URL our sahana instance is accessible on
                Field("peer_description", length=128, default = "This is a SahanaEden instance, see http://eden.sahanafoundation.org" ),
                Field("beacon_service_url", default = "http://sync.eden.sahanafoundation.org/sync/beacon"), # URL of beacon service that our sahana instance is configured to work with
                Field("sync_pools"),        # Comma-separated list of sync pools we've subscribed to
                migrate=migrate)

# Custom settings for sync partners
resource = "partner"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("uuid", length=36),           # uuid of this partner
                Field("instance_url", default = "http://eden.sahanafoundation.org/"), # URL of their instance
                Field("instance_type"),             # the type of instance => "SahanaEden", "SahanaAgasti", "Ushahidi", etc.
                Field("username"),                  # login username for this partner
                Field("password"),                  # login password for this partner
                Field("peer_description", length=64),
                Field("sync_pools"),                # Comma-separated list of sync pools they're subscribed to
                opt_sync_policy,                    # sync_policy for this partner
                Field("last_sync_on", "datetime"),  # the last time we sync-ed with this partner
                migrate=migrate)

# Sync Conflicts - record all conflicts here
resource = "conflict"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("uuid", length=36),                   # uuid of the conflicting resource
                Field("remote_record"),                     # String dump of the remote record
                Field("remote_modified_by"),                # the user who modified the remote resource, empty if it is None
                Field("remote_modified_on", "datetime"),    # the date and time when the remote record was modified
                Field("resolved", "boolean"),               # whether this conflict has been resolved or not
                migrate=migrate)

# Sync Log / Keeps log of all webservices calls. Used to view sync history
resource = "log"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("uuid", length=36),           # uuid of remote system we synced with
                Field("timestamp", "datetime"),     # the date and time when sync was performed
                Field("sync_tables_success"),       # comma-separated list of tables successfully synced
                Field("sync_tables_error"),         # comma-separated list of tables that couldn't be synced
                Field("sync_mode", "string"),       # whether this was an "online" sync (standard sync mode) or "offline" sync (USB/File based)
                Field("complete_sync", "boolean"),  # whether all resources were synced (complete sync) or only those modified since the last sync (partial sync)
                migrate=migrate)
