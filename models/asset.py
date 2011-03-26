# -*- coding: utf-8 -*-

""" Asset

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2011-03-18

    Asset Management Functionality

"""

module = "asset"
if deployment_settings.has_module(module):
    #==========================================================================
    # Asset 
    #
    resourcename = "asset"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("number",
                                  label = T("Asset Number")),
                            item_id(),                            
                            Field("sn",
                                  label = T("Serial Number"),
                                  ),
                            Field("purchase_date",
                                  "date"),        
                            comments(),
                            migrate=migrate, *s3_meta_fields())


    # CRUD strings
    ADD_ASSET = T("Add Asset")
    LIST_ASSET = T("List Assets")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ASSET,
        title_display = T("Asset Details"),
        title_list = LIST_ASSET,
        title_update = T("Edit Asset"),
        title_search = T("Search Assets"),
        subtitle_create = T("Add New Asset"),
        subtitle_list = T("Assets"),
        label_list_button = LIST_ASSET,
        label_create_button = ADD_ASSET,
        label_delete_button = T("Delete Asset"),
        msg_record_created = T("Asset added"),
        msg_record_modified = T("Asset updated"),
        msg_record_deleted = T("Asset deleted"),
        msg_list_empty = T("No Assets currently registered"))
    
    def shn_asset_represent(id):
        """
            include item fields
        """
        return shn_get_db_field_value(db=db, table="asset_asset", 
                                      field="number", look_up=id)

    # Reusable Field
    asset_id = S3ReusableField("asset_id", db.asset_asset, sortby="number",
                requires = IS_NULL_OR(IS_ONE_OF(db, "asset_asset.id",
                                                "%(number)s",
                                                sort=True)),
                represent = shn_asset_represent,
                label = T("Asset"),
                ondelete = "RESTRICT"
                )
        
    #==========================================================================
    # Asset Assignment
    # @ToDo: Look at using S3Track to help with this
    #
    resourcename = "assign"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            asset_id(),
                            Field("datetime_from",
                                  "datetime"),
                            Field("datetime_until",
                                  "datetime"),    
                            location_id("to_location_id",
                                        label = T("To Location"),
                                        ),      
                            location_id("from_location_id",
                                        label = T("From Location"),
                                        ), 
                            organisation_id("to_organisation_id",
                                        label = T("To Organization"),
                                        ),      
                            organisation_id("from_organisation_id",
                                        label = T("From Organization"),
                                        ),                                           
                            person_id("to_person_id",
                                        label = T("To Person"),
                                        ),      
                            person_id("from_person_id",
                                        label = T("From Person"),
                                        ),                                  
                            comments(),
                            migrate=migrate, *s3_meta_fields())

    # CRUD strings
    ADD_ASSIGN = T("Assign Asset")
    LIST_ASSIGN = T("List Asset Assignments")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ASSIGN,
        title_display = T("Asset Assignment Details"),
        title_list = LIST_ASSIGN,
        title_update = T("Edit Asset Assignment"),
        title_search = T("Search Asset Assignments"),
        subtitle_create = ADD_ASSIGN,
        subtitle_list = T("Asset Assignments"),
        label_list_button = LIST_ITEM_CATEGORIES,
        label_create_button = LIST_ASSIGN,
        label_delete_button = T("Delete Asset Assignments"),
        msg_record_created = T("Asset Assigned"),
        msg_record_modified = T("Asset Assignments updated"),
        msg_record_deleted = T("Asset Assignments deleted"),
        msg_list_empty = T("No Asset Assignments currently registered"))

    # assign as component of asset
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(asset_asset="asset_id"))

# END =========================================================================