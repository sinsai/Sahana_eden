# -*- coding: utf-8 -*-

""" Synchronisation - Controllers

    @author: Amer Tahir

"""

module = "sync"
module_name = T("Synchronization")

# Options Menu (available in all Functions' Views)
response.menu_options = admin_menu_options

# -----------------------------------------------------------------------------
# S3 framework functions
#
def index():

    """ Module's Home Page """

    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
@auth.requires_login()
def now():

    """ Manual synchronization """

    import gluon.contrib.simplejson as json

    pid = None

    error = lambda message: s3_sync_push_message(message,
                                                 pid=pid, error=True)
    notify = lambda message: s3_sync_push_message(message, pid=pid)

    # Get synchronization settings from the DB
    settings = db().select(db.sync_setting.uuid,
                           db.sync_setting.proxy,
                           limitby=(0, 1)).first()
    if not settings:
        session.error = T("Synchronization not configured")
        return dict(module_name=module_name,
                    sync_status="Configuration Error - no settings found.",
                    sync_start=False,
                    sync_state=None)

    # Load status
    status = db().select(db.sync_now.ALL, limitby=(0, 1)).first()

    # Read the action from URL vars
    action = request.get_vars.get("sync", None)

    if action == "start": # Start synchronization

        # Set view
        response.view = "xml.html"

        if not status:
            # Get all scheduled jobs
            table_job = db.sync_schedule
            jobs = db((table_job.period == "m") &
                      (table_job.enabled == True)).select(table_job.ALL)
            if not jobs:
                job_list = None
                error("There are no scheduled jobs. Please schedule a sync operation (set to run manually).")
                return dict(item="SYNC NOW: no jobs on schedule.")
            else:
                job_list = ",".join(map(str, [j.id for j in jobs]))
                job = jobs.first()
                try:
                    job_cmd = json.loads(job.job_command)
                except:
                    res_list = ""
                else:
                    res_list = ",".join(map(str, job_cmd.get("resources", [])))

            # Save state
            sync_pid = db.sync_now.insert(sync_jobs = job_list,
                                          started_on = request.utcnow,
                                          job_resources_done = "",
                                          job_resources_pending = res_list,
                                          job_sync_errors = "")

            if not sync_pid:
                error("Could not store synchronization session data.")
                return dict(item="SYNC NOW: cannot store sync session.")
            else:
                db.commit()

            # Reload status
            status = db(db.sync_now.id == sync_pid).select(db.sync_now.ALL, limitby=(0, 1)).first()

            # Notification
            notify("Starting new synchronization process (started on %s)" % \
                    status.started_on.strftime("%x %H:%M:%S"))

        else:

            # Notification
            notify("Resuming prior synchronization process (originally started on %s)" % \
                    status.started_on.strftime("%x %H:%M:%S"))

        # Lock
        if status and status.locked:
            error("Manual synchronization already activated.")
            return dict(item="SYNC NOW: already active")
        else:
            pid = status.id
            db(db.sync_now.id==pid).update(locked=True)
            s3_sync_init_messages()
            db.commit()

        session._unlock(response)

        #for i in xrange(5):
            #time.sleep(3)
            #notify("Test message")

        # Become admin
        session.s3.roles.append(1)

        # Get job list
        jobs = status.sync_jobs.split(",")

        # Process jobs
        total_errors = 0
        while jobs:

            # Initialize result
            result = None

            # Load first job
            job_id = jobs.pop(0)
            job = db(db.sync_schedule.id == job_id).select(db.sync_schedule.ALL, limitby=(0, 1)).first()

            # Process job
            if job:

                # Last synchronization for this job
                last_sync_on = job.last_run

                # Parse job command
                try:
                    job_cmd = json.loads(job.job_command)
                except:
                    job_cmd = None

                # Load peer_uuid, complete and mode from job command
                if job_cmd and isinstance(job_cmd, dict):
                    peer_uuid = job_cmd.get("partner_uuid", None)
                    complete = job_cmd.get("complete", False) == "True" and True or False
                    try:
                        mode = int(job_cmd.get("mode", 1))
                    except ValueError:
                        mode = 1
                else:
                    peer_uuid = None
                    complete = None
                    mode = None

                # Get the peer
                peer = db(db.sync_partner.uuid == peer_uuid).select(limitby=(0, 1)).first()
                if peer:

                    notify("Processing job %s..." % job_id)

                    # Get policy and set resolver (defaults to peer policy)
                    job_policy = job_cmd.get("policy", peer.policy)
                    if job_policy:
                        try:
                            policy = int(job_policy)
                        except ValueError:
                            policy = None
                    s3xrc.sync_resolve = lambda vector, peer=peer, policy=policy: \
                                                sync_res(vector, peer, policy)


                    # Find resources to sync
                    tn = status.job_resources_pending.split(",")
                    tablenames = [n.strip().lower() for n in tn]

                    # Synchronize all tables
                    if job.job_type == 1:
                        result = s3_sync_eden_eden(peer, mode, tablenames,
                                                   settings=settings,
                                                   last_sync=last_sync_on,
                                                   complete_sync=complete)
                    else:
                        result = s3_sync_eden_other(peer, mode, tablenames,
                                                    pid=pid,
                                                    settings=settings)

            # Job done => read status
            if result:
                job_sync_errors = ",".join(result.errors)
                resources_done = ",".join(result.done)
                total_errors += result.errcount
            else:
                job_sync_errors = ""

            notify("Job %s done." % job_id)

            # Next job
            if jobs:
                job_id = jobs[0]
                job = db(db.sync_schedule.id == job_id).select(db.sync_schedule.ALL, limitby=(0, 1)).first()
                try:
                    job_cmd = json.loads(job.job_command)
                except:
                    res_list = ""
                else:
                    res_list = ",".join(map(str, job_cmd.get("resources", [])))

            # Update status
            db(db.sync_now.id==status.id).update(
                    sync_jobs = ",".join(jobs),
                    job_resources_done = "%s,%s" % (status.job_resources_done,
                                                    resources_done),
                    job_resources_pending = res_list,
                    job_sync_errors = "%s,%s" % (status.job_sync_errors, job_sync_errors))

            # Reload status
            status = db(db.sync_now.id == status.id).select(db.sync_now.ALL, limitby=(0, 1)).first()

        # All jobs done?
        if not status.sync_jobs:

            # @todo: log in history

            # Remove status
            db(db.sync_now.id==status.id).delete()

            # Notification
            if total_errors:
                notify("Synchronization complete (%s errors)." % total_errors)
            else:
                notify("Synchronization complete.")

        else:

            # Unlock
            db(db.sync_now.id==pid).update(locked=False, stop=False)

            # Notification
            error("Synchronization suspended.")

        return dict(item="SYNC NOW: done")

    elif action == "halt":

        """ Send HALT command to suspend a running sync/now """

        response.view = "xml.html"

        table = db.sync_now

        if status:
            pid = status.id
            db(table.id == pid).update(halt=True)

        notify("HALT command sent.")
        return dict(item="SYNC HALT: done")

    elif action == "stop":

        """ Remove a suspended sync/now """

        response.view = "xml.html"

        force = request.vars.get("force", False) and True

        table = db.sync_now

        if status:
            pid = status.id
            if (status.locked or status.halt) and not force:
                error("Synchronization process not halted - send HALT command first.")
            else:
                db(table.id == pid).delete()
                notify("Synchronization process removed.")
        else:
            error("No synchronization process found.")

        return dict(item="SYNC STOP: done")

    elif action == "unlock":

        """ Safely remove the lock from a broken Sync/now """

        response.view = "xml.html"

        table = db.sync_now

        if status:
            pid = status.id
            # Set HALT status at the same time to not deny
            # immedate resumption => requires two calls to
            # "start" to resume.
            db(table.id == pid).update(locked=False, halt=True)
            notify("Synchronization process unlocked and halted.")

        return dict(item="SYNC UNLOCK: done")

    elif action == "status":

        """ Retrieve pending messages from the notification queue """

        response.view = "xml.html"

        # Clear message queue
        s3_sync_clear_messages()

        table = db.sync_now

        if status:
            messages = s3_sync_get_messages(pid=status.id)
            if not messages:
                if status.locked:
                    return dict(item="")
        else:
            messages = s3_sync_get_messages()

        msg_list = []
        for i in xrange(len(messages)):
            msg = messages[i]
            if msg["error"]:
                msg_list.append(DIV(SPAN(msg["message"], _class="sync_message"),
                                    SPAN("ERROR", _class="sync_status"),
                                    _class="failure"))
            else:
                msg_list.append(DIV(SPAN(msg["message"], _class="sync_message"),
                                    SPAN("OK", _class="sync_status"),
                                    _class="success"))

        if msg_list:
            item = DIV(msg_list).xml()
        else:
            item = "DONE"

        return dict(item=item)

    else:
        """ Default view """

        pass

    # Extra stylesheet
    response.extra_styles = ["S3/sync.css"]

    return dict(module_name=module_name, action=action, status=status)

