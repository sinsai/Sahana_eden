# -*- coding: utf-8 -*-

""" Human Resource Management

    @author: Dominic König <dominic AT aidiq DOT com>

"""

prefix = "hrm"
if deployment_settings.has_module(prefix):

    # =========================================================================
    # Human Resource
    #
    hrm_type_opts = {
        1: T("staff"),
        2: T("volunteer")
    }

    hrm_status_opts = {
        1: T("active"),
        2: T("obsolete")
    }

    resourcename = "human_resource"
    tablename = "hrm_human_resource"
    table = db.define_table(tablename,
                            #super_link(db.sit_resource), # is a resource

                            organisation_id(),
                            person_id(),

                            Field("type", "integer",
                                  requires = IS_IN_SET(hrm_type_opts, zero=None),
                                  default = 1,
                                  label = T("Type"),
                                  represent = lambda opt: hrm_type_opts.get(opt, UNKNOWN_OPT)),

                            Field("status", "integer",
                                  requires = IS_IN_SET(hrm_status_opts, zero=None),
                                  default = 1,
                                  label = T("Status"),
                                  represent = lambda opt: hrm_status_opts.get(opt, UNKNOWN_OPT)),

                            migrate=migrate, *s3_meta_fields())

    human_resource_id = S3ReusableField("human_resource_id", db.hrm_human_resource,
                                        sortby = ["type", "status"],
                                        requires = IS_ONE_OF(db, "hrm_human_resource.id",
                                                             #hrm_skill_represent,
                                                             orderby="hrm_skill.name"),
                                        #represent = hrm_skill_represent,
                                        label = T("Human Resource"),
                                        ondelete = "RESTRICT")


    # =========================================================================
    # Skills
    #
    hrm_skill_category_opts = {
        1:T("Certification"),
        2:T("Experience")
    }

    resourcename = "skill"
    tablename = "hrm_skill"
    table = db.define_table(tablename,
                            Field("name",
                                  length=128,
                                  notnull=True,
                                  label=T("Name")),
                            Field("category", "integer",
                                  requires=IS_IN_SET(hrm_skill_category_opts, zero=None),
                                  notnull=True,
                                  label=T("Category"),
                                  represent = lambda opt: hrm_skill_category_opts(opt, UNKNOWN_OPT)),
                            #Field("description"),
                            migrate=migrate, *s3_meta_fields())

    skill_id = S3ReusableField("skill_id", db.hrm_skill,
                               sortby = ["category", "name"],
                               requires = IS_ONE_OF(db, "hrm_skill.id",
                                                    #hrm_skill_represent,
                                                    orderby="hrm_skill.name"),
                               #represent = hrm_skill_represent,
                               label = T("Skill"),
                               ondelete = "RESTRICT")

    # =========================================================================
    # Credentials
    #
    hrm_credential_status_opts = {
        1:T("Pending"),
        2:T("Approved"),
        3:T("Rejected")
    }

    resourcename = "credential"
    tablename = "hrm_credential"
    table = db.define_table(tablename,
                            person_id(),
                            skill_id(),
                            Field("status",
                                  requires=IS_IN_SET(hrm_credential_status_opts, zero=None),
                                  notnull=True,
                                  default=1, # pending
                                  label=T("Status"),
                                  represent = lambda opt: hrm_credential_status_opts.get(opt, UNKNOWN_OPT)),
                            migrate=migrate, *s3_meta_fields())

    # =========================================================================
    # Availability
    #
    resourcename = "availability"
    tablename = "hrm_availability"
    table = db.define_table(tablename,
                            human_resource_id(),
                            Field("date_start", "date"),
                            Field("date_end", "date"),
                            Field("day_of_week", "integer"),
                            Field("hours_start", "time"),
                            Field("hours_end", "time"),
                            #location_id(label=T("Available for Location"),
                                        #requires=IS_ONE_OF(db, "gis_location.id",
                                                           #shn_gis_location_represent_row,
                                                           #filterby="level",
                                                           ##This is likely to be customised for the deployment
                                                           #filter_opts=["GR", "L0", "L1", "L2", "L3"],
                                                           #orderby="gis_location.name"),
                                        #widget=None),
                            migrate=migrate, *s3_meta_fields())

    # Availability as component of human resources
    s3xrc.model.add_component(prefix, resourcename,
                              joinby=dict(
                                hrm_human_resource="human_resource_id"),
                              multiple=True)

    # =========================================================================
    # CRUD Strings
    #

    #s3.crud_strings[tablename] = Storage(
        #title_create = T("Add Credential"),
        #title_display = T("Credential Details"),
        #title_list = T("Credentials"),
        #title_update = T("Edit Credential"),
        #title_search = T("Search Credentials"),
        #subtitle_create = T("Add New Credential"),
        #subtitle_list = T("Credentials"),
        #label_list_button = T("List Credentials"),
        #label_create_button = T("Add Credentials"),
        #label_delete_button = T("Delete Credential"),
        #msg_record_created = T("Credential added"),
        #msg_record_modified = T("Credential updated"),
        #msg_record_deleted = T("Credential deleted"),
        #msg_list_empty = T("No Credentials currently set"))

    # =========================================================================
    # Common Functions
    #

# END =========================================================================
