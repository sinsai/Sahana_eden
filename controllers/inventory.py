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
                                                        (T("Received" ), "recv"),
                                                        (T("Sent"), "send"),
                                                       ])
            
            rheader = DIV(TABLE(TR(
                                   TH(T("Location") + ": "), shn_gis_location_represent(inventory_store.location_id),
                                   TH(T("Description") + ": "), inventory_store.comments,
                                   ),
                               ),
                          rheader_tabs
                          )
            return rheader
    return None

def store():

    """ RESTful CRUD controller """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Don't send the locations list to client (pulled by AJAX instead)
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

    # Post-processor
    def postp(r, output):
        if r.representation in shn_interactive_view_formats \
            and r.method != "delete" and not r.component:
                # Redirect to the Items tabs after creation
                r.next = r.other(method="store_item", record_id=s3xrc.get_session(module, resource))                
        return output
    response.s3.postp = postp

    output = s3_rest_controller(module, 
                                resource, 
                                rheader=shn_store_rheader)
    return output

#==============================================================================
def store_item():

    """ RESTful CRUD controller """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    return s3_rest_controller(module, resource)

def store_item_quantity():
    response.headers["Content-Type"] = "text/x-json"
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