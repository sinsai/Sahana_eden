# -*- coding: utf-8 -*-

"""
    Supply

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16

    Generic Supply functionality such as catalogs and items that will be used across multiple modules
"""

module = "supply"
if deployment_settings.has_module("inv") or deployment_settings.has_module("asset"):
    #==============================================================================
    # Item Category
    #
    resourcename = "item_category"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("name", length=128, notnull=True, unique=True),
                            comments(),
                            migrate=migrate, *s3_meta_fields())


    # CRUD strings
    ADD_ITEM_CATEGORY = T("Add Item Category")
    LIST_ITEM_CATEGORIES = T("List Item Categories")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ITEM_CATEGORY,
        title_display = T("Item Category Details"),
        title_list = LIST_ITEM_CATEGORIES,
        title_update = T("Edit Item Category"),
        title_search = T("Search Item Categories"),
        subtitle_create = T("Add New Item Category"),
        subtitle_list = T("Item Categories"),
        label_list_button = LIST_ITEM_CATEGORIES,
        label_create_button = ADD_ITEM_CATEGORY,
        label_delete_button = T("Delete Item Category"),
        msg_record_created = T("Item Category added"),
        msg_record_modified = T("Item Category updated"),
        msg_record_deleted = T("Item Category deleted"),
        msg_list_empty = T("No Item Categories currently registered"))

    # Reusable Field
    item_category_id = S3ReusableField("item_category_id", db.supply_item_category, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "supply_item_category.id",
                                                "%(name)s",
                                                sort=True)),
                represent = lambda id: shn_get_db_field_value(db=db, table="supply_item_category", field="name", look_up=id),
                label = T("Category"),
                comment = DIV( _class="tooltip",
                               _title="%s|%s" % (T("Item Category"),
                                                 T("The list of Item categories are maintained by the Administrators."))),
                ondelete = "RESTRICT"
                )
    
    #==============================================================================
    # Brand
    #
    resourcename = "brand"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("name", length=128, notnull=True, unique=True),
                            comments(),
                            migrate=migrate, *s3_meta_fields())


    # CRUD strings
    ADD_BRAND = T("Add Brand")
    LIST_BRAND = T("List Brands")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_BRAND,
        title_display = T("Brand Details"),
        title_list = LIST_BRAND,
        title_update = T("Edit Brand"),
        title_search = T("Search Brands"),
        subtitle_create = T("Add New Brand"),
        subtitle_list = T("Brands"),
        label_list_button = LIST_BRAND,
        label_create_button = ADD_BRAND,
        label_delete_button = T("Delete Brand"),
        msg_record_created = T("Brand added"),
        msg_record_modified = T("Brand updated"),
        msg_record_deleted = T("Brand deleted"),
        msg_list_empty = T("No Brands currently registered"))

    # Reusable Field
    brand_id = S3ReusableField("brand_id", db.supply_brand, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "supply_brand.id",
                                                "%(name)s",
                                                sort=True)),
                represent = lambda id: shn_get_db_field_value(db=db, table="supply_brand", field="name", look_up=id),
                label = T("Brand"),
                comment = DIV( _class="tooltip",
                               _title="%s|%s" % (T("Brand"),
                                                 T("The list of Brands are maintained by the Administrators."))),
                ondelete = "RESTRICT"
                )    

    #==============================================================================
    # Item
    #
    resourcename = "item"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            item_category_id(),
                            brand_id(),
                            Field("name", 
                                  label = T("Name/Model/Type"),
                                  length=128, 
                                  notnull=True, 
                                  unique=True),                            
                            Field("year",
                                  "integer", 
                                  label = T("Year of Manufacture")),
                            Field("um", 
                                  length=128,
                                  label = T("Unit of Measure"),
                                  notnull=True),
                            comments(), # These comments do *not* pull through to an Inventory's Items or a Request's Items
                            migrate=migrate, *s3_meta_fields())


    # CRUD strings
    ADD_ITEM = T("Add Catalog Item")
    LIST_ITEMS = T("List Catalog Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ITEM,
        title_display = T("Item Catalog Details"),
        title_list = LIST_ITEMS,
        title_update = T("Edit Catalog Item"),
        title_search = T("Search Catalog Items"),
        subtitle_create = T("Add New Catalog Item"),
        subtitle_list = T("Catalog Items"),
        label_list_button = LIST_ITEMS,
        label_create_button = ADD_ITEM,
        label_delete_button = T("Delete Catalog Item"),
        msg_record_created = T("Catalog Item added"),
        msg_record_modified = T("Catalog Item updated"),
        msg_record_deleted = T("Catalog Item deleted"),
        msg_list_empty = T("No Catalog Items currently registered"),
        msg_match = T("Matching Catalog Items"),
        msg_no_match = T("No Matching Catalog Items")
        )
    
    def shn_item_represent(id):
        record = db(db.supply_item.id == id).select(db.supply_item.name,
                                                    db.supply_item.um,
                                                    limitby=(0, 1)).first()    
        if not record:
            return NONE
        elif not record.um:
            return record.name
        else:
            item_represent = "%s (%s)" % (record.name, record.um)
            return item_represent


    # Reusable Field
    item_id = S3ReusableField("item_id", db.supply_item, sortby="name",
                requires = IS_ONE_OF(db, "supply_item.id", "%(name)s", sort=True),
                represent = shn_item_represent,
                label = T("Item"),
                comment = DIV(A(ADD_ITEM,
                                _class="colorbox",
                                _href=URL(r=request, c="supply", f="item", args="create", vars=dict(format="popup")),
                                _target="top",
                                _title=ADD_ITEM),
                          DIV( _class="tooltip",
                               _title="%s|%s" % (T("Catalog Item"),
                                                 ADD_ITEM))),
                ondelete = "RESTRICT"
                )    
    
    #------------------------------------------------------------------------------
    # Update the UM in the supply_item_pack table   
    def shn_supply_item_onaccept(form):
        item_id = session.rcvars.supply_item
        
        # try to update the existing record
        if db((db.supply_item_pack.item_id == item_id) &
              (db.supply_item_pack.quantity == 1 ) &
              (db.supply_item_pack.deleted == False ) 
              ).update(name = form.vars.um) == 0:
            #Create a new item packet
            db.supply_item_pack.insert(item_id = item_id,
                                       name = form.vars.um,
                                       quantity = 1,
                                       )
            
    # -----------------------------------------------------------------------------
    # Item Search Method
    #
    shn_item_search = s3base.S3Find(
        #name="shn_item_search",
        #label=T("Name and/or ID"),
        #comment=T("To search for a hospital, enter any of the names or IDs of the hospital, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all hospitals."),
        #field=["gov_uuid", "name", "aka1", "aka2"],
        advanced=(s3base.S3SearchSimpleWidget(
                    name="item_search_text",
                    label=T("Search"),
                    comment=T("Search for an item by text."),
                    field=["name", "comment", "item_category_id$name"]
                  ),
                  s3base.S3SearchSelectWidget(    
                    name="item_search_category",
                    label=T("Category"),
                    comment=T("Search for an item by  category."),
                    field=["item_category_id"],
                    represent ="%(name)s",
                    cols = 3
                  ),                  
                  ## for testing:
                  #s3base.S3SearchMinMaxWidget(
                    #name="hospital_search_bedcount",
                    #method="range",
                    #label=T("Total Beds"),
                    #comment=T("Select a range for the number of total beds"),
                    #field=["total_beds"]
                  #)
        ))       

    #------------------------------------------------------------------------------
    s3xrc.model.configure(
        table, 
        onaccept = shn_supply_item_onaccept,
        search_method = shn_item_search
    )     
    #==============================================================================
    # Item Pack
    #
    resourcename = "item_pack"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            item_id(notnull=True),
                            Field("name", length=128, notnull=True), # Ideally this would reference another table for normalising Pack names
                            Field("quantity", "double", notnull=True),
                            comments(),
                            migrate=migrate, *s3_meta_fields())
    # CRUD strings
    ADD_ITEM_PACKET = T("Add Item Pack")
    LIST_ITEM_PACKET = T("List Item Packs")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ITEM_PACKET,
        title_display = T("Item Pack Details"),
        title_list = LIST_ITEM_PACKET,
        title_update = T("Edit Item Pack"),
        title_search = T("Search Item Packs"),
        subtitle_create = T("Add New Item Pack"),
        subtitle_list = T("Item Packs"),
        label_list_button = LIST_ITEM_PACKET,
        label_create_button = ADD_ITEM_PACKET,
        label_delete_button = T("Delete Item Pack"),
        msg_record_created = T("Item Pack added"),
        msg_record_modified = T("Item Pack updated"),
        msg_record_deleted = T("Item Pack deleted"),
        msg_list_empty = T("No Item Packs currently registered"))

    def shn_item_pack_represent(id):
        record = db((db.supply_item_pack.id == id) &
                    (db.supply_item_pack.item_id == db.supply_item.id) 
                    ).select( db.supply_item_pack.name,
                              db.supply_item_pack.quantity,
                              db.supply_item.um,
                              limitby = (0,1)
                             ).first()
        if record:            
            if record.supply_item_pack.quantity == 1:
                return record.supply_item_pack.name            
            else:                
                return "%s (%s x %s)" % ( record.supply_item_pack.name, 
                                          record.supply_item_pack.quantity, 
                                          record.supply_item.um )
        else:
            return NONE

    # Reusable Field
    item_pack_id = S3ReusableField("item_pack_id", db.supply_item_pack, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, 
                                                "supply_item_pack.id",
                                                shn_item_pack_represent,
                                                sort=True)),
                represent = shn_item_pack_represent,
                label = T("Pack"),    
                comment = DIV(DIV( _class="tooltip",
                                   _title="%s|%s" % (T("Item Packs"),
                                                     T("The way in which an item is normally distributed"))),
                              A( ADD_ITEM_PACKET, 
                                 _class="colorbox", 
                                 _href=URL(r=request, 
                                           c="supply", 
                                           f="item_pack", 
                                           args="create", 
                                           vars=dict(format="popup")
                                           ), 
                                 _target="top", 
                                 _id = "item_pack_add",
                                 _style = "display: none",
                                 ),                               
                              ),
                ondelete = "RESTRICT"
                )    
    
    def shn_record_pack_quantity(r):
        item_pack_id = r.get("item_pack_id", None)
        if item_pack_id:
            return shn_get_db_field_value(db,
                                          "supply_item_pack",
                                          "quantity",
                                          item_pack_id)  
        else:
            return None  
        
    # Virtual Field for pack_quantity
    class item_pack_virtualfields(dict, object):
        def __init__(self,
                     tablename):
            self.tablename = tablename
        def pack_quantity(self):
            if self.tablename == "inv_inv_item":
                item_pack = self.inv_inv_item.item_pack_id
            elif self.tablename == "req_req_item":
                item_pack = self.req_req_item.item_pack_id
            elif self.tablename == "req_commit_item":
                item_pack = self.req_commit_item.item_pack_id       
            elif self.tablename == "inv_recv_item":
                item_pack = self.inv_recv_item.item_pack_id     
            elif self.tablename == "inv_send_item":
                item_pack = self.inv_send_item.item_pack_id                                                           
            else:
                item_pack = None
            if item_pack:
                return item_pack.quantity 
            else:
                return None
    
    #Packs as component of Items
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(supply_item="item_id"))      
    
     #==============================================================================   
    def shn_supply_item_add (quantity_1, pack_quantity_1, 
                             quantity_2, pack_quantity_2,): 
        """
        Adds item quantities together, accounting for different pack quantities.
        Returned quantity according to pack_quantity_1
        """
        if pack_quantity_1 == pack_quantity_2:
            # Faster calculation
            return quantity_1 + quantity_2
        else:
            return ((quantity_1*pack_quantity_1) + 
                    (quantity_2*pack_quantity_2)
                    ) / pack_quantity_1
