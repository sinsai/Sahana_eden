# -*- coding: utf-8 -*-

module = 'dvi'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)
