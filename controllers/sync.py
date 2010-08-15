# -*- coding: utf-8 -*-

"""
    Synchronisation - Controllers
"""

module = "admin"
module_name = T("Synchronization")

log_table = "sync_log"
conflict_table = "sync_conflict"
sync_peer = None

# Options Menu (available in all Functions' Views)
# - can Insert/Delete items from default menus within a function, if required.
response.menu_options = admin_menu_options

# Web2Py Tools functions
def call():
    "Call an XMLRPC, JSONRPC or RSS service"
    # Sync webservices don't use sessions, so avoid cluttering up the storage
    session.forget()
    return service()

# S3 framework functions
def index():
    "Module's Home Page"
    
    return dict(module_name=module_name)

import urllib2

class RequestWithMethod(urllib2.Request):
    def __init__(self, method, *args, **kwargs):
        self._method = method
        urllib2.Request.__init__(self, *args, **kwargs)
    def get_method(self):
        return self._method

class Error:
    # indicates an HTTP error
    def __init__(self, url, errcode, errmsg, headers, body=None):
        self.url = url
        self.errcode = errcode
        self.errmsg = errmsg
        self.headers = headers
        self.body = body
    def __repr__(self):
        return (
            "Error for %s: %s %s\n Response body: %s" %
            (self.url, self.errcode, self.errmsg, self.body)
            )

class FetchURL:
    def fetch(self, request, host, path, data, cookie=None, username=None, password=None):
        import httplib, base64
        http = httplib.HTTPConnection(host)
        # write header
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        if cookie:
            headers["Cookie"] = cookie
        # auth
        if username:
            base64string =  base64.encodestring("%s:%s" % (username, password))[:-1]
            authheader =  "Basic %s" % base64string
            headers["Authorization"] = authheader
        http.request(request, path, data, headers)
        # get response
        response = http.getresponse()
        retcode = response.status
        retmsg = response.reason
        retbody = None
        if retcode != 200:
            try:
                retbody = response.read()
            except:
                retbody = None
            raise Error(str(host) + str(path), retcode, retmsg, headers, retbody)
        return response.read()

@auth.requires_login()
def now():
    "Manual syncing"

    import urllib, urlparse

    final_status = ""
    sync_start = False

    if "start" in request.args:
        sync_start = True

    # retrieve sync now state
    states = db().select(db.sync_now.ALL)
    state = None
    if states:
        state = states[0]

    if sync_start:
        # retrieve sync partners from DB
        peers = db().select(db.sync_partner.ALL)

        # retrieve settings
        settings = db().select(db.sync_setting.ALL)[0]

        # url fetcher
        fetcher = FetchURL()

        # for eden instances
        final_status = ""
        modules = deployment_settings.modules
        _db_tables = db.tables
        db_tables = []
        for __table in _db_tables:
            if "modified_on" in db[__table].fields and "uuid" in db[__table].fields:
                db_tables.append(__table)
        tables = []
        for _module in modules:
            for _table in db_tables:
                if _table.startswith(_module + "_"):
                    tables.append([_module, _table[len(_module)+1:]])

    #    self_instance_url = db().select(db.sync_setting.instance_url)[0].instance_url
    #    if not self_instance_url:
    #        final_status = "Please specify Instance URL in Sync Settings before proceeding with Sync, your instance URL is the root URL of Sahana Eden application, similar to http://demo.eden.sahanafoundation.org/eden/.<br /><br /><a href=\"" + URL(r=request, c="sync", f="setting/1/update") + "\">Click here</a> to go to Sync Settings.<br /><br />\n"
    #        return dict(module_name=module_name, sync_status=final_status, sync_start=False)

        if len(peers) < 1:
            final_status = "There are no sync partners. Please add peers (Sync Partners) to sync with.<br /><br /><a href=\"" + URL(r=request, c="sync", f="partner") + "\">Click here</a> to go to Sync Partners page.<br /><br />\n"
            return dict(module_name=module_name, sync_status=final_status, sync_start=False)

        if not state:
            # begin new sync now session
            sync_now_id = db["sync_now"].insert(
                sync_jobs = ", ".join(map(lambda x: str(x.uuid) + "||" + str(x.name), peers)),
                started_on = datetime.datetime.utcnow(),
                job_resources_done = "",
                job_resources_pending = ", ".join(map(lambda x: str(x[0]) + "||" + str(x[1]), tables)),
                job_sync_errors = ""
            )
            state = db(db.sync_now.id==sync_now_id).select(db.sync_now.ALL)[0]
            final_status += "Sync Now started:<br /><br /><br />\n"
        else:
            sync_now_id = state.id
            final_status += "Sync Now resumed (originally started on " + state.started_on.strftime("%x %H:%M:%S")+ "):<br /><br /><br />\n"

        # unlock session
        +133
        session._unlock(response)

        # get job (peer in this case) from queue
        sync_jobs_list = state.sync_jobs.split(", ")
        if "" in sync_jobs_list:
            sync_jobs_list.remove("")
        sync_job = sync_jobs_list[0]
        sync_job_partner = sync_job.split("||")
        peers_sel = db(db.sync_partner.uuid==sync_job_partner[0] and db.sync_partner.name==sync_job_partner[1]).select()
        if peers_sel:
            peer = peers_sel[0]

        # Whether a push was successful => means Push + Pull Sync was performed
        push_success = False
        if peer:
            final_status += "<br />Syncing with: " + peer.name + ", " + peer.instance_url + " (" + peer.instance_type + "):<br />\n\n"
            peer_sync_success = True
            last_sync_on = peer.last_sync_on
            sync_resources = []
            sync_errors = ""
            if peer.instance_type == "Sahana Eden":
                if not last_sync_on is None:
                    last_sync_on_str = "?msince=" + last_sync_on.strftime("%Y-%m-%dT%H:%M:%SZ")
                else:
                    last_sync_on_str = ""
                job_res_tmp = state.job_resources_pending.split(", ")
                if "" in job_res_tmp:
                    job_res_tmp.remove("")
                job_res_list = []
                for i in xrange(5):
                    if len(job_res_tmp) > 0 and i < len(job_res_tmp):
                        job_res = job_res_tmp[i].split("||")
                        job_res_list.append([job_res[0], job_res[1]])
                for _module, _resource in job_res_list:
                    _resource_name = _module + "_" + _resource
