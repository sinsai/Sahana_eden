# -*- coding: utf-8 -*-

"""
    Inventory 
    
    @author: Michael Howden (michael@aidiq.com)
    @date-created: 2010-08-16    
    
    A module for record inventories of items at a location
"""

module = "inventory"
if deployment_settings.has_module(module):
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
                            location_id,
                            #get_location_id(),
                            Field("description", 
                                  "text",
                                  length=320),
                            document_id,
                            migrate=migrate)

    #THESE CHANGE THE VALUE OF location_id EVERYWHERE!!!
    #table.location_id.requires = IS_ONE_OF(db, "gis_location.id", repr_select, sort=True)
    #table.location_id.comment.append(SPAN("*", _class="req"))

    s3.crud_strings[tablename] = shn_crud_strings("Inventory Location")

    # -----------------------------------------------------------------------------
    def inventory_location_represent(id):
        if id:
            location = db(db.inventory_location.id == id).select(db.inventory_location.location_id, limitby=(0, 1)).first().location_id
            return shn_gis_location_represent(location)
        else:
            return None
    
    def get_inventory_location_id (field_name = "inventory_location_id", 
                                   label = T("Inventory Location"),
                                   ):
                                   
        requires = IS_NULL_OR(IS_ONE_OF(db, "inventory_location.id", inventory_location_represent, sort=True))
        
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
                                    vars=dict(format="popup", child=field_name)
                                    ),
                          _target="top",
                          _title="Add Inventory Location",
                          ),
                       DIV( _class="tooltip",
                            _title=Tstr("Inventory Location") + "|" + Tstr("Add a New Inventory Location")
                            )
                       )

        return db.Table(None, 
                        field_name,
                        FieldS3(field_name, 
                                db.supply_item, sortby="name",
                                requires = requires,
                                represent = represent,
                                label = label,
                                comment = comment,
                                ondelete = "RESTRICT"
                                )
                        )
        
    # inventory_location as component of doc_documents
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(doc_document="document_id"),
                              deletable=True,
                              editable=True)

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


    inventory_menu = [[T("Inventory Stores"), False, URL(r=request, 
                                                    c = "inventory",
                                                    f = "location"),
                       None],
                      [T("Relief Items"), False, URL(r=request, 
                                                     c = "supply",
                                                     f = "item"),
                       None]
                      ]