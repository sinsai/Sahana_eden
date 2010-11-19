# -*- coding: utf-8 -*-

"""
    Inventory (Warehouse) Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16

    A module to record inventories of items at a location (store)
"""

module = "inventory"
if deployment_settings.has_module("logs"):

    #==============================================================================
    # Inventory Store / Warehouse
    #
    resourcename = "store"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            organisation_id(),
                            location_id(),
                            #document_id(),
                            person_id("contact_person_id"
                                      ),
                            super_link(db.org_site),
                            comments(),
                            migrate=migrate, *s3_meta_fields())


    table.location_id.requires = IS_ONE_OF(db, "gis_location.id", repr_select, orderby="gis_location.name", sort=True)

    table.contact_person_id.label = T("Contact Person")
    s3xrc.model.configure(table, mark_required=["location_id"])

    # -----------------------------------------------------------------------------
    def inventory_store_represent(id):
        if id:
            location = db(db.inventory_store.id == id).select(db.inventory_store.location_id, limitby=(0, 1)).first().location_id
            return shn_gis_location_represent(location)
        else:
            return NONE

    # CRUD strings
    ADD_INVENTORY_STORE = T("Add Warehouse")
    LIST_INVENTORY_STORES = T("List Warehouses")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_INVENTORY_STORE,
        title_display = T("Warehouse Details"),
        title_list = LIST_INVENTORY_STORES,
        title_update = T("Edit Warehouse"),
        title_search = T("Search Warehouses"),
        subtitle_create = T("Add New Warehouse"),
        subtitle_list = T("Warehouses"),
        label_list_button = LIST_INVENTORY_STORES,
        label_create_button = ADD_INVENTORY_STORE,
        label_delete_button = T("Delete Warehouse"),
        msg_record_created = T("Warehouse added"),
        msg_record_modified = T("Warehouse updated"),
        msg_record_deleted = T("Warehouse deleted"),
        msg_list_empty = T("No Warehouses currently registered"),
        #msg_no_match = T("No Warehouses match this criteria")
        )

    # Reusable Field
    inventory_store_id = S3ReusableField("inventory_store_id", db.inventory_store,
                requires = IS_NULL_OR(IS_ONE_OF(db, "inventory_store.id", inventory_store_represent, orderby="inventory_store.id", sort=True)),
                represent = lambda id: shn_gis_location_represent(shn_get_db_field_value(db=db, table="inventory_store", field="location_id", look_up=id)),
                label = T("Warehouse"),
                comment = DIV(A(ADD_INVENTORY_STORE, _class="colorbox", _href=URL(r=request, c="inventory", f="store", args="create", vars=dict(format="popup")), _target="top", _title=ADD_INVENTORY_STORE),
                          DIV( _class="tooltip", _title=T("Warehouse") + "|" + T("A Warehouse is a physical place which contains Relief Items available to be Distributed."))),
                ondelete = "RESTRICT"
                )

    # inventory_store as component of doc_documents and org_organisation
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(org_organisation="organisation_id"))
                                          #doc_document="document_id")

    # Also a component of sites, but these are 1-1 and use a natural join.
    s3xrc.model.add_component(module, resourcename,
                              multiple=False,
                              joinby=super_key(db.org_site))

    #==============================================================================
    # Inventory Item
    #
    resourcename = "store_item"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            inventory_store_id(),
                            item_id(),
                            Field("quantity", "double"),
                            comments(),
                            migrate=migrate, *s3_meta_fields())


    # CRUD strings
    ADD_INVENTORY_ITEM = T("Add Warehouse Item")
    LIST_INVENTORY_ITEMS = T("List Warehouse Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_INVENTORY_ITEM,
        title_display = T("Warehouse Item Details"),
        title_list = LIST_INVENTORY_ITEMS,
        title_update = T("Edit Warehouse Item"),
        title_search = T("Search Warehouse Items"),
        subtitle_create = T("Add New Warehouse Item"),
        subtitle_list = T("Warehouse Items"),
        label_list_button = LIST_INVENTORY_ITEMS,
        label_create_button = ADD_INVENTORY_ITEM,
        label_delete_button = T("Delete Warehouse Item"),
        msg_record_created = T("Warehouse Item added"),
        msg_record_modified = T("Warehouse Item updated"),
        msg_record_deleted = T("Warehouse Item deleted"),
        msg_list_empty = T("No Warehouse Items currently registered"))

    # Items as component of Stores
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(inventory_store="inventory_store_id",
                                          supply_item="item_id"))


    logs_menu = [
                [T("Home"), False, URL(r=request, c="logs", f="index")],
                [T("Warehouses"), False, URL(r=request, c="inventory", f="store"),
                [
                    [T("List"), False, URL(r=request, c="inventory", f="store")],
                    [T("Add"), False, URL(r=request, c="inventory", f="store", args="create")],
                ]],
                [T("Distributions"), False, URL(r=request, c="logs", f="distrib"),
                [
                    [T("List"), False, URL(r=request, c="logs", f="distrib")],
                    [T("Add"), False, URL(r=request, c="logs", f="distrib", args="create")],
                ]],
                [T("Catalog Items"), False, URL(r=request, c="supply", f="item"),
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
