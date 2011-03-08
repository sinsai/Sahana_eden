# -*- coding: utf-8 -*-

"""
    Supply

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16

    Generic Supply functionality such as catalogs and items that will be used across multiple modules
"""

module = "supply"
if deployment_settings.has_module("inv"):
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
    # Item
    #
    resourcename = "item"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            item_category_id(),
                            Field("name", length=128, notnull=True, unique=True),
                            Field("base_unit", length=128),
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
        msg_list_empty = T("No Catalog Items currently registered"))
    
    def shn_item_represent(id):
        record = db(db.supply_item.id == id).select(db.supply_item.name,
                                                    db.supply_item.base_unit,
                                                    limitby=(0, 1)).first()    
        if not record:
            return NONE
        elif not record.base_unit:
            return record.name
        else:
            item_represent = "%s (%s)" % (record.name, record.base_unit)
            return item_represent


    # Reusable Field
    item_id = S3ReusableField("item_id", db.supply_item, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "supply_item.id", "%(name)s", sort=True)),
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
    #==============================================================================
    # Item Packet
    #
    resourcename = "item_packet"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            item_id(notnull=True),
                            Field("name", length=128, notnull=True), # Ideally this would reference another table for normalising Packet names
                            Field("quantity", "double", notnull=True),
                            comments(),
                            migrate=migrate, *s3_meta_fields())
    # CRUD strings
    ADD_ITEM_PACKET = T("Add Item Packet")
    LIST_ITEM_PACKET = T("List Item Packets")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ITEM_PACKET,
        title_display = T("Item Packet Details"),
        title_list = LIST_ITEM_PACKET,
        title_update = T("Edit Item Packet"),
        title_search = T("Search Item Packets"),
        subtitle_create = T("Add New Item Packet"),
        subtitle_list = T("Item Packets"),
        label_list_button = LIST_ITEM_PACKET,
        label_create_button = ADD_ITEM_PACKET,
        label_delete_button = T("Delete Item Packet"),
        msg_record_created = T("Item Packet added"),
        msg_record_modified = T("Item Packet updated"),
        msg_record_deleted = T("Item Packet deleted"),
        msg_list_empty = T("No Item Packets currently registered"))

    # Reusable Field
    item_packet_id = S3ReusableField("item_packet_id", db.supply_item_packet, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "supply_item_packet.id",
                                                "%(name)s",
                                                sort=True)),
                represent = lambda id: shn_get_db_field_value(db=db, table="supply_item_packet", field="name", look_up=id),
                label = T("Packet"),    
                comment = DIV(DIV( _class="tooltip",
                                   _title="%s|%s" % (T("Item Packets"),
                                                     T("The way in which an item is normally distributed"))),
                              A( ADD_ITEM_PACKET, 
                                 _class="colorbox", 
                                 _href=URL(r=request, 
                                           c="supply", 
                                           f="item_packet", 
                                           args="create", 
                                           vars=dict(format="popup")
                                           ), 
                                 _target="top", 
                                 _id = "item_packet_add",
                                 _style = "display: none",
                                 ),                               
                              ),
                ondelete = "RESTRICT"
                )    
    
    def shn_record_packet_quantity(r):
        item_packet_id = r.get("item_packet_id", None)
        if item_packet_id:
            return shn_get_db_field_value(db,
                                          "supply_item_packet",
                                          "quantity",
                                          item_packet_id)  
        else:
            return None  
        
    # Virtual Field for packet_quantity
    class item_packet_virtualfields(dict, object):
        def __init__(self,
                     tablename):
            self.tablename = tablename
        def packet_quantity(self):
            if self.tablename == "inv_inv_item":
                item_packet = self.inv_inv_item.item_packet_id
            elif self.tablename == "req_req_item":
                item_packet = self.req_req_item.item_packet_id
            elif self.tablename == "req_commit_item":
                item_packet = self.req_commit_item.item_packet_id       
            elif self.tablename == "inv_recv_item":
                item_packet = self.inv_recv_item.item_packet_id     
            elif self.tablename == "inv_send_item":
                item_packet = self.inv_send_item.item_packet_id                                                           
            else:
                item_packet = None
            if item_packet:
                return item_packet.quantity 
            else:
                return None
    
    #Packets as component of Items
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(supply_item="item_id"))                       
