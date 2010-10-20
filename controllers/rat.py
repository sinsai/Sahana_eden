# -*- coding: utf-8 -*-

""" Rapid Assessment Tool - Controllers

    @author: Fran Boon
    @author: Dominic König

    @see: http://eden.sahanafoundation.org/wiki/Pakistan
    @todo: Rename as 'assessment' (Deprioritised due to Data
        Migration issues being distracting for us currently)

"""

prefix = request.controller
resourcename = request.function

if prefix not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# -----------------------------------------------------------------------------
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Assessments"), False, URL(r=request, f="assessment"),[
       [T("List"), False, URL(r=request, f="assessment")],
       [T("Add"), False, URL(r=request, f="assessment", args="create")],
       #[T("Search"), False, URL(r=request, f="assessment", args="search")],
    ]],
    #[T("Summary"), False, URL(r=request, f="assessment", args="summary")],
    #[T("Map"), False, URL(r=request, f="maps")],
]


# -----------------------------------------------------------------------------
def index():

    """ Module Homepage """

    module_name = deployment_settings.modules[prefix].name_nice
    return dict(module_name=module_name)


# -----------------------------------------------------------------------------
def maps():

    """ Show a Map of all Assessments """

    freports = db(db.gis_location.id == db.rat_freport.location_id).select()
    freport_popup_url = URL(r=request, f="freport", args="read.popup?freport.location_id=")
    map = gis.show_map(feature_queries = [{"name":T("Flood Reports"), "query":freports, "active":True, "popup_url": freport_popup_url}], window=True)

    return dict(map=map)


