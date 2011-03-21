# -*- coding: utf-8 -*-

""" S3 Situations

    @author: nursix

"""

prefix = "sit"

# -----------------------------------------------------------------------------
# Situation super-entity
situation_types = Storage(
    irs_incident = T("Incident"),
    rms_req = T("Request"),
    pr_presence = T("Presence")
)

resourcename = "situation"
tablename = "sit_situation"

table = super_entity(tablename, "sit_id", situation_types,
                     Field("datetime", "datetime"),
                     location_id(),
                     migrate=migrate)

s3xrc.model.configure(table, editable=False, deletable=False, listadd=False)

# -----------------------------------------------------------------------------
# Trackable super-entity
# Use:
#       - add a field with super_link(db.sit_trackable)
#       - add as super-entity in configure (super_entity=db.sit_trackable)
#
trackable_types = Storage(
    pr_person = T("Person"),
    dvi_body = T("Dead Body")
)

resourcename = "trackable"
tablename = "sit_trackable"

table = super_entity(tablename, "track_id", trackable_types,
                     location_id("base_location"),
                     migrate=migrate)

s3xrc.model.configure(table, editable=False, deletable=False, listadd=False)

# -----------------------------------------------------------------------------
# Universal presence
# Use:
#       - will be automatically available to all trackable types
#
resourcename = "presence"
tablename = "sit_presence"

table = db.define_table(tablename,
                        super_link(db.sit_trackable),
                        Field("timestmp", "datetime"),
                        location_id(),
                        Field("interlock"),
                        migrate=migrate, *s3_meta_fields())

# Shared component of all trackable types
s3xrc.model.add_component(prefix, resourcename,
                          multiple=True,
                          joinby=super_key(db.sit_trackable))

# -----------------------------------------------------------------------------
# Resource super-entity
resource_types = Storage(
    hrm_human_resource = T("Human Resource"),
)

resourcename = "resource"
tablename = "sit_resource"

table = super_entity(tablename, "res_id", resource_types,
                     migrate=migrate)

s3xrc.model.configure(table, editable=False, deletable=False, listadd=False)
# -----------------------------------------------------------------------------
