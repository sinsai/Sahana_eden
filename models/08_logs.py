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
            [T("Catalog Items"), False, URL(r=request, c="supply", f="item"),
            [
                [T("List"), False, URL(r=request, c="supply", f="item")],
                [T("Add"), False, URL(r=request, c="supply", f="item", args="create")],
            ]],
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

#==============================================================================
# Request
    resourcename = "req"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("request_date",
                                  "date",
                                  label = T("Date Requested")),
                            Field("require_date",
                                  "date",
                                  label = T("Date Required")),
                            inventory_store_id(label = T("Requested From Warehouse")),
                            location_id("by_location_id",
                                        label = T("Requested By Location")),
                            Field("status", "boolean"),
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
        msg_list_empty = T("No Request Shipments"))

    # -----------------------------------------------------------------------------
    def logs_req_represent(id):
        if id:
            logs_req_row = db(db.logs_req.id == id).\
                              select(db.logs_req.date,
                                     db.logs_req.from_location_id,
                                     limitby=(0, 1))\
                              .first()
            return "%s - %s" % (shn_gis_location_represent( \
                                logs_req_row.from_location_id),
                                logs_req_row.date)
        else:
            return NONE

    # -----------------------------------------------------------------------------
    # Reusable Field
    logs_req_id = S3ReusableField("logs_req_id", db.logs_req, sortby="name",
                                  requires = IS_NULL_OR( \
                                                 IS_ONE_OF(db,
                                                           "logs_req.id",
                                                           logs_req_represent,
                                                           orderby="logs_req_id.date",
                                                           sort=True)),
                                 represent = logs_req_represent,
                                 label = T("Receive Shipment"),
                                 #comment = DIV(A(ADD_DISTRIBUTION, _class="colorbox", _href=URL(r=request, c="logs", f="distrib", args="create", vars=dict(format="popup")), _target="top", _title=ADD_DISTRIBUTION),
                                 #          DIV( _class="tooltip", _title=T("Distribution") + "|" + T("Add Distribution."))),
                                 ondelete = "RESTRICT"
                                 )

    #------------------------------------------------------------------------------
    # Logs In as a component of Inventory Store
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict( inventory_store = \
                                               "inventory_store_id" ) )

    #------------------------------------------------------------------------------
    # Redirect to the Items tabs after creation
    s3xrc.model.configure(table,
                          create_next = URL(r=request, c="logs", f="req", args=["[id]", "req_item"]))

    #==============================================================================
    # Request Items
    #
    resourcename = "req_item"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            logs_req_id(),
                            item_id(),
                            item_packet_id(),
                            Field("quantity", 
                                  "double",
                                  notnull = True),
                            comments(),
                            migrate=migrate, *s3_meta_fields())

    # CRUD strings
    ADD_LOGS_REQUEST_ITEM = T("Request Item")
    LIST_LOGS_REQUEST_ITEM = T("List Request Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_LOGS_REQUEST_ITEM,
        title_display = T("Request Item Details"),
        title_list = LIST_LOGS_REQUEST_ITEM,
        title_update = T("Edit Request Item"),
        title_search = T("Search Request Items"),
        subtitle_create = T("Add New Request Item"),
        subtitle_list = T("Request Items"),
        label_list_button = LIST_LOGS_REQUEST_ITEM,
        label_create_button = ADD_LOGS_REQUEST_ITEM,
        label_delete_button = T("Delete Request Item"),
        msg_record_created = T("Request Item added"),
        msg_record_modified = T("Request Item updated"),
        msg_record_deleted = T("Request Item deleted"),
        msg_list_empty = T("No Request Items currently registered"))

    #------------------------------------------------------------------------------
    # Request Items as component of Request
    # Request Items as a component of Items
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(logs_req = "logs_req_id",
                                          supply_item = "item_id"))

#==============================================================================
# Received (In/Receive / Donation / etc)
#
    resourcename = "recv"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("datetime", "datetime",
                                  label = "Date"),
                            inventory_store_id(label = T("By Warehouse")),
                            location_id("from_location_id",
                                        label = T("From Location")),
                            Field("status", "boolean",
                                  writable = False),
                            person_id(name = "recipient_id",
                                      label = T("Received By")),
                            comments(),
                            migrate=migrate, *s3_meta_fields()
                            )
    
    table.status.represent = lambda status: T("Received") if status else T("In Process")
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
        msg_list_empty = T("No Received Shipments"))

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
                                                                 orderby="logs_recv_id.datetime", sort=True)),
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
                            migrate=migrate, *s3_meta_fields())

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
        msg_record_created = T("Received Item added"),
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
                            Field("datetime", "datetime",
                                  label = "Date"),
                            inventory_store_id(),
                            location_id("to_location_id",
                                        label = T("To Location") ),
                            Field("to_inventory_store_id",
                                  "integer",
                                  compute = shn_logs_send_store_id,
                                  readable = False),
                            Field("status", "boolean",
                                  writable = False),
                            person_id(name = "recipient_id"),
                            comments(),
                            migrate=migrate, *s3_meta_fields())

    table.status.represent = lambda status: T("Sent") if status else T("In Process")
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
    logs_send_id = S3ReusableField("logs_send_id", db.logs_send, sortby="datetime",
                                 requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                 "logs_send.id",
                                                                 logs_send_represent,
                                                                 orderby="logs_send_id.datetime", sort=True)),
                                 represent = logs_send_represent,
                                 label = T("Receive Shipment"),
                                 #comment = DIV(A(ADD_DISTRIBUTION, _class="colorbox", _href=URL(r=request, c="logs", f="distrib", args="create", vars=dict(format="popup")), _target="top", _title=ADD_DISTRIBUTION),
                                 #          DIV( _class="tooltip", _title=T("Distribution") + "|" + T("Add Distribution."))),
                                 ondelete = "RESTRICT"
                                 )

    #------------------------------------------------------------------------------
    # Logs Send  as a component of Inventory Store
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict( inventory_store ="inventory_store_id" ) )

    #------------------------------------------------------------------------------
    # Redirect to the Items tabs after creation
    s3xrc.model.configure(table,
                          create_next = URL(r=request, c="logs", f="send", args=["[id]", "send_item"]))

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
                            migrate=migrate, *s3_meta_fields())

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
