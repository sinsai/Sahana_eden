# -*- coding: utf-8 -*-

""" SYNC Synchronisation, Controllers

    @author: Amer Tahir
    @author: nursix
    @version: 0.1.0

"""

prefix = "sync" # common table prefix
module_name = T("Synchronization")

# Options Menu (available in all Functions' Views)
response.menu_options = admin_menu_options # uses the admin menu in 01_menu.py

# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    response.title = module_name
    return dict(module_name=module_name)


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def setting():

    """ Synchronisation Settings - RESTful controller """

    resourcename = "setting"
    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    # Tablename
    table.uuid.label = "UUID"
    table.uuid.comment = DIV(_class="tooltip",
        _title="UUID|" + T("The unique identifier which identifies this instance to other instances."))

    # CRUD strings
    s3.crud_strings.sync_setting = Storage(
        title_update = T("Synchronization Settings"),
        msg_record_modified = T("Synchronization settings updated"))

    s3xrc.model.configure(table, deletable=False, listadd=False)

    return s3_rest_controller("sync", "setting", list_btn=None)


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def peer():

    """ Synchronization Peer - RESTful controller """

    resourcename = "peer"
    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    s3.crud_strings[tablename] = Storage(
        title_create = T("New Synchronization Peer"),
        title_display = T("Peer Details"),
        title_list = T("Synchronization Peers"),
        title_update = T("Edit Peer Details"),
        title_search = T("Search Peer"),
        subtitle_create = T("New Peer"),
        subtitle_list = T("List of Peers"),
        label_list_button = T("List Peers"),
        label_create_button = T("Add Peer"),
        label_delete_button = T("Delete Peer"),
        msg_record_created = T("Peer added"),
        msg_record_modified = T("Peer updated"),
        msg_record_deleted = T("Peer deleted"),
        msg_list_empty = T("No peers currently registered"),
        msg_no_match = T("No records matching the query"))

    db.sync_job.peer_id.readable = False
    db.sync_job.peer_id.writable = False

    primary_resources = s3_sync_primary_resources()
    db.sync_job.resources.requires = IS_NULL_OR(IS_IN_SET(primary_resources,
                                                          multiple=True,
                                                          zero=None))

    db.sync_log.peer_id.readable = False
    db.sync_log.peer_id.writable = False

    table.uuid.label = T("UID")
    table.url.label = T("URL")

    rheader = lambda r: sync_rheader(r, tabs=[
                                    (T("Peer"), None),
                                    (T("Jobs"), "job"),
                                    (T("Log"), "log")])

    return s3_rest_controller(prefix, resourcename, rheader=rheader)


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def job():

    """ Synchronization Job - RESTful controller """

    resourcename = "job"

    # Get primary resources
    primary_resources = s3_sync_primary_resources()
    db.sync_job.resources.requires = IS_NULL_OR(IS_IN_SET(primary_resources,
                                                          multiple=True,
                                                          zero=None))

    return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
@auth.requires_login()
def registration():

    """ Peer registration requests - RESTful controller """

    resourcename = "registration"

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    s3xrc.model.configure(table,
                          listadd=False,
                          editable=False,
                          deletable=True)

    return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
@auth.requires_login()
def log():

    """ Synchronization log - RESTful controller """

    resourcename = "log"

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    s3.crud_strings[tablename] = Storage(
        title_display = T("Synchronization Details"),
        title_list = T("Synchronization History"),
        subtitle_list = T("Finished Jobs"),
        label_list_button = T("List All Entries"),
        label_delete_button = T("Delete Entry"),
        msg_record_deleted = T("Entry deleted"),
        msg_list_empty = T("No entries found"),
        msg_no_match = T("No entries matching the query"))

    s3xrc.model.configure(table,
                          insertable = False,
                          editable = False,
                          deletable = True)

    return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
