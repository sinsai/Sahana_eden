# -*- coding: utf-8 -*-

"""
    Impact

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-10-12

    Impact resources used by I(ncident)RS and Assessment 
"""

module = "impact"
if deployment_settings.has_module("irs") or deployment_settings.has_module("assess"):
    # -----------------------------------------------------------------------------
    # Impact Type
    resource = "type"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field("name", length=128, notnull=True, unique=True),
                            migrate=migrate, *s3_meta_fields()
                            )        
    
    # CRUD strings
    ADD_IMPACT_TYPE = T("Add Impact Type")
    LIST_IMPACT_TYPE = T("List Impact Types")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_IMPACT_TYPE,
        title_display = T("Impact Type Details"),
        title_list = LIST_IMPACT_TYPE,
        title_update = T("Edit Impact Type"),
        title_search = T("Search Impact Type"),
        subtitle_create = T("Add New Impact Type"),
        subtitle_list = T("Impact Types"),
        label_list_button = LIST_IMPACT_TYPE,
        label_create_button = ADD_IMPACT_TYPE,
        label_delete_button = T("Delete Impact Type"),
        msg_record_created = T("Impact Type added"),
        msg_record_modified = T("Impact Type updated"),
        msg_record_deleted = T("Impact Type deleted"),
        msg_list_empty = T("No Impact Types currently registered"))  
    
    def impact_type_comment():
        if auth.has_membership(auth.id_group("'Administrator'")):
            return DIV(A(ADD_IMPACT_TYPE,
                         _class="colorbox",
                         _href=URL(r=request, c="impact", f="type", args="create", vars=dict(format="popup")),
                         _target="top",
                         _title=ADD_IMPACT_TYPE
                         )
                       )
        else:
            return None    

    impact_type_id = S3ReusableField("impact_type_id", db.impact_type, sortby="name",
                                       requires = IS_NULL_OR(IS_ONE_OF(db, "impact_type.id","%(name)s", sort=True)),
                                       represent = lambda id: shn_get_db_field_value(db = db,
                                                                                     table = "impact_type",
                                                                                     field = "name",
                                                                                     look_up = id),
                                       label = T("Impact Type"),
                                       comment = impact_type_comment(),
                                       ondelete = "RESTRICT"
                                       )    
    
    shn_import_table("impact_type")
    
    # -----------------------------------------------------------------------------
    # Impact
    resource = "impact"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            incident_id(),
                            assess_id(),
                            impact_type_id(),
                            Field("value", "double"),
                            comments(),
                            migrate=migrate, *s3_meta_fields()
                            )        
    
    #Hide fk fields in forms
    table.incident_id.readable = table.incident_id.writable = False
    table.assess_id.readable = table.assess_id.writable = False
    
    # CRUD strings
    ADD_IMPACT = T("Add Impact")
    LIST_IMPACT = T("List Impacts")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_IMPACT,
        title_display = T("Impact Details"),
        title_list = LIST_IMPACT,
        title_update = T("Edit Impact"),
        title_search = T("Search Impacts"),
        subtitle_create = T("Add New Impact"),
        subtitle_list = T("Impacts"),
        label_list_button = LIST_IMPACT,
        label_create_button = ADD_IMPACT,
        label_delete_button = T("Delete Impact"),
        msg_record_created = T("Impact added"),
        msg_record_modified = T("Impact updated"),
        msg_record_deleted = T("Impact deleted"),
        msg_list_empty = T("No Impacts currently registered"))     
    
    # Impact as component of assessments and incidents
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(assess_assess="assess_id", irs_incident="incident_id"),
                              deletable=True,
                              editable=True)  
    
    # -----------------------------------------------------------------------------
                        