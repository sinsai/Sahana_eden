"""
    Request Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16

    A module to record request of:
     - items
     - staff
     - assets
"""

module = "req"
if deployment_settings.has_module("inv"):
    #==========================================================================
    # Request
    REQ_STATUS_NONE       = 0
    REQ_STATUS_PARTIAL    = 1
    REQ_STATUS_COMPLETE   = 2

    req_status_opts = { REQ_STATUS_NONE:       T("None"),
                        REQ_STATUS_PARTIAL:    T("Partial"),
                        REQ_STATUS_COMPLETE:   T("Complete")
                       }

    req_status= S3ReusableField("req_status",
                                "integer",
                                label = T("Request Status"),
                                requires = IS_NULL_OR(IS_IN_SET(req_status_opts,
                                                                zero = None)),
                                represent = lambda status: req_status_opts[status] if status else T("None"),
                                default = REQ_STATUS_NONE,
                                writable = deployment_settings.get_req_status_writable(),
                                )

    req_priority_opts = {
        3:T("High"),
        2:T("Medium"),
        1:T("Low")
    }

    def shn_req_priority_represent(id):
        src = "/%s/static/img/priority/priority_%d.gif" % \
                  (request.application,(id or 4))
        return DIV(IMG(_src= src))

    resourcename = "req"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            super_link( db.org_site, 
                                        writable = True,
                                        readable = True,
                                        label = T("Requested By Site"),
                                        represent = shn_site_represent
                                        ),                            
                            Field("datetime",
                                  "datetime",
                                  label = T("Date Requested")),
                            Field("date_required",
                                  "date",
                                  label = T("Date Required")),
                            person_id("requester_id",
                                      label = T("Requester") ),
                            Field("priority",
                                  "integer",
                                  label = T("Priority"),
                                  represent = shn_req_priority_represent,
                                  requires = IS_NULL_OR(
                                                IS_IN_SET(req_priority_opts))
                                  ),
                            req_status("commit_status",
                                       label = T("Commit. Status"),
                                       ),
                            req_status("transit_status",
                                       label = T("Transit Status"),
                                       ),
                            req_status("fulfil_status",
                                       label = T("Fulfil. Status"),
                                       ),
                            Field("cancel",
                                  "boolean"),
                            comments(),
                            migrate=migrate, *s3_meta_fields())

    # -------------------------------------------------------------------------
    # CRUD strings
    ADD_REQUEST = T("Make Request")
    LIST_REQUEST = T("List Requests")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_REQUEST,
        title_display = T("Request Details"),
        title_list = LIST_REQUEST,
        title_update = T("Edit Request"),
        title_search = T("Search Requests"),
        subtitle_create = ADD_REQUEST,
        subtitle_list = T("Requests"),
        label_list_button = LIST_REQUEST,
        label_create_button = ADD_REQUEST,
        label_delete_button = T("Delete Request"),
        msg_record_created = T("Request Added"),
        msg_record_modified = T("Request Updated"),
        msg_record_deleted = T("Request Canceled"),
        msg_list_empty = T("No Requests"))

    # -----------------------------------------------------------------------------
    def shn_req_represent(id, link = True):
        id = int(id)
        if id:
            req_row = db(db.req_req.id == id).\
                              select(db.req_req.datetime,
                                     db.req_req.site_id,
                                     limitby=(0, 1))\
                              .first()
            req = "%s - %s" % (shn_site_represent( \
                                    req_row.site_id),
                                req_row.datetime
                                )
            if link:
                return A(req,
                         _href = URL(r = request,
                                     c = "req",
                                     f = "req",
                                     args = [id]),
                         _title = T("Go to Request"))
            else:
                return req
        else:
            return NONE

    # -----------------------------------------------------------------------------
    # Reusable Field
    req_id = S3ReusableField("req_id", db.req_req, sortby="request_date",
                                  requires = IS_ONE_OF(db,
                                                       "req_req.id",
                                                       lambda id: 
                                                           shn_req_represent(id,
                                                                             False
                                                                             ),
                                                       orderby="req_req.datetime",
                                                       sort=True),
                                  represent = shn_req_represent,
                                  label = T("Request"),
                                  ondelete = "RESTRICT"
                                  )

    #------------------------------------------------------------------------------
    # Request as a component of Sites
    s3xrc.model.add_component(module,
                              resourcename,
                              multiple = True,
                              joinby = super_key(db.org_site)
                              )

    #------------------------------------------------------------------------------
    # Redirect to the Items tabs after creation
    s3xrc.model.configure(table,
                          create_next = URL(r=request,
                                            c="req",
                                            f="req",
                                            args=["[id]", "req_item"]))

    #------------------------------------------------------------------------------
    # Update owned_by_role to the site's owned_by_role
    s3xrc.model.configure(
        table,
        onaccept = shn_component_copy_role_func(component_name = tablename,
                                                resource_name = "org_site",
                                                fk = "site_id",
                                                pk = "site_id")
    )
    #==============================================================================
    # Request Items
    #
    resourcename = "req_item"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            req_id(),
                            item_id(),
                            item_pack_id(),
                            Field( "quantity",
                                   "double",
                                   notnull = True),
                            Field( "quantity_commit",
                                   "double",
                                   default = 0,
                                   writable = False),
                            Field( "quantity_transit",
                                   "double",
                                   default = 0,
                                   writable = False),
                            Field( "quantity_fulfil",
                                   "double",
                                   default = 0,
                                   writable = False),
                            comments(),
                            migrate=migrate, *s3_meta_fields())

    #pack_quantity virtual field
    table.virtualfields.append(item_pack_virtualfields(tablename = tablename))

    # -----------------------------------------------------------------------------
    def shn_req_quantity_represent(quantity, type):
        if quantity:
            return TAG[""]( quantity,
                            A(DIV(_class = "quantity %s ajax_more collapsed" % type
                                  ),
                                _href = "#",
                              )
                            )
        else:
            return quantity

    table.quantity_commit.represent = lambda quantity_commit: shn_req_quantity_represent(quantity_commit, "commit")
    table.quantity_fulfil.represent = lambda quantity_fulfil: shn_req_quantity_represent(quantity_fulfil, "fulfil")
    table.quantity_transit.represent = lambda quantity_transit: shn_req_quantity_represent(quantity_transit, "transit")

    # -----------------------------------------------------------------------------
    # CRUD strings
    ADD_REQUEST_ITEM = T("Add Item to Request")
    LIST_REQUEST_ITEM = T("List Request Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_REQUEST_ITEM,
        title_display = T("Request Item Details"),
        title_list = LIST_REQUEST_ITEM,
        title_update = T("Edit Request Item"),
        title_search = T("Search Request Items"),
        subtitle_create = T("Add New Request Item"),
        subtitle_list = T("Requested Items"),
        label_list_button = LIST_REQUEST_ITEM,
        label_create_button = ADD_REQUEST_ITEM,
        label_delete_button = T("Delete Request Item"),
        msg_record_created = T("Request Item added"),
        msg_record_modified = T("Request Item updated"),
        msg_record_deleted = T("Request Item deleted"),
        msg_list_empty = T("No Request Items currently registered"))

    # -----------------------------------------------------------------------------
    # Reusable Field
    def shn_req_item_represent (id):
        record = db( (db.req_req_item.id == id) & \
                     (db.req_req_item.item_id == db.supply_item.id)
                    ).select( db.supply_item.name,
                              limitby = [0,1]).first()
        if record:
            return record.name
        else:
            return None

    # Reusable Field
    req_item_id = S3ReusableField( "req_item_id",
                                        db.req_req_item,
                                        requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                        "req_req_item.id",
                                                                        shn_req_item_represent,
                                                                        orderby="req_req_item.id",
                                                                        sort=True),
                                                              ),
                                        represent = shn_req_item_represent,
                                        label = T("Request Item"),
                                        comment = DIV( _class="tooltip", _title=T("Request Item") + "|" + T("Select Items from the Request")),
                                        ondelete = "RESTRICT"
                                        )

    #------------------------------------------------------------------------------
    # Request Items as component of Request
    # Request Items as a component of Items
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(req_req = "req_id",
                                          supply_item = "item_id"))

    #------------------------------------------------------------------------------
    # On Accept to update req_req
    def shn_req_item_onaccept(form):
        """
        Update req_req. commit_status, transit_status, fulfil_status
        None = quantity = 0 for ALL items
        Partial = some items have quantity > 0
        Complete = quantity_x = quantity(requested) for ALL items
        """
        # Update owned_by_role to the req's owned_by_role
        shn_component_copy_role_func(component_name = "req_req_item",
                                     resource_name = "req_req",
                                     fk = "req_id")(form)


        req_id = session.rcvars.req_req

        is_none = dict(commit = True,
                       transit = True,
                       fulfil = True,
                       )

        is_complete = dict(commit = True,
                           transit = True,
                           fulfil = True,
                           )

        #Must check all items in the req
        req_items = db( (db.req_req_item.req_id == req_id) & \
                        (db.req_req_item.deleted == False )
                        ).select(db.req_req_item.quantity,
                                 db.req_req_item.quantity_commit,
                                 db.req_req_item.quantity_transit,
                                 db.req_req_item.quantity_fulfil,
                                 )

        for req_item in req_items:
            for status_type in ["commit","transit", "fulfil"]:
                if req_item["quantity_%s" % status_type] < req_item.quantity:
                    is_complete[status_type] = False
                if req_item["quantity_%s" % status_type]:
                    is_none[status_type] = False

        status_update = {}
        for status_type in ["commit","transit", "fulfil"]:
            if is_complete[status_type]:
                status_update["%s_status" % status_type] = REQ_STATUS_COMPLETE
            elif is_none[status_type]:
                status_update["%s_status" % status_type] = REQ_STATUS_NONE
            else:
                status_update["%s_status" % status_type] = REQ_STATUS_PARTIAL
        db.req_req[req_id] = status_update

    s3xrc.model.configure(table, onaccept=shn_req_item_onaccept)
    
    #------------------------------------------------------------------------------