# -----------------------------------------------------------------------------
def sync():

    """ Sync interface

        allows PUT/GET of any resource (universal RESTful controller)

    """

    import gluon.contrib.simplejson as json

    if len(request.args) < 2:
        # No resource specified
        raise HTTP(501, body=s3xrc.ERROR.BAD_RESOURCE)
    else:
        prefix = request.args.pop(0)
        name = request.args.pop(0)

        if name.find(".") != -1:
            name, extension = name.rsplit(".", 1)
            request.extension = extension

    # Get the sync partner
    peer_uuid = request.vars.get("sync_partner_uuid", None)
    if peer_uuid:
        peers = db.sync_partner
        peer = db(peers.uuid == peer_uuid).select(limitby=(0,1)).first()

    # remote push?
    method = request.env.request_method
    if method in ("PUT", "POST"):
        remote_push = True
        # Must be registered partner for push:
        if not sync_peer:
            raise HTTP(501, body=s3xrc.ERROR.NOT_PERMITTED)
    elif method == "GET":
        remote_push = False
    else:
        raise HTTP(501, body=s3xrc.ERROR.BAD_METHOD)

    # Set the sync resolver with no policy (defaults to peer policy)
    s3xrc.sync_resolve = lambda vector, peer=peer: sync_res(vector, peer, None)

    def prep(r):
        # Do not allow interactive formats
        if r.representation in ("html", "popup", "iframe", "aadata"):
            return False
        # Do not allow URL methods
        if r.method:
            return False
        return True
    response.s3.prep = prep

    def postp(r, output, sync_peer=sync_peer):

        try:
            output_json = Storage(json.loads(output))
        except:
            # No JSON response?
            pass
        else:
            if r.http in ("PUT", "POST"):

                resource = r.resource
                sr = [c.component.tablename for c in resource.components.values()]
                sr.insert(0, resource.tablename)
                sync_resources = ",".join(sr)

                if str(output_json["statuscode"]) != "200":
                    sync_resources += " (error)"
                    sync_errors = str(output)
                else:
                    sync_errors = ""

                db[log_table].insert(
                    partner_uuid = sync_peer.uuid,
                    timestmp = datetime.datetime.utcnow(),
                    sync_resources = sync_resources,
                    sync_errors = sync_errors,
                    sync_mode = "online",
                    sync_method = "Remote Push",
                    complete_sync = False)

        return output
    response.s3.postp = postp

    # Execute the request
    output = shn_rest_controller(prefix, name)

    #return ret_data
    return output


