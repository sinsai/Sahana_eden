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
@auth.shn_requires_membership(1)
def peer():

    prefix = module
    name = "peer"

    db.sync_job.peer_id.readable = False
    db.sync_job.peer_id.writable = False

    primary_resources = s3_sync_primary_resources()
    db.sync_job.resources.requires = IS_NULL_OR(IS_IN_SET(primary_resources, multiple=True, zero=None))

    db.sync_log.peer_id.readable = False
    db.sync_log.peer_id.writable = False

    table = db.sync_peer
    table.uuid.label = T("UID")
    table.url.label = "URL"

    response.s3.pagination = True

    rheader = lambda r: sync_rheader(r, tabs=[
                                    (T("Peer"), None),
                                    (T("Jobs"), "job"),
                                    (T("Log"), "log")])

    return shn_rest_controller(prefix, name,
                               listadd=False,
                               rheader=rheader)


# -----------------------------------------------------------------------------
@auth.requires_login()
def now():

    """ Manual synchronization """

    import gluon.contrib.simplejson as json

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
@auth.requires_login()
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
            # Set the sync resolver with no policy (defaults to peer policy)
            s3xrc.sync_resolve = lambda vector, peer=peer: sync_res(vector, peer, None)
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


## -----------------------------------------------------------------------------
#@auth.shn_requires_membership(1)
#def partner():

    #""" Synchronization Partners """

    #import gluon.contrib.simplejson as json

    #table = db.sync_partner

    #table.uuid.label = "UUID"
    #table.uuid.comment = DIV(SPAN("*", _class="req"), DIV(_class="tooltip",
        #_title="UUID|" + T("The unique identifier of the peer. Leave blank if the peer is no Sahana Eden instance, it will be auto-assigned in that case.")))

    #table.name.label = T("Name")
    #table.name.comment = DIV(_class="tooltip",
        #_title=T("Name") + "|" + T("The descriptive name of the peer."))

    #table.url.label = "URL"
    #table.url.comment = DIV(SPAN("*", _class="req"), DIV(_class="tooltip",
        #_title="URL" + "|" + T("For Eden instances enter the application base URL, e.g. http://sync.sahanfoundation.org/eden, for other peers the URL of the synchronization interface.")))

    ##table.type.label = T("Instance Type")
    ##table.type.comment = DIV(SPAN("*", _class="req"), DIV(_class="tooltip",
        ##_title=T("Instance Type") + "|" + T("Whether this is a Sahana Eden, Sahana Agasti, Ushahidi or Other instance.")))

    #table.username.label = T("Username")
    #table.username.comment = DIV(_class="tooltip",
        #_title=T("Username") + "|" + T("Username for authentication at the peer. Note that only HTTP Basic authentication is supported."))

    #table.password.label = T("Password")
    #table.password.comment = DIV(_class="tooltip",
        #_title=T("Password") + "|" + T("Password for authentication at the peer. Note that only HTTP Basic authentication is supported."))

    ##table.comments.label = T("Comments")
    ##table.comments.comment = DIV(_class="tooltip",
        ##_title=T("Comments") + "|" + T("Any comments about this sync partner."))

    #table.policy.label = T("Data import policy")
    #table.policy.comment = DIV(SPAN("*", _class="req"), DIV(_class="tooltip",
        #_title=T("Data import policy") + "|" + T("The default policy for data import from this peer.")))

    ## CRUD Strings
    #s3.crud_strings["sync_partner"] = Storage(
        #title_create = T("Add Peer"),
        #title_display = T("Peer Details"),
        #title_list = T("Synchronization Peers"),
        #title_update = T("Edit Peer"),
        #title_search = T("Search Peers"),
        #subtitle_create = T("Add New Peer"),
        #subtitle_list = T("Peers"),
        #label_list_button = T("List Peers"),
        #label_create_button = T("Add Peer"),
        #label_search_button = T("Search Peers"),
        #msg_record_created = T("Peer added"),
        #msg_record_modified = T("Peer updated"),
        #msg_record_deleted = T("Peer deleted"),
        #msg_list_empty = T("No Peers currently registered"))


    #def prep(r):
        #if r.method == "create":
            #s3xrc.model.configure(db.sync_partner,
                #onaccept = lambda form: s3_sync_partner_oncreate(form))
        #return True
    #response.s3.prep = prep

    #response.s3.pagination = True

    #return shn_rest_controller("sync", "partner")


