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

def report():
    "REST Controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    table.name.label = T("Short Description")
    table.name.comment = SPAN("*", _class="req")
    table.person_id.label = T("Reporter Name")
    table.affected.label = T("Number of People Affected")

    # CRUD strings
    ADD_REPORT = T("Add Report")
    LIST_REPORTS = T("List Reports")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_REPORT,
        title_display = T("Report Details"),
        title_list = LIST_REPORTS,
        title_update = T("Edit Report"),
        title_search = T("Search Reports"),
        subtitle_create = T("Add New Report"),
        subtitle_list = T("Reports"),
        label_list_button = LIST_REPORTS,
        label_create_button = ADD_REPORT,
        msg_record_created = T("Report added"),
        msg_record_modified = T("Report updated"),
        msg_record_deleted = T("Report deleted"),
        msg_list_empty = T("No Reports currently registered"))

    output = shn_rest_controller(module, resource,
                                 rheader=lambda jr: shn_ir_rheader(jr,
                                                                   tabs = [ (T("Basic Details"), None),
                                                                            (T("Status"), "status")  ]),
                                                                   sticky=True)
    return output

# Better accessed as Components
#def status():
#    resource = request.function
#    return shn_rest_controller(module, resource)

# CRUD strings
#- defined outside function as used as a component
ADD_UPDATE = T("Add Update")
LIST_UPDATES = T("List Updates")
s3.crud_strings["ir_status"] = Storage(
    title_create = ADD_UPDATE,
    title_display = T("Update Details"),
    title_list = LIST_UPDATES,
    title_update = T("Edit Update"),
    title_search = T("Search Updates"),
    subtitle_create = T("Add New Update"),
    subtitle_list = T("Updates"),
    label_list_button = LIST_UPDATES,
    label_create_button = ADD_UPDATE,
    msg_record_created = T("Update added"),
    msg_record_modified = T("Update updated"),
    msg_record_deleted = T("Update deleted"),
    msg_list_empty = T("No Updates currently registered"))

def shn_ir_rheader(jr, tabs=[]):
    
    if jr.representation == "html":
        rheader_tabs = shn_rheader_tabs(jr, tabs)
        
        report = jr.record
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
        
        return rheader
    else:
        return None
