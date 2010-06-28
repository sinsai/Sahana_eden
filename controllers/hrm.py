# -*- coding: utf-8 -*-

"""
    Human Resources Management - Controllers

    @author: nursix
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = []

# S3 framework functions
def index():
    "Module's Home Page"
    
    module_name = deployment_settings.modules[module].name_nice
    
    return dict(module_name=module_name)

