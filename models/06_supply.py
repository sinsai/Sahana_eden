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
                comment = DIV(A(ADD_ITEM, _class="colorbox", _href=URL(r=request, c="supply", f="item", args="create", vars=dict(format="popup")), _target="top", _title=ADD_ITEM),
                          DIV( _class="tooltip", _title=T("Catalog Item") + "|" + ADD_ITEM)),
                ondelete = "RESTRICT"
                )    
    #==============================================================================
    # Item Packet
    #
    resourcename = "item_packet"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            item_id(notnull=True),
                            Field("name", length=128, notnull=True), #Ideally this would reference another table for normalising Packet names
                            Field("quantity", "double", notnull=True),
                            comments(),
                            migrate=migrate, *s3_meta_fields())
    # CRUD strings
    ADD_ITEM_PACKET = T("Add Item Packet")
    LIST_ITEM_PACKET = T("List Item Packets")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ITEM_CATEGORY,
        title_display = T("Item Packet Details"),
        title_list = LIST_ITEM_CATEGORIES,
        title_update = T("Edit Item Packet"),
        title_search = T("Search Item Packets"),
        subtitle_create = T("Add New Item Packet"),
        subtitle_list = T("Item Packets"),
        label_list_button = LIST_ITEM_CATEGORIES,
        label_create_button = ADD_ITEM_CATEGORY,
        label_delete_button = T("Delete Item Packet"),
        msg_record_created = T("Item Packet added"),
        msg_record_modified = T("Item Packet updated"),
        msg_record_deleted = T("Item Packet deleted"),
        msg_list_empty = T("No Item Packets currently registered"))

    # Reusable Field
    item_packet_id = S3ReusableField("item_packet_id", db.supply_item_packet, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "supply_item_packet.id", "%(name)s", sort=True)),
                represent = lambda id: shn_get_db_field_value(db=db, table="supply_item_packet", field="name", look_up=id),
                label = T("Packet"),    
                comment = DIV(DIV( _class="tooltip", _title=T("Item Packets") + "|" + T("Needs elaboration!!!")),
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
                                 IMG(_src = "/" + request.application + "/static/img/ajax-loader.gif",
                                     _id = "item_packet_loader_img",
                                     _style = "display:none;"
                                      ),                                     
                SCRIPT("""
    function ItemIDChange() {                
        var selSubField = $('[name = "item_packet_id"]');
        
        $('[id$="item_packet_id__row1"]').show();
        $('[id$="item_packet_id__row"]').show();        
        
        /* Show Throbber */
        selSubField.after('<img src="/eden/static/img/ajax-loader.gif" id="item_packet_loader_img">');
        selSubField.hide();
        
        if ($('[name = "item_id"]').length != 0) {
            url = '/eden/supply/item_packet.json?item_packet.item_id=' + $('[name = "item_id"]').val();
        } else {
            url = '/eden/inventory/store_item_packets/' + $('[name $= "item_id"]').val();
        }
                                
        $.getJSON(url, function(data) {
            /* Create Select Element */
            var options = '';
            var v = '';
            
            if (data.length == 0) {
                options += '<option value="">' + '{{=T("No Packets  for Item")}}</options>';
            } else {
                for (var i = 0; i < data.length; i++){
                    v = data[i].id;
                    options += '<option value="' +  data[i].id + '">' + data[i].name + ' (' + data[i].quantity + ')</option>';
                }                
            }
            selSubField.html(options);  
            selSubField.val(1); /* default value */       
            selSubField.show(); 
            
            /* Show "Add" Button & modify link */  
            href = $('#item_packet_add').attr('href') + "&item_id=" + $('[name = "item_id"]').val();
            $('#item_packet_add').attr('href', href)
            $('#item_packet_add').show();
            
            /* Hide Throbber */
            $('#item_packet_loader_img').remove();
            
            if ( typeof ItemPacketIDChange == "function" ) {
                ItemPacketIDChange();
            }; 
        });   
    }
                
    if ($('[name $= "item_id"]').val() == '') {
        /* Hide the item packet input if the item hasn't been entered */
        $('[id$="item_packet_id__row1"]').hide();
        $('[id$="item_packet_id__row"]').hide();    
    } else {
        /* Show the item packet input id the item has already been entered (if this is an error or update) */      
        ItemIDChange();
    }
   
    /* Includes Inventory Item too */
    $('[name $= "item_id"]').change(ItemIDChange);
                """) ),

                ondelete = "RESTRICT"
                )    
    
    def shn_record_packet_quantity(r):
        item_packet_id = r.get("item_packet_id",None)
        if item_packet_id:
            return shn_get_db_field_value(db,
                                          "supply_item_packet",
                                          "quantity",
                                          item_packet_id)  
        else:
            return None  
    
    #Packets as component of Items
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(supply_item="item_id"))        
    
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
        
