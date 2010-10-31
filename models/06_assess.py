# -*- coding: utf-8 -*-

""" Assessment - Model

    @author: Michael Howden
"""

module = "assess"
if deployment_settings.has_module(module):
    #==============================================================================
    # Assement
    # This is the current status of an Incident
    # @ToDo Change this so that there is a 'lead' ireport updated in the case of duplicates
    resourcename = "assess"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("datetime", "datetime"),
                            location_id(),
                            organisation_id(), 
                            person_id("assessor_person_id"                                      
                                      ),
                            comments(),
                            migrate=migrate, *s3_meta_fields()
                            )
    
    table.datetime.label = T("Date & Time")
    table.datetime.default = request.utcnow
    
    table.assessor_person_id.label = T("Assessor")
    if auth.is_logged_in():
        table.assessor_person_id.default = shn_get_db_field_value(db = db,
                                                                  table = "pr_person",
                                                                  field = "pe_id",
                                                                  look_up = session.auth.user.person_uuid,
                                                                  look_up_field = "uuid"
                                                                  )
    
    assess_id = S3ReusableField("assess_id", table,
                                  requires = IS_NULL_OR(IS_ONE_OF(db, "assess_assess.id", "%(id)s")),
                                  represent = lambda id: id,
                                  label = T("Assessment"),
                                  ondelete = "RESTRICT"
                                  )    
    
    # CRUD strings
    ADD_ASSESSMENT = T("Add Assessment")
    LIST_ASSESSMENTS = T("List Assessments")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ASSESSMENT,
        title_display = T("Assessment Details"),
        title_list = LIST_ASSESSMENTS,
        title_update = T("Edit Assessment"),
        title_search = T("Search Assessments"),
        subtitle_create = T("Add New Assessment"),
        subtitle_list = T("Assessments"),
        label_list_button = LIST_ASSESSMENTS,
        label_create_button = ADD_ASSESSMENT,
        label_delete_button = T("Delete Assessment"),
        msg_record_created = T("Assessment added"),
        msg_record_modified = T("Assessment updated"),
        msg_record_deleted = T("Assessment deleted"),
        msg_list_empty = T("No Assessments currently registered"))
    
    #assess_assess as component of org_organisation
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(org_organisation="organisation_id"
                                          )
                              )    
    
    #==============================================================================
    # Baseline Type
    resourcename = "baseline_type"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("name", length=128, notnull=True, unique=True),
                            migrate=migrate, *s3_meta_fields()
                            )        
    
    # CRUD strings
    ADD_BASELINE_TYPE = T("Add Baseline Type")
    LIST_BASELINE_TYPE = T("List Baseline Types")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_BASELINE_TYPE,
        title_display = T("Baseline Type Details"),
        title_list = LIST_BASELINE_TYPE,
        title_update = T("Edit Baseline Type"),
        title_search = T("Search Baseline Type"),
        subtitle_create = T("Add New Baseline Type"),
        subtitle_list = T("Baseline Types"),
        label_list_button = LIST_BASELINE_TYPE,
        label_create_button = ADD_BASELINE_TYPE,
        label_delete_button = T("Delete Baseline Type"),
        msg_record_created = T("Baseline Type added"),
        msg_record_modified = T("Baseline Type updated"),
        msg_record_deleted = T("Baseline Type deleted"),
        msg_list_empty = T("No Baseline Types currently registered"))  
    
    def baseline_type_comment():
        if auth.has_membership(auth.id_group("'Administrator'")):
            return DIV(A(ADD_BASELINE_TYPE,
                         _class="colorbox",
                         _href=URL(r=request, c="assess", f="baseline_type", args="create", vars=dict(format="popup")),
                         _target="top",
                         _title=ADD_BASELINE_TYPE
                         )
                       )
        else:
            return None    

    baseline_type_id = S3ReusableField("baseline_type_id", db.assess_baseline_type, sortby="name",
                                       requires = IS_NULL_OR(IS_ONE_OF(db, "assess_baseline_type.id","%(name)s", sort=True)),
                                       represent = lambda id: shn_get_db_field_value(db = db,
                                                                                     table = "assess_baseline_type",
                                                                                     field = "name",
                                                                                     look_up = id),
                                       label = T("Baseline Type"),
                                       comment = baseline_type_comment(),
                                       ondelete = "RESTRICT"
                                       )    
    
    #==============================================================================
    # Baseline
    resourcename = "baseline"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            assess_id(),
                            baseline_type_id(),
                            Field("value", "double"),
                            comments(),
                            migrate=migrate, *s3_meta_fields()
                            )        
    
    #Hide fk fields in forms
    table.assess_id.readable = table.assess_id.writable = False    
    
    # CRUD strings
    ADD_BASELINE = T("Add Baseline")
    LIST_BASELINE = T("List Baselines")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_BASELINE,
        title_display = T("Impact Baselines"),
        title_list = LIST_BASELINE,
        title_update = T("Edit Baseline"),
        title_search = T("Search Baselines"),
        subtitle_create = T("Add New Baseline"),
        subtitle_list = T("Baselines"),
        label_list_button = LIST_BASELINE,
        label_create_button = ADD_BASELINE,
        label_delete_button = T("Delete Baseline"),
        msg_record_created = T("Baseline added"),
        msg_record_modified = T("Baseline updated"),
        msg_record_deleted = T("Baseline deleted"),
        msg_list_empty = T("No Baselines currently registered"))     
    
    # Baseline as component of assessments
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(assess_assess="assess_id"),
                              deletable=True,
                              editable=True)      
    

    #==============================================================================
    # Summary
    resourcename = "summary"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            assess_id(),
                            cluster_subsector_id(),
                            #Field("value", "double"),
                            Field("value", "integer",
                                  default = 0),
                            comments(),
                            migrate=migrate, *s3_meta_fields()
                            )        
    
    #Hide fk fields in forms
    table.assess_id.readable = table.assess_id.writable = False    
    
    assess_severity_opts = {  0: T("Low"),
                              1: T("Medium"),
                              2: T("High"),
                              3: T("Very High"),
                           }

    table.value.label = T("Severity")                            
    table.value.requires = IS_EMPTY_OR(IS_IN_SET(assess_severity_opts))
    table.value.widget=SQLFORM.widgets.radio.widget
    
    def shn_assess_summary_value_represent(value):        
        if value:
            value_colour_dict = {0:"green",
                                 1:"yellow",
                                 2:"orange",
                                 3:"red"}
            return IMG( _src="/%s/static/img/%s_circle_16px.png" % (request.application, value_colour_dict[value]),
                        _alt= value,
                        _align="middle"
                        )
        else:
            return NONE
    
    table.value.represent = shn_assess_summary_value_represent
    
    # CRUD strings
    ADD_ASSESS_SUMMARY = T("Add Assessment Summary")
    LIST_ASSESS_SUMMARY = T("List Assessment Summaries")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ASSESS_SUMMARY,
        title_display = T("Impact Assessment Summaries"),
        title_list = LIST_ASSESS_SUMMARY,
        title_update = T("Edit Assessment Summary"),
        title_search = T("Search Assessment Summaries"),
        subtitle_create = T("Add New Assessment Summary"),
        subtitle_list = T("Assessment Summaries"),
        label_list_button = LIST_ASSESS_SUMMARY,
        label_create_button = ADD_ASSESS_SUMMARY,
        label_delete_button = T("Delete Assessment Summary"),
        msg_record_created = T("Assessment Summary added"),
        msg_record_modified = T("Assessment Summary updated"),
        msg_record_deleted = T("Assessment Summary deleted"),
        msg_list_empty = T("No Assessment Summaries currently registered"))     
    
    # Summary as component of assessments
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(assess_assess="assess_id"),
                              deletable=True,
                              editable=True)      
    
    
    #==============================================================================  
