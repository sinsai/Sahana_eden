# -*- coding: utf-8 -*-

""" Synchronization

    @author: Amer Tahir

"""

module = "sync"

# -----------------------------------------------------------------------------
# Sync Policy
#
sync_policy_opts = {
    0: T("No synchronization"),
    1: T("Manual"),             # choose records manually
    2: T("Import"),             # import new records, do not update existing records
    3: T("Replace"),            # import new records and update existing records to peer version
    4: T("Update"),             # update existing records to peer version, do not import new records
    5: T("Replace/Newer"),      # import new records, update existing records to newer version
    6: T("Update/Newer"),       # do not import new records, only update existing records to newer version
    7: T("Import/Master"),      # import master records, do not update existing records
    8: T("Replace/Master"),     # import master records and update existing records to master version
    9: T("Update/Master"),      # update existing records to master version, do not import new records
    #10: T("Role-based") # not implemented yet
}

# reusable field
policy = db.Table(None, "policy",
                  Field("policy", "integer", notnull=True,
                        requires = IS_IN_SET(sync_policy_opts),
                        default = 3,
                        represent = lambda opt: sync_policy_opts.get(opt, UNKNOWN_OPT)))

# -----------------------------------------------------------------------------
# Settings
#
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        uuidstamp,
                        Field("beacon_service_url"),
                        Field("sync_pools"),
                        Field("proxy"),
                        #Field("comments", length=128),
                        migrate=migrate)

table.uuid.readable = True

table.beacon_service_url.readable = False
table.beacon_service_url.writable = False
table.beacon_service_url.default = "http://sync.eden.sahanafoundation.org/sync/beacon"

table.sync_pools.readable = False
table.sync_pools.writable = False

table.proxy.label = T("Proxy-server")

# -----------------------------------------------------------------------------
# Sync partners
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

# Custom settings for sync partners
resource = "partner"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        uuidstamp,
                        Field("name"),
                        Field("url", notnull=True),
                        Field("type", "integer"),
                        Field("username"),
                        Field("password", "password"),
                        Field("format"),
                        Field("sync_pools"),
                        policy,
                        Field("last_sync_on", "datetime"),
                        #Field("comments", length=128),
                        migrate=migrate)

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

table.sync_pools.readable = False
table.sync_pools.writable = False

table.policy.label = T("Default synchronization policy")

table.last_sync_on.label = T("Last synchronization on")
table.last_sync_on.writable = False


def s3_sync_partner_ondelete(row):

    """ Delete all jobs with this partner """

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


def s3_sync_partner_onaccept(form):

    """ Create default job for Eden peers """

    table = db.sync_partner
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

    print job_command

    db.sync_schedule.insert(
        comments = "auto-generated job for %s" % peer.name,
        period = "m",
        job_type = 1,
        job_command = json.dumps(sch_cmd),
        last_run = None,
        enabled = True)


s3xrc.model.configure(table,
    delete_onaccept=s3_sync_partner_ondelete,
    list_fields = ["id", "name", "uuid", "type", "url", "last_sync_on"])


# -----------------------------------------------------------------------------
# Sync Conflicts Log - record all conflicts here
#
resource = "conflict"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        Field("uuid", length=36, notnull=True),     # uuid of the conflicting resource
                        Field("resource_table"),                    # the table name of the conflicting resource
                        Field("remote_record", "text"),             # String dump of the remote record
                        Field("remote_modified_by"),                # the user who modified the remote resource, empty if it is None
                        Field("remote_modified_on", "datetime"),    # the date and time when the remote record was modified
                        Field("logged_on", "datetime"),             # the date and time when this conflict was logged
                        Field("resolved", "boolean"),               # whether this conflict has been resolved or not
                        migrate=migrate)


# -----------------------------------------------------------------------------
# Sync General Log - keeps log of all syncs
#
resource = "log"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        Field("partner_uuid", length=36),           # uuid of remote system we synced with
                        Field("timestmp", "datetime"),              # the date and time when sync was performed
                        Field("sync_resources", "text"),            # comma-separated list of resources synced
                        Field("sync_errors", "text"),               # sync errors encountered
                        Field("sync_mode"),                         # whether this was an "online" sync (standard sync mode) or "offline" sync (USB/File based)
                        Field("complete_sync", "boolean"),          # whether all resources were synced (complete sync) or only those modified since the last sync (partial sync)
                        Field("sync_method"),                       # whether this was a Pull only, Push only, Remote Push or a Pull-Push sync operation
                        migrate=migrate)