@auth.requires_login()
def now():

    """ Manual synchronization """

    pid = None

    # Notification helpers
    error = lambda message, type="ERROR": \
            s3_sync_push_message(message, pid=pid, type=type)
    notify = lambda message, type="": \
             s3_sync_push_message(message, pid=pid, type=type)

    # Get settings
    settings = db().select(db.sync_setting.ALL, limitby=(0, 1)).first()
    if not settings:
        response.flash = T("Synchronization not configured.")
        return dict(module_name=module_name, action=None, status=None)

    status = db().select(db.sync_status.ALL, limitby=(0, 1)).first()
    if status:
        pid = status.id

    action = request.get_vars.get("action", None)

    if action == "start":

        """ Start synchronization """

        response.view = "xml.html"

        if not status:
            table_job = db.sync_job
            jobs = db((table_job.run_interval == "m") &
                      (table_job.enabled == True)).select(table_job.ALL)
            if not jobs:
                job_list = None
                error("There are no scheduled jobs. Please schedule a sync operation (set to run manually).")
                return dict(item="SYNC NOW: no jobs on schedule.")
            else:
                job_list = ",".join(map(str, [j.id for j in jobs]))
                job = jobs.first()
                res_list = ",".join(map(str, job.resources))

            sync_pid = db.sync_status.insert(jobs = job_list,
                                             start_time = request.utcnow,
                                             done = "",
                                             pending = res_list,
                                             errors = "")
            if not sync_pid:
                error("Could not store synchronization session data.")
                return dict(item="SYNC NOW: cannot store sync session.")
            else:
                db.commit()

            status = db(db.sync_status.id == sync_pid).select(db.sync_status.ALL, limitby=(0, 1)).first()
            s3_sync_init_messages()
            notify("Starting new synchronization process (started on %s)" % \
                    status.start_time.strftime("%x %H:%M:%S"))
        else:
            if status.locked:
                error("Manual synchronization already activated.")
                return dict(item="SYNC NOW: already active")
            else:
                notify("Resuming prior synchronization process (originally started on %s)" % \
                       status.start_time.strftime("%x %H:%M:%S"))

        pid = status.id
        db(db.sync_status.id==pid).update(locked=True)
        db.commit()

        session._unlock(response)
        session.s3.roles.append(1)

        jobs = status.jobs.split(",")
        total_errors = 0
        while jobs:

            result = None

            job_id = jobs.pop(0)
            job = db(db.sync_job.id == job_id).select(db.sync_job.ALL, limitby=(0, 1)).first()

            if job:
                pending = status.pending.split(",")
                result = sync_run_job(job,
                                      settings=settings,
                                      pid=pid,
                                      tables=pending,
                                      silent=False)

            if result:
                errors = ",".join(result.errors)
                done = ",".join(result.done)
                pending = ",".join(result.pending)
                total_errors += result.errcount
                notify("Job %s done." % job_id, type="DONE")
            else:
                errors = ""
                done = ""
                pending = ""

            if not pending:
                if jobs:
                    job_id = jobs[0]
                    job = db(db.sync_job.id == job_id).select(db.sync_job.ALL, limitby=(0, 1)).first()
                    res_list = ",".join(map(str, job.resources))
                else:
                    res_list = ""
            else:
                # Restore job
                jobs.insert(0, job_id)
                res_list = pending

            db(db.sync_status.id==status.id).update(
                    jobs = ",".join(jobs),
                    done = "%s,%s" % (status.done, done),
                    errors = "%s,%s" % (status.errors, errors),
                    pending = res_list)
            status = db(db.sync_status.id == pid).select(db.sync_status.ALL, limitby=(0, 1)).first()
            if status and status.halt:
                break

        if not status.halt and not status.jobs:
            # @todo: log in history
            db(db.sync_status.id==pid).delete()
            notify("Synchronization complete (%s errors)." % total_errors, type="DONE")
            return dict(item="SYNC NOW: done")
        else:
            db(db.sync_status.id==pid).update(locked=False, halt=False)
            notify("Synchronization halted.", type="DONE")
            return dict(item="SYNC NOW: halted")

    elif action == "halt":

        """ Send HALT command to suspend a running sync/now """

        response.view = "xml.html"

        table = db.sync_status
        if status:
            pid = status.id
            db(table.id == pid).update(halt=True)
        else:
            return dict(item="HALT: No synchronization process found.")

        return dict(item="HALT: Halting current synchronization - please wait...")

    elif action == "stop":

        """ Remove a suspended sync/now """

        response.view = "xml.html"

        force = request.vars.get("force", False) and True

        table = db.sync_status
        if status:
            if (status.locked or status.halt) and not force:
                item = "Synchronization still active - need to halt process first."
            else:
                db(table.id == status.id).delete()
                item = "Synchronization process removed."
        else:
            item = "No synchronization process found."

        return dict(item="STOP: %s" % item)

    elif action == "unlock":

        """ Safely remove the lock from a broken Sync/now """

        response.view = "xml.html"

        table = db.sync_status
        if status:
            pid = status.id
            db(table.id == pid).update(locked=False, halt=True)

        return dict(item="UNLOCK: done")

    elif action == "status":

        """ Retrieve pending messages from the notification queue """

        response.view = "xml.html"

        s3_sync_clear_messages()

        messages = s3_sync_get_messages()
        if not messages:
            if status.locked:
                return dict(item="")

        msg_list = []
        for i in xrange(len(messages)):
            msg = Storage(messages[i])
            if msg.type:
                _class = "sync_%s" % msg.type.lower()
                msg_list.append(DIV(SPAN(msg.message, _class="sync_message"),
                                    SPAN(msg.type, _class="sync_status"),
                                    _class=_class))
            else:
                msg_list.append(DIV(SPAN(msg.message, _class="sync_message"),
                                    _class="sync_ok"))

        if msg_list:
            item = DIV(msg_list).xml()
        else:
            item = "DONE"
        return dict(item=item)

    # Extra stylesheet
    response.extra_styles = ["S3/sync.css"]
    return dict(module_name=module_name, action=action, status=status)


