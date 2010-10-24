# -*- coding: utf-8 -*-

""" S3 Situations

    @author: nursix

"""

module = "sit"

# Situation super-entity
situation_types = Storage(
    irs_incident = T("Incident"),
    rms_req = T("Request"),
    pr_presence = T("Presence")
)

resourcename = "situation"
tablename = "%s_%s" % (module, resourcename)

table = s3xrc.model.super_entity(tablename, "sit_id", situation_types,
                                 Field("datetime", "datetime"),
                                 location_id(),
                                 migrate=migrate)

sit_id = S3ReusableField("sit_id", db.sit_situation,
                         requires = IS_NULL_OR(IS_ONE_OF(db, "sit_situation.sit_id", "%(sit_id)s", orderby="sit_situation.sit_id")),
                         represent = lambda id: id and str(id) or NONE,
                         readable = False,
                         writable = False,
                         ondelete = "RESTRICT")

# -----------------------------------------------------------------------------
