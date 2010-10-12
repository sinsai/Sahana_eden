# -*- coding: utf-8 -*-

"""
    Assessment - COntroller
    
    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-25    
    
"""

module = request.controller

#==============================================================================
def assess():
    "RESTful CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    return shn_rest_controller(module, resource, listadd=False)