# -----------------------------------------------------------------------------
def sync_res(vector, peer, policy):

    """ Sync resolver

        designed as callback for s3xrc.sync_resolve

    """

    import cPickle

    if policy is None:
        policy = peer.policy

    newer = True # assume that the peer record is newer

    if vector.method == vector.METHOD.UPDATE:
        table = vector.table
        if "modified_on" in table.fields and vector.mtime is not None:
            row = vector.db(table.id==vector.id).select(table.modified_on,
                                                        limitby=(0,1)).first()
            if row:
                local_mtime = row.modified_on
            if local_mtime > vector.mtime:
                newer = False

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

    conflict = False

    # @todo: conflict detection

    if policy == 0: # No Sync
        vector.resolution = vector.RESOLUTION.THIS
        vector.strategy = []
    elif policy == 1: # Manual
        vector.resolution = vector.RESOLUTION.THIS
        vector.strategy = []
    elif policy == 2: # Import
        vector.resolution = vector.RESOLUTION.OTHER
        vector.strategy = [vector.METHOD.CREATE]
    elif policy == 3: # Replace
        vector.resolution = vector.RESOLUTION.OTHER
        vector.strategy = [vector.METHOD.CREATE, vector.METHOD.UPDATE]
    elif policy == 4: # Update
        vector.resolution = vector.RESOLUTION.OTHER
        vector.strategy = [vector.METHOD.UPDATE]
    elif policy == 5: # Replace Newer
        vector.resolution = vector.RESOLUTION.NEWER
        vector.strategy = [vector.METHOD.CREATE, vector.METHOD.UPDATE]
    elif policy == 6: # Update Newer
        vector.resolution = vector.RESOLUTION.NEWER
        vector.strategy = [vector.METHOD.UPDATE]
    elif policy == 7: # Import Master
        vector.resolution = vector.RESOLUTION.MASTER
        vector.strategy = [vector.METHOD.CREATE]
    elif policy == 8: # Replace Master
        vector.resolution = vector.RESOLUTION.MASTER
        vector.strategy = [vector.METHOD.CREATE, vector.METHOD.UPDATE]
    elif policy == 9: # Update Master
        vector.resolution = vector.RESOLUTION.THIS
        vector.strategy = [vector.METHOD.UPDATE]
    elif policy == 10: # Role Based (not implemented)
        vector.resolution = vector.RESOLUTION.THIS
        vector.strategy = []
    else:
        pass # use defaults

    #elif sync_policy == 1:  # Keep Local
        #vector.resolution = vector.RESOLUTION.THIS

    #elif sync_policy == 2:  # Replace with Remote
        #vector.resolution = vector.RESOLUTION.OTHER
        #if (db_record_mtime and vector.mtime < db_record_mtime) or \
           #(db_record_mtime and sync_peer.last_sync_on and db_record_mtime > sync_peer.last_sync_on):
           ## log this as a conflict, remote record is older
            ## log this as a conflict, local record was modified too, but overwritten

    #elif sync_policy == 3:  # Keep with Newer Timestamp
        #vector.resolution = vector.RESOLUTION.NEWER
        #if db_record_mtime and vector.mtime < db_record_mtime:
            ## log this as a conflict, remote record is older

    #elif sync_policy == 4:  # Role-based
        ## not implemented, defaulting to "Newer Timestamp"
        #vector.resolution = vector.RESOLUTION.NEWER

    #elif sync_policy == 5:  # Choose Manually
        #if db_record_mtime and vector.mtime != db_record_mtime:
            ## just log and skip
            #vector.strategy = []

    if conflict: # log conflict

        record_dump = cPickle.dumps(dict(vector.record), 0)

        table_conflict.insert(
            uuid = vector.uuid,
            resource_table = vector.tablename,
            remote_record = record_dump,
            remote_modified_by = vector.element.get("modified_by", None),
            remote_modified_on = vector.mtime,
            logged_on = datetime.datetime.utcnow(),
            resolved = False)

    return