# -----------------------------------------------------------------------------
def sync_cron():

    """ Automatic synchronization:

        Run all due jobs from the schedule, designed to be called
        by cron on a regular basis.

    """

    import sys
    #print >> sys.stderr, "Synchronization CRON process"

    # Get settings
    settings = db().select(db.sync_setting.ALL, limitby=(0,1)).first()
    if not settings:
        return

    # Get all enabled jobs
    jobs = db((db.sync_job.enabled == True) &
              (db.sync_job.run_interval != "m")).select(db.sync_job.ALL)
    #jobs = db((db.sync_job.enabled == True)).select(db.sync_job.ALL)

    now = datetime.datetime.now()

    jobs_done = 0
    error_count = 0
    for job in jobs:
        due = False
        interval = job.run_interval
        last_run = job.last_run
        if not last_run:
            due = True
        elif interval == "h": # hourly
            if now >= (last_run + datetime.timedelta(hours=job.hours)):
                due = True
        elif interval == "d": # daily
            if last_run.date() < now.date():
                if not job.hour or now.hour() >= job.hour:
                    due = True
        elif interval == "w": # weekly
            pass
        elif interval == "o": # once
            pass
        else:
            continue

        if due:
            result = sync_run_job(job,
                                  settings=settings,
                                  pid=None,
                                  tables=job.resources,
                                  silent=True)
            if result.success:
                db(db.sync_job.id == job.id).update(last_run=now)
                jobs_done += 1
            else:
                error_count +=1


    response.view = "xml.html"
    item = s3xrc.xml.json_message(True, 200, message="%s jobs done, %s errors." % (jobs_done, error_count))

    return dict(item=item)


