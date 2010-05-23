# -*- coding: utf-8 -*-
"""
    Template for a Controller
    
    @author: Michael Howden (michael@aidiq.com)
    @date-created: 2010-05-23
    
    This controller introduces some of the basic features of Sahana
    it can be used as a template to build a controller for your own modules
"""

module = "template"

def disaster():
    "RESTful CRUD controller"
    return shn_rest_controller(module, "disaster" )

