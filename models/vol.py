# -*- coding: utf-8 -*-

"""
    Volunteer Management System

    @author: zubair assad
    @author: nursix
"""

module = "vol"
if deployment_settings.has_module(module):

    # Settings
    resource = "setting"
    tablename = module + "_" + resource
    table = db.define_table(tablename,
                    Field("audit_read", "boolean"),
                    Field("audit_write", "boolean"),
                    migrate=migrate)

    # -----------------------------------------------------------------------------
    # vol_volunteer (Component of pr_person)
    #   describes a person's availability as a volunteer
    #
    vol_volunteer_status_opts = {
    1: T("active"),
    2: T("retired")
    }

    resource = "volunteer"
    tablename = module + "_" + resource
    table = db.define_table(tablename, timestamp, uuidstamp,
                    person_id,
                    organisation_id,
                    Field("date_avail_start", "date"),
                    Field("date_avail_end", "date"),
                    Field("hrs_avail_start", "time"),
                    Field("hrs_avail_end", "time"),
                    Field("status", "integer",
                        requires = IS_IN_SET(vol_volunteer_status_opts, zero=None),
                        # default = 1,
                        label = T("Status"),
                        represent = lambda opt: vol_volunteer_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("special_needs", "text"),
                    migrate=migrate)

    # Settings and Restrictions

    # Field labels
    table.date_avail_start.label = T("Available from")
    table.date_avail_end.label = T("Available until")
    table.hrs_avail_start.label = T("Working hours start")
    table.hrs_avail_end.label = T("Working hours end")
    table.special_needs.label = T("Special needs")

    # Representation function
    def shn_vol_volunteer_represent(id):
        person = db((db.vol_volunteer.id == id) & (db.pr_person.id == db.vol_volunteer.person_id)).select(
                    db.pr_person.first_name,
                    db.pr_person.middle_name,
                    db.pr_person.last_name,
                    limitby=(0, 1))
        if person:
            return vita.fullname(person.first())
        else:
            return None

    # CRUD Strings
    ADD_VOLUNTEER = Tstr("Add Volunteer Registration")
    VOLUNTEERS = T("Volunteer Registrations")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_VOLUNTEER,
        title_display = T("Volunteer Registration"),
        title_list = VOLUNTEERS,
        title_update = T("Edit Volunteer Registration"),
        title_search = T("Search Volunteer Registrations"),
        subtitle_create = ADD_VOLUNTEER,
        subtitle_list = VOLUNTEERS,
        label_list_button = T("List Registrations"),
        label_create_button = T("Add Volunteer Registration"),
        msg_record_created = T("Volunteer registration added"),
        msg_record_modified = T("Volunteer registration updated"),
        msg_record_deleted = T("Volunteer registration deleted"),
        msg_list_empty = T("No volunteer information registered"))

    # Reusable field
    vol_volunteer_id = db.Table(None, "vol_volunteer_id",
                                FieldS3("vol_volunteer_id", db.vol_volunteer, sortby=["first_name", "middle_name", "last_name"],
                                requires = IS_NULL_OR(IS_ONE_OF(db(db.vol_volunteer.status == 1), "vol_volunteer.id", shn_vol_volunteer_represent)),
                                represent = lambda id: (id and [shn_vol_volunteer_represent(id)] or ["None"])[0],
                                comment = DIV(A(ADD_VOLUNTEER, _class="colorbox", _href=URL(r=request, c="vol", f="volunteer", args="create", vars=dict(format="popup")), _target="top", _title=ADD_VOLUNTEER),
                                          DIV( _class="tooltip", _title=ADD_VOLUNTEER + "|" + Tstr("Add new volunteer."))),
                                ondelete = "RESTRICT"
                            ))

    s3xrc.model.add_component(module, resource,
                              multiple=False,
                              joinby=dict(pr_person="person_id"),
                              deletable=True,
                              editable=True,
                              main="person_id", extra="organisation_id")

    s3xrc.model.configure(table,
                          list_fields=["organisation_id",
                                       "status"])

    # -----------------------------------------------------------------------------
    # vol_resource (Component of pr_person)
    #   describes resources (skills, tools) of a volunteer
    #
    vol_resource_type_opts = {
        1:T("General Skills"),
        2:T("Resources"),
        3:T("Restrictions"),
        4:T("Site Manager"),
        5:T("Unskilled"),
        99:T("Other")
    }

    vol_resource_subject_opts = {
        1:T("Animals"),
        2:T("Automotive"),
        3:T("Baby And Child Care"),
        4:T("Tree"),
        5:T("Warehouse"),
        99:T("Other")
    }

    vol_resource_deployment_opts = {
        1:T("Building Aide"),
        2:T("Vehicle"),
        3:T("Warehouse"),
        99:T("Other")
    }

    vol_resource_status_opts = {
        1:T("approved"),
        2:T("unapproved"),
        3:T("denied")
    }

    resource = "resource"
    tablename = module + "_" + resource
    table = db.define_table(tablename, timestamp, uuidstamp,
                    person_id,
                    Field("type", "integer",
                        requires = IS_IN_SET(vol_resource_type_opts, zero=None),
                        # default = 99,
                        label = T("Resource"),
                        represent = lambda opt: vol_resource_type_opts.get(opt, UNKNOWN_OPT)),
                    Field("subject", "integer",
                        requires = IS_IN_SET(vol_resource_subject_opts, zero=None),
                        # default = 99,
                        label = T("Subject"),
                        represent = lambda opt: vol_resource_subject_opts.get(opt, UNKNOWN_OPT)),
                    Field("deployment", "integer",
                        requires = IS_IN_SET(vol_resource_deployment_opts, zero=None),
                        # default = 99,
                        label = T("Deployment"),
                        represent = lambda opt: vol_resource_deployment_opts.get(opt, UNKNOWN_OPT)),
                    Field("status", "integer",
                        requires = IS_IN_SET(vol_resource_status_opts, zero=None),
                        # default = 2,
                        label = T("Status"),
                        represent = lambda opt: vol_resource_status_opts.get(opt, UNKNOWN_OPT)),
                    migrate=migrate)

    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(pr_person="person_id"),
                              deletable=True,
                              editable=True,
                              main="person_id", extra="subject")

    s3xrc.model.configure(table,
                          list_fields=["id",
                                       "type",
                                       "subject",
                                       "deployment",
                                       "status"])

    # CRUD Strings
    ADD_RESOURCE = T("Add Resource")
    RESOURCES = T("Resources")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_RESOURCE,
        title_display = T("Resource Details"),
        title_list = RESOURCES,
        title_update = T("Edit Resource"),
        title_search = T("Search Resources"),
        subtitle_create = T("Add New Resource"),
        subtitle_list = RESOURCES,
        label_list_button = T("List Resources"),
        label_create_button = ADD_RESOURCE,
        msg_record_created = T("Resource added"),
        msg_record_modified = T("Resource updated"),
        msg_record_deleted = T("Resource deleted"),
        msg_list_empty = T("No resources currently registered"))

    # -----------------------------------------------------------------------------
    # vol_hours:
    #   documents the hours a volunteer has a position
    #
    #resource = "hours"
    #table = module + "_" + resource
    #db.define_table(table,
    #                person_id,
    #                vol_position_id,
    #                Field("shift_start", "datetime", label=T("shift_start"), notnull=True),
    #                Field("shift_end", "datetime", label=T("shift_end"), notnull=True),
    #                migrate=migrate)

    #db[table].shift_start.requires=[IS_NOT_EMPTY(),
    #                                      IS_DATETIME]
    #db[table].shift_end.requires=[IS_NOT_EMPTY(),
    #                                      IS_DATETIME]

    # -----------------------------------------------------------------------------
    # vol_mailbox
    #
    #resource = "mailbox"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp, deletion_status,
    #                person_id,
    #                Field("message_id", "integer", notnull=True,label=T("message_id"), default=0),
    #    Field("box", "integer", notnull=True, label=T("box"), default=0),
    #    Field("checked", "integer", label=T("checked"), default=0),
    #    migrate=migrate)


    # -----------------------------------------------------------------------------
    # vol_message
    #   a text message
    #
    #resource = "message"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp, deletion_status,
    #                Field("message", "text", label=T("message")),
    #                Field("time", "datetime", label=T("time"), notnull=True, default=request.now),
    #                migrate=migrate)

    # -----------------------------------------------------------------------------
    # courier
    #resource = "courier"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp,
    #db.define_table("vol_courier", timestamp, uuidstamp,
    #    Field("message_id", "integer", label=T("message_id"), notnull=True),
    #    Field("to_id", "string", label=T("to_id"), notnull=True),
    #    Field("from_id", "string", label=T("from_id"), notnull=True),
    #    migrate=migrate)

    #db[table].message_id.requires = IS_NOT_EMPTY()
    #db[table].to_id.requires = IS_NOT_EMPTY()
    #db[table].from_id.requires = IS_NOT_EMPTY()
    #db[table].message_id.requires = IS_NOT_NULL()

    # -----------------------------------------------------------------------------
    # vol_access_request
    #resource = "access_request"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp,
    #    Field("request_id", "integer", notnull=True),
    #    Field("act", "string", length=100, label=T("act")),
    #    Field("vm_action", "string", length=100, label=T("vm_action")),
    #    Field("description", "string", length=300, label=T("description")),
    #    migrate=migrate)

    # -----------------------------------------------------------------------------
    # vol_access_constraint
    #resource = "access_constraint"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp,
    #    Field("constraint_id","string", length=30, notnull=True, default=" ", label=T("constraint_id")),
    #    Field("description","string", length=200,label=T("description")),
    #    migrate=migrate)

    # -----------------------------------------------------------------------------
    # vol_access_constraint_to_request
    #resource = "access_constraint_to_request"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp,
    #    Field("request_id", db.vol_access_request),
    #    Field("constraint_id", db.vol_access_constraint),
    #    migrate=migrate)

    # -----------------------------------------------------------------------------
    # vol_access_classification_to_request
    #resource = "access_classification_to_request"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp,
    #    Field("request_id", "integer", length=11, notnull=True, default=0),
    #    Field("table_name", "string", length=200, notnull=True, default=" ", label=T("table_name")),
    #    Field("crud", "string", length=4, notnull=True, default=" ", label=T("crud")),
    #    migrate=migrate)

