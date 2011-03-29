# -*- coding: utf-8 -*-

""" Assessments - Controller

    @author: Fran Boon
    @author: Dominic König
    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-25

"""

prefix = request.controller
resourcename = request.function

if prefix not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
def shn_menu():
    menu = [
        [T("Rapid Assessments"), False, aURL(r=request, f="rat"), [
            [T("List"), False, aURL(r=request, f="rat")],
            [T("Add"), False, aURL(p="create", r=request, f="rat", args="create")],
            #[T("Search"), False, URL(r=request, f="rat", args="search")],
        ]],
        [T("Impact Assessments"), False, aURL(r=request, f="assess"), [
            [T("List"), False, aURL(r=request, f="assess")],
            #[T("Add"), False, aURL(p="create", r=request, f="assess", args="create")],
            [T("Add"), False, aURL(r=request, f="basic_assess")],
            [T("Mobile"), False, aURL(r=request, f="mobile_basic_assess")],
            #[T("Search"), False, aURL(r=request, f="assess", args="search")],
        ]],
    ]
    if s3_has_role(1):
        menu_editor = [
            [T("Edit Options"), False, URL(r=request, f="#"), [
                [T("List / Add Baseline Types"), False, URL(r=request, f="baseline_type")],
                [T("List / Add Impact Types"), False, URL(r=request, f="impact_type")],
            ]],
        ]
        menu.extend(menu_editor)
    response.menu_options = menu

shn_menu()

#==============================================================================
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[prefix].name_nice
    response.title = module_name
    return dict(module_name=module_name)


# -----------------------------------------------------------------------------
def maps():

    """ Show a Map of all Rapid Assessments """

    reports = db(db.gis_location.id == db.assess_rat.location_id).select()
    report_popup_url = URL(r=request, f="rat",
                           args="read.popup?rat.location_id=")
    map = gis.show_map(feature_queries = [{"name":T("Rapid Assessments"),
                                           "query":reports,
                                           "active":True,
                                           "popup_url": report_popup_url}],
                       window=True)

    return dict(map=map)