# -----------------------------------------------------------------------------
# Sync Now - stored state
#
resource = "now"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        Field("sync_jobs", "text"),                 # comma-separated list of sync jobs (partner uuids for now, sync job ids from scheduler in future)
                        Field("started_on", "datetime"),            # timestamp when the sync now process began
                        Field("job_resources_done", "text"),        # comma-separated list of resources synced of the currently running job
                        Field("job_resources_pending", "text"),     # comma-separated list of resources to be synced of the currently running job
                        Field("job_sync_errors", "text"),           # sync errors encountered while processing the current job
                        Field("locked", "boolean"),
                        Field("halt", "boolean"),
                        migrate=migrate)

# -----------------------------------------------------------------------------
# Sync Schedule - scheduled sync jobs
#
sync_schedule_period_opts = {
    "h": T("Hourly"),
    "d": T("Daily"),
    "w": T("Weekly"),
    "o": T("Just Once"),
    "m": T("Manual")
}

sync_schedule_job_type_opts = {
    1: T("Sahana Eden <=> Sahana Eden"),
    2: T("Sahana Eden <=> Other (Sahana Agasti, Ushahidi, etc.)")
}

resource = "schedule"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp,
                        Field("comments", length=128),              # brief comments about the scheduled job
                        Field("period",                             # schedule interval period, either hourly, "h", daily, "d", weekly, "w" or one-time, "o"
                              length=10,
                              notnull=True,
                              default="m",
                              requires = IS_IN_SET(sync_schedule_period_opts) ),
                        Field("hours", "integer", default=4),   # specifies the number of hours when hourly period is specified in 'period' field
                        Field("days_of_week", length=40),       # comma-separated list of the day(s) of the week when job runs on weekly basis.
                                                                # A day in a week is represented as a number ranging from 1 to 7 (1 = Sunday, 7 = Saturday)
                        Field("time_of_day", "time"),           # the time (at day_of_week) when job runs on a weekly or daily basis
                        Field("runonce_datetime", "datetime"),  # the date and time when job runs just once
                        Field("job_type", "integer", default=1, # This specifies the type of job: 1 - SahanaEden <=> SahanaEden sync,
                              requires = IS_IN_SET(sync_schedule_job_type_opts) ),
                                                            # 2 - SahanaEden <= Other sync (could be SahanaAgasti, Ushahidi, etc.)
                        Field("job_command", "text", notnull=True), # sync command to execute when this job runs. This command is encoded as a JSON formatted object.
                                                            # It contains the UUID of the sync partner, the list of modules along
                                                            # with resources within them to sync, whether this would be a complete or partial sync
                                                            # (partial sync only retrieves data modified after the last sync, complete sync fetches all),
                                                            # whether this sync would be a two-way (both push and pull) or one-way (push or pull),
                                                            # and sync policy (default policy is taken from the sync partner's record)
                        Field("last_run", "datetime"),      # the date and time of last scheduled run
                        Field("enabled", "boolean",         # whether this schedule is enabled or not. Useful in cases when you want to temporarily
                              default=True),                # disable a schedule
                        migrate=migrate)


# -----------------------------------------------------------------------------
# Notifications - notifications queue
#
resource = "notification"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp,
                        Field("pid", "integer"),
                        Field("notified", "boolean", default=False),
                        Field("error", "boolean", default=False),
                        Field("message", length=192),
                        migrate=migrate)


# -----------------------------------------------------------------------------
def s3_sync_push_message(message, error=False, pid=None):

    """ Push a notification message to the queue """

    table = db.sync_notification

    if message:
        if not pid:
            status = db().select(db.sync_now.id, limitby=(0,1)).first()
            if status:
                pid = status.id
            else:
                pid = 0

        success = table.insert(pid=pid, message=message, error=error)

        if success:
            db.commit()
            return True

    return False


