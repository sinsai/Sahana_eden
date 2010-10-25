# -*- coding: utf-8 -*-

""" S3 Situations

    @author: nursix

"""

prefix = "sit"

# Situation super-entity
situation_types = Storage(
    irs_incident = T("Incident"),
    rms_req = T("Request"),
    pr_presence = T("Presence")
)

resourcename = "situation"
tablename = "%s_%s" % (prefix, resourcename)

table = super_entity(tablename, "sit_id", situation_types,
                     Field("datetime", "datetime"),
                     location_id(),
                     migrate=migrate)

s3xrc.model.configure(table, editable=False, deletable=False, listadd=False)

