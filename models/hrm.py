# -*- coding: utf-8 -*-

"""
    HRM Human Resources Management

    @author: nursix
"""

module = "hrm"
if deployment_settings.has_module(module):

    #
    # Settings --------------------------------------------------------------------
    #
    resource = "setting"
    table = module + "_" + resource
    db.define_table(table,
                    Field("audit_read", "boolean"),
                    Field("audit_write", "boolean"),
                    migrate=migrate)
