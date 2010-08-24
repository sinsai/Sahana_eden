# -*- coding: utf-8 -*-

""" Rapid Assessment Tool - Model

    @author: Fran Boon
    @author: Dominic König

    @see: U{<http://www.ecbproject.org/page/48>}

"""

module = "rat"
if deployment_settings.has_module(module):

    # -------------------------------------------------------------------------
    # Settings
    resource = "setting"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field("audit_read", "boolean"),
                            Field("audit_write", "boolean"),
                            migrate=migrate)

    # -------------------------------------------------------------------------
    # Constants
    NOT_APPLICABLE = T("N/A")

    # Section CRUD strings
    ADD_SECTION = T("Add Section")
    LIST_SECTIONS = T("List Sections")
    rat_section_crud_strings = Storage(
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

    # -------------------------------------------------------------------------
    # Common options
    rat_walking_time_opts = {
        1: T("0-15 minutes"),
        2: T("15-30 minutes"),
        3: T("30-60 minutes"),
        4: T("over one hour"),
        999: NOT_APPLICABLE
    }

    # -------------------------------------------------------------------------
    # Helper functions
    def shn_rat_represent_multiple(set, opt):

        """ Represent a IS_IN_SET with multiple=True as
            comma-separated list of options

            @param set: the options set as dict
            @param opt: the selected option(s)

        """

        if isinstance(opt, basestring):
            opts = opt.split("|")
            vals = [str(set.get(int(o), o)) for o in opts if o]
        elif isinstance(opt, (list, tuple)):
            opts = opt
            vals = [str(set.get(o, o)) for o in opts]
        elif isinstance(opt, int):
            opts = [opt]
            vals = str(set.get(opt, opt))
        else:
            return T("None")
        if len(opts) > 1:
            vals = ", ".join(vals)
        else:
            vals = len(vals) and vals[0] or ""
        return vals


    def shn_rat_label_and_tooltip(field, label, tooltip, multiple=False):

        """ Add label and tooltip to a field """

        field.label = T(label)
        if multiple:
            field.comment = DIV("(%s)" % T("Select all that apply"),
                                DIV(_class="tooltip",
                                    _title="%s|%s" % (T(label), T(tooltip))))
        else:
            field.comment = DIV(DIV(_class="tooltip",
                                    _title="%s|%s" % (T(label), T(tooltip))))


    # Rapid Assessment Tool ***************************************************

    rat_interview_location_opts = {
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

    rat_interviewee_opts = {
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

    rat_accessibility_opts = {
        1:T("2x4 Car"),
        2:T("4x4 Car"),
        3:T("Truck"),
        4:T("Motorcycle"),
        5:T("Boat"),
        6:T("Walking Only"),
        7:T("No access at all"),
        99:T("Other")
    }


    # Main Resource -----------------------------------------------------------
    # contains Section 1: Identification Information
    #
    resource = "assessment"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            Field("date", "date"),
                            location_id,
                            staff_id,
                            Field("staff2_id", db.org_staff, ondelete = "RESTRICT"),
                            Field("interview_location"),
                            Field("interviewee"),
                            Field("accessibility", "integer"),
                            comments,
                            document_id,
                            #document,
                            migrate=migrate)

    table.date.requires = [IS_DATE(), IS_NOT_EMPTY()]
    table.date.comment = SPAN("*", _class="req")
    table.date.default = datetime.datetime.today()

    table.staff2_id.requires = IS_NULL_OR(IS_ONE_OF(db, "org_staff.id", shn_org_staff_represent))
    table.staff2_id.represent = lambda id: shn_org_staff_represent(id)
    table.staff2_id.comment = A(ADD_STAFF, _class="colorbox", _href=URL(r=request, c="org", f="staff", args="create", vars=dict(format="popup", child="staff2_id")), _target="top", _title=ADD_STAFF)
    table.staff2_id.label = T("Staff 2")

    table.interview_location.label = T("Interview taking place at")
    table.interview_location.requires = IS_NULL_OR(IS_IN_SET(rat_interview_location_opts, multiple=True, zero=None))
    table.interview_location.represent = lambda opt, set=rat_interview_location_opts: \
                                         shn_rat_represent_multiple(set, opt)
    table.interview_location.comment = "(" + Tstr("Select all that apply") + ")"

    table.interviewee.label = T("Person interviewed")
    table.interviewee.requires = IS_NULL_OR(IS_IN_SET(rat_interviewee_opts, multiple=True, zero=None))
    table.interviewee.represent = lambda opt, set=rat_interviewee_opts: \
                                         shn_rat_represent_multiple(set, opt)
    table.interviewee.comment = "(" + Tstr("Select all that apply") + ")"

    table.accessibility.requires = IS_NULL_OR(IS_IN_SET(rat_accessibility_opts, zero=None))
    table.accessibility.represent = lambda opt: rat_accessibility_opts.get(opt, opt)
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


    # -------------------------------------------------------------------------
    def shn_assessment_represent(id):

        """ Represent assessment as string """

        table = db.rat_assessment
        row = db(table.id == id).select(table.date,
                                        table.staff_id,
                                        table.staff2_id,
                                        table.location_id,
                                        limitby = (0, 1)).first()

        if row:
            date = row.date and str(row.date) or ""
            location = row.location_id and shn_gis_location_represent(row.location_id) or ""

            table = db.org_staff
            org = ("", "")
            i = 0
            for staff_id in [row.staff_id, row.staff2_id]:
                i += 1
                if staff_id:
                    staff = db(table.id == staff_id).select(table.organisation_id,
                                                            limitby=(0, 1)).first()
                    if staff:
                        org[i] = shn_organisation_represent(staff.organisation_id)

            assessment_represent = XML("<div>%s %s, %s %s</div>" % (location, org[0], org[1], date))

        else:
            assessment_represent = "-"

        return assessment_represent


    # -------------------------------------------------------------------------
    # re-usable field
    assessment_id = db.Table(None, "assessment_id",
                             Field("assessment_id", table,
                                   requires = IS_NULL_OR(IS_ONE_OF(db, "rat_assessment.id", shn_assessment_represent)),
                                   represent = lambda id: shn_assessment_represent(id),
                                   label = T("Rapid Assessment"),
                                   comment = A(ADD_ASSESSMENT, _class="colorbox", _href=URL(r=request, c="rat", f="assessment", args="create", vars=dict(format="popup")), _target="top", _title=ADD_ASSESSMENT),
                                   ondelete = "RESTRICT"))


    # Assessment as component of doc_documents
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(doc_document="document_id"),
                              deletable=True,
                              editable=True)


    # Section 2: Demographic --------------------------------------------------

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

    table.assessment_id.readable = False
    table.assessment_id.writable = False

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
    s3.crud_strings[tablename] = rat_section_crud_strings

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(rat_assessment="assessment_id"),
                              deletable = False,
                              editable = True)


    # Section 3: Shelter & Essential NFIs -------------------------------------

    rat_houses_salvmat_types = {
        1: T("Wooden plank"),
        2: T("Zinc roof"),
        3: T("Bricks"),
        4: T("Wooden poles"),
        5: T("Door frame"),
        6: T("Window frame"),
        7: T("Roof tile"),
        999: NOT_APPLICABLE
    }

    rat_water_container_types = {
        1: T("Jerry can"),
        2: T("Bucket"),
        3: T("Water gallon"),
        99: T("Other (specify)")
    }

    resource = "section3"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            assessment_id,
                            Field("houses_total", "integer"),
                            Field("houses_destroyed", "integer"),
                            Field("houses_damaged", "integer"),
                            Field("houses_salvmat"),
                            Field("water_containers_available", "boolean"),
                            Field("water_containers_sufficient", "boolean"),
                            Field("water_containers_types"),
                            Field("water_containers_types_other"),
                            Field("cooking_equipment_available", "boolean"),
                            Field("sanitation_items_available", "boolean"),
                            Field("sanitation_items_available_women", "boolean"),
                            Field("bedding_materials_available", "boolean"),
                            Field("clothing_sets_available", "boolean"),
                            Field("nfi_assistance_available", "boolean"),
                            Field("kits_hygiene_received", "boolean"),
                            Field("kits_hygiene_source"),
                            Field("kits_household_received", "boolean"),
                            Field("kits_household_source"),
                            Field("kits_dwelling_received", "boolean"),
                            Field("kits_dwelling_source"),
                            comments,
                            migrate=migrate)

    table.assessment_id.readable = False
    table.assessment_id.writable = False

    table.houses_total.label = T("Total number of houses in the area")
    table.houses_total.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0,99999999))
    shn_rat_label_and_tooltip(table.houses_destroyed,
        "Number of houses destroyed/uninhabitable",
        "How many houses are uninhabitable (uninhabitable = foundation and structure destroyed)?")
    table.houses_destroyed.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0,99999999))
    shn_rat_label_and_tooltip(table.houses_damaged,
        "Number of houses damaged, but usable",
        "How many houses suffered damage but remain usable (usable = windows broken, cracks in walls, roof slightly damaged)?")
    table.houses_destroyed.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0,99999999))
    shn_rat_label_and_tooltip(table.houses_salvmat,
        "Salvage material usable from destroyed houses",
        "What type of salvage material can be used from destroyed houses?",
        multiple=True)
    table.houses_salvmat.requires = IS_NULL_OR(IS_IN_SET(rat_houses_salvmat_types, multiple=True, zero=None))
    table.houses_salvmat.represent = lambda opt, set=rat_houses_salvmat_types: \
        shn_rat_represent_multiple(set, opt)

    shn_rat_label_and_tooltip(table.water_containers_available,
        "Water storage containers available for HH",
        "Do households have household water storage containers?")
    shn_rat_label_and_tooltip(table.water_containers_sufficient,
        "Water storage containers sufficient per HH",
        "Do households each have at least 2 containers (10-20 litres each) to hold water?")
    shn_rat_label_and_tooltip(table.water_containers_types,
        "Types of water storage containers available",
        "What types of household water storage containers are available?",
        multiple=True)
    table.water_containers_types.requires = IS_EMPTY_OR(IS_IN_SET(rat_water_container_types, zero=None, multiple=True))
    table.water_containers_types.represents = lambda opt, set=rat_water_container_types: \
                                              shn_rat_represent_multiple(set, opt)
    table.water_containers_types_other.label = T("Other types of water storage containers")

    shn_rat_label_and_tooltip(table.cooking_equipment_available,
        "Appropriate cooking equipment/materials in HH",
        "Do households have appropriate equipment and materials to cook their food (stove, pots, dished plates, and a mug/drinking vessel, etc)?")
    shn_rat_label_and_tooltip(table.sanitation_items_available,
        "Reliable access to sanitation/hygiene items",
        "Do people have reliable access to sufficient sanitation/hygiene items (bathing soap, laundry soap, shampoo, toothpaste and toothbrush)?")
    shn_rat_label_and_tooltip(table.sanitation_items_available_women,
        "Easy access to sanitation items for women/girls",
        "Do women and girls have easy access to sanitary materials?")
    shn_rat_label_and_tooltip(table.bedding_materials_available,
        "Bedding materials available",
        "Do households have bedding materials available (tarps, plastic mats, blankets)?")
    shn_rat_label_and_tooltip(table.clothing_sets_available,
        "Appropriate clothing available",
        "Do people have at least 2 full sets of clothing (shirts, pants/sarong, underwear)?")

    shn_rat_label_and_tooltip(table.nfi_assistance_available,
        "Shelter/NFI assistance received/expected",
        "Have households received any shelter/NFI assistance or is assistance expected in the coming days?")

    table.kits_hygiene_received.label = T("Hygiene kits received")
    table.kits_hygiene_source.label = T("Hygiene kits, source")
    table.kits_household_received.label = T("Household kits received")
    table.kits_household_source.label = T("Household kits, source")
    table.kits_dwelling_received.label = T("Family tarpaulins received")
    table.kits_dwelling_source.label = T("Family tarpaulins, source")

    # CRUD strings
    s3.crud_strings[tablename] = rat_section_crud_strings

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(rat_assessment="assessment_id"),
                              deletable = False,
                              editable = True)

    # Section 4 - Water and Sanitation ----------------------------------------

    rat_water_source_types = {
        1: T("PDAM"),
        2: T("Dug Well"),
        3: T("Spring"),
        4: T("River"),
        5: T("Other Faucet/Piped Water"),
        99: T("Other (describe)"),
        999: NOT_APPLICABLE
    }

    rat_water_coll_person_opts = {
        1: T("Child"),
        2: T("Adult male"),
        3: T("Adult female"),
        4: T("Older person (>60 yrs)"),
        999: NOT_APPLICABLE
    }

    rat_defec_place_types = {
        1: T("open defecation"),
        2: T("pit"),
        3: T("latrines"),
        4: T("river"),
        99: T("other")
    }

    rat_defec_place_animals_opts = {
        1: T("enclosed area"),
        2: T("within human habitat"),
        999: NOT_APPLICABLE
    }

    rat_latrine_types = {
        1: T("flush latrine with septic tank"),
        2: T("pit latrine"),
        999: NOT_APPLICABLE
    }

    resource = "section4"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            assessment_id,
                            Field("water_source_pre_disaster_type", "integer"),
                            Field("water_source_pre_disaster_description"),
                            Field("dwater_source_type", "integer"),
                            Field("dwater_source_description"),
                            Field("dwater_reserve"),
                            Field("swater_source_type", "integer"),
                            Field("swater_source_description"),
                            Field("swater_reserve"),
                            Field("water_coll_time", "integer"),
                            Field("water_coll_safe", "boolean"),
                            Field("water_coll_safety_problems"),
                            Field("water_coll_person", "integer"),
                            Field("defec_place_type"),
                            Field("defec_place_description"),
                            Field("defec_place_distance", "integer"),
                            Field("defec_place_animals", "integer"),
                            Field("close_industry", "boolean"),
                            Field("waste_disposal"),
                            Field("latrines_number", "integer"),
                            Field("latrines_type", "integer"),
                            Field("latrines_separation", "boolean"),
                            Field("latrines_distance", "integer"),
                            comments,
                            migrate=migrate)

    table.assessment_id.readable = False
    table.assessment_id.writable = False

    table.water_source_pre_disaster_type.label = T("Type of water source before the disaster")
    table.water_source_pre_disaster_type.requires = IS_EMPTY_OR(IS_IN_SET(rat_water_source_types, zero=None))
    table.water_source_pre_disaster_description.label = T("Description of water source before the disaster")

    shn_rat_label_and_tooltip(table.dwater_source_type,
        "Current type of source for drinking water",
        "What is your major source of drinking water?")
    table.dwater_source_type.requires = IS_EMPTY_OR(IS_IN_SET(rat_water_source_types, zero=None))
    table.dwater_source_description.label = T("Description of drinking water source")

    shn_rat_label_and_tooltip(table.dwater_reserve,
        "How long will this water resource last?",
        "Specify the minimum sustainability in weeks or days.")

    shn_rat_label_and_tooltip(table.swater_source_type,
        "Current type of source for sanitary water",
        "What is your major source of clean water for daily use (ex: washing, cooking, bathing)?")
    table.swater_source_type.requires = IS_EMPTY_OR(IS_IN_SET(rat_water_source_types, zero=None))
    table.swater_source_description.label = T("Description of sanitary water source")
    shn_rat_label_and_tooltip(table.swater_reserve,
        "How long will this water resource last?",
        "Specify the minimum sustainability in weeks or days.")

    shn_rat_label_and_tooltip(table.water_coll_time,
        "Time needed to collect water",
        "How long does it take you to reach the available water resources? Specify the time required to go there and back, including queuing time, by foot.")
    table.water_coll_time.requires = IS_EMPTY_OR(IS_IN_SET(rat_walking_time_opts, zero=None))
    table.water_coll_safe.label = T("Is it safe to collect water?")
    table.water_coll_safe.default = True
    table.water_coll_safety_problems.label = T("If no, specify why")
    table.water_coll_person.label = T("Who usually collects water for the family?")
    table.water_coll_person.requires = IS_EMPTY_OR(IS_IN_SET(rat_water_coll_person_opts, zero=None))

    shn_rat_label_and_tooltip(table.defec_place_type,
        "Type of place for defecation",
        "Where do the majority of people defecate?",
        multiple=True)
    table.defec_place_type.requires = IS_EMPTY_OR(IS_IN_SET(rat_defec_place_types, zero=None, multiple=True))
    table.defec_place_description.label = T("Description of defecation area")
    table.defec_place_distance.label = T("Distance between defecation area and water source")
    table.defec_place_distance.comment = T("meters")
    table.defec_place_animals.label = T("Defecation area for animals")
    table.defec_place_animals.requires = IS_EMPTY_OR(IS_IN_SET(rat_defec_place_animals_opts, zero = None))

    shn_rat_label_and_tooltip(table.close_industry,
        "Industry close to village/camp",
        "Is there any industrial or agro-chemical production close to the affected area/village?")

    shn_rat_label_and_tooltip(table.waste_disposal,
        "Place for solid waste disposal",
        "Where is solid waste disposed in the village/camp?")

    shn_rat_label_and_tooltip(table.latrines_number,
        "Number of latrines",
        "How many latrines are available in the village/IDP centre/Camp?")
    table.latrines_number.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999))

    shn_rat_label_and_tooltip(table.latrines_type,
        "Type of latrines",
        "What type of latrines are available in the village/IDP centre/Camp?")
    table.latrines_type.requires = IS_EMPTY_OR(IS_IN_SET(rat_latrine_types, zero=None))

    shn_rat_label_and_tooltip(table.latrines_separation,
        "Separate latrines for women and men",
        "Are there separate latrines for women and men available?")

    shn_rat_label_and_tooltip(table.latrines_distance,
        "Distance between shelter and latrines",
        "Distance between latrines and temporary shelter in meters")

    # CRUD strings
    s3.crud_strings[tablename] = rat_section_crud_strings

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(rat_assessment="assessment_id"),
                              deletable = False,
                              editable = True)

    # Section 5 - Health ------------------------------------------------------

    rat_health_services_types = {
        1: T("Community Health Center"),
        2: T("Hospital")
    }

    rat_health_problems_opts = {
        1: T("Respiratory Infections"),
        2: T("Diarrhea"),
        3: T("Dehydration"),
        99: T("Other (specify)")
    }

    rat_infant_nutrition_alternative_opts = {
        1: T("Porridge"),
        2: T("Banana"),
        3: T("Instant Porridge"),
        4: T("Air tajin"),
        99: T("Other (specify)")
    }

    resource = "section5"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            assessment_id,
                            Field("health_services_pre_disaster", "boolean"),
                            Field("medical_supplies_pre_disaster", "boolean"),
                            Field("health_services_post_disaster", "boolean"),
                            Field("medical_supplies_post_disaster", "boolean"),
                            Field("medical_supplies_reserve", "integer"),
                            Field("health_services_available_types"),
                            Field("staff_number_doctors", "integer"),
                            Field("staff_number_nurses", "integer"),
                            Field("staff_number_midwives", "integer"),
                            Field("health_service_walking_time", "integer"),
                            Field("health_problems_adults"),
                            Field("health_problems_adults_other"),
                            Field("health_problems_children"),
                            Field("health_problems_children_other"),
                            Field("chronical_illness_cases", "boolean"),
                            Field("chronical_illness_children", "boolean"),
                            Field("chronical_illness_elderly", "boolean"),
                            Field("chronical_care_sufficient", "boolean"),
                            Field("malnutrition_present_pre_disaster", "boolean"),
                            Field("mmd_present_pre_disaster", "boolean"),
                            Field("breast_milk_substitutes_pre_disaster", "boolean"),
                            Field("breast_milk_substitutes_post_disaster", "boolean"),
                            Field("infant_nutrition_alternative"),
                            Field("infant_nutrition_alternative_other"),
                            Field("u5_diarrhea", "boolean"),
                            Field("u5_diarrhea_rate_48h", "integer"),
                            comments,
                            migrate=migrate)

    table.assessment_id.readable = False
    table.assessment_id.writable = False

    shn_rat_label_and_tooltip(table.health_services_pre_disaster,
        "Health services functioning prior to disaster",
        "Were there health services functioning for the community prior to the disaster?")

    shn_rat_label_and_tooltip(table.medical_supplies_pre_disaster,
        "Basic medical supplies available prior to disaster",
        "Were basic medical supplies available for health services prior to the disaster?")

    shn_rat_label_and_tooltip(table.health_services_post_disaster,
        "Health services functioning since disaster",
        "Are there health services functioning for the community since the disaster?")

    shn_rat_label_and_tooltip(table.medical_supplies_post_disaster,
        "Basic medical supplies available since disaster",
        "Are basic medical supplies available for health services since the disaster?")

    table.medical_supplies_reserve.label = T("How many days will the supplies last?")

    shn_rat_label_and_tooltip(table.health_services_available_types,
        "Types of health services available",
        "What types of health services are still functioning in the affected area?",
        multiple=True)
    table.health_services_available_types.requires = IS_EMPTY_OR(IS_IN_SET(rat_health_services_types,
                                                                           zero=None, multiple=True))
    table.health_services_available_types.represent = lambda opt: \
        shn_rat_represent_multiple(rat_health_service_types, opt)

    shn_rat_label_and_tooltip(table.staff_number_doctors,
        "Number of doctors actively working",
        "How many doctors in the health centers are still actively working?")
    table.staff_number_doctors.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999))

    shn_rat_label_and_tooltip(table.staff_number_nurses,
        "Number of nurses actively working",
        "How many nurses in the health centers are still actively working?")
    table.staff_number_nurses.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999))

    shn_rat_label_and_tooltip(table.staff_number_midwives,
        "Number of midwives actively working",
        "How many midwives in the health centers are still actively working?")
    table.staff_number_midwives.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999))

    shn_rat_label_and_tooltip(table.health_service_walking_time,
        "Walking time to the health service",
        "How long does it take you to walk to the health service?")
    table.health_service_walking_time.requires = IS_EMPTY_OR(IS_IN_SET(rat_walking_time_opts, zero=None))

    shn_rat_label_and_tooltip(table.health_problems_adults,
        "Current type of health problems, adults",
        "What types of health problems do people currently have?",
        multiple=True)
    table.health_problems_adults.requires = IS_EMPTY_OR(IS_IN_SET(rat_health_problems_opts, zero=None, multiple=True))
    table.health_problems_adults.represent = lambda opt, set=rat_health_problems_opts: \
                                             shn_rat_represent_multiple(set, opt)
    table.health_problems_adults_other.label = T("Other current health problems, adults")

    shn_rat_label_and_tooltip(table.health_problems_children,
        "Current type of health problems, children",
        "What types of health problems do children currently have?",
        multiple=True)
    table.health_problems_children.requires = IS_EMPTY_OR(IS_IN_SET(rat_health_problems_opts, zero=None, multiple=True))
    table.health_problems_children.represent = lambda opt, set=rat_health_problems_opts: \
                                               shn_rat_represent_multiple(set, opt)
    table.health_problems_children_other.label = T("Other current health problems, children")

    shn_rat_label_and_tooltip(table.chronical_illness_cases,
        "People with chronical illnesses",
        "Are there people with chronical illnesses in your community?")

    shn_rat_label_and_tooltip(table.chronical_illness_children,
        "Children with chronical illnesses",
        "Are there children with chronical illnesses in your community?")

    shn_rat_label_and_tooltip(table.chronical_illness_elderly,
        "Older people with chronical illnesses",
        "Are there older people with chronical illnesses in your community?")

    shn_rat_label_and_tooltip(table.chronical_care_sufficient,
        "Sufficient care/assistance for chronically ill",
        "Are the chronically ill receiving sufficient care and assistance?")

    shn_rat_label_and_tooltip(table.malnutrition_present_pre_disaster,
        "Malnutrition present prior to disaster",
        "Were there cases of malnutrition in this area prior to the disaster?")

    shn_rat_label_and_tooltip(table.mmd_present_pre_disaster,
        "Micronutrient malnutrition prior to disaster",
        "Were there reports or evidence of outbreaks of any micronutrient malnutrition disorders before the emergency?")

    shn_rat_label_and_tooltip(table.breast_milk_substitutes_pre_disaster,
        "Breast milk substitutes used prior to disaster",
        "Were breast milk substitutes used prior to the disaster?")
    shn_rat_label_and_tooltip(table.breast_milk_substitutes_post_disaster,
        "Breast milk substitutes in use since disaster",
        "Are breast milk substitutes being used here since the disaster?")

    shn_rat_label_and_tooltip(table.infant_nutrition_alternative,
        "Alternative infant nutrition in use",
        "Babies who are not being breastfed, what are they being fed on?",
        multiple=True)
    table.infant_nutrition_alternative.requires = \
        IS_EMPTY_OR(IS_IN_SET(rat_infant_nutrition_alternative_opts, zero=None, multiple=True))
    table.infant_nutrition_alternative.represent = lambda opt, set=rat_infant_nutrition_alternative_opts: \
        shn_rat_represent_multiple(set, opt)

    table.infant_nutrition_alternative_other.label = T("Other alternative infant nutrition in use")

    shn_rat_label_and_tooltip(table.u5_diarrhea,
        "Diarrhea among children under 5",
        "Are there cases of diarrhea among children under the age of 5?")

    shn_rat_label_and_tooltip(table.u5_diarrhea_rate_48h,
        "Approx. number of cases/48h",
        "Approximately how many children under 5 with diarrhea in the past 48 hours?"),

    # CRUD strings
    s3.crud_strings[tablename] = rat_section_crud_strings

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(rat_assessment="assessment_id"),
                              deletable = False,
                              editable = True)

    # Section 6 - Nutrition/Food Security -------------------------------------

    rat_main_dish_types = {
        1: T("Rice"),
        2: T("Noodles"),
        3: T("Biscuits"),
        4: T("Corn"),
        5: T("Wheat"),
        6: T("Cassava"),
        7: T("Cooking Oil")
    }

    rat_side_dish_types = {
        1: T("Salted Fish"),
        2: T("Canned Fish"),
        3: T("Chicken"),
        4: T("Eggs"),
        99: T("Other (specify)")
    }

    rat_food_stock_reserve_opts = {
        1: T("1-3 days"),
        2: T("4-7 days"),
        3: T("8-14 days")
    }

    rat_food_source_types = {
        1: "Local market",
        2: "Field cultivation",
        3: "Food stall",
        4: "Animal husbandry",
        5: "Raising poultry",
        99: "Other (specify)"
    }

    resource = "section6"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            assessment_id,
                            Field("food_stocks_main_dishes"),
                            Field("food_stocks_side_dishes"),
                            Field("food_stocks_other_side_dishes"),
                            Field("food_stocks_reserve", "integer"),
                            Field("food_sources"),
                            Field("food_sources_other"),
                            Field("food_sources_disruption", "boolean"),
                            Field("food_sources_disruption_details"),
                            Field("food_assistance_available", "boolean"),
                            Field("food_assistance_details", "text"),
                            comments,
                            migrate=migrate)

    table.assessment_id.readable = False
    table.assessment_id.writable = False

    shn_rat_label_and_tooltip(table.food_stocks_main_dishes,
        "Existing food stocks, main dishes",
        "What food stocks exist? (main dishes)",
        multiple=True)
    table.food_stocks_main_dishes.requires = IS_EMPTY_OR(IS_IN_SET(rat_main_dish_types, zero=None, multiple=True))
    table.food_stocks_main_dishes.represent = lambda opt, set=rat_main_dish_types: \
                                              shn_rat_represent_multiple(set, opt)
    shn_rat_label_and_tooltip(table.food_stocks_side_dishes,
        "Existing food stocks, side dishes",
        "What food stocks exist? (side dishes)",
        multiple=True)
    table.food_stocks_side_dishes.requires = IS_EMPTY_OR(IS_IN_SET(rat_side_dish_types, zero=None, multiple=True))
    table.food_stocks_side_dishes.represent = lambda opt, set=rat_side_dish_types: \
                                              shn_rat_represent_multiple(set, opt)
    table.food_stocks_other_side_dishes.label = T("Other side dishes in stock")
    table.food_stocks_reserve.label = T("How long will the food last?")
    table.food_stocks_reserve.requires = IS_EMPTY_OR(IS_IN_SET(rat_food_stock_reserve_opts, zero=None))

    shn_rat_label_and_tooltip(table.food_sources,
        "Usual food sources in the area",
        "What are the people's normal ways to obtain food in this area?",
        multiple=True)
    table.food_sources.requires = IS_EMPTY_OR(IS_IN_SET(rat_food_source_types, zero=None, multiple=True))
    table.food_sources.represent = lambda opt, set=rat_food_source_types: \
                                   shn_rat_represent_multiple(set, opt)
    table.food_sources_other.label = T("Other ways to obtain food")

    shn_rat_label_and_tooltip(table.food_sources_disruption,
        "Normal food sources disrupted",
        "Have normal food sources been disrupted?")
    table.food_sources_disruption_details.label = T("If yes, which and how")

    shn_rat_label_and_tooltip(table.food_assistance_available,
        "Food assistance available/expected",
        "Have the people received or are you expecting any medical or food assistance in the coming days?")

    table.food_assistance_details.label = T("If yes, specify what and by whom")

    # CRUD strings
    s3.crud_strings[tablename] = rat_section_crud_strings

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(rat_assessment="assessment_id"),
                              deletable = False,
                              editable = True)

    # Section 7 - Livelihood --------------------------------------------------

    rat_income_source_opts = {
        1: T("Agriculture"),
        2: T("Fishing"),
        3: T("Poultry"),
        4: T("Casual Labor"),
        5: T("Small Trade"),
        6: T("Other")
    }

    rat_expense_types = {
        1: T("Education"),
        2: T("Health"),
        3: T("Food"),
        4: T("Hygiene"),
        5: T("Shelter"),
        6: T("Clothing"),
        7: T("Funeral"),
        8: T("Alcohol"),
        99: T("Other (specify)")
    }

    rat_cash_source_opts = {
        1: T("Family/friends"),
        2: T("Government"),
        3: T("Bank/micro finance"),
        4: T("Humanitarian NGO"),
        99: T("Other (specify)")
    }

    rat_ranking_opts = xrange(1,7)

    resource = "section7"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            assessment_id,
                            Field("income_sources_pre_disaster"),
                            Field("income_sources_post_disaster"),
                            Field("main_expenses"),
                            Field("main_expenses_other"),

                            Field("business_damaged", "boolean"),
                            Field("business_cash_available", "boolean"),
                            Field("business_cash_source"),

                            Field("rank_reconstruction_assistance", "integer"),
                            Field("rank_farmland_fishing_assistance", "integer"),
                            Field("rank_poultry_restocking", "integer"),
                            Field("rank_health_care_assistance", "integer"),
                            Field("rank_transportation_assistance", "integer"),
                            Field("other_assistance_needed"),
                            Field("rank_other_assistance", "integer"),

                            comments,
                            migrate=migrate)

    table.assessment_id.readable = False
    table.assessment_id.writable = False

    shn_rat_label_and_tooltip(table.income_sources_pre_disaster,
        "Main income sources before disaster",
        "What were your main sources of income before the disaster?",
        multiple=True)
    table.income_sources_pre_disaster.requires = IS_EMPTY_OR(IS_IN_SET(rat_income_source_opts, zero=None, multiple=True))
    table.income_sources_pre_disaster.represent =  lambda opt, set=rat_income_source_opts: \
                                                   shn_rat_represent_multiple(set, opt)
    shn_rat_label_and_tooltip(table.income_sources_post_disaster,
        "Current main income sources",
        "What are your main sources of income now?",
        multiple=True)
    table.income_sources_post_disaster.requires = IS_EMPTY_OR(IS_IN_SET(rat_income_source_opts, zero=None, multiple=True))
    table.income_sources_post_disaster.represent = lambda opt, set=rat_income_source_opts: \
                                                   shn_rat_represent_multiple(set, opt)
    shn_rat_label_and_tooltip(table.main_expenses,
        "Current major expenses",
        "What do you spend most of your income on now?",
        multiple=True)
    table.main_expenses.requires = IS_EMPTY_OR(IS_IN_SET(rat_expense_types, zero=None, multiple=True))
    table.main_expenses.represent = lambda opt, set=rat_expense_types: \
                                    shn_rat_represent_multiple(set, opt)
    table.main_expenses_other.label = T("Other major expenses")

    shn_rat_label_and_tooltip(table.business_damaged,
        "Business damaged",
        "Has your business been damaged in the course of the disaster?")
    shn_rat_label_and_tooltip(table.business_cash_available,
        "Cash available to restart business",
        "Do you have access to cash to restart your business?")
    shn_rat_label_and_tooltip(table.business_cash_source,
        "Main cash source",
        "What are your main sources of cash to restart your business?")
    table.business_cash_source.requires = IS_EMPTY_OR(IS_IN_SET(rat_cash_source_opts, zero=None, multiple=True))
    table.business_cash_source.represent = lambda opt, set=rat_cash_source_opts: \
                                           shn_rat_represent_multiple(set, opt)

    shn_rat_label_and_tooltip(table.rank_reconstruction_assistance,
        "Immediate reconstruction assistance, Rank",
        "Assistance for immediate repair/reconstruction of houses")
    table.rank_reconstruction_assistance.requires = IS_EMPTY_OR(IS_IN_SET(rat_ranking_opts, zero=None))
    table.rank_farmland_fishing_assistance.label = T("Farmland/fishing material assistance, Rank")
    table.rank_farmland_fishing_assistance.requires = IS_EMPTY_OR(IS_IN_SET(rat_ranking_opts, zero=None))
    table.rank_poultry_restocking.label = T("Poultry restocking, Rank")
    table.rank_poultry_restocking.requires = IS_EMPTY_OR(IS_IN_SET(rat_ranking_opts, zero=None))
    table.rank_health_care_assistance.label = T("Health care assistance, Rank")
    table.rank_health_care_assistance.requires = IS_EMPTY_OR(IS_IN_SET(rat_ranking_opts, zero=None))
    table.rank_transportation_assistance.label = T("Transportation assistance, Rank")
    table.rank_transportation_assistance.requires = IS_EMPTY_OR(IS_IN_SET(rat_ranking_opts, zero=None))
    table.other_assistance_needed.label = T("Other assistance needed")
    table.rank_other_assistance.label = T("Other assistance, Rank")
    table.rank_other_assistance.requires = IS_EMPTY_OR(IS_IN_SET(rat_ranking_opts, zero=None))

    # CRUD strings
    s3.crud_strings[tablename] = rat_section_crud_strings

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(rat_assessment="assessment_id"),
                              deletable = False,
                              editable = True)

    # Section 8 - Education ---------------------------------------------------

    resource = "section8"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            assessment_id,
                            # Total number of schools in the affected area
                            Field("schools_total", "integer"),
                            # Number of public schools
                            Field("schools_public", "integer"),
                            # Number of private schools
                            Field("schools_private", "integer"),
                            # Number of religious schools
                            Field("schools_religious", "integer"),
                            # Number of schools uninhabitable/destroyed
                            Field("schools_destroyed", "integer"),
                            # Number of schools damaged, but usable
                            Field("schools_damaged", "integer"),
                            # Type of salvage material from destroyed schools
                            # Alternative places for studying - available
                            # Alternative places for studying - how many
                            # Alternative places for studying - where
                            # ...
                            comments,
                            migrate=migrate)

    table.assessment_id.readable = False
    table.assessment_id.writable = False

    table.schools_total.label = T("Total number of schools in affected area")
    table.schools_total.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999))
    table.schools_total.comment = T("schools")

    table.schools_public.label = T("Number of Public schools")
    table.schools_public.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999))
    table.schools_private.label = T("Number of Private schools")
    table.schools_private.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999))
    table.schools_religious.label = T("Number of Religious schools")
    table.schools_religious.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999))

    table.schools_destroyed.label = T("How many schools are uninhabitable/destroyed")
    table.schools_destroyed.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999))
    table.schools_destroyed.comment = T("schools")

    table.schools_damaged.label = T("How many schools are damaged, but remain usable")
    table.schools_damaged.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999))
    table.schools_damaged.comment = T("schools")

    # CRUD strings
    s3.crud_strings[tablename] = rat_section_crud_strings

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(rat_assessment="assessment_id"),
                              deletable = False,
                              editable = True)

    # Section 9 - Protection --------------------------------------------------

    rat_quantity_opts = {
        1: T("None"),
        2: T("Few"),
        3: T("Some"),
        4: T("Many")
    }

    resource = "section9"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            assessment_id,
                            # Are the areas that children, older people, and
                            # people with disabilities live in, play in and
                            # walk through on a daily basis physically safe?
                            Field("sec_vuln_groups", "boolean"),
                            # Has the safety and security of women and children
                            # in your community changed since the emergency
                            Field("sec_vuln_groups_affected", "boolean"),

                            Field("sec_incidents", "boolean"),
                            Field("sec_incidents_gbv", "boolean"),

                            Field("sec_current_needs"),

                            Field("children_separated", "integer",
                                  requires = IS_IN_SET(rat_quantity_opts, zero=None)),
                            Field("children_separated_origin"),
                            Field("children_missing", "integer",
                                  requires = IS_IN_SET(rat_quantity_opts, zero=None)),
                            Field("children_orphaned", "integer",
                                  requires = IS_IN_SET(rat_quantity_opts, zero=None)),
                            Field("children_evacuated", "integer",
                                  requires = IS_IN_SET(rat_quantity_opts, zero=None)),
                            Field("children_evacuated_to"),
                            Field("children_unattended", "integer",
                                  requires = IS_IN_SET(rat_quantity_opts, zero=None)),
                            Field("children_disappeared", "integer",
                                  requires = IS_IN_SET(rat_quantity_opts, zero=None)),
                            Field("children_with_older_caregivers", "integer",
                                  requires = IS_IN_SET(rat_quantity_opts, zero=None)),

                            comments,
                            migrate=migrate)

    table.assessment_id.readable = False
    table.assessment_id.writable = False

    #table.sec_area_safe.label = T("Children, elderly and disabled persons physically safe")
    #table.sec_safety_affected.label = T("Safety of children and women affected by disaster")

    table.sec_incidents.label = T("Known incidents of violence")
    table.sec_incidents_gbv.label = T("Known incidents of gender-based violence")

    table.sec_current_needs.label = T("Current needs to improve safety for vulnerable groups")

    table.children_separated.label = T("Children separated from their parents/caregivers")
    table.children_missing.label = T("Parents/Caregivers missing children")
    table.children_orphaned.label = T("Children orphaned by the disaster")
    table.children_evacuated.label = T("Children that have been sent to safe places")
    table.children_evacuated_to.label = T("Places the children have been sent to")
    table.children_unattended.label = T("Children living on their own (without adults)")
    table.children_disappeared.label = T("Children who have disappeared since the disaster")
    table.children_with_older_caregivers.label = T("Older people as primary caregivers of children")

    # CRUD strings
    s3.crud_strings[tablename] = rat_section_crud_strings

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = dict(rat_assessment="assessment_id"),
                              deletable = False,
                              editable = True)

    # -----------------------------------------------------------------------------
    def shn_rat_summary(r, **attr):

        """ Aggregate reports """

        if r.name == "assessment":
            if r.representation == "html":
                return dict()
            elif r.representation == "xls":
                return None
            else:
                # Other formats?
                raise HTTP(501, body=BADFORMAT)
        else:
            raise HTTP(501, body=BADMETHOD)


    s3xrc.model.set_method(module, "assessment",
                           method="summary",
                           action=shn_rat_summary)


    # -----------------------------------------------------------------------------
