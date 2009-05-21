module = 'msg'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Send SMS'), False, URL(r=request, f='outgoing_sms', args='create')],
    [T('List Received SMS'), False, URL(r=request, f='incoming_sms')],
    [T('List Sent SMS'), False, URL(r=request, f='outgoing_sms')],
    [T('Search SMS'), False, URL(r=request, f='message', args='search')]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def outgoing_sms():
    " RESTlike CRUD controller "
    return shn_rest_controller(module, 'outgoing_sms')
def incoming_sms():
    " RESTlike CRUD controller "
    return shn_rest_controller(module, 'incoming_sms')