# -----------------------------------------------------------------------------
@auth.shn_requires_membership(1)
def setting():

    """ Synchronisation Settings """

    # Table settings
    table = db.sync_setting

    table.uuid.label = "UUID"
    table.uuid.comment = DIV(_class="tooltip",
        _title="UUID|" + T("The unique identifier which identifies this instance to other instances."))

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
def job():

    prefix = module
    name = "job"

    primary_resources = s3_sync_primary_resources()
    db.sync_job.resources.requires = IS_NULL_OR(IS_IN_SET(primary_resources, multiple=True, zero=None))

    response.s3.pagination = True

    return shn_rest_controller(prefix, name)


# -----------------------------------------------------------------------------
@auth.requires_login()
def log():

    prefix = module
    name = "log"

    response.s3.pagination = True

    return shn_rest_controller(prefix, name,
                listadd = False,
                editable = False,
                deletable = True)

## -----------------------------------------------------------------------------
#@auth.shn_requires_membership(1)
#def schedule():

    #""" Synchronisation Schedules """

    #import gluon.contrib.simplejson as json
    #title = T("Syncronisation Schedules")

    #jobs = None
    #confirmation_msg = None

    #if "create" in request.args:

        #response.view = "sync/schedule_create.html"

        #if "form_action" in request.vars and request.vars["form_action"] == "submit":
            ## create new job - add it to database
            #sch_enabled = True
            #if "job_enabled" in request.vars and request.vars["job_enabled"] == "0":
                #sch_enabled = False
            #sch_comments = None
            #if "comments" in request.vars:
                #sch_comments = request.vars["comments"]
            #sch_source_type = "eden"
            #if "sync_data_source_type" in request.vars:
                #sch_source_type = request.vars["sync_data_source_type"]
            #sch_period = "h"
            #if "sync_schedule_period" in request.vars:
                #sch_period = request.vars["sync_schedule_period"]
            #sch_period_hours = 5
            #if "sync_schedule_period_hours" in request.vars:
                #sch_period_hours = request.vars["sync_schedule_period_hours"]
            #sch_days_of_week = []
            #if "sync_schedule_weekly_days" in request.vars and request.vars["sync_schedule_weekly_days"]:
                #sch_days_of_week = request.vars["sync_schedule_weekly_days"]
            #sch_time_of_day = None
            #if sch_period == "d":
                #sch_time_of_day = datetime.datetime.strptime(str(request.vars["sync_schedule_daily_time"]), "%H:%M").time()
            #elif sch_period == "w":
                #sch_time_of_day = datetime.datetime.strptime(str(request.vars["sync_schedule_weekly_time"]), "%H:%M").time()
            #sch_runonce_datetime = None
            #if "sync_schedule_once_datetime" in request.vars and request.vars["sync_schedule_once_datetime"]:
                #sch_runonce_datetime = datetime.datetime.strptime(str(request.vars["sync_schedule_once_datetime"]), "%Y-%m-%d %H:%M:%S")

            #sch_job_type = 1
            #sch_cmd = dict()
            #sch_cmd["partner_uuid"] = request.vars["sync_partner_uuid"]
            #sch_cmd["policy"] = int(request.vars["sync_policy"])
            #if sch_source_type == "eden":
                ## eden data source
                #if "sync_resources" in request.vars and request.vars["sync_resources"]:
                    #sch_cmd["resources"] = request.vars["sync_resources"]
                    #if type(sch_cmd["resources"]) == str:
                        #sch_cmd["resources"] = [sch_cmd["resources"]]
                #else:
                    #sch_cmd["resources"] = None
                #sch_cmd["complete"] = False
                #if "sync_complete" in request.vars and request.vars["sync_complete"] == "1":
                    #sch_cmd["complete"] = True
                #sch_cmd["mode"] = 3
                #if "sync_mode" in request.vars and request.vars["sync_mode"]:
                    #sch_cmd["mode"] = int(request.vars["sync_mode"])
            #else:
                ## custom data source
                #sch_job_type = 2
                #sch_cmd["custom_command"] = request.vars["sync_custom"]

            ## add job to db
            #db["sync_schedule"].insert(
                #comments = sch_comments,
                #period = sch_period,
                #hours = sch_period_hours,
                #days_of_week = ",".join(map(str, sch_days_of_week)),
                #time_of_day = sch_time_of_day,
                #runonce_datetime = sch_runonce_datetime,
                #job_type = sch_job_type,
                #job_command = json.dumps(sch_cmd),
                #last_run = None,
                #enabled = sch_enabled,
                #created_on = datetime.datetime.now(),
                #modified_on = datetime.datetime.now()
            #)

            #confirmation_msg = "New Scheduled job created"
            #response.view = "sync/schedule.html"
    #else:
        #if "form_action" in request.vars and "selected_jobs" in request.vars:
            #sel_jobs = request.vars["selected_jobs"]
            #if request.vars["form_action"] == "enable":
                #for s_job_id in sel_jobs:
                    #vals = {"enabled": True}
                    #db(db.sync_schedule.id==int(s_job_id)).update(**vals)
            #elif request.vars["form_action"] == "disable":
                #for s_job_id in sel_jobs:
                    #vals = {"enabled": False}
                    #db(db.sync_schedule.id==int(s_job_id)).update(**vals)
            #elif request.vars["form_action"] == "delete":
                #for s_job_id in sel_jobs:
                    #db(db.sync_schedule.id==int(s_job_id)).delete()

    #jobs = db().select(db.sync_schedule.ALL)

    #return dict(title=title, jobs=jobs, confirmation_msg=confirmation_msg)