# Moved to controller
#    def shn_req_item_inv_item (xrequest, **attr):
#        req_item_id  = xrequest.id
#        item_id = xrequest.record.item_id
#        
#        response.s3.no_sspag = False
#        
#        # Get list of matching inventory items
#        #xrequest.resource.build_query(db.inv_inv_item.item_id == item_id)
#        response.s3.filter = (db.inv_inv_item.item_id == item_id)
#        inv_items = s3_rest_controller("inv", "inv_item")
#        
#        # Get list of alternative inventory items 
#        
#        
#        return inv_items

#    s3xrc.model.set_method(module, resourcename,
#                           method='inv_item', action=shn_req_item_inv_item )

    #==========================================================================
    # Commit

    resourcename = "commit"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            super_link( db.org_site, 
                                        writable = True,
                                        readable = True,
                                        label = T("From Inventory"),
                                        represent = shn_site_represent
                                        ),
                            req_id(),
                            Field("datetime",
                                  "datetime",
                                  label = T("Date")),
                            
                            Field("date_available",
                                  "date",
                                  label = T("Date Available")),

                            #For site should be a virtual field
                            #Field("for_site_id",
                            #      db.org_site,
                            #      ),
                            person_id("committer_id",
                                      label = T("Committed By") ),
                            comments(),
                            migrate=migrate, *s3_meta_fields())

    # -------------------------------------------------------------------------
    # CRUD strings
    ADD_COMMIT = T("Make Commitment")
    LIST_COMMIT = T("List Commitments")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_COMMIT,
        title_display = T("Commitment Details"),
        title_list = LIST_COMMIT,
        title_update = T("Edit Commitment"),
        title_search = T("Search Commitments"),
        subtitle_create = ADD_COMMIT,
        subtitle_list = T("Commitments"),
        label_list_button = LIST_COMMIT,
        label_create_button = ADD_COMMIT,
        label_delete_button = T("Delete Commitment"),
        msg_record_created = T("Commitment Added"),
        msg_record_modified = T("Commitment Updated"),
        msg_record_deleted = T("Commitment Canceled"),
        msg_list_empty = T("No Commitments"))

    # -----------------------------------------------------------------------------
    def shn_commit_represent(id):
        if id:
            r = db(db.req_commit.id == id).select(db.req_commit.datetime,
                                                   db.req_commit.site_id,
                                                   limitby=(0, 1)).first()
            return "%s - %s" % \
                    ( shn_site_represent(r.site_id),
                      r.datetime
                     )
        else:
            return NONE

    # -----------------------------------------------------------------------------
    # Reusable Field
    commit_id = S3ReusableField("commit_id", db.req_commit, sortby="date",
                                  requires = IS_NULL_OR( \
                                                 IS_ONE_OF(db,
                                                           "req_commit.id",
                                                           shn_commit_represent,
                                                           orderby="req_commit.date",
                                                           sort=True)),
                                  represent = shn_commit_represent,
                                  label = T("Commitment"),
                                  ondelete = "RESTRICT"
                                  )

    #------------------------------------------------------------------------------
    # Commitment as a component of Sites
    s3xrc.model.add_component(module,
                              resourcename,
                              multiple = True,
                              joinby = super_key(db.org_site)
                              )

    #------------------------------------------------------------------------------
    # Redirect to the Items tabs after creation
    s3xrc.model.configure(table,
                          create_next = URL(r=request, c="req", f="commit", args=["[id]", "commit_item"]))

    #------------------------------------------------------------------------------
    # Update owned_by_role to the site's owned_by_role
    s3xrc.model.configure(
        table,
        onaccept = shn_component_copy_role_func(component_name = tablename,
                                                resource_name = "org_site",
                                                fk = "site_id",
                                                pk = "site_id")
    )

    #==============================================================================
    # Commitment Items
    #
    resourcename = "commit_item"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            commit_id(),
                            #item_id(),
                            req_item_id(),
                            item_pack_id(),
                            Field("quantity",
                                  "double",
                                  notnull = True),
                            comments(),
                            migrate=migrate, *s3_meta_fields())

    #pack_quantity virtual field
    table.virtualfields.append(item_pack_virtualfields(tablename = tablename))

    # CRUD strings
    ADD_COMMIT_ITEM = T("Commitment Item")
    LIST_COMMIT_ITEM = T("List Commitment Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_COMMIT_ITEM,
        title_display = T("Commitment Item Details"),
        title_list = LIST_COMMIT_ITEM,
        title_update = T("Edit Commitment Item"),
        title_search = T("Search Commitment Items"),
        subtitle_create = T("Add New Commitment Item"),
        subtitle_list = T("Commitment Items"),
        label_list_button = LIST_COMMIT_ITEM,
        label_create_button = ADD_COMMIT_ITEM,
        label_delete_button = T("Delete Commitment Item"),
        msg_record_created = T("Commitment Item added"),
        msg_record_modified = T("Commitment Item updated"),
        msg_record_deleted = T("Commitment Item deleted"),
        msg_list_empty = T("No Commitment Items currently registered"))

    #------------------------------------------------------------------------------
    # Commitment Items as component of Commitment
    # Commitment Items as a component of Items
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict( req_commit = "commit_id" )
                              )

    #------------------------------------------------------------------------------
    def shn_commit_item_onaccept(form):
         # Update owned_by_role to the commit's owned_by_role
        shn_component_copy_role_func(component_name = "req_commit_item",
                                     resource_name = "req_commit",
                                     fk = "commit_id")(form)

        # try to get req_item_id from the form
        req_item_id = 0
        if form:
            req_item_id = form.vars.get("req_item_id")
        if not req_item_id:
            commit_item_id = session.rcvars.req_commit_item
            r_commit_item = db.req_commit_item[commit_item_id]

            req_item_id = r_commit_item.req_item_id

        commit_items =  db( (db.req_commit_item.req_item_id == req_item_id) & \
                            (db.req_commit_item.deleted == False)
                            ).select(db.req_commit_item.quantity ,
                                     db.req_commit_item.item_pack_id
                                     )
        quantity_commit = 0
        for commit_item in commit_items:
            quantity_commit += commit_item.quantity * commit_item.pack_quantity

        r_req_item = db.req_req_item[req_item_id]
        quantity_commit = quantity_commit / r_req_item.pack_quantity
        db.req_req_item[req_item_id] = dict(quantity_commit = quantity_commit)

        #Update status_commit of the req record
        session.rcvars.req_req = r_req_item.req_id
        shn_req_item_onaccept(None)


    s3xrc.model.configure(table, onaccept = shn_commit_item_onaccept )