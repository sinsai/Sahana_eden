# -*- coding: utf-8 -*-

"""
    Request Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @author: Fran Boon
    @date-created: 2010-09-02
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

response.menu_options = req_menu

#==============================================================================
def index():
    """
        Application Home page
        - custom View
    """
    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)
#==============================================================================
def req():
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Limit site_id to sites the user has permissions for
    shn_site_based_permissions(table,
                               T("You do not have permission for any site to make a request."))

    # Improve - get site which the staff is allocated to?
    site_id  = shn_get_db_field_value(db,
                                      "org_staff",
                                      "site_id",
                                      auth.person_id(),
                                      "person_id"
                                      )

    if not request.args: # No component 
        req_item_actions = [dict(url = str( URL(r=request,
                                                c = "req",
                                                f = "req",
                                                args = ["[id]", "req_item"]
                                               )
                                           ),
                                _class = "action-btn",
                                label = str(T("Request Items")),
                                ),
                            dict(url = str( URL( r=request,
                                                 c = "req",
                                                 f = "commit",
                                                 args = ["create"],
                                                 vars = dict(req_id = "[id]")
                                                )
                                            ),
                                 _class = "action-btn",
                                 label = str(T("Commit")),
                                 ),
                            ]
    elif "req_item" in request.args and deployment_settings.has_module("inv"):
        req_item_actions = [req_item_inv_item_btn]
    else:
        req_item_actions = []

    def prep(r):
        if r.interactive:
            if r.method != "update" and r.method != "read":
                # Hide fields which don't make sense in a Create form
                # - includes one embedded in list_create
                # - list_fields over-rides, so still visible within list itself
                shn_req_create_form_mods()
                # Request_items only applicable to the main Request Controller
                table = db.req_req_item
                table.quantity_commit.readable = table.quantity_commit.writable = False
                table.quantity_transit.readable = table.quantity_commit.writable = False
                table.quantity_fulfil.readable = table.quantity_commit.writable = False

        return True
    response.s3.prep = prep

    rheader = shn_req_rheader

    output = s3_rest_controller(module, resourcename, rheader=rheader)

    if deployment_settings.has_module("inv"):
        if response.s3.actions:
            response.s3.actions += req_item_actions
        else:
            response.s3.actions = req_item_actions

    return output
#==============================================================================
def req_item():
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    def prep(r):
        if r.interactive:
            if r.method != "update" and r.method != "read":
                # Hide fields which don't make sense in a Create form
                # - includes one embedded in list_create
                # - list_fields over-rides, so still visible within list itself
                table.quantity_commit.readable = table.quantity_commit.writable = False
                table.quantity_transit.readable = table.quantity_commit.writable = False
                table.quantity_fulfil.readable = table.quantity_commit.writable = False

        return True
    response.s3.prep = prep

    output = s3_rest_controller( module,
                                 resourcename,
                                 rheader=shn_commit_rheader)

    if response.s3.actions:
        response.s3.actions += [req_item_inv_item_btn]
    else:
        response.s3.actions = [req_item_inv_item_btn]

    return output

#------------------------------------------------------------------------------
def req_item_inv_item():
    """
    Shows the inventory items which match a requested item
    @ToDo: Make this page a component of req_item
    """
    req_item_id  = request.args[0]
    request.args = [] #
    req_item = db.req_req_item[req_item_id]
    req = db.req_req[req_item.req_id]

    output = {}

    output["title"] = T("Inventory Items Available for Request Item")
    output["req_item"] = TABLE( TR(
                                    TH( "%s: " % T("Requested By") ),
                                    shn_site_represent(req.site_id),
                                    TH( "%s: " % T("Item")),
                                    shn_item_represent(req_item.item_id),
                                   ),
                                TR(
                                    TH( "%s: " % T("Requester") ),
                                    shn_pr_person_represent(req.requester_id),
                                    TH( "%s: " % T("Quantity")),
                                    req_item.quantity,
                                   ),
                                TR(
                                    TH( "%s: " % T("Date Requested") ),
                                    req.date,
                                    TH( T("Quantity Committed")),
                                    req_item.quantity_commit,
                                   ),
                                TR(
                                    TH( "%s: " % T("Date Required") ),
                                    req.date_required,
                                    TH( "%s: " % T("Quantity in Transit")),
                                    req_item.quantity_transit,
                                   ),
                                TR(
                                    TH( "%s: " % T("Priority") ),
                                    shn_req_priority_represent(req.priority),
                                    TH( "%s: " % T("Quantity Fulfilled")),
                                    req_item.quantity_fulfil,
                                   )
                               )

    response.s3.no_sspag = True # pag won't work with 2 datatables on one page @todo: test

    # Get list of matching inventory items
    response.s3.filter = (db.inv_inv_item.item_id == req_item.item_id)
    inv_items = s3_rest_controller("inv", "inv_item")
    output["items"] = inv_items["items"]

    # Get list of alternative inventory items
    alt_item_rows = db( (db.supply_item_alt.item_id == req_item.item_id ) & \
                        (db.supply_item_alt.deleted == False )
                       ).select(db.supply_item_alt.alt_item_id)
    alt_item_ids = [alt_item_row.alt_item_id for alt_item_row in alt_item_rows]

    if alt_item_ids:
        response.s3.filter = (db.inv_inv_item.item_id.belongs(alt_item_ids))
        inv_items_alt = s3_rest_controller("inv", "inv_item")
        output["items_alt"] = inv_items_alt["items"]
    else:
        output["items_alt"] = None

    response.view = "req/req_item_inv_item.html"
    response.s3.actions = [dict(url = str(URL( r=request,
                                               c = "inv",
                                               f = "inv_item",
                                               args = ["[id]"],
                                               )
                                           ),
                                _class = "action-btn",
                                label = str(T("Open")),
                                )]

    return output

#==============================================================================
def commit():
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    if "req_id" in request.vars:
        db.req_commit.req_id.default = request.vars["req_id"]
        db.req_commit.req_id.writable = False

    # Limit site_id to sites the user has permissions for
    shn_site_based_permissions(table,
                               T("You do not have permission for any site to make a commitment.") )

    def prep(r):
        if r.record:
            req_id = r.record.req_id

            # Limit commit items to items from the request
            db.req_commit_item.req_item_id.requires = \
                IS_ONE_OF(db,
                          "req_req_item.id",
                          shn_req_item_represent,
                          orderby="req_req_item.id",
                          filterby ="req_id",
                          filter_opts = [req_id],
                          sort=True
                          )
        return True
    response.s3.prep = prep

    rheader = shn_commit_rheader

    output = s3_rest_controller(module, resourcename, rheader=rheader)

    return output

#------------------------------------------------------------------------------
def shn_commit_rheader(r):
    """ Resource Header for Commitments """

    if r.representation == "html":
        if r.name == "commit":
            commit_record = r.record
            if commit_record:
                rheader_tabs = s3_rheader_tabs( r,
                                                 [(T("Edit Details"), None),
                                                  (T("Items"), "commit_item"),
                                                  ]
                                                 )
                #req_record = db.req_req[commit_record.req_id]
                #req_date = req_record.date
                rheader = DIV( TABLE( TR( TH( "%s: " % T("Request")),
                                          shn_req_represent(commit_record.req_id),
                                         ),
                                      TR( TH( "%s: " % T("Committing Inventory")),
                                          shn_site_represent(commit_record.site_id),
                                          TH( "%s: " % T("Commit Date")),
                                          commit_record.date,
                                          ),
                                       TR( TH( "%s: " % T("Comments")),
                                           TD(commit_record.comments, _colspan=3)
                                          ),
                                         ),
                                        )

                send_btn = A( T("Send Items"),
                              _href = URL(r = request,
                                          c = "inv",
                                          f = "send_commit",
                                          args = [commit_record.id]
                                          ),
                              _id = "send_commit",
                              _class = "action-btn"
                              )

                send_btn_confirm = SCRIPT("S3ConfirmClick('#send_commit', '%s')" %
                                          T("Do you want to send these Committed items?") )
                rheader.append(send_btn)
                rheader.append(send_btn_confirm)

                rheader.append(rheader_tabs)

                return rheader
    return None

#------------------------------------------------------------------------------
def commit_item():
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]
    output = s3_rest_controller(module, resourcename)
    return output

#------------------------------------------------------------------------------
def commit_req():
    """
        function to commit items according to a request.
        copy data from a req into a commitment
        arg: req_id
        vars: site_id
    """

    req_id = request.args[0]
    r_req = db.req_req[req_id]
    site_id = request.vars.get("site_id")

    # User must have permissions over site which is sending
    (prefix, resourcename, id) = auth.s3_site_resource(site_id)
    if not site_id or not auth.s3_has_permission("update",
                                              db["%s_%s" % (prefix,
                                                            resourcename)],
                                              record_id=id):
        session.error = T("You do no have permission to make this commitment.")
        redirect(URL(r = request,
                     c = "req",
                     f = "req",
                     args = [req_id],
                     )
                 )

    # Create a new commit record
    commit_id = db.req_commit.insert( date = request.utcnow,
                                      req_id = req_id,
                                      site_id = site_id,
                                      )

    # Only select items which are in the warehouse
    req_items = db( (db.req_req_item.req_id == req_id) & \
                    (db.req_req_item.quantity_fulfil < db.req_req_item.quantity) & \
                    (db.inv_inv_item.site_id == site_id) & \
                    (db.req_req_item.item_id == db.inv_inv_item.item_id) & \
                    (db.req_req_item.deleted == False)  & \
                   (db.inv_inv_item.deleted == False)
                   ).select(db.req_req_item.id,
                            db.req_req_item.quantity,
                            db.req_req_item.item_pack_id,
                            db.inv_inv_item.item_id,
                            db.inv_inv_item.quantity,
                            db.inv_inv_item.item_pack_id)

    for req_item in req_items:
        req_item_quantity = req_item.req_req_item.quantity * \
                        req_item.req_req_item.pack_quantity

        inv_item_quantity = req_item.inv_inv_item.quantity * \
                        req_item.inv_inv_item.pack_quantity

        if inv_item_quantity > req_item_quantity:
            commit_item_quantity = req_item_quantity
        else:
            commit_item_quantity = inv_item_quantity
        commit_item_quantity = commit_item_quantity / req_item.req_req_item.pack_quantity

        if commit_item_quantity:
            commit_item_id = db.req_commit_item.insert( commit_id = commit_id,
                                        req_item_id = req_item.req_req_item.id,
                                        item_pack_id = req_item.req_req_item.item_pack_id,
                                        quantity = commit_item_quantity
                                       )

            # Update the req_item.commit_quantity  & req.commit_status
            session.rcvars.req_commit_item = commit_item_id
            shn_commit_item_onaccept(None)

    redirect(URL(r = request,
                 c = "req",
                 f = "commit",
                 args = [commit_id, "commit_item"]
                 )
             )

#==============================================================================#
def send_req():
    """
        function to send items according to a request.
        copy data from a req into a send
        arg: req_id
        vars: site_id
    """
    req_id = request.args[0]
    r_req = db.req_req[req_id]
    site_id = request.vars.get("site_id")

    # User must have permissions over site which is sending
    (prefix, resourcename, id) = auth.s3_site_resource(site_id)
    if not site_id or not auth.s3_has_permission("update",
                                              db["%s_%s" % (prefix,
                                                            resourcename)],
                                              record_id=id):
        session.error = T("You do no have permission to send this shipment.")
        redirect(URL(r = request,
                     c = "req",
                     f = "req",
                     args = [req_id],
                     )
                 )
    
    to_location_id = db.org_site[r_req.site_id].location_id

    # Create a new send record
    send_id = db.inv_send.insert( date = request.utcnow,
                                  site_id = site_id,
                                  to_location_id = to_location_id,
                                  )

    # Only select items which are in the warehouse
    req_items = db( (db.req_req_item.req_id == req_id) & \
                    (db.req_req_item.quantity_fulfil < db.req_req_item.quantity) & \
                    (db.inv_inv_item.site_id == site_id) & \
                    (db.req_req_item.item_id == db.inv_inv_item.item_id) & \
                    (db.req_req_item.deleted == False)  & \
                   (db.inv_inv_item.deleted == False)
                   ).select(db.req_req_item.id,
                            db.req_req_item.quantity,
                            db.req_req_item.item_pack_id,
                            db.inv_inv_item.id,
                            db.inv_inv_item.item_id,
                            db.inv_inv_item.quantity,
                            db.inv_inv_item.item_pack_id)

    for req_item in req_items:
        req_item_quantity = req_item.req_req_item.quantity * \
                        req_item.req_req_item.pack_quantity

        inv_item_quantity = req_item.inv_inv_item.quantity * \
                        req_item.inv_inv_item.pack_quantity

        if inv_item_quantity > req_item_quantity:
            send_item_quantity = req_item_quantity
        else:
            send_item_quantity = inv_item_quantity
        send_item_quantity = send_item_quantity / req_item.req_req_item.pack_quantity

        if send_item_quantity:
            send_item_id = db.inv_send_item.insert( send_id = send_id,
                                                    inv_item_id = req_item.inv_inv_item.id,
                                                    req_item_id = req_item.req_req_item.id,
                                                    item_pack_id = req_item.req_req_item.item_pack_id,
                                                    quantity = send_item_quantity
                                                    )
    # Redirect to commit
    redirect(URL(r = request,
                 c = "inv",
                 f = "send",
                 args = [send_id, "send_item"]
                 )
             )
#==============================================================================#
def commit_item_json():
    response.headers["Content-Type"] = "application/json"
    #db.req_commit.date.represent = lambda dt: dt[:10]
    records =  db( (db.req_commit_item.req_item_id == request.args[0]) & \
                   (db.req_commit.id == db.req_commit_item.commit_id) & \
                   (db.req_commit.site_id == db.org_site.id) & \
                   (db.req_commit_item.deleted == False )
                  ).select(db.req_commit.id,
                           db.req_commit.date,
                           db.org_site.name,
                           db.req_commit_item.quantity,
                           orderby = db.req_commit.date
                           )
    json_str = "[%s,%s" % ( json.dumps(dict(id = str(T("Committed")),
                                            quantity = "#"
                                            )
                                        ) ,
                            records.json()[1:]
                           )
    return json_str

# END =========================================================================