# -----------------------------------------------------------------------------
@auth.shn_requires_membership(1)
def partner():

    """ Synchronization Partners """

    import gluon.contrib.simplejson as json

    table = db.sync_partner

    table.uuid.label = "UUID"
    table.uuid.comment = DIV(SPAN("*", _class="req"), DIV(_class="tooltip",
        _title="UUID|" + Tstr("The unique identifier of the peer. Leave blank if the peer is no Sahana Eden instance, it will be auto-assigned in that case.")))

    table.name.label = T("Name")
    table.name.comment = DIV(_class="tooltip",
        _title=Tstr("Name") + "|" + Tstr("The descriptive name of the peer."))

    table.url.label = T("URL")
    table.url.comment = DIV(SPAN("*", _class="req"), DIV(_class="tooltip",
        _title=Tstr("URL") + "|" + Tstr("For Eden instances enter the application base URL, e.g. http://sync.sahanfoundation.org/eden, for other peers the URL of the synchronization interface.")))

    #table.type.label = T("Instance Type")
    #table.type.comment = DIV(SPAN("*", _class="req"), DIV(_class="tooltip",
        #_title=Tstr("Instance Type") + "|" + Tstr("Whether this is a Sahana Eden, Sahana Agasti, Ushahidi or Other instance.")))

    table.username.label = T("Username")
    table.username.comment = DIV(_class="tooltip",
        _title=Tstr("Username") + "|" + Tstr("Username for authentication at the peer. Note that only HTTP Basic authentication is supported."))

    table.password.label = T("Password")
    table.password.comment = DIV(_class="tooltip",
        _title=Tstr("Password") + "|" + Tstr("Password for authentication at the peer. Note that only HTTP Basic authentication is supported."))

    #table.comments.label = T("Comments")
    #table.comments.comment = DIV(_class="tooltip",
        #_title=Tstr("Comments") + "|" + Tstr("Any comments about this sync partner."))

    table.policy.label = T("Data import policy")
    table.policy.comment = DIV(SPAN("*", _class="req"), DIV(_class="tooltip",
        _title=Tstr("Data import policy") + "|" + Tstr("The default policy for data import from this peer.")))

    # CRUD Strings
    s3.crud_strings["sync_partner"] = Storage(
        title_create = T("Add Peer"),
        title_display = T("Peer Details"),
        title_list = T("Synchronization Peers"),
        title_update = T("Edit Peer"),
        title_search = T("Search Peers"),
        subtitle_create = T("Add New Peer"),
        subtitle_list = T("Peers"),
        label_list_button = T("List Peers"),
        label_create_button = T("Add Peer"),
        label_search_button = T("Search Peers"),
        msg_record_created = T("Peer added"),
        msg_record_modified = T("Peer updated"),
        msg_record_deleted = T("Peer deleted"),
        msg_list_empty = T("No Peers currently registered"))


    def prep(r):
        if r.method == "create":
            s3xrc.model.configure(db.sync_partner,
                onaccept = lambda form: sync_partner_onaccept(form))
        return True
    response.s3.prep = prep

    response.s3.pagination = True

    return shn_rest_controller("sync", "partner")


# -----------------------------------------------------------------------------
@auth.shn_requires_membership(1)
def setting():

    """ Synchronisation Settings """

    # Table settings
    table = db.sync_setting

    table.uuid.label = "UUID"
    table.uuid.comment = DIV(_class="tooltip",
        _title="UUID|" + Tstr("The unique identifier which identifies this instance to other instances."))

    # CRUD strings
    s3.crud_strings.sync_setting = Storage(
        title_update = T("Synchronization Settings"),
        msg_record_modified = T("Synchronization settings updated"))

    def prep(r):
        if r.component or \
           str(r.id) != "1" or r.method != "update":
               redirect(URL(r=request, args=["update", 1]))
        return True
    response.s3.prep = prep

    def postp(r, output):
        if isinstance(output, dict) and output.get("list_btn", None):
            del output["list_btn"]
        return output
    response.s3.postp = postp

    crud.settings.update_next = URL(r=request, args=["update", 1])

    return shn_rest_controller("sync", "setting", deletable=False, listadd=False)


