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
    # Settings
    #
    resource = "setting"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field("audit_read", "boolean"),
                            Field("audit_write", "boolean"),
                            migrate=migrate)


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

    s3.crud_strings[tablename] = shn_crud_strings("Distribution")

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
    
    def get_distrib_id (field_name = "distrib_id", 
                                   label = T("Distribution"),
                                   ):
                                   
        requires = IS_NULL_OR(IS_ONE_OF(db, "logs_distrib.id", distrib_represent, sort=True))
        
        represent = distrib_represent
        
        comment = DIV( A( "Add Distribution",
                          _class="colorbox",
                          _href=URL(r=request, 
                                    c="log", 
                                    f="distrib", 
                                    args="create", 
                                    vars=dict(format="popup", child=field_name)
                                    ),
                          _target="top",
                          _title="Add Distribution",
                          ),
                       DIV( _class="tooltip",
                            _title=Tstr("Distribution") + "|" + Tstr("Add Distribution")
                            )
                       )

        return db.Table(None, 
                        field_name,
                        FieldS3(field_name, 
                                db.logs_distrib, #sortby="name",
                                requires = requires,
                                represent = represent,
                                label = label,
                                comment = comment,
                                ondelete = "RESTRICT"
                                )
                        )

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
                            get_distrib_id(),
                            get_item_id(),
                            Field("quantity", "double"),
                            comments,
                            migrate=migrate)

    s3.crud_strings[tablename] = shn_crud_strings("Distribution Item")

    # Items as component of Distributions
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(logs_distrib="distrib_id", supply_item="item_id"),
                              deletable=True,
                              editable=True)