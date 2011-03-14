# -*- coding: utf-8 -*-

"""
    Request Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-09-02
"""

module = request.controller

response.menu_options = inv_menu

#==============================================================================
def req():
    resourcename = request.function
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]
    
    # Improve - get site which the staff is allocated to? 
    site_id  = shn_get_db_field_value(db,
                                      "org_staff",
                                      "site_id",                                                           
                                      auth.person_id(),   
                                      "person_id"
                                      ) 
    
    req_actions = [dict(url = str( URL( r=request,
                                        c = "req",
                                        f = "req",
                                        args = ["[id]","req_item"]                                  
                                       )
                                   ),
                        _class = "action-btn",
                        label = str(T("Items")),
                        ),
                    ]
    if site_id:
        req_actions.append(dict(url = str(URL( r=request,
                                       c = "req",
                                       f = "commit_req",
                                       args = ["[id]"],
                                       vars = {"site_id": site_id}
                                      )
                                       ),
                                _class = "action-btn",
                                label = str(T("Commit")),
                                )
                            )
                    
    output = s3_rest_controller( module,
                                 resourcename,
                                 rheader=shn_req_rheader)
    
    if response.s3.actions:
        response.s3.actions += req_actions
    else:
        response.s3.actions = req_actions    
          
    return output
#------------------------------------------------------------------------------
def shn_req_rheader(r):
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
                                       req_record.datetime,
                                       TH( T("Date Required") + ": "),
                                       req_record.date_required,
                                      ),
                                   TR( TH( T("Requested By Warehouse") + ": "),
                                       shn_site_represent(req_record.site_id),
                                      ),
                                   TR( TH( T("Commit. Status") + ": "),
                                       req_status_opts.get(req_record.commit_status),
                                       TH( T("Transit. Status") + ": "),
                                       req_status_opts.get(req_record.transit_status),
                                       TH( T("Fulfil. Status") + ": "),
                                       req_status_opts.get(req_record.fulfil_status)
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
                                 rheader=shn_commit_rheader)
    return output
#------------------------------------------------------------------------------
def shn_commit_rheader(r):
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
                                           shn_site_represent(commit_record.site_id),
                                           TH( T("For Warehouse") + ": "),
                                           shn_site_represent(commit_record.for_site_id),
                                          ),
                                       TR( TH( T("Comments") + ": "),
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
                
                send_btn_confirm = SCRIPT("S3ConfirmClick('#send_commit','%s')" 
                                          % T("Do you want to send these Committed items?") )
                rheader.append(send_btn)
                rheader.append(send_btn_confirm)    
                
                rheader.append(rheader_tabs) 
                        
                return rheader
    return None
#==============================================================================
def commit_item():
    resourcename = request.function
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]
    output = s3_rest_controller( module,
                                 resourcename
                                 )
    return output
#==============================================================================
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
    
    #User must have permissions over site which is sending 
    (prefix, resourcename, id) = shn_site_resource(site_id)        
    if not site or not auth.s3_has_permission("update", 
                                              db["%s_%s" % (prefix,
                                                            resourcename)], 
                                              record_id=id):    
        session.error = T("You do no have permission to make this commitment.")    
        redirect(URL(r = request,
                     c = "req",
                     f = "commit",
                     args = [commit_id],
                     )
                 )      

    # Create a new commit record
    commit_id = db.req_commit.insert( datetime = request.utcnow,
                                       req_id = req_id,
                                       site_id = site_id,
                                       for_site_id = r_req.site_id
                                      )
    
    #Only populate commit items if we know the site committing 
    if site_id:
        #Only select items which are in the warehouse
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
                
                #Update the req_item.commit_quantity  & req.commit_status   
                session.rcvars.req_commit_item = commit_item_id
                shn_commit_item_onaccept(None)
                                             
    # Redirect to commit
    redirect(URL(r = request,
                 c = "req",
                 f = "commit",
                 args = [commit_id, "commit_item"]
                 )
             )   
    
#==============================================================================#    
def commit_item_json():
    response.headers["Content-Type"] = "application/json"
    db.req_commit.datetime.represent = lambda dt: dt[:10]
    records =  db( (db.req_commit_item.req_item_id == request.args[0]) & \
                   (db.req_commit.id == db.req_commit_item.commit_id) & \
                   (db.req_commit_item.deleted == False )
                  ).select(db.req_commit.id,
                           db.req_commit_item.quantity,
                           db.req_commit.datetime,
                           )
    json_str = "[%s,%s" % ( json.dumps(dict(id = str(T("Committed")), 
                                            quantity = "#"
                                            ) 
                                        ) , 
                            records.json()[1:] 
                           )   
    return json_str
    