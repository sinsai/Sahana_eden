# -*- coding: utf-8 -*-

""" Assessment - Model

    @author: Michael Howden
"""

module = "assess"
if deployment_settings.has_module(module):
    # ---------------------------------------------------------------------
    # Assement
    # This is the current status of an Incident
    # @ToDo Change this so that there is a 'lead' ireport updated in the case of duplicates
    resource = "assess"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field("datetime", "datetime"),
                            location_id(),
                            person_id("assessor_person_id"),
                            comments(),
                            )
    
    table.datetime.Label = T("Date & Time")
    table.datetime.default = request.utcnow
    
    table.assessor_person_id.label = T("Assessor")