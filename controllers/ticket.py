# -*- coding: utf-8 -*-

"""
    Ticketing Module - Controllers
"""

module = 'ticket'

# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select().first().name_nice

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Add Ticket'), False, URL(r=request, f='log', args='create')],
    [T('View Tickets'), False, URL(r=request, f='log')],
#    [T('Search Tickets'), False, URL(r=request, f='log', args='search')] #disabled due to problems with pagination
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name, a=1)

def category():
    """ RESTlike CRUD controller """
    resource = 'category'
    return shn_rest_controller(module, resource, listadd=False)

def log():
    """ RESTlike CRUD controller """
    resource = 'log'
    tablename = "%s_%s" % (module, resource)

    # Model options
    ticket_priority_opts = {
        3:T('High'),
        2:T('Medium'),
        1:T('Low')
    }
    
    table = db[tablename]
    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    table.message.requires = IS_NOT_EMPTY()
    table.message.comment = SPAN("*", _class="req")
    table.priority.requires = IS_NULL_OR(IS_IN_SET(ticket_priority_opts))
    table.priority.represent = lambda id: (id and [DIV(IMG(_src='/%s/static/img/priority/priority_%d.gif' % (request.application,id,), _height=12))] or [DIV(IMG(_src='/%s/static/img/priority/priority_4.gif' % request.application), _height=12)])
    table.priority.label = T('Priority')
    table.categories.requires = IS_NULL_OR(IS_IN_DB(db, db.ticket_category.id, '%(name)s', multiple=True))
    #FixMe: represent for multiple=True
    #table.categories.represent = lambda id: (id and [db(db.ticket_category.id==id).select()[0].name] or ["None"])[0]
    table.source.label = T('Source')
    table.source_id.label = T('Source ID')
    table.source_time.label = T('Source Time')
    
    # Only people with the TicketAdmin or Administrator role should be able to access some fields
    try:
        ticket_group = db(db[auth.settings.table_group_name].role == 'TicketAdmin').select().first().id
        if auth.has_membership(ticket_group) or auth_has_membership(1):
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
    ADD_TICKET = T('Add Ticket')
    LIST_TICKETS = T('List Tickets')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_TICKET,
        title_display = T('Ticket Details'),
        title_list = LIST_TICKETS,
        title_update = T('Edit Ticket'),
        title_search = T('Search Tickets'),
        subtitle_create = T('Add New Ticket'),
        subtitle_list = T('Tickets'),
        label_list_button = LIST_TICKETS,
        label_create_button = ADD_TICKET,
        msg_record_created = T('Ticket added'),
        msg_record_modified = T('Ticket updated'),
        msg_record_deleted = T('Ticket deleted'),
        msg_list_empty = T('No Tickets currently registered'))

    if len(request.args) == 0:
        # List View - reduce fields to declutter
        table.message.readable = False
        table.categories.readable = False
        table.verified_details.readable = False
        table.actioned_details.readable = False
    
    return shn_rest_controller(module, resource, listadd=False)