# -----------------------------------------------------------------------------
@auth.shn_requires_membership(1)
def schedule():

    """ Synchronisation Schedules """

    import gluon.contrib.simplejson as json
    title = T("Syncronisation Schedules")

    jobs = None
    confirmation_msg = None

    if "create" in request.args:

        response.view = "sync/schedule_create.html"

        if "form_action" in request.vars and request.vars["form_action"] == "submit":
            # create new job - add it to database
            sch_enabled = True
            if "job_enabled" in request.vars and request.vars["job_enabled"] == "0":
                sch_enabled = False
            sch_comments = None
            if "comments" in request.vars:
                sch_comments = request.vars["comments"]
            sch_source_type = "eden"
            if "sync_data_source_type" in request.vars:
                sch_source_type = request.vars["sync_data_source_type"]
            sch_period = "h"
            if "sync_schedule_period" in request.vars:
                sch_period = request.vars["sync_schedule_period"]
            sch_period_hours = 5
            if "sync_schedule_period_hours" in request.vars:
                sch_period_hours = request.vars["sync_schedule_period_hours"]
            sch_days_of_week = []
            if "sync_schedule_weekly_days" in request.vars and request.vars["sync_schedule_weekly_days"]:
                sch_days_of_week = request.vars["sync_schedule_weekly_days"]
            sch_time_of_day = None
            if sch_period == "d":
                sch_time_of_day = datetime.datetime.strptime(str(request.vars["sync_schedule_daily_time"]), "%H:%M").time()
            elif sch_period == "w":
                sch_time_of_day = datetime.datetime.strptime(str(request.vars["sync_schedule_weekly_time"]), "%H:%M").time()
            sch_runonce_datetime = None
            if "sync_schedule_once_datetime" in request.vars and request.vars["sync_schedule_once_datetime"]:
                sch_runonce_datetime = datetime.datetime.strptime(str(request.vars["sync_schedule_once_datetime"]), "%Y-%m-%d %H:%M:%S")

            sch_job_type = 1
            sch_cmd = dict()
            sch_cmd["partner_uuid"] = request.vars["sync_partner_uuid"]
            sch_cmd["policy"] = int(request.vars["sync_policy"])
            if sch_source_type == "eden":
                # eden data source
                if "sync_resources" in request.vars and request.vars["sync_resources"]:
                    sch_cmd["resources"] = request.vars["sync_resources"]
                    if type(sch_cmd["resources"]) == str:
                        sch_cmd["resources"] = [sch_cmd["resources"]]
                else:
                    sch_cmd["resources"] = None
                sch_cmd["complete"] = False
                if "sync_complete" in request.vars and request.vars["sync_complete"] == "1":
                    sch_cmd["complete"] = True
                sch_cmd["mode"] = 3
                if "sync_mode" in request.vars and request.vars["sync_mode"]:
                    sch_cmd["mode"] = int(request.vars["sync_mode"])
            else:
                # custom data source
                sch_job_type = 2
                sch_cmd["custom_command"] = request.vars["sync_custom"]

            # add job to db
            db["sync_schedule"].insert(
                comments = sch_comments,
                period = sch_period,
                hours = sch_period_hours,
                days_of_week = ",".join(map(str, sch_days_of_week)),
                time_of_day = sch_time_of_day,
                runonce_datetime = sch_runonce_datetime,
                job_type = sch_job_type,
                job_command = json.dumps(sch_cmd),
                last_run = None,
                enabled = sch_enabled,
                created_on = datetime.datetime.now(),
                modified_on = datetime.datetime.now()
            )

            confirmation_msg = "New Scheduled job created"
            response.view = "sync/schedule.html"
    else:
        if "form_action" in request.vars and "selected_jobs" in request.vars:
            sel_jobs = request.vars["selected_jobs"]
            if request.vars["form_action"] == "enable":
                for s_job_id in sel_jobs:
                    vals = {"enabled": True}
                    db(db.sync_schedule.id==int(s_job_id)).update(**vals)
            elif request.vars["form_action"] == "disable":
                for s_job_id in sel_jobs:
                    vals = {"enabled": False}
                    db(db.sync_schedule.id==int(s_job_id)).update(**vals)
            elif request.vars["form_action"] == "delete":
                for s_job_id in sel_jobs:
                    db(db.sync_schedule.id==int(s_job_id)).delete()

    jobs = db().select(db.sync_schedule.ALL)

    return dict(title=title, jobs=jobs, confirmation_msg=confirmation_msg)


