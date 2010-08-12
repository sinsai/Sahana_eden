# -*- coding: utf-8 -*-

""" Situation Reporting Module - Model

    @author: Fran Boon
    @see: http://eden.sahanafoundation.org/wiki/Pakistan
"""

module = "sitrep"
if deployment_settings.has_module(module):

    # Settings
    resource = "setting"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field("audit_read", "boolean"),
                            Field("audit_write", "boolean"),
                            migrate=migrate)

    # Rivers
    resource = "river"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            Field("name"),
                            comments,
                            migrate=migrate)

    table.name.requires = IS_NOT_EMPTY()

    # CRUD strings
    ADD_RIVER = T("Add River")
    LIST_RIVERS = T("List Rivers")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_RIVER,
        title_display = T("River Details"),
        title_list = LIST_RIVERS,
        title_update = T("Edit River"),
        title_search = T("Search Rivers"),
        subtitle_create = T("Add New River"),
        subtitle_list = T("Rivers"),
        label_list_button = LIST_RIVERS,
        label_create_button = ADD_RIVER,
        msg_record_created = T("River added"),
        msg_record_modified = T("River updated"),
        msg_record_deleted = T("River deleted"),
        msg_list_empty = T("No Rivers currently registered"))

    river_id = db.Table(None, "river_id",
                        Field("river_id", table,
                              requires = IS_NULL_OR(IS_ONE_OF(db, "sitrep_river.id", "%(name)s")),
                              represent = lambda id: (id and [db(db.sitrep_river.id == id).select(db.sitrep_river.name, limitby=(0, 1)).first().name] or ["None"])[0],
                              label = T("River"),
                              comment = A(ADD_RIVER, _class="colorbox", _href=URL(r=request, c="sitrep", f="river", args="create", vars=dict(format="popup")), _target="top", _title=ADD_RIVER),
                              ondelete = "RESTRICT"))

    # -----------------------------------------------------------------------------
    # Flood Reports
    resource = "freport"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            Field("time", "datetime"),
                            document,
                            comments,
                            migrate=migrate)

    # CRUD strings
    ADD_FLOOD_REPORT = T("Add Flood Report")
    LIST_FLOOD_REPORTS = T("List Flood Reports")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_FLOOD_REPORT,
        title_display = T("Flood Report Details"),
        title_list = LIST_FLOOD_REPORTS,
        title_update = T("Edit Flood Report"),
        title_search = T("Search Flood Reports"),
        subtitle_create = T("Add New Flood Report"),
        subtitle_list = T("Flood Reports"),
        label_list_button = LIST_FLOOD_REPORTS,
        label_create_button = ADD_FLOOD_REPORT,
        msg_record_created = T("Flood Report added"),
        msg_record_modified = T("Flood Report updated"),
        msg_record_deleted = T("Flood Report deleted"),
        msg_list_empty = T("No Flood Reports currently registered"))

    freport_id = db.Table(None, "freport_id",
                          Field("freport_id", table,
                                requires = IS_NULL_OR(IS_ONE_OF(db, "sitrep_freport.id", "%(time)s")),
                                represent = lambda id: (id and [db(db.sitrep_freport.id == id).select(db.sitrep_freport.time, limitby=(0, 1)).first().time] or ["None"])[0],
                                label = T("Flood Report"),
                                ondelete = "RESTRICT"))

    # -----------------------------------------------------------------------------
    # Locations
    resource = "freport_location"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            freport_id,
                            river_id,
                            location_id,
                            Field("discharge", "integer"),
                            comments,
                            migrate=migrate)

    table.discharge.label = T("Discharge (cusecs)")

    # CRUD strings
    ADD_LOCATION = T("Add Location")
    LIST_LOCATIONS = T("List Locations")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_LOCATION,
        title_display = T("Location Details"),
        title_list = LIST_LOCATIONS,
        title_update = T("Edit Location"),
        title_search = T("Search Locations"),
        subtitle_create = T("Add New Location"),
        subtitle_list = T("Locations"),
        label_list_button = LIST_LOCATIONS,
        label_create_button = ADD_LOCATION,
        msg_record_created = T("Location added"),
        msg_record_modified = T("Location updated"),
        msg_record_deleted = T("Location deleted"),
        msg_list_empty = T("No Locations currently registered"))

    s3xrc.model.add_component(module, resource,
                              multiple = True,
                              joinby = dict(sitrep_freport="freport_id"),
                              deletable = True,
                              editable = True)

    # -----------------------------------------------------------------------------
    # Assessments - WFP
    resource = "assessment"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            location_id,
                            organisation_id,
                            Field("date", "date"),
                            Field("households", "integer"),
                            Field("houses_destroyed", "integer"),
                            Field("houses_damaged", "integer"),
                            Field("crop_losses", "integer"),
                            Field("water_level", "boolean"),
                            Field("crops_affectees", "double"),
                            comments,
                            migrate=migrate)

    table.crop_losses.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 100))

    table.households.label = T("Total Households")

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

    # -----------------------------------------------------------------------------
    # School Districts
    resource = "school_district"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            Field("name"),
                            location_id,
                            Field("reported_by"),
                            Field("date", "date"),
                            document,
                            comments,
                            migrate=migrate)

    table.name.label = T("Title")
    table.location_id.label = T("District")
    table.reported_by.label = T("Reported By")

    # CRUD strings
    ADD_SCHOOL_DISTRICT = T("Add School District")
    LIST_SCHOOL_DISTRICTS = T("List School Districts")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SCHOOL_DISTRICT,
        title_display = T("School District Details"),
        title_list = LIST_SCHOOL_DISTRICTS,
        title_update = T("Edit School District"),
        title_search = T("Search School Districts"),
        subtitle_create = T("Add New School District"),
        subtitle_list = T("School Districts"),
        label_list_button = LIST_SCHOOL_DISTRICTS,
        label_create_button = ADD_SCHOOL_DISTRICT,
        msg_record_created = T("School District added"),
        msg_record_modified = T("School District updated"),
        msg_record_deleted = T("School District deleted"),
        msg_list_empty = T("No School Districts currently registered"))

    school_district_id = db.Table(None, "school_district_id",
                                  Field("school_district_id", table,
                                  requires = IS_NULL_OR(IS_ONE_OF(db, "sitrep_school_district.id", "%(name)s")),
                                  represent = lambda id: (id and [db(db.sitrep_school_district.id == id).select(db.sitrep_school_district.name, limitby=(0, 1)).first().name] or ["None"])[0],
                                  label = T("School District"),
                                  ondelete = "RESTRICT"))

    # -----------------------------------------------------------------------------
    # School Reports
    resource = "school_report"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            school_district_id,
                            Field("name"),
                            Field("code", "integer"),
                            Field("union_council", db.gis_location),
                            Field("pf", "integer"),
                            Field("rooms_occupied", "integer"),
                            Field("families_settled", "integer"),
                            location_id,
                            Field("facilities_food", "integer"),
                            Field("facilities_nfi", "integer"),
                            Field("facilities_hygiene", "integer"),
                            Field("total_affected_male", "integer"),
                            Field("total_affected_female", "integer"),
                            Field("total_affected_total", "integer"),
                            Field("students_affected_male", "integer"),
                            Field("students_affected_female", "integer"),
                            Field("students_affected_total", "integer"),
                            Field("teachers_affected_male", "integer"),
                            Field("teachers_affected_female", "integer"),
                            Field("teachers_affected_total", "integer"),
                            comments,
                            migrate=migrate)

    table.name.label = T("Name of School")
    table.code.label = T("School Code")
    table.union_council.label = T("Union Council")
    table.union_council.requires = IS_NULL_OR(IS_ONE_OF(db(db.gis_location.level == "L3"), "gis_location.id", repr_select, sort=True))
    table.union_council.represent = lambda id: shn_gis_location_represent(id)
    table.union_council.comment = A(ADD_LOCATION,
                                       _class="colorbox",
                                       _href=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup", child="union_council")),
                                       _target="top",
                                       _title=ADD_LOCATION)
    table.pf.label = "PF"
    table.rooms_occupied.label = T("No of Rooms Occupied By Flood Affectees")
    table.families_settled.label = T("No of Families Settled in the Schools")
    table.location_id.label = T("Affectees Families settled in the school belong to district")
    table.facilities_food.label = T("No of Families to whom Food Items are Available")
    table.facilities_nfi.label = T("No of Families to whom Non-Food Items are Available")
    table.facilities_hygiene.label = T("No of Families to whom Hygiene is Available")

    table.total_affected_male.label = T("Total No of Male Affectees (Including Students, Teachers & Others)")
    table.total_affected_male.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999999))
    table.total_affected_female.label = T("Total No of Female Affectees (Including Students, Teachers & Others)")
    table.total_affected_female.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999999))
    table.total_affected_total.label = T("Total No of Affectees (Including Students, Teachers & Others)")
    table.total_affected_total.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999999))

    table.students_affected_male.label = T("No of Male Students (Primary To Higher Secondary) in the Total Affectees")
    table.students_affected_male.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999999))
    table.students_affected_female.label = T("No of Female Students (Primary To Higher Secondary) in the Total Affectees")
    table.students_affected_female.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999999))
    table.students_affected_total.label = T("Total No of Students (Primary To Higher Secondary) in the Total Affectees")
    table.students_affected_total.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999999))

    table.teachers_affected_male.label = T("No of Male Teachers & Other Govt Servants in the Total Affectees")
    table.teachers_affected_male.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999999))
    table.teachers_affected_female.label = T("No of Female Teachers & Other Govt Servants in the Total Affectees")
    table.teachers_affected_female.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999999))
    table.teachers_affected_total.label = T("Total No of Teachers & Other Govt Servants in the Total Affectees")
    table.teachers_affected_total.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999999))

    # CRUD strings
    ADD_SCHOOL_REPORT = T("Add School Report")
    LIST_SCHOOL_REPORTS = T("List School Reports")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SCHOOL_REPORT,
        title_display = T("School Report Details"),
        title_list = LIST_SCHOOL_REPORTS,
        title_update = T("Edit School Report"),
        title_search = T("Search School Reports"),
        subtitle_create = T("Add New School Report"),
        subtitle_list = T("School Reports"),
        label_list_button = LIST_SCHOOL_REPORTS,
        label_create_button = ADD_SCHOOL_REPORT,
        msg_record_created = T("School Report added"),
        msg_record_modified = T("School Report updated"),
        msg_record_deleted = T("School Report deleted"),
        msg_list_empty = T("No School Reports currently registered"))

    s3xrc.model.add_component(module, resource,
                              multiple = True,
                              joinby = dict(sitrep_school_district="school_district_id"),
                              deletable = True,
                              editable = True)

    def shn_sitrep_school_report_onvalidation(form):

        """ School report validation """

        def validate_total(total, female, male):

            error_msg = T("Contradictory values!")

            _total = form.vars.get(total, None)
            _female = form.vars.get(female, None)
            _male = form.vars.get(male, None)

            if _total is None:
                form.vars[total] = int(_female or 0) + int(_male or 0)
            else:
                _total = int(_total)
                if _male is None:
                    if _female is not None:
                        _female = int(_female)
                        if _female <= _total:
                            form.vars[male] = _total - _female
                        else:
                            form.errors[total] = form.errors[female] = error_msg
                else:
                    _male = int(_male)
                    if _female is not None:
                        _female = int(_female)
                        if _total != _female + _male:
                            form.errors[total] = form.errors[female] = form.errors[male] = error_msg
                    else:
                        if _male <= _total:
                            form.vars[female] = _total - _male
                        else:
                            form.errors[total] = form.errors[male] = error_msg

        validate_total("total_affected_total",
                       "total_affected_female",
                       "total_affected_male")

        validate_total("teachers_affected_total",
                       "teachers_affected_female",
                       "teachers_affected_male")

        validate_total("students_affected_total",
                       "students_affected_female",
                       "students_affected_male")


    s3xrc.model.configure(table,
        onvalidation = lambda form: shn_sitrep_school_report_onvalidation(form))

    # -----------------------------------------------------------------------------
