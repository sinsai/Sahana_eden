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
    resourcename = request.function
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]
    
    def postp(r, output):
        if r.component_name == "req_item":
            #@todo create a function to add static JS & use min if available
            response.js = SCRIPT(_src="/%s/static/scripts/S3/S3.logs.js" % request.application ) 
        return output   
            
    response.s3.postp = postp         
    
    inventory_store_id = shn_get_db_field_value(db,
                                                "inventory_store_user",
                                                "inventory_store_id",                                                           
                                                auth.user_id,   
                                                "user_id"
                                                ) 
    
    req_actions = [dict(url = str( URL( r=request,
                                        c = "logs",
                                        f = "req",
                                        args = ["[id]","req_item"]                                  
                                       )
                                   ),
                        _class = "action-btn",
                        label = str(T("Items")),
                        ),
                   dict(url = str(URL( r=request,
                                       c = "logs",
                                       f = "commit_req",
                                       args = ["[id]"],
                                       vars = {"inventory_store_id": inventory_store_id}
                                      )
                                       ),
                        _class = "action-btn",
                        label = str(T("Commit")),
                        ),
                    ]
       
    output = s3_rest_controller( module,
                                 resourcename,
                                 rheader=shn_logs_req_rheader)
    
    if response.s3.actions:
        response.s3.actions += req_actions
    else:
        response.s3.actions = req_actions    
          
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
                                       req_record.date,
                                       TH( T("Date Required") + ": "),
                                       req_record.date_required,
                                      ),
                                   TR( TH( T("Requested By Warehouse") + ": "),
                                       inventory_store_represent(req_record.inventory_store_id),
                                      ),
                                   TR( TH( T("Commit. Status") + ": "),
                                       log_req_status_dict.get(req_record.commit_status),
                                       TH( T("Transit. Status") + ": "),
                                       log_req_status_dict.get(req_record.transit_status),
                                       TH( T("Fulfil. Status") + ": "),
                                       log_req_status_dict.get(req_record.fulfil_status)
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
def commit():
    resourcename = request.function
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]
    output = s3_rest_controller( module,
                                 resourcename,
                                 rheader=shn_logs_commit_rheader)
    return output
#------------------------------------------------------------------------------
def shn_logs_commit_rheader(r):
    """ Resource Header for Commitments """

    if r.representation == "html":
        if r.name == "commit":
            commit_record = r.record
            if commit_record:
                rheader_tabs = shn_rheader_tabs( r,
                                                 [(T("Edit Details"), None),
                                                  (T("Items"), "commit_item"),
                                                  ]
                                                 )
                rheader = DIV( TABLE( TR( TH( T("Date") + ": "),
                                           commit_record.datetime,
                                           TH( T("Date Avaialble") + ": "),
                                           commit_record.date_available,
                                          ),
                                       TR( TH( T("By Warehouse") + ": "),
                                           inventory_store_represent(commit_record.inventory_store_id),
                                           TH( T("For Warehouse") + ": "),
                                           inventory_store_represent(commit_record.for_inventory_store_id),
                                          ),
                                       TR( TH( T("Comments") + ": "),
                                           TD(commit_record.comments, _colspan=3)
                                          ),
                                         ),                                                                 
                                        )
                
                send_btn = A( T("Send Items"),
                              _href = URL(r = request,
                                          c = "logs",
                                          f = "send_commit",
                                          args = [commit_record.id]
                                          ),
                              _id = "send_commit",
                              _class = "action-btn"
                              )
                
                send_btn_confirm = SCRIPT("S3ConfirmClick('#send_commit','%s')" 
                                          % T("Do you want to send these Committed items?") )
                rheader.append(send_btn)
                rheader.append(send_btn_confirm)    
                
                rheader.append(rheader_tabs) 
                        
                return rheader
    return None

