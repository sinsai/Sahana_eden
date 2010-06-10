# -*- coding: utf-8 -*-

"""
    Master Message Log to record/route all Inbound messages
"""

module = "ticket"
if deployment_settings.has_module(module):

    # Settings
    resource = 'setting'
    table = module + '_' + resource
    db.define_table(table,
                    Field('audit_read', 'boolean'),
                    Field('audit_write', 'boolean'),
                    migrate=migrate)

    # -----------------
    # Categories table
    resource = 'category'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
        Field("name"),
        migrate=migrate)

    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)

    # -----------------
    # Tickets table (All sources get entered here : either manually or via S3XRC or Messaging)

    resource = 'log'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
        Field("subject"),
        Field("message", "text"),
        Field("attachment", 'upload', autodelete = True),
        Field("priority", "integer"),
        Field("source", default='local'),
        Field("source_id", "integer"),
        Field("source_time", "datetime", default=request.utcnow),
        location_id,
        Field("categories"),
        Field("verified", "boolean"),
        Field("verified_details", "text"),
        Field("actionable", "boolean"),
        Field("actioned", "boolean"),
        Field("actioned_details", "text"),
        migrate=migrate)

