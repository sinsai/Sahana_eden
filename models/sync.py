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

opt_sync_policy = db.Table(None, "sync_policy",
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
                        #Field("uuid", length=36, notnull=True),     # Our UUID for sync purposes
                        Field("beacon_service_url", default = "http://sync.eden.sahanafoundation.org/sync/beacon"), # URL of beacon service that our sahana instance is configured to work with
                        Field("sync_pools"),                        # Comma-separated list of sync pools we've subscribed to
                        Field("proxy"),
                        Field("comments", length=128, default = "This is a SahanaEden instance, see http://eden.sahanafoundation.org" ),
                        migrate=migrate)


# -----------------------------------------------------------------------------
# Sync partners
#
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
                        uuidstamp,
                        #Field("uuid", length=36, notnull=True),     # uuid of this partner
                        Field("name", default="Sahana Eden Instance"), # name of the partner (descriptive title)
                        Field("instance_url", default = "http://sync.eden.sahanafoundation.org/eden", notnull=True), # URL of their instance
                        Field("instance_type",                      # the type of instance => "SahanaEden", "SahanaAgasti", "Ushahidi", etc.
                              default="Sahana Eden",
                              requires = IS_IN_SET(sync_partner_instance_type_opts) ),
                        Field("username"),                          # username required to sync with this partner
                        Field("password", "password"),              # password required to sync with this partner
                        Field("format"),
                        Field("sync_pools"),                        # Comma-separated list of sync pools they're subscribed to
                        opt_sync_policy,                            # sync_policy for this partner
                        Field("last_sync_on", "datetime"),          # the last time we sync-ed with this partner
                        Field("comments", length=128),
                        migrate=migrate)


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
                        migrate=migrate)

# -----------------------------------------------------------------------------
# Sync Schedule - scheduled sync jobs
#
sync_schedule_period_opts = {
    "h":T("Hourly"),
    "d":T("Daily"),
    "w":T("Weekly"),
    "o":T("Just Once"),
    "m":T("Manual")
}

sync_schedule_job_type_opts = {
    1:T("Sahana Eden <=> Sahana Eden sync"),
    2:T("Sahana Eden <=> Other sync (Sahana Agasti, Ushahidi, etc.)")
}

