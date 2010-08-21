# -*- coding: utf-8 -*-

"""
    Supply 
    
    @author: Michael Howden (michael@aidiq.com)
    @date-created: 2010-08-16    
    
    Generic Supply functionality such as catalogs and items that will be used across multiple modules
"""

module = request.controller

response.menu_options = inventory_menu

#==============================================================================
# @ToDo: Create should be restricted to Admin
def item_category():
    "RESTful CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    return shn_rest_controller(module, resource, listadd=False)

#==============================================================================
def shn_item_rheader(jr, tabs=[]):
    if jr.representation == "html":
        rheader_tabs = shn_rheader_tabs(jr, tabs)
        item = jr.record
        category = db(db.supply_item_category.id == item.item_category_id).select(db.supply_item_category.name, limitby=(0, 1)).first().name
        rheader = DIV(TABLE(TR(
                               TH(Tstr("Category") + ": "),   category,
                               TH(Tstr("Name") + ": "), item.name,
                              ),
                           ),
                      rheader_tabs
                     )
        return rheader
    return None

def item():
    "RESTful CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    def postp(jr, output):                          
        shn_action_buttons(jr)
        return output
    response.s3.postp = postp
    
    rheader = lambda jr: shn_item_rheader(jr,
                                          tabs = [(T("Details"), None),
                                                  (T("Inventories with Items"), "location_item"),                                                                                                    
                                                 ]
                                         )    
    
    return shn_rest_controller(module, resource, rheader=rheader, sticky=True)