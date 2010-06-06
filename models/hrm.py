# -*- coding: utf-8 -*-

"""
    HRM Human Resources Management

    @author: nursix
"""

module = "hrm"
if module in deployment_settings.modules:

    #
    # Settings --------------------------------------------------------------------
    #
    resource = "setting"
    table = module + "_" + resource
    db.define_table(table,
                    Field("audit_read", "boolean"),
                    Field("audit_write", "boolean"),
                    migrate=migrate)
