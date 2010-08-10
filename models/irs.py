# -*- coding: utf-8 -*-

"""
    Incident Reporting System - Model
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

    irs_incident_type_opts = {
        1:T("animalHealth.animalDieOff"),
        2:T("animalHealth.animalFeed"),
        3:T("aviation.aircraftCrash"),
        4:T("aviation.aircraftHijacking"),
        5:T("aviation.airportClosure"),
        6:T("aviation.airspaceClosure"),
        7:T("aviation.noticeToAirmen"),
        8:T("aviation.spaceDebris"),
        9:T("civil.demonstrations"),
        10:T("civil.dignitaryVisit"),
        11:T("civil.displacedPopulations"),
        12:T("civil.emergency"),
        13:T("civil.looting"),
        14:T("civil.publicEvent"),
        15:T("civil.riot"),
        16:T("civil.volunteerRequest"),
        17:T("crime.bomb"),
        18:T("crime.bombExplosion"),
        19:T("crime.bombThreat"),
        20:T("crime.dangerousPerson"),
        21:T("crime.drugs"),
        22:T("crime.homeCrime"),
        23:T("crime.illegalImmigrant"),
        24:T("crime.industrialCrime"),
        25:T("crime.poisoning"),
        26:T("crime.retailCrime"),
        27:T("crime.shooting"),
        28:T("crime.stowaway"),
        29:T("crime.terrorism"),
        30:T("crime.vehicleCrime"),
        31:T("fire.forestFire"),
        32:T("fire.hotSpot"),
        33:T("fire.industryFire"),
        34:T("fire.smoke"),
        35:T("fire.urbanFire"),
        36:T("fire.wildFire"),
        37:T("flood.damOverflow"),
        38:T("flood.flashFlood"),
        39:T("flood.highWater"),
        40:T("flood.overlandFlowFlood"),
        41:T("flood.tsunami"),
        42:T("geophysical.avalanche"),
        43:T("geophysical.earthquake"),
        44:T("geophysical.lahar"),
        45:T("geophysical.landslide"),
        46:T("geophysical.magneticStorm"),
        47:T("geophysical.meteorite"),
        48:T("geophysical.pyroclasticFlow"),
        49:T("geophysical.pyroclasticSurge"),
        50:T("geophysical.volcanicAshCloud"),
        51:T("geophysical.volcanicEvent"),
        52:T("hazardousMaterial.biologicalHazard"),
        53:T("hazardousMaterial.chemicalHazard"),
        54:T("hazardousMaterial.explosiveHazard"),
        55:T("hazardousMaterial.fallingObjectHazard"),
        56:T("hazardousMaterial.infectiousDisease"),
        57:T("hazardousMaterial.poisonousGas"),
        58:T("hazardousMaterial.radiologicalHazard"),
        59:T("health.infectiousDisease"),
        60:T("health.infestation"),
        61:T("ice.iceberg"),
        62:T("ice.icePressure"),
        63:T("ice.rapidCloseLead"),
        64:T("ice.specialIce"),
        65:T("marine.marineSecurity"),
        66:T("marine.nauticalAccident"),
        67:T("marine.nauticalHijacking"),
        68:T("marine.portClosure"),
        69:T("marine.specialMarine"),
        70:T("meteorological.blizzard"),
        71:T("meteorological.blowingSnow"),
        72:T("meteorological.drought"),
        73:T("meteorological.dustStorm"),
        74:T("meteorological.fog"),
        75:T("meteorological.freezingDrizzle"),
        76:T("meteorological.freezingRain"),
        77:T("meteorological.freezingSpray"),
        78:T("meteorological.hail"),
        79:T("meteorological.hurricane"),
        80:T("meteorological.rainFall"),
        81:T("meteorological.snowFall"),
        82:T("meteorological.snowSquall"),
        83:T("meteorological.squall"),
        84:T("meteorological.stormSurge"),
        85:T("meteorological.thunderstorm"),
        86:T("meteorological.tornado"),
        87:T("meteorological.tropicalStorm"),
        88:T("meteorological.waterspout"),
        89:T("meteorological.winterStorm"),
        90:T("missingPerson.amberAlert"),
        91:T("missingPerson.missingVulnerablePerson"),
        92:T("missingPerson.silver"),
        93:T("publicService.emergencySupportFacility"),
        94:T("publicService.emergencySupportService"),
        95:T("publicService.schoolClosure"),
        96:T("publicService.schoolLockdown"),
        97:T("publicService.serviceOrFacility"),
        98:T("publicService.transit"),
        99:T("railway.railwayAccident"),
        100:T("railway.railwayHijacking"),
        101:T("roadway.bridgeClosure"),
        102:T("roadway.hazardousRoadConditions"),
        103:T("roadway.roadwayAccident"),
        104:T("roadway.roadwayClosure"),
        105:T("roadway.roadwayDelay"),
        106:T("roadway.roadwayHijacking"),
        107:T("roadway.roadwayUsageCondition"),
        108:T("roadway.trafficReport"),
        109:T("temperature.arcticOutflow"),
        110:T("temperature.coldWave"),
        111:T("temperature.flashFreeze"),
        112:T("temperature.frost"),
        113:T("temperature.heatAndHumidity"),
        114:T("temperature.heatWave"),
        115:T("temperature.windChill"),
        116:T("wind.galeWind"),
        117:T("wind.hurricaneForceWind"),
        118:T("wind.stormForceWind"),
        119:T("wind.strongWind")
    }

    # Incidents
    # This is the current status of an Incident
    resource = "incident"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
            Field("name"),
            Field("category", "integer"),
            Field("contact"),
            location_id,
            Field("time", "datetime"),
            Field("persons_affected", "integer"),
            Field("persons_injured", "integer"),
            Field("persons_deceased", "integer"),
            comments,
            )
    table.name.requires = IS_NOT_EMPTY()
    table.category.requires = IS_NULL_OR(IS_IN_SET(irs_incident_type_opts))
    table.category.represent = lambda opt: irs_incident_type_opts.get(opt, opt)

    # CRUD strings
    ADD_INCIDENT = T("Add Incident")
    LIST_INCIDENTS = T("List Incidents")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_INCIDENT,
        title_display = T("Incident Details"),
        title_list = LIST_INCIDENTS,
        title_update = T("Edit Incident"),
        title_search = T("Search Incidents"),
        subtitle_create = T("Add New Incident"),
        subtitle_list = T("Incidents"),
        label_list_button = LIST_INCIDENTS,
        label_create_button = ADD_INCIDENT,
        msg_record_created = T("Incident added"),
        msg_record_modified = T("Incident updated"),
        msg_record_deleted = T("Incident deleted"),
        msg_list_empty = T("No Incidents currently registered"))

    incident_id = db.Table(None, "incident_id",
                           Field("incident_id", table,
                                 requires = IS_NULL_OR(IS_ONE_OF(db, "irs_incident.id", "%(id)s")),
                                 represent = lambda id: id,
                                 label = T("Incident"),
                                 ondelete = "RESTRICT"))
    s3xrc.model.configure(table,
                        list_fields = [
                            "id",
                            "category",
                            "time",
                            "location_id"
                        ])
    # -----------------------------------------------------------------------------
    # Reports
    # This is a report of an Incident
    # A single incident may generate many reports
    resource = "ireport"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
            incident_id,
            Field("name"),
            Field("category", "integer"),
            person_id,
            Field("contact"),
            location_id,
            Field("time", "datetime"),
            Field("persons_affected", "integer"),
            Field("persons_injured", "integer"),
            Field("persons_deceased", "integer"),
            comments,
            )
    table.name.requires = IS_NOT_EMPTY()
    table.category.requires = IS_NULL_OR(IS_IN_SET(irs_incident_type_opts))
    table.category.represent = lambda opt: irs_incident_type_opts.get(opt, opt)
    table.person_id.default = session.auth.user.id if auth.is_logged_in() else None

    table.name.label = T("Short Description")
    table.name.comment = SPAN("*", _class="req")
    table.person_id.label = T("Reporter Name")
    table.persons_affected.label = T("Number of People Affected")
    table.persons_injured.label = T("Number of People Injured")
    table.persons_deceased.label = T("Number of People Deceased")

    # CRUD strings
    ADD_REPORT = T("Add Report")
    LIST_REPORTS = T("List Reports")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_REPORT,
        title_display = T("Report Details"),
        title_list = LIST_REPORTS,
        title_update = T("Edit Report"),
        title_search = T("Search Reports"),
        subtitle_create = T("Add New Report"),
        subtitle_list = T("Reports"),
        label_list_button = LIST_REPORTS,
        label_create_button = ADD_REPORT,
        msg_record_created = T("Report added"),
        msg_record_modified = T("Report updated"),
        msg_record_deleted = T("Report deleted"),
        msg_list_empty = T("No Reports currently registered"))

    s3xrc.model.add_component(module, resource,
                              multiple = True,
                              joinby = dict(irs_incident="incident_id"),
                              deletable = True,
                              editable = True)

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

    # Assessments
    # This is a follow-up assessment of an Incident
    resource = "iassessment"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            incident_id,
                            Field("datetime", "datetime"),
                            Field("itype", "integer",
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
        msg_record_created = T("Assessment added"),
        msg_record_modified = T("Assessment updated"),
        msg_record_deleted = T("Assessment deleted"),
        msg_list_empty = T("No Assessments currently registered"))

    s3xrc.model.configure(table,
        list_fields = [
            "id",
            "datetime",
            "itype",
            "modified_by"
        ])

    s3xrc.model.add_component(module, resource,
                              multiple = True,
                              joinby = dict(irs_incident="incident_id"),
                              deletable = True,
                              editable = True)

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
                            Field("report_id", db.irs_ireport),
                            incident_id,
                            Field("assessment_id", db.irs_iassessment),
                            Field("type", "integer",
                                requires = IS_IN_SET(irs_image_type_opts, zero=None),
                                default = 1,
                                label = T("Image Type"),
                                represent = lambda opt: irs_image_type_opts.get(opt, UNKNOWN_OPT)),
                            Field("image", "upload", autodelete=True),
                            #Field("url"),
                            Field("description"),
                            #Field("tags"),
                            migrate=migrate)

    # CRUD strings
    ADD_IMAGE = T("Add Image")
    LIST_IMAGES = T("List Images")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_IMAGE,
        title_display = T("Image Details"),
        title_list = LIST_IMAGES,
        title_update = T("Edit Image"),
        title_search = T("Search Images"),
        subtitle_create = T("Add New Image"),
        subtitle_list = T("Images"),
        label_list_button = LIST_IMAGES,
        label_create_button = ADD_IMAGE,
        msg_record_created = T("Image added"),
        msg_record_modified = T("Image updated"),
        msg_record_deleted = T("Image deleted"),
        msg_list_empty = T("No Images currently registered"))

    s3xrc.model.add_component(module, resource,
                              multiple = True,
                              joinby = dict(irs_incident="incident_id",
                                            irs_ireport="report_id",
                                            irs_iassessment="assessment_id"),
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
                            Field("itype", "integer",
                                requires = IS_IN_SET(irs_response_type_opts, zero=None),
                                default = 1,
                                label = T("Type"),
                                represent = lambda opt: irs_response_type_opts.get(opt, UNKNOWN_OPT)),
                            Field("report", "text"),
                            migrate=migrate)

    # CRUD strings
    ADD_RESPONSE = T("Add Response")
    LIST_RESPONSES = T("List Responses")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_RESPONSE,
        title_display = T("Response Details"),
        title_list = LIST_RESPONSES,
        title_update = T("Edit Response"),
        title_search = T("Search Responses"),
        subtitle_create = T("Add New Response"),
        subtitle_list = T("Responses"),
        label_list_button = LIST_RESPONSES,
        label_create_button = ADD_RESPONSE,
        msg_record_created = T("Response added"),
        msg_record_modified = T("Response updated"),
        msg_record_deleted = T("Response deleted"),
        msg_list_empty = T("No Responses currently registered"))

    s3xrc.model.add_component(module, resource,
                              multiple = True,
                              joinby = dict(irs_incident="incident_id"),
                              deletable = True,
                              editable = True)

    # -----------------------------------------------------------------------------