#                    if not (_module == "budget" and _resource == "item"):
#                        continue
                    peer_instance_url = list(urlparse.urlparse(peer.instance_url))
                    if peer_instance_url[2].endswith("/")==False:
                        peer_instance_url[2] += "/"
                    resource_remote_pull_url = peer.instance_url
                    if resource_remote_pull_url.endswith("/")==False:
                        resource_remote_pull_url += "/"
                    resource_remote_pull_url += "sync/sync.json/" + _module + "/" + _resource + last_sync_on_str
                    resource_remote_push_url = peer_instance_url[2] + "sync/sync.json/push/" + _module + "/" + _resource + "?sync_partner_uuid=" + str(settings.uuid)
                    resource_local_pull_url = "/" + request.application + "/sync/sync.json/" + _module + "/" + _resource + last_sync_on_str
                    resource_local_push_url = "/" + request.application + "/sync/sync.json/create/" + _module + "/" + _resource
                    final_status += "......processing " + resource_remote_pull_url + "<br />\n"
                    # Sync this resource, try Pull and Push
                    _request_params = urllib.urlencode({"sync_partner_uuid": str(peer.uuid), "fetchurl": resource_remote_pull_url})
                    # Keep Session for local URLs
                    cookie = str(response.session_id_name) + "=" + str(response.session_id)
                    # Sync -> Pull
                    try:
                        #_request = RequestWithMethod("PUT", "http://" + str(request.env.http_host) + resource_local_push_url, _request_params)
                        #_response = urllib2.urlopen(_request).read()
                        _response = fetcher.fetch("PUT", request.env.http_host, resource_local_push_url, _request_params, cookie)
                    except Error, e:
                        if not _resource_name + " (error)" in sync_resources and not _resource_name in sync_resources:
                            sync_resources.append(_resource_name + " (error)")
                        #final_status += "ERROR while processing: http://" +  + str(request.env.http_host) + resource_local_push_url + "<br />\n"
                        error_str = str(e)
                        sync_errors +=  "Error while syncing => " + _resource_name + ": \n" + error_str + "\n\n"
                        final_status += error_str + "<br /><br />\n"
                    else:
                        if not _resource_name + " (error)" in sync_resources and not _resource_name in sync_resources:
                            sync_resources.append(_resource_name)
                        final_status += ".........processed http://" + str(request.env.http_host) + resource_local_push_url + " (Pull Sync)<br />\n"
                    # Sync -> Push
                    try:
                        _local_data = fetcher.fetch("GET", request.env.http_host, resource_local_pull_url, None, cookie)
                        _response = fetcher.fetch("PUT", peer_instance_url[1], resource_remote_push_url, _local_data, None, peer.username, peer.password)
                    except Error, e:
                        if not _resource_name + " (error)" in sync_resources and not _resource_name in sync_resources:
                            sync_resources.append(_resource_name + " (error)")
                        error_str = str(e)
                        sync_errors +=  "Error while syncing => " + _resource_name + ": \n" + error_str + "\n\n"
                        final_status += error_str + "<br /><br />\n"
                    else:
                        if not _resource_name + " (error)" in sync_resources and not _resource_name in sync_resources:
                            sync_resources.append(_resource_name)
                        final_status += ".........processed http://" + peer_instance_url[1] + resource_remote_push_url + " (Push Sync)<br />\n"
