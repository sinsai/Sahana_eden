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
                            person_id("contact_person_id"),
                            super_link(db.org_site),
                            comments(),
                            migrate=migrate, *s3_meta_fields())


    table.location_id.requires = IS_ONE_OF(db, "gis_location.id", repr_select, orderby="gis_location.name", sort=True)

    table.contact_person_id.label = T("Contact Person")
    
    def inventory_store_onvalidation(form): 
        if form.vars.location_id == None: 
            form.errors.location_id = T("Enter a location") 
        return

    s3xrc.model.configure(table,
                          onvalidation=inventory_store_onvalidation,
                          mark_required=["location_id"])

    # -----------------------------------------------------------------------------
    def inventory_store_represent(id, link = True):
        if id:
            location = db( ( db.inventory_store.id == id ) & \
                           ( db.gis_location.id == db.inventory_store.location_id )
                          ).select(db.gis_location.name, limitby=(0, 1)).first().name
            if link:
                return A(location,
                         _href = URL(r = request,
                                     c = "inventory",
                                     f = "store",
                                     args = [id]
                                     )
                         )
            else:
                return location
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
                represent = inventory_store_represent,
                label = T("Warehouse"),
                comment = DIV(A(ADD_INVENTORY_STORE, _class="colorbox", _href=URL(r=request, c="inventory", f="store", args="create", vars=dict(format="popup")), _target="top", _title=ADD_INVENTORY_STORE),
                          DIV( _class="tooltip", _title=T("Warehouse") + "|" + T("A Warehouse is a physical place to store items."))),
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
    # -----------------------------------------------------------------------------
    #Ideally should be on create
    def inventory_store_onaccept(form):
        #Adds a group for user with authorization for store
        store_id = session.rcvars.inventory_store
        store_name = inventory_store_represent(store_id, link = False)
        if not auth.id_group("store_%s" % store_id):
            store_group_id = auth.s3_create_role( "store_%s" % store_id,
                                                  "group for user with authorization for store '%s'" % store_name,
                                                  dict(c="inventory", uacl=auth.permission.READ, oacl=auth.permission.ALL)
                                                  )
            db.inventory_store[store_id] = dict(owned_by = store_group_id)
    s3xrc.model.configure(table, onaccept=inventory_store_onaccept)

    #==============================================================================
    # Inventory Item
    #
    resourcename = "store_item"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            inventory_store_id(),
                            item_id(),
                            item_packet_id(),
                            Field("quantity", 
                                  "double",
                                  notnull = True),
                            Field("packet_quantity",
                                  "double",
                                  compute = shn_record_packet_quantity),                               
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
    
    def shn_inventory_store_item_represent (id):
        record = db( (db.inventory_store_item.id == id) & \
                     (db.inventory_store_item.item_id == db.supply_item.id) 
                    ).select( db.supply_item.name,
                              limitby = [0,1]).first()
        if record:
            return record.name
        else:
            return None  

    # Reusable Field
    store_item_id = S3ReusableField("store_item_id", db.inventory_store_item,
                requires = IS_ONE_OF(db, 
                                     "inventory_store_item.id", 
                                     shn_inventory_store_item_represent, 
                                     orderby="inventory_store_item.id", 
                                     sort=True),
                represent = shn_inventory_store_item_represent,
                label = T("Warehouse Item"),
                comment = DIV( _class="tooltip", _title=T("Warehouse Item") + "|" + T("Select Items from this Warehouse")),
                ondelete = "RESTRICT"
                )    

    # Items as component of Stores
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(inventory_store="inventory_store_id")
                              )
    
    s3xrc.model.add_component(module, resourcename,
                              multiple=False,
                              joinby=dict(supply_item="item_id")
                              )     
    #==============================================================================
    # Inventory Store User
    #
    resourcename = "store_user"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            inventory_store_id(),
                            Field("user_id",
                                  auth.settings.table_user,
                                  requires = IS_IN_DB(db, "%s.id" %
                                                      auth.settings.table_user._tablename,
                                                      "%(id)s: %(first_name)s %(last_name)s")
                                  ),
                            migrate=migrate, *s3_meta_fields())
    # CRUD strings
    ADD_INVENTORY_USER = T("Add Warehouse User")
    LIST_INVENTORY_USERS = T("List Warehouse Users")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_INVENTORY_USER,
        title_display = T("Warehouse User Details"),
        title_list = LIST_INVENTORY_USERS,
        title_update = T("Edit Warehouse User"),
        title_search = T("Search Warehouse Users"),
        subtitle_create = T("Add New Warehouse User"),
        subtitle_list = T("Warehouse User"),
        label_list_button = LIST_INVENTORY_USERS,
        label_create_button = ADD_INVENTORY_USER,
        label_delete_button = T("Delete Warehouse User"),
        msg_record_created = T("Warehouse User added"),
        msg_record_modified = T("Warehouse User updated"),
        msg_record_deleted = T("Warehouse User deleted"),
        msg_list_empty = T("No Warehouse Users currently registered")) 
    
    # User as component of Stores
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(inventory_store="inventory_store_id")
                              )
    # -----------------------------------------------------------------------------
    def store_user_onaccept(form):
        #Updates the membership of the store group
        inventory_store_id = session.rcvars.inventory_store
        store_group_id = shn_get_db_field_value(db,
                                                "inventory_store",
                                                "owned_by",
                                                inventory_store_id )
        group_members = auth.s3_group_members(store_group_id)
        store_users = [ store_user.user_id for store_user in 
                        db( (db.inventory_store_user.inventory_store_id == 
                                inventory_store_id ) & \
                            (db.inventory_store_user.deleted == False )    
                           ).select(db.inventory_store_user.user_id)
                       ]
        
        #Add store users to group not currently in group
        for store_user in store_users:
            if store_user not in group_members:
                auth.add_membership(group_id = store_group_id,
                                    user_id = store_user)
        #Delete members from group who are no longer store users
        for group_member in group_members:
            if group_member not in store_users:
                auth.del_membership(group_id = store_group_id,
                                    user_id = store_user)                
    s3xrc.model.configure(table, onaccept = store_user_onaccept)    