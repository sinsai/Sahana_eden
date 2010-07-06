# -*- coding: utf-8 -*-

"""
    Messaging module
"""

module = "msg"
if deployment_settings.has_module(module):

    # Settings
    resource = "setting"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                    Field("audit_read", "boolean"),
                    Field("audit_write", "boolean"),
                    Field("outgoing_sms_handler"),
                    migrate=migrate)
    table.outgoing_sms_handler.requires = IS_IN_SET(["Modem","Gateway"], zero = None)

    resource = "email_settings"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                    Field("inbound_mail_server"),
                    Field("inbound_mail_type"),
                    Field("inbound_mail_ssl", "boolean"),
                    Field("inbound_mail_port", "integer"),
                    Field("inbound_mail_username"),
                    Field("inbound_mail_password"),
                    Field("inbound_mail_delete", "boolean"),
                    # Also needs to be used by Auth (order issues), DB calls are overheads
                    # - as easy for admin to edit source in 000_config.py as to edit DB (although an admin panel can be nice)
                    #Field("outbound_mail_server"),
                    #Field("outbound_mail_from"),
                    migrate=migrate)
    table.inbound_mail_type.requires = IS_IN_SET(["imap", "pop3"], zero=None)
    
    # Status
    resource = "email_inbound_status"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                    Field("status"),
                    migrate=migrate)


    # Valid message outbox status'
    msg_status_type_opts = {
        1:T("Unsent"),
        2:T("Sent"),
        3:T("Draft"),
        4:T("Invalid")
        }

    opt_msg_status = db.Table(None, "opt_msg_status",
                        Field("status", "integer", notnull=True,
                        requires = IS_IN_SET(msg_status_type_opts, zero=None),
                        default = 1,
                        label = T("Status"),
                        represent = lambda opt: msg_status_type_opts.get(opt, UNKNOWN_OPT)))

	# Person entity outbox - Should be extended for non pr_pe_id type resources
    resource = "outbox"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, authorstamp, uuidstamp, deletion_status,
                    pr_pe_id,
                    person_id,
                    Field("subject", length=78),    # RFC 2822
                    Field("body", "text"),
                    Field("pr_message_method",
                      "integer",
                      requires = IS_IN_SET(pr_contact_method_opts, zero=None),
                      default = 1,
                      label = T("Contact Method"),
                      represent = lambda opt: pr_contact_method_opts.get(opt, UNKNOWN_OPT)),
                    opt_msg_status,
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    

    # SMS store for persistence and scratch pad for combining incoming xform chunks
    resource = "xforms_store"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                Field("sender", "string", length = 20),
                Field("fileno", "integer"),
                Field("totalno", "integer"),
                Field("partno", "integer"),
                Field("message", "string", length = 160),
            migrate=migrate)

    # Settings for modem.
    resource = "modem_settings"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                #Field("account_name"), # Nametag to remember account - To be used later
                Field("modem_port"),
                Field("modem_baud", "integer", default = 115200),
                Field("enabled", "boolean", default = False),
#                Field("preference", "integer", default = 5), To be used later
                migrate=migrate)
    

    # Settings for modem.
    resource = "gateway_settings"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
               Field("url", default =\
                "https://api.clickatell.com/http/sendmsg"),
                Field("parameters", default =\
                "user=yourusername&password=yourpassword&api_id=yourapiid"),
                Field("message_variable", "string", default = "text"),
                Field("to_variable", "string", default = "to"),
                Field("enabled", "boolean", default = False),
#                Field("preference", "integer", default = 5), To be used later
                migrate=migrate)
    # Message priority
    msg_priority_opts = {
        3:T('High'),
        2:T('Medium'),
        1:T('Low')
    }

    # Message Log - This is where all the messges / logs go into
    resource = 'log'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
        person_id,#Sender
        Field("subject"),
        Field("message", "text"),
        Field("attachment", 'upload', autodelete = True),
        Field("verified", "boolean", default = False),
        Field("verified_comments", "text"),
        Field("actionable", "boolean", default = True),
        Field("actioned", "boolean", default = False),
        Field("actioned_comments", "text"),
        Field("priority", "integer"),
        migrate=migrate)

    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    table.priority.requires = IS_NULL_OR(IS_IN_SET(msg_priority_opts))
    s3xrc.model.configure(table,
                          list_fields=['id',
                                       'person_id',
                                       'subject',
                                       'verified',
                                       'verified_comments',
                                       'actionable',
                                       'actioned',
                                       'actioned_comments',
                                       'priority'])

    # Reusable Message ID
    message_id = db.Table(None, "message_id",
                FieldS3("message_id", db.msg_log,
                    requires = IS_NULL_OR(IS_ONE_OF(db, "msg_log.id")),
                    ondelete = "RESTRICT"
                ))

    # Message Tag - Used to tag a message to a resource
    resource = 'tag'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
        message_id,
        Field('resource'),
        Field("record_uuid", # null in this field implies subscription to the entire resource
            type=s3uuid,
            length=128),
        migrate=migrate)

    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    s3xrc.model.configure(table,
                          list_fields=[ 'id',
                                        'message_id',
                                        'record_uuid',
                                        'resource',
                                       ])

    # Message Outbox1 - To replace Message Outbox #TODO
    resource = 'outbox1'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
        message_id,
        pe_contact_id,
        Field('status'),
        Field('log'),
        migrate=migrate)

    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    s3xrc.model.configure(table,
                          list_fields=[ 'id',
                                        'message_id',
                                        'pe_contact_id',
                                        'status',
                                        'log',
                                       ])
    # Message Read Status - To replace Message Outbox #TODO
    resource = 'read_status'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
        message_id,
        person_id,
        migrate=migrate)

    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    s3xrc.model.configure(table,
                          list_fields=[ 'id',
                                        'message_id',
                                        'person_id',
                                       ])
