# -*- coding: utf-8 -*-
"""
    Logistics Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-09-02

    Distribution, Shipments

"""
#==============================================================================
logs_menu = [
            [T("Home"), False, URL(r=request, c="logs", f="index")],
            [T("Catalog Items"), False, URL(r=request, c="supply", f="item"),
            [
                [T("List"), False, URL(r=request, c="supply", f="item")],
                [T("Add"), False, URL(r=request, c="supply", f="item", args="create")],
            ]],            
            [T("Warehouses"), False, URL(r=request, c="inventory", f="store"),
            [
                [T("List"), False, URL(r=request, c="inventory", f="store")],
                [T("Add"), False, URL(r=request, c="inventory", f="store", args="create")],
            ]],
            [T("Request"), False, URL(r=request, c="logs", f="req"),
            [
                [T("List"), False, URL(r=request, c="logs", f="req")],
          #      [T("Add"), False, URL(r=request, c="logs", f="req", args="create")],
            ]],
           # [T("Receive"), False, URL(r=request, c="logs", f="recv"),
           # [
           #     [T("List"), False, URL(r=request, c="logs", f="recv")],
           #     [T("Add"), False, URL(r=request, c="logs", f="recv", args="create")],
           # ]],
           # [T("Send"), False, URL(r=request, c="logs", f="send"),
           # [
           #     [T("List"), False, URL(r=request, c="logs", f="send")],
           #     [T("Add"), False, URL(r=request, c="logs", f="send", args="create")],
           # ]],
            ]
if s3_has_role(1):
    logs_menu.append(
        [T("Item Categories"), False, URL(r=request, c="supply", f="item_category"),[
            [T("List"), False, URL(r=request, c="supply", f="item_category")],
            [T("Add"), False, URL(r=request, c="supply", f="item_category", args="create")]
        ]]
    )