# -----------------------------------------------------------------------------
#@auth.requires_login()
def sync():

    """ Sync interface

        allows PUT/GET of any resource (universal RESTful controller)

    """

    if len(request.args) < 2:
        # No resource specified
        raise HTTP(501, body=s3xrc.ERROR.BAD_RESOURCE)
    else:
        prefix = request.args.pop(0)
        name = request.args.pop(0)

        if prefix in s3xrc.PROTECTED:
            raise HTTP(501, body="%s: %s" %
                      (s3xrc.ERROR.NOT_PERMITTED, T("Protected resource")))

        if name.find(".") != -1:
            name, extension = name.rsplit(".", 1)
            request.extension = extension

    # Get the sync partner
    peer_uuid = request.vars.get("sync_partner_uuid", None)
    if peer_uuid:
        peers = db.sync_partner
        peer = db(peers.peer_uid == peer_uuid).select(limitby=(0,1)).first()

    # remote push?
    peer = None
    method = request.env.request_method
    if method in ("PUT", "POST"):
        remote_push = True
        # Must be registered partner for push:
        if not peer:
            raise HTTP(501, body="%s: %s" %
                      (s3xrc.ERROR.NOT_PERMITTED, T("Unknown Peer")))
        else:
            if not peer.allow_push:
                raise HTTP(501, body="%s: %s" %
                        (s3xrc.ERROR.NOT_PERMITTED, T("Peer not allowed to push")))
            # Set the sync resolver with no policy (defaults to peer policy)
            s3xrc.resolve = lambda import_job, peer=peer: \
                                   sync_resolve(import_job, peer, None)
    elif method == "GET":
        remote_push = False
    else:
        raise HTTP(501, body=s3xrc.ERROR.BAD_METHOD)

    def prep(r):
        # Do not allow interactive formats
        if r.representation in ("html", "popup", "iframe", "aadata"):
            return False
        # Do not allow URL methods
        if r.method:
            return False
        return True
    response.s3.prep = prep

    def postp(r, output, peer=peer):

        if r.http in ("PUT", "POST") and peer:
            try:
                output_json = Storage(json.loads(output))
            except:
                # No JSON response?
                pass
            else:
                resource = r.resource
                sr = [c.component.tablename for c in resource.components.values()]
                sr.insert(0, resource.tablename)
                sync_resources = ", ".join(sr)

                if str(output_json["statuscode"]) != "200":
                    sync_errors = str(output)
                else:
                    sync_errors = ""

                db.sync_log.insert(
                    peer_id = peer.id,
                    timestmp = datetime.datetime.now(),
                    resources = sync_resources,
                    errors = sync_errors,
                    mode = 1,
                    run_interval = "o",
                    complete = False
                )

        return output
    response.s3.postp = postp

    # Execute the request
    output = s3_rest_controller(prefix, name)

    return output


# -----------------------------------------------------------------------------
def sync_run_job(job, settings=None, pid=None, tables=[], silent=False):

    """ Run synchronization job """

    # Notification helpers
    error = lambda message, pid=pid, silent=silent: not silent and \
                   s3_sync_push_message(message, pid=pid, error=True)
    notify = lambda message, pid=pid, silent=silent: not silent and \
                    s3_sync_push_message(message, pid=pid)

    # Last synchronization time for this job
    last_sync_on = job.last_run

    peer_id = job.peer_id
    peer = db(db.sync_peer.id == peer_id).select(limitby=(0, 1)).first()
    peer_uuid = peer.uuid

    mode = job.mode
    complete = job.complete
    ignore_errors = job.ignore_errors or peer.ignore_errors

    result = None

    # Get the peer
    if peer:
        notify("Processing job %s..." % job.id)

        job_policy = job.policy or peer.policy
        s3xrc.resolve = lambda import_job, peer=peer, policy=policy: \
                               sync_resolve(import_job, peer, policy)

        # Find resources to sync
        tablenames = [n.strip().lower() for n in tables]

        # Synchronize all tables
        if job.type == 1:
            result = s3_sync_eden_eden(peer, mode, tablenames,
                                       settings=settings,
                                       pid=pid,
                                       last_sync=last_sync_on,
                                       complete_sync=complete,
                                       ignore_errors=ignore_errors)
        else:
            result = s3_sync_eden_other(peer, mode, tablenames,
                                        pid=pid,
                                        settings=settings,
                                        ignore_errors=ignore_errors)

        if result:
            db.sync_log.insert(peer_id = peer.id,
                               timestmp = datetime.datetime.now(),
                               resources = ", ".join(result.done),
                               errors = ", ".join(result.errors),
                               mode = job.mode,
                               run_interval = job.run_interval,
                               complete = job.complete)

    return result