resource = "schedule"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp,
                        Field("comments", length=128),              # brief comments about the scheduled job
                        Field("period",                             # schedule interval period, either hourly, "h", daily, "d", weekly, "w" or one-time, "o"
                              length=10,
                              notnull=True,
                              default="h",
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

            # Not a component
            tablenames.append(t)

    return tablenames


# -----------------------------------------------------------------------------
def s3_sync_eden_eden(peer, mode, tablenames,
                      settings=None,
                      last_sync=None,
                      complete_sync=False):

    """ Synchronization Eden<->Eden """

    import urllib, urlparse
    import gluon.contrib.simplejson as json

    print "s3_sync_eden_eden"

    status = Storage(
        success = False,
        errors = [],
        messages = [],
        pending = tablenames,
        done = []
    )

    uuid = settings.uuid
    proxy = settings.proxy or None

    format = peer.format

    if last_sync is not None and complete_sync == False:
        msince = last_sync.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        msince = None

    errcount = 0
    print tablenames
    for tablename in tablenames:
        print tablename
        if tablename not in db.tables or tablename.find("_") == -1:
            status.pending.remove(tablename)
            status.done.append(tablename)
            print "table not found"
            continue

        if session.s3.sync_stop:
            print "Got sync_stop"
            return status

        prefix, name = tablename.split("_", 1)
        resource = s3xrc.resource(prefix, name)

        print "resource created"

        if format == "json":
            _get = resource.fetch_json
            _put = resource.push_json
        elif format == "xml":
            _get = resource.fetch_xml
            _put = resource.push_xml
        else:
            print "Error: bad format"
            status.success = False
            status.errors.append(s3xrc.ERROR.BAD_FORMAT)
            return status

        sync_path = "sync/sync/%s/%s.%s" % (prefix, name, format)
        print "sync_path %s" % sync_path

        remote_url = urlparse.urlparse(peer.instance_url)
        print remote_url
        if remote_url.path[-1:] != "/":
            remote_path = "%s/%s" % (remote_url.path, sync_path)
        else:
            remote_path = "%s%s" % (remote_url.path, sync_path)

        print "remote_path=%s" % remote_path

        if mode in [1, 3]: # pull

            if msince:
                params = "?%s" % urllib.urlencode(dict(msince=msince))
            else:
                params = ""

            fetch_url = "%s://%s%s%s" % (remote_url.scheme,
                                         remote_url.netloc,
                                         remote_path,
                                         params)
            error = None
            try:
                print "Fetching %s" % fetch_url
                result = _get(fetch_url,
                              username=peer.username,
                              password=peer.password,
                              proxy=proxy)
                print "fetched=%s" % result
            except Exception, e:
                print "Error %s" % e
                result = str(e)
            else:
                try:
                    result_json = json.loads(result)
                except:
                    error = str(result)
                else:
                    print result_json
                    statuscode = str(result_json.get("statuscode", ""))
                    message = str(result_json.get("message", "Unknown error"))
                    if statuscode.startswith("2"):
                        error = None
                    else:
                        error = message
            if error:
                errcount += 1
                msg = "...fetch %s - FAILURE: %s" (tablename, error)
                status.messages.append(msg)
                status.errors.append(error)
                continue
            else:
                msg = "...fetch %s - SUCCESS" % tablename
                status.messages.append(msg)

            print msg

        if mode in [2, 3]: # push

            if uuid:
                params = "?%s" % urllib.urlencode(dict(sync_partner_uuid=uuid))
            else:
                params = ""

            push_url = "%s://%s%s%s" % (remote_url.scheme,
                                        remote_url.netloc,
                                        remote_path,
                                        params)
            error = None
            try:
                result = _put(push_url,
                              username=peer.username,
                              password=peer.password,
                              proxy=proxy,
                              msince=last_sync)
            except Exception, e:
                print "Error %s" % e
                result = str(e)
            else:
                try:
                    result_json = json.loads(result)
                except:
                    error = str(result)
                else:
                    statuscode = str(result_json.get("statuscode", ""))
                    message = str(result_json.get("message", "Unknown error"))
                    if statuscode.startswith("2"):
                        error = None
                    else:
                        error = message
            if error:
                errcount += 1
                msg = "...send %s - FAILURE: %s" (tablename, error)
                status.messages.append(msg)
                status.errors.append(error)
                continue
            else:
                msg = "...send %s - SUCCESS." % tablename
                status.messages.append(msg)

        status.done.append(tablename)
        status.pending.remove(tablename)

    msg = "...synchronize %s - DONE (%s errors)." % (peer.instance_url, errcount)
    status.messages.append(msg)
    status.success = True
    return status


# -----------------------------------------------------------------------------
def s3_sync_eden_other(peer, mode, tablenames, settings=None):

    """ Synchronization Eden<->Other """

    import urllib, urlparse
    import gluon.contrib.simplejson as json

    status = Storage(
        success = False,
        errors = [],
        messages = [],
        pending = list(tablenames),
        done = []
    )

    proxy = settings.proxy or None

    format = peer.format

    is_json = False
    pull = False
    push = False

    import_templates = os.path.join(request.folder, s3xrc.XSLT_IMPORT_TEMPLATES)
    export_templates = os.path.join(request.folder, s3xrc.XSLT_EXPORT_TEMPLATES)
    template_name = "%s.%s" % (format, s3xrc.XSLT_FILE_EXTENSION)
    import_template_path = os.path.join(import_templates, template_name)
    export_template_path = os.path.join(export_templates, template_name)

    if format == "xml":
        pull = True
        push = True
    elif format == "json":
        pull = True
        push = True
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
        status.success = False
        status.errors.append(s3xrc.ERROR.BAD_FORMAT)
        return status

    errcount = 0
    msg = dict(success=True,
               message="....Synchronization with %s - START" % peer.name)
    status.messages.append(msg)
    print "tablenames=%s" % tablenames
    for tablename in tablenames:
        print tablename
        if tablename not in db.tables or tablename.find("_") == -1:
            status.pending.remove(tablename)
            status.done.append(tablename)
            continue

        if session.s3.sync_stop:
            return status

        prefix, name = tablename.split("_", 1)
        resource = s3xrc.resource(prefix, name)

        if pull and mode in [1, 3]: # pull

            fetch_url = peer.instance_url

            error = None
            try:
                result = resource.fetch(fetch_url,
                                        username=peer.username,
                                        password=peer.password,
                                        json=is_json,
                                        proxy=proxy)
            except Exception, e:
                error = str(e)
            else:
                try:
                    result_json = json.loads(str(result))
                except Exception, e:
                    error = str(result)
                else:
                    statuscode = str(result_json.get("statuscode", ""))
                    message = str(result_json.get("message", "Unknown error"))
                    if statuscode.startswith("2"):
                        error = None
                    else:
                        error = message
            if error:
                errcount += 1
                msg = dict(success=False,
                           message="........fetch %s - FAILURE: %s" % (tablename, error))
                status.messages.append(msg)
                status.errors.append(error)
                continue
            else:
                msg = dict(success=True,
                           message="........fetch %s - SUCCESS" % tablename)
                status.messages.append(msg)

        if push and mode in [2, 3]: # push

            push_url = peer.instance_url

            if is_json:
                _put = resource.push_json
            else:
                _put = resource.push_xml

            error = None
            try:
                result = _put(push_url,
                              username=peer.username,
                              password=peer.password,
                              proxy=proxy)
            except Exception, e:
                result = str(e)
            else:
                try:
                    result_json = json.loads(result)
                except:
                    error = str(result)
                else:
                    statuscode = str(result_json.get("statuscode", ""))
                    message = str(result_json.get("message", "Unknown error"))
                    if statuscode.startswith("2"):
                        error = None
                    else:
                        error = message
            if error:
                errcount += 1
                msg = dict(success=False,
                           message="........send %s - FAILURE: %s" % (tablename, error))
                status.messages.append(msg)
                status.errors.append(error)
                continue
            else:
                msg = dict(success=True,
                           message="........send %s - SUCCESS" % tablename)
                status.messages.append(msg)

        status.done.append(tablename)
        status.pending.remove(tablename)
        print tablenames

    msg = dict(success=errcount and False or True,
               message="...Synchronization with %s - DONE (%s errors)." % (peer.name, errcount))
    status.messages.append(msg)
    status.success = True

    return status

# -----------------------------------------------------------------------------
