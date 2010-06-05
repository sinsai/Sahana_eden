# -*- coding: utf-8 -*-

"""
    Human Resources Management - Controllers

    @author: nursix
"""

module = 'hrm'

# Options Menu (available in all Functions' Views)
response.menu_options = []

# S3 framework functions
def index():
    "Module's Home Page"
    
    module_name = db(db.s3_module.name==module).select().first().name_nice
    
    return dict(module_name=module_name)

