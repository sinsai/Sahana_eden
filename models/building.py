# -*- coding: utf-8 -*-

"""
    Buildings Assessments module

    @author Pradnya Kulkarni <kulkarni.pradnya@gmail.com>
    @author Akila Ramakr <aramakr@ncsu.edu>
    @author Fran Boon <fran@aidiq.com>

    Data model from:
    http://www.atcouncil.org/products/downloadable-products/placards

    Postearthquake Safety Evaluation of Buildings: ATC-20
    http://www.atcouncil.org/pdfs/rapid.pdf
    
    @ToDo: add other forms (ATC-38, ATC-45)
"""

module = "building"

if deployment_settings.has_module(module):

    # Section CRUD strings
    ADD_SECTION = T("Add Section")
    LIST_SECTIONS = T("List Sections")
    section_crud_strings = Storage(
        title_create = ADD_SECTION,
        title_display = T("Section Details"),
        title_list = LIST_SECTIONS,
        title_update = "",
        title_search = T("Search Sections"),
        subtitle_create = "",
        subtitle_list = T("Sections"),
        label_list_button = LIST_SECTIONS,
        label_create_button = ADD_SECTION,
        label_delete_button = T("Delete Section"),
        msg_record_created = T("Section updated"),
        msg_record_modified = T("Section updated"),
        msg_record_deleted = T("Section deleted"),
        msg_list_empty = T("No Sections currently registered"))

    # Options
    am_pm = {
        1:T("AM"),
        2:T("PM")
    }

    building_area_inspected = {
        1:T("Exterior and Interior"),
        2:T("Exterior Only")
    }

    atc20_construction_types = {
        1:T("Timber frame"), # Wood frame
        2:T("Steel frame"),
        3:T("Tilt-up concrete"),
        4:T("Concrete frame"),
        5:T("Concrete shear wall"),
        6:T("Unreinforced masonry"),
        7:T("Reinforced masonry"),
        8:T("RC frame with masonry infill"),
        99:T("Other")
    }
    
    atc20_primary_occupancy_opts = {
        1:T("Dwelling"),
        2:T("Other residential"),
        3:T("Public assembly"),
        4:T("School"),
        5:T("Religious"),
        6:T("Commercial/Offices"),
        7:T("Industrial"),
        8:T("Government"),
        9:T("Heritage Listed"), # Historic
        99:T("Other")
    }
    
    building_evaluation_condition = {
        1:T("Minor/None"),
        2:T("Moderate"),
        3:T("Severe")
    }

    building_estimated_damage = {
        1:T("None"),
        2:"0-1%",
        3:"1-10%",
        4:"10-30%",
        5:"30-60%",
        6:"60-100%",
        7:"100%"
    }

    building_posting_state = {
        1:T("INSPECTED (GREEN"),
        2:T("RESTRICTED USE (YELLOW)"),
        3:T("UNSAFE (RED")
    }

    # ATC-20 Rapid Evaluation Safety Assessment Form --------------------------
    resourcename = "atc20"
    tablename = "%s_%s" % (module, resourcename)

    table = db.define_table(tablename,
                            person_id(label=T("Inspector ID"), empty=False), # pre-populated in Controller
                            organisation_id(label=T("Territorial Authority")), # Affiliation in ATC20 terminology
                            Field("date", "date", default=request.now,
                                  label=T("Inspection date")),
                            Field("daytime", "integer", label=T("Inspection time"),
                                  requires=IS_EMPTY_OR(IS_IN_SET(am_pm)),
                                  represent=lambda opt: am_pm.get(opt, UNKNOWN_OPT)),
                            Field("area", "integer", label=T("Areas inspected"),
                                  requires=IS_IN_SET(building_area_inspected),
                                  represent=lambda opt: building_area_inspected.get(opt, UNKNOWN_OPT)),
                            migrate=migrate)

    # CRUD strings
    ADD_ASSESSMENT = T("Add ATC-20 Rapid Assessment")
    LIST_ASSESSMENTS = T("List ATC-20 Rapid Assessments")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ASSESSMENT,
        title_display = T("ATC-20 Rapid Assessment Details"),
        title_list = LIST_ASSESSMENTS,
        title_update = T("Edit ATC-20 Rapid Assessment"),
        title_search = T("Search ATC-20 Rapid Assessments"),
        subtitle_create = T("Add New ATC-20 Rapid Assessment"),
        subtitle_list = T("ATC-20 Rapid Assessments"),
        label_list_button = LIST_ASSESSMENTS,
        label_create_button = ADD_ASSESSMENT,
        label_delete_button = T("Delete ATC-20 Rapid Assessment"),
        msg_record_created = T("ATC-20 Rapid Assessment added"),
        msg_record_modified = T("ATC-20 Rapid Assessment updated"),
        msg_record_deleted = T("ATC-20 Rapid Assessment deleted"),
        msg_list_empty = T("No ATC-20 Rapid Assessments currently registered"))


    # -------------------------------------------------------------------------
    def atc20_onaccept(form):

        id = form.vars.get("id", None)

        if id:
            for x in ["description", "evaluation", "posting", "actions"]:
                section = "building_atc20_%s" % x
                set = db(db[section].atc20_id == id)
                record = set.select(db[section].id, limitby=(0, 1)).first()
                if not record:
                    db[section].insert(atc20_id=id)


    # -------------------------------------------------------------------------
    def atc20_represent(id):

        """ Represent assessment as string """

        table = db.building_atc20
        row = db(table.id == id).select(table.date,
                                        table.person_id,
                                        table.location_id,
                                        limitby = (0, 1)).first()

        if row:
            date = row.date and str(row.date) or ""
            location = row.location_id and shn_gis_location_represent(row.location_id) or ""
            person = row.person_id and vita.fullname(row.person_id) or ""

            assessment_represent = XML("<div>%s %s, %s %s</div>" % (location, person, date))

        else:
            assessment_represent = NONE

        return assessment_represent


    # -------------------------------------------------------------------------
    atc20_id = S3ReusableField("atc20_id", table,
                               requires = IS_NULL_OR(IS_ONE_OF(db, "building_atc20.id",
                                                               atc20_represent,
                                                               orderby="building_atc20.id")),
                               represent = lambda id: shn_atc20_represent(id),
                               label = T("ATC-20 Form"),
                               comment = A(ADD_ASSESSMENT,
                                           _class="colorbox",
                                           _href=URL(r=request, c="building", f="atc20",
                                                     args="create",
                                                     vars=dict(format="popup")),
                                           _target="top",
                                           _title=ADD_ASSESSMENT),
                               ondelete = "RESTRICT")

    s3xrc.model.configure(table,
                          listadd=False,    # We override this in the controller for when not a component
                          onaccept=lambda form: atc20_onaccept(form))

    # Section 2: Building Description -----------------------------------------
    resourcename = "atc20_description"
    tablename = "%s_%s" % (module, resourcename)

    table = db.define_table(tablename,
                            atc20_id(),
                            Field("name", label=T("Building Name")),
                            Field("name_short", label=T("Short Name")),
                            location_id(),
                            #Field("address", "text"), # inside location_id?
                            Field("contact_name", label=T("Contact name")),
                            Field("contact_phone", label=T("Contact phone")),
                            Field("stories_above", "integer", label=T("Storeys at and above ground level")), # Number of stories above ground
                            Field("stories_below", "integer", label=T("Below ground level")), # Number of stories below ground
                            Field("footprint", "integer", label=T("Total gross floor area (square meters)")),
                            Field("year_built", "integer", label=T("Year built")),
                            Field("residential_units", "integer", label=T("Number of residential units")),
                            Field("residential_units_not_habitable", "integer",
                                  label=T("Number of residential units not habitable")),
                            Field("construction_type", "integer", label=T("Type of Construction"),
                                  requires=IS_IN_SET(atc20_construction_types),
                                  represent=lambda opt: atc20_construction_types.get(opt, UNKNOWN_OPT)),
                            Field("construction_type_other", label="(%s)" % T("specify")),
                            Field("primary_occupancy", "integer", label=T("Primary Occupancy"),
                                  requires=IS_IN_SET(atc20_primary_occupancy_opts),
                                  represent=lambda opt: atc20_primary_occupancy_opts.get(opt, UNKNOWN_OPT)),
                            Field("primary_occupancy_other", label="(%s)" % T("specify")),
                            migrate=migrate)

    # CRUD strings
    s3.crud_strings[tablename] = section_crud_strings

    s3xrc.model.add_component(module, resourcename,
                              multiple = False,
                              joinby = dict(building_atc20="atc20_id"))

    s3xrc.model.configure(table, deletable=False)
    
    # Section 3: Evaluation--------------------------------------------------------
    resourcename = "atc20_evaluation"
    tablename = "%s_%s" % (module, resourcename)
    # @ToDo: Helptext in view

    table = db.define_table(tablename,
                            atc20_id(), # @ToDo: Represents for below
                            Field("estimated_damage", "integer",
                                  label=T("Estimated Overall Building Damage"),
                                  comment="(%s)" % T("Exclude contents"),
                                  requires=IS_IN_SET(building_estimated_damage),
                                  represent=lambda opt: building_estimated_damage.get(opt, UNKNOWN_OPT)),
                            Field("collapse", "integer",
                                  label=T("Collapse, partial collapse, off foundation"),
                                  requires=IS_IN_SET(building_evaluation_condition),
                                  represent=lambda opt: building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                            Field("leaning", "integer", label=T("Building or storey leaning"),
                                  requires=IS_IN_SET(building_evaluation_condition),
                                  represent=lambda opt: building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                            Field("structural", "integer",
                                  label=T("Wall or other structural damage"),
                                  requires=IS_IN_SET(building_evaluation_condition),
                                  represent=lambda opt: building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                            Field("falling", "integer",
                                  label=T("Overhead falling hazard"),
                                  requires=IS_IN_SET(building_evaluation_condition),
                                  represent=lambda opt: building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                            Field("slips", "integer",
                                  label=T("Ground movement, settlement, slips"),
                                  requires=IS_IN_SET(building_evaluation_condition),
                                  represent=lambda opt: building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                            Field("neighbour", "integer",
                                  label=T("Neighbouring building hazard"),
                                  requires=IS_IN_SET(building_evaluation_condition),
                                  represent=lambda opt: building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                            Field("other", "integer", label=T("Other"),
                                  requires=IS_IN_SET(building_evaluation_condition),
                                  represent=lambda opt: building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                            Field("other_details", label="(%s)" % T("specify")),
                            comments(),
                            migrate=migrate)

    # CRUD strings
    s3.crud_strings[tablename] = section_crud_strings

    s3xrc.model.add_component(module, resourcename,
                              multiple = False,
                              joinby = dict(building_atc20="atc20_id"))

    s3xrc.model.configure(table, deletable=False)
    
    # Section 3: Posting ------------------------------------------------------
    resourcename = "atc20_posting"
    tablename = "%s_%s" % (module, resourcename)
    # @ToDo: Helptext in view

    table = db.define_table(tablename,
                            atc20_id(),
                            Field("posting", "integer",
                                  requires=IS_IN_SET(building_posting_state),
                                  represent=lambda opt: building_posting_state.get(opt, UNKNOWN_OPT)),
                            Field("restrictions", "text", label=T("Record any restriction on use or entry")),
                            migrate=migrate
                            )
    # CRUD strings
    s3.crud_strings[tablename] = section_crud_strings

    s3xrc.model.add_component(module, resourcename,
                              multiple = False,
                              joinby = dict(building_atc20="atc20_id"))

    s3xrc.model.configure(table, deletable=False)
    
    # Section 3: Further actions ----------------------------------------------
    resourcename = "atc20_actions"
    tablename = "%s_%s" % (module, resourcename)
    # @ToDo: Helptext in view

    table = db.define_table(tablename,
                            atc20_id(),
                            Field("barricades", "boolean",
                                  label=T("Barricades are needed")),
                            Field("barricades_details", "text",
                                  label=T("(state location)")),
                            Field("detailed_evaluation", "boolean",
                                  label=T("Level 2 or detailed engineering evaluation recommended")),
                            # @ToDo: Hide these fields in JS until parent ticked
                            Field("structural", "boolean",
                                  label=T("Structural")),
                            Field("geotechnical", "boolean",
                                  label=T("Geotechnical")),
                            Field("other", "boolean", label=T("Other")),
                            Field("other_details", label="(%s)" % T("specify")),
                            Field("other_recommendations", "text",
                                  label=T("Other recommendations")),
                            comments(),
                            migrate=migrate
                            )

    # CRUD strings
    s3.crud_strings[tablename] = section_crud_strings

    s3xrc.model.add_component(module, resourcename,
                              multiple = False,
                              joinby = dict(building_atc20="atc20_id"))

    s3xrc.model.configure(table, deletable=False)
    
    