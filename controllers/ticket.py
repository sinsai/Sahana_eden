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

def log():
    """ RESTlike CRUD controller """
    return shn_rest_controller(module, 'log', listadd=False)