# -----------------------------------------------------------------------------
def s3_sync_get_messages(pid=None):

    """ Get pending notification messages from the queue """

    table = db.sync_notification

    if pid is None:
        status = db().select(db.sync_now.id, limitby=(0,1)).first()
        if status:
            pid = status.id

    if pid is not None:
        query = ((table.pid == pid) | (table.pid == 0)) & \
                (table.notified == False)
    else:
        query = (table.notified == False)

    rows = db(query).select(table.id, table.message, table.error)
    ids = [row.id for row in rows]
    messages = [dict(error=row.error,
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
def s3_sync_eden_eden(peer, mode, tablenames,
                      settings=None,
                      last_sync=None,
                      complete_sync=False,
                      pid=None,
                      silent=False):

    """ Synchronization Eden<->Eden """

    import urllib, urlparse
    import gluon.contrib.simplejson as json

    # Initialize output object
    output = Storage(success = False,
                     errors = [],
                     errcount = 0,
                     pending = list(tablenames),
                     done = [])

    # Notification helpers
    notify = lambda message: not silent and s3_sync_push_message(message, pid=pid) or True
    def error(message, output=output, pid=pid, silent=silent):
        output.errors.append(message)
        if not silent:
            return s3_sync_push_message(message, error=True, pid=pid)
        else:
            return True

    # Get proxy setting and uuid
    uuid = settings.uuid
    proxy = settings.proxy or None

    # Analyse requested format
    format = peer.format

    if format == "json":
        is_json = True
    elif format == "xml":
        is_json = False
    else:
        output.errors.append(s3xrc.ERROR.BAD_FORMAT)
        return output

    # Get msince
    if last_sync is not None and complete_sync == False:
        msince = last_sync.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        msince = None

    for tablename in tablenames:

        # Skip invalid tablenames silently
        if tablename not in db.tables or tablename.find("_") == -1:
            output.pending.remove(tablename)
            output.done.append(tablename)
            continue

        # Reload status
        now = db.sync_now
        status = db(now.id==pid).select(db.sync_now.halt, limitby=(0,1)).first()

        # Check for HALT
        if status and status.halt:
            notify("HALT command received.")
            output.success = True
            return output

        # Create resource
        prefix, name = tablename.split("_", 1)
        resource = s3xrc.resource(prefix, name)

        if is_json:
            _get = resource.fetch_json
            _put = resource.psuh_json
        else:
            _get = resource.fetch_xml
            _put = resource.push_xml

        # Sync path
        sync_path = "sync/sync/%s/%s.%s" % (prefix, name, format)
        remote_url = urlparse.urlparse(peer.url)
        if remote_url.path[-1:] != "/":
            remote_path = "%s/%s" % (remote_url.path, sync_path)
        else:
            remote_path = "%s%s" % (remote_url.path, sync_path)

        if mode in [1, 3]: # pull

            if msince:
                params = "?%s" % urllib.urlencode(dict(msince=msince))
            else:
                params = ""

            fetch_url = "%s://%s%s%s" % (remote_url.scheme,
                                         remote_url.netloc,
                                         remote_path,
                                         params)
            notify(fetch_url)
            err = None
            try:
                result = _get(fetch_url,
                              username=peer.username,
                              password=peer.password,
                              proxy=proxy)
            except Exception, e:
                err = str(e)
            else:
                try:
                    result_json = json.loads(str(result))
                except:
                    error = str(result)
                else:
                    statuscode = str(result_json.get("statuscode", ""))
                    if statuscode.startswith("2"):
                        err = None
                    else:
                        err = str(result_json.get("message", "Unknown error"))
            if err is not None:
                output.errcount += 1
                error("........fetch %s : %s" % (tablename, err))
                if mode == 1:
                    continue
            else:
                notify("........fetch %s : success" % tablename)

        if mode in [2, 3]: # push

            if uuid:
                params = "?%s" % urllib.urlencode(dict(sync_partner_uuid=uuid))
            else:
                params = ""

            push_url = "%s://%s%s%s" % (remote_url.scheme,
                                        remote_url.netloc,
                                        remote_path,
                                        params)
            #notify(push_url)
            err = None
            try:
                result = _put(push_url,
                              username=peer.username,
                              password=peer.password,
                              proxy=proxy,
                              msince=last_sync)
            except Exception, e:
                err = str(e)
            else:
                try:
                    result_json = json.loads(result)
                except:
                    err = str(result)
                else:
                    statuscode = str(result_json.get("statuscode", ""))
                    if statuscode.startswith("2"):
                        err = None
                    else:
                        err = str(result_json.get("message", "Unknown error"))
            if err is not None:
                output.errcount += 1
                error("........send %s : %s" % (tablename, err))
                continue
            else:
                notify("........send %s : success" % tablename)

        output.done.append(tablename)
        output.pending.remove(tablename)

    notify("...Synchronization with %s - done (%s errors)" % (peer.name, output.errcount))

    output.success = True
    return output


# -----------------------------------------------------------------------------
def s3_sync_eden_other(peer, mode, tablenames,
                       settings=None,
                       pid=None,
                       silent=False):

    """ Synchronization Eden<->Other """

    import urllib, urlparse
    import gluon.contrib.simplejson as json

    # Initialize output object
    output = Storage(success = False,
                     errors = [],
                     errcount = 0,
                     pending = list(tablenames),
                     done = [])

    # Notification helpers
    notify = lambda message: not silent and s3_sync_push_message(message, pid=pid) or True
    def error(message, output=output, pid=pid, silent=silent):
        output.errors.append(message)
        if not silent:
            return s3_sync_push_message(message, error=True, pid=pid)
        else:
            return True

    # Get the proxy setting
    proxy = settings.proxy or None

    # Analyse requested format
    format = peer.format
    is_json = False
    pull = False
    push = False

    import_templates = os.path.join(request.folder, s3xrc.XSLT_IMPORT_TEMPLATES)
    export_templates = os.path.join(request.folder, s3xrc.XSLT_EXPORT_TEMPLATES)
    template_name = "%s.%s" % (format, s3xrc.XSLT_FILE_EXTENSION)
    import_template = os.path.join(import_templates, template_name)
    export_template = os.path.join(export_templates, template_name)

    if format == "xml":
        pull = True
        push = True
        import_template = None
        export_template = None
    elif format == "json":
        pull = True
        push = True
        import_template = None
        export_template = None
        is_json = True
    elif format in s3xrc.xml_import_formats and \
         os.path.exists(import_template):
            pull = True
            if format in s3xrc.xml_export_formats and \
               os.path.exists(export_template):
                push = True
    elif format in s3xrc.json_import_formats and \
         os.path.exists(import_template):
            pull = True
            is_json = True
            if format in s3xrc.json_export_formats and \
               os.path.exists(export_template):
                push = True
    else:
        error(s3xrc.ERROR.BAD_FORMAT)
        output.success = False
        return output

    notify("....Synchronization with %s (%s) - started" % (peer.name, peer.url))

    for tablename in tablenames:

        # Skip invalid tablenames silently
        if tablename not in db.tables or tablename.find("_") == -1:
            output.pending.remove(tablename)
            output.done.append(tablename)
            continue

        # Reload status
        now = db.sync_now
        status = db(now.id==pid).select(db.sync_now.halt, limitby=(0,1)).first()

        # Check for HALT
        if status and status.halt:
            notify("HALT command received.")
            output.success = True
            return output

        # Create resource
        prefix, name = tablename.split("_", 1)
        resource = s3xrc.resource(prefix, name)

        if pull and mode in [1, 3]:

            fetch_url = peer.url

            err = None
            try:
                result = resource.fetch(fetch_url,
                                        username=peer.username,
                                        password=peer.password,
                                        json=is_json,
                                        template=import_template,
                                        proxy=proxy)
            except Exception, e:
                err = str(e)
            else:
                try:
                    result_json = json.loads(str(result))
                except:
                    err = str(result)
                else:
                    statuscode = str(result_json.get("statuscode", ""))
                    if statuscode.startswith("2"):
                        err = None
                    else:
                        err = str(result_json.get("message", "Unknown error"))
            if err is not None:
                output.errcount += 1
                error("........fetch %s : %s" % (tablename, err))
                if mode == 1:
                    continue
            else:
                notify("........fetch %s : success" % tablename)

        if push and mode in [2, 3]: # push

            push_url = peer.url

            if is_json:
                _put = resource.push_json
            else:
                _put = resource.push_xml

            err = None
            try:
                result = _put(push_url,
                              username=peer.username,
                              password=peer.password,
                              template=export_template,
                              proxy=proxy)
            except Exception, e:
                err = str(e)
            else:
                try:
                    result_json = json.loads(result)
                except:
                    err = str(result)
                else:
                    statuscode = str(result_json.get("statuscode", ""))
                    if statuscode.startswith("2"):
                        err = None
                    else:
                        err = str(result_json.get("message", "Unknown error"))
            if err is not None:
                output.errcount += 1
                error("........send %s : %s" % (tablename, err))
                continue
            else:
                notify("........send %s : success" % tablename)

        output.done.append(tablename)
        output.pending.remove(tablename)

    notify("...Synchronization with %s - done (%s errors)" % (peer.name, output.errcount))

    output.success = True
    return output


# -----------------------------------------------------------------------------