#==============================================================================
module = "logs"
if deployment_settings.has_module(module):

    #==========================================================================
    # Request
    REQ_STATUS_NONE       = 0 
    REQ_STATUS_PARTIAL    = 1
    REQ_STATUS_COMPLETE   = 2
    
    log_req_status_dict = { REQ_STATUS_NONE:       T("None"),
                            REQ_STATUS_PARTIAL:    T("Partial"),
                            REQ_STATUS_COMPLETE:   T("Complete")
                           }

    req_status= S3ReusableField("req_status", 
                                "integer",
                                label = T("Request Status"),
                                requires = IS_NULL_OR(IS_IN_SET(log_req_status_dict,
                                                                zero = None)),
                                represent = lambda status: log_req_status_dict[status] if status else T("None"),
                                default = REQ_STATUS_NONE,
                                writable = False,
                                )

    resourcename = "req"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("date",
                                  "date",
                                  label = T("Date Requested")),
                            Field("date_required",
                                  "date",
                                  label = T("Date Required")),
                            inventory_store_id(label = T("Requested By Store")),
                            req_status("commit_status",
                                       label = T("Commit. Status"),
                                       ),
                            req_status("transit_status",
                                       label = T("Transit Status"),
                                       ),                                       
                            req_status("fulfil_status",
                                       label = T("Fulfil. Status"),
                                       ),                                  
                            person_id("requester_id",
                                      label = T("Requester") ),
                            comments(),
                            migrate=migrate, *s3_meta_fields())

    # -------------------------------------------------------------------------
    # CRUD strings
    ADD_LOGS_REQUEST = T("Make Request")
    LIST_LOGS_REQUEST = T("List Requests")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_LOGS_REQUEST,
        title_display = T("Request Details"),
        title_list = LIST_LOGS_REQUEST,
        title_update = T("Edit Request"),
        title_search = T("Search Requests"),
        subtitle_create = ADD_LOGS_REQUEST,
        subtitle_list = T("Requests"),
        label_list_button = LIST_LOGS_REQUEST,
        label_create_button = ADD_LOGS_REQUEST,
        label_delete_button = T("Delete Request"),
        msg_record_created = T("Request Added"),
        msg_record_modified = T("Request Updated"),
        msg_record_deleted = T("Request Canceled"),
        msg_list_empty = T("No Requests"))

    # -----------------------------------------------------------------------------
    def logs_req_represent(id, link = True):
        if id:
            logs_req_row = db(db.logs_req.id == id).\
                              select(db.logs_req.date,
                                     db.logs_req.inventory_store_id,
                                     limitby=(0, 1))\
                              .first()
            return "%s - %s" % (inventory_store_represent( \
                                    logs_req_row.inventory_store_id,
                                    link
                                    ),
                                logs_req_row.date
                                )
        else:
            return NONE

    # -----------------------------------------------------------------------------
    # Reusable Field
    logs_req_id = S3ReusableField("logs_req_id", db.logs_req, sortby="request_date",
                                  requires = IS_NULL_OR( \
                                                 IS_ONE_OF(db,
                                                           "logs_req.id",
                                                           lambda id: logs_req_represent(id,
                                                                                         False
                                                                                         ),
                                                           orderby="logs_req.date",
                                                           sort=True)),
                                  represent = logs_req_represent,
                                  label = T("Request"),
                                  #comment = DIV(A(ADD_DISTRIBUTION, _class="colorbox", _href=URL(r=request, c="logs", f="distrib", args="create", vars=dict(format="popup")), _target="top", _title=ADD_DISTRIBUTION),
                                  #          DIV( _class="tooltip", _title=T("Distribution") + "|" + T("Add Distribution."))),
                                  ondelete = "RESTRICT"
                                  )

    #------------------------------------------------------------------------------
    # Request as a component of Inventory Store
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict( inventory_store = \
                                               "inventory_store_id" ) )

    #------------------------------------------------------------------------------
    # Redirect to the Items tabs after creation
    s3xrc.model.configure(table,
                          create_next = URL(r=request, c="logs", f="req", args=["[id]", "req_item"]))
    
    #------------------------------------------------------------------------------
    # Update owned_by_role to the store's owned_by_role    
    s3xrc.model.configure(
        table, 
        onaccept = lambda form, tablename = tablename : store_resource_onaccept(form, tablename)
    )    
    #==============================================================================
    # Request Items
    #
    resourcename = "req_item"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            logs_req_id(),
                            item_id(),
                            item_packet_id(),
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
    
    #packet_quantity virtual field
    table.virtualfields.append(item_packet_virtualfields(tablename = tablename))   
    
    # -----------------------------------------------------------------------------
    def logs_req_quantity_represent(quantity, type):
        if quantity:            
            return TAG[""]( quantity,
                            A(DIV(_class = "quantity %s ajax_more collapsed" % type
                                  ),                                                        
                                _href = "#",
                              )
                            ) 
        else:
            return quantity                
    
    table.quantity_commit.represent = lambda quantity_commit: logs_req_quantity_represent(quantity_commit, "commit")  
    table.quantity_fulfil.represent = lambda quantity_fulfil: logs_req_quantity_represent(quantity_fulfil, "fulfil")    
    table.quantity_transit.represent = lambda quantity_transit: logs_req_quantity_represent(quantity_transit, "transit")  

    # -----------------------------------------------------------------------------
    # CRUD strings
    ADD_LOGS_REQUEST_ITEM = T("Add Item to Request")
    LIST_LOGS_REQUEST_ITEM = T("List Request Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_LOGS_REQUEST_ITEM,
        title_display = T("Request Item Details"),
        title_list = LIST_LOGS_REQUEST_ITEM,
        title_update = T("Edit Request Item"),
        title_search = T("Search Request Items"),
        subtitle_create = T("Add New Request Item"),
        subtitle_list = T("Requested Items"),
        label_list_button = LIST_LOGS_REQUEST_ITEM,
        label_create_button = ADD_LOGS_REQUEST_ITEM,
        label_delete_button = T("Delete Request Item"),
        msg_record_created = T("Request Item added"),
        msg_record_modified = T("Request Item updated"),
        msg_record_deleted = T("Request Item deleted"),
        msg_list_empty = T("No Request Items currently registered"))
    
    # -----------------------------------------------------------------------------
    # Reusable Field
    def shn_logs_req_item_represent (id):
        record = db( (db.logs_req_item.id == id) & \
                     (db.logs_req_item.item_id == db.supply_item.id) 
                    ).select( db.supply_item.name,
                              limitby = [0,1]).first()
        if record:
            return record.name
        else:
            return None  

    # Reusable Field
    logs_req_item_id = S3ReusableField( "logs_req_item_id", 
                                        db.logs_req_item,
                                        requires = IS_NULL_OR(IS_ONE_OF(db, 
                                                                        "logs_req_item.id", 
                                                                        shn_logs_req_item_represent, 
                                                                        orderby="logs_req_item.id", 
                                                                        sort=True),
                                                              ),
                                        represent = shn_logs_req_item_represent,
                                        label = T("Request Item"),
                                        comment = DIV( _class="tooltip", _title=T("Request Item") + "|" + T("Select Items from the Request")),
                                        ondelete = "RESTRICT"
                                        )    
    
    #------------------------------------------------------------------------------
    # Request Items as component of Request
    # Request Items as a component of Items
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(logs_req = "logs_req_id",
                                          supply_item = "item_id")) 

    #------------------------------------------------------------------------------
    # On Accept to update logs_req
    def logs_req_item_onaccept(form):
        """
        Update logs_req. commit_status, transit_status, fulfil_status
        None = quantity = 0 for ALL items
        Partial = some items have quantity > 0 
        Complete = quantity_x = quantity(requested) for ALL items
        """       
        req_id = session.rcvars.logs_req
                
        is_none = dict(commit = True,
                       transit = True,
                       fulfil = True,
                       )
        
        is_complete = dict(commit = True,
                           transit = True,
                           fulfil = True,
                           )      
          
        #Must check all items in the req
        req_items = db( (db.logs_req_item.logs_req_id == req_id) & \
                        (db.logs_req_item.deleted == False ) 
                        ).select(db.logs_req_item.quantity,
                                 db.logs_req_item.quantity_commit,
                                 db.logs_req_item.quantity_transit,
                                 db.logs_req_item.quantity_fulfil,
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
        db.logs_req[req_id] = status_update  
            
    s3xrc.model.configure(table, onaccept=logs_req_item_onaccept)

    #==========================================================================
    # Commit
    
    resourcename = "commit"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("datetime",
                                  "datetime",
                                  label = T("Date")),
                            logs_req_id(),                            
                            Field("date_available",
                                  "date",
                                  label = T("Date Available")),
                            inventory_store_id(label = T("By Store")),
                            inventory_store_id("for_inventory_store_id",
                                               label = T("For Store")),                                 
                            person_id("committer_id",
                                      label = T("Requester") ),
                            comments(),
                            migrate=migrate, *s3_meta_fields())

    # -------------------------------------------------------------------------
    # CRUD strings
    ADD_LOGS_COMMIT = T("Make Commitment")
    LIST_LOGS_COMMIT = T("List Commitments")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_LOGS_COMMIT,
        title_display = T("Commitment Details"),
        title_list = LIST_LOGS_COMMIT,
        title_update = T("Edit Commitment"),
        title_search = T("Search Commitments"),
        subtitle_create = ADD_LOGS_COMMIT,
        subtitle_list = T("Commitments"),
        label_list_button = LIST_LOGS_COMMIT,
        label_create_button = ADD_LOGS_COMMIT,
        label_delete_button = T("Delete Commitment"),
        msg_record_created = T("Commitment Added"),
        msg_record_modified = T("Commitment Updated"),
        msg_record_deleted = T("Commitment Canceled"),
        msg_list_empty = T("No Commitments"))

    # -----------------------------------------------------------------------------
    def logs_commit_represent(id):
        if id:
            r = db(db.logs_commit.id == id).select(db.logs_commit.datetime,
                                                   db.logs_commit.inventory_store_id,
                                                   limitby=(0, 1)).first()
            return "%s - %s" % \
                    ( inventory_store_represent(r.inventory_store_id),
                      r.datetime
                     )
        else:
            return NONE

    # -----------------------------------------------------------------------------
    # Reusable Field
    logs_commit_id = S3ReusableField("logs_commit_id", db.logs_commit, sortby="date",
                                  requires = IS_NULL_OR( \
                                                 IS_ONE_OF(db,
                                                           "logs_commit.id",
                                                           logs_commit_represent,
                                                           orderby="logs_commit.date",
                                                           sort=True)),
                                  represent = logs_commit_represent,
                                  label = T("Commitment"),
                                  #comment = DIV(A(ADD_DISTRIBUTION, _class="colorbox", _href=URL(r=request, c="logs", f="distrib", args="create", vars=dict(format="popup")), _target="top", _title=ADD_DISTRIBUTION),
                                  #          DIV( _class="tooltip", _title=T("Distribution") + "|" + T("Add Distribution."))),
                                  ondelete = "RESTRICT"
                                  )

    #------------------------------------------------------------------------------
    # Commitment as a component of Inventory Store
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict( inventory_store = \
                                               "inventory_store_id" ) )

    #------------------------------------------------------------------------------
    # Redirect to the Items tabs after creation
    s3xrc.model.configure(table,
                          create_next = URL(r=request, c="logs", f="commit", args=["[id]", "commit_item"]))
    
    #------------------------------------------------------------------------------
    # Update owned_by_role to the store's owned_by_role    
    s3xrc.model.configure(
        table, 
        onaccept = lambda form, tablename = tablename : store_resource_onaccept(form, tablename)
    )      

    #==============================================================================
    # Commitment Items
    #
    resourcename = "commit_item"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            logs_commit_id(),
                            #item_id(),
                            logs_req_item_id(),
                            item_packet_id(),
                            Field("quantity", 
                                  "double",
                                  notnull = True),                          
                            comments(),
                            migrate=migrate, *s3_meta_fields())
    
    #packet_quantity virtual field
    table.virtualfields.append(item_packet_virtualfields(tablename = tablename))    

    # CRUD strings
    ADD_LOGS_COMMIT_ITEM = T("Commitment Item")
    LIST_LOGS_COMMIT_ITEM = T("List Commitment Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_LOGS_COMMIT_ITEM,
        title_display = T("Commitment Item Details"),
        title_list = LIST_LOGS_COMMIT_ITEM,
        title_update = T("Edit Commitment Item"),
        title_search = T("Search Commitment Items"),
        subtitle_create = T("Add New Commitment Item"),
        subtitle_list = T("Commitment Items"),
        label_list_button = LIST_LOGS_COMMIT_ITEM,
        label_create_button = ADD_LOGS_COMMIT_ITEM,
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
                              joinby=dict( logs_commit = "logs_commit_id" ) 
                              )       
    
    #------------------------------------------------------------------------------
    def logs_commit_item_onaccept(form):
        # try to get req_item_id from the form
        req_item_id = 0
        if form:
            req_item_id = form.vars.get("req_item_id")  
        if not req_item_id:
            commit_item_id = session.rcvars.logs_commit_item
            r_commit_item = db.logs_commit_item[commit_item_id]
        
            req_item_id = r_commit_item.logs_req_item_id
        
        commit_items =  db( (db.logs_commit_item.logs_req_item_id == req_item_id) & \
                            (db.logs_commit_item.deleted == False) 
                            ).select(db.logs_commit_item.quantity ,
                                     db.logs_commit_item.item_packet_id 
                                     )
        quantity_commit = 0
        for commit_item in commit_items:
            quantity_commit += commit_item.quantity * commit_item.packet_quantity
        
        r_req_item = db.logs_req_item[req_item_id]
        quantity_commit = quantity_commit / r_req_item.packet_quantity
        db.logs_req_item[req_item_id] = dict(quantity_commit = quantity_commit)
        
        #Update status_commit of the req record
        session.rcvars.logs_req = r_req_item.logs_req_id
        logs_req_item_onaccept(None)             
        
     
    s3xrc.model.configure(table, onaccept = logs_commit_item_onaccept )          

    #==============================================================================
    # Received (In/Receive / Donation / etc)
    #
    
    logs_recv_type = {0:NONE,
                      1:"Another Store",
                      2:"Donation",
                      3:"Supplier"}
    
    LOGS_STATUS_IN_PROCESS = 0
    LOGS_STATUS_RECEIVED   = 1
    LOGS_STATUS_SENT       = 2
    
    logs_status = { LOGS_STATUS_IN_PROCESS: T("In Process"),
                    LOGS_STATUS_RECEIVED:   T("Received"),
                    LOGS_STATUS_SENT:       T("Sent")
                   }    
     
    resourcename = "recv"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("datetime",
                                  "datetime",
                                  label = "Date Received",
                                  writable = False,
                                  readable = False #unless the record is locked
                                  ),
                            inventory_store_id(label = T("By Warehouse")),
                            Field("type",
                                  "integer",
                                  requires = IS_NULL_OR(IS_IN_SET(logs_recv_type)),
                                  represent = lambda type: logs_recv_type[type] if type else NONE,
                                  default = 0,
                                  ),
                            organisation_id("from_organisation_id",
                                            label = T("From Organisation")),
                            location_id("from_location_id",
                                        label = T("From Location")),
                            Field("from_person"), #Text field, because lookup to pr_person record is unnecessary complex workflow                                              
                            Field("status", 
                                  "integer",
                                  requires = IS_NULL_OR(IS_IN_SET(logs_status)),
                                  represent = lambda status: logs_status[status],       
                                  default = LOGS_STATUS_IN_PROCESS,                           
                                 # writable = False,
                                  ),
                            person_id(name = "recipient_id",
                                      label = T("Received By")),
                            comments(),
                            migrate=migrate, *s3_meta_fields()
                            )

    # -----------------------------------------------------------------------------
    # CRUD strings
    ADD_LOGS_IN = T("Receive Shipment")
    LIST_LOGS_IN = T("List Received Shipments")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_LOGS_IN,
        title_display = T("Received Shipment Details"),
        title_list = LIST_LOGS_IN,
        title_update = T("Edit Received Shipment"),
        title_search = T("Search Received Shipments"),
        subtitle_create = ADD_LOGS_IN,
        subtitle_list = T("Received Shipments"),
        label_list_button = LIST_LOGS_IN,
        label_create_button = ADD_LOGS_IN,
        label_delete_button = T("Delete Received Shipment"),
        msg_record_created = T("Shipment Created"),
        msg_record_modified = T("Received Shipment updated"),
        msg_record_deleted = T("Received Shipment canceled"),
        msg_list_empty = T("No Received Shipments")
    )

    # -----------------------------------------------------------------------------
    def logs_recv_represent(id):
        if id:
            logs_recv_row = db(db.logs_recv.id == id).\
                              select(db.logs_recv.datetime,
                                     db.logs_recv.from_location_id,
                                     limitby=(0, 1))\
                              .first()
            return SPAN( shn_gis_location_represent( logs_recv_row.from_location_id),
                         " - ",
                        logs_recv_row.datetime)
        else:
            return NONE

    # -----------------------------------------------------------------------------
    # Reusable Field
    logs_recv_id = S3ReusableField("logs_recv_id", db.logs_recv, sortby="datetime",
                                 requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                 "logs_recv.id",
                                                                 logs_recv_represent,
                                                                 orderby="logs_recv.datetime", sort=True)),
                                 represent = logs_recv_represent,
                                 label = T("Receive Shipment"),
                                 #comment = DIV(A(ADD_DISTRIBUTION, _class="colorbox", _href=URL(r=request, c="logs", f="distrib", args="create", vars=dict(format="popup")), _target="top", _title=ADD_DISTRIBUTION),
                                 #          DIV( _class="tooltip", _title=T("Distribution") + "|" + T("Add Distribution."))),
                                 ondelete = "RESTRICT"
                                 )

    #------------------------------------------------------------------------------
    # Logs In as a component of Inventory Store
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict( inventory_store ="inventory_store_id" ) )

    #------------------------------------------------------------------------------
    # Redirect to the Items tabs after creation
    s3xrc.model.configure(table,
                          create_next = URL(r=request, c="logs", f="recv", args=["[id]", "recv_item"]))
    
    #------------------------------------------------------------------------------
    # Update owned_by_role to the store's owned_by_role    
    s3xrc.model.configure(
        table, 
        onaccept = lambda form, tablename = tablename : store_resource_onaccept(form, tablename)
    )      

    #==============================================================================
    # In (Receive / Donation / etc) Items
    #
    resourcename = "recv_item"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            logs_recv_id(),
                            item_id(),
                            item_packet_id(),
                            Field("quantity", "double",
                                  notnull = True),
                            comments(),
                            logs_req_item_id(readable = False,
                                             writable = False),
                            migrate=migrate, *s3_meta_fields())
        
    #packet_quantity virtual field
    table.virtualfields.append(item_packet_virtualfields(tablename = tablename))      

    # CRUD strings
    ADD_LOGS_IN_ITEM = T("Add Item to Shipment")
    LIST_LOGS_IN_ITEMS = T("List Received Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_LOGS_IN_ITEM,
        title_display = T("Received Item Details"),
        title_list = LIST_LOGS_IN_ITEMS,
        title_update = T("Edit Received Item"),
        title_search = T("Search Received Items"),
        subtitle_create = T("Add New Received Item"),
        subtitle_list = T("Shipment Items"),
        label_list_button = LIST_LOGS_IN_ITEMS,
        label_create_button = ADD_LOGS_IN_ITEM,
        label_delete_button = T("Delete Received Item"),
        msg_record_created = T("Item added to shipment"),
        msg_record_modified = T("Received Item updated"),
        msg_record_deleted = T("Received Item deleted"),
        msg_list_empty = T("No Received Items currently registered"))

    #------------------------------------------------------------------------------
    # In Items as component of In
    # In Items as a component of Items
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(logs_recv = "logs_recv_id",
                                          supply_item = "item_id")) 

    #==============================================================================
    def shn_logs_send_store_id(r):
        if r.to_location_id:
            return shn_get_db_field_value(db,
                                          "inventory_store",
                                          "id",
                                          r.to_location_id,
                                          "location_id")
        else:
            return None        

    #==============================================================================
    # Send (Outgoing / Dispatch / etc)
    #        
    resourcename = "send"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field( "datetime", 
                                   "datetime",
                                   label = "Date Sent"),
                            inventory_store_id( label = T("From Warehouse")),
                            location_id( "to_location_id",
                                         label = T("To Location") ),
                            inventory_store_id( "to_inventory_store_id",
                                                label = T("To Warehouse"),
                                                compute = shn_logs_send_store_id,
                                                readable = False),                                   
                            Field("status", 
                                  "integer",
                                  requires = IS_NULL_OR(IS_IN_SET(logs_status)),
                                  represent = lambda status: logs_status[status],       
                                  default = LOGS_STATUS_IN_PROCESS,                           
                                  writable = False,
                                  ),
                            person_id(name = "recipient_id",
                                      label = T("To Person")),
                            comments(),
                            migrate=migrate, *s3_meta_fields())
    
    # -----------------------------------------------------------------------------
    # CRUD strings
    ADD_LOGS_OUT = T("Add New Shipment to Send")
    LIST_LOGS_OUT = T("List Shipments")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_LOGS_OUT,
        title_display = T("Shipment Details"),
        title_list = LIST_LOGS_OUT,
        title_update = T("Edit Shipment to Send"),
        title_search = T("Search Sent Shipments"),
        subtitle_create = ADD_LOGS_OUT,
        subtitle_list = T("Shipments"),
        label_list_button = LIST_LOGS_OUT,
        label_create_button = ADD_LOGS_OUT,
        label_delete_button = T("Delete Sent Shipment"),
        msg_record_created = T("Shipment Created"),
        msg_record_modified = T("Sent Shipment updated"),
        msg_record_deleted = T("Sent Shipment canceled"),
        msg_list_empty = T("No Sent Shipments"))

    # -----------------------------------------------------------------------------
    def logs_send_represent(id):
        if id:
            logs_send_row = db(db.logs_send.id == id).\
                              select(db.logs_send.datetime,
                                     db.logs_send.to_location_id,
                                     limitby=(0, 1))\
                              .first()
            return SPAN( shn_gis_location_represent( logs_send_row.to_location_id),
                         " - ",
                        logs_send_row.datetime)
        else:
            return NONE

    # -----------------------------------------------------------------------------
    # Reusable Field
    logs_send_id = S3ReusableField( "logs_send_id", db.logs_send, sortby="datetime",
                                    requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                    "logs_send.id",
                                                                    logs_send_represent,
                                                                    orderby="logs_send_id.datetime", sort=True)),
                                    represent = logs_send_represent,
                                    label = T("Send Shipment"),
                                    #comment = DIV(A(ADD_DISTRIBUTION, _class="colorbox", _href=URL(r=request, c="logs", f="distrib", args="create", vars=dict(format="popup")), _target="top", _title=ADD_DISTRIBUTION),
                                    #          DIV( _class="tooltip", _title=T("Distribution") + "|" + T("Add Distribution."))),
                                    ondelete = "RESTRICT"
                                    )

    #------------------------------------------------------------------------------
    # Logs Send added as a component of Inventory Store in controller
    # joinby inventory_store_id (send) OR to_inventory_store_id (incoming), depending on component tab

    #------------------------------------------------------------------------------
    # Redirect to the Items tabs after create & update
    url_logs_send_items = URL(r=request, c="logs", f="send", args=["[id]", "send_item"])
    s3xrc.model.configure(table,
                          create_next = url_logs_send_items,
                          update_next = url_logs_send_items
                          )
    
    #------------------------------------------------------------------------------
    # Update owned_by_role to the store's owned_by_role    
    s3xrc.model.configure(
        table, 
        onaccept = lambda form, tablename = tablename : store_resource_onaccept(form, tablename)
    )  
    
    #==============================================================================
    # Send (Outgoing / Dispatch / etc) Items
    #
    log_sent_item_status = {0: NONE,
                            1: "Invalid Quantity"
                            }

    resourcename = "send_item"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            logs_send_id(),
                            store_item_id(),
                            item_packet_id(),
                            Field("quantity", "double",
                                  notnull = True),
                            comments(),
                            Field("status",
                                  "integer",
                                  requires = IS_NULL_OR(IS_IN_SET(log_sent_item_status)),
                                  represent = lambda status: log_sent_item_status[status] if status else log_sent_item_status[0],
                                  writable = False),
                            logs_req_item_id(readable = False,
                                             writable = False),      
                            migrate=migrate, *s3_meta_fields())
    
    #packet_quantity virtual field
    table.virtualfields.append(item_packet_virtualfields(tablename = tablename))       

    # CRUD strings
    ADD_LOGS_OUT_ITEM = T("Add Item to Shipment")
    LIST_LOGS_OUT_ITEMS = T("List Sent Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_LOGS_OUT_ITEM,
        title_display = T("Sent Item Details"),
        title_list = LIST_LOGS_OUT_ITEMS,
        title_update = T("Edit Sent Item"),
        title_search = T("Search Sent Items"),
        subtitle_create = T("Add New Sent Item"),
        subtitle_list = T("Shipment Items"),
        label_list_button = LIST_LOGS_OUT_ITEMS,
        label_create_button = ADD_LOGS_OUT_ITEM,
        label_delete_button = T("Delete Sent Item"),
        msg_record_created = T("Item Added to Shipment"),
        msg_record_modified = T("Sent Item updated"),
        msg_record_deleted = T("Sent Item deleted"),
        msg_list_empty = T("No Sent Items currently registered"))

    #------------------------------------------------------------------------------
    # Send Items as component of Send
    # Send Items as a component of Items
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(logs_send = "logs_send_id",
                                          store_item = "store_item_id"))

#==============================================================================
