# -*- coding: utf-8 -*-

"""
    Inventory

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16

    A module to record inventories of items at a location (store)
"""

module = "inventory"
if deployment_settings.has_module("logs"):

    #==============================================================================
    # Inventory Store
    #
    resource = "store"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp,
                            uuidstamp,
                            authorstamp,
                            deletion_status,
                            location_id,
                            document_id,
                            site_id,
                            comments,
                            migrate=migrate)

    table.location_id.requires = IS_ONE_OF(db, "gis_location.id", repr_select, orderby="gis_location.name", sort=True)
    table.location_id.comment = DIV(table.location_id.comment, SPAN("*", _class="req"))

    # -----------------------------------------------------------------------------
    def inventory_store_represent(id):
        if id:
            location = db(db.inventory_store.id == id).select(db.inventory_store.location_id, limitby=(0, 1)).first().location_id
            return shn_gis_location_represent(location)
        else:
            return NONE

    # CRUD strings
    ADD_INVENTORY_STORE = T("Add Inventory Store")
    LIST_INVENTORY_STORES = T("List Inventory Stores")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_INVENTORY_STORE,
        title_display = T("Inventory Store Details"),
        title_list = LIST_INVENTORY_STORES,
        title_update = T("Edit Inventory Store"),
        title_search = T("Search Inventory Stores"),
        subtitle_create = T("Add New Inventory Store"),
        subtitle_list = T("Inventory Stores"),
        label_list_button = LIST_INVENTORY_STORES,
        label_create_button = ADD_INVENTORY_STORE,
        label_delete_button = T("Delete Inventory Store"),
        msg_record_created = T("Inventory Store added"),
        msg_record_modified = T("Inventory Store updated"),
        msg_record_deleted = T("Inventory Store deleted"),
        msg_list_empty = T("No Inventory Stores currently registered"))

    # Reusable Field
    inventory_store_id = db.Table(None, "inventory_store_id",
            FieldS3("inventory_store_id", db.inventory_store, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "inventory_store.id", inventory_store_represent, orderby="inventory_store.id", sort=True)),
                represent = lambda id: shn_gis_location_represent(shn_get_db_field_value(db=db, table="inventory_store", field="location_id", look_up=id)),
                label = T("Inventory Store"),
                comment = DIV(A(ADD_INVENTORY_STORE, _class="colorbox", _href=URL(r=request, c="inventory", f="store", args="create", vars=dict(format="popup")), _target="top", _title=ADD_INVENTORY_STORE),
                          DIV( _class="tooltip", _title=Tstr("Inventory Store") + "|" + Tstr("An Inventory Store is a physical place which contains Relief Items available to be Distributed."))),
                ondelete = "RESTRICT"
                ))

    # inventory_store as component of doc_documents
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(doc_document="document_id"),
                              deletable=True,
                              editable=True)
    # Also a component of sites, but these are 1-1 and use a natural join.
    # @ToDo Should these be editable and deletable?  Or should an
    # inventory store be created when a site is created?
    # @ToDo Is multiple assumed True or False?  It's not touched
    # in add_component, so safest to set it explicitly.
    s3xrc.model.add_component(module, resource,
                              multiple=False,
                              joinby="site_id",
                              deletable=True,
                              editable=True)

    #==============================================================================
    # Inventory Item
    #
    resource = "store_item"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp,
                            uuidstamp,
                            authorstamp,
                            deletion_status,
                            inventory_store_id,
                            item_id,
                            Field("quantity", "double"),
                            comments,
                            migrate=migrate)

    # CRUD strings
    ADD_INVENTORY_ITEM = T("Add Inventory Item")
    LIST_INVENTORY_ITEMS = T("List Inventory Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_INVENTORY_ITEM,
        title_display = T("Inventory Item Details"),
        title_list = LIST_INVENTORY_ITEMS,
        title_update = T("Edit Inventory Item"),
        title_search = T("Search Inventory Items"),
        subtitle_create = T("Add New Inventory Item"),
        subtitle_list = T("Inventory Items"),
        label_list_button = LIST_INVENTORY_ITEMS,
        label_create_button = ADD_INVENTORY_ITEM,
        label_delete_button = T("Delete Inventory Item"),
        msg_record_created = T("Inventory Item added"),
        msg_record_modified = T("Inventory Item updated"),
        msg_record_deleted = T("Inventory Item deleted"),
        msg_list_empty = T("No Inventory Items currently registered"))

    # Items as component of Stores
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(inventory_store="inventory_store_id", supply_item="item_id"),
                              deletable=True,
                              editable=True)


    logs_menu = [
                [T("Home"), False, URL(r=request, c="logs", f="index")],
                [T("Inventory Stores"), False, URL(r=request, c="inventory", f="store"),
                [
                    [T("List"), False, URL(r=request, c="inventory", f="store")],
                    [T("Add"), False, URL(r=request, c="inventory", f="store", args="create")],
                ]],
                [T("Distributions"), False, URL(r=request, c="logs", f="distrib"),
                [
                    [T("List"), False, URL(r=request, c="logs", f="distrib")],
                    [T("Add"), False, URL(r=request, c="logs", f="distrib", args="create")],
                ]],
                [T("Relief Items"), False, URL(r=request, c="supply", f="item"),
                [
                    [T("List"), False, URL(r=request, c="supply", f="item")],
                    [T("Add"), False, URL(r=request, c="supply", f="item", args="create")],
                ]],
                ]
    if shn_has_role(1):
        logs_menu.append(
            [T("Item Categories"), False, URL(r=request, c="supply", f="item_category"),[
                [T("List"), False, URL(r=request, c="supply", f="item_category")],
                [T("Add"), False, URL(r=request, c="supply", f="item_category", args="create")]
            ]]
        )
