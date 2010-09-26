# -*- coding: utf-8 -*-

""" Synchronization - model

    @author: Amer Tahir
    @author: nursix

    Resources:

        setting         - Global synchronization settings
        status          - Status of manual synchronization
        notification    - Queue for notification messages
        peer            - Synchronization peers
         |
         +----job       - Synchronization jobs (per peer)
         +----log       - Synchronization history log
        conflict        - Queue for synchronization conflicts

"""

module = "sync"

import sys

# -----------------------------------------------------------------------------
# Synchronization policy
#
sync_policy_opts = {
    0: T("No synchronization"),
    1: T("Manual"),             # choose records manually
    2: T("Import"),             # import new records, do not update existing records
    3: T("Replace"),            # import new records and update existing records to peer version
    4: T("Update"),             # update existing records to peer version, do not import new records
    5: T("Replace if Newer"),   # import new records, update existing records to newer version
    6: T("Update if Newer"),    # do not import new records, only update existing records to newer version
    7: T("Import if Master"),   # import master records, do not update existing records
    8: T("Replace if Master"),  # import master records and update existing records to master version
    9: T("Update if Master"),   # update existing records to master version, do not import new records
    #10: T("Role-based")         # not implemented yet
}

# Reusable field
policy = S3ReusableField("policy", "integer", notnull=True,
                         requires = IS_IN_SET(sync_policy_opts),
                         default = 5,
                         represent = lambda opt: sync_policy_opts.get(opt, UNKNOWN_OPT))

# -----------------------------------------------------------------------------
# Settings
#
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, #uuidstamp,
                        Field("proxy"),
                        migrate=migrate, *s3_uid())


table.uuid.readable = True

table.proxy.label = T("Proxy-server")


# -----------------------------------------------------------------------------
# Synchronization status
#
resource = "status"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        Field("locked", "boolean"),
                        Field("halt", "boolean"),
                        Field("jobs", "text"),
                        Field("start_time", "datetime"),
                        Field("done", "text"),
                        Field("pending", "text"),
                        Field("errors", "text"),
                        migrate=migrate)


# -----------------------------------------------------------------------------
# Notifications - notification messages queue
#
sync_message_types = ("OK", "ERROR", "SUCCESS", "FAILURE", "DONE", "SKIPPED", "")

resource = "notification"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp,
                        Field("pid", "integer"),
                        Field("type", default=""),
                        Field("message", "text"),
                        Field("notified", "boolean", default=False),
                        migrate=migrate)


# -----------------------------------------------------------------------------
# Peers
#
sync_peer_types = {
    1: T("Sahana Eden"),
    2: T("Sahana Agasti"),
    3: T("Ushahidi"),
    99: T("Other")
}

formats = [f for f in s3xrc.xml_export_formats]
formats += [f for f in s3xrc.xml_import_formats if f not in formats]
formats += [f for f in s3xrc.json_export_formats if f not in formats]
formats += [f for f in s3xrc.json_import_formats if f not in formats]

resource = "peer"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        #uuidstamp,
                        Field("name"),
                        Field("url", notnull=True),
                        Field("type", "integer"),
                        Field("username"),
                        Field("password", "password"),
                        Field("format"),
                        policy(),
                        Field("ignore_errors", "boolean", default=False),
                        Field("last_sync_time", "datetime"),
                        migrate=migrate, *s3_uid())


table.uuid.readable = True
table.uuid.writable = True

table.name.requires = IS_NOT_EMPTY()
table.name.default = "Sahana Eden Instance"

table.url.requires = IS_NOT_EMPTY()
table.url.default = "http://sync.eden.sahanafoundation.org/eden"

table.type.requires = IS_IN_SET(sync_peer_types, zero=None)
table.type.represent = lambda opt: sync_peer_types.get(opt, UNKNOWN_OPT)
table.type.default = 1

table.format.requires = IS_IN_SET(formats, zero=None)
table.format.default = "xml"

table.policy.label = T("Default synchronization policy")

table.last_sync_time.label = T("Last synchronization time")
table.last_sync_time.writable = False

peer_id = S3ReusableField("peer_id", db.sync_peer, notnull=True,
                          requires = IS_ONE_OF(db, "sync_peer.id", "%(name)s"),
                          represent = lambda id: (id and [db.sync_peer(id).name] or [NONE])[0])
#peer_id = db.Table(None, "peer_id",
                   #Field("peer_id", db.sync_peer, notnull=True,
                         #requires = IS_ONE_OF(db, "sync_peer.id", "%(name)s"),
                         #represent = lambda id: (id and [db.sync_peer(id).name] or [NONE])[0]))

def s3_sync_peer_ondelete(row):

    """ Delete all jobs with this peer """

    uuid = row.get("uuid")
    if uuid:
        schedule = db.sync_schedule
        jobs = db().select(schedule.id, schedule.job_command)
        jobs_del = []
        for job in jobs:
            try:
                job_cmd = json.loads(job.job_command)
            except:
                continue
            else:
                if job_cmd["partner_uuid"] == uuid:
                    jobs_del.append(job.id)
        db(schedule.id.belongs(jobs_del)).delete()


