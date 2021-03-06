# -*- coding: utf-8 -*-

"""
    Inventory Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16

    A module to record inventories of items at a locations (sites),
    including Warehouses, Offices, Shelters & Hospitals
    
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

response.menu_options = inv_menu

#------------------------------------------------------------------------------
def index():
    """
        Application Home page
        - custom View
    """
    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

#==============================================================================
def office():
    """
        Required to ensure the tabs work from req_match
    """
    return warehouse()

def warehouse():
    """
        RESTful CRUD controller
        Filtered version of the org_office resource
    """

    module = "org"
    resourcename = "office"
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]
    
    s3.crud_strings[tablename] = s3_warehouse_crud_strings

    # Type is Warehouse
    table.type.default = 5 # Warehouse
    table.type.writable = False

    # Only show warehouses
    response.s3.filter = (db.org_office.type == 5)

    # Remove type from list_fields
    list_fields = s3xrc.model.get_config(db.org_office, "list_fields")
    list_fields.remove("type")
    s3xrc.model.configure(table, list_fields=list_fields)

    def prep(r):
        if r.interactive:


            if r.method != "read":
                # Don't want to see in Create forms
                # inc list_create (list_fields over-rides)
                pr_address_hide(table)
                # Process Base Location
                #s3xrc.model.configure(table,
                #                      onaccept=address_onaccept)

            if r.component and r.component.name == "req":
                if r.method != "update" and r.method != "read":
                    # Hide fields which don't make sense in a Create form
                    # inc list_create (list_fields over-rides)
                    shn_req_create_form_mods()

        # Filter out people which are already staff for this warehouse
        shn_staff_prep(r)
        if deployment_settings.has_module("inv"):
            # Filter out items which are already in this inventory
            shn_inv_prep(r)

        # Cascade the organisation_id from the Warehouse to the staff
        if r.record:
            db.org_staff.organisation_id.default = r.record.organisation_id
            db.org_staff.organisation_id.writable = False

        # "show_obsolete" var option can be added (btn?) later to
        # disable this filter
        if r.method in [None, "list"] and \
            not r.request.vars.get("show_obsolete", False):
            r.resource.add_filter((db.org_office.obsolete != True))
        return True
    response.s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.component_name == "staff" and \
                isinstance(output, dict) and \
                deployment_settings.get_aaa_has_staff_permissions():
            addheader = "%s %s." % (STAFF_HELP,
                                    T("Warehouse"))
            output.update(addheader=addheader)
        return output
    response.s3.postp = postp

    rheader = shn_office_rheader

    output = s3_rest_controller(module, resourcename, rheader=rheader)

    return output

#==============================================================================
def incoming():
    """ Simulated component tab for Inventories """
    return s3_inv_incoming()

# -----------------------------------------------------------------------------
def req_match():
    s3.crud_strings.org_office.title_display = T("Warehouse Details")
    return s3_req_match()
#==============================================================================
def inv_item():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Limit site_id to sites the user has permissions for
    shn_site_based_permissions(table,
                               T("You do not have permission for any site to add an inventory item."))

    return s3_rest_controller(module, resourcename)
#------------------------------------------------------------------------------
def inv_item_quantity():
    response.headers["Content-Type"] = "application/json"
    record =  db( (db.inv_inv_item.id == request.args[0]) & \
                  (db.inv_inv_item.item_pack_id == db.supply_item_pack.id)
                 ).select(db.inv_inv_item.quantity,
                          db.supply_item_pack.quantity,
                          limitby=(0, 1)).first()#

    return json.dumps(record)
#------------------------------------------------------------------------------
def inv_item_packs():
    response.headers["Content-Type"] = "text/x-json"
    return db( (db.req_req_item.id == request.args[0]) & \
               (db.req_req_item.item_id == db.supply_item_pack.item_id)
              ).select( db.supply_item_pack.id,
                        db.supply_item_pack.name,
                        db.supply_item_pack.quantity).json()
#==============================================================================
def recv():
    """ RESTful CRUD controller """
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Limit site_id to sites the user has permissions for
    shn_site_based_permissions(table,
                               T("You do not have permission for any site to receive a shipment."))

    output = s3_rest_controller(module,
                                resourcename,
                                rheader=shn_recv_rheader)
    return output
#------------------------------------------------------------------------------
def shn_recv_rheader(r):
    """ Resource Header for Receiving """

    if r.representation == "html":
        if r.name == "recv":
            recv_record = r.record
            if recv_record:
                rheader = DIV( TABLE(
                                   TR( TH( "%s: " % T("Date")),
                                       recv_record.date,
                                       TH( "%s: " % T("From Organisation")),
                                       shn_organisation_represent(recv_record.from_organisation_id),
                                      ),
                                   TR( TH( "%s: " % T("By Site")),
                                       shn_site_represent(recv_record.site_id),
                                       TH( "%s: " % T("From Person")),
                                       recv_record.from_person,
                                      ),
                                   TR( TH( "%s: " % T("By Person")),
                                       vita.fullname(recv_record.recipient_id),
                                       TH( "%s: " % T("From Location")),
                                       shn_gis_location_represent(recv_record.from_location_id),
                                      ),
                                   TR( TH( "%s: " % T("Comments")),
                                       TD(recv_record.comments, _colspan=2),
                                      ),
                                     )
                                )


                if recv_record.status == SHIP_STATUS_IN_PROCESS:
                    if auth.s3_has_permission("update",
                                              db.inv_recv,
                                              record_id=recv_record.id):
                        recv_btn = A( T("Receive Items"),
                                      _href = URL(r = request,
                                                  c = "inv",
                                                  f = "recv_process",
                                                  args = [recv_record.id]
                                                  ),
                                      _id = "recv_process",
                                      _class = "action-btn"
                                      )

                        recv_btn_confirm = SCRIPT("S3ConfirmClick('#recv_process','%s')"
                                                  % T("Do you want to receive this shipment?") )
                        rheader.append(recv_btn)
                        rheader.append(recv_btn_confirm)
                else:
                    grn_btn = A( T("Goods Received Note"),
                                  _href = URL(r = request,
                                              c = "inv",
                                              f = "recv",
                                              args = [recv_record.id, "form.pdf"]
                                              ),
                                  _class = "action-btn"
                                  )
                    rheader.append(grn_btn)
                    dc_btn = A( T("Donation Certificate"),
                                  _href = URL(r = request,
                                              c = "inv",
                                              f = "recv",
                                              args = [recv_record.id, "cert.pdf"]
                                              ),
                                  _class = "action-btn"
                                  )
                    rheader.append(dc_btn)

                    if recv_record.status != SHIP_STATUS_CANCEL:
                        if auth.s3_has_permission("delete",
                                                  db.inv_recv,
                                                  record_id=recv_record.id):
                            cancel_btn = A( T("Cancel Shipment"),
                                            _href = URL(r = request,
                                                        c = "inv",
                                                        f = "recv_cancel",
                                                        args = [recv_record.id]
                                                        ),
                                            _id = "recv_cancel",
                                            _class = "action-btn"
                                            )

                            cancel_btn_confirm = SCRIPT("S3ConfirmClick('#recv_cancel', '%s')"
                                                         % T("Do you want to cancel this received shipment? The items will be removed from the Inventory. This action CANNOT be undone!") )
                            rheader.append(cancel_btn)
                            rheader.append(cancel_btn_confirm)

                rheader_tabs = s3_rheader_tabs( r,
                                                 [(T("Edit Details"), None),
                                                  (T("Items"), "recv_item"),
                                                  ]
                                                 )
                rheader.append(rheader_tabs)

                return rheader
    return None

#------------------------------------------------------------------------------
def recv_item():
    """ RESTful CRUD controller """
    #tablename = "%s_%s" % (module, resourcename)
    #table = db[tablename]
    output = s3_rest_controller(module, resourcename)
    return output

#==============================================================================
def send():
    """ RESTful CRUD controller """
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Limit site_id to sites the user has permissions for
    shn_site_based_permissions(table,
                               T("You do not have permission for any site to send a shipment.") )

    # Set Validator for checking against the number of items in the warehouse
    if (request.vars.inv_item_id):
        db.inv_send_item.quantity.requires = QUANTITY_INV_ITEM(db,
                                                               request.vars.inv_item_id,
                                                               request.vars.item_pack_id)

    def prep(r):
        # If component view
        if r.record and r.record.get("site_id"):
            # Restrict to items from this warehouse only
            db.inv_send_item.inv_item_id.requires = IS_ONE_OF(db,
                                                              "inv_inv_item.id",
                                                              shn_inv_item_represent,
                                                              orderby="inv_inv_item.id",
                                                              sort=True,
                                                              filterby = "site_id",
                                                              filter_opts = [r.record.site_id]
                                                             )
        return True

    response.s3.prep = prep

    output = s3_rest_controller(module,
                                resourcename,
                                rheader=shn_send_rheader)
    return output

#------------------------------------------------------------------------------
def shn_send_rheader(r):
    """ Resource Header for Send """

    if r.representation == "html":
        if r.name == "send":
            send_record = r.record
            if send_record:
                rheader = DIV( TABLE(
                                   TR( TH("%s: " % T("Date")),
                                       send_record.date,
                                      ),
                                   TR( TH("%s: " % T("From")),
                                       shn_site_represent(send_record.site_id),
                                       TH("%s: " % T("To")),
                                       shn_gis_location_represent(send_record.to_location_id),
                                      ),
                                   TR( TH("%s: " % T("Comments")),
                                       TD(send_record.comments, _colspan=3)
                                      )
                                     )
                                )

                if send_record.status == SHIP_STATUS_IN_PROCESS:
                    if auth.s3_has_permission("update",
                                              db.inv_send,
                                              record_id=send_record.id):
                        send_btn = A( T("Send Shipment"),
                                      _href = URL(r = request,
                                                  c = "inv",
                                                  f = "send_process",
                                                  args = [send_record.id]
                                                  ),
                                      _id = "send_process",
                                      _class = "action-btn"
                                      )

                        send_btn_confirm = SCRIPT("S3ConfirmClick('#send_process', '%s')"
                                                  % T("Do you want to send this shipment?") )
                        rheader.append(send_btn)
                        rheader.append(send_btn_confirm)
                else:
                    cn_btn = A( T("Consignment Note"),
                                  _href = URL(r = request,
                                              c = "inv",
                                              f = "send",
                                              args = [send_record.id, "form.pdf"]
                                              ),
                                  _class = "action-btn"
                                  )
                    rheader.append(cn_btn)

                    if send_record.status != SHIP_STATUS_CANCEL:
                        if auth.s3_has_permission("delete",
                                                  db.inv_send,
                                                  record_id=send_record.id):
                            if send_record.status == SHIP_STATUS_SENT:
                                if "site_id" in request.vars:
                                    receive_btn = A( T("Receive Shipment"),
                                                    _href = URL(r = request,
                                                                c = "inv",
                                                                f = "recv_sent",
                                                                args = [send_record.id],
                                                                vars = request.vars
                                                                ),
                                                    _id = "send_receive",
                                                    _class = "action-btn",
                                                    _title = "Receive this shipment"
                                                    )

                                    #receive_btn_confirm = SCRIPT("S3ConfirmClick('#send_receive', '%s')"
                                    #                             % T("Receive this shipment?") )
                                    rheader.append(receive_btn)
                                    #rheader.append(receive_btn_confirm)
                                elif "received" in request.vars:
                                    db.inv_send[send_record.id] = \
                                        dict(status = SHIP_STATUS_RECEIVED)
                                else:
                                    receive_btn = A( T("Confirm Shipment Received"),
                                                    _href = URL(r = request,
                                                                c = "inv",
                                                                f = "send",
                                                                args = [send_record.id],
                                                                vars = dict(received = True),
                                                                ),
                                                    _id = "send_receive",
                                                    _class = "action-btn",
                                                    _title = "Only use this button to confirm that the shipment has been received by the destination, if the destination will not enter this information into the system directly"
                                                    )

                                    receive_btn_confirm = SCRIPT("S3ConfirmClick('#send_receive', '%s')"
                                                                 % T("This shipment will be confirmed as received.") )
                                    rheader.append(receive_btn)
                                    rheader.append(receive_btn_confirm)

                            cancel_btn = A( T("Cancel Shipment"),
                                            _href = URL(r = request,
                                                        c = "inv",
                                                        f = "send_cancel",
                                                        args = [send_record.id]
                                                        ),
                                            _id = "send_cancel",
                                            _class = "action-btn"
                                            )

                            cancel_btn_confirm = SCRIPT("S3ConfirmClick('#send_cancel', '%s')"
                                                         % T("Do you want to cancel this sent shipment? The items will be returned to the Inventory. This action CANNOT be undone!") )
                            rheader.append(cancel_btn)
                            rheader.append(cancel_btn_confirm)

                rheader.append(s3_rheader_tabs( r,
                                                 [(T("Edit Details"), None),
                                                  (T("Items"), "send_item"),
                                                  ]
                                                 )
                               )
                return rheader
    return None
#------------------------------------------------------------------------------
def req_items_for_inv(site_id, quantity_type):
    """
    used by recv_process & send_process
    returns a dict of unique req items (with min  db.req_req.date_required | db.req_req.date)
    key = item_id
    @param site_id: The inventory to find the req_items from
    @param quantity_type: str ("commit", "transit" or "fulfil) The
                          quantity type which will be used to determine if this item is still outstanding
    """

    req_items = db( ( db.req_req.site_id == site_id ) & \
                    ( db.req_req.id == db.req_req_item.req_id) & \
                    ( db.req_req_item.item_pack_id == db.req_req_item.item_pack_id) & \
                    ( db.req_req_item["quantity_%s" % quantity_type] < db.req_req_item.quantity) & \
                    ( db.req_req.cancel == False ) & \
                    ( db.req_req.deleted == False ) & \
                    ( db.req_req_item.deleted == False )
                   ).select(db.req_req_item.id,
                            db.req_req_item.req_id,
                            db.req_req_item.item_id,
                            db.req_req_item.quantity,
                            db.req_req_item["quantity_%s" % quantity_type],
                            db.req_req_item.item_pack_id,
                            orderby = db.req_req.date_required | db.req_req.date,
                            #groupby = db.req_req_item.item_id
                            )

    # Because groupby doesn't follow the orderby, this will remove any
    # duplicate req_item, using the first record according to the orderby
    # req_items = req_items.as_dict( key = "req_req_item.item_id") <- doensn't work
    # @todo: web2py Rows.as_dict function could be extended to enable this functionality instead
    req_item_ids = []
    unique_req_items = Storage()
    for req_item in req_items:
        if req_item.item_id not in req_item_ids:
            # This item is not already in the dict
            unique_req_items[req_item.item_id] = Storage( req_item.as_dict() )
            req_item_ids.append(req_item.item_id)

    return unique_req_items

def req_item_in_shipment( shipment_item,
                          shipment_type,
                          req_items,
                         ):
    """
        Checks if a shipment item is in a request and updates req_item
        and the shipment.
    """

    shipment_item_table = "inv_%s_item" % shipment_type
    try:
        item_id = shipment_item[shipment_item_table].item_id
    except:
        item_id = shipment_item.inv_inv_item.item_id

    # Check for req_items
    if item_id in req_items:
        shn_shipment_to_req_type = dict(recv = "fulfil",
                                        send = "transit")
        quantity_req_type = "quantity_%s" % shn_shipment_to_req_type[shipment_type]

        # This item has been requested from this inv
        req_item = req_items[item_id]
        req_item_id = req_item.id

        # Update the req quantity
        # convert the shipment items quantity into the req_tem.quantity_fulfil (according to pack)
        quantity = req_item[quantity_req_type] + \
                   (shipment_item[shipment_item_table].pack_quantity / \
                    req_item.pack_quantity) * \
                    shipment_item[shipment_item_table].quantity
        quantity = min(quantity, req_item.quantity)  #Cap at req. quantity
        db.req_req_item[req_item_id] = {quantity_req_type: quantity}

        # Link the shipment_item to the req_item
        db[shipment_item_table][shipment_item[shipment_item_table].id] = dict(req_item_id = req_item_id)

        # Flag req record to update status_fulfil
        return req_item.req_id, req_item.id
    else:
        return None, None


def recv_process():
    recv_id = request.args[0]
    if not auth.s3_has_permission("update",
                                  db.inv_recv,
                                  record_id=recv_id):
        session.error = T("You do no have permission to receive this shipment.")


    recv_record = db.inv_recv[recv_id]

    if recv_record.status != SHIP_STATUS_IN_PROCESS:
        session.error = T("This shipment has already been received.")

    if session.error:
        redirect(URL(r = request,
                     c = "inv",
                     f = "recv",
                     args = [recv_id],
                     )
                 )

    site_id = recv_record.site_id

    # Get Recv & Inv Items
    recv_items = db( ( db.inv_recv_item.recv_id == recv_id ) & \
                     ( db.inv_recv_item.deleted == False )
                     ).select(db.inv_recv_item.id,
                              db.inv_recv_item.item_id,
                              db.inv_recv_item.quantity,
                              db.inv_recv_item.item_pack_id, # required by pack_quantity virtualfield
                              )

    inv_items = db( ( db.inv_inv_item.site_id == site_id ) & \
                      ( db.inv_inv_item.deleted == False )
                      ).select(db.inv_inv_item.id,
                               db.inv_inv_item.item_id,
                               db.inv_inv_item.quantity,
                               db.inv_inv_item.item_pack_id, # required by pack_quantity virtualfield
                               )

    inv_items_dict = inv_items.as_dict(key = "item_id")

    req_items = req_items_for_inv(site_id, "fulfil")

    update_req_id = []

    for recv_item in recv_items:
        item_id = recv_item.item_id
        if item_id in inv_items_dict:
            # This item already exists in the inv, and the quantity must be incremented
            inv_item = Storage(inv_items_dict[item_id])

            inv_item_id = inv_item.id

            quantity = shn_supply_item_add(inv_item.quantity,
                                           inv_item.pack_quantity,
                                           recv_item.quantity,
                                           recv_item.pack_quantity)
            item = dict(quantity = quantity)
        else:
            # This item must be added to the inv
            inv_item_id = 0
            item = dict( site_id = site_id,
                         item_id = item_id,
                         quantity = recv_item.quantity,
                         item_pack_id = recv_item.item_pack_id
                         )

        # Update Inv Item
        db.inv_inv_item[inv_item_id] = item

        # Check for req_items (-> fulfil)
        update_req_id.append( req_item_in_shipment(shipment_item = Storage(inv_recv_item = recv_item),
                                                       shipment_type = "recv",
                                                       req_items = req_items,
                                                       )
                                 )

    # Update recv record & lock for editing
    db.inv_recv[recv_id] = dict(date = request.utcnow,
                                 status = SHIP_STATUS_RECEIVED,
                                 owned_by_user = None,
                                 owned_by_role = ADMIN
                                 )

    # Update status_fulfil of the req record(s)
    for req_id, req_item_id in update_req_id:
        if req_id:
            session.rcvars.req_req = req_id
            session.rcvars.req_req_item = req_item_id
            shn_req_item_onaccept(None)

    session.confirmation = T("Shipment Items received by Inventory")

    # Go to the Inventory of the Site which has received these items
    (prefix, resourcename, id) = auth.s3_site_resource(site_id)

    redirect(URL(r = request,
                 c = prefix,
                 f = resourcename,
                 args = [id, "inv_item"],
                 vars = dict(show_inv="True")
                 )
             )
#------------------------------------------------------------------------------
def recv_cancel():
    recv_id = request.args[0]
    if not auth.s3_has_permission("delete",
                                  db.inv_recv,
                                  record_id=recv_id):
        session.error = T("You do no have permission to cancel this received shipment.")


    recv_record = db.inv_recv[recv_id]

    if recv_record.status != SHIP_STATUS_RECEIVED:
        session.error = T("This shipment has not been received - it has NOT been canceled because can still be edited.")

    if session.error:
        redirect(URL(r = request,
                     c = "inv",
                     f = "recv",
                     args = [recv_id],
                     )
                 )

    site_id = recv_record.site_id

    # Get Recv & Inv Items
    recv_items = db( ( db.inv_recv_item.recv_id == recv_id ) & \
                     ( db.inv_recv_item.deleted == False )
                     ).select(db.inv_recv_item.id,
                              db.inv_recv_item.item_id,
                              db.inv_recv_item.quantity,
                              db.inv_recv_item.item_pack_id, # required by pack_quantity virtualfield
                              db.inv_recv_item.req_item_id,
                              )

    inv_items = db( ( db.inv_inv_item.site_id == site_id ) & \
                      ( db.inv_inv_item.deleted == False )
                      ).select(db.inv_inv_item.id,
                               db.inv_inv_item.item_id,
                               db.inv_inv_item.quantity,
                               db.inv_inv_item.item_pack_id, # required by pack_quantity virtualfield
                               )

    inv_items_dict = inv_items.as_dict(key = "item_id")

    req_items = req_items_for_inv(site_id, "fulfil")

    update_req_id = []

    for recv_item in recv_items:
        item_id = recv_item.item_id
        # All Items received *should* exist in the inv.
        if item_id in inv_items_dict:
            # Decrease the inv_item.quantity
            inv_item = Storage(inv_items_dict[item_id])

            inv_item_id = inv_item.id

            quantity = shn_supply_item_add(inv_item.quantity,
                                           inv_item.pack_quantity,
                                           -recv_item.quantity,
                                           recv_item.pack_quantity)

            item = dict(quantity = quantity)
        else:
            # This Value should be added with a negative value
            inv_item_id = 0
            item = dict( site_id = site_id,
                         item_id = item_id,
                         quantity = -recv_item.quantity,
                         item_pack_id = recv_item.item_pack_id
                         )

        # Update Inv Item
        db.inv_inv_item[inv_item_id] = item

        # Remove the link from the recv_item to the req_item
        db.inv_recv_item[recv_item.id] = dict(req_item_id = None)

        # Reduce any req_item
        req_item_id = recv_item.req_item_id
        r_req_item = db((db.req_req_item.id == recv_item.req_item_id) &
                        (db.req_req_item.deleted == False)
                        ).select(db.req_req_item.quantity_fulfil,
                                 db.req_req_item.item_pack_id, # required by pack_quantity virtualfield
                                 limitby = (0,1)).first()
        if r_req_item:
            quantity_fulfil = shn_supply_item_add(r_req_item.quantity_fulfil,
                                                  r_req_item.pack_quantity,
                                                  -recv_item.quantity,
                                                  recv_item.pack_quantity)
            db.req_req_item[req_item_id] = dict(quantity_fulfil=quantity_fulfil)

            # Check for req_items (-> fulfil)
            update_req_id.append( [r_req_item.req_id, req_item_id] )

    # Update recv record & lock for editing
    db.inv_recv[recv_id] = dict(date = request.utcnow,
                                status = SHIP_STATUS_CANCEL,
                                owned_by_user = None,
                                owned_by_role = ADMIN
                                )

    # Update status_fulfil of the req record(s)
    for req_id, req_item_id in update_req_id:
        if req_id:
            session.rcvars.req_req = req_id
            session.rcvars.req_req_item = req_item_id
            shn_req_item_onaccept(None)

    session.confirmation = T("Received Shipment canceled and items removed from Inventory")

    redirect(URL(r = request,
                 c = "inv",
                 f = "recv",
                 args = [recv_id],
                 )
             )
#------------------------------------------------------------------------------
def send_process():
    send_id = request.args[0]
    if not auth.s3_has_permission("update",
                                  db.inv_send,
                                  record_id=send_id):
        session.error = T("You do no have permission to send this shipment.")

    send_record = db.inv_send[send_id]

    if send_record.status != SHIP_STATUS_IN_PROCESS:
        session.error = T("This shipment has already been sent.")

    if session.error:
        redirect(URL(r = request,
                     c = "inv",
                     f = "send",
                     args = [send_id],
                     )
                 )


    site_id = send_record.site_id
    
    cancel_send = False
    invalid_send_item_ids = []

    # Get Send & Inv Items
    send_items = db( ( db.inv_send_item.send_id == send_id ) & \
                     ( db.inv_send_item.deleted == False ) )\
                 .select( db.inv_send_item.id,
                          db.inv_send_item.quantity,
                          db.inv_send_item.item_pack_id,
                          db.inv_inv_item.id,
                          db.inv_inv_item.item_id,
                          db.inv_inv_item.quantity,
                          db.inv_inv_item.item_pack_id, # required by pack_quantity virtualfield
                          db.inv_inv_item.deleted,
                          left=db.inv_inv_item.on(db.inv_send_item.inv_item_id == db.inv_inv_item.id),
                          # To ensure that all send items are selected, even if the inv item has been deleted.
                          )

    # Filter for inv site records (separate due to left-join
    send_items.exclude(lambda row: row.inv_inv_item.id and \
                                   row.inv_inv_item.deleted == True
                       )

    try:
        to_site_id = db( (db.org_site.location_id == send_record.to_location_id) & \
                         (db.org_site.deleted == False)
                        ).select( db.org_site.id,
                                  limitby = (0,1)
                                 ).first().id
    except:
        to_site_id = None
                             
    req_items = req_items_for_inv(to_site_id, "transit")

    update_req_id = []

    for send_item in send_items:
        item_id = send_item.inv_inv_item.item_id
        send_item_id = send_item.inv_send_item.id
        inv_item_id = send_item.inv_inv_item.id

        new_inv_quantity = shn_supply_item_add(send_item.inv_inv_item.quantity,
                                               send_item.inv_inv_item.pack_quantity,
                                               -send_item.inv_send_item.quantity,
                                               send_item.inv_send_item.pack_quantity,
                                               )

        if new_inv_quantity < 0:
            # This shipment is invalid
            # flag this item
            invalid_send_item_ids.append(send_item_id)

            # Cancel this processing
            cancel_send = True
        else:
            # Update the Inv Item Quantity
            db.inv_inv_item[inv_item_id] = dict(quantity = new_inv_quantity)

        # Check for req_items (-> transit)
        update_req_id.append(req_item_in_shipment(shipment_item = send_item,
                                                      shipment_type = "send",
                                                      req_items = req_items
                                                      )
                                 )

    if cancel_send:
        db.rollback()
        for invalid_send_item_id in invalid_send_item_ids:
            db.inv_send_item[invalid_send_item_id] = dict(status = 1)

        response.error = T("There are not sufficient items in the Inventory to send this shipment") #@todo: list the items and the quantities in the error message
        redirect(URL(r = request,
                     c = "inv",
                     f = "send",
                     args = [send_id, "send_item"]
                     )
                 )
    else:
        # Update Send record & lock for editing
        db.inv_send[send_id] = dict(date = request.utcnow,
                                     status = SHIP_STATUS_SENT,
                                     owned_by_user = None,
                                     owned_by_role = ADMIN
                                     )
        session.confirmation = T("Shipment Items sent from Inventory")

        # Update status_fulfil of the req record(s)
        for req_id, req_item_id in update_req_id:
            if req_id:
                session.rcvars.req_req = req_id
                session.rcvars.req_req_item = req_item_id
                shn_req_item_onaccept(None)

        # Go to the Site which has sent these items
        (prefix, resourcename, id) = auth.s3_site_resource(site_id)

        redirect(URL(r = request,
                     c = prefix,
                     f = resourcename,
                     args = [id, "inv_item"]
                     )
                 )
#------------------------------------------------------------------------------
def send_cancel():
    """
    Could we reuse recv_cancel? Challenges:
     * errors
     * sent_items query
      * Different query
      * two tables in rows result
    """
    send_id = request.args[0]
    if not auth.s3_has_permission("delete",
                                  db.inv_send,
                                  record_id=send_id):
        session.error = T("You do no have permission to cancel this sent shipment.")


    send_record = db.inv_send[send_id]

    if send_record.status != SHIP_STATUS_SENT:
        session.error = T("This shipment has not been sent - it has NOT been canceled because can still be edited.")

    if session.error:
        redirect(URL(r = request,
                     c = "inv",
                     f = "send",
                     args = [send_id],
                     )
                 )

    site_id = send_record.site_id

    #Get Send & Inv Items
    send_items = db( ( db.inv_send_item.send_id == send_id ) & \
                     ( db.inv_send_item.inv_item_id == db.inv_inv_item.id ) & \
                     ( db.inv_send_item.deleted == False ) & \
                     ( db.inv_inv_item.deleted == False )
                     ).select(db.inv_send_item.id,
                              db.inv_inv_item.item_id,
                              db.inv_send_item.quantity,
                              db.inv_send_item.item_pack_id, # required by pack_quantity virtualfield
                              db.inv_send_item.req_item_id,
                              )

    inv_items = db( ( db.inv_inv_item.site_id == site_id ) & \
                      ( db.inv_inv_item.deleted == False )
                      ).select(db.inv_inv_item.id,
                               db.inv_inv_item.item_id,
                               db.inv_inv_item.quantity,
                               db.inv_inv_item.item_pack_id, # required by pack_quantity virtualfield
                               )

    inv_items_dict = inv_items.as_dict(key = "item_id")

    req_items = req_items_for_inv(site_id, "transit")

    update_req_id = []

    for send_item in send_items:
        item_id = send_item.inv_inv_item.item_id
        # All Items received *should* exist in the inv.
        if item_id in inv_items_dict:
            # Decrease the inv_item.quantity
            inv_item = Storage(inv_items_dict[item_id])

            inv_item_id = inv_item.id

            quantity = shn_supply_item_add(inv_item.quantity,
                                           inv_item.pack_quantity,
                                           send_item.inv_send_item.quantity,
                                           send_item.inv_send_item.pack_quantity)

            item = dict(quantity = quantity)
        else:
            # This Value should be added with a negative value
            inv_item_id = 0
            item = dict( site_id = site_id,
                         item_id = item_id,
                         quantity = send_item.inv_send_item.quantity,
                         item_pack_id = send_item.inv_send_item.item_pack_id
                         )

        # Update Inv Item
        db.inv_inv_item[inv_item_id] = item

        # Remove the link from the recv_item to the req_item
        db.inv_recv_item[send_item.inv_send_item.id] = dict(req_item_id = None)

        # Reduce any req_item
        req_item_id = send_item.inv_send_item.req_item_id
        r_req_item = db((db.req_req_item.id == req_item_id) &
                        (db.req_req_item.deleted == False)
                        ).select(db.req_req_item.quantity_fulfil,
                                 db.req_req_item.item_pack_id, # required by pack_quantity virtualfield
                                 limitby = (0, 1)).first()
        if r_req_item:
            quantity_fulfil = shn_supply_item_add(r_req_item.quantity_fulfil,
                                                  r_req_item.pack_quantity,
                                                  -send_item.inv_send_item.quantity,
                                                  send_item.inv_send_item.pack_quantity)
            db.req_req_item[req_item_id] = dict(quantity_fulfil=quantity_fulfil)

            # Check for req_items (-> fulfil)
            update_req_id.append( [r_req_item.req_id, req_item_id] )

    # Update send record & lock for editing
    db.inv_send[send_id] = dict(date = request.utcnow,
                                status = SHIP_STATUS_CANCEL,
                                owned_by_user = None,
                                owned_by_role = ADMIN
                                )

    # Update status_fulfil of the req record(s)
    for req_id, req_item_id in update_req_id:
        if req_id:
            session.rcvars.req_req = req_id
            session.rcvars.req_req_item = req_item_id
            shn_req_item_onaccept(None)

    session.confirmation = T("Sent Shipment canceled and items returned to Inventory")

    redirect(URL(r = request,
                 c = "inv",
                 f = "send",
                 args = [send_id],
                 )
             )
#==============================================================================
def recv_sent():
    """ function to copy data from a shipment which was sent to the warehouse to a recv shipment """

    send_id = request.args[0]

    if not auth.s3_has_permission("update",
                                  db.inv_send,
                                  record_id=send_id):
        session.error = T("You do no have permission to receive this shipment.")

    r_send = db.inv_send[send_id]

    if r_send.status != SHIP_STATUS_SENT:
        session.error = T("This shipment has already been received.")

    if session.error:
        redirect(URL(r = request,
                     c = "inv",
                     f = "send",
                     args = [send_id],
                     )
                 )

    # This is more explicit than getting the site_id from the inv_send.to_location_id
    # As there may be multiple sites per location.
    site_id = request.vars.site_id

    from_location_id = shn_get_db_field_value(db,
                                              "org_site",
                                              "location_id",
                                              r_send.site_id,
                                              "site_id" )

    # Create a new recv record
    recv_id = db.inv_recv.insert(site_id = site_id,
                                  from_location_id = from_location_id)

    sent_items = db( (db.inv_send_item.send_id == send_id) & \
                     (db.inv_send_item.inv_item_id == db.inv_inv_item.id) & \
                     (db.inv_send_item.deleted == False)
                     ).select(db.inv_inv_item.item_id,
                              db.inv_send_item.item_pack_id,
                              db.inv_send_item.quantity,
                              db.inv_send_item.req_item_id,)

    # Copy items from send to recv
    for sent_item in sent_items:
        db.inv_recv_item.insert(recv_id = recv_id,
                                item_id = sent_item.inv_inv_item.item_id,
                                item_pack_id = sent_item.inv_send_item.item_pack_id,
                                quantity = sent_item.inv_send_item.quantity,
                                req_item_id = sent_item.inv_send_item.req_item_id)


    # Flag shipment as received as received
    db.inv_send[send_id] = dict(status = SHIP_STATUS_RECEIVED)

    # Redirect to rec
    redirect(URL(r = request,
                 c = "inv",
                 f = "recv",
                 args = [recv_id]
                 )
             )
#==============================================================================
def send_commit():
    """
        function to send items according to a commit.
        copy data from a commit into a send
        arg: commit_id
        @ToDo: This function needs to be able to detect the site to send the items from,
        site_id is currently undefined and this will not work.
    """

    commit_id = request.args[0]
    r_commit = db.req_commit[commit_id]

    # User must have permissions over site which is sending
    (prefix, resourcename, id) = auth.s3_site_resource(r_commit.site_id)
    if not auth.s3_has_permission("update",
                                  db["%s_%s" % (prefix, resourcename)],
                                  record_id=id):
        session.error = T("You do not have permission to send a shipment from this site.")
        redirect(URL(r = request,
                     c = "req",
                     f = "commit",
                     args = [commit_id],
                     )
                 )
    
    to_location_id = db( (db.req_req.id == r_commit.req_id) &
                         (db.org_site.id == db.req_req.site_id)
                        ).select(db.org_site.location_id,
                                 limitby = (0,1)
                                 ).first().location_id
                                 

    # Create a new send record
    send_id = db.inv_send.insert( date = request.utcnow,
                                  site_id = r_commit.site_id,
                                  to_location_id = to_location_id,
                                   )

    # Only select items which are in the warehouse
    commit_items = db( (db.req_commit_item.commit_id == commit_id) & \
                       (db.req_commit_item.req_item_id == db.req_req_item.id) & \
                       (db.req_req_item.item_id == db.inv_inv_item.item_id) & \
                       (db.req_commit_item.deleted == False) & \
                       (db.req_req_item.deleted == False) & \
                       (db.inv_inv_item.deleted == False)
                   ).select( db.inv_inv_item.id,
                             db.req_commit_item.quantity,
                             db.req_commit_item.item_pack_id,
                             db.req_commit_item.req_item_id,
                            )

    for commit_item in commit_items:
        send_item_id = db.inv_send_item.insert( send_id = send_id,
                                                inv_item_id = commit_item.inv_inv_item.id,
                                                quantity = commit_item.req_commit_item.quantity,
                                                item_pack_id = commit_item.req_commit_item.item_pack_id,
                                                req_item_id = commit_item.req_commit_item.req_item_id,
                                                )

    # Redirect to send
    redirect(URL(r = request,
                 c = "inv",
                 f = "send",
                 args = [send_id]
                 )
             )
#==============================================================================#
def recv_item_json():
    response.headers["Content-Type"] = "application/json"
    db.inv_recv.date.represent = lambda dt: dt[:10]
    records =  db( (db.inv_recv_item.req_item_id == request.args[0]) & \
                   (db.inv_recv.id == db.inv_recv_item.recv_id) & \
                   (db.inv_recv.site_id == db.org_site.id) & \
                   (db.inv_recv.status == SHIP_STATUS_RECEIVED) & \
                   (db.inv_recv_item.deleted == False )
                  ).select(db.inv_recv.id,
                           db.inv_recv.date,
                           db.org_site.name,
                           db.inv_recv_item.quantity,
                           )
    json_str = "[%s,%s" % ( json.dumps(dict(id = str(T("Received")),
                                            quantity = "#"
                                            )
                                        ) ,
                            records.json()[1:]
                           )
    return json_str
#==============================================================================#
def send_item_json():
    response.headers["Content-Type"] = "application/json"
    db.inv_send.date.represent = lambda dt: dt[:10]
    records =  db( (db.inv_send_item.req_item_id == request.args[0]) & \
                   (db.inv_send.id == db.inv_send_item.send_id) & \
                   (db.inv_send.site_id == db.org_site.id) & \
                   (db.inv_send.status == SHIP_STATUS_SENT ) & \
                   (db.inv_send_item.deleted == False )
                  ).select(db.inv_send.id,
                           db.inv_send.date,
                           db.org_site.name,
                           db.inv_send_item.quantity,
                           )
    json_str = "[%s,%s" % ( json.dumps(dict(id = str(T("Sent")),
                                            quantity = "#"
                                            )
                                        ) ,
                            records.json()[1:]
                           )
    return json_str