# -----------------------------------------------------------------------------
def s3_sync_eden_eden(peer, mode, tablenames,
                      settings=None,
                      last_sync=None,
                      complete_sync=False,
                      pid=None,
                      silent=False,
                      ignore_errors=False):

    """ Synchronization Eden<->Eden """

    import urllib, urlparse
    # Initialize output object
    output = Storage(success = False,
                     errors = [],
                     errcount = 0,
                     pending = list(tablenames),
                     done = [])

    # Notification helpers
    notify = lambda message, type=None: not silent and \
             s3_sync_push_message(message, pid=pid, type=type or "")

    def error(message, output=output, pid=pid, silent=silent, type="ERROR"):
        output.errors.append(message)
        if not silent:
            notify(message, type=type)

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

    notify("....Synchronization with %s (%s) - started %s" % (
            peer.name,
            peer.url,
            ignore_errors and "(ignoring invalid records)" or ""))

    for tablename in tablenames:

        # Skip invalid tablenames silently
        if tablename not in db.tables or tablename.find("_") == -1:
            output.done.append(tablename)
            continue

        # Reload status
        now = db.sync_status
        status = db(now.id==pid).select(db.sync_status.halt, limitby=(0,1)).first()

        # Check for HALT
        if status and status.halt:
            notify("HALT command received.")
            output.success = True
            return output

        output.pending.remove(tablename)

        # Create resource
        prefix, name = tablename.split("_", 1)
        resource = s3xrc.define_resource(prefix, name)

        if is_json:
            _get = resource.fetch_json
            _put = resource.push_json
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
                              proxy=proxy,
                              ignore_errors=ignore_errors)
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
                output.errors.append("%s: %s" % (tablename, err))
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
                output.errors.append("%s: %s" % (tablename, err))
                error("........send %s : %s" % (tablename, err))
                continue
            else:
                notify("........send %s : success" % tablename)

        output.done.append(tablename)

    notify("...Synchronization with %s - done (%s errors)" % (peer.name, output.errcount))

    output.success = True
    return output


# -----------------------------------------------------------------------------
def s3_sync_eden_other(peer, mode, tablenames,
                       settings=None,
                       pid=None,
                       silent=False,
                       ignore_errors=False):

    """ Synchronization Eden<->Other """

    import urllib, urlparse

    # Initialize output object
    output = Storage(success = False,
                     errors = [],
                     errcount = 0,
                     pending = list(tablenames),
                     done = [])

    # Notification helpers
    notify = lambda message, type=None: not silent and \
             s3_sync_push_message(message, pid=pid, type=type or "")

    def error(message, output=output, pid=pid, silent=silent, type="ERROR"):
        output.errors.append(message)
        if not silent:
            notify(message, type=type)

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

    notify("....Synchronization with %s (%s) - started %s" % (
            peer.name,
            peer.url,
            ignore_errors and "(ignoring invalid records)" or ""))

    for tablename in tablenames:

        # Skip invalid tablenames silently
        if tablename not in db.tables or tablename.find("_") == -1:
            output.pending.remove(tablename)
            output.done.append(tablename)
            continue

        # Reload status
        now = db.sync_status
        status = db(now.id==pid).select(db.sync_status.halt, limitby=(0,1)).first()

        # Check for HALT
        if status and status.halt:
            notify("HALT command received.")
            output.success = True
            return output

        output.pending.remove(tablename)

        # Create resource
        prefix, name = tablename.split("_", 1)
        resource = s3xrc.define_resource(prefix, name)

        if pull and mode in [1, 3]:

            fetch_url = peer.url

            err = None
            try:
                result = resource.fetch(fetch_url,
                                        username=peer.username,
                                        password=peer.password,
                                        json=is_json,
                                        template=import_template,
                                        proxy=proxy,
                                        ignore_errors=ignore_errors)
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
                output.errors.append("%s: %s" % (tablename, err))
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
                output.errors.append("%s: %s" % (tablename, err))
                error("........send %s : %s" % (tablename, err))
                continue
            else:
                notify("........send %s : success" % tablename)

        output.done.append(tablename)

    notify("...Synchronization with %s - done (%s errors)" % (peer.name, output.errcount))

    output.success = True
    return output


# -----------------------------------------------------------------------------
def sync_rheader(r, tabs=[]):

    """ Resource headers """

    if r.representation == "html":

        if r.name == "peer":

            peer = r.record
            if peer:
                _next = r.here()
                _same = r.same()

                if tabs:
                    rheader_tabs = shn_rheader_tabs(r, tabs)
                else:
                    rheader_tabs = ""

                rheader = DIV(TABLE(

                    TR(TH("%s: " % T("Name")),
                       peer.name,
                       TH(""),
                       ""),

                    TR(TH("%s: " % T("Type")),
                       sync_peer_types.get(peer.type, UNKNOWN_OPT),
                       TH(""),
                       ""),

                    TR(TH("%s: " % T("URL")),
                       peer.url,
                       TH(""),
                       "")),

                    rheader_tabs)

                return rheader

    return None


