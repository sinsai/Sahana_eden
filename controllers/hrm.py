# -*- coding: utf-8 -*-

module = 'hrm'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select().first().name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = []

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