## -----------------------------------------------------------------------------
#def schedule_cron():
    ## only accept requests from local machine
    #if not request.env.remote_addr == "127.0.0.1":
        #return

    #while False:
        #try:
            ## look at each job and run if it it's scheduled time
            #jobs = db(db.sync_schedule.enabled==True).select(db.sync_schedule.ALL)
            #for job in jobs:
                #last_run = job.last_run
                #if not last_run:
                    #last_run = job.created_on - datetime.timedelta(days=2)
                #try:
                    #if job.period == "h":
                        #if datetime.datetime.now() >= (last_run + datetime.timedelta(hours=job.hours)):
                            #schedule_process_job(job.id)
                            #db.commit()
                    #elif job.period == "d":
                        #if job.time_of_day and last_run.date() != datetime.datetime.now().date() and datetime.datetime.now().hour >= job.time_of_day.hour and datetime.datetime.now().minute >= job.time_of_day.minute:
                            #schedule_process_job(job.id)
                            #db.commit()
                    #elif job.period == "w":
                        #days_of_week = None
                        #last_run_weekday = last_run.weekday() + 1
                        #if last_run_weekday == 8:
                            #last_run_weekday = 1
                        #now_weekday = datetime.datetime.now().weekday() + 1
                        #if now_weekday == 8:
                            #now_weekday = 1
                        #if job.days_of_week:
                            #days_of_week = map(int, job.days_of_week.split(","))
                        #if job.time_of_day and now_weekday in days_of_week and last_run_weekday < now_weekday and datetime.datetime.now().hour >= job.time_of_day.hour and datetime.datetime.now().minute >= job.time_of_day.minute:
                            #schedule_process_job(job.id)
                            #db.commit()
                    #elif job.period == "o":
                        #if job.runonce_datetime and last_run < job.runonce_datetime and datetime.datetime.now() >= job.runonce_datetime:
                            #schedule_process_job(job.id)
                            #db.commit()
                #except Error, e:
                    ## log scheduler error
                    #try:
                        #log_file = open("applications/" + request.application + "/cron/scheduler_errors.txt", "a")
                        #log_file.write(str(datetime.datetime.now()) + " - error while running job " + str(job.id) + ":\n" + str(e) + "\n\n")
                        #log_file.close()
                    #except:
                        #pass
            #db.commit()
        #except Error, e:
            ## log scheduler error
            #try:
                #log_file = open("applications/" + request.application + "/cron/scheduler_errors.txt", "a")
                #log_file.write(str(datetime.datetime.now()) + " - error while running job " + str(job.id) + ":\n" + str(e) + "\n\n")
                #log_file.close()
            #except:
                #pass

        ## pause for 15 seconds
        #time.sleep(15)

    #return


