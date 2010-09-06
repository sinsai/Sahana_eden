# -*- coding: utf-8 -*-

"""
    Logistics Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-09-02

    Distribution, Shipments

"""

module = "logs"
if deployment_settings.has_module(module):
    #==============================================================================
    # Distribution
    #
    resource = "distrib"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp,
                            uuidstamp,
                            authorstamp,
                            deletion_status,
                            Field("date", "date"),
                            location_id,
                            #site_id,
                            comments,
                            migrate=migrate)

    # -----------------------------------------------------------------------------
    def distrib_represent(id):
        if id:
            distrib_row = db(db.logs_distrib.id == id).select(db.logs_distrib.location_id, db.logs_distrib.date, limitby=(0, 1)).first()
            location = shn_get_db_field_value(db = db,
                                              table = "gis_location",
                                              field = "name",
                                              look_up = distrib_row.location_id
                                              )
            return "%s - %s" % (shn_gis_location_represent(location), distrib_row.date)
        else:
            return NONE

    # CRUD strings
    ADD_DISTRIBUTION = T("Add Distribution")
    LIST_DISTRIBUTIONS = T("List Distributions")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_DISTRIBUTION,
        title_display = T("Distribution Details"),
        title_list = LIST_DISTRIBUTIONS,
        title_update = T("Edit Distribution"),
        title_search = T("Search Distributions"),
        subtitle_create = T("Add New Distribution"),
        subtitle_list = T("Distributions"),
        label_list_button = LIST_DISTRIBUTIONS,
        label_create_button = ADD_DISTRIBUTION,
        label_delete_button = T("Delete Distribution"),
        msg_record_created = T("Distribution added"),
        msg_record_modified = T("Distribution updated"),
        msg_record_deleted = T("Distribution deleted"),
        msg_list_empty = T("No Distributions currently registered"))

    # Reusable Field
    distrib_id = db.Table(None, "distrib_id",
            FieldS3("distrib_id", db.logs_distrib, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "logs_distrib.id", distrib_represent, orderby="logs_distrib.date", sort=True)),
                represent = distrib_represent,
                label = T("Distribution"),
                #comment = DIV(A(ADD_DISTRIBUTION, _class="colorbox", _href=URL(r=request, c="logs", f="distrib", args="create", vars=dict(format="popup")), _target="top", _title=ADD_DISTRIBUTION),
                #          DIV( _class="tooltip", _title=Tstr("Distribution") + "|" + Tstr("Add Distribution."))),
                ondelete = "RESTRICT"
                ))

    #==============================================================================
    # Distribution Item
    #
    resource = "distrib_item"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp,
                            uuidstamp,
                            authorstamp,
                            deletion_status,
                            distrib_id,
                            item_id,
                            Field("quantity", "double"),
                            comments,
                            migrate=migrate)

    # CRUD strings
    ADD_DISTRIBUTION_ITEM = T("Distribution Item")
    LIST_DISTRIBUTION_ITEMS = T("List Distribution Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_DISTRIBUTION_ITEM,
        title_display = T("Distribution Item Details"),
        title_list = LIST_DISTRIBUTION_ITEMS,
        title_update = T("Edit Distribution Item"),
        title_search = T("Search Distribution Items"),
        subtitle_create = T("Add New Distribution Item"),
        subtitle_list = T("Distribution Items"),
        label_list_button = LIST_DISTRIBUTION_ITEMS,
        label_create_button = ADD_DISTRIBUTION_ITEM,
        label_delete_button = T("Delete Distribution Item"),
        msg_record_created = T("Distribution Item added"),
        msg_record_modified = T("Distribution Item updated"),
        msg_record_deleted = T("Distribution Item deleted"),
        msg_list_empty = T("No Distribution Items currently registered"))

    # Items as component of Distributions
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(logs_distrib="distrib_id", supply_item="item_id"),
                              deletable=True,
                              editable=True)