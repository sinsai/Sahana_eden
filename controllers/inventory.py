# -*- coding: utf-8 -*-

"""
    Inventory (Warehouse) Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16

    A module to record inventories of items at a location (store)
"""

module = request.controller

response.menu_options = logs_menu

def index():

    """
        Use main Logs homepage
        @ToDo: Default to the inventory_store list view
        - does not work with paginate!!!
    """
    response.view = "logs/index.html"
    module_name = deployment_settings.modules["logs"].name_nice
    response.title = module_name
    return dict(module_name=module_name)

    #request.function = "store"
    #request.args = []
    #return store()
    #module_name = deployment_settings.modules[module].name_nice
    #return dict(module_name=module_name)

#==============================================================================
def shn_store_rheader(r):
    if r.representation == "html":
        inventory_store = r.record
        if inventory_store:
            rheader_tabs = shn_rheader_tabs(r, tabs = [ (T("Details"), None),
                                                        (T("Items"), "store_item"),
                                                        (T("Request"), "req"),
                                                        #(T("Match Requests"), "match_req"),
                                                        (T("Incoming"), "send", dict(select="incoming")),
                                                        (T("Receive" ), "recv"),
                                                        (T("Send"), "send", dict(select="sent")),
                                                        (T("Commit"), "commit"),
                                                        (T("Users"), "store_user"),
                                                       ])

            rheader = DIV(TABLE(TR(
                                   TH(T("Location") + ": "), inventory_store_represent(inventory_store.id),
                                   TH(T("Description") + ": "), inventory_store.comments,
                                   ),
                                ),
                          rheader_tabs
                          )
            return rheader
    return None

def store():

    """ RESTful CRUD controller """

    resourcename = request.function
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Don't send the locations list to client (pulled by AJAX instead)
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

    # Add logs_send as component joinby field according to tab selected
    if request.get_vars.get("select","sent") == "incoming":
        s3xrc.model.add_component("logs",
                                  "send",
                                  multiple=True,
                                  joinby=dict( inventory_store = "to_inventory_store_id" )
                                  )
        
        # Hide the Add button for incoming shipments
        s3xrc.model.configure(db.logs_send, insertable=False)
        
        # Probably need to adjust some more CRUD strings:
        s3.crud_strings["logs_send"].update(
            msg_record_modified = T("Incoming Shipment updated"),
            msg_record_deleted = T("Incoming Shipment canceled"),
            msg_list_empty = T("No Incoming Shipments"))
        
        def prep(r):         
            filter = (db.logs_send.status == LOGS_STATUS_SENT)
            r.resource.add_component_filter("send", filter)
            return True
        response.s3.prep = prep             
    else:
        s3xrc.model.add_component("logs",
                                  "send",
                                  multiple=True,
                                  joinby=dict( inventory_store = "inventory_store_id" )
                                  )
        s3.crud_strings["logs_send"].update(
            msg_record_modified = T("Sent Shipment updated"),
            msg_record_deleted = T("Sent Shipment canceled"),
            msg_list_empty = T("No Sent Shipments"))       

    s3xrc.model.configure(table, create_next=URL(r=request,
                                                 c=module, f=resourcename,
                                                 args=["[id]", "store_item"]))

    output = s3_rest_controller(module, resourcename,
                                rheader=shn_store_rheader)
    
    if "send" in request.args and request.get_vars.get("select","sent") == "incoming":
        recv_sent_action = dict(url = str(URL(r=request,
                                              c = "logs",
                                              f = "recv_sent",
                                              args = ["[id]"]
                                              )
                                           ),
                                _class = "action-btn",
                                label = "Receive",
                                )
        
        if response.s3.actions:
            response.s3.actions.append(recv_sent_action)
        else:
            response.s3.actions = [recv_sent_action]  
                                    
    return output

#==============================================================================
def store_item():

    """ RESTful CRUD controller """

    resourcename = request.function
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    return s3_rest_controller(module, resourcename)

def store_item_quantity():
    response.headers["Content-Type"] = "application/json"
    record =  db( (db.inventory_store_item.id == request.args[0]) & \
                  (db.inventory_store_item.item_packet_id == db.supply_item_packet.id)
                 ).select(db.inventory_store_item.quantity,
                          db.supply_item_packet.quantity,
                          limitby=[0,1]).first()#
    return json.dumps(record)

def store_item_packets():
    response.headers["Content-Type"] = "text/x-json"
    return db( (db.inventory_store_item.id == request.args[0]) & \
               (db.inventory_store_item.item_id == db.supply_item_packet.item_id)
              ).select( db.supply_item_packet.id,
                        db.supply_item_packet.name,
                        db.supply_item_packet.quantity).json()
#==============================================================================