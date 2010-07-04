# -*- coding: utf-8 -*-

"""
    Synchronisation - Controllers
"""

module = "admin"
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
    
    module_name = "Synchronisation"
    
    return dict(module_name=module_name)

import urllib2

class RequestWithMethod(urllib2.Request):
    def __init__(self, method, *args, **kwargs):
        self._method = method
        urllib2.Request.__init__(self, *args, **kwargs)
    def get_method(self):
        return self._method

@auth.requires_login()
def now():
    "Manual syncing"

    module_name = "Synchronisation"
    final_status = ""

    # retrieve sync partners from DB
    peers = db().select(db.sync_partner.ALL)

    # retrieve settings (to get username and password for login)
    settings = db().select(db.sync_setting.ALL)[0]

    if not (settings.username or settings.password):
        final_status = "Please specify Username and Password in Sync Settings before proceeding with Sync, this Username and Password must belong to a user account that is capable of modifying records (in database), usually an Administrator.<br /><br /><a href=\"" + URL(r=request, c="sync", f="setting/1/update") + "\">Click here</a> to go to Sync Settings.<br /><br />\n"
        return dict(module_name=module_name, sync_status=final_status)

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

    self_instance_url = db().select(db.sync_setting.instance_url)[0].instance_url
    if not self_instance_url:
        final_status = "Please specify Instance URL in Sync Settings before proceeding with Sync, your instance URL is the root URL of SahanaEden application, similar to http://demo.eden.sahanafoundation.org/eden/.<br /><br /><a href=\"" + URL(r=request, c="sync", f="setting/1/update") + "\">Click here</a> to go to Sync Settings.<br /><br />\n"
        return dict(module_name=module_name, sync_status=final_status)
    
    _base_url = s3xrc.base_url
    if _base_url.endswith("/")==False:
        _base_url += "/"

    if len(peers) < 1:
        final_status = "There are no sync partners. Please add peers (Sync Partners) to sync with.<br /><br /><a href=\"" + URL(r=request, c="sync", f="partner") + "\">Click here</a> to go to Sync Partners page.<br /><br />\n"
        return dict(module_name=module_name, sync_status=final_status)
    
    for peer in peers:
        final_status += "<br />Begin sync with: " + peer.uuid + ", " + peer.instance_url + " (" + peer.instance_type + "):<br />\n\n"
        peer_sync_success = True
        last_sync_on = peer.last_sync_on
        tables_success = ""
        tables_error = ""
        if peer.instance_type == "SahanaEden":
            if not last_sync_on is None:
                last_sync_on_str = "?msince=" + last_sync_on.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                last_sync_on_str = ""
            for _module, _resource in tables:
#                if not (_module == "pr" and _resource == "person"):
#                    continue
                resource_url = peer.instance_url
                if resource_url.endswith("/")==False:
                    resource_url += "/"
                resource_url += "sync/sync.xml/" + _module + "/" + _resource + last_sync_on_str
                final_status += "......processing " + resource_url + "<br />\n"
                # sync this resource (Pull => fetch and sync)
                resource_sync_url = _base_url + "sync/sync.xml/create/" + _module + "/" + _resource
                import urllib, urllib2
                _request_params = urllib.urlencode({"sync_partner_uuid": str(peer.uuid), "fetchurl": resource_url, "sync_username": settings.username, "sync_password": settings.password})
                try:
                    _request = RequestWithMethod("PUT", resource_sync_url, _request_params)
                    _response = urllib2.urlopen(_request).read()
                except IOError, e:
                    if tables_error:
                        tables_error += ", "
                    tables_error += _module + "_" + _resource
                    final_status += "ERROR while processing: " + resource_sync_url + "<br />\n"
                    error_str = str(e).replace("<", "&lt;").replace(">", "&gt;")
                    final_status += "ERROR: " + error_str + "<br /><br />\n"
                else:
                    if tables_success:
                        tables_success += ", "
                    tables_success += _module + "_" + _resource
                    final_status += ".........processed " + resource_sync_url + "<br />\n"
            final_status += "......completed<br /><br />\n"
        else:
            peer_sync_success = False

        if tables_success == "":
            peer_sync_success = False

        # log sync job and update sync partner's last_sync_on
        if peer_sync_success:
            # log sync job
            db[log_table].insert(
                uuid = peer.uuid,
                timestamp = datetime.datetime.utcnow(),
                sync_tables_success = tables_success,
                sync_tables_error = tables_error,
                sync_mode = "online",
                complete_sync = False
            )
            # update last_sync_on
            vals = {"last_sync_on": datetime.datetime.utcnow()}
            db(db.sync_partner.id==peer.id).update(**vals)

    final_status += "Sync completed sucessfully."
    
    return dict(module_name=module_name, sync_status=final_status)

def sync():
    global sync_peer

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

    user = None
    if "sync_username" in request.vars and "sync_password" in request.vars:
        user = auth.login_bare(request.vars["sync_username"], request.vars["sync_password"])

    sync_peer = None
    if "sync_partner_uuid" in request.vars:
        sync_peer = db(db.sync_partner.uuid == request.vars["sync_partner_uuid"]).select()[0]

    if _function == "create" and not user:
        return T("Access Denied")

    if _function == "list" or _function == "create":
        s3xrc.sync_resolve = sync_res
        return shn_rest_controller(module=_module, resource=_resource)
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
    #db.sync_partner.password.readable = False
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
    db.sync_setting.uuid.writable = False
    db.sync_setting.uuid.label = "UUID"
    db.sync_setting.uuid.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("UUID|The unique identifier which identifies this server to other instances."))
    title_update = T("Edit Sync Settings")
    label_list_button = None
    msg_record_modified = T("Sync Settings updated")
    s3.crud_strings.sync_setting = Storage(title_update=title_update,label_list_button=label_list_button,msg_record_modified=msg_record_modified)
    crud.settings.update_next = URL(r=request, args=["update", 1])
    return shn_rest_controller("sync", "setting", deletable=False, listadd=False)

@auth.shn_requires_membership(1)
def schedule():
    "Synchronisation Schedules"
    title = T("Syncronisation Schedules")

    if "create" in request.args:
        return shn_rest_controller("sync", "schedule")

    jobs = db().select(db.sync_schedule.ALL)

    return dict(title=title, jobs=jobs)

@auth.requires_login()
def history():
    "Shows history of database synchronisations"
    title = T("Synchronisation History")
    logs = db().select(db[log_table].ALL, orderby=db[log_table].timestamp)
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

    conflicts = db(db[conflict_table].resolved==False).select(db[conflict_table].ALL, orderby=db[conflict_table].logged_on)
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
            conflicts = db(db[conflict_table].resolved==False).select(db[conflict_table].ALL, orderby=db[conflict_table].logged_on)
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
    return dict(title=title, skip_fields=skip_fields, total_conflicts=total_conflicts, conflict=conflict, record_nbr=record_nbr, local_record=local_record, remote_record=remote_record, local_modified_by=local_modified_by, remote_modified_by=remote_modified_by, form=form, field_errors=field_errors)
