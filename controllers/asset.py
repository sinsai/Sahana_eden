# -*- coding: utf-8 -*-

""" Asset

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2011-03-18

    Asset Management Functionality

"""

prefix = request.controller
resourcename = request.function

#==============================================================================
response.menu_options = [
    #[T("Home"), False, URL(r=request, c="asset", f="index")],
    [T("Assets"), False, URL(r=request, c="asset", f="asset"),
    [
        [T("List"), False, URL(r=request, c="asset", f="asset")],
        [T("Add"), False, URL(r=request, c="asset", f="asset", args="create")],
    ]],    
    [T("Catalog Items"), False, URL(r=request, c="supply", f="item"),
    [
        [T("List"), False, URL(r=request, c="supply", f="item")],
        [T("Add"), False, URL(r=request, c="supply", f="item", args="create")],
    ]],            
]

def index():
    """
    """
    module_name = deployment_settings.modules[prefix].name_nice
    response.title = module_name
    return dict(module_name=module_name)

#==============================================================================
def shn_asset_rheader(r):

    """ Resource Header for Items """

    if r.representation == "html":
        asset = r.record
        if asset:
            tabs = [
                    (T("Edit Details"), None),
                    (T("Assignments"), "assign"),           
                   ]            
            rheader_tabs = shn_rheader_tabs(r, tabs)
            
            item = db.asset_asset.item_id.represent(asset.item_id)
            rheader = DIV(TABLE(TR( TH("%s: " % T("Asset Number")),
                                    asset.number,
                                    TH("%s: " % T("Item")), item,
                                  ),
                               ),
                          rheader_tabs
                         )
            return rheader
    return None

#==============================================================================
def asset():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    return s3_rest_controller(prefix, resourcename, rheader=shn_asset_rheader)

# END =========================================================================