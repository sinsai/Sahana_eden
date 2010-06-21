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
    
    module_name = s3.modules[module]["name_nice"]
    
    return dict(module_name=module_name)

@auth.requires_login()
def now():
    "Manual syncing"
    
    module_name = "Synchronisation"
    final_status = ""
    
    # retrieve sync partners from DB
    peers = db().select(db.sync_partner.ALL)
    
    # for eden instances
    final_status = ""
    modules = s3.modules
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
                resource_sync_url = _base_url + "sync/sync.xml/create/" + _module + "/" + _resource + "?sync_partner_uuid=" + str(peer.uuid) + "&fetchurl=" + resource_url
                import urllib2
                auth_cookie_name = "session_id_" + request.application
                _request_headers = dict(Cookie = request.cookies[auth_cookie_name].key + "=" + request.cookies[auth_cookie_name].value)
                try:
                    _request = urllib2.Request(resource_sync_url, None, _request_headers)
                    _response = urllib2.urlopen(_request).read()
                except IOError, e:
                    if tables_error:
                        tables_error += ", "
                    tables_error += _module + "_" + _resource
                    final_status += "\n<br />ERROR while processing: " + resource_sync_url + "<br />\n"
                else:
                    if tables_success:
                        tables_success += ", "
                    tables_success += _module + "_" + _resource
                    final_status += ".........processed " + resource_sync_url + "<br />\n"
            final_status += "......completed<br /><br />\n"
        else:
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

def sync_auth():
    def decorator(action):
        def f(*a, **b):
            if auth.environment.request.raw_args and "create/" in auth.environment.request.raw_args:
                if not auth.basic() and not auth.is_logged_in():
                    request = auth.environment.request
                    next = URL(r=request,args=request.args,
                               vars=request.get_vars)
                    redirect(auth.settings.login_url + "?_next="+urllib.quote(next))
            return action(*a, **b)
        f.__doc__ = action.__doc__
        return f
    return decorator

@sync_auth()
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

    sync_peer = None
    if "sync_partner_uuid" in request.vars:
        sync_peer = db(db.sync_partner.uuid == request.vars["sync_partner_uuid"]).select()[0]

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
                remote_record = record_dump,
                remote_modified_by = vector.element.get("modified_by"),
                remote_modified_on = vector.mtime,
                resolved = False
            )
    elif sync_peer.policy == 2:  # Replace with Remote
        vector.resolution = vector.RESOLUTION.OTHER
        if db_record_mtime and vector.mtime < db_record_mtime:
            # log this as a conflict, remote record is older
            #print "Conflict: remote record is imported and is older"
            db[conflict_table].insert(
                uuid = vector.record.uuid,
                remote_record = record_dump,
                remote_modified_by = vector.element.get("modified_by"),
                remote_modified_on = vector.mtime,
                resolved = False
            )
        elif db_record_mtime and sync_peer.last_sync_on and db_record_mtime > sync_peer.last_sync_on:
            # log this as a conflict, local record was modified too, but overwritten
            #print "Conflict: local record was modified since last sync but overwritten by remote record"
            db[conflict_table].insert(
                uuid = vector.record.uuid,
                remote_record = record_dump,
                remote_modified_by = vector.element.get("modified_by"),
                remote_modified_on = vector.mtime,
                resolved = False
            )
    elif sync_peer.policy == 3:  # Keep with Newer Timestamp
        vector.resolution = vector.RESOLUTION.NEWER
        if db_record_mtime and vector.mtime < db_record_mtime:
            # log this as a conflict, remote record is older
            #print "Conflict: remote record is imported and is older"
            db[conflict_table].insert(
                uuid = vector.record.uuid,
                remote_record = record_dump,
                remote_modified_by = vector.element.get("modified_by"),
                remote_modified_on = vector.mtime,
                resolved = False
            )
    elif sync_peer.policy == 4:  # Role-based
        # not implemented, defaulting to "Newer Timestamp"
        vector.resolution = vector.RESOLUTION.NEWER
    elif sync_peer.policy == 5:  # Choose Manually
        if db_record_mtime and vector.mtime != db_record_mtime:
            # just log and skip
            vector.strategy = []
    return

@auth.requires_membership("Administrator")
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

@auth.requires_membership("Administrator")
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

@auth.requires_login()
def history():
    "Shows history of database synchronisations"
    title = T("Synchronisation History")
    logs = db().select(db[log_table].ALL, orderby=db[log_table].timestamp)
    return dict(title=title, logs=logs)

@auth.requires_membership("Administrator")
def conflict():
    "Conflict Resolution UI"
    # going to be a simple CRUD right now, will be changed later
    return shn_rest_controller("sync", "conflict", listadd=False)