# -----------------------------------------------------------------------------
def schedule_cron():
    # only accept requests from local machine
    if not request.env.remote_addr == "127.0.0.1":
        return

    while True:
        try:
            # look at each job and run if it it's scheduled time
            jobs = db(db.sync_schedule.enabled==True).select(db.sync_schedule.ALL)
            for job in jobs:
                last_run = job.last_run
                if not last_run:
                    last_run = job.created_on - datetime.timedelta(days=2)
                try:
                    if job.period == "h":
                        if datetime.datetime.now() >= (last_run + datetime.timedelta(hours=job.hours)):
                            schedule_process_job(job.id)
                            db.commit()
                    elif job.period == "d":
                        if job.time_of_day and last_run.date() != datetime.datetime.now().date() and datetime.datetime.now().hour >= job.time_of_day.hour and datetime.datetime.now().minute >= job.time_of_day.minute:
                            schedule_process_job(job.id)
                            db.commit()
                    elif job.period == "w":
                        days_of_week = None
                        last_run_weekday = last_run.weekday() + 1
                        if last_run_weekday == 8:
                            last_run_weekday = 1
                        now_weekday = datetime.datetime.now().weekday() + 1
                        if now_weekday == 8:
                            now_weekday = 1
                        if job.days_of_week:
                            days_of_week = map(int, job.days_of_week.split(","))
                        if job.time_of_day and now_weekday in days_of_week and last_run_weekday < now_weekday and datetime.datetime.now().hour >= job.time_of_day.hour and datetime.datetime.now().minute >= job.time_of_day.minute:
                            schedule_process_job(job.id)
                            db.commit()
                    elif job.period == "o":
                        if job.runonce_datetime and last_run < job.runonce_datetime and datetime.datetime.now() >= job.runonce_datetime:
                            schedule_process_job(job.id)
                            db.commit()
                except Error, e:
                    # log scheduler error
                    try:
                        log_file = open("applications/" + request.application + "/cron/scheduler_errors.txt", "a")
                        log_file.write(str(datetime.datetime.now()) + " - error while running job " + str(job.id) + ":\n" + str(e) + "\n\n")
                        log_file.close()
                    except:
                        pass
            db.commit()
        except Error, e:
            # log scheduler error
            try:
                log_file = open("applications/" + request.application + "/cron/scheduler_errors.txt", "a")
                log_file.write(str(datetime.datetime.now()) + " - error while running job " + str(job.id) + ":\n" + str(e) + "\n\n")
                log_file.close()
            except:
                pass

        # pause for 15 seconds
        time.sleep(15)

    return