## -----------------------------------------------------------------------------
#@auth.requires_login()
#def history():

    #""" Shows history of database synchronisations """

    #title = T("Synchronisation History")

    #table = db.sync_log

    #id = None
    #if len(request.args) > 0:
        #try:
            #id = int(request.args[0])
        #except ValueError:
            #pass

    #if id:
        #logs = db(table.id==id).select(table.ALL, limitby=(0,1))
    #else:
        #logs = db().select(table.ALL, orderby=table.timestmp)

    #return dict(title=title, logs=logs)


# -----------------------------------------------------------------------------
@auth.shn_requires_membership(1)
def conflict():

    """ Conflict Resolution UI """

    prefix = module
    name = "conflict"

    return shn_rest_controller(prefix, name,
                listadd = False,
                editable = False,
                deletable = True)

    #import cPickle
    #table_conflict = db.sync_conflict

    #title = T("Conflict Resolution")

    #def get_modified_by(user_email):
        #""" Get a "nice" name for a user """
        ## Q: is this necessary? isn't the email-address better?
        #modified_by = user_email
        #table = db.auth_user
        #user = db(table.email == user_email).select(user.first_name,
                                                    #user.last_name,
                                                    #limitby=(0,1)).first()
        #if user:
            #modified_by  = user.first_name
            #if user.last_name:
                #modified_by += " " + user.last_name
        #return modified_by

    #skip_fields = ["uuid", "id"]

    #field_errors = dict()

    #conflicts = db(table_conflict.resolved==False).select(table_conflict.ALL, orderby=table_conflict.logged_on)
    #for idx in xrange(0, len(conflicts)):
        #if not conflicts[idx].resource_table in db.tables:
            #del conflicts[idx]
    #record_nbr = 1
    #if "record_nbr" in request.vars:
        #record_nbr = int(request.vars["record_nbr"])
    #total_conflicts = len(conflicts)
    #if record_nbr < 1 or record_nbr > total_conflicts:
        #record_nbr = 1
    #if total_conflicts == 0:
        #conflict = None
    #else:
        #conflict = conflicts[record_nbr - 1]
    #remote_record = None
    #local_record = None
    #local_modified_by = None
    #remote_modified_by = None
    #if conflict:
        #remote_record = cPickle.loads(conflict.remote_record)
        #local_record = db(db[conflict.resource_table].uuid==conflict.uuid).select().first()
        #if conflict.remote_modified_by:
            #remote_modified_by = get_modified_by(conflict.remote_modified_by)
        #if "modified_by" in local_record:
            #local_modified_by = get_modified_by(local_record.modified_by.email)

    #if "form_action" in request.vars:
        #if request.vars["form_action"] == "resolve" and conflict:
            #if local_record:
                ## update local record
                #for field in remote_record:
                    #if (not field in skip_fields) and (field in db[conflict.resource_table].fields):
                        #if "final_"+str(field) in request.vars:
                            #vals = {field: request.vars["final_" + str(field)]}
                        #else:
                            #if db[conflict.resource_table][field].type == "boolean":
                                #vals = {field: "False"}
                            #else:
                                #vals = {field: ""}

                        #field_error = db[conflict.resource_table][field].validate(vals[field])[1]
                        #if field_error:
                            #field_errors[field] = field_error
                        ## update only if no errors
                        #if len(field_errors) == 0:
                            #db(db[conflict.resource_table].uuid==conflict.uuid).update(**vals)
                            ## undelete record
                            #if "deleted" in db[conflict.resource_table].fields:
                                #vals = {"deleted": False}
                                #db(db[conflict.resource_table].uuid==conflict.uuid).update(**vals)
            #else:
                ## insert record
                #new_rec = dict()
                #for field in remote_record:
                    #if field in table_conflict.fields:
                        #if "final_"+field in request.vars:
                            #new_rec[field] = request.vars["final_"+field]
                        #else:
                            #new_rec[field] = remote_record[field]
                        #field_error = db[conflict.resource_table][field].validate(vals[field])[1]
                        #if field_error:
                            #field_errors[field] = field_error
                ## insert only if no errors
                #if len(field_errors) == 0:
                    #db[conflict.resource_table].insert(**new_rec)

            ## set status to resolved if no errors
            #if len(field_errors) == 0:
                #conflict.update_record(resolved = True)
            ## next conflict
            #conflicts = db(table_conflict.resolved==False).select(table_conflict.ALL, orderby=table_conflict.logged_on)
            #for idx in xrange(0, len(conflicts)):
                #if not conflicts[idx].resource_table in db.tables:
                    #del conflicts[idx]
            #total_conflicts = len(conflicts)
            #if record_nbr < 1 or record_nbr > total_conflicts:
                #record_nbr = 1
            #if total_conflicts == 0:
                #conflict = None
            #else:
                #conflict = conflicts[record_nbr - 1]
            #remote_record = None
            #local_record = None
            #if conflict:
                #remote_record = cPickle.loads(conflict.remote_record)
                #local_record = db(db[conflict.resource_table].uuid==conflict.uuid).select().first()
                #if conflict.remote_modified_by:
                    #remote_modified_by = get_modified_by(conflict.remote_modified_by)
                #if "modified_by" in local_record:
                    #local_modified_by = get_modified_by(local_record.modified_by.email)

    #form = None
    #if conflict:
        #form = SQLFORM.factory(db[conflict.resource_table])

    #return dict(title=title,
                #skip_fields=skip_fields,
                #total_conflicts=total_conflicts,
                #conflict=conflict,
                #record_nbr=record_nbr,
                #local_record=local_record,
                #remote_record=remote_record,
                #local_modified_by=local_modified_by,
                #remote_modified_by=remote_modified_by,
                #form=form,
                #field_errors=field_errors)

