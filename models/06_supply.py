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
                requires = IS_NULL_OR(IS_ONE_OF(db, "supply_item_category.id", "%(name)s", sort=True)),
                represent = lambda id: shn_get_db_field_value(db=db, table="supply_item_category", field="name", look_up=id),
                label = T("Category"),
                comment = DIV( _class="tooltip", _title=T("Item Category") + "|" + T("The list of Item categories are maintained by the Administrators.")),
                #comment = DIV(A(ADD_ITEM_CATEGORY, _class="colorbox", _href=URL(r=request, c="supply", f="item_category", args="create", vars=dict(format="popup")), _target="top", _title=ADD_ITEM_CATEGORY),
                #          DIV( _class="tooltip", _title=T("Item Category") + "|" + T("The category of the Item."))),
                ondelete = "RESTRICT"
                )

    #==============================================================================
    # Units
    #
    logs_unit_opts = {
        "piece" : T("piece"),
        "kit" : T("kit"),
        "sack50kg" : T("sack 50kg"),
        "sack20kg" : T("sack 20kg"),
        "pack10" : T("pack of 10"),
        "m" : T("meter"),
        "m3" : T("meter cubed"),
        "l" : T("liter"),
        "kg" : T("kilogram"),
        "ton" : T("ton"),
    }
    
    #==============================================================================
    # Item
    #
    resourcename = "item"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            item_category_id(),
                            Field("name", length=128, notnull=True, unique=True),
                            Field("unit", notnull=True, default="piece",
                                  requires = IS_IN_SET(logs_unit_opts, zero=None),
                                  represent = lambda opt: logs_unit_opts.get(opt, T("not specified"))
                                 ),
                            comments(), # These comments do *not* pull through to an Inventory's Items or a Request's Items
                            migrate=migrate, *s3_meta_fields())


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
    
    def shn_item_represent(id):
        record = db(db.supply_item.id == id).select(db.supply_item.name,
                                                    db.supply_item.unit,
                                                    limitby=(0, 1)).first()    
        if not record:
            return NONE
        elif not record.unit:
            return record.name
        else:
            item_represent = "%s (%s)" % (record.name, record.unit)
            return item_represent


    # Reusable Field
    item_id = S3ReusableField("item_id", db.supply_item, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "supply_item.id", "%(name)s (%(unit)s)", sort=True)),
                represent = shn_item_represent,
                label = T("Item"),
                comment = DIV(A(ADD_ITEM, _class="colorbox", _href=URL(r=request, c="supply", f="item", args="create", vars=dict(format="popup")), _target="top", _title=ADD_ITEM),
                          DIV( _class="tooltip", _title=T("Relief Item") + "|" + T("Add a new Relief Item."))),
                ondelete = "RESTRICT"
                )
