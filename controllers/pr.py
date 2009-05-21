module = 'pr'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Add Person'), False, URL(r=request, f='person', args='create')],
    [T('List People'), False, URL(r=request, f='person')],
    [T('Search People'), False, URL(r=request, f='person', args='search')]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def person():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'person', main='first_name', extra='last_name')
def contact():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'contact')
