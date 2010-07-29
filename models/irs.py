# -*- coding: utf-8 -*-

""" IRS - Incident Report System

    @author: nursix

"""

module = "irs"
if deployment_settings.has_module(module):

    # Settings
    resource = "setting"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field("audit_read", "boolean"),
                            Field("audit_write", "boolean"),
                            migrate=migrate)

    # -----------------------------------------------------------------------------
    irs_incident_type_opts = {
        1: T("Natural Disaster"),
        2: T("Accident"),
        3: T("Hazard"),
        99: T("other")
    }
    resource = "incident"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            Field("datetime", "datetime"),
                            location_id,
                            Field("type", "integer",
                                  requires = IS_IN_SET(irs_incident_type_opts, zero=None),
                                  represent = lambda opt: \
                                              irs_incident_type_opts.get(opt, UNKNOWN_OPT),
                                  default = 99),
                            Field("note", length=64),
                            Field("details", "text"),
                            Field("persons_affected", "integer"),
                            Field("persons_injured", "integer"),
                            Field("persons_deceased", "integer"),
                            migrate=migrate)

    incident_id = db.Table(None, "incident_id",
                           Field("incident_id", table,
                                 requires = IS_NULL_OR(IS_ONE_OF(db, "irs_incident.id", "%(id)s")),
                                 represent = lambda id: id,
                                 readable = False,
                                 writable = False,
                                 ondelete = "RESTRICT"))

    s3xrc.model.configure(table,
        list_fields = [
            "id",
            "datetime",
            "location_id",
            "type",
            "note"
        ])

    # -----------------------------------------------------------------------------
    irs_image_type_opts = {
        1:T("Photograph"),
        2:T("Map"),
        3:T("Document Scan"),
        99:T("other")
    }

    resource = "iimage"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            incident_id,
                            Field("type", "integer",
                                requires = IS_IN_SET(irs_image_type_opts, zero=None),
                                default = 1,
                                label = T("Image Type"),
                                represent = lambda opt: irs_image_type_opts.get(opt, UNKNOWN_OPT)),
                            Field("image", "upload", autodelete=True),
                            Field("url"),
                            Field("description"),
                            Field("tags"),
                            migrate=migrate)

    s3xrc.model.add_component(module, resource,
                              multiple = True,
                              joinby = dict(irs_incident="incident_id"),
                              deletable = True,
                              editable = True)

    s3xrc.model.configure(table,
        list_fields = [
            "id",
            "type",
            "description"
        ])

    # -----------------------------------------------------------------------------
    irs_assessment_type_opts = {
        1:T("initial assessment"),
        2:T("follow-up assessment"),
        3:T("final report"),
        99:T("other")
    }

    irs_event_type_opts = {
        1:T("primary incident"),
        2:T("secondary effect"),
        3:T("collateral event"),
        99:T("other")
    }

    irs_cause_type_opts = {
        1:T("natural hazard"),
        2:T("technical failure"),
        3:T("human error"),
        4:T("criminal intent"),
        5:T("operational intent"),
        99:T("other")
    }

    resource = "iassessment"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            incident_id,
                            Field("datetime", "datetime"),
                            Field("type", "integer",
                                requires = IS_IN_SET(irs_assessment_type_opts, zero=None),
                                default = 1,
                                label = T("Report Type"),
                                represent = lambda opt: irs_assessment_type_opts.get(opt, UNKNOWN_OPT)),
                            Field("event_type", "integer",
                                requires = IS_IN_SET(irs_event_type_opts, zero=None),
                                default = 1,
                                label = T("Event type"),
                                represent = lambda opt: irs_event_type_opts.get(opt, UNKNOWN_OPT)),
                            Field("cause_type", "integer",
                                requires = IS_IN_SET(irs_cause_type_opts, zero=None),
                                default = 1,
                                label = T("Type of cause"),
                                represent = lambda opt: irs_cause_type_opts.get(opt, UNKNOWN_OPT)),
                            Field("report", "text"),
                            Field("persons_affected", "integer"),
                            Field("persons_injured", "integer"),
                            Field("persons_deceased", "integer"),
                            migrate=migrate)

    table.modified_by.label = T("Reporter")
    table.modified_by.readable = True

    table.datetime.label = T("Date/Time")

    s3xrc.model.configure(table,
        list_fields = [
            "id",
            "datetime",
            "type",
            "modified_by"
        ])

    s3xrc.model.add_component(module, resource,
                              multiple = True,
                              joinby = dict(irs_incident="incident_id"),
                              deletable = True,
                              editable = True)

    # -----------------------------------------------------------------------------
    irs_response_type_opts = {
        1:T("Alert"),
        2:T("Intervention"),
        3:T("Closure"),
        99:T("other")
    }

    resource = "iresponse"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            incident_id,
                            Field("datetime", "datetime"),
                            Field("type", "integer",
                                requires = IS_IN_SET(irs_response_type_opts, zero=None),
                                default = 1,
                                label = T("Type"),
                                represent = lambda opt: irs_response_type_opts.get(opt, UNKNOWN_OPT)),
                            Field("report", "text"),
                            migrate=migrate)

    s3xrc.model.add_component(module, resource,
                              multiple = True,
                              joinby = dict(irs_incident="incident_id"),
                              deletable = True,
                              editable = True)

    # -----------------------------------------------------------------------------
