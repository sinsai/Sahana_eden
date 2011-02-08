# -*- coding: utf-8 -*-

""" SYNC Synchronization, Model

    @author: Amer Tahir
    @author: nursix
    @version: 0.1.0

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

prefix = "sync"

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
resourcename = "setting"
tablename = "%s_%s" % (prefix, resourcename)
table = db.define_table(tablename,
                        Field("proxy"),
                        migrate=migrate, *s3_uid())

table.uuid.readable = True

table.proxy.label = T("Proxy-server")


# -----------------------------------------------------------------------------
# Synchronization status
#
resourcename = "status"
tablename = "%s_%s" % (prefix, resourcename)
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

resourcename = "notification"
tablename = "%s_%s" % (prefix, resourcename)
table = db.define_table(tablename,
                        Field("pid", "integer"),
                        Field("type", default=""),
                        Field("message", "text"),
                        Field("notified", "boolean", default=False),
                        migrate=migrate, *s3_timestamp())


# -----------------------------------------------------------------------------
# Peers
#
sync_peer_types = {
    1: T("Sahana Eden"),
    2: T("Sahana Agasti"),
    3: T("Ushahidi"),
    99: T("Other")
}

formats = ["xml", "json"]

resourcename = "peer"
tablename = "%s_%s" % (prefix, resourcename)
table = db.define_table(tablename,
                        #uuidstamp,
                        Field("name"),
                        Field("url", notnull=True),
                        Field("type", "integer"),
                        Field("username"),
                        Field("password", "password"),
                        Field("format"),
                        Field("allow_push", "boolean", default=True),
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

table.allow_push.label = T("Allowed to push")

table.policy.label = T("Default synchronization policy")

table.last_sync_time.label = T("Last synchronization time")
table.last_sync_time.writable = False

peer_id = S3ReusableField("peer_id", db.sync_peer, notnull=True,
                          requires = IS_ONE_OF(db, "sync_peer.id", "%(name)s"),
                          represent = lambda id: (id and [db.sync_peer(id).name] or [NONE])[0])


# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
def s3_sync_peer_oncreate(form):

    """ Create default job for Eden peers """

    table = db.sync_peer
    peer = db(table.id == form.vars.id).select(table.type,
                                               table.name,
                                               table.policy,
                                               table.ignore_errors,
                                               limitby=(0,1)).first()
    if peer and peer.type == 1:

        resources = s3_sync_primary_resources()

        jobtype = 1 # Eden<->Eden
        jobmode = 1 # Pull

        db.sync_job.insert(type = jobtype,
                           mode = jobmode,
                           peer_id = peer.id,
                           resources = resources,
                           policy = peer.policy,
                           ignore_errors = peer.ignore_errors)


# -----------------------------------------------------------------------------
s3xrc.model.configure(table,
    delete_onaccept=s3_sync_peer_ondelete,
    list_fields = ["id", "name", "uuid", "type", "url", "last_sync_time"])


# -----------------------------------------------------------------------------
# Sync Job - scheduled synchronization jobs
#
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

resourcename = "job"
tablename = "%s_%s" % (prefix, resourcename)
table = db.define_table(tablename,
                        Field("last_run", "datetime"),
                        Field("type", "integer"),
                        peer_id(),
                        Field("resources", "list:string"),
                        Field("mode", "integer"),
                        policy(),
                        Field("complete", "boolean", default=False),
                        Field("ignore_errors", "boolean", default=True),
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

s3xrc.model.add_component(prefix, resourcename,
                          joinby = dict(sync_peer="peer_id"),
                          multiple = True)


# -----------------------------------------------------------------------------
# Sync General Log - keeps log of all syncs
#
resourcename = "log"
tablename = "%s_%s" % (prefix, resourcename)
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

s3xrc.model.add_component(prefix, resourcename,
                          joinby = dict(sync_peer="peer_id"),
                          multiple = True)

s3xrc.model.configure(table,
    editable = False,
    listadd = False,
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
resourcename = "conflict"
tablename = "%s_%s" % (prefix, resourcename)
table = db.define_table(tablename,
                        peer_id(),
                        Field("tablename"),
                        Field("uuid", length=128),
                        Field("remote_record", "text"),
                        Field("remote_modified_by"),
                        Field("remote_modified_on", "datetime"),
                        Field("timestmp", "datetime"),
                        Field("resolved", "boolean"),
                        migrate=migrate)

table.remote_record.readable = False
table.remote_record.writable = False

table.timestmp.default = request.utcnow

table.resolved.default = False
table.resolved.represent = lambda value: value and T("yes") or T("no")

s3xrc.model.configure(table,
    insertable = False,
    listadd = False,
    list_fields = ["id", "timestmp", "peer_id", "tablename", "uuid", "resolved"])

s3.crud_strings[tablename] = Storage(
    title_display = T("Conflict Details"),
    title_list = T("Synchronization Conflicts"),
    title_update = T("Resolve Conflict"),
    subtitle_list = T("Unresolved Conflicts"),
    label_list_button = T("List Conflicts"),
    label_delete_button = T("Delete Entry"),
    msg_no_match = T("No log entries matching the query"),
    msg_list_empty = T("No conflicts logged"))

s3xrc.model.add_component(prefix, resourcename,
                          joinby = dict(sync_peer="peer_id"),
                          multiple = True)


# -----------------------------------------------------------------------------
# Peer registrations
#
resourcename = "registration"
tablename = "%s_%s" % (prefix, resourcename)
table = db.define_table(tablename,
                        Field("name"),
                        Field("uuid", length=128),
                        Field("type"),
                        migrate=migrate,
                        *(s3_authorstamp() + s3_ownerstamp() + s3_timestamp()))

table.created_by.label = T("Requested by")
table.created_by.readable = True
table.created_by.writable = False

table.created_on.label = T("Requested on")
table.created_on.readable = True
table.created_on.writable = False

table.uuid.label = T("Peer UID")

table.type.label = T("Peer Type")
table.type.requires = IS_IN_SET(sync_peer_types, zero=None)
table.type.represent = lambda opt: sync_peer_types.get(opt, UNKNOWN_OPT)
table.type.default = 1

s3xrc.model.configure(table,
    list_fields = ["id", "name", "type", "uuid", "created_by", "created_on"])

s3.crud_strings[tablename] = Storage(
    title_create = T("Peer Registration Request"),
    title_display = T("Peer Registration Details"),
    title_list = T("Peer Registration"),
    title_update = T("Edit Registration Details"),
    title_search = T("Search Registration Request"),
    subtitle_create = T("New Request"),
    subtitle_list = T("Pending Requests"),
    label_list_button = T("List Requests"),
    label_create_button = T("Add Request"),
    label_delete_button = T("Delete Request"),
    msg_record_created = T("Peer registration request added"),
    msg_record_modified = T("Peer registration request updated"),
    msg_record_deleted = T("Peer registration request deleted"),
    msg_list_empty = T("No pending registrations found"),
    msg_no_match = T("No pending registrations matching the query"))


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
