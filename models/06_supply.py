# -*- coding: utf-8 -*-

"""
    Supply 
    
    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16    
    
    Generic Supply functionality such as catalogs and items that will be used across multiple modules
"""

module = "supply"
if deployment_settings.has_module("logs"):
    #==============================================================================
    # Item Category
    #
    resource = "item_category"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, 
                            timestamp, 
                            uuidstamp, 
                            authorstamp, 
                            deletion_status,
                            Field("name", length=128, notnull=True, unique=True),
                            comments,
                            migrate=migrate)

    table.name.comment = SPAN("*", _class="req")

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
    item_category_id = db.Table(None, "item_category_id",
            FieldS3("item_category_id", db.supply_item_category, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "supply_item_category.id", "%(name)s", sort=True)),
                represent = lambda id: shn_get_db_field_value(db=db, table="supply_item_category", field="name", look_up=id),
                label = T("Category"),
                comment = DIV( _class="tooltip", _title=Tstr("Item Category") + "|" + Tstr("The list of Item categories are maintained by the Administrators.")),
                #comment = DIV(A(ADD_ITEM_CATEGORY, _class="colorbox", _href=URL(r=request, c="supply", f="item_category", args="create", vars=dict(format="popup")), _target="top", _title=ADD_ITEM_CATEGORY),
                #          DIV( _class="tooltip", _title=Tstr("Item Category") + "|" + Tstr("The category of the Item."))),
                ondelete = "RESTRICT"
                ))
    
    #==============================================================================
    # Item
    #
    resource = "item"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, 
                            timestamp, 
                            uuidstamp, 
                            authorstamp, 
                            deletion_status,                        
                            item_category_id,
                            Field("name", length=128, notnull=True, unique=True),
                            comments,
                            migrate=migrate)

    table.name.comment = SPAN("*", _class="req")

    # CRUD strings
    ADD_ITEM = T("Add Item")
    LIST_ITEMS = T("List Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ITEM,
        title_display = T("Item Details"),
        title_list = LIST_ITEMS,
        title_update = T("Edit Item"),
        title_search = T("Search Items"),
        subtitle_create = T("Add New Item"),
        subtitle_list = T("Items"),
        label_list_button = LIST_ITEMS,
        label_create_button = ADD_ITEM,
        label_delete_button = T("Delete Item"),
        msg_record_created = T("Item added"),
        msg_record_modified = T("Item updated"),
        msg_record_deleted = T("Item deleted"),
        msg_list_empty = T("No Items currently registered"))
    
    # Reusable Field
    item_id = db.Table(None, "item_id",
            FieldS3("item_id", db.supply_item, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "supply_item.id", "%(name)s", sort=True)),
                represent = lambda id: shn_get_db_field_value(db=db, table="supply_item", field="name", look_up=id),
                label = T("Item"),
                comment = DIV(A(ADD_ITEM, _class="colorbox", _href=URL(r=request, c="supply", f="item", args="create", vars=dict(format="popup")), _target="top", _title=ADD_ITEM),
                          DIV( _class="tooltip", _title=Tstr("Relief Item") + "|" + Tstr("Add a new Relief Item."))),
                ondelete = "RESTRICT"
                ))
