# -*- coding: utf-8 -*-

"""
    Logistics Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-09-02

    Distribution, Shipments
"""

module = request.controller

response.menu_options = logs_menu

#==============================================================================
def index():

    """
        Home page for the Logs Application
        @ToDo: Add Dashboard functionality
    """

    module_name = deployment_settings.modules[module].name_nice
    return dict(module_name=module_name)

#==============================================================================
def req():
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    output = s3_rest_controller(module,
                                resource,
                                rheader=shn_logs_req_rheader)
    return output
#------------------------------------------------------------------------------
def shn_logs_req_rheader(r):
    """ Resource Header for Requests """

    if r.representation == "html":
        if r.name == "req":
            req_record = r.record
            if req_record:
                rheader_tabs = shn_rheader_tabs( r,
                                                 [(T("Edit Details"), None),
                                                  (T("Items"), "req_item"),
                                                  ]
                                                 )
                rheader = DIV( TABLE(
                                   TR( TH( T("Date Requested") + ": "),
                                       req_record.request_date,
                                       TH( T("Date Required") + ": "),
                                       req_record.require_date,
                                      ),
                                   TR( TH( T("From Location") + ": "),
                                       shn_gis_location_represent(req_record.by_location_id),
                                       TH( T("Requested From Warehouse") + ": "),
                                       shn_inventory_store_represent(req_record.inventory_store_id),
                                      ),
                                   TR( TH( T("Comments") + ": "),
                                       TD(req_record.comments, _colspan=3)
                                      ),
                                     ),
                                rheader_tabs
                                )
                return rheader
    return None

#=============================================================================
def recv():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    output = s3_rest_controller(module,
                                resource,
                                rheader=shn_logs_recv_rheader)
    return output
#------------------------------------------------------------------------------
def shn_logs_recv_rheader(r):
    """ Resource Header for Receiving """

    if r.representation == "html":
        if r.name == "recv":
            recv_record = r.record
            if recv_record:
                recv_btn = A( T("Receive Items"),
                              _href = URL(r = request,
                                          c = "logs",
                                          f = "recv_process",
                                          args = [recv_record.id]
                                          ),
                              _class = "action-btn"
                              )
                rheader_tabs = shn_rheader_tabs( r,
                                                 [(T("Edit Details"), None),
                                                  (T("Items"), "recv_item"),
                                                  ]
                                                 )
                rheader = DIV( TABLE(
                                   TR( TH( T("Date") + ": "),
                                       recv_record.date,
                                      ),
                                   TR( TH( T( "By" ) + ": "),
                                       shn_inventory_store_represent(recv_record.inventory_store_id),
                                       TH( T( "From" ) + ": "),
                                       shn_inventory_store_represent(recv_record.from_location_id),
                                      ),
                                   TR( TH( T("Comments") + ": "),
                                       TD(recv_record.comments, _colspan=3)
                                      ),
                                     ),
                                recv_btn,
                                rheader_tabs
                                )
                return rheader
    return None
#------------------------------------------------------------------------------
def recv_process():
    recv_id = request.args[0]
    recv_record = db.logs_recv[recv_id]
    inventory_store_id = recv_record.inventory_store_id


    recv_items = db( ( db.logs_recv_item.logs_recv_id == recv_id ) & \
                     ( db.logs_recv_item.item_packet_id == db.supply_item_packet.id) &
                     ( db.logs_recv_item.deleted == False ) )\
                 .select(db.logs_recv_item.item_id,
                         db.logs_recv_item.quantity,
                         db.logs_recv_item.item_packet_id,
                         db.supply_item_packet.quantity,
                         )
    store_items = db( ( db.inventory_store_item.inventory_store_id == inventory_store_id ) & \
                      ( db.inventory_store_item.item_packet_id == db.supply_item_packet.id) & \
                      ( db.inventory_store_item.deleted == False ) )\
                  .select(db.inventory_store_item.id,
                          db.inventory_store_item.item_id,
                          db.inventory_store_item.quantity,
                          db.supply_item_packet.quantity)

    store_items_dict = store_items.as_dict( key = "inventory_store_item.item_id")

    for recv_item in recv_items:
        recv_item_id = recv_item.logs_recv_item.item_id
        if recv_item_id in store_items_dict.keys():
            #This item already exists in the store, and the quantity must be incremeneted
            store_item = Storage(store_items_dict[recv_item_id])
            store_item_id = store_item.inventory_store_item["id"]

            #convert the recv items packet into the store item packet
            quantity = store_item.inventory_store_item["quantity"] + \
                       (recv_item.supply_item_packet.quantity / \
                        store_item.supply_item_packet["quantity"]) * \
                        recv_item.logs_recv_item.quantity
            item = dict(quantity = quantity)
        else:
            #This item must be added to the store
            store_item_id = 0
            item = dict( inventory_store_id = inventory_store_id,
                         item_id = recv_item.logs_recv_item.item_id,
                         quantity = recv_item.logs_recv_item.quantity,
                         item_packet_id = recv_item.logs_recv_item.item_packet_id
                         )

        db.inventory_store_item[store_item_id] = item

    response.message = T("Received Items added to Warehouse Items")

    #Go to the Warehouse which has received these items
    redirect(URL(r = request,
                 c = "inventory",
                 f = "store",
                 args = [inventory_store_id, "store_item"]
                 )
             )

#==============================================================================
def send():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    output = s3_rest_controller(module,
                                resource,
                                rheader=shn_logs_send_rheader)
    return output
#------------------------------------------------------------------------------
def shn_logs_send_rheader(r):
    """ Resource Header for Out """

    if r.representation == "html":
        if r.name == "send":
            req_record = r.record
            if req_record:
                rheader_tabs = shn_rheader_tabs( r,
                                                 [(T("Edit Details"), None),
                                                  (T("Items"), "send_item"),
                                                  ]
                                                 )
                rheader = DIV( TABLE(
                                   TR( TH( T("Date") + ": "),
                                       req_record.date,
                                      ),
                                   TR( TH( T( "From" ) + ": "),
                                       shn_inventory_store_represent(req_record.inventory_store_id),
                                       TH( T( "To" ) + ": "),
                                       shn_gis_location_represent(req_record.to_location_id),
                                      ),
                                   TR( TH( T("Comments") + ": "),
                                       TD(req_record.comments, _colspan=3)
                                      ),
                                     ),
                                rheader_tabs
                                )
                return rheader
    return None

#==============================================================================
