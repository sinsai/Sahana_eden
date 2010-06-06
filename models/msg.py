# -*- coding: utf-8 -*-

"""
    Messaging module
"""

module = "msg"
if module in deployment_settings.modules:

    # Settings
    resource = "setting"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                    Field('audit_read', 'boolean'),
                    Field('audit_write', 'boolean'),
                    # Also needs to be used by Auth (order issues), DB calls are overheads
                    # - as easy for admin to edit source in 00_db.py as to edit DB (although an admin panel can be nice)
                    Field('inbound_mail_server'),
                    Field('inbound_mail_type'),
                    Field('inbound_mail_ssl', 'boolean'),
                    Field('inbound_mail_port', 'integer'),
                    Field('inbound_mail_username'),
                    Field('inbound_mail_password'),
                    Field('inbound_mail_delete', 'boolean'),
                    #Field('outbound_mail_server'),
                    #Field('outbound_mail_from'),
                    migrate=migrate)
    table.inbound_mail_type.requires = IS_IN_SET(['imap', 'pop3'])
    table.inbound_mail_port.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Port|For POP-3 this is usually 110 (995 for SSL), for IMAP this is usually 143 (993 for IMAP)."))
    table.inbound_mail_delete.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Delete|If this is set to True then mails will be deleted from the server after downloading."))

    # Status
    resource = 'email_inbound_status'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                    Field('status'),
                    migrate=migrate)


    # Valid message outbox status'
    msg_status_type_opts = {
        1:T('Unsent'),
        2:T('Sent'),
        3:T('Draft'),
        4:T('Invalid')
        }

    opt_msg_status = db.Table(None, 'opt_msg_status',
                        Field('status', 'integer', notnull=True,
                        requires = IS_IN_SET(msg_status_type_opts),
                        default = 1,
                        label = T('Status'),
                        represent = lambda opt: msg_status_type_opts.get(opt, UNKNOWN_OPT)))

	# Person entity outbox - Should be extended for non pr_pe_id type resources
    resource = 'outbox'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, authorstamp, uuidstamp, deletion_status,
                    pr_pe_id,
                    person_id,
                    Field('subject', length=78),    # RFC 2822
                    Field('body', 'text'),
                    Field("pr_message_method",
                      "integer",
                      requires = IS_IN_SET(pr_contact_method_opts),
                      default = 1,
                      label = T("Contact Method"),
                      represent = lambda opt: pr_contact_method_opts.get(opt, UNKNOWN_OPT)),
                    opt_msg_status,
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % tablename)
    table.pr_pe_id.label = T('Recipients ')
    table.person_id.label = T('Sender')
    table.subject.label = T('Subject')
    table.body.label = T('Body')
    SEND_MESSAGE = T('Send Message')
    VIEW_MESSAGE_OUTBOX = T('View OutBox')
    s3.crud_strings[tablename] = Storage(
            title_create = SEND_MESSAGE,
            title_display = T('Message Details'),
            title_list = VIEW_MESSAGE_OUTBOX,
            title_update = T('Edit Message'),
            title_search = T('Search OutBox'),
            subtitle_create = SEND_MESSAGE,
            subtitle_list = T('OutBox'),
            label_list_button = VIEW_MESSAGE_OUTBOX,
            label_create_button = SEND_MESSAGE,
            msg_record_created = T('Message created'),
            msg_record_modified = T('Message updated'),
            msg_record_deleted = T('Message deleted'),
            msg_list_empty = T('No Message currently in your OutBox'))