#=============================================================================
def recv():
    """ RESTful CRUD controller """
    resourcename = request.function
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]
    output = s3_rest_controller(module,
                                resourcename,
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
                                       inventory_store_represent(recv_record.inventory_store_id),
                                       TH( T( "From" ) + ": "),
                                       shn_gis_location_represent(recv_record.from_location_id),
                                      ),
                                   TR( TH( T("Comments") + ": "),
                                       TD(recv_record.comments, _colspan=3)
                                      ),
                                     )
                                )                            
               
                if recv_record.status == LOGS_STATUS_IN_PROCESS: 
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
def recv_item():
    """ RESTful CRUD controller """
    resourcename = request.function
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]
    output = s3_rest_controller(module,
                                resourcename,
                                )
    return output

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
    resourcename = request.function
    tablename = "%s_%s" % (module, resourcename)
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
                $('[name = "quantity"]').after('<div id="store_quantity_ajax_throbber" class="ajax_throbber" style="float:right"/>'); 
                     
                url = '/eden/inventory/store_item_quantity/' 
                url += $('[name = "store_item_id"]').val();
                $.getJSON(url, function(data) {
                    /* @todo Error Checking */
                    var StoreQuantity = data.inventory_store_item.quantity; 
                    var StorePacketQuantity = data.supply_item_packet.quantity; 
                    
                    var PacketName = $('[name = "item_packet_id"] option:selected').text();
                    var re = /\(([0-9]*)/;
                    var PacketQuantity = re.exec(PacketName)[1];
                    
                    var Quantity = (StoreQuantity * StorePacketQuantity) / PacketQuantity;
                                    
                    TotalQuantity = '<span id = "TotalQuantity"> / ' + Quantity.toFixed(2) + ' ' + PacketName + ' in store.</span>';
                    $('#store_quantity_ajax_throbber').remove();
                    $('[name = "quantity"]').after(TotalQuantity);
                });
            };
            
            $('[name = "item_packet_id"]').change(ItemPacketIDChange);
            """ % dict(inventory_store_id = r.record.inventory_store_id) )
            db.logs_send_item.item_packet_id.comment.append(js_store_quantity)
        return True
        
    response.s3.prep = prep           
        
    output = s3_rest_controller(module,
                                resourcename,
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
                                       inventory_store_represent(send_record.inventory_store_id),
                                       TH( T( "To" ) + ": "),
                                       shn_gis_location_represent(send_record.to_location_id),
                                      ),
                                   TR( TH( T("Comments") + ": "),
                                       TD(send_record.comments, _colspan=3)
                                      )
                                     )                              
                                )
                
                if send_record.status == LOGS_STATUS_IN_PROCESS: 
                    send_btn = A( T("Send Shipment"),
                                  _href = URL(r = request,
                                              c = "logs",
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

                rheader.append(shn_rheader_tabs( r,
                                                 [(T("Edit Details"), None),
                                                  (T("Items"), "send_item"),
                                                  ]
                                                 )
                               )                               
                return rheader
    return None

#------------------------------------------------------------------------------
def req_items_for_store(inventory_store_id, quantity_type):
    """
    used by recv_process & send_process
    returns a dict of unique req items (with min  db.logs_req.date_required | db.logs_req.date) 
    key = item_id
    @param inventory_store_id: The store to find the req_items from
    @param quantity_type: str ("commit", "transit" or "fulfil) The 
                          quantity type which will be used to determine if this item is still outstanding  
    """
    
    req_items = db( ( db.logs_req.inventory_store_id == inventory_store_id ) & \
                    ( db.logs_req.id == db.logs_req_item.logs_req_id) & \
                    ( db.logs_req_item.item_packet_id == db.logs_req_item.item_packet_id) & \
                    ( db.logs_req_item["quantity_%s" % quantity_type] < db.logs_req_item.quantity) & \
                    ( db.logs_req_item.deleted == False ) 
                   ).select(db.logs_req_item.id,
                            db.logs_req_item.logs_req_id,
                            db.logs_req_item.item_id,
                            db.logs_req_item.quantity,
                            db.logs_req_item["quantity_%s" % quantity_type],
                            db.logs_req_item.item_packet_id,
                            orderby = db.logs_req.date_required | db.logs_req.date, 
                            #groupby = db.logs_req_item.item_id
                            )  
                   
    # Because groupby doesn't follow the orderby remove any duplicate req_item 
    # req_items = req_items.as_dict( key = "logs_req_item.item_id") <- doensn't work 
    # @todo: Rows.as_dict function could be extended to enable this functionality instead 
    req_item_ids = []
    unique_req_items = Storage()
    for req_item in req_items:
        if req_item.item_id not in req_item_ids:
            #This item is not already in the dict 
            unique_req_items[req_item.item_id] = Storage( req_item.as_dict() )
            req_item_ids.append(req_item.item_id)    
            
    return unique_req_items      

shipment_to_req_type = dict( recv = "fulfil",
                             send = "transit",
                             commit = "commit"
                             )

def req_item_in_shipment( shipment_item,
                          shipment_type,
                          req_items,
                         ):
    """
    Checks if a shipment item is in a request and updates the shipment
    """    
  
    shipment_item_table = "logs_%s_item" % shipment_type
    try:
        item_id = shipment_item[shipment_item_table].item_id
    except:
        item_id = shipment_item.inventory_store_item.item_id
    
    #Check for req_items
    if item_id in req_items:      
        quantity_req_type = "quantity_%s" % shipment_to_req_type[shipment_type]
              
        #This item has been requested by this store
        req_item = req_items[item_id]
        req_item_id = req_item.id
        
        #Update the quantity_fulfil             
        #convert the shipment items quantity into the req_tem.quantity_fulfil (according to packet)
        quantity = req_item[quantity_req_type] + \
                   (shipment_item[shipment_item_table].packet_quantity / \
                    req_item.packet_quantity) * \
                    shipment_item[shipment_item_table].quantity    
        quantity = min(quantity, req_item.quantity)  #Cap at req. quantity  
        db.logs_req_item[req_item_id] = {quantity_req_type: quantity}      
                          
        #link the shipment_item to the req_item    
        db[shipment_item_table][shipment_item[shipment_item_table].id] = dict(logs_req_item_id = req_item_id)
        
        #Flag req record to update status_fulfil 
        return req_item.logs_req_id
    else:
        return None
         

def recv_process():
    recv_id = request.args[0]
    recv_record = db.logs_recv[recv_id]
    inventory_store_id = recv_record.inventory_store_id
    
    #Get Recv & Store Items 
    recv_items = db( ( db.logs_recv_item.logs_recv_id == recv_id ) & \
                     ( db.logs_recv_item.deleted == False )  
                     ).select(db.logs_recv_item.id,     
                              db.logs_recv_item.item_id,                    
                              db.logs_recv_item.quantity,
                              db.logs_recv_item.item_packet_id,    
                              )
                      
    store_items = db( ( db.inventory_store_item.inventory_store_id == inventory_store_id ) & \
                      ( db.inventory_store_item.deleted == False )  
                      ).select(db.inventory_store_item.id,
                               db.inventory_store_item.item_id,
                               db.inventory_store_item.quantity,
                               db.inventory_store_item.item_packet_id,
                               ) 
                      
    store_items_dict = store_items.as_dict(key = "item_id")                      
                
    req_items = req_items_for_store(inventory_store_id, "fulfil")
    
    update_log_req_id = []

    for recv_item in recv_items:
        item_id = recv_item.item_id
        if item_id in store_items_dict:
            #This item already exists in the store, and the quantity must be incremented
            store_item = Storage(store_items_dict[item_id])
            
            store_item_id = store_item.id        
            
            store_item_quantity = store_item.quantity * \
                                  store_item.packet_quantity
            
            recv_item_quantity = recv_item.quantity * \
                                 recv_item.packet_quantity         

            #convert the recv items quantity into the store item quantity (according to packet)
            quantity = (store_item_quantity + recv_item_quantity) / \
                        store_item.packet_quantity
            item = dict(quantity = quantity)
        else:
            # This item must be added to the store
            store_item_id = 0
            item = dict( inventory_store_id = inventory_store_id,
                         item_id = item_id,
                         quantity = recv_item.quantity,
                         item_packet_id = recv_item.item_packet_id
                         )    
                    
        # Update Store Item
        db.inventory_store_item[store_item_id] = item
        
        #Check for req_items (-> fulfil)
        update_log_req_id.append( req_item_in_shipment(shipment_item = Storage(logs_recv_item = recv_item),
                                                       shipment_type = "recv",
                                                       req_items = req_items,
                                                       )   
                                 )         
        
    #Update recv record & lock for editing 
    db.logs_recv[recv_id] = dict(datetime = request.utcnow,
                                 status = LOGS_STATUS_RECEIVED,
                                 owned_by_user = None,   
                                 owned_by_role = ADMIN                                
                                 ) 
    
    #Update status_fulfil of the req record(s)
    for log_req_id in update_log_req_id:
        if log_req_id:
            session.rcvars.logs_req = log_req_id
            logs_req_item_onaccept(None)

    response.confirmation = T("Received Items added to Warehouse Items")

    # Go to the Warehouse which has received these items
    redirect(URL(r = request,
                 c = "inventory",
                 f = "store",
                 args = [inventory_store_id, "store_item"]
                 )
             )

#------------------------------------------------------------------------------
def send_process():
    send_id = request.args[0]
    send_record = db.logs_send[send_id]
    inventory_store_id = send_record.inventory_store_id
    to_inventory_store_id = send_record.to_inventory_store_id
    cancel_send = False
    invalid_send_item_ids = []

    #Get Send & Store Items
    send_items = db( ( db.logs_send_item.logs_send_id == send_id ) & \
                     ( db.logs_send_item.deleted == False ) )\
                 .select( db.logs_send_item.id,                         
                          db.logs_send_item.quantity,
                          db.logs_send_item.item_packet_id,
                          db.inventory_store_item.id,
                          db.inventory_store_item.item_id,
                          db.inventory_store_item.quantity,
                          db.inventory_store_item.item_packet_id, #required by packet_quantity virtualfield
                          db.inventory_store_item.deleted,
                          left=db.inventory_store_item.on(db.logs_send_item.store_item_id == db.inventory_store_item.id),
                          #To ensure that all send items are selected, even if the store item has been deleted.
                          )   
                 
    #Filter for inventory store records (separate due to left-join                   
    send_items.exclude(lambda row: row.inventory_store_item.id and \
                                   row.inventory_store_item.deleted == True
                       )                    
                 
    req_items = req_items_for_store(to_inventory_store_id, "transit")       
    
    update_log_req_id = []                  

    for send_item in send_items:     
        item_id = send_item.inventory_store_item.item_id   
        send_item_id = send_item.logs_send_item.id
        store_item_id = send_item.inventory_store_item.id        
        
        store_item_quantity = send_item.inventory_store_item.quantity * \
                        send_item.inventory_store_item.packet_quantity
        
        send_item_quantity = send_item.logs_send_item.quantity * \
                        send_item.logs_send_item.packet_quantity
                        
        if send_item_quantity > store_item_quantity:
            # This shipment is invalid
            # flag this item
            invalid_send_item_ids.append(send_item_id)            
            
            # Cancel this processing
            cancel_send = True
        else:
            # Update the Store Item Quantity
            new_store_quantity = ( store_item_quantity - send_item_quantity) / \
                                 send_item.inventory_store_item.packet_quantity
            db.inventory_store_item[store_item_id] = dict(quantity = new_store_quantity)
        
        #Check for req_items (-> transit)
        update_log_req_id.append(req_item_in_shipment(shipment_item = send_item,
                                                      shipment_type = "send",   
                                                      req_items = req_items
                                                      ) 
                                 )            
            
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
        # Update Send record & lock for editing 
        db.logs_send[send_id] = dict(datetime = request.utcnow,
                                     status = LOGS_STATUS_SENT,
                                     owned_by_user = None,   
                                     owned_by_role = ADMIN                                      
                                     )          
        response.confirmation = T("Items Sent from Warehouse")           
        
        #Update status_fulfil of the req record(s)
        for log_req_id in update_log_req_id:
            if log_req_id:
                session.rcvars.logs_req = log_req_id
                logs_req_item_onaccept(None)        
               
        # Go to the Warehouse which has sent these items
        redirect(URL(r = request,
                     c = "inventory",
                     f = "store",
                     args = [inventory_store_id, "store_item"]
                     )
                 )                    
#==============================================================================
def recv_sent():
    """ function to copy data from a shipment which was sent to the warehouse to a recv shipment """

    send_id = request.args[0]

    r_send = db.logs_send[send_id]

    inventory_store_id = r_send.to_inventory_store_id

    from_location_id = shn_get_db_field_value(db,
                                              "inventory_store",
                                              "location_id",
                                              r_send.inventory_store_id )

    # Create a new recv record
    recv_id = db.logs_recv.insert(inventory_store_id = inventory_store_id,
                                  from_location_id = from_location_id)

    sent_items = db( (db.logs_send_item.logs_send_id == send_id) & \
                     (db.logs_send_item.store_item_id == db.inventory_store_item.id) & \
                     (db.logs_send_item.deleted == False) 
                     ).select(db.inventory_store_item.item_id,
                              db.logs_send_item.item_packet_id,
                              db.logs_send_item.quantity)   

    # Copy items from send to recv
    for sent_item in sent_items:
        db.logs_recv_item.insert(logs_recv_id = recv_id,
                                 item_id = sent_item.inventory_store_item.item_id,
                                 item_packet_id = sent_item.logs_send_item.item_packet_id,
                                 quantity = sent_item.logs_send_item.quantity)

    #Flag shipment as received as received
    db.logs_send[send_id] = dict(status = LOGS_STATUS_RECEIVED)

    # Redirect to rec
    redirect(URL(r = request,
                 c = "logs",
                 f = "recv",
                 args = [recv_id]
                 )
             )     
#==============================================================================
def commit_req():
    """ 
    function to commit items according to a request.
    copy data from a req into a commitment 
    arg: req_id
    vars: inventory_store_id
    """    
    
    req_id = request.args[0]
    r_req = db.logs_req[req_id]
    inventory_store_id = request.vars.get("inventory_store_id")

    # Create a new commit record
    commit_id = db.logs_commit.insert( datetime = request.utcnow,
                                       logs_req_id = req_id,
                                       inventory_store_id = inventory_store_id,
                                       for_inventory_store_id = r_req.inventory_store_id
                                      )
    
    #Only populate commit items if we know the store committing 
    if inventory_store_id:
        #Only select items which are in the warehouse
        req_items = db( (db.logs_req_item.logs_req_id == req_id) & \
                        (db.logs_req_item.quantity_fulfil < db.logs_req_item.quantity) & \
                        (db.inventory_store_item.inventory_store_id == inventory_store_id) & \
                        (db.logs_req_item.item_id == db.inventory_store_item.item_id) & \
                        (db.logs_req_item.deleted == False)  & \
                       (db.inventory_store_item.deleted == False)
                       ).select(db.logs_req_item.id,
                                db.logs_req_item.quantity,
                                db.logs_req_item.item_packet_id,
                                db.inventory_store_item.item_id,
                                db.inventory_store_item.quantity,
                                db.inventory_store_item.item_packet_id)   
        
        for req_item in req_items:
            req_item_quantity = req_item.logs_req_item.quantity * \
                            req_item.logs_req_item.packet_quantity   
                                        
            store_item_quantity = req_item.inventory_store_item.quantity * \
                            req_item.inventory_store_item.packet_quantity
                            
            if store_item_quantity > req_item_quantity:
                commit_item_quantity = req_item_quantity
            else:
                commit_item_quantity = store_item_quantity
            commit_item_quantity = commit_item_quantity / req_item.logs_req_item.packet_quantity
            
            if commit_item_quantity:                 
                commit_item_id = db.logs_commit_item.insert( logs_commit_id = commit_id,
                                            logs_req_item_id = req_item.logs_req_item.id,
                                            item_packet_id = req_item.logs_req_item.item_packet_id,
                                            quantity = commit_item_quantity
                                           ) 
                
                #Update the req_item.commit_quantity  & req.commit_status   
                session.rcvars.logs_commit_item = commit_item_id
                logs_commit_item_onaccept(None)
                                             
    # Redirect to commit
    redirect(URL(r = request,
                 c = "logs",
                 f = "commit",
                 args = [commit_id, "commit_item"]
                 )
             )   
#==============================================================================
def send_commit():
    """ 
    function to send items according to a commit.
    copy data from a commit into a send 
    arg: req_id
    """    
    
    commit_id = request.args[0]
    r_commit = db.logs_commit[commit_id]
    
    # Create a new send record
    send_id = db.logs_send.insert( datetime = request.utcnow,
                                   inventory_store_id = r_commit.inventory_store_id,
                                   to_inventory_store_id = r_commit.for_inventory_store_id
                                   )
    
    #Only select items which are in the warehouse
    commit_items = db( (db.logs_commit_item.logs_commit_id == commit_id) & \
                       (db.logs_commit_item.logs_req_item_id == db.logs_req_item.id) & \
                       (db.logs_req_item.item_id == db.inventory_store_item.item_id) & \
                       (db.logs_commit_item.deleted == False) & \
                       (db.logs_req_item.deleted == False) & \
                       (db.inventory_store_item.deleted == False)
                   ).select( db.inventory_store_item.id,
                             db.logs_commit_item.quantity,
                             db.logs_commit_item.item_packet_id,
                            )   
    
    for commit_item in commit_items:                        
        send_item_id = db.logs_send_item.insert( logs_send_id = send_id,
                                                 store_item_id = commit_item.inventory_store_item.id,
                                                 quantity = commit_item.logs_commit_item.quantity,
                                                 item_packet_id = commit_item.logs_commit_item.item_packet_id                                                 
                                                 ) 
                                                    
    # Redirect to send
    redirect(URL(r = request,
                 c = "logs",
                 f = "send",
                 args = [send_id]
                 )
             )       
#==============================================================================#    
def recv_item_json():
    response.headers["Content-Type"] = "text/x-json"
    db.logs_recv.datetime.represent = lambda dt: dt[:10]
    records =  db( (db.logs_recv_item.logs_req_item_id == request.args[0]) & \
                   (db.logs_recv.id == db.logs_recv_item.logs_recv_id) & \
                   (db.logs_recv_item.deleted == False )
                  ).select(db.logs_recv.id,
                           db.logs_recv_item.quantity,
                           db.logs_recv.datetime,
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
    response.headers["Content-Type"] = "text/x-json"
    db.logs_send.datetime.represent = lambda dt: dt[:10]
    records =  db( (db.logs_send_item.logs_req_item_id == request.args[0]) & \
                   (db.logs_send.id == db.logs_send_item.logs_send_id) & \
                   (db.logs_send_item.deleted == False )
                  ).select(db.logs_send.id,
                           db.logs_send_item.quantity,
                           db.logs_send.datetime,
                           )
    json_str = "[%s,%s" % ( json.dumps(dict(id = str(T("Sent")), 
                                            quantity = "#"
                                            ) 
                                        ) , 
                            records.json()[1:] 
                           )   
    return json_str
#==============================================================================#    
def commit_item_json():
    response.headers["Content-Type"] = "text/x-json"
    db.logs_commit.datetime.represent = lambda dt: dt[:10]
    records =  db( (db.logs_commit_item.logs_req_item_id == request.args[0]) & \
                   (db.logs_commit.id == db.logs_commit_item.logs_commit_id) & \
                   (db.logs_commit_item.deleted == False )
                  ).select(db.logs_commit.id,
                           db.logs_commit_item.quantity,
                           db.logs_commit.datetime,
                           )
    json_str = "[%s,%s" % ( json.dumps(dict(id = str(T("Committed")), 
                                            quantity = "#"
                                            ) 
                                        ) , 
                            records.json()[1:] 
                           )   
    return json_str