# -----------------------------------------------------------------------------
def schedule_process_job(job_id):

    """ docstring??? """

    import gluon.contrib.simplejson as json
    import urllib, urlparse

    #global sync_policy # @todo: do not use global vars

    job_sel = db(db.sync_schedule.id==job_id).select(db.sync_schedule.ALL)
    if not job_sel:
        return
    job = job_sel[0]
    if not job:
        return
    if not job.enabled:
        return

    job_cmd = json.loads(job.job_command)

    # url fetcher
    #fetcher = FetchURL()
    # retrieve settings
    settings = db().select(db.sync_setting.ALL)[0]
    peer_sel = db(db.sync_partner.uuid==str(job_cmd["partner_uuid"])).select(db.sync_partner.ALL)
    if not peer_sel:
        return
    peer = peer_sel[0]

    peer_sync_success = True
    last_sync_on = job.last_run
    complete_sync = False
    sync_mode = 1
    if "complete" in job_cmd and str(job_cmd["complete"]) == "True":
        complete_sync = True
    if "policy" in job_cmd:
        sync_policy = int(job_cmd["policy"])
    if "mode" in job_cmd:
        sync_mode = int(job_cmd["mode"])
    sync_resources = []
    sync_errors = ""

    # Keep Session for local URLs
    cookie = str(response.session_id_name) + "=" + str(response.session_id)

    if job.job_type == 1:
        # Sync Eden sync
        if (not last_sync_on is None) and complete_sync == False:
            last_sync_on_str = "?msince=" + last_sync_on.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            last_sync_on_str = ""

        log_file = open("applications/" + request.application + "/cron/scheduler_log.txt", "a")
        log_file.write(str(datetime.datetime.now()) + " - running job " + str(job.id) + "\n")
        log_file.close()
        for res_item in job_cmd["resources"]:
            _module, _resource = res_item.split("||")
            _resource_name = _module + "_" + _resource
            peer_url = list(urlparse.urlparse(peer.url))
            if peer_url[2].endswith("/")==False:
                peer_url[2] += "/"
            resource_remote_pull_url = peer.url
            if resource_remote_pull_url.endswith("/")==False:
                resource_remote_pull_url += "/"
            resource_remote_pull_url += "sync/sync." + import_export_format + "/" + _module + "/" + _resource + last_sync_on_str
            resource_remote_push_url = peer_url[2] + "sync/sync." + import_export_format + "/push/" + _module + "/" + _resource + "?sync_partner_uuid=" + str(settings.uuid)
            resource_local_pull_url = "/" + request.application + "/sync/sync." + import_export_format + "/" + _module + "/" + _resource + last_sync_on_str
            resource_local_push_url = "/" + request.application + "/sync/sync." + import_export_format + "/create/" + _module + "/" + _resource
            if sync_mode in [1, 3]:
                # Sync -> Pull
                _request_params = urllib.urlencode({"sync_partner_uuid": str(peer.uuid), "fetchurl": resource_remote_pull_url})
                _request_vars_copy = request.vars
                _request_get_vars_copy = request.get_vars
                _request_post_vars_copy = request.post_vars
                _request_args_copy = request.args
                _request_extension_copy = request.extension
                _request_env_request_method_copy = request.env.request_method
                try:
                    #_response = fetcher.fetch("PUT", request.env.http_host, resource_local_push_url, _request_params, cookie)
                    request.vars = Storage()
                    request.vars["sync_partner_uuid"] = str(peer.uuid)
                    request.vars["fetchurl"] = resource_remote_pull_url
                    request.args = ["push", _module, _resource]
                    request.extension = import_export_format
                    request.env.request_method = "PUT"
                    session.auth = Storage()
                    session.auth["user"] = None
                    session.s3.roles.append(1)
                    _response = sync()
                except Error, e:
                    if not _resource_name + " (error)" in sync_resources and not _resource_name in sync_resources:
                        sync_resources.append(_resource_name + " (error)")
                        error_str = str(e)
                        sync_errors +=  "Error while syncing => " + _resource_name + ": \n" + error_str + "\n\n"
                else:
                    if not _resource_name + " (error)" in sync_resources and not _resource_name in sync_resources:
                        sync_resources.append(_resource_name)
                request.args = _request_args_copy
                request.get_vars = _request_get_vars_copy
                request.post_vars = _request_post_vars_copy
                request.vars = _request_vars_copy
                request.extension = _request_extension_copy
                request.env.request_method = _request_env_request_method_copy
            if sync_mode in [2, 3]:
                # Sync -> Push
                try:
                    _local_data = fetcher.fetch("GET", request.env.http_host, resource_local_pull_url, None, cookie)
                    _response = fetcher.fetch("PUT", peer_url[1], resource_remote_push_url, _local_data, None, peer.username, peer.password)
                except Error, e:
                    if not _resource_name + " (error)" in sync_resources and not _resource_name in sync_resources:
                        sync_resources.append(_resource_name + " (error)")
                    error_str = str(e)
                    sync_errors +=  "Error while syncing => " + _resource_name + ": \n" + error_str + "\n\n"
                else:
                    if not _resource_name + " (error)" in sync_resources and not _resource_name in sync_resources:
                        sync_resources.append(_resource_name)

    else:
        # Custom sync
        sync_mode = 1
        _request_vars_copy = request.vars
        _request_get_vars_copy = request.get_vars
        _request_post_vars_copy = request.post_vars
        _request_args_copy = request.args
        _request_extension_copy = request.extension
        try:
            request.vars = Storage()
            request.vars["sync_partner_uuid"] = str(peer.uuid)
            request.vars["fetchurl"] = job_cmd["custom_command"]
            request.args = ["create", "sync", "log"]
            request.extension = import_export_format
            _response = sync()
        except Error, e:
            error_str = str(e)
            sync_errors =  "Error while syncing job " + str(job.id) + ": \n" + error_str + "\n\n"
        request.args = _request_args_copy
        request.get_vars = _request_get_vars_copy
        request.post_vars = _request_post_vars_copy
        request.vars = _request_vars_copy
        request.extension = _request_extension_copy

    if sync_mode == 1:
        sync_method = "Pull"
    elif sync_mode == 2:
        sync_method = "Push"
    elif sync_mode == 3:
        sync_method = "Pull-Push"

    # log sync job
    log_table_id = db[log_table].insert(
        partner_uuid = peer.uuid,
        timestmp = datetime.datetime.utcnow(),
        sync_resources = ", ".join(map(str, sync_resources)),
        sync_errors = sync_errors,
        sync_mode = "online",
        sync_method = sync_method,
        complete_sync = complete_sync
    )

    # update last_sync_on
    vals = {"last_sync_on": datetime.datetime.utcnow()}
    db(db.sync_partner.id==peer.id).update(**vals)
    vals = {"last_run": datetime.datetime.utcnow()}
    db(db.sync_schedule.id==job_id).update(**vals)

    return


# -----------------------------------------------------------------------------
@auth.requires_login()
def history():

    """ Shows history of database synchronisations """

    title = T("Synchronisation History")

    table = db.sync_log

    id = None
    if len(request.args) > 0:
        try:
            id = int(request.args[0])
        except ValueError:
            pass

    if id:
        logs = db(table.id==id).select(table.ALL, limitby=(0,1))
    else:
        logs = db().select(table.ALL, orderby=table.timestmp)

    return dict(title=title, logs=logs)