# -----------------------------------------------------------------------------
def sync_cron():

    """ Run all due jobs from the schedule """

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
def sync_run_job(job, settings=None, pid=None, tables=[], silent=False):

    """ Run synchronization job """

    import gluon.contrib.simplejson as json

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

    result = None

    # Get the peer
    if peer:

        notify("Processing job %s..." % job.id)

        job_policy = job.policy or peer.policy
        s3xrc.sync_resolve = lambda vector, peer=peer, policy=policy: \
                                    sync_res(vector, peer, policy)

        # Find resources to sync
        tablenames = [n.strip().lower() for n in tables]

        # Synchronize all tables
        if job.type == 1:
            result = s3_sync_eden_eden(peer, mode, tablenames,
                                       settings=settings,
                                       pid=pid,
                                       last_sync=last_sync_on,
                                       complete_sync=complete)
        else:
            result = s3_sync_eden_other(peer, mode, tablenames,
                                        pid=pid,
                                        settings=settings)

        if result:
            db.sync_log.insert(
                peer_id = peer.id,
                timestmp = datetime.datetime.now(),
                resources = ", ".join(result.done),
                errors = ", ".join(result.errors),
                mode = job.mode,
                run_interval = job.run_interval,
                complete = job.complete
            )

    return result


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

    # Ignore errors?
    ignore_errors = peer.ignore_errors

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
        resource = s3xrc.resource(prefix, name)

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

    # Ignore errors?
    ignore_errors = peer.ignore_errors

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
#
def sync_rheader(r, tabs=[]):

    if r.representation == "html":

        _next = r.here()
        _same = r.same()

        if tabs:
            rheader_tabs = shn_rheader_tabs(r, tabs)
        else:
            rheader_tabs = ""

        if r.name == "peer":

            peer = r.record
            if peer:
                rheader = DIV(TABLE(

                    TR(TH(T("Name") + ": "),
                       peer.name,
                       TH(""),
                       ""),

                    TR(TH(T("Type") + ": "),
                       sync_peer_types.get(peer.type, UNKNOWN_OPT),
                       TH(""),
                       ""),

                    TR(TH("URL: "),
                       peer.url,
                       TH(""),
                       "")),

                    rheader_tabs)

                return rheader

    return None

# -----------------------------------------------------------------------------