# -----------------------------------------------------------------------------
def assessment():

    """ Rapid Assessments, RESTful controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    # Don't send the locations list to client (pulled by AJAX instead)
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

    # Villages only
    #table.location_id.requires = IS_NULL_OR(IS_ONE_OF(db(db.gis_location.level == "L5"),
    #                                                  "gis_location.id",
    #                                                  repr_select, sort=True))

    # Pre-populate staff ID
    if auth.is_logged_in():
        staff_id = db((db.pr_person.uuid == session.auth.user.person_uuid) & \
                      (db.org_staff.person_id == db.pr_person.id)).select(
                       db.org_staff.id, limitby=(0, 1)).first()
        if staff_id:
            table.staff_id.default = staff_id.id

    # Subheadings in forms:
    s3xrc.model.configure(db.rat_section2,
        subheadings = {
            "Population and number of households": "population_total",
            "Fatalities": "dead_women",
            "Casualties": "injured_women",
            "Missing Persons": "missing_women",
            "General information on demographics": "household_head_elderly",
            "Comments": "comments"})
    s3xrc.model.configure(db.rat_section3,
        subheadings = {
            "Access to Shelter": "houses_total",
            "Water storage containers in households": "water_containers_available",
            "Other non-food items": "cooking_equipment_available",
            "Shelter/NFI Assistance": "nfi_assistance_available",
            "Comments": "comments"})
    s3xrc.model.configure(db.rat_section4,
        subheadings = {
            "Water supply": "water_source_pre_disaster_type",
            "Water collection": "water_coll_time",
            "Places for defecation": "defec_place_type",
            "Environment": "close_industry",
            "Latrines": "latrines_number",
            "Comments": "comments"})
    s3xrc.model.configure(db.rat_section5,
        subheadings = {
            "Health services status": "health_services_pre_disaster",
            "Current health problems": "health_problems_adults",
            "Nutrition problems": "malnutrition_present_pre_disaster",
            "Comments": "comments"})
    s3xrc.model.configure(db.rat_section6,
        subheadings = {
            "Existing food stocks": "food_stocks_main_dishes",
            "food_sources" : "Food sources",
            "Food assistance": "food_assistance_available",
            "Comments": "comments"})
    s3xrc.model.configure(db.rat_section7,
        subheadings = {
            "Sources of income / Major expenses": "income_sources_pre_disaster",
            "business_damaged" : "Access to cash",
            "Current community priorities": "rank_reconstruction_assistance",
            "Comments": "comments"})
    s3xrc.model.configure(db.rat_section8,
        subheadings = {
            "Access to education services": "schools_total",
            "Alternative places for studying": "alternative_study_places_available",
            "School activities": "schools_open_pre_disaster",
            "School attendance": "children_0612_female",
            "School assistance": "school_assistance_available",
            "Comments": "comments"})
    s3xrc.model.configure(db.rat_section9,
        subheadings = {
            "Physical Safety": "vulnerable_groups_safe_env",
            "Separated children, caregiving arrangements": "children_separated",
            "Persons in institutions": "children_in_disabled_homes",
            "Activities of children": "child_activities_u12f_pre_disaster",
            "Coping Activities": "coping_activities_elderly",
            "Current general needs": "current_general_needs",
            "Comments": "comments"})

    # @ToDo  Generalize this and make it available as a function that other
    # component prep methods can call to set the default for a join field.
    def prep(r):
        if r.representation=="html" and r.http=="GET" and r.method=="create":
            # If this assessment is being created as a component of a shelter,
            # it will have the shelter id in its vars.
            shelter_id = r.request.get_vars.get("assessment.shelter_id", None)
            if shelter_id:
                try:
                    shelter_id = int(shelter_id)
                except ValueError:
                    pass
                else:
                    db.rat_assessment.shelter_id.default = shelter_id
            # If this assessment is being created as a component of a document,
            # it will have the document id in its vars.
            document_id = r.request.get_vars.get("assessment.document_id", None)
            if document_id:
                try:
                    document_id = int(document_id)
                except ValueError:
                    pass
                else:
                    db.rat_assessment.document_id.default = document_id
        return True
    response.s3.prep = prep

    # Post-processor
    def postp(r, output):
        shn_action_buttons(r, deletable=False)
        # Redirect to read/edit view rather than list view
        if r.representation == "html" and r.method == "create":
            r.next = r.other(method="",
                             record_id=s3xrc.get_session("rat", "assessment"))
        return output
    response.s3.postp = postp

    s3xrc.model.configure(table, create_next="", listadd=False)

    rheader = lambda r: shn_rat_rheader(r,
                                        tabs = [(T("Identification"), None),
                                                (T("Demographic"), "section2"),
                                                (T("Shelter & Essential NFIs"), "section3"),
                                                (T("WatSan"), "section4"),
                                                (T("Health"), "section5"),
                                                (T("Nutrition"), "section6"),
                                                (T("Livelihood"), "section7"),
                                                (T("Education"), "section8"),
                                                (T("Protection"), "section9") ])

    output = s3_rest_controller(prefix, resourcename, rheader=rheader)

    response.extra_styles = ["S3/rat.css"]
    return output


# -----------------------------------------------------------------------------
def download():

    """ Download a file """

    return response.download(request, db)


# -----------------------------------------------------------------------------
def shn_rat_rheader(r, tabs=[]):

    """ Resource Headers """

    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, tabs, paging=True)

        if r.name == "assessment":

            report = r.record
            location = report.location_id
            if location:
                location = shn_gis_location_represent(location)
            staff = report.staff_id
            if staff:
                organisation_id = db(db.org_staff.id == staff).select(db.org_staff.organisation_id).first().organisation_id
                organisation = shn_organisation_represent(organisation_id)
            else:
                organisation = None
            staff = report.staff2_id
            if staff:
                organisation_id = db(db.org_staff.id == staff).select(db.org_staff.organisation_id).first().organisation_id
                organisation2 = shn_organisation_represent(organisation_id)
            else:
                organisation2 = None
            if organisation2:
                orgs = organisation + ", " + organisation2
            else:
                orgs = organisation
            doc_name = doc_url = None
            document = db(db.doc_document.id == report.document_id).select(db.doc_document.name, db.doc_document.file, limitby=(0, 1)).first()
            if document:
                doc_name = document.name
                doc_url = URL(r=request, f="download", args=[document.file])
            rheader = DIV(TABLE(
                            TR(
                                TH(T("Location") + ": "), location,
                                TH(T("Date") + ": "), report.date
                              ),
                            TR(
                                TH(T("Organizations") + ": "), orgs,
                                TH(T("Document") + ": "), A(doc_name, _href=doc_url)
                              )
                            ),
                          rheader_tabs)

            return rheader

        else:
            return None

# -----------------------------------------------------------------------------