# -----------------------------------------------------------------------------
@auth.shn_requires_membership(1)
def conflict():

    """ Conflict Resolution UI """

    import cPickle
    table_conflict = db.sync_conflict

    title = T("Conflict Resolution")

    def get_modified_by(user_email):
        """ Get a "nice" name for a user """
        # Q: is this necessary? isn't the email-address better?
        modified_by = user_email
        table = db.auth_user
        user = db(table.email == user_email).select(user.first_name,
                                                    user.last_name,
                                                    limitby=(0,1)).first()
        if user:
            modified_by  = user.first_name
            if user.last_name:
                modified_by += " " + user.last_name
        return modified_by

    skip_fields = ["uuid", "id"]

    field_errors = dict()

    conflicts = db(table_conflict.resolved==False).select(table_conflict.ALL, orderby=table_conflict.logged_on)
    for idx in xrange(0, len(conflicts)):
        if not conflicts[idx].resource_table in db.tables:
            del conflicts[idx]
    record_nbr = 1
    if "record_nbr" in request.vars:
        record_nbr = int(request.vars["record_nbr"])
    total_conflicts = len(conflicts)
    if record_nbr < 1 or record_nbr > total_conflicts:
        record_nbr = 1
    if total_conflicts == 0:
        conflict = None
    else:
        conflict = conflicts[record_nbr - 1]
    remote_record = None
    local_record = None
    local_modified_by = None
    remote_modified_by = None
    if conflict:
        remote_record = cPickle.loads(conflict.remote_record)
        local_record = db(db[conflict.resource_table].uuid==conflict.uuid).select().first()
        if conflict.remote_modified_by:
            remote_modified_by = get_modified_by(conflict.remote_modified_by)
        if "modified_by" in local_record:
            local_modified_by = get_modified_by(local_record.modified_by.email)

    if "form_action" in request.vars:
        if request.vars["form_action"] == "resolve" and conflict:
            if local_record:
                # update local record
                for field in remote_record:
                    if (not field in skip_fields) and (field in db[conflict.resource_table].fields):
                        if "final_"+str(field) in request.vars:
                            vals = {field: request.vars["final_" + str(field)]}
                        else:
                            if db[conflict.resource_table][field].type == "boolean":
                                vals = {field: "False"}
                            else:
                                vals = {field: ""}

                        field_error = db[conflict.resource_table][field].validate(vals[field])[1]
                        if field_error:
                            field_errors[field] = field_error
                        # update only if no errors
                        if len(field_errors) == 0:
                            db(db[conflict.resource_table].uuid==conflict.uuid).update(**vals)
                            # undelete record
                            if "deleted" in db[conflict.resource_table].fields:
                                vals = {"deleted": False}
                                db(db[conflict.resource_table].uuid==conflict.uuid).update(**vals)
            else:
                # insert record
                new_rec = dict()
                for field in remote_record:
                    if field in table_conflict.fields:
                        if "final_"+field in request.vars:
                            new_rec[field] = request.vars["final_"+field]
                        else:
                            new_rec[field] = remote_record[field]
                        field_error = db[conflict.resource_table][field].validate(vals[field])[1]
                        if field_error:
                            field_errors[field] = field_error
                # insert only if no errors
                if len(field_errors) == 0:
                    db[conflict.resource_table].insert(**new_rec)

            # set status to resolved if no errors
            if len(field_errors) == 0:
                conflict.update_record(resolved = True)
            # next conflict
            conflicts = db(table_conflict.resolved==False).select(table_conflict.ALL, orderby=table_conflict.logged_on)
            for idx in xrange(0, len(conflicts)):
                if not conflicts[idx].resource_table in db.tables:
                    del conflicts[idx]
            total_conflicts = len(conflicts)
            if record_nbr < 1 or record_nbr > total_conflicts:
                record_nbr = 1
            if total_conflicts == 0:
                conflict = None
            else:
                conflict = conflicts[record_nbr - 1]
            remote_record = None
            local_record = None
            if conflict:
                remote_record = cPickle.loads(conflict.remote_record)
                local_record = db(db[conflict.resource_table].uuid==conflict.uuid).select().first()
                if conflict.remote_modified_by:
                    remote_modified_by = get_modified_by(conflict.remote_modified_by)
                if "modified_by" in local_record:
                    local_modified_by = get_modified_by(local_record.modified_by.email)

    form = None
    if conflict:
        form = SQLFORM.factory(db[conflict.resource_table])

    return dict(title=title,
                skip_fields=skip_fields,
                total_conflicts=total_conflicts,
                conflict=conflict,
                record_nbr=record_nbr,
                local_record=local_record,
                remote_record=remote_record,
                local_modified_by=local_modified_by,
                remote_modified_by=remote_modified_by,
                form=form,
                field_errors=field_errors)

# -----------------------------------------------------------------------------
