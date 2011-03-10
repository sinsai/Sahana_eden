# -*- coding: utf-8 -*-

""" Supply

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16

    Generic Supply functionality such as catalogs and items that will be used across multiple modules

"""

prefix = request.controller
resourcename = request.function

response.menu_options = inv_menu

#==============================================================================
#@auth.s3_requires_membership(1)
def item_category():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    s3xrc.model.configure(table, 
                          listadd=False)
    return s3_rest_controller(prefix, resourcename)

def item_pack():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    s3xrc.model.configure(table, 
                          listadd=False) 
                          #insertable=False)
    return s3_rest_controller(prefix, resourcename)


#==============================================================================
def shn_item_rheader(r, tabs=[]):

    """ Resource Header for Items """

    if r.representation == "html":
        item = r.record
        if item:
            rheader_tabs = shn_rheader_tabs(r, tabs)
            category = db(db.supply_item_category.id == item.item_category_id).select(db.supply_item_category.name,
                                                                                      limitby=(0, 1)).first().name
            rheader = DIV(TABLE(TR( TH(T("Name") + ": "), item.name,
                                    TH(T("Category") + ": "),   category,
                                  ),
                               ),
                          rheader_tabs
                         )
            return rheader
    return None


#==============================================================================
def item():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    tabs = [
            (T("Edit Details"), None),
            (T("packs"), "item_pack"),
            (T("In Inventories"), "store_item"),
            (T("Requested"), "ritem")            
           ]

    rheader = lambda r: shn_item_rheader(r, tabs)
    return s3_rest_controller(prefix, resourcename, rheader=rheader)

#==============================================================================