#                final_status += "......completed<br />\n"
            else:
                peer_sync_success = False

#            if len(sync_resources) == 0:
#                peer_sync_success = False

            # update sync now state
            if state.job_resources_done:
                state.job_resources_done += ", "
            state.job_resources_done += ", ".join(map(str, sync_resources))
            job_res_pending = state.job_resources_pending.split(", ")
            if "" in job_res_pending:
                job_res_pending.remove("")
            for _module, _resource in job_res_list:
                job_res_pending.remove(_module + "||" + _resource)
            state.job_resources_pending = ", ".join(map(str, job_res_pending))
            state.job_sync_errors += sync_errors
            vals = {"job_resources_done": state.job_resources_done, "job_resources_pending": state.job_resources_pending, "job_sync_errors": state.job_sync_errors}
            db(db.sync_now.id == sync_now_id).update(**vals)
            state = db(db.sync_now.id == sync_now_id).select(db.sync_now.ALL)[0]

            # check if all resources are synced for the current job, i.e. is it done?
            if not state.job_resources_pending:
                # job completed, check if there are any more jobs, if not, then sync now completed
                # log sync job
                log_table_id = db[log_table].insert(
                    partner_uuid = sync_job_partner[0],
                    partner_name = sync_job_partner[1],
                    timestmp = datetime.datetime.utcnow(),
                    sync_resources = state.job_resources_done,
                    sync_errors = state.job_sync_errors,
                    sync_mode = "online",
                    sync_method = "Pull-Push",
                    complete_sync = False
                )
                # remove this job from queue and process next
                sync_jobs_list = state.sync_jobs.split(", ")
                if "" in sync_jobs_list:
                    sync_jobs_list.remove("")
                if len(sync_jobs_list) > 0:
                    sync_jobs_list.remove(sync_jobs_list[0])
                    state.sync_jobs = ", ".join(map(str, sync_jobs_list))
                    vals = {"sync_jobs": state.sync_jobs}
                    db(db.sync_now.id == sync_now_id).update(**vals)
                    state = db(db.sync_now.id == sync_now_id).select(db.sync_now.ALL)[0]
                # update last_sync_on
                vals = {"last_sync_on": datetime.datetime.utcnow()}
                db(db.sync_partner.id == peer.id).update(**vals)

            if not state.sync_jobs:
                # remove sync now session state
                db(db.sync_now.id == sync_now_id).delete()
                # we're done
                final_status += "Sync completed successfully. Logs generated: " + str(A(T("Click here to open log"),_href=URL(r=request, c="sync", f="history"))) + "<br /><br />\n"
    
    return dict(module_name=module_name, sync_status=final_status, sync_start=sync_start, sync_state=state)

def sync():
    global sync_peer
    import gluon.contrib.simplejson as json

    if len(request.args) == 3:
        _function, _module, _resource = tuple(request.args)
        if _function.startswith("list"):
            request.args = []
        else:
            request.args = [_function]
    elif len(request.args) == 2:
        _module, _resource = tuple(request.args)
        _function = "list"
        request.args = []
    else:
        return T("Not supported")

    sync_peer = None
    if "sync_partner_uuid" in request.vars:
        sync_peer = db(db.sync_partner.uuid == request.vars["sync_partner_uuid"]).select()[0]

    # remote push?
    remote_push = False
    if _function == "push":
        remote_push = True
        request.args = ["create"]
        _function = "create"

    if _function == "create" and not sync_peer:
        return T("Invalid Request")

    if _function in ["list", "create"]:
        s3xrc.sync_resolve = sync_res
        ret_data = shn_rest_controller(module=_module, resource=_resource, push_limit=None)
        if remote_push:
                sync_resources = _module + "_" + _resource
                sync_errors = ""
                ret_json = json.loads(ret_data["item"])
                if str(ret_json["statuscode"]) != "200":
                    sync_resources += " (error)"
                    sync_errors = str(ret_data["item"])
                # log sync remote push
                log_table_id = db[log_table].insert(
                    partner_uuid = sync_peer.uuid,
                    partner_name = sync_peer.name,
                    timestmp = datetime.datetime.utcnow(),
                    sync_resources = sync_resources,
                    sync_errors = sync_errors,
                    sync_mode = "online",
                    sync_method = "Remote Push",
                    complete_sync = False
                )
        return ret_data
    else:
        return T("Not supported")
    
    return dict()

