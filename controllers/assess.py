# -*- coding: utf-8 -*-

""" Assessment - Controller

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
        [T("Assessments"), False, URL(r=request, f="assess"), [
            [T("List"), False, URL(r=request, f="assess")],
            [T("Add"), False, URL(r=request, f="assess", args="create")],
            [T("Mobile"), False, URL(r=request, f="assess_short_mobile")],
            #[T("Search"), False, URL(r=request, f="assess", args="search")],
        ]],
        [T("Baselines"), False, URL(r=request, f="baseline"), [
            [T("List"), False, URL(r=request, f="baseline")],
            [T("Add"), False, URL(r=request, f="baseline", args="create")],
            #[T("Search"), False, URL(r=request, f="baseline", args="search")],
        ]],
        [T("Summary"), False, URL(r=request, f="summary"), [
            [T("List"), False, URL(r=request, f="summary")],
            [T("Add"), False, URL(r=request, f="summary", args="create")],
            #[T("Search"), False, URL(r=request, f="summary", args="search")],
        ]],
    ]
    if shn_has_role(1):
        menu_editor = [
            [T("Edit Options"), False, URL(r=request, f="#"), [
                [T("List / Add Baseline Types"), False, URL(r=request, f="baseline_type")],
            ]],
        ]
        menu.extend(menu_editor)
    response.menu_options = menu

shn_menu()

#==============================================================================
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[prefix].name_nice

    return dict(module_name=module_name)


#==============================================================================
def shn_assess_rheader(jr, tabs=[]):

    """ @todo: fix docstring """

    if jr.representation == "html":
        rheader_tabs = shn_rheader_tabs(jr, tabs)
        assess = jr.record
        rheader = DIV(TABLE(TR(
                               TH(T("Date & Time") + ": "), assess.datetime,
                               TH(T("Location") + ": "), shn_gis_location_represent(assess.location_id),
                               TH(T("Assessor") + ": "), shn_pr_person_represent(assess.assessor_person_id),
                              ),
                           ),
                      rheader_tabs
                     )
        return rheader
    return None


#==============================================================================
def assess():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    tabs = [
            (T("Edit Details"), None),
            (T("Impacts"), "impact"),
            (T("Baselines"), "baseline"),
            (T("Summary"), "summary"),
            #(T("Requested"), "ritem"),
           ]

    rheader = lambda r: shn_assess_rheader(r, tabs)

    return s3_rest_controller(prefix, resourcename, rheader=rheader)


#==============================================================================
def baseline_type():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    return s3_rest_controller(prefix, resourcename)


#==============================================================================
def baseline():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    return s3_rest_controller(prefix, resourcename)


#==============================================================================
def summary():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    return s3_rest_controller(prefix, resourcename)


#==============================================================================
def assess_short_mobile():

    """ @todo: fix docstring """

    assess_short_fields = (("assess", "location"),
                           ("baseline", 1),
                           ("baseline", 2),
                           ("baseline", 4),
                           ("baseline", 3),
                           ("impact", 3),
                           ("impact", 4),
                           ("title", "Cluster Indicators:"),
                           ("summary", 4),
                           ("summary", 3),
                           ("summary", 10),
                           ("summary", 11),
                           ("summary", 9),
                           ("assess", "comments"),
                           )
    form_row = []
    comment = ""
    for field in assess_short_fields:
        name = "assess_short_%s_%s" % (field[0], field[1])
        id = name
        if field[0] == "assess":
            if field[1] == "comments":
                label = "%s:" % db.assess_assess[ field[1] ].label
                #widget = db.assess_assess[ field[1] ].widget
                widget = TEXTAREA(_name = id,
                                  _class = "double",
                                  _type = "text")
            if field[1] == "location":
                label = "Location:"
                #widget = db.assess_assess[ field[1] ].widget
                widget = DIV(INPUT(_name = id,
                               _type = "text"),
                         INPUT(_name = "gis_location_lat",
                               _id = "gis_location_lat",
                               _type = "text"),
                         INPUT(_name = "gis_location_lon",
                               _id = "gis_location_lon",
                               _type = "text"))
        elif field[0] == "baseline":
            label = shn_get_db_field_value(db = db,
                                           table = "assess_baseline_type",
                                           field = "name",
                                           look_up = field[1]
                                           )
            widget = INPUT(_name = id,
                           _class = "double",
                           _type = "text")
        elif field[0] == "impact":
            label = "%s:" % shn_get_db_field_value(db = db,
                                                   table = "impact_type",
                                                   field = "name",
                                                   look_up = field[1]
                                                   )
            widget = INPUT(_name = id,
                           _class = "double",
                           _type = "text")
        elif field[0] == "summary":
            label = "%s:" % shn_cluster_subsector_represent( field[1] )
            widget = db.assess_summary.value.widget(db.assess_summary.value,
                                                       0,
                                                       _name = name
                                                       )
            for option, color in zip(widget, ["green", "yellow", "orange", "red"]):
                option[0].__setitem__("_style", "background-color:%s;" % color)
                option[0][0].__setitem__("_name", name)



        if field[0] == "title":
            form_row.append(TR(H3( field[1] )))
        else:
            form_row = form_row + list( s3_formstyle(id, label, widget, comment) )

    form = FORM(H1("Sahana Eden"),
                H2("Short Assessment"),
                TABLE(*form_row),
                INPUT(_value = T("Save"),
                      _type = "submit"
                      ),
                _class = "mobile",
                )

    if auth.is_logged_in():
        if form.accepts(request.vars, session):
            record_dict = {}

            #Add Assess (must happen first)
            for field in assess_short_fields:
                if field[0] != "assess" or field[1] == "location":
                    continue
                name = "assess_short_assess_%s" % field[1]
                if name in request.vars:
                    record_dict[field[1]] = request.vars[name]
            if "assess_short_assess_location" in request.vars:
                location_dict = {}
                location_dict["name"] = request.vars["assess_short_assess_location"]
                if "gis_location_lat" in request.vars:
                    location_dict["lat"] = request.vars["gis_location_lat"]
                if "gis_location_lon" in request.vars:
                    location_dict["lon"] = request.vars["gis_location_lon"]
                location_id = db.gis_location.insert(**location_dict)
                record_dict["location_id"] = location_id
            asssess_id = db.assess_assess.insert(**record_dict)

            fk_dict = dict(baseline = "baseline_type_id",
                           impact = "impact_type_id",
                           summary = "cluster_subsector_id"
                           )

            component_dict = dict(baseline = "assess_baseline",
                           impact = "impact_impact",
                           summary = "assess_summary"
                           )

            #Add Assess Components
            for field in assess_short_fields:
                if field[0] == "assess":
                    continue
                record_dict = {}
                name = "assess_short_%s_%s" % (field[0], field[1])
                if name in request.vars:
                    record_dict["assess_id"] = asssess_id
                    record_dict[fk_dict[ field[0] ] ] = field[1]
                    record_dict["value"] = request.vars[name]
                    db[component_dict[ field[0] ] ].insert(**record_dict)

            #Send Out Notification SMS (to Taipida)
            message = "Sahana: New Assessment reported from %s by %s %s" % ( location_dict["name"],
                                                                     session.auth.user.first_name,
                                                                     session.auth.user.last_name
                                                                     )
            #Hard coded notification message for Demo
            #msg.send_by_pe_id(    3,
            #                      subject="",
            #                      message=message,
            #                      sender_pe_id = None,
            #                      pr_message_method = 2,
            #                      sender="",
            #                      fromaddress="")

            form = FORM(H1("Sahana Eden"),
                        H2("Short Assessment"),
                        P(T("Assessment Reported")),
                        A(T("Report Another Assessment..."),
                          _href = URL(r=request)
                          ),
                        _class = "mobile",
                        )
    else:
         redirect(URL(r=request, c = "default", f = "index"))

    return dict(form = form)

#==============================================================================
