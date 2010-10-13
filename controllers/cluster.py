# -*- coding: utf-8 -*-

"""
    Cluster - COntroller
    
    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-11-13    
    
"""

module = request.controller

#==============================================================================
def cluster():
    "RESTful CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    return shn_rest_controller(module, resource)    
#==============================================================================
def subsector():
    "RESTful CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    return shn_rest_controller(module, resource)    
#==============================================================================