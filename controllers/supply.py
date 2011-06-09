# -*- coding: utf-8 -*-

""" Supply

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16

    Generic Supply functionality such as catalogs and items that will be used across multiple modules

"""

module = request.controller
resourcename = request.function

if not (deployment_settings.has_module("inv") or deployment_settings.has_module("asset")):
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

response.menu_options = inv_menu # Defined in inv model

#==============================================================================
#@auth.s3_requires_membership(1)
def item_category():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    s3xrc.model.configure(table,
                          listadd=False)
    return s3_rest_controller(module, resourcename)

def item_pack():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    s3xrc.model.configure(table,
                          listadd=False)
    return s3_rest_controller(module, resourcename)

#------------------------------------------------------------------------------
def brand():
    """ RESTful CRUD controller """

    return s3_rest_controller(module, resourcename)

#==============================================================================
def item():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    return s3_rest_controller(module, resourcename, rheader=shn_item_rheader)

#------------------------------------------------------------------------------
def shn_item_rheader(r):

    """ Resource Header for Items """

    if r.representation == "html":
        item = r.record
        if item:
            tabs = [
                    (T("Edit Details"), None),
                    (T("Packs"), "item_pack"),
                    (T("Alternative Items"), "item_alt"),
                    (T("In Inventories"), "store_item"),
                    (T("Requested"), "ritem")
                   ]
            rheader_tabs = s3_rheader_tabs(r, tabs)
            query = (db.supply_item_category.id == item.item_category_id)
            category = db(query).select(db.supply_item_category.name,
                                        limitby=(0, 1)).first()
            if category:
                category = category.name
            else:
                category = NONE
            rheader = DIV(TABLE(TR( TH("%s: " % T("Name")), item.name,
                                    TH("%s: " % T("Category")), category,
                                  ),
                               ),
                          rheader_tabs
                         )
            return rheader
    return None

# END =========================================================================
