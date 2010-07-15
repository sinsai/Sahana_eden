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
                Field("uuid", length=36),                   # Our UUID for sync purposes
                Field("instance_url"),                      # URL our sahana instance is accessible on
                Field("Comments", length=128, default = "This is a SahanaEden instance, see http://eden.sahanafoundation.org" ),
                Field("beacon_service_url", default = "http://sync.eden.sahanafoundation.org/sync/beacon"), # URL of beacon service that our sahana instance is configured to work with
#                Field("sync_pools"),                        # Comma-separated list of sync pools we've subscribed to
                migrate=migrate)

sync_partner_instance_type_opts = {
    "Sahana Eden":T("Sahana Eden"),
    "Sahana Agasti":T("Sahana Agasti"),
    "Ushahidi":T("Ushahidi"),
    "Other":T("Other")
}

# Custom settings for sync partners
resource = "partner"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("uuid", length=36),                   # uuid of this partner
                Field("name", default="Sahana Eden Instance"), # name of the partner (descriptive title)
                Field("instance_url", default = "http://sync.eden.sahanafoundation.org/eden"), # URL of their instance
                Field("instance_type",                      # the type of instance => "SahanaEden", "SahanaAgasti", "Ushahidi", etc.
                    default="SahanaEden",
                    requires = IS_IN_SET(sync_partner_instance_type_opts) ),
                Field("username"),                          # username required to sync with this partner
                Field("password", "password"),              # password required to sync with this partner
                Field("comments", length=128),
#                Field("sync_pools"),                        # Comma-separated list of sync pools they're subscribed to
                opt_sync_policy,                            # sync_policy for this partner
                Field("last_sync_on", "datetime"),          # the last time we sync-ed with this partner
                migrate=migrate)

# Sync Conflicts - record all conflicts here
resource = "conflict"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("uuid", length=36),                   # uuid of the conflicting resource
                Field("resource_table"),                    # the table name of the conflicting resource
                Field("remote_record", "text"),             # String dump of the remote record
                Field("remote_modified_by"),                # the user who modified the remote resource, empty if it is None
                Field("remote_modified_on", "datetime"),    # the date and time when the remote record was modified
                Field("logged_on", "datetime"),             # the date and time when this conflict was logged
                Field("resolved", "boolean"),               # whether this conflict has been resolved or not
                migrate=migrate)

# Sync Log - Keeps log of all syncs
resource = "log"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("partner_uuid", length=36),           # uuid of remote system we synced with
                Field("partner_name"),                      # descriptive name of remote system we synced with
                Field("timestamp", "datetime"),             # the date and time when sync was performed
                Field("sync_resources", "text"),            # comma-separated list of resources synced
                Field("sync_errors", "text"),               # sync errors encountered
                Field("sync_mode"),                         # whether this was an "online" sync (standard sync mode) or "offline" sync (USB/File based)
                Field("complete_sync", "boolean"),          # whether all resources were synced (complete sync) or only those modified since the last sync (partial sync)
                Field("sync_method"),                       # whether this was a Pull only, Push only, Remote Push or a Pull-Push sync operation
                migrate=migrate)

sync_schedule_period_opts = {
    "h":T("Hourly"),
    "d":T("Daily"),
    "w":T("Weekly"),
    "o":T("Just Once")
}

sync_schedule_job_type_opts = {
    1:T("Sahana Eden <=> Sahana Eden sync"),
    2:T("Sahana Eden <= Other sync (Sahana Agasti, Ushahidi, etc.)")
}

# Scheduled sync jobs
resource = "schedule"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("description", length=128),           # brief description about the scheduled job
                Field("period",                             # schedule interval period, either hourly, "h", daily, "d", weekly, "w" or one-time, "o"
                    length=10,
                    notnull=True,
                    default="d",
                    requires = IS_IN_SET(sync_schedule_period_opts) ),
                Field("hours", "integer", default=4),       # specifies the number of hours when hourly period is specified in 'period' field
                Field("days_of_week", length=30),           # comma-separated list of the day(s) of the week when job runs on weekly basis.
                                                            # A day in a week is represented as a number having value between 1 (Monday) and 7 (Sunday)
                Field("time_of_day", "time"),               # the time (at day_of_week) when job runs on a weekly basis
                Field("job_type", "integer", default=1,     # This specifies the type of job: 1 - SahanaEden <=> SahanaEden sync,
                    requires = IS_IN_SET(sync_schedule_job_type_opts) ),
                                                            # 2 - SahanaEden <= Other sync (could be SahanaAgasti, Ushahidi, etc.)
                Field("job_command", "text"),               # sync command to execute when this job runs. This command is encoded as a JSON formatted object.
                                                            # It contains the UUID of the sync partner (if present, 0 otherwise),
                                                            # the instance URL (would be root location for Eden instance and full URL for other instance
                                                            # types such as Agasti, Ushahidi or possibly spreadsheet source), the list of modules along
                                                            # with resources within them to sync, whether this would be a complete or partial sync
                                                            # (partial sync only retrieves data modified after the last sync, complete sync fetches all),
                                                            # whether this sync would be a two-way (both push and pull) or one-way (push or pull),
                                                            # and sync policy (default policy is taken from the sync partner's record
                Field("running", "boolean"),                # indicates whether this job is currently executing or not
                Field("last_run", "datetime"),              # the date and time of last scheduled run
                Field("enabled", "boolean",                 # whether this schedule is enabled or not. Useful in cases when you want to temporarily
                    notnull=True, default=True),            # disable a schedule
                migrate=migrate)
