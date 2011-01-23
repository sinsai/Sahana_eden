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
    response.title = module_name
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
                rheader = DIV( TABLE(
                                   TR( TH( T("Date") + ": "),
                                       recv_record.datetime,
                                      ),
                                   TR( TH( T( "By" ) + ": "),
                                       shn_inventory_store_represent(recv_record.inventory_store_id),
                                       TH( T( "From" ) + ": "),
                                       shn_inventory_store_represent(recv_record.from_location_id),
                                      ),
                                   TR( TH( T("Comments") + ": "),
                                       TD(recv_record.comments, _colspan=3)
                                      ),
                                     )
                                )                            
               
                if not recv_record.status: 
                    #Shipment not recv
                    recv_btn = A( T("Receive Items"),
                                  _href = URL(r = request,
                                              c = "logs",
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
                                    
                rheader_tabs = shn_rheader_tabs( r,
                                                 [(T("Edit Details"), None),
                                                  (T("Items"), "recv_item"),
                                                  ]
                                                 )
                rheader.append(rheader_tabs)                 
               
                return rheader
    return None
#------------------------------------------------------------------------------
def recv_process():
    recv_id = request.args[0]
    recv_record = db.logs_recv[recv_id]
    inventory_store_id = recv_record.inventory_store_id

    #Get Recv & Store Items to compare
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
            
        #Update Store Item
        db.inventory_store_item[store_item_id] = item
        
        
    #Update recv record
    db.logs_recv[recv_id] = dict(datetime = request.utcnow,
                                 status = True ) 

    response.confirmation = T("Received Items added to Warehouse Items")

    #Go to the Warehouse which has received these items
    redirect(URL(r = request,
                 c = "inventory",
                 f = "store",
                 args = [inventory_store_id, "store_item"]
                 )
             )
#==============================================================================
class QUANTITY_ITEM_IN_STORE:
    def __init__(self, 
                 store_item_id,
                 item_packet_id):
        self.store_item_id = store_item_id
        self.item_packet_id = item_packet_id
    def __call__(self, value):
        error = "Invalid Quantity" # @todo: better error catching
        store_item_record = db( (db.inventory_store_item.id == self.store_item_id) & \
                                (db.inventory_store_item.item_packet_id == db.supply_item_packet.id)
                               ).select(db.inventory_store_item.quantity,
                                        db.supply_item_packet.quantity,
                                        db.supply_item_packet.name,
                                        limitby = [0,1]).first() # @todo: this should be a virtual field
        if store_item_record and value:
            send_quantity = float(value) * shn_get_db_field_value(db,
                                                           "supply_item_packet",
                                                           "quantity",                                                           
                                                           self.item_packet_id   
                                                           )       
            store_quantity = store_item_record.inventory_store_item.quantity * \
                             store_item_record.supply_item_packet.quantity
            if send_quantity > store_quantity:
                return (value, 
                        "Only %s %s (%s) in the store." %
                        (store_quantity,
                         store_item_record.supply_item_packet.name,
                         store_item_record.supply_item_packet.quantity)    
                        )
            else:
                return (value, None)
        else:
            return (value, error)
    def formatter(self, value):
        return value
#------------------------------------------------------------------------------
def send():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    #Set Validator for checking against the number of items in the warehouse
    if (request.vars.store_item_id):
        db.logs_send_item.quantity.requires = QUANTITY_ITEM_IN_STORE(request.vars.store_item_id, 
                                                                     request.vars.item_packet_id)
    
    def prep(r):
        # If component view
        if r.record and r.record.get("inventory_store_id"):        
            #Restrict to items from this warehouse only
            db.logs_send_item.store_item_id.requires = IS_ONE_OF(db, 
                                                                 "inventory_store_item.id", 
                                                                 shn_inventory_store_item_represent, 
                                                                 orderby="inventory_store_item.id", 
                                                                 sort=True,
                                                                 filterby = "inventory_store_id",
                                                                 filter_opts = [r.record.inventory_store_id]
                                                                 )
    
            js_store_quantity = SCRIPT("""
            function ItemPacketIDChange() {       
                $('#TotalQuantity').remove();           
                $('[name = "quantity"]').after('<img src="/eden/static/img/ajax-loader.gif" id="store_quantity_loader_img">');    
                     
                url = '/eden/inventory/store_item_quantity/' 
                url += $('[name = "store_item_id"]').val();
                $.getJSON(url, function(data) {
                    /* @todo Error Checking */
                    var StoreQuantity = data.inventory_store_item.quantity; 
                    var StorePacketQuantity = data.supply_item_packet.quantity; 
                    
                    var PacketName = $('[name = "item_packet_id"] option:selected').text();
                    var re = /\(([0-9])*\)/;
                    var PacketQuantity = re.exec(PacketName)[1];
                    
                    var Quantity = (StoreQuantity * StorePacketQuantity) / PacketQuantity;
                                    
                    TotalQuantity = '<span id = "TotalQuantity"> / ' + Quantity.toFixed(2) + ' ' + PacketName + ' in store.</span>';
                    $('#store_quantity_loader_img').remove();
                    $('[name = "quantity"]').after(TotalQuantity);
                });
            };
            
            $('[name = "item_packet_id"]').change(ItemPacketIDChange);
            """ % dict(inventory_store_id = r.record.inventory_store_id) )
            db.logs_send_item.item_packet_id.comment.append(js_store_quantity)
        return True
        
    response.s3.prep = prep           
        
    output = s3_rest_controller(module,
                                resource,
                                rheader=shn_logs_send_rheader)
    return output
#------------------------------------------------------------------------------
def shn_logs_send_rheader(r):
    """ Resource Header for Out """

    if r.representation == "html":
        if r.name == "send":
            send_record = r.record
            if send_record:
                rheader = DIV( TABLE(
                                   TR( TH( T("Date") + ": "),
                                       send_record.datetime,
                                      ),
                                   TR( TH( T( "From" ) + ": "),
                                       shn_inventory_store_represent(send_record.inventory_store_id),
                                       TH( T( "To" ) + ": "),
                                       shn_gis_location_represent(send_record.to_location_id),
                                      ),
                                   TR( TH( T("Comments") + ": "),
                                       TD(send_record.comments, _colspan=3)
                                      )
                                     )                              
                                )
                
                if not send_record.status: 
                    #Shipment not recv
                    send_btn = A( T("Send Shipment"),
                                  _href = URL(r = request,
                                              c = "logs",
                                              f = "send_process",
                                              args = [send_record.id]
                                              ),
                                  _id = "send_process",
                                  _class = "action-btn"
                                  )
                    
                    send_btn_confirm = SCRIPT("S3ConfirmClick('#send_process','%s')" 
                                              % T("Do you want to send this shipment?") )
                    rheader.append(send_btn)
                    rheader.append(send_btn_confirm)     

                rheader.append(shn_rheader_tabs( r,
                                                 [(T("Edit Details"), None),
                                                  (T("Items"), "send_item"),
                                                  ]
                                                 )
                               )                               
                return rheader
    return None
#------------------------------------------------------------------------------
def send_process():
    send_id = request.args[0]
    send_record = db.logs_send[send_id]
    inventory_store_id = send_record.inventory_store_id
    cancel_send = False
    invalid_send_item_ids = []

    #Get Send & Store Items
    send_items = db( ( db.logs_send_item.logs_send_id == send_id ) & \
                     ( db.logs_send_item.store_item_id == db.inventory_store_item.id) & \
                     ( db.logs_send_item.item_packet_id == db.supply_item_packet.id) & \
                     ( db.logs_send_item.deleted == False ) & \
                     ( db.inventory_store_item.deleted == False ) )\
                 .select(db.logs_send_item.id,
                         db.logs_send_item.quantity,
                         db.supply_item_packet.quantity,
                         db.inventory_store_item.id,
                         db.inventory_store_item.quantity,
                         db.inventory_store_item.packet_quantity,
                         left=db.inventory_store_item.on(db.logs_send_item.store_item_id == db.inventory_store_item.id), #To ensure that all send items are selected, even if the store item has been deleted.
                         )

    for send_item in send_items:
        send_item_id = send_item.logs_send_item.id
        store_item_id = send_item.inventory_store_item.id
        
        store_item_quantity = send_item.inventory_store_item.quantity * \
                        send_item.inventory_store_item.packet_quantity
        
        send_item_quantity = send_item.logs_send_item.quantity * \
                        send_item.supply_item_packet.quantity
                        
        if send_item_quantity > store_item_quantity:
            #This shipment is invalid
            #flag this item
            invalid_send_item_ids.append(send_item_id)            
            
            #Cancel this processing
            cancel_send = True
        else:
            #Update the Store Item Quantity
            new_store_quantity = ( store_item_quantity - send_item_quantity) / \
                                 send_item.inventory_store_item.packet_quantity
            db.inventory_store_item[store_item_id] = dict(quantity = new_store_quantity)
            
    if cancel_send:        
        db.rollback()
        for invalid_send_item_id in invalid_send_item_ids:
            db.logs_send_item[invalid_send_item_id] = dict(status = 1)
            
        response.error = T("There are not sufficient items in the store to send this shipment") #@todo: list the items and the quantities in the error message
        redirect(URL(r = request,
                     c = "logs",
                     f = "send",
                     args = [send_id, "send_item"]
                     )
                 )      
    else:
        #Update Send record
        db.logs_send[send_id] = dict(datetime = request.utcnow,
                                     status = True )        
        response.confirmation = T("Items Sent from Warehouse")                  
        #Go to the Warehouse which has sent these items
        redirect(URL(r = request,
                     c = "inventory",
                     f = "store",
                     args = [inventory_store_id, "store_item"]
                     )
                 )                    
#==============================================================================#
def recv_sent():
    send_id = request.args[0]
    
    r_send = db.logs_send[send_id]
    
    inventory_store_id = r_send.to_inventory_store_id
    
    from_location_id = shn_get_db_field_value(db,
                                              "inventory_store",
                                              "location_id",
                                              r_send.inventory_store_id )
    #create a new recv record
    recv_id = db.logs_recv.insert(inventory_store_id = inventory_store_id,
                                  from_location_id = from_location_id)
    
    sent_items = db( (db.logs_send_item.logs_send_id == send_id) & \
                     (db.logs_send_item.store_item_id == db.inventory_store_item.id) & \
                     (db.logs_send_item.deleted == False) 
                     ).select(db.inventory_store_item.item_id,
                              db.logs_send_item.item_packet_id,
                              db.logs_send_item.quantity)   
    
    #copy items from send to recv
    for sent_item in sent_items:
        db.logs_recv_item.insert(logs_recv_id = recv_id,
                                 item_id = sent_item.inventory_store_item.item_id,
                                 item_packet_id = sent_item.logs_send_item.item_packet_id,
                                 quantity = sent_item.logs_send_item.quantity)
    
    #redirect to rec    
    redirect(URL(r = request,
                 c = "logs",
                 f = "recv",
                 args = [recv_id]
                 )
             )     