# -----------------------------------------------------------------------------
def sync_resolve(import_job, peer, policy):

    """ Sync resolver """

    import cPickle

    # Assume both records have been modified
    lmodified = True
    rmodified = True

    table = import_job.table

    # Get last synchronization time
    last_sync_time = peer.last_sync_time

    # Get the local record and its modification time
    lmtime = None
    if import_job.method == import_job.METHOD.UPDATE:
        fields = import_job.record.keys()
        if not "modified_on" in fields:
            fields.append("modified_on")
        row = db(table.id==import_job.id).select(limitby=(0,1), *fields).first()
        if row:
            lmtime = row.modified_on
    else:
        row = None

    # Get remote record modification time
    rmtime = import_job.mtime

    # Conflict detection
    conflict = False
    if last_sync_time:
        if rmtime and rmtime <= last_sync_time:
            rmodified = False
        if lmtime and lmtime <= last_sync_time:
            lmodified = False
    if lmodified and rmodified:
        # Is the remote record really different?
        for f in fields:
            if f != "modified_on" and import_job.record[f] != row[f]:
                conflict = True
                break;

    # Get synchronization policy
    if policy is None:
        policy = peer.policy

    # Sync policies:
    #
    #  Option    local records                 peer records     Title
    #
    #  0         do nothing                    do nothing       No Sync
    #  1         --                            --               Manual
    #  2         do nothing                    import           Import
    #  3         update to peer version        import           Replace
    #  4         update to peer version        do nothing       Update
    #  5         update to/keep newer version  import           Replace Newer
    #  6         update to/keep newer version  do nothing       Update Newer
    #  7         do nothing                    import master    Import Master
    #  8         update to master              import master    Replace Master
    #  9         update to master              do nothing       Update Master
    # 10         --                            --               Role-Based (not implemented)

    if not conflict:

        # Apply default policy
        if policy == 0: # No Sync
            import_job.resolution = import_job.RESOLUTION.THIS
            import_job.strategy = []
        elif policy == 1: # Manual
            conflict = True
        elif policy == 2: # Import
            import_job.resolution = import_job.RESOLUTION.OTHER
            import_job.strategy = [import_job.METHOD.CREATE]
        elif policy == 3: # Replace
            import_job.resolution = import_job.RESOLUTION.OTHER
            import_job.strategy = [import_job.METHOD.CREATE, import_job.METHOD.UPDATE]
        elif policy == 4: # Update
            import_job.resolution = import_job.RESOLUTION.OTHER
            import_job.strategy = [import_job.METHOD.UPDATE]
        elif policy == 5: # Replace Newer
            import_job.resolution = import_job.RESOLUTION.NEWER
            import_job.strategy = [import_job.METHOD.CREATE, import_job.METHOD.UPDATE]
        elif policy == 6: # Update Newer
            import_job.resolution = import_job.RESOLUTION.NEWER
            import_job.strategy = [import_job.METHOD.UPDATE]
        elif policy == 7: # Import Master
            import_job.resolution = import_job.RESOLUTION.MASTER
            import_job.strategy = [import_job.METHOD.CREATE]
        elif policy == 8: # Replace Master
            import_job.resolution = import_job.RESOLUTION.MASTER
            import_job.strategy = [import_job.METHOD.CREATE, import_job.METHOD.UPDATE]
        elif policy == 9: # Update Master
            import_job.resolution = import_job.RESOLUTION.THIS
            import_job.strategy = [import_job.METHOD.UPDATE]
        elif policy == 10: # Role Based (not implemented)
            conflict = True
        else:
            pass # use defaults

    if conflict:

        # Do not synchronize
        import_job.resolution = import_job.RESOLUTION.THIS
        import_job.strategy = []

        # Log conflict for manual resolution
        now = datetime.datetime.utcnow()
        modifier = import_job.element.get("modified_by", None)
        record_dump = cPickle.dumps(dict(import_job.record), 0)

        table_conflict.insert(peer_id=peer.id,
                              tablename=import_job.tablename,
                              uuid=import_job.uid,
                              remote_record = record_dump,
                              remote_modified_by = modifier,
                              remote_modified_on = rmtime)

    return


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def conflict():

    """ Conflict Resolution UI """

    resourcename = "conflict"

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    response.s3.filter = (table.resolved == False)

    return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
