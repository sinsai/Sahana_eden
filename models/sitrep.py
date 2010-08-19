# -*- coding: utf-8 -*-

"""
    Flood Alerts Module - Model

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

    # Rapid Assessments
    # See: http://www.ecbproject.org/page/48
    rassessment_interview_location_opts = {
        1:T("Village"),
        2:T("Urban area"),
        3:T("Collective center"),
        4:T("Informal camp"),
        5:T("Formal camp"),
        6:T("School"),
        7:T("Mosque"),
        8:T("Church"),
        99:T("Other")
    }
    rassessment_interviewee_opts = {
        1:T("Male"),
        2:T("Female"),
        3:T("Village Leader"),
        4:T("Informal Leader"),
        5:T("Community Member"),
        6:T("Religious Leader"),
        7:T("Police"),
        8:T("Healthcare Worker"),
        9:T("School Teacher"),
        10:T("Womens Focus Groups"),
        11:T("Child (< 18 yrs)"),
        99:T("Other")
    }
    rassessment_accessibility_opts = {
        1:T("2x4 Car"),
        2:T("4x4 Car"),
        3:T("Truck"),
        4:T("Motorcycle"),
        5:T("Boat"),
        6:T("Walking Only"),
        7:T("No access at all"),
        99:T("Other")
    }
    # Main Resource
    # contains Section 1: Identification Information
    resource = "rassessment"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            Field("date", "date"),
                            location_id,
                            staff_id,
                            Field("staff2_id", db.org_staff, ondelete = "RESTRICT"),
                            Field("interview_location", "integer"),
                            Field("interviewee", "integer"),
                            Field("accessibility", "integer"),
                            comments,
                            document_id,
                            document,
                            migrate=migrate)

    table.date.requires = IS_NULL_OR(IS_DATE())
    table.staff2_id.requires = IS_NULL_OR(IS_ONE_OF(db, "org_staff.id", shn_org_staff_represent))
    table.staff2_id.represent = lambda id: shn_org_staff_represent(id)
    table.staff2_id.comment = A(ADD_STAFF, _class="colorbox", _href=URL(r=request, c="org", f="staff", args="create", vars=dict(format="popup", child="staff2_id")), _target="top", _title=ADD_STAFF)
    table.staff2_id.label = T("Staff 2")
    table.interview_location.requires = IS_NULL_OR(IS_IN_SET(rassessment_interview_location_opts, multiple=True, zero=None))
    table.interview_location.represent = lambda opt: rassessment_interview_location_opts.get(opt, opt)
    table.interview_location.label = T("Interview taking place at")
    table.interview_location.comment = "(" + Tstr("Select all that apply") + ")"
    table.interviewee.requires = IS_NULL_OR(IS_IN_SET(rassessment_interviewee_opts, multiple=True, zero=None))
    table.interviewee.represent = lambda opt: rassessment_interviewee_opts.get(opt, opt)
    table.interviewee.label = T("Person interviewed")
    table.interviewee.comment = "(" + Tstr("Select all that apply") + ")"
    table.accessibility.requires = IS_NULL_OR(IS_IN_SET(rassessment_accessibility_opts, zero=None))
    table.accessibility.represent = lambda opt: rassessment_accessibility_opts.get(opt, opt)
    table.accessibility.label = T("Accessibility of Affected Location")
    
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

    # re-usable field
    def shn_rassessment_represent(id):
        row = db(db.sitrep_rassessment == id).select(db.sitrep_rassessment.date,
                                                        db.sitrep_rassessment.staff_id,
                                                        db.sitrep_rassessment.staff2_id,
                                                        db.sitrep_rassessment.location_id, 
                                                        limitby = [0, 1]).first()
        if row:
            if row.date:
                date = str(row.date)
            else:
                date = ""
            if row.location_id:
                location = shn_location_represent(row.location_id)
            else:
                location = ""
            if row.staff_id:
                staff = db(db.org_staff.id == row.staff_id).select(db.org_staff.organisation_id).first()
                organisation = shn_organisation_represent(staff.organisation_id)
            else:
                organisation = ""
            if row.staff2_id:
                staff2 = db(db.org_staff.id == row.staff2_id).select(db.org_staff.organisation_id).first()
                organisation2 = shn_organisation_represent(staff2.organisation_id)
            else:
                organisation2 = ""
            rassessment_represent = location + organisation + ", " + organisation2 + " " + date
        else:
            rassessment_represent = "-"

        return rassessment_represent

    assessment_id = db.Table(None, "assessment_id",
                             Field("assessment_id", table,
                                   requires = IS_NULL_OR(IS_ONE_OF(db, "sitrep_rassessment.id", shn_rassessment_represent)),
                                   represent = lambda id: shn_rassessment_represent(id),
                                   label = T("Rapid Assessment"),
                                   comment = A(ADD_ASSESSMENT, _class="colorbox", _href=URL(r=request, c="sitrep", f="rassessment", args="create", vars=dict(format="popup")), _target="top", _title=ADD_ASSESSMENT),
                                   ondelete = "RESTRICT"))
    
    # rassessment as component of doc_documents
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(doc_document="document_id"),
                              deletable=True,
                              editable=True)

    # Section 2: Demographic
    resource = "section2"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            assessment_id,
                            Field("population_affected", "integer"),
                            Field("households_affected", "integer"),
                            Field("population_total", "integer"),
                            Field("households_total", "integer"),
                            Field("male_05", "double"),
                            Field("male_612", "double"),
                            Field("male_1317", "double"),
                            Field("male_1825", "double"),
                            Field("male_2660", "double"),
                            Field("male_61", "double"),
                            Field("female_05", "double"),
                            Field("female_612", "double"),
                            Field("female_1317", "double"),
                            Field("female_1825", "double"),
                            Field("female_2660", "double"),
                            Field("female_61", "double"),
                            Field("dead_women", "integer"),
                            Field("dead_men", "integer"),
                            Field("dead_girl", "integer"),
                            Field("dead_boy", "integer"),
                            Field("missing_women", "integer"),
                            Field("missing_men", "integer"),
                            Field("missing_girl", "integer"),
                            Field("missing_boy", "integer"),
                            Field("injured_women", "integer"),
                            Field("injured_men", "integer"),
                            Field("injured_girl", "integer"),
                            Field("injured_boy", "integer"),
                            Field("household_head_elderly", "integer"),
                            Field("household_head_female", "integer"),
                            Field("household_head_child", "integer"),
                            Field("disabled_physical", "integer"),
                            Field("disabled_mental", "integer"),
                            Field("pregnant", "integer"),
                            Field("lactating", "integer"),
                            Field("minorities", "integer"),
                            comments,
                            migrate=migrate)

    table.population_affected.label = T("Estimated # of people who are affected by the emergency")
    table.population_affected.comment = T("people")
    table.households_affected.label = T("Estimated # of households who are affected by the emergency")
    table.households_affected.comment = T("HH")
    table.population_total.label = T("Total population of site visited")
    table.population_total.comment = T("people")
    table.households_total.label = T("Total # of households of site visited")
    table.households_total.comment = T("HH")
    table.male_05.label = T("Number/Percentage of affected population that is Male & Aged 0-5")
    table.male_612.label = T("Number/Percentage of affected population that is Male & Aged 6-12")
    table.male_1317.label = T("Number/Percentage of affected population that is Male & Aged 13-17")
    table.male_1825.label = T("Number/Percentage of affected population that is Male & Aged 18-25")
    table.male_2660.label = T("Number/Percentage of affected population that is Male & Aged 26-60")
    table.male_61.label = T("Number/Percentage of affected population that is Male & Aged 61+")
    table.female_05.label = T("Number/Percentage of affected population that is Female & Aged 0-5")
    table.female_612.label = T("Number/Percentage of affected population that is Female & Aged 6-12")
    table.female_1317.label = T("Number/Percentage of affected population that is Female & Aged 13-17")
    table.female_1825.label = T("Number/Percentage of affected population that is Female & Aged 18-25")
    table.female_2660.label = T("Number/Percentage of affected population that is Female & Aged 26-60")
    table.female_61.label = T("Number/Percentage of affected population that is Female & Aged 61+")
    table.dead_women.label = T("How many Women (18 yrs+) are Dead due to the crisis")
    table.dead_women.comment = T("people")
    table.dead_men.label = T("How many Men (18 yrs+) are Dead due to the crisis")
    table.dead_men.comment = T("people")
    table.dead_girl.label = T("How many Girls (0-17 yrs) are Dead due to the crisis")
    table.dead_girl.comment = T("people")
    table.dead_boy.label = T("How many Boys (0-17 yrs) are Dead due to the crisis")
    table.dead_boy.comment = T("people")
    table.missing_women.label = T("How many Women (18 yrs+) are Missing due to the crisis")
    table.missing_women.comment = T("people")
    table.missing_men.label = T("How many Men (18 yrs+) are Missing due to the crisis")
    table.missing_men.comment = T("people")
    table.missing_girl.label = T("How many Girls (0-17 yrs) are Missing due to the crisis")
    table.missing_girl.comment = T("people")
    table.missing_boy.label = T("How many Boys (0-17 yrs) are Missing due to the crisis")
    table.missing_boy.comment = T("people")
    table.injured_women.label = T("How many Women (18 yrs+) are Injured due to the crisis")
    table.injured_women.comment = T("people")
    table.injured_men.label = T("How many Men (18 yrs+) are Injured due to the crisis")
    table.injured_men.comment = T("people")
    table.injured_girl.label = T("How many Girls (0-17 yrs) are Injured due to the crisis")
    table.injured_girl.comment = T("people")
    table.injured_boy.label = T("How many Boys (0-17 yrs) are Injured due to the crisis")
    table.injured_boy.comment = T("people")
    table.household_head_elderly.label = T("Elderly person headed HH (>60 yrs)")
    table.household_head_elderly.comment = T("HH")
    table.household_head_female.label = T("Female headed HH")
    table.household_head_female.comment = T("HH")
    table.household_head_child.label = T("Child headed HH (<18 yrs)")
    table.household_head_child.comment = T("HH")
    table.disabled_physical.label = T("Person with disability (physical)")
    table.disabled_physical.comment = T("people")
    table.disabled_mental.label = T("Person with disability (mental)")
    table.disabled_mental.comment = T("people")
    table.pregnant.label = T("Pregnant women")
    table.pregnant.comment = T("people")
    table.lactating.label = T("Lactating women")
    table.lactating.comment = T("people")
    table.minorities.label = T("Migrants or ethnic minorities")
    table.minorities.comment = T("people")
                            
    # CRUD strings
    ADD_SECTION = T("Add Section")
    LIST_SECTIONS = T("List Sections")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SECTION,
        title_display = T("Section Details"),
        title_list = LIST_SECTIONS,
        title_update = "",
        title_search = T("Search Sections"),
        subtitle_create = "",
        subtitle_list = T("Sections"),
        label_list_button = LIST_SECTIONS,
        label_create_button = ADD_SECTION,
        msg_record_created = T("Section updated"),
        msg_record_modified = T("Section updated"),
        msg_record_deleted = T("Section deleted"),
        msg_list_empty = T("No Sections currently registered"))

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(sitrep_rassessment="assessment_id"),
                              deletable = False,
                              editable = True)

    # Section 3: Shelter & Essential NFIs
    resource = "section3"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            assessment_id,
                            comments,
                            migrate=migrate)

    # CRUD strings
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SECTION,
        title_display = T("Section Details"),
        title_list = LIST_SECTIONS,
        title_update = "",
        title_search = T("Search Sections"),
        subtitle_create = "",
        subtitle_list = T("Sections"),
        label_list_button = LIST_SECTIONS,
        label_create_button = ADD_SECTION,
        msg_record_created = T("Section updated"),
        msg_record_modified = T("Section updated"),
        msg_record_deleted = T("Section deleted"),
        msg_list_empty = T("No Sections currently registered"))

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(sitrep_rassessment="assessment_id"),
                              deletable = False,
                              editable = True)

    # Section 4
    resource = "section4"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            assessment_id,
                            comments,
                            migrate=migrate)

    # CRUD strings
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SECTION,
        title_display = T("Section Details"),
        title_list = LIST_SECTIONS,
        title_update = "",
        title_search = T("Search Sections"),
        subtitle_create = "",
        subtitle_list = T("Sections"),
        label_list_button = LIST_SECTIONS,
        label_create_button = ADD_SECTION,
        msg_record_created = T("Section updated"),
        msg_record_modified = T("Section updated"),
        msg_record_deleted = T("Section deleted"),
        msg_list_empty = T("No Sections currently registered"))

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(sitrep_rassessment="assessment_id"),
                              deletable = False,
                              editable = True)

    # Section 5
    resource = "section5"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            assessment_id,
                            comments,
                            migrate=migrate)

    # CRUD strings
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SECTION,
        title_display = T("Section Details"),
        title_list = LIST_SECTIONS,
        title_update = "",
        title_search = T("Search Sections"),
        subtitle_create = "",
        subtitle_list = T("Sections"),
        label_list_button = LIST_SECTIONS,
        label_create_button = ADD_SECTION,
        msg_record_created = T("Section updated"),
        msg_record_modified = T("Section updated"),
        msg_record_deleted = T("Section deleted"),
        msg_list_empty = T("No Sections currently registered"))

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(sitrep_rassessment="assessment_id"),
                              deletable = False,
                              editable = True)
    
    # Section 6
    resource = "section6"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            assessment_id,
                            comments,
                            migrate=migrate)

    # CRUD strings
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SECTION,
        title_display = T("Section Details"),
        title_list = LIST_SECTIONS,
        title_update = "",
        title_search = T("Search Sections"),
        subtitle_create = "",
        subtitle_list = T("Sections"),
        label_list_button = LIST_SECTIONS,
        label_create_button = ADD_SECTION,
        msg_record_created = T("Section updated"),
        msg_record_modified = T("Section updated"),
        msg_record_deleted = T("Section deleted"),
        msg_list_empty = T("No Sections currently registered"))

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(sitrep_rassessment="assessment_id"),
                              deletable = False,
                              editable = True)

    # Section 7
    resource = "section7"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            assessment_id,
                            comments,
                            migrate=migrate)

    # CRUD strings
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SECTION,
        title_display = T("Section Details"),
        title_list = LIST_SECTIONS,
        title_update = "",
        title_search = T("Search Sections"),
        subtitle_create = "",
        subtitle_list = T("Sections"),
        label_list_button = LIST_SECTIONS,
        label_create_button = ADD_SECTION,
        msg_record_created = T("Section updated"),
        msg_record_modified = T("Section updated"),
        msg_record_deleted = T("Section deleted"),
        msg_list_empty = T("No Sections currently registered"))

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(sitrep_rassessment="assessment_id"),
                              deletable = False,
                              editable = True)
    
    # Section 8
    resource = "section8"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            assessment_id,
                            comments,
                            migrate=migrate)

    # CRUD strings
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SECTION,
        title_display = T("Section Details"),
        title_list = LIST_SECTIONS,
        title_update = "",
        title_search = T("Search Sections"),
        subtitle_create = "",
        subtitle_list = T("Sections"),
        label_list_button = LIST_SECTIONS,
        label_create_button = ADD_SECTION,
        msg_record_created = T("Section updated"),
        msg_record_modified = T("Section updated"),
        msg_record_deleted = T("Section deleted"),
        msg_list_empty = T("No Sections currently registered"))

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(sitrep_rassessment="assessment_id"),
                              deletable = False,
                              editable = True)
    
    # Section 9
    resource = "section9"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            assessment_id,
                            comments,
                            migrate=migrate)

    # CRUD strings
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SECTION,
        title_display = T("Section Details"),
        title_list = LIST_SECTIONS,
        title_update = "",
        title_search = T("Search Sections"),
        subtitle_create = "",
        subtitle_list = T("Sections"),
        label_list_button = LIST_SECTIONS,
        label_create_button = ADD_SECTION,
        msg_record_created = T("Section updated"),
        msg_record_modified = T("Section updated"),
        msg_record_deleted = T("Section deleted"),
        msg_list_empty = T("No Sections currently registered"))

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(sitrep_rassessment="assessment_id"),
                              deletable = False,
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
                            Field("population", "integer"),
                            Field("persons_affected", "integer"),
                            Field("persons_injured", "integer"),
                            Field("persons_deceased", "integer"),                            
                            Field("houses_destroyed", "integer"),
                            Field("houses_damaged", "integer"),
                            Field("crop_losses", "integer"),
                            Field("water_level", "boolean"),
                            Field("crops_affectees", "double"),
                            Field("source"),
                            document_id,
                            comments,
                            migrate=migrate)

    table.households.label = T("Total Households")
    table.households.requires = IS_INT_IN_RANGE(0,99999999)
    table.households.default = 0
    table.population.label = T("Population")
    table.population.requires = IS_INT_IN_RANGE(0,99999999)
    table.population.default = 0
    
    table.persons_affected.label = T("# of People Affected")
    table.persons_injured.label = T("# of People Injured")
    table.persons_deceased.label = T("# of People Deceased")    
    table.houses_destroyed.label = T("# of Houses Destroyed") 
    table.houses_damaged.label = T("# of Houses Damaged") 
    
    table.houses_destroyed.requires = IS_INT_IN_RANGE(0,99999999)
    table.houses_destroyed.default = 0
    table.houses_damaged.requires = IS_INT_IN_RANGE(0,99999999)
    table.houses_damaged.default = 0

    table.crop_losses.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 100))

    table.source.comment = DIV(DIV(_class="tooltip",
                              _title=Tstr("Source") + "|" + Tstr("Ideally a full URL to the source file, otherwise just a note on where data came from.")))

    # CRUD strings
    #ADD_ASSESSMENT = T("Add Assessment")
    #LIST_ASSESSMENTS = T("List Assessments")
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
    
    # assessment as component of doc_documents
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(doc_document="document_id"),
                              deletable=True,
                              editable=True)    

    # -----------------------------------------------------------------------------
    # School Districts
    # @ToDo Move to CR
    resource = "school_district"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            Field("name"),
                            location_id,
                            Field("reported_by"),
                            Field("date", "date"),
                            document_id,
                            document,
                            comments,
                            migrate=migrate)

    table.document.represent = lambda document, table=table: (document and [A(table.document.retrieve(document)[0], _href=URL(r=request, f="download", args=[document]))] or ["None"])[0]
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

    # school_district as component of doc_documents
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(doc_document="document_id"),
                              deletable=True,
                              editable=True)
    
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
    def shn_sitrep_summary(r, **attr):

        """ Aggregate reports """

        if r.name == "assessment":
            if r.representation == "html":
                return dict()
            elif r.representation == "xls":
                return None
            else:
                # Other formats?
                raise HTTP(501, body=BADFORMAT)
        elif r.name == "school_district":
            if r.representation == "html":
                # School reports HTML/jqplot reporting here
                return dict()
            else:
                # Other formats?
                raise HTTP(501, body=BADFORMAT)
        else:
            raise HTTP(501, body=BADMETHOD)


    s3xrc.model.set_method(module, "assessment",
                           method="summary",
                           action=shn_sitrep_summary)

    s3xrc.model.set_method(module, "school_district",
                           method="summary",
                           action=shn_sitrep_summary)


    # -----------------------------------------------------------------------------
