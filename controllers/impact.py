# -*- coding: utf-8 -*-

"""
    Impact - Controller
    
    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-10-12  
    
"""

module = request.controller

#==============================================================================
def type():
    "RESTful CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    return shn_rest_controller(module, resource)    
#==============================================================================
def impact():
    "RESTful CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    return shn_rest_controller(module, resource)    
#==============================================================================