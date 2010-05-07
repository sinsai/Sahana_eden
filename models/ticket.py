# -*- coding: utf-8 -*-

"""
    Master Message Log to record/route all Inbound messages
"""

module = 'ticket'
if shn_module_enable.get(module, False):

    # Settings
    resource = 'setting'
    table = module + '_' + resource
    db.define_table(table,
                    Field('audit_read', 'boolean'),
                    Field('audit_write', 'boolean'),
                    migrate=migrate)

    # -------------------------------
    # Load lists/dictionaries for drop down menus

    ticket_priority_opts = {
        3:T('High'),
        2:T('Medium'),
        1:T('Low')
    }

    # -----------------
    # Tickets table (All sources get entered here : either manually or via S3XRC or Messaging)

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

    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    table.message.requires = IS_NOT_EMPTY()
    table.message.comment = SPAN("*", _class="req")
    table.priority.requires = IS_NULL_OR(IS_IN_SET(ticket_priority_opts))
    table.priority.represent = lambda id: (id and [DIV(IMG(_src='/%s/static/img/priority/priority_%d.gif' % (request.application,id,), _height=12))] or [DIV(IMG(_src='/%s/static/img/priority/priority_4.gif' % request.application), _height=12)])
    table.priority.label = T('Priority')
    table.categories.requires = IS_NULL_OR(IS_IN_DB(db, db.ticket_category.id, '%(name)s', multiple=True))
    table.source.label = T('Source')
    table.source_id.label = T('Source ID')
    table.source_time.label = T('Source Time')
    