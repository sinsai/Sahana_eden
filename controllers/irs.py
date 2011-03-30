# -*- coding: utf-8 -*-

""" Incident Reporting System - Controllers

    @author: Sahana Taiwan Team

"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Incident Reports"), False, URL(r=request, f="ireport"),[
        [T("List"), False, URL(r=request, f="ireport")],
        [T("Add"), False, URL(r=request, f="ireport", args="create")],
        #[T("Search"), False, URL(r=request, f="ireport", args="search")]
    ]],
    #[T("Map"), False, URL(r=request, f="maps")],
]

if s3_has_role(1):
    response.menu_options.append(
        [T("Incident Categories"), False, URL(r=request, f="icategory"),[
            [T("List"), False, URL(r=request, f="icategory")],
            [T("Add"), False, URL(r=request, f="icategory", args="create")]
        ]]
    )
    response.menu_options.append(
        ["Ushahidi " + T("Import"), False, URL(r=request, f="ireport", args="ushahidi")],
    )

# -----------------------------------------------------------------------------
def index():

    """ Custom View """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)


# -----------------------------------------------------------------------------
def maps():

    """ Show a Map of all Incident Reports """

    reports = db(db.gis_location.id == db.irs_ireport.location_id).select()
    popup_url = URL(r=request, f="ireport", args="read.popup?ireport.location_id=")
    incidents = {"name":T("Incident Reports"), "query":reports, "active":True, "popup_url": popup_url}
    feature_queries = [incidents]

    map = gis.show_map(feature_queries=feature_queries, window=True)

    return dict(map=map)


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def icategory():

    """
        Incident Categories, RESTful controller
        Note: This just defines which categories are visible to end-users
        The full list of hard-coded categories are visible to admins & should remain unchanged for sync
    """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    output = s3_rest_controller(module, resource)
    return output

# -----------------------------------------------------------------------------
def ireport():

    """ Incident Reports, RESTful controller """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Don't send the locations list to client (pulled by AJAX instead)
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

    # Non-Editors should only see a limited set of options
    if not s3_has_role("Editor"):
        allowed_opts = [irs_incident_type_opts.get(opt.code, opt.code) for opt in db().select(db.irs_icategory.code)]
        allowed_opts.sort()
        table.category.requires = IS_NULL_OR(IS_IN_SET(allowed_opts))

    # Pre-processor
    def prep(r):
        if r.method == "ushahidi":
            auth.settings.on_failed_authorization = r.other(method="", vars=None)
            # Allow the 'XX' levels
            db.gis_location.level.requires = IS_NULL_OR(IS_IN_SET(
                gis.get_all_current_levels()))
        elif r.representation in shn_interactive_view_formats and r.method == "update":
            table.verified.writable = True
        elif r.representation in shn_interactive_view_formats and (r.method == "create" or r.method == None):
            table.datetime.default = request.utcnow
            table.person_id.default = s3_logged_in_person()

        return True
    response.s3.prep = prep

    # Post-processor
    def user_postp(r, output):
        shn_action_buttons(r, deletable=True, copyable=False)
        return output
    response.s3.postp = user_postp

    rheader = lambda r: shn_irs_rheader(r, tabs = [(T("Report Details"), None),
                                                   (T("Images"), "iimage")
                                                  ])

    output = s3_rest_controller(module, resource, rheader=rheader)
    if response.s3.actions:
        response.s3.actions.append({"url" : str(URL(r=request, c="assess", f="basic_assess", vars = {"ireport_id":"[id]"})),
                                    "_class" : "action-btn",
                                    "label" : "Assess"})

    return output

# -----------------------------------------------------------------------------
def shn_irs_rheader(r, tabs=[]):

    """ Resource Headers for IRS """

    if r.representation == "html":
        if r.record is None:
            # List or Create form: rheader makes no sense here
            return None

        rheader_tabs = shn_rheader_tabs(r, tabs)

        if r.name == "ireport":
            report = r.record
            reporter = report.person_id
            if reporter:
                reporter = shn_pr_person_represent(reporter)
            location = report.location_id
            if location:
                location = shn_gis_location_represent(location)
            create_request = A(T("Create Request"), _class="action-btn colorbox", _href=URL(r=request, c="rms", f="req", args="create", vars={"format":"popup", "caller":"irs_ireport"}), _title=T("Add Request"))
            create_task = A(T("Create Task"), _class="action-btn colorbox", _href=URL(r=request, c="project", f="task", args="create", vars={"format":"popup", "caller":"irs_ireport"}), _title=T("Add Task"))
            rheader = DIV(TABLE(
                            TR(
                                TH(T("Short Description") + ": "), report.name,
                                TH(T("Reporter") + ": "), reporter),
                            TR(
                                TH(T("Contacts") + ": "), report.contact,
                                TH(T("Location") + ": "), location)
                            ),
                          DIV(P(), create_request, " ", create_task, P()),
                          rheader_tabs)

        return rheader

    else:
        return None


# -----------------------------------------------------------------------------
