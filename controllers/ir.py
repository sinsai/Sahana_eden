def event():
    db.ir_event.reporter.label = T("Reporter Name")
    s3.crud_strings["ir_event"] = Storage(
        title_create = T("Add Event"),
        title_display = T("Event Details"),
        title_list =  T("List Event"),
        title_update = T("Edit Event"),
        title_search = T("Search Records"),
        subtitle_create = T("Add New Record"),
        subtitle_list = T("Available Records"),
        label_list_button = T("LIST_RECORDS"),
        label_create_button = T("Add Event"),
        label_delete_button = T("Delete Record"),
        msg_record_created = T("Event added"),
        msg_record_modified = T("Record updated"),
        msg_record_deleted = T("Record deleted"),
        msg_list_empty = T("No Records currently available"))


    output = shn_rest_controller(module, "event", rheader=lambda jr: shn_ir_rheader(jr, tabs = [(T("Basic Details"), None), (T("Event Status"), "eventstatus")  ]),     sticky=True)
    #output = shn_rest_controller(module, "event", rheader=lambda jr: shn_ir_rheader(jr, tabs = [(T("Basic Details"), None), (T("Presence"), "presence")]),sticky=True)
    return output


module = request.controller
resource = "event"    

def eventstatus():    
    resource = request.function
    return shn_rest_controller(module, resource)

def index():
    "Custom View"
    module_name = \
    deployment_settings.modules[module].name_nice
    return dict(module_name=module_name)

def shn_ir_rheader(jr, tabs=[]):
    if jr.representation == "html":
        rheader_tabs = shn_rheader_tabs(jr, tabs)
        event = jr.record
        rheader = DIV(TABLE(
        TR(TH(T("Short : ")), event.shortDescription,
        TH(T("Reportre: ")), event.reporter),
        TR(TH(T("Contacts: ")),
            event.contacts,
        TH(T("Location: ")), event.location_id)),
            rheader_tabs)
        return rheader
    return None

    
  