def sync_res(vector):
    import cPickle
    global sync_peer
    db_record = vector.db(vector.table.id==vector.id).select(vector.table.ALL, limitby=(0,1))
    db_record_mtime = None
    record_dump = cPickle.dumps(dict(vector.record), 0)
    if db_record:
        db_record = db_record.first()
        if "modified_on" in vector.table.fields:
            db_record_mtime = db_record.modified_on
    # based on the sync_policy, make resolution
    if sync_peer.policy == 0:    # No Sync
        # don't import anything in this case
        vector.strategy = []
    elif sync_peer.policy == 1:  # Keep Local
        vector.resolution = vector.RESOLUTION.THIS
        if db_record_mtime and vector.mtime > db_record_mtime:
            # log this as a conflict, local record is older
            #print "Conflict: local record is kept and is older"
            db[conflict_table].insert(
                uuid = vector.record.uuid,
                resource_table = vector.tablename,
                remote_record = record_dump,
                remote_modified_by = vector.element.get("modified_by"),
                remote_modified_on = vector.mtime,
                logged_on = datetime.datetime.utcnow(),
                resolved = False
            )
    elif sync_peer.policy == 2:  # Replace with Remote
        vector.resolution = vector.RESOLUTION.OTHER
        if db_record_mtime and vector.mtime < db_record_mtime:
            # log this as a conflict, remote record is older
            #print "Conflict: remote record is imported and is older"
            db[conflict_table].insert(
                uuid = vector.record.uuid,
                resource_table = vector.tablename,
                remote_record = record_dump,
                remote_modified_by = vector.element.get("modified_by"),
                remote_modified_on = vector.mtime,
                logged_on = datetime.datetime.utcnow(),
                resolved = False
            )
        elif db_record_mtime and sync_peer.last_sync_on and db_record_mtime > sync_peer.last_sync_on:
            # log this as a conflict, local record was modified too, but overwritten
            #print "Conflict: local record was modified since last sync but overwritten by remote record"
            db[conflict_table].insert(
                uuid = vector.record.uuid,
                resource_table = vector.tablename,
                remote_record = record_dump,
                remote_modified_by = vector.element.get("modified_by"),
                remote_modified_on = vector.mtime,
                logged_on = datetime.datetime.utcnow(),
                resolved = False
            )
    elif sync_peer.policy == 3:  # Keep with Newer Timestamp
        vector.resolution = vector.RESOLUTION.NEWER
        if db_record_mtime and vector.mtime < db_record_mtime:
            # log this as a conflict, remote record is older
            #print "Conflict: remote record is imported and is older"
            db[conflict_table].insert(
                uuid = vector.record.uuid,
                resource_table = vector.tablename,
                remote_record = record_dump,
                remote_modified_by = vector.element.get("modified_by"),
                remote_modified_on = vector.mtime,
                logged_on = datetime.datetime.utcnow(),
                resolved = False
            )
    elif sync_peer.policy == 4:  # Role-based
        # not implemented, defaulting to "Newer Timestamp"
        vector.resolution = vector.RESOLUTION.NEWER
    elif sync_peer.policy == 5:  # Choose Manually
        if db_record_mtime and vector.mtime != db_record_mtime:
            # just log and skip
            vector.strategy = []
            db[conflict_table].insert(
                uuid = vector.record.uuid,
                resource_table = vector.tablename,
                remote_record = record_dump,
                remote_modified_by = vector.element.get("modified_by"),
                remote_modified_on = vector.mtime,
                logged_on = datetime.datetime.utcnow(),
                resolved = False
            )
    return