# -----------------------------------------------------------------------------
def rat():

    """ Rapid Assessments, RESTful controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    # Don't send the locations list to client (pulled by AJAX instead)
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db,
                                                            "gis_location.id"))

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
    s3xrc.model.configure(db.assess_section2,
        subheadings = {
            T("Population and number of households"): "population_total",
            T("Fatalities"): "dead_women",
            T("Casualties"): "injured_women",
            T("Missing Persons"): "missing_women",
            T("General information on demographics"): "household_head_elderly",
            T("Comments"): "comments"})
    s3xrc.model.configure(db.assess_section3,
        subheadings = {
            T("Access to Shelter"): "houses_total",
            T("Water storage containers in households"): "water_containers_available",
            T("Other non-food items"): "cooking_equipment_available",
            T("Shelter/NFI Assistance"): "nfi_assistance_available",
            T("Comments"): "comments"})
    s3xrc.model.configure(db.assess_section4,
        subheadings = {
            T("Water supply"): "water_source_pre_disaster_type",
            T("Water collection"): "water_coll_time",
            T("Places for defecation"): "defec_place_type",
            T("Environment"): "close_industry",
            T("Latrines"): "latrines_number",
            T("Comments"): "comments"})
    s3xrc.model.configure(db.assess_section5,
        subheadings = {
            T("Health services status"): "health_services_pre_disaster",
            T("Current health problems"): "health_problems_adults",
            T("Nutrition problems"): "malnutrition_present_pre_disaster",
            T("Comments"): "comments"})
    s3xrc.model.configure(db.assess_section6,
        subheadings = {
            T("Existing food stocks"): "food_stocks_main_dishes",
            T("food_sources") : "Food sources",
            T("Food assistance"): "food_assistance_available",
            T("Comments"): "comments"})
    s3xrc.model.configure(db.assess_section7,
        subheadings = {
            "%s / %s" % (T("Sources of income"), T("Major expenses")): "income_sources_pre_disaster",
            T("business_damaged"): "Access to cash",
            T("Current community priorities"): "rank_reconstruction_assistance",
            T("Comments"): "comments"})
    s3xrc.model.configure(db.assess_section8,
        subheadings = {
            T("Access to education services"): "schools_total",
            T("Alternative places for studying"): "alternative_study_places_available",
            T("School activities"): "schools_open_pre_disaster",
            T("School attendance"): "children_0612_female",
            T("School assistance"): "school_assistance_available",
            T("Comments"): "comments"})
    s3xrc.model.configure(db.assess_section9,
        subheadings = {
            T("Physical Safety"): "vulnerable_groups_safe_env",
            T("Separated children, caregiving arrangements"): "children_separated",
            T("Persons in institutions"): "children_in_disabled_homes",
            T("Activities of children"): "child_activities_u12f_pre_disaster",
            T("Coping Activities"): "coping_activities_elderly",
            T("Current general needs"): "current_general_needs",
            T("Comments"): "comments"})

    # @ToDo  Generalize this and make it available as a function that other
    # component prep methods can call to set the default for a join field.
    def prep(r):
        if r.representation=="html" and r.http=="GET" and r.method=="create":
            # If this assessment is being created as a component of a shelter,
            # it will have the shelter id in its vars.
            shelter_id = r.request.get_vars.get("rat.shelter_id", None)
            if shelter_id:
                try:
                    shelter_id = int(shelter_id)
                except ValueError:
                    pass
                else:
                    db.assess_rat.shelter_id.default = shelter_id
            # If this assessment is being created as a component of a document,
            # it will have the document id in its vars.
            document_id = r.request.get_vars.get("rat.document_id", None)
            if document_id:
                try:
                    document_id = int(document_id)
                except ValueError:
                    pass
                else:
                    db.assess_rat.document_id.default = document_id
        return True
    response.s3.prep = prep

    # Post-processor
    def postp(r, output):
        shn_action_buttons(r, deletable=False)
        # Redirect to read/edit view rather than list view
        if r.representation == "html" and r.method == "create":
            r.next = r.other(method="",
                             record_id=s3xrc.get_session("assess", "rat"))
        return output
    response.s3.postp = postp

    # Over-ride the listadd since we're not a component here
    s3xrc.model.configure(table, create_next="", listadd=True)

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
def shn_rat_rheader(r, tabs=[]):

    """ Resource Headers """

    if r.representation == "html":
        if r.name == "rat":
            report = r.record
            if report:
                rheader_tabs = s3_rheader_tabs(r, tabs, paging=True)
                location = report.location_id
                if location:
                    location = shn_gis_location_represent(location)
                staff = report.staff_id
                if staff:
                    query = (db.org_staff.id == staff)
                    organisation_id = db(query).select(db.org_staff.organisation_id).first().organisation_id
                    organisation = shn_organisation_represent(organisation_id)
                else:
                    organisation = None
                staff = report.staff2_id
                if staff:
                    query = (db.org_staff.id == staff)
                    organisation_id = db(query).select(db.org_staff.organisation_id).first().organisation_id
                    organisation2 = shn_organisation_represent(organisation_id)
                else:
                    organisation2 = None
                if organisation2:
                    orgs = organisation + ", " + organisation2
                else:
                    orgs = organisation
                doc_name = doc_url = None
                query = (db.doc_document.id == report.document_id)
                document = db(query).select(db.doc_document.name,
                                            db.doc_document.file,
                                            limitby=(0, 1)).first()
                if document:
                    doc_name = document.name
                    doc_url = URL(r=request, c="default", f="download",
                                  args=[document.file])
                rheader = DIV(TABLE(
                                TR(
                                    TH("%s: " % T("Location")), location,
                                    TH(": " % T("Date")), report.date
                                  ),
                                TR(
                                    TH(": " % T("Organizations")), orgs,
                                    TH(": " % T("Document")), A(doc_name,
                                                                _href=doc_url)
                                  )
                                ),
                              rheader_tabs)

                return rheader
    return None

#==============================================================================
# Flexible Impact Assessments
#==============================================================================
def shn_assess_rheader(r, tabs=[]):
    """ Resource Headers for Flexible Impact Assessments """

    if r.representation == "html":

        rheader_tabs = s3_rheader_tabs(r, tabs)

        assess = r.record

        if assess:
            rheader = DIV(TABLE(TR(
                                   TH("%s: " % T("Date & Time")),
                                   assess.datetime,
                                   TH("%s: " % T("Location")),
                                   shn_gis_location_represent(assess.location_id),
                                   TH("%s: " % T("Assessor")),
                                   shn_pr_person_represent(assess.assessor_person_id),
                                  ),
                               ),
                          rheader_tabs
                         )
            return rheader

    return None

# -----------------------------------------------------------------------------
def assess():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    # Pre-processor
    def shn_assess_prep(r):
        if session.s3.mobile and r.method == "create" and r.representation in shn_interactive_view_formats:
            # redirect to mobile-specific form:
            redirect(URL(r=request, f="assess_short_mobile"))
        return True
    response.s3.prep = shn_assess_prep

    table.incident_id.comment = DIV(_class="tooltip",
                                    _title="%s|%s" % (T("Incident"),
                                                      T("Optional link to an Incident which this Assessment was triggered by.")))

    tabs = [
            (T("Edit Details"), None),
            (T("Baselines"), "baseline"),
            (T("Impacts"), "impact"),
            (T("Summary"), "summary"),
            #(T("Requested"), "ritem"),
           ]

    rheader = lambda r: shn_assess_rheader(r, tabs)

    return s3_rest_controller(prefix, resourcename, rheader=rheader)

# -----------------------------------------------------------------------------
def impact_type():
    """ RESTful CRUD controller """

    prefix = "impact"
    resourcename = "type"

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    return s3_rest_controller(prefix, resourcename)

# -----------------------------------------------------------------------------
def baseline_type():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    return s3_rest_controller(prefix, resourcename)

# -----------------------------------------------------------------------------
def baseline():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    return s3_rest_controller(prefix, resourcename)

# -----------------------------------------------------------------------------
def summary():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    return s3_rest_controller(prefix, resourcename)

#==============================================================================
def basic_assess():
    """ Custom page to hide the complexity of the Assessments/Impacts/Summary model: PC Browser version """

    if not auth.is_logged_in():
        session.error = T("Need to be logged-in to be able to submit assessments")
        redirect(URL(r=request, c="default", f="user", args=["login"]))

    # See if we've been created from an Incident
    ireport_id = request.vars.get("ireport_id")
    if ireport_id:
        # Location is the same as the calling Incident
        irs_location_id = shn_get_db_field_value(db = db,
                                                 table = "irs_ireport",
                                                 field = "location_id",
                                                 look_up = ireport_id
                                                )
        location = shn_gis_location_represent(irs_location_id)
        custom_assess_fields = (
                                ("impact", 1),
                                ("impact", 2),
                                ("impact", 3),
                                ("impact", 4),
                                ("impact", 5),
                                ("impact", 6),
                                ("impact", 7),
                                ("assess", "comments"),
                            )
        form, form_accepted, assess_id = custom_assess(custom_assess_fields,
                                                       location_id=irs_location_id)
    else:
        location = None
        custom_assess_fields = (
                                ("assess", "location_id", "selector"),
                                ("impact", 1),
                                ("impact", 2),
                                ("impact", 3),
                                ("impact", 4),
                                ("impact", 5),
                                ("impact", 6),
                                ("impact", 7),
                                ("assess", "comments"),
                            )
        form, form_accepted, assess_id = custom_assess(custom_assess_fields)

    if form_accepted:
        session.confirmation = T("Basic Assessment Reported")
        redirect(URL(r=request, f="assess", args=[assess_id, "impact"]))

    return dict(title = T("Basic Assessment"),
                location = location,
                form = form)

# -----------------------------------------------------------------------------
def mobile_basic_assess():
    """ Custom page to hide the complexity of the Assessments/Impacts/Summary model: Mobile device version """

    if not auth.is_logged_in():
        redirect(URL(r=request, c="default", f="index"))

    custom_assess_fields = (
                            ("assess", "location_id", "auto"),
                            ("impact", 1),
                            ("impact", 2),
                            ("impact", 3),
                            ("impact", 4),
                            ("impact", 5),
                            ("impact", 6),
                            ("impact", 7),
                            ("assess", "comments"),
                        )

    form, form_accepted, assess_id = custom_assess(custom_assess_fields)

    if form_accepted:
        form = FORM(H1(T("Sahana Eden")),
                    H2(T("Short Assessment")),
                    P(T("Assessment Reported")),
                    A(T("Report Another Assessment..."),
                      _href = URL(r=request)
                      ),
                    _class = "mobile",
                    )

    return dict(form = form)

# -----------------------------------------------------------------------------
def color_code_severity_widget(widget, name):
    """ Utility function to colour-code Severity options """

    for option, color in zip(widget, ["green", "yellow", "orange", "red"]):
        option[0].__setitem__("_style", "background-color:%s;" % color)
        option[0][0].__setitem__("_name", name)

    return widget

# -----------------------------------------------------------------------------
def custom_assess(custom_assess_fields, location_id=None):
    """ Build a custom page to hide the complexity of the Assessments/Impacts/Summary model """

    form_rows = []
    comment = ""
    for field in custom_assess_fields:
        name = "custom_%s_%s" % (field[0], field[1])
        if field[0] == "assess":
            if field[1] == "comments":
                label = "%s:" % db.assess_assess[ field[1] ].label
                #widget = db.assess_assess[ field[1] ].widget
                widget = TEXTAREA(_name = name,
                                  _class = "double",
                                  _type = "text")

            elif field[1] == "location_id":
                if field[2] == "auto":
                    # HTML5 Geolocate
                    label = "%s:" % T("Location")
                    #widget = db.assess_assess[ field[1] ].widget
                    widget = DIV(INPUT(_name = name,
                                       _type = "text"),
                             INPUT(_name = "gis_location_lat",
                                   _id = "gis_location_lat",
                                   _type = "text"),
                             INPUT(_name = "gis_location_lon",
                                   _id = "gis_location_lon",
                                   _type = "text"))
                else:
                    # Locaton Selector
                    label = "%s:" % T("Location")
                    #widget = SELECT(_id = name,
                    #                _class = "reference gis_location",
                    #                _name = "location_id")
                    #response.s3.gis.location_id = "custom_assess_location_id"
                    widget = db.assess_assess.location_id.widget(field=db.assess_assess.location_id,
                                                                 value="")

        elif field[0] == "baseline":
            label = shn_get_db_field_value(db = db,
                                           table = "assess_baseline_type",
                                           field = "name",
                                           look_up = field[1]
                                           )
            label = T(label)
            widget = INPUT(_name = name,
                           _class = "double",
                           _type = "text")

        elif field[0] == "impact":
            label = "%s:" % T(shn_get_db_field_value(db = db,
                                                   table = "impact_type",
                                                   field = "name",
                                                   look_up = field[1]
                                                   ))
            value_widget = INPUT(_name = name,
                                 _class = "double",
                                 _type = "text")
            severity_widget = db.assess_summary.value.widget(db.impact_impact.severity,
                                                             0,
                                                             _name = "%s_severity" % name
                                                            )
            severity_widget = color_code_severity_widget(severity_widget,
                                                         "%s_severity" % name)

            widget = DIV(value_widget,
                         DIV("%s:" % T("Severity")),
                         severity_widget,
                         XML("&nbsp"))

        elif field[0] == "summary":
            label = "%s:" % T(shn_org_cluster_subsector_represent( field[1] ))
            widget = db.assess_summary.value.widget(db.assess_summary.value,
                                                    0,
                                                    _name = name
                                                   )
            widget = color_code_severity_widget(widget)

        # Add the field components to the form_rows
        if field[0] == "title":
            form_rows.append(TR(H3( field[1] )))
        else:
            form_rows = form_rows + list(s3_formstyle("%s__row" % name,
                                         label,
                                         widget,
                                         comment))

    form = FORM(TABLE(*form_rows),
                INPUT(_value = T("Save"),
                      _type = "submit"),
               )
    assess_id = None

    form_accepted = form.accepts(request.vars, session)
    if form_accepted:
        record_dict = {"organisation_id" : session.s3.organisation_id}

        for field in custom_assess_fields:
            if field[0] != "assess" or field[1] == "location":
                continue
            name = "custom__assess_%s" % field[1]
            if name in request.vars:
                record_dict[field[1]] = request.vars[name]

        # Add Location (must happen first)
        if "custom_assess_location_id" in request.vars:
            # Auto
            location_dict = {}
            if "gis_location_lat" in request.vars:
                location_dict["lat"] = request.vars["gis_location_lat"]
            if "gis_location_lon" in request.vars:
                location_dict["lon"] = request.vars["gis_location_lon"]
            location_dict["name"] = request.vars["custom_assess_location_id"]
            record_dict["location_id"] = db.gis_location.insert(**location_dict)

        if "location_id" in request.vars:
            # Location Selector
            record_dict["location_id"] = request.vars["location_id"]

        if location_id:
            # Location_id was passed to function
            record_dict["location_id"] = location_id

        # Add Assessment
        assess_id = db.assess_assess.insert(**record_dict)

        fk_dict = dict(baseline = "baseline_type_id",
                       impact = "impact_type_id",
                       summary = "cluster_subsector_id"
                      )

        component_dict = dict(baseline = "assess_baseline",
                              impact = "impact_impact",
                              summary = "assess_summary"
                            )

        # Add Assessment Components
        cluster_summary = {}
        for field in custom_assess_fields:
            if field[0] == "assess":
                continue
            record_dict = {}
            name = "custom_%s_%s" % (field[0], field[1])
            if name in request.vars:
                record_dict["assess_id"] = assess_id
                record_dict[fk_dict[ field[0] ] ] = field[1]
                record_dict["value"] = request.vars[name]

                if field[0] == "impact":
                    severity = int(request.vars[name + "_severity"])
                    record_dict["severity"] = severity

                    if not record_dict["value"] and not record_dict["severity"]:
                        # Do not record impact if there is no data for it.
                        # Should we still average severity though? Now not doing this
                        continue

                    # Record the Severity per cluster
                    cluster_id = \
                        shn_get_db_field_value(db = db,
                                               table = "impact_type",
                                               field = "cluster_id",
                                               look_up = field[1])
                    if cluster_id in cluster_summary.keys():
                        cluster_summary[cluster_id].append(severity)
                    elif cluster_id:
                        cluster_summary[cluster_id] = [severity]

                db[component_dict[ field[0] ] ].insert(**record_dict)

        # Add Cluster summaries
        # @ToDo: make sure that this doesn't happen if there are clusters in the assess
        for cluster_id in cluster_summary.keys():
            severity_values = cluster_summary[cluster_id]
            db.assess_summary.insert(assess_id = assess_id,
                                     cluster_id = cluster_id,
                                     # Average severity
                                     value = sum(severity_values) / len(severity_values)
                                     )

        # Send Out Notification SMS
        #message = "Sahana: " + T("New Assessment reported from") + " %s by %s %s" % ( location_dict["name"],
        #                                                         session.auth.user.first_name,
        #                                                         session.auth.user.last_name
        #                                                         )
        # Hard coded notification message for Demo
        #msg.send_by_pe_id(    3,
        #                      subject="",
        #                      message=message,
        #                      sender_pe_id = None,
        #                      pr_message_method = 2,
        #                      sender="",
        #                      fromaddress="")

    return form, form_accepted, assess_id

#==============================================================================
