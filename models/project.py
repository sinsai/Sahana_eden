# -*- coding: utf-8 -*-

"""
    Project

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-25

    Project Management
"""

module = "project"
if deployment_settings.has_module("org"):
    #==============================================================================
    # Activity Type
    #
    resource = "activity_type"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field("name", length=128, notnull=True, unique=True),
                            migrate=migrate, *s3_meta_fields())


    ADD_ACTIVITY_TYPE = T("Add Activity Type")
    
    def activity_type_comment():
        if auth.has_membership(auth.id_group("'Administrator'")):
            return DIV(A(ADD_ACTIVITY_TYPE,
                         _class="colorbox",
                         _href=URL(r=request, c="project", f="activity_type", args="create", vars=dict(format="popup")),
                         _target="top",
                         _title=ADD_ACTIVITY_TYPE
                         )
                       )
        else:
            return None    

    activity_type_id = S3ReusableField("activity_type_id", db.project_activity_type, sortby="name",
                                       requires = IS_NULL_OR(IS_ONE_OF(db, "project_activity_type.id","%(name)s", sort=True)),
                                       represent = lambda id: shn_get_db_field_value(db = db,
                                                                                     table = "project_activity_type",
                                                                                     field = "name",
                                                                                     look_up = id),
                                       label = T("Activity Type"),
                                       comment = activity_type_comment(),
                                       ondelete = "RESTRICT"
                                       )

    #==============================================================================
    # Activity
    #
    opt_bnf_type = { 1: T("Individuals"),
                     2: T("Families/HH")
                   }

    resource = "activity"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            organisation_id("donor_id",
                                            label = T("Funding Organization"),
                                            comment = DIV(A(ADD_ORGANIZATION,
                                                            _class="colorbox",
                                                            _href=organisation_popup_url,
                                                            _target="top",
                                                            _title=ADD_ORGANIZATION),
                                                          DIV(DIV(_class="tooltip",
                                                                  _title=ADD_ORGANIZATION + "|" + T("The Organization which is funding this Activity."))))
                                           ),
                            organisation_id(),
                            cluster_subsector_id(),
                            Field("description"),
                            #Field("quantity"),
                            #Field("unit"), # Change to link to supply
                            Field("start_date","date"),
                            Field("end_date","date"),
                            location_id(),
                            #shelter_id(),
                            Field("total_bnf_reach","integer"),
                            #Field("bnf_type","integer"),
                            #Field("bnf_date","date"),
                            #Field("total_bnf_target","integer"),
                            #Field("male","integer"),
                            #Field("female","integer"),
                            #Field("child_2","integer"),
                            #Field("child_5","integer"),
                            #Field("child_15","integer"),
                            #Field("cba_women","integer"),
                            #Field("pl_women","integer"),
                            person_id(),
                            comments(),
                            migrate=migrate, *s3_meta_fields())


    table.total_bnf_reach.label = T("Total # of Beneficiaries Reached ")
    #table.bnf_type.label = T("Beneficiary Type")
    #table.bnf_date.label = T("Date of Latest Information on Beneficiaries Reached")
    #table.total_bnf_target.label = T("Total # of Target Beneficiaries")
    #table.child_2.label = T("Children (< 2 years)")
    #table.child_5.label = T("Children (2-5 years)")
    #table.child_15.label = T("Children (5-15 years)")
    #table.cba_women.label = T("CBA Women")
    #table.cba_women.comment = DIV( _class="tooltip", _title= T("Women of Child Bearing Age"))
    #table.pl_women.label = T("PL Women")
    #table.pl_women.comment = DIV( _class="tooltip", _title= T("Women who are Pregnant or in Labour"))

    table.person_id.label = T("Contact Person")

    #table.comments.comment = T("(Constraints Only)")

    for field in table:
        if field.type == "integer":
            field.requires = IS_NULL_OR( IS_INT_IN_RANGE(0,99999999) )

    #table.bnf_type.requires = IS_NULL_OR(IS_IN_SET(opt_bnf_type))
    #table.bnf_type.represent = lambda opt: opt_bnf_type.get(opt, NONE)

    # CRUD Strings
    ADD_ACTIVITY = T("Add Activity")
    LIST_ACTIVITIES = T("List Activities")
    s3.crud_strings[tablename] = Storage(title_create = ADD_ACTIVITY,
                                         title_display = T("Activity Details"),
                                         title_list = LIST_ACTIVITIES,
                                         title_update = T("Edit Activity"),
                                         title_search = T("Search Activities"),
                                         subtitle_create = T("Add New Activity"),
                                         subtitle_list = T("Activities"),
                                         label_list_button = LIST_ACTIVITIES,
                                         label_create_button = ADD_ACTIVITY,
                                         msg_record_created = T("Activity Added"),
                                         msg_record_modified = T("Activity Updated"),
                                         msg_record_deleted = T("Activity Deleted"),
                                         msg_list_empty = T("No Activities Found")
                                         )
    # Activities as component of Orgs
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(org_organisation="organisation_id"))

