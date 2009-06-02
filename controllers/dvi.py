module = 'dvi'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Add Body'), False, URL(r=request, f='dead_body', args='create')],
    [T('List Bodies'), False, URL(r=request, f='dead_body')],
    [T('Search Bodies'), False, URL(r=request, f='dead_body', args='search')]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def dead_body():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'dead_body', main='tag_label')