@auth.shn_requires_membership(1)
def partner():
    "Synchronisation Partners"
    db.sync_partner.uuid.label = "UUID"
    db.sync_partner.uuid.comment = DIV(SPAN("*", _class="req"), DIV(_class="tooltip",
        _title="UUID|" + Tstr("The unique identifier of the sync partner. Enter 0 for non-Eden instances.")))
    db.sync_partner.name.label = T("Name")
    db.sync_partner.name.comment = DIV(_class="tooltip",
        _title=Tstr("Name") + "|" + Tstr("The descriptive name of the sync partner."))
    db.sync_partner.instance_url.label = T("Instance URL")
    db.sync_partner.instance_url.comment = DIV(SPAN("*", _class="req"), DIV(_class="tooltip",
        _title=Tstr("Instance URL") + "|" + Tstr("For Eden instances - this is the application URL, e.g. http://sync.sahanfoundation.org/eden. For non-Eden instances, this is the Full ")))
    db.sync_partner.instance_type.label = T("Instance Type")
    db.sync_partner.instance_type.comment = DIV(SPAN("*", _class="req"), DIV(_class="tooltip",
        _title=Tstr("Instance Type") + "|" + Tstr("Whether this is a Sahana Eden, Sahana Agasti, Ushahidi or Other instance.")))
    db.sync_partner.username.label = T("Sync Username")
    db.sync_partner.username.comment = DIV(_class="tooltip",
        _title=Tstr("Sync Username") + "|" + Tstr("Username used to login when synchronising with this partner. Note that only HTTP Basic authentication is supported."))
    db.sync_partner.password.label = T("Sync Password")
    db.sync_partner.password.comment = DIV(_class="tooltip",
        _title=Tstr("Sync Password") + "|" + Tstr("Password used to login when synchronising with this partner. Note that only HTTP Basic authentication is supported."))
    db.sync_partner.comments.label = T("Comments")
    db.sync_partner.comments.comment = DIV(_class="tooltip",
        _title=Tstr("Comments") + "|" + Tstr("Any comments about this sync partner."))
    db.sync_partner.policy.label = T("Sync Policy")
    db.sync_partner.policy.comment = DIV(SPAN("*", _class="req"), DIV(_class="tooltip",
        _title=Tstr("Sync Policy") + "|" + Tstr("The policy to use while synchronising with this partner. All policies other than 'No Sync' come into effect when conflicts arise.")))
    db.sync_partner.sync_pools.readable = False
    db.sync_partner.sync_pools.writable = False
    db.sync_partner.password.readable = False
    db.sync_partner.last_sync_on.writable = False
    title_create = T("Add Partner")
    title_display = T("Partner Details")
    title_list = T("List Partners")
    title_update = T("Edit Partner")
    title_search = T("Search Partners")
    subtitle_create = T("Add New Partner")
    subtitle_list = T("Partners")
    label_list_button = T("List Partners")
    label_create_button = T("Add Partner")
    label_search_button = T("Search Partners")
    msg_record_created = T("Partner added")
    msg_record_modified = T("Partner updated")
    msg_record_deleted = T("Partner deleted")
    msg_list_empty = T("No Partners currently registered")
    s3.crud_strings.sync_partner = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
    return shn_rest_controller("sync", "partner")

@auth.shn_requires_membership(1)
def setting():
    "Synchronisation Settings"
    if not "update" in request.args:
        redirect(URL(r=request, args=["update", 1]))
    db.sync_setting.uuid.writable = False
    db.sync_setting.uuid.label = "UUID"
    db.sync_setting.uuid.comment = DIV(_class="tooltip",
        _title="UUID|" + Tstr("The unique identifier which identifies this instance to other instances."))
    db.sync_setting.comments.label = T("Comments")
    db.sync_setting.comments.comment = DIV(_class="tooltip",
        _title=Tstr("Comments") + "|" + Tstr("Any comments for this instance."))
#    db.sync_setting.beacon_service_url.label = T("Beacon Service URL")
#    db.sync_setting.beacon_service_url.comment = DIV(_class="tooltip",
#        _title=Tstr("Beacon Service URL") + "|" + Tstr("Beacon service allows searching for other instances that wish to synchronise. This is the URL of the beacon service this instance will use."))
    db.sync_setting.sync_pools.readable = False
    db.sync_setting.sync_pools.writable = False
    db.sync_setting.beacon_service_url.readable = False
    db.sync_setting.beacon_service_url.writable = False
    title_update = T("Edit Sync Settings")
    label_list_button = T("Sync Settings")
    msg_record_modified = T("Sync Settings updated")
    s3.crud_strings.sync_setting = Storage(title_update=title_update,label_list_button=label_list_button,msg_record_modified=msg_record_modified)
    crud.settings.update_next = URL(r=request, args=["update", 1])
    return shn_rest_controller("sync", "setting", deletable=False, listadd=False)

