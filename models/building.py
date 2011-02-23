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
    
    This is actually based on the New Zealand variant:
    http://eden.sahanafoundation.org/wiki/BluePrintBuildingAssessments
    
    @ToDo: add other forms (ATC-38, ATC-45)
"""

module = "building"

if deployment_settings.has_module(module):

    # Options
    am_pm = {
        1:T("AM"),
        2:T("PM")
    }

    building_area_inspected = {
        1:T("Exterior and Interior"),
        2:T("Exterior Only")
    }

    building_construction_types = {
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
    
    building_primary_occupancy_opts = {
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
        1:"%s (%s)" % (T("Inspected"), T("Green")),
        2:"%s (%s)" % (T("Restricted Use"), T("Yellow")),
        3:"%s (%s)" % (T("Unsafe"), T("Red")),
    }

    # NZSEE Level 1 (~ATC-20 Rapid Evaluation) Safety Assessment Form ---------
    resourcename = "nzseel1"
    tablename = "%s_%s" % (module, resourcename)

    table = db.define_table(tablename,
                            person_id(label=T("Inspector ID"), empty=False), # pre-populated in Controller
                            organisation_id(label=T("Territorial Authority")), # Affiliation in ATC20 terminology
                            Field("date", "date", default=request.now,
                                  requires=IS_DATE(),
                                  label=T("Inspection date")),
                            Field("daytime", "integer", label=T("Inspection time"),
                                  requires=IS_IN_SET(am_pm),
                                  represent=lambda opt: am_pm.get(opt, UNKNOWN_OPT)),
                            Field("area", "integer", label=T("Areas inspected"),
                                  requires=IS_NULL_OR(IS_IN_SET(building_area_inspected)),
                                  represent=lambda opt: building_area_inspected.get(opt, UNKNOWN_OPT)),
                            #Field("name", label=T("Building Name"), requires=IS_NOT_EMPTY()), # Included in location_id
                            location_id(empty=False),
                            Field("name_short", label=T("Building Short Name")),
                            Field("contact_name", label=T("Contact Name"), requires=IS_NOT_EMPTY()),
                            Field("contact_phone", label=T("Contact Phone"), requires=IS_NOT_EMPTY()),
                            Field("stories_above", "integer", label=T("Storeys at and above ground level")), # Number of stories above ground
                            Field("stories_below", "integer", label=T("Below ground level")), # Number of stories below ground
                            Field("footprint", "integer", label=T("Total gross floor area (square meters)")),
                            Field("year_built", "integer", label=T("Year built")),
                            Field("residential_units", "integer", label=T("Number of residential units")),
                            #Field("residential_units_not_habitable", "integer",
                            #      label=T("Number of residential units not habitable")),
                            Field("photo", "boolean", label=T("Photo Taken?")),
                            Field("construction_type", "integer", label=T("Type of Construction"),
                                  requires=IS_NULL_OR(IS_IN_SET(building_construction_types)),
                                  represent=lambda opt: building_construction_types.get(opt, UNKNOWN_OPT)),
                            Field("construction_type_other", label="(%s)" % T("specify")),
                            Field("primary_occupancy", "integer", label=T("Primary Occupancy"),
                                  requires=IS_NULL_OR(IS_IN_SET(building_primary_occupancy_opts)),
                                  represent=lambda opt: building_primary_occupancy_opts.get(opt, UNKNOWN_OPT)),
                            Field("primary_occupancy_other", label="(%s)" % T("specify")),
                            Field("collapse", "integer",
                                  label=T("Collapse, partial collapse, off foundation"),
                                  requires=IS_NULL_OR(IS_IN_SET(building_evaluation_condition)),
                                  represent=lambda opt: building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                            Field("leaning", "integer", label=T("Building or storey leaning"),
                                  requires=IS_NULL_OR(IS_IN_SET(building_evaluation_condition)),
                                  represent=lambda opt: building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                            Field("structural", "integer",
                                  label=T("Wall or other structural damage"),
                                  requires=IS_NULL_OR(IS_IN_SET(building_evaluation_condition)),
                                  represent=lambda opt: building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                            Field("falling", "integer",
                                  label=T("Overhead falling hazard"),
                                  requires=IS_NULL_OR(IS_IN_SET(building_evaluation_condition)),
                                  represent=lambda opt: building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                            Field("slips", "integer",
                                  label=T("Ground movement, settlement, slips"),
                                  requires=IS_NULL_OR(IS_IN_SET(building_evaluation_condition)),
                                  represent=lambda opt: building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                            Field("neighbour", "integer",
                                  label=T("Neighbouring building hazard"),
                                  requires=IS_NULL_OR(IS_IN_SET(building_evaluation_condition)),
                                  represent=lambda opt: building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                            Field("other", "integer", label=T("Other"),
                                  requires=IS_NULL_OR(IS_IN_SET(building_evaluation_condition)),
                                  represent=lambda opt: building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                            Field("other_details", label="(%s)" % T("specify")),
                            Field("action_comments", "text", label=T("Comments")),
                            Field("posting", "integer",
                                  requires=IS_IN_SET(building_posting_state),
                                  represent=lambda opt: building_posting_state.get(opt, UNKNOWN_OPT)),
                            Field("restrictions", "text", label=T("Record any restriction on use or entry")),
                            #Field("posting_comments", "text", label=T("Comments")),
                            Field("barricades", "boolean",
                                  label=T("Barricades are needed")),
                            Field("barricades_details", "text",
                                  label=T("(state location)")),
                            Field("detailed_evaluation", "boolean",
                                  label=T("Level 2 or detailed engineering evaluation recommended")),
                            Field("detailed_structural", "boolean",
                                  label=T("Structural")),
                            Field("detailed_geotechnical", "boolean",
                                  label=T("Geotechnical")),
                            Field("detailed_other", "boolean", label=T("Other")),
                            Field("detailed_other_details", label="(%s)" % T("specify")),
                            Field("other_recommendations", "text",
                                  label=T("Other recommendations")),
                            Field("estimated_damage", "integer",
                                  label=T("Estimated Overall Building Damage"),
                                  comment="(%s)" % T("Exclude contents"),
                                  requires=IS_IN_SET(building_estimated_damage),
                                  represent=lambda opt: building_estimated_damage.get(opt, UNKNOWN_OPT)),
                            migrate=migrate, *s3_meta_fields())

    # CRUD strings
    ADD_ASSESSMENT = T("Add NZEE Level 1 Assessment")
    LIST_ASSESSMENTS = T("List NZEE Level 1 Assessments")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ASSESSMENT,
        title_display = T("NZEE Level 1 Assessment Details"),
        title_list = LIST_ASSESSMENTS,
        title_update = T("Edit NZEE Level 1 Assessment"),
        title_search = T("Search NZEE Level 1 Assessments"),
        subtitle_create = T("Add New NZEE Level 1 Assessment"),
        subtitle_list = T("NZEE Level 1 Assessments"),
        label_list_button = LIST_ASSESSMENTS,
        label_create_button = ADD_ASSESSMENT,
        label_delete_button = T("Delete NZEE Level 1 Assessment"),
        msg_record_created = T("NZEE Level 1 Assessment added"),
        msg_record_modified = T("NZEE Level 1 Assessment updated"),
        msg_record_deleted = T("NZEE Level 1 Assessment deleted"),
        msg_list_empty = T("No NZEE Level 1 Assessments currently registered"))
    # -------------------------------------------------------------------------