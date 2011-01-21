# -*- coding: utf-8 -*-

""" Ticketing Module - Controllers """

prefix = request.controller
resourcename = request.function

if prefix not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Home"), False, URL(r=request, f="index")],
    [T("Add Ticket"), False, URL(r=request, f="log", args="create")],
    [T("View Tickets"), False, URL(r=request, f="log")],
#    [T("Search Tickets"), False, URL(r=request, f="log", args="search")] #disabled due to problems with pagination
]


def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[prefix].name_nice
    response.title = module_name
    return dict(module_name=module_name, a=1)


def category():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    s3xrc.model.configure(table, listadd=False)
    return s3_rest_controller(prefix, resourcename)


def log():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    # Model options
    table.person_id.label = T("Assigned To")
    table.priority.represent = lambda id: (
        [id and
            DIV(IMG(_src="/%s/static/img/priority/priority_%d.gif" % (request.application,id,), _height=12)) or
            DIV(IMG(_src="/%s/static/img/priority/priority_4.gif" % request.application), _height=12)
        ][0].xml())
    table.priority.label = T("Priority")
    table.source.label = T("Source")
    table.source_id.label = T("Source ID")
    table.source_time.label = T("Source Time")

    # Only people with the TicketAdmin or Administrator role should be able to access some fields
    try:
        ticket_group = db(db[auth.settings.table_group_name].role == "TicketAdmin").select(db[auth.settings.table_group_name].id, limitby=(0, 1)).first().id
        if auth.has_membership(ticket_group) or auth.has_membership(1):
            # Auth ok, so can grant full access
            pass
        else:
            # Logged-in, but no rights
            table.verified.writable = False
            table.verified_details.writable = False
            table.actioned.writable = False
            table.actioned_details.writable = False
    except:
        # Anonymous
        table.verified.writable = False
        table.verified_details.writable = False
        table.actioned.writable = False
        table.actioned_details.writable = False

    # CRUD Strings
    ADD_TICKET = T("Add Ticket")
    LIST_TICKETS = T("List Tickets")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_TICKET,
        title_display = T("Ticket Details"),
        title_list = LIST_TICKETS,
        title_update = T("Edit Ticket"),
        title_search = T("Search Tickets"),
        subtitle_create = T("Add New Ticket"),
        subtitle_list = T("Tickets"),
        label_list_button = LIST_TICKETS,
        label_create_button = ADD_TICKET,
        msg_record_created = T("Ticket added"),
        msg_record_modified = T("Ticket updated"),
        msg_record_deleted = T("Ticket deleted"),
        msg_list_empty = T("No Tickets currently registered"))

    s3xrc.model.configure(table, listadd=False)
    return s3_rest_controller(prefix, resourcename)

