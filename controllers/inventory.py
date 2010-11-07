# -*- coding: utf-8 -*-

"""
    Inventory

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16

    A module to record inventories of items at a location (store)
"""

module = request.controller

response.menu_options = logs_menu

#==============================================================================
def shn_store_rheader(r, tabs=[]):
    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, tabs)
        inventory_store = r.record
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
        if r.representation in shn_interactive_view_formats:
            #if r.method == "create" and not r.component:
            # listadd arrives here as method=None
            if r.method != "delete" and not r.component:
                # Redirect to the Items tabs after creation
                r.next = r.other(method="store_item", record_id=s3xrc.get_session(module, resource))

            # Normal Action Buttons
            shn_action_buttons(r)

        return output
    response.s3.postp = postp

    tabs = [
            (T("Details"), None),
            (T("Items"), "store_item"),
            (T("Requests From"), "req"),
           ]
    rheader = lambda r: shn_store_rheader(r, tabs)

    output = s3_rest_controller(module, 
                                resource, 
                                rheader=rheader)
    return output

def index():

    """
        Default to the inventory_store list view
        @TODO does not work with paginate!!!
    """
    response.view = "logs/index.html"
    module_name = deployment_settings.modules["logs"].name_nice
    return dict(module_name=module_name)    

    #request.function = "store"
    #request.args = []
    #return store()
    #module_name = deployment_settings.modules[module].name_nice
    #return dict(module_name=module_name)

#==============================================================================
def store_item():

    """ RESTful CRUD controller """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    return s3_rest_controller(module, resource)