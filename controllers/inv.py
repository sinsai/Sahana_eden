# -*- coding: utf-8 -*-

"""
    Inventory (Warehouse) Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16

    A module to record inventories of items at a location (site)
"""

module = request.controller

response.menu_options = inv_menu

def index():
    """
    """
    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

    #request.args = []
    #module_name = deployment_settings.modules[module].name_nice
    #return dict(module_name=module_name)

#==============================================================================
def inv_item():

    """ RESTful CRUD controller """

    resourcename = request.function
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    return s3_rest_controller(module, resourcename)
#------------------------------------------------------------------------------
def inv_item_quantity():
    response.headers["Content-Type"] = "application/json"
    record =  db( (db.inv_inv_item.id == request.args[0]) & \
                  (db.inv_inv_item.item_pack_id == db.supply_item_pack.id)
                 ).select(db.inv_inv_item.quantity,
                          db.supply_item_pack.quantity,
                          limitby=[0, 1]).first()#

    return json.dumps(record)
#------------------------------------------------------------------------------
def inv_item_packs():
    response.headers["Content-Type"] = "text/x-json"
    return db( (db.inv_inv_item.id == request.args[0]) & \
               (db.inv_inv_item.item_id == db.supply_item_pack.item_id)
              ).select( db.supply_item_pack.id,
                        db.supply_item_pack.name,
                        db.supply_item_pack.quantity).json()
