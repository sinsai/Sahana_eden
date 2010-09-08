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
def shn_distrib_rheader(r, tabs=[]):
    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, tabs)
        logs_distrib = r.record
        rheader = DIV(TABLE(TR(
                               TH(Tstr("Location") + ": "), shn_gis_location_represent(logs_distrib.location_id),
                               TH(Tstr("Date") + ": "), logs_distrib.date,
                               ),
                           ),
                      rheader_tabs
                      )
        return rheader
    return None

def distrib():

    """ RESTful CRUD controller """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    # Don't send the locations list to client (pulled by AJAX instead)
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

    tabs = [
            (T("Details"), None),
            (T("Items"), "distrib_item"),
           ]
    rheader = lambda r: shn_distrib_rheader(r, tabs)

    return shn_rest_controller(module, resource, rheader=rheader)

def index():

    """
        Default to the logs_distrib list view
        @TODO does not work with paginate!!!
    """

    request.function = "distrib"
    request.args = []
    return dict()
    #module_name = deployment_settings.modules[module].name_nice
    #return dict(module_name=module_name)

#==============================================================================
def distrib_item():

    """ RESTful CRUD controller """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
       
    return shn_rest_controller(module, resource)