# -*- coding: utf-8 -*-

"""
    Inventory 
    
    @author: Michael Howden (michael@aidiq.com)
    @date-created: 2010-08-16    
    
    A module for record inventories of items at a location
"""

module = "inventory"

#==============================================================================
# Settings
#
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        Field("audit_read", "boolean"),
                        Field("audit_write", "boolean"),
                        migrate=migrate)


#==============================================================================
# Inventory Location
#
resource = "location"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, 
                        timestamp, 
                        uuidstamp, 
                        authorstamp, 
                        deletion_status,
                        get_location_id(),
                        Field("description", 
                              "text",
                              length=320),
                        migrate=migrate)

table.location_id.comment = SPAN("*", _class="req")

s3.crud_strings[tablename] = shn_crud_strings("Inventory Location")

# -----------------------------------------------------------------------------
def get_inventory_location_id (field_name = "inventory_location_id", 
                               label = T("Inventory Location"),
                               ):
    repr_select = lambda l: shn_gis_location_represent( l.location_id )
    requires = IS_NULL_OR(IS_ONE_OF(db, "inventory_location.id", repr_select, sort=True))
    
    represent = lambda id: shn_gis_location_represent( 
                               shn_get_db_field_value(db = db,
                                                      table = "inventory_location", 
                                                      field = "location_id", 
                                                      look_up = id
                                                      )
                                                      )
    
    comment = DIV( A( "Add Inventory Location",
                      _class="colorbox",
                      _href=URL(r=request, 
                                c="inventory", 
                                f="location", 
                                args="create", 
                                vars=dict(format="popup")
                                ),
                      _target="top",
                      _title="Add Inventory Location",
                      ),
                   DIV( _class="tooltip",
                        _title=Tstr("Reliet Item") + "|" + Tstr("Add a New Relief Item")
                        )
                   )

    return db.Table(None, 
                    field_name,
                    FieldS3(field_name, 
                            db.supply_item, sortby='name',
                            requires = requires,
                            represent = represent,
                            label = label,
                            comment = comment,
                            ondelete = 'RESTRICT'
                            )
                    )

#==============================================================================
# Inventory Item
#
resource = "location_item"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, 
                        timestamp, 
                        uuidstamp, 
                        authorstamp, 
                        deletion_status,
                        get_inventory_location_id(),
                        get_item_id(),
                        Field("quantity", "double"),
                        comments,
                        migrate=migrate)

s3.crud_strings[tablename] = shn_crud_strings("Inventory Item")

# Items as component of Locations
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby=dict(inventory_location="inventory_location_id", supply_item="item_id"),
                          deletable=True,
                          editable=True)


inventory_menu = [[T("Inventories"), False, URL(r=request, 
                                                c = "inventory",
                                                f = "location"),
                   None],
                  [T("Relief Items"), False, URL(r=request, 
                                                 c = "supply",
                                                 f = "item"),
                   None]
                  ]