#==============================================================================
def recv():
    """ RESTful CRUD controller """
    resourcename = request.function
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]
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
                                   TR( TH( T("Date") + ": "),
                                       recv_record.datetime,
                                      ),
                                   TR( TH( T( "By" ) + ": "),
                                       shn_site_represent(recv_record.site_id),
                                       TH( T( "From" ) + ": "),
                                       shn_gis_location_represent(recv_record.from_location_id),
                                      ),
                                   TR( TH( T("Comments") + ": "),
                                       TD(recv_record.comments, _colspan=3)
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
class QUANTITY_INV_ITEM:
    def __init__(self, 
                 inv_item_id,
                 item_pack_id):
        self.inv_item_id = inv_item_id
        self.item_pack_id = item_pack_id
    def __call__(self, value):
        error = "Invalid Quantity" # @todo: better error catching
        inv_item_record = db( (db.inv_inv_item.id == self.inv_item_id) & \
                                (db.inv_inv_item.item_pack_id == db.supply_item_pack.id)
                               ).select(db.inv_inv_item.quantity,
                                        db.supply_item_pack.quantity,
                                        db.supply_item_pack.name,
                                        limitby = [0,1]).first() # @todo: this should be a virtual field
        if inv_item_record and value:
            send_quantity = float(value) * shn_get_db_field_value(db,
                                                           "supply_item_pack",
                                                           "quantity",                                                           
                                                           self.item_pack_id   
                                                           )       
            inv_quantity = inv_item_record.inv_inv_item.quantity * \
                             inv_item_record.supply_item_pack.quantity
            if send_quantity > inv_quantity:
                return (value, 
                        "Only %s %s (%s) in the Inventory." %
                        (inv_quantity,
                         inv_item_record.supply_item_pack.name,
                         inv_item_record.supply_item_pack.quantity)    
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
    if (request.vars.inv_item_id):
        db.inv_send_item.quantity.requires = QUANTITY_INV_ITEM(request.vars.inv_item_id, 
                                                                     request.vars.item_pack_id)
    
    def prep(r):
        # If component view
        if r.record and r.record.get("site_id"):        
            #Restrict to items from this warehouse only
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
                                   TR( TH( T("Date") + ": "),
                                       send_record.datetime,
                                      ),
                                   TR( TH( T( "From" ) + ": "),
                                       shn_site_represent(send_record.site_id),
                                       TH( T( "To" ) + ": "),
                                       shn_site_represent(send_record.to_site_id),
                                      ),
                                   TR( TH( T("Comments") + ": "),
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
                    
                    if recv_record.status != SHIP_STATUS_CANCEL:
                        if auth.s3_has_permission("delete", 
                                                  db.inv_send, 
                                                  record_id=send_record.id):                    
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

                rheader.append(shn_rheader_tabs( r,
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
                    ( db.req_req_item.cancel == False ) & \
                    ( db.req_req_item.deleted == False ) 
                   ).select(db.req_req_item.id,
                            db.req_req_item.req_id,
                            db.req_req_item.item_id,
                            db.req_req_item.quantity,
                            db.req_req_item["quantity_%s" % quantity_type],
                            db.req_req_item.item_pack_id,
                            orderby = db.req_req.date_required | db.req_req.datetime, 
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
            #This item is not already in the dict 
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
    
    #Check for req_items
    if item_id in req_items:      
        quantity_req_type = "quantity_%s" % shn_shipment_to_req_type[shipment_type]
              
        #This item has been requested from this inv
        req_item = req_items[item_id]
        req_item_id = req_item.id
        
        #Update the req quantity             
        #convert the shipment items quantity into the req_tem.quantity_fulfil (according to pack)
        quantity = req_item[quantity_req_type] + \
                   (shipment_item[shipment_item_table].pack_quantity / \
                    req_item.pack_quantity) * \
                    shipment_item[shipment_item_table].quantity    
        quantity = min(quantity, req_item.quantity)  #Cap at req. quantity  
        db.req_req_item[req_item_id] = {quantity_req_type: quantity}      
                          
        #link the shipment_item to the req_item    
        db[shipment_item_table][shipment_item[shipment_item_table].id] = dict(req_item_id = req_item_id)
        
        #Flag req record to update status_fulfil 
        return req_item.req_id
    else:
        return None
         

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
    
    #Get Recv & Inv Items 
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
            #This item already exists in the inv, and the quantity must be incremented
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
        
        #Check for req_items (-> fulfil)
        update_req_id.append( req_item_in_shipment(shipment_item = Storage(inv_recv_item = recv_item),
                                                       shipment_type = "recv",
                                                       req_items = req_items,
                                                       )   
                                 )         
        
    #Update recv record & lock for editing 
    db.inv_recv[recv_id] = dict(datetime = request.utcnow,
                                 status = SHIP_STATUS_RECEIVED,
                                 owned_by_user = None,   
                                 owned_by_role = ADMIN                                
                                 ) 
    
    #Update status_fulfil of the req record(s)
    for req_id in update_req_id:
        if req_id:
            session.rcvars.req_req = req_id
            shn_req_item_onaccept(None)

    session.confirmation = T("Shipment Items received by Inventory")

    # Go to the Site which has received these items
    (prefix, resourcename, id) = shn_site_resource(site_id)
    
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
    
    #Get Recv & Inv Items 
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
        #All Items received *should* exist in the inv.
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
        
        # reduce any req_item
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
        
            #Check for req_items (-> fulfil)
            update_req_id.append(  )         
        
    #Update recv record & lock for editing 
    db.inv_recv[recv_id] = dict(datetime = request.utcnow,
                                status = SHIP_STATUS_CANCEL,
                                owned_by_user = None,   
                                owned_by_role = ADMIN                                
                                ) 
    
    #Update status_fulfil of the req record(s)
    for req_id in update_req_id:
        if req_id:
            session.rcvars.req_req = req_id
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
    to_site_id = send_record.to_site_id
    cancel_send = False
    invalid_send_item_ids = []

    #Get Send & Inv Items
    send_items = db( ( db.inv_send_item.send_id == send_id ) & \
                     ( db.inv_send_item.deleted == False ) )\
                 .select( db.inv_send_item.id,                         
                          db.inv_send_item.quantity,
                          db.inv_send_item.item_pack_id,
                          db.inv_inv_item.id,
                          db.inv_inv_item.item_id,
                          db.inv_inv_item.quantity,
                          db.inv_inv_item.item_pack_id, #required by pack_quantity virtualfield
                          db.inv_inv_item.deleted,
                          left=db.inv_inv_item.on(db.inv_send_item.inv_item_id == db.inv_inv_item.id),
                          #To ensure that all send items are selected, even if the inv item has been deleted.
                          )   
                 
    #Filter for inv site records (separate due to left-join                   
    send_items.exclude(lambda row: row.inv_inv_item.id and \
                                   row.inv_inv_item.deleted == True
                       )                    
                 
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
        
        #Check for req_items (-> transit)
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
        db.inv_send[send_id] = dict(datetime = request.utcnow,
                                     status = SHIP_STATUS_SENT,
                                     owned_by_user = None,   
                                     owned_by_role = ADMIN                                      
                                     )          
        session.confirmation = T("Shipment Items sent from Inventory")           
        
        #Update status_fulfil of the req record(s)
        for req_id in update_req_id:
            if req_id:
                session.rcvars.req_req = req_id
                shn_req_item_onaccept(None)        
               
        # Go to the Site which has sent these items
        (prefix, resourcename, id) = shn_site_resource(site_id)

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
        #All Items received *should* exist in the inv.
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
        
        # reduce any req_item
        req_item_id = send_item.inv_send_item.req_item_id
        r_req_item = db((db.req_req_item.id == req_item_id) &
                        (db.req_req_item.deleted == False)
                        ).select(db.req_req_item.quantity_fulfil,
                                 db.req_req_item.item_pack_id, # required by pack_quantity virtualfield
                                 limitby = (0,1)).first()
        if r_req_item:
            quantity_fulfil = shn_supply_item_add(r_req_item.quantity_fulfil,
                                                  r_req_item.pack_quantity,
                                                  -send_item.inv_send_item.quantity,
                                                  send_item.inv_send_item.pack_quantity)   
            db.req_req_item[req_item_id] = dict(quantity_fulfil=quantity_fulfil)          
        
            #Check for req_items (-> fulfil)
            update_req_id.append(  )         
        
    #Update send record & lock for editing 
    db.inv_send[send_id] = dict(datetime = request.utcnow,
                                status = SHIP_STATUS_CANCEL,
                                owned_by_user = None,   
                                owned_by_role = ADMIN                                
                                ) 
    
    #Update status_fulfil of the req record(s)
    for req_id in update_req_id:
        if req_id:
            session.rcvars.req_req = req_id
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
    
    if r_send.status != SHIP_STATUS_IN_PROCESS:
        session.error = T("This shipment has already been received.")

    if session.error:                
        redirect(URL(r = request,
                     c = "inv",
                     f = "send",
                     args = [send_id],
                     )
                 )     

    site_id = r_send.to_site_id

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
                              db.inv_send_item.quantity)   

    # Copy items from send to recv
    for sent_item in sent_items:
        db.inv_recv_item.insert(recv_id = recv_id,
                                item_id = sent_item.inv_inv_item.item_id,
                                item_pack_id = sent_item.inv_send_item.item_pack_id,
                                quantity = sent_item.inv_send_item.quantity)

    #Flag shipment as received as received
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
    arg: req_id
    """    
    
    commit_id = request.args[0]
    r_commit = db.req_commit[commit_id]
    
    #User must have permissions over site which is sending 
    (prefix, resourcename, id) = shn_site_resource(site_id)        
    if not auth.s3_has_permission("update", 
                                  db["%s_%s" % (prefix, resourcename)], 
                                  record_id=id):    
        session.error = T("You do no have permission to send this shipment.")    
        redirect(URL(r = request,
                     c = "req",
                     f = "commit",
                     args = [commit_id],
                     )
                 )         
    # Create a new send record
    to_site_id = r_commit.for_site_id
    to_location_id = db.org_site[to_site_id].location_id    
    send_id = db.inv_send.insert( datetime = request.utcnow,
                                  site_id = r_commit.site_id,
                                  to_location_id = to_location_id,
                                  to_site_id = to_site_id,
                                   
                                   )
    
    #Only select items which are in the warehouse
    commit_items = db( (db.req_commit_item.commit_id == commit_id) & \
                       (db.req_commit_item.req_item_id == db.req_req_item.id) & \
                       (db.req_req_item.item_id == db.inv_inv_item.item_id) & \
                       (db.req_commit_item.deleted == False) & \
                       (db.req_req_item.deleted == False) & \
                       (db.inv_inv_item.deleted == False)
                   ).select( db.inv_inv_item.id,
                             db.req_commit_item.quantity,
                             db.req_commit_item.item_pack_id,
                            )   
    
    for commit_item in commit_items:                        
        send_item_id = db.inv_send_item.insert( send_id = send_id,
                                                 inv_item_id = commit_item.inv_inv_item.id,
                                                 quantity = commit_item.req_commit_item.quantity,
                                                 item_pack_id = commit_item.req_commit_item.item_pack_id                                                 
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
    db.inv_recv.datetime.represent = lambda dt: dt[:10]
    records =  db( (db.inv_recv_item.req_item_id == request.args[0]) & \
                   (db.inv_recv.id == db.inv_recv_item.inv_recv_id) & \
                   (db.inv_recv_item.deleted == False )
                  ).select(db.inv_recv.id,
                           db.inv_recv_item.quantity,
                           db.inv_recv.datetime,
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
    db.inv_send.datetime.represent = lambda dt: dt[:10]
    records =  db( (db.inv_send_item.req_item_id == request.args[0]) & \
                   (db.inv_send.id == db.inv_send_item.send_id) & \
                   (db.inv_send_item.deleted == False )
                  ).select(db.inv_send.id,
                           db.inv_send_item.quantity,
                           db.inv_send.datetime,
                           )
    json_str = "[%s,%s" % ( json.dumps(dict(id = str(T("Sent")), 
                                            quantity = "#"
                                            ) 
                                        ) , 
                            records.json()[1:] 
                           )   
    return json_str