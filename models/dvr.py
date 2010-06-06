# -*- coding: utf-8 -*-

"""
    DVR Disaster Victim Registry (Sahana Legacy)

    @author nursix
"""

module = "dvr"
if module in deployment_settings.modules:

    # Settings
    resource = "setting"
    table = module + "_" + resource
    db.define_table(table,
                    Field("audit_read", "boolean"),
                    Field("audit_write", "boolean"),
                    migrate=migrate)
