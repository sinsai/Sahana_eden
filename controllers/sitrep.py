# -*- coding: utf-8 -*-

"""
    Situation Reporting Module - Controllers
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Flood Reports"), False, URL(r=request, f="freport"),[
        [T("List"), False, URL(r=request, f="freport")],
        [T("Add"), False, URL(r=request, f="freport", args="create")],
        #[T("Search"), False, URL(r=request, f="freport", args="search")]
    ]],
    [T("Assessments"), False, URL(r=request, f="assessment"),[
        [T("List"), False, URL(r=request, f="assessment")],
        [T("Add"), False, URL(r=request, f="assessment", args="create")],
        #[T("Search"), False, URL(r=request, f="assessment", args="search")]
    ]],
    [T("Schools"), False, URL(r=request, f="school_district"),[
        [T("List"), False, URL(r=request, f="school_district")],
        [T("Add"), False, URL(r=request, f="school_district", args="create")],
        #[T("Search"), False, URL(r=request, f="school_district", args="search")]
    ]],
    #[T("Map"), False, URL(r=request, f="maps")],
]

def index():
    "Custom View"
    module_name = deployment_settings.modules[module].name_nice
    return dict(module_name=module_name)

def maps():
    "Show a Map of all Flood Reports"

    feature_class_id = db(db.gis_feature_class.name == "Report").select(db.gis_feature_class.id, limitby=(0, 1)).first().id
    reports = db(db.gis_location.feature_class_id == feature_class_id).select()
    popup_url = URL(r=request, f="freport", args="read.popup?freport.location_id=")
    map = gis.show_map(feature_queries = [{"name":Tstr("Flood Reports"), "query":reports, "active":True, "popup_url": popup_url}], window=True)

    return dict(map=map)

def river():
    "REST Controller"
    resource = request.function

    response.s3.pagination = True

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)
    return output

def freport():
    "REST Controller"
    resource = request.function

    response.s3.pagination = True

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource,
                                 rheader=lambda r: shn_freport_rheader(r,
                                                                   tabs = [(T("Basic Details"), None),
                                                                           (T("Locations"), "freport_location")  ]),
                                                                   sticky=True)
    return output

def assessment():
    "REST Controller"
    resource = request.function

    response.s3.pagination = True

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)
    return output

def school_district():
    "REST Controller"
    resource = request.function

    response.s3.pagination = True

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource,
                                 rheader=lambda r: shn_school_district_rheader(r,
                                                                   tabs = [(T("Basic Details"), None),
                                                                           (T("School Reports"), "school_report")  ]),
                                                                   sticky=True)
    return output

def shn_school_district_rheader(r, tabs=[]):

    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, tabs)

        report = r.record
        location = report.location_id
        if location:
            location = shn_gis_location_represent(location)
        rheader = DIV(TABLE(
                        TR(
                            TH(T("Title: ")), report.name,
                            TH(T("Location: ")), location),
                        TR(
                            TH(T("Reported By: ")), report.reported_by,
                            TH(T("Date: ")), report.date)
                        ),
                    rheader_tabs)

        return rheader
    else:
        return None

def shn_freport_rheader(r, tabs=[]):

    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, tabs)

        report = r.record
        rheader = DIV(TABLE(
                        TR(
                            TH(T("Time: ")), report.time,
                            TH(T("Document: ")), report.document),
                        ),
                    rheader_tabs)

        return rheader
    else:
        return None