@auth.shn_requires_membership(1)
def schedule():
    "Synchronisation Schedules"
    import gluon.contrib.simplejson as json
    title = T("Syncronisation Schedules")

    jobs = None
    if "create" in request.args:
        response.view = "sync/schedule_create.html"

        if "form_action" in request.vars and request.vars["form_action"] == "submit":
            # create new job - add it to database
            print request.vars
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
            if "days_of_week" in request.vars and request.vars["days_of_week"]:
                sch_days_of_week = map(lambda x: x-1, request.vars["days_of_week"])
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
                else:
                    sch_cmd["resources"] = None
                sch_cmd["complete"] = False
                if "sync_complete" in request.vars and request.vars["sync_complete"] == "1":
                    sch_cmd["complete"] = True
                sch_cmd["mode"] = False
                if "sync_mode" in request.vars and request.vars["sync_mode"]:
                    sch_cmd["mode"] = int(request.vars["sync_mode"])
            else:
                # custom data source
                sch_job_type = 2
                sch_cmd["custom_command"] = request.vars["sync_custom"]

            db["sync_schedule"].insert(
                    comments = sch_comments,
                    period = sch_period,
                    hours = sch_period_hours,
                    days_of_week = ", ".join(map(str, sch_days_of_week)),
                    time_of_day = sch_time_of_day,
                    runonce_datetime = sch_runonce_datetime,
                    job_type = sch_job_type,
                    job_command = json.dumps(sch_cmd),
                    running = False,
                    last_run = None,
                    enabled = sch_enabled
                )

    else:
        jobs = db().select(db.sync_schedule.ALL)

    return dict(title=title, jobs=jobs)

@auth.requires_login()
def history():
    "Shows history of database synchronisations"
    title = T("Synchronisation History")
    if len(request.args) > 0:
        logs = db(db[log_table].id == int(request.args[0])).select(db[log_table].ALL, orderby=db[log_table].timestmp)
    else:
        logs = db().select(db[log_table].ALL, orderby=db[log_table].timestmp)
    return dict(title=title, logs=logs)

@auth.shn_requires_membership(1)
def conflict():
    "Conflict Resolution UI"
    import cPickle
    title = T("Conflict Resolution")

    def get_modified_by(user_email):
        modified_by = user_email
        user = db(db.auth_user.email == user_email).select().first()
        if user:
            modified_by  = user.first_name
            if user.last_name:
                modified_by += " " + user.last_name
        return modified_by

    skip_fields = ["uuid", "id"]
    field_errors = dict()

    conflicts = db(db[conflict_table].resolved == False).select(db[conflict_table].ALL, orderby=db[conflict_table].logged_on)
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
        local_record = db(db[conflict.resource_table].uuid == conflict.uuid).select().first()
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
                            db(db[conflict.resource_table].uuid == conflict.uuid).update(**vals)
                            # undelete record
                            if "deleted" in db[conflict.resource_table].fields:
                                vals = {"deleted": False}
                                db(db[conflict.resource_table].uuid == conflict.uuid).update(**vals)
            else:
                # insert record
                new_rec = dict()
                for field in remote_record:
                    if field in db[conflict_table].fields:
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
            conflicts = db(db[conflict_table].resolved == False).select(db[conflict_table].ALL, orderby=db[conflict_table].logged_on)
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
                local_record = db(db[conflict.resource_table].uuid == conflict.uuid).select().first()
                if conflict.remote_modified_by:
                    remote_modified_by = get_modified_by(conflict.remote_modified_by)
                if "modified_by" in local_record:
                    local_modified_by = get_modified_by(local_record.modified_by.email)

    form = None
    if conflict:
        form = SQLFORM.factory(db[conflict.resource_table])
    return dict(title=title, skip_fields=skip_fields, total_conflicts=total_conflicts, conflict=conflict, record_nbr=record_nbr, local_record=local_record, remote_record=remote_record, local_modified_by=local_modified_by, remote_modified_by=remote_modified_by, form=form, field_errors=field_errors)
