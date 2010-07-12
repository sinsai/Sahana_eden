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


    # Valid message outbox statuses
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

	# Person entity outbox - Should be extended for non pr_pe_id type resources #TODO 
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
                #Field("preference", "integer", default = 5), To be used later
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
                #Field("preference", "integer", default = 5), To be used later
                migrate=migrate)
    # Message priority
    msg_priority_opts = {
        3:T("High"),
        2:T("Medium"),
        1:T("Low")
    }

    # Message Log - This is where all the messages / logs go into
    resource = "log"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
        person_id,#Sender
        Field("sender"), #The name to go out incase of the email, if set used
        Field("fromaddress"), #From address if set changes sender to this
        Field("subject"),
        Field("message", "text"),
        Field("attachment", "upload", autodelete = True),
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
                          list_fields=["id",
                                       "person_id",
                                       "subject",
                                       "verified",
                                       "verified_comments",
                                       "actionable",
                                       "actioned",
                                       "actioned_comments",
                                       "priority"])

    # Reusable Message ID
    message_id = db.Table(None, "message_id",
                FieldS3("message_id", db.msg_log,
                    requires = IS_NULL_OR(IS_ONE_OF(db, "msg_log.id")),
                    ondelete = "RESTRICT"
                ))

    # Message Tag - Used to tag a message to a resource
    resource = "tag"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
        message_id,
        Field("resource"),
        Field("record_uuid", # null in this field implies subscription to the entire resource
            type=s3uuid,
            length=128),
        migrate=migrate)

    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    s3xrc.model.configure(table,
                          list_fields=[ "id",
                                        "message_id",
                                        "record_uuid",
                                        "resource",
                                       ])

    # Message Outbox1 - To replace Message Outbox #TODO
    resource = "outbox1"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
        message_id,
        pe_contact_id, # Person/Group to send the message out to 
        Field("address"), # If set used instead of pe_contact_id
        opt_msg_status,
        Field("log"),
        migrate=migrate)

    s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby=dict(msg_log="message_id"),
                          deletable=True,
                          editable=True)

    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    s3xrc.model.configure(table,
                          list_fields=[ "id",
                                        "message_id",
                                        "pe_contact_id",
                                        "status",
                                        "log",
                                       ])
    # Message Read Status - To replace Message Outbox #TODO
    resource = "read_status"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
        message_id,
        person_id,
        migrate=migrate)

    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    s3xrc.model.configure(table,
                          list_fields=[ "id",
                                        "message_id",
                                        "person_id",
                                       ])

    # CAP: Common Alerting Protocol
    # http://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2.html
    # CAP alert Status Code (status) 
    cap_alert_status_code_opts = {
        "Actual":T("Actionable by all targeted recipients"),
        "Exercise":T("Actionable only by designated exercise participants; exercise identifier SHOULD appear in <note>"),
        "System":T("For messages that support alert network internal functions"),
        "Test":T("Technical testing only, all recipients disregard"),
        "Draft":T("preliminary template or draft, not actionable in its current form"),
    }
    # CAP info Event Category (category) 
    cap_info_category_opts = {
        "Geo":T("Geophysical (inc. landslide)"),
        "Met":T("Meteorological (inc. flood)"),
        "Safety":T("General emergency and public safety"),
        "Security":T("Law enforcement, military, homeland and local/private security"),
        "Rescue":T("Rescue and recovery"),
        "Fire":T("Fire suppression and rescue"),
        "Health":T("Medical and public health"),
        "Env":T("Pollution and other environmental"),
        "Transport":T("Public and private transportation"),
        "Infra":T("Utility, telecommunication, other non-transport infrastructure"),
        "CBRNE":T("Chemical, Biological, Radiological, Nuclear or High-Yield Explosive threat or attack"),
        "Other":T("Other events"),
    }
    # CAP info Response Type (responseType) 
    cap_info_responseType_opts = {
        "Shelter":T("Take shelter in place or per <instruction>"),
        "Evacuate":T("Relocate as instructed in the <instruction>"),
        "Prepare":T("Make preparations per the <instruction>"),
        "Execute":T("Execute a pre-planned activity identified in <instruction>"),
        "Avoid":T("Avoid the subject event as per the <instruction>"),
        "Monitor":T("Attend to information sources as described in <instruction>"),
        "Assess":T("Evaluate the information in this message.  (This value SHOULD NOT be used in public warning applications.)"),
        "AllClear":T("The subject event no longer poses a threat or concern and any follow on action is described in <instruction>"),
        "None":T("No action recommended"),
    }
    
    # Reports
    # Verified reports ready to be sent out as alerts or displayed on a map 
    msg_report_type_opts = {
        "Shelter":T("Take shelter in place or per <instruction>"),
        "Evacuate":T("Relocate as instructed in the <instruction>"),
        "Prepare":T("Make preparations per the <instruction>"),
        "Execute":T("Execute a pre-planned activity identified in <instruction>"),
        "Avoid":T("Avoid the subject event as per the <instruction>"),
        "Monitor":T("Attend to information sources as described in <instruction>"),
        "Assess":T("Evaluate the information in this message.  (This value SHOULD NOT be used in public warning applications.)"),
        "AllClear":T("The subject event no longer poses a threat or concern and any follow on action is described in <instruction>"),
        "None":T("No action recommended"),
    }
    resource = "report"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    message_id,
                    location_id,
                    Field("image", "upload", autodelete = True),
                    Field("url", requires=IS_NULL_OR(IS_URL())),
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
