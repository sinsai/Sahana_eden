# -*- coding: utf-8 -*-

"""
    Logistics Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-09-02

    Distribution, Shipments
"""

module = request.controller

response.menu_options = logs_menu

#------------------------------------------------------------------------------
def index():

    """
        Home page for the Logs Application
        @ToDo: Add Dashboard functionality
    """

    # @ToDo: Default to the logs_distrib list view
    # Does not work with paginate!!!
    #request.function = "distrib"
    #request.args = []
    #return dict()
    module_name = deployment_settings.modules[module].name_nice
    return dict(module_name=module_name)

#------------------------------------------------------------------------------
def shn_distrib_rheader(r, tabs=[]):
    if r.representation == "html":
        logs_distrib = r.record
        if logs_distrib:
            rheader_tabs = shn_rheader_tabs(r, tabs)
            rheader = DIV(TABLE(TR(
                                   TH(T("Location") + ": "), shn_gis_location_represent(logs_distrib.location_id),
                                   TH(T("Date") + ": "), logs_distrib.date,
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

    # Post-processor
    def postp(r, output):
        if r.representation in shn_interactive_view_formats:
            #if r.method == "create" and not r.component:
            # listadd arrives here as method=None
            if r.method != "delete" and not r.component:
                # Redirect to the Items tabs after creation
                r.next = r.other(method="distrib_item", record_id=s3xrc.get_session(module, resource))

            # Normal Action Buttons
            shn_action_buttons(r)

        return output
    response.s3.postp = postp

    tabs = [
            (T("Details"), None),
            (T("Items"), "distrib_item"),
           ]
    rheader = lambda r: shn_distrib_rheader(r, tabs)

    output = s3_rest_controller(module, resource, rheader=rheader)
    return output

#------------------------------------------------------------------------------
def distrib_item():

    """ RESTful CRUD controller """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    output = s3_rest_controller(module, resource)
    return output
#------------------------------------------------------------------------------