def s3_sync_peer_oncreate(form):

    """ Create default job for Eden peers """

    table = db.sync_peer
    peer = db(table.id == form.id).select(table.uuid,
                                          table.name,
                                          table.policy,
                                          limitby=(0,1)).first()
    if not peer or not peer.uuid:
        return

    tablenames = s3_sync_primary_resources()

    job_command = json.dumps(dict(
        partner_uuid = uuid,
        policy = peer.policy,
        resources = ",".join(tablenames),
        complete = False,
        mode = 3
    ))

    db.sync_schedule.insert(
        comments = "auto-generated job for %s" % peer.name,
        period = "m",
        job_type = 1,
        job_command = json.dumps(sch_cmd),
        last_run = None,
        enabled = True)


s3xrc.model.configure(table,
    delete_onaccept=s3_sync_peer_ondelete,
    list_fields = ["id", "name", "uuid", "type", "url", "last_sync_time"])


# -----------------------------------------------------------------------------
# Sync Schedule - scheduled sync jobs
#
#sync_schedule_period_opts = {
    #"h": T("Hourly"),
    #"d": T("Daily"),
    #"w": T("Weekly"),
    #"o": T("Just Once"),
    #"m": T("Manual")
#}

#sync_schedule_job_type_opts = {
    #1: T("Sahana Eden <=> Sahana Eden"),
    #2: T("Sahana Eden <=> Other (Sahana Agasti, Ushahidi, etc.)")
#}

#resource = "schedule"
#tablename = "%s_%s" % (module, resource)
#table = db.define_table(tablename, timestamp,
                        #Field("comments", length=128),              # brief comments about the scheduled job
                        #Field("period",                             # schedule interval period, either hourly, "h", daily, "d", weekly, "w" or one-time, "o"
                              #length=10,
                              #notnull=True,
                              #default="m",
                              #requires = IS_IN_SET(sync_schedule_period_opts) ),
                        #Field("hours", "integer", default=4),   # specifies the number of hours when hourly period is specified in 'period' field
                        #Field("days_of_week", length=40),       # comma-separated list of the day(s) of the week when job runs on weekly basis.
                                                                ## A day in a week is represented as a number ranging from 1 to 7 (1 = Sunday, 7 = Saturday)
                        #Field("time_of_day", "time"),           # the time (at day_of_week) when job runs on a weekly or daily basis
                        #Field("runonce_datetime", "datetime"),  # the date and time when job runs just once
                        #Field("job_type", "integer", default=1, # This specifies the type of job: 1 - SahanaEden <=> SahanaEden sync,
                              #requires = IS_IN_SET(sync_schedule_job_type_opts) ),
                                                            ## 2 - SahanaEden <= Other sync (could be SahanaAgasti, Ushahidi, etc.)
                        #Field("job_command", "text", notnull=True), # sync command to execute when this job runs. This command is encoded as a JSON formatted object.
                                                            ## It contains the UUID of the sync partner, the list of modules along
                                                            ## with resources within them to sync, whether this would be a complete or partial sync
                                                            ## (partial sync only retrieves data modified after the last sync, complete sync fetches all),
                                                            ## whether this sync would be a two-way (both push and pull) or one-way (push or pull),
                                                            ## and sync policy (default policy is taken from the sync partner's record)
                        #Field("last_run", "datetime"),      # the date and time of last scheduled run
                        #Field("enabled", "boolean",         # whether this schedule is enabled or not. Useful in cases when you want to temporarily
                              #default=True),                # disable a schedule
                        #migrate=migrate)

sync_job_types = {
    1: T("Sahana Eden <=> Sahana Eden"),
    2: T("Sahana Eden <=> Other")
}

sync_job_intervals = {
    "h": T("hourly"),
    "d": T("daily"),
    "w": T("weekly"),
    "o": T("once"),
    "m": T("manual")
}

sync_modes = {
    1: T("Import"),
    2: T("Export"),
    3: T("Import and Export")
}

sync_weekdays = {
    1: T("Monday"),
    2: T("Tuesday"),
    3: T("Wednesday"),
    4: T("Thursday"),
    5: T("Friday"),
    6: T("Saturday"),
    7: T("Sunday"),
}

resource = "job"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        #uuidstamp, timestamp,
                        Field("last_run", "datetime"),
                        Field("type", "integer"),
                        peer_id(),
                        Field("resources", "list:string"),
                        Field("mode", "integer"),
                        policy(),
                        Field("complete", "boolean", default=False),
                        Field("run_interval", default="m"),
                        Field("hours"),
                        Field("days", "list:integer"),
                        Field("runonce_on"),
                        Field("enabled", "boolean", default=True),
                        migrate=migrate,
                        *(s3_uid()+s3_timestamp()))

table.last_run.represent = lambda value: value and str(value) or T("never")

table.type.requires = IS_IN_SET(sync_job_types, zero=None)
table.type.represent = lambda opt: sync_job_types.get(opt, UNKNOWN_OPT)
table.type.default = 1

table.mode.requires = IS_IN_SET(sync_modes, zero=None)
table.mode.represent = lambda opt: sync_modes.get(opt, UNKNOWN_OPT)
table.mode.default = 1

table.policy.requires = IS_EMPTY_OR(IS_IN_SET(sync_policy_opts, zero=None))

table.last_run.writable = False

table.run_interval.requires = IS_IN_SET(sync_job_intervals, zero=None)
table.run_interval.represent = lambda opt: sync_job_intervals.get(opt, UNKNOWN_OPT)

table.days.requires = IS_EMPTY_OR(IS_IN_SET(sync_weekdays, zero=None, multiple=True))
table.days.default = sync_weekdays.keys()

s3xrc.model.add_component(module, resource,
                          joinby = dict(sync_peer="peer_id"),
                          multiple = True)


# -----------------------------------------------------------------------------
# Sync General Log - keeps log of all syncs
#
resource = "log"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        peer_id(),
                        Field("timestmp", "datetime"),
                        Field("resources", "text"),
                        Field("errors", "text"),
                        Field("mode", "integer"),
                        Field("complete", "boolean"),
                        Field("run_interval"),
                        migrate=migrate)

table.peer_id.label = T("Peer")
table.timestmp.label = T("Date/Time")
table.resources.label = T("Resources")
table.errors.label = T("Errors")
table.mode.label = T("Mode")
table.mode.represent = lambda opt: sync_modes.get(opt, UNKNOWN_OPT)
table.complete.label = T("Records")
table.complete.represent = lambda val: val and T("all records") or T("updates only")
table.run_interval.label = T("Run Interval")
table.run_interval.represent = lambda opt: sync_job_intervals.get(opt, UNKNOWN_OPT)

s3xrc.model.add_component(module, resource,
                          joinby = dict(sync_peer="peer_id"),
                          multiple = True,
                          editable = False,
                          listadd = False,
                          deletable = True)

s3xrc.model.configure(table,
    list_fields = ["id",
        "timestmp",
        "peer_id",
        "mode",
        "resources",
        "complete",
        "run_interval",
        "errors"])

# -----------------------------------------------------------------------------
# Synchronization conflicts
#
resource = "conflict"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        Field("peer_uuid", length=128),
                        Field("tablename"),
                        Field("uuid", length=128),
                        Field("remote_record", "text"),
                        Field("remote_modified_by"),
                        Field("remote_modified_on", "datetime"),
                        Field("timestmp", "datetime"),
                        Field("resolved", "boolean"),
                        migrate=migrate)


# -----------------------------------------------------------------------------
def s3_sync_push_message(message, type="", pid=None):

    """ Push a notification message to the queue """

    table = db.sync_notification

    if message:
        if not pid:
            status = db().select(db.sync_status.id, limitby=(0,1)).first()
            if status:
                pid = status.id
            else:
                pid = 0

        success = table.insert(pid=pid, message=message, type=type)

        if success:
            #print >> sys.stderr, "[%s] %s: %s" % (pid, type or "OK", message)
            db.commit()
            return True

    return False


# -----------------------------------------------------------------------------
def s3_sync_get_messages(pid=None):

    """ Get pending notification messages from the queue """

    table = db.sync_notification

    if pid is None:
        status = db().select(db.sync_status.id, limitby=(0,1)).first()
        if status:
            pid = status.id

    if pid is not None:
        query = ((table.pid == pid) | (table.pid == 0)) & \
                (table.notified == False)
    else:
        query = (table.notified == False)

    rows = db(query).select(table.id, table.message, table.type)
    ids = [row.id for row in rows]
    messages = [dict(type=row.type,
                     message=row.message) for row in rows]

    if ids:
        db(table.id.belongs(ids)).update(notified=True)

    return messages


# -----------------------------------------------------------------------------
def s3_sync_clear_messages():

    """ Remove notified messages from the queue """

    table = db.sync_notification
    db(table.notified == True).delete()


# -----------------------------------------------------------------------------
def s3_sync_init_messages():

    """ Remove all (pid-bound) messages from the queue """

    table = db.sync_notification
    db(table.pid > 0).delete()


# -----------------------------------------------------------------------------
def s3_sync_primary_resources():

    """ Find primay resources (tablenames) """

    modules = deployment_settings.modules
    tablenames = []

    for t in db.tables:
        table = db[t]

        if t.find("_") == -1:
            continue
        prefix, name = t.split("_", 1)

        if prefix in modules and \
        "modified_on" in table.fields and \
        "uuid" in table.fields:
            is_component = False
            if not s3xrc.model.has_components(prefix, name):
                hook = s3xrc.model.components.get(name, None)
                if hook:
                    link = hook.get("_component", None)
                    if link and link.tablename == t:
                        continue
                    for h in hook.values():
                        if isinstance(h, dict):
                            link = h.get("_component", None)
                            if link and link.tablename == t:
                                is_component = True
                                break
                    if is_component:
                        continue

            tablenames.append(t)

    return tablenames

# -----------------------------------------------------------------------------
