module = 'mpr'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Search'), False, '#',[
        [T('Search for a Person'), False, URL(r=request, f='person', args='search')]
    ]],
    [T('Reports'), False, '#',[
        [T('Report a missing person'), False, URL(r=request, f='person', args='create')],
        [T('Report a found person'), False, URL(r=request, f='person', args='update')]
    ]]
]

def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def person():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'person')
