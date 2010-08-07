# -*- coding: utf-8 -*-

"""
    Incident Reporting System - Controllers
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Reports"), False, URL(r=request, f="report"),[
        [T("List"), False, URL(r=request, f="report")],
        [T("Add"), False, URL(r=request, f="report", args="create")],
        #[T("Search"), False, URL(r=request, f="report", args="search")]
    ]],
    [T("Incidents"), False, URL(r=request, f="incident"),[
        [T("List"), False, URL(r=request, f="incident")],
        [T("Add"), False, URL(r=request, f="incident", args="create")],
        #[T("Search"), False, URL(r=request, f="incident", args="search")]
    ]],
    [T("Assessments"), False, URL(r=request, f="assessment"),[
        [T("List"), False, URL(r=request, f="assessment")],
        [T("Add"), False, URL(r=request, f="assessment", args="create")],
        #[T("Search"), False, URL(r=request, f="assessment", args="search")]
    ]],
    [T("Map"), False, URL(r=request, f="maps")],
]

def index():
    "Custom View"
    module_name = deployment_settings.modules[module].name_nice
    return dict(module_name=module_name)

def maps():
    "Show a Map of all Reports"
    
    feature_class_id = db(db.gis_feature_class.name == "Incident").select(db.gis_feature_class.id, limitby=(0, 1)).first().id
    reports = db(db.gis_location.feature_class_id == feature_class_id).select()
    popup_url = URL(r=request, f="report", args="read.popup?report.location_id=")
    map = gis.show_map(feature_queries = [{"name":Tstr("Reports"), "query":reports, "active":True, "popup_url": popup_url}], window=True)
    
    return dict(map=map)

def incident():
    "REST Controller"
    resource = request.function

    response.s3.pagination = True

    db.irs_image.assessment_id.readable = db.irs_image.assessment_id.writable = False
    db.irs_image.incident_id.readable = db.irs_image.incident_id.writable = False
    db.irs_image.report_id.readable = db.irs_image.report_id.writable = False

    output = shn_rest_controller(module, resource,
                                 rheader=lambda r: shn_irs_rheader(r,
                                                                    tabs = [(T("Incident Details"), None),
                                                                            (T("Reports"), "report"),
                                                                            (T("Images"), "image"),
                                                                            (T("Assessments"), "assessment"),
                                                                            (T("Response"), "iresponse")]),
                                                                    sticky=True)
    return output

def report():
    "REST Controller"
    resource = request.function

    db.irs_image.assessment_id.readable = db.irs_image.assessment_id.writable = False
    db.irs_image.report_id.readable = db.irs_image.report_id.writable = False

    response.s3.pagination = True

    output = shn_rest_controller(module, resource,
                                 rheader=lambda r: shn_irs_rheader(r,
                                                                   tabs = [(T("Report Details"), None),
                                                                           (T("Images"), "image")  ]),
                                                                   sticky=True)
    return output

def assessment():
    "REST Controller"
    resource = request.function

    db.irs_image.assessment_id.readable = db.irs_image.assessment_id.writable = False
    db.irs_image.report_id.readable = db.irs_image.report_id.writable = False

    response.s3.pagination = True

    output = shn_rest_controller(module, resource,
                                 rheader=lambda r: shn_irs_rheader(r,
                                                                   tabs = [(T("Assessment Details"), None),
                                                                           (T("Images"), "image")  ]),
                                                                   sticky=True)
    return output

def shn_irs_rheader(r, tabs=[]):
    
    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, tabs)
        
        if r.name == "report":
            report = r.record
            reporter = report.person_id
            if reporter:
                reporter = shn_pr_person_represent(reporter)
            location = report.location_id
            if location:
                location = shn_gis_location_represent(location)
            rheader = DIV(TABLE(
                            TR(
                                TH(T("Short Description: ")), report.name,
                                TH(T("Reporter: ")), reporter),
                            TR(
                                TH(T("Contacts: ")), report.contact,
                                TH(T("Location: ")), location)
                            ),
                        rheader_tabs)

        elif r.name == "incident":
            incident = r.record
            location = incident.location_id
            if location:
                location = shn_gis_location_represent(location)
            category = irs_incident_type_opts.get(incident.category, incident.category)
            rheader = DIV(TABLE(
                            TR(
                                TH(T("Short Description: ")), incident.name,
                                TH(T("Category: ")), category),
                            TR(
                                TH(T("Contacts: ")), incident.contact,
                                TH(T("Location: ")), location)
                            ),
                      rheader_tabs)
                      
        elif r.name == "assessment":
            assessment = r.record
            author = shn_pr_person_represent(assessment.created_by)
            itype = irs_assessment_type_opts.get(assessment.itype, UNKNOWN_OPT)
            etype = irs_event_type_opts.get(assessment.event_type, UNKNOWN_OPT)
            rheader = DIV(TABLE(
                            TR(
                                TH(T("Assessment Type: ")), itype,
                                TH(T("Author: ")), author),
                            TR(
                                TH("Event type: "), etype,
                                TH(T("Date: ")), assessment.datetime)
                            ),
                      rheader_tabs)

        return rheader
    else:
        return None
