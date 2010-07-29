# -*- coding: utf-8 -*-

""" IRS Incident Report System

    @author: nursix

"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# -----------------------------------------------------------------------------
def shn_menu():
    menu = [
        [T("Home"), False, URL(r=request, f="index")],
        [T("Incidents"), False, URL(r=request, f="incident"), [
            [T("List Reports"), False, URL(r=request, f="incident")],
            [T("Add Report"), False, URL(r=request, f="incident", args="create")]
        ]],
    ]
    #if session.rcvars and "hms_hospital" in session.rcvars:
        #hospital = db.hms_hospital
        #query = (hospital.id == session.rcvars["hms_hospital"])
        #selection = db(query).select(hospital.id, hospital.name, limitby=(0,1)).first()
        #if selection:
            #menu_hospital = [
                    #[selection.name, False, URL(r=request, f="hospital", args=[selection.id])]
            #]
            #menu.extend(menu_hospital)
    #menu2 = [
        #[T("Add Request"), False, URL(r=request, f="hrequest", args="create")],
        #[T("Requests"), False, URL(r=request, f="hrequest")],
        #[T("Pledges"), False, URL(r=request, f="hpledge")],
    #]
    #menu.extend(menu2)
    response.menu_options = menu

shn_menu()

# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    return dict(module_name=module_name, public_url=deployment_settings.base.public_url)

# -----------------------------------------------------------------------------
def incident():

    """ RESTful CRUD controller """

    resource = request.function

    response.s3.pagination = True

    output = shn_rest_controller(module, resource,
                main="type",
                extra="subject",
                rheader=lambda r: shn_irs_rheader(r,
                    tabs = [(T("Incident"), None),
                            (T("Images"), "iimage"),
                            (T("Assessment"), "iassessment"),
                            (T("Response"), "iresponse")
                            ]),
                sticky=True)

    shn_menu()
    return output

# -----------------------------------------------------------------------------
def iassessment():

    """ RESTful CRUD controller """

    resource = request.function

    response.s3.pagination = True

    return shn_rest_controller(module, resource)

# -----------------------------------------------------------------------------
def iresponse():

    """ RESTful CRUD controller """

    resource = request.function

    response.s3.pagination = True

    return shn_rest_controller(module, resource)

# -----------------------------------------------------------------------------
def shn_irs_rheader(r, tabs=[]):

    """ Page header for component resources """

    if r.name == "incident" and r.representation == "html":

        _next = r.here()
        _same = r.same()

        rheader_tabs = shn_rheader_tabs(r, tabs)

        incident = r.resource.records().first()
        if incident:
            location = db.gis_location[incident.location_id]
            if location:
                location = location.name
            else:
                location = UNKNOWN_OPT
            rheader = DIV(TABLE(
                        TR(TH(T("Date/Time: ")),
                           incident.datetime,
                           TH(T("Type: ")),
                           "%s" % db.irs_incident.type.represent(incident.type),
                           TH(""),
                           TH("")),

                        TR(TH(T("Location: ")),
                           location,
                           TH(T("Note: ")),
                           incident.note,
                           TH(""),
                           TH("")),

                    ), rheader_tabs)

            return rheader

    return None

