# -*- coding: utf-8 -*-

"""
    Messaging module
"""

module = 'msg'
if shn_module_enable.get(module, False):

    # Settings
    resource = 'setting'
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

    # Group
    #msg_group_type_opts = {
        #1:T('Email'),
        #2:T('SMS'),
        #3:T('Both')
        #}
    #opt_msg_group_type = db.Table(None, 'opt_msg_group_type',
                        #Field('group_type', 'integer', notnull=True,
                        #requires = IS_IN_SET(msg_group_type_opts),
                        ## default = 1,
                        #label = T('Type'),
                        #represent = lambda opt: msg_group_type_opts.get(opt, UNKNOWN_OPT)))

    resource = 'group'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('name', notnull=True),
                    #opt_msg_group_type,
                    Field('comments'),
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % tablename)
    table.name.requires = IS_NOT_EMPTY()
    table.name.label = T('Name')
    table.name.comment = SPAN("*", _class="req")
    table.comments.label = T('Comments')
    ADD_GROUP = T('Add Group')
    LIST_GROUP = T('List Groups')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_GROUP,
        title_display = T('Group Details'),
        title_list = LIST_GROUP,
        title_update = T('Edit Group'),
        title_search = T('Search Groups'),
        subtitle_create = T('Add New Group'),
        subtitle_list = T('Groups'),
        label_list_button = LIST_GROUP,
        label_create_button = ADD_GROUP,
        msg_record_created = T('Group added'),
        msg_record_modified = T('Group updated'),
        msg_record_deleted = T('Group deleted'),
        msg_list_empty = T('No Groups currently registered'))
    # Reusable field for other tables to reference
    msg_group_id = db.Table(None, 'msg_group_id',
                FieldS3('msg_group_id', db.msg_group, sortby='name',
                    requires = IS_ONE_OF(db, 'msg_group.id', '%(name)s'),
                    represent = lambda id: (id and [db(db.msg_group.id==id).select()[0].name] or ["None"])[0],
                    label = T('Group'),
                    comment = DIV(A(T('Add Group'), _class='colorbox', _href=URL(r=request, c='msg', f='group', args='create', vars=dict(format='popup')), _target='top', _title=T('Add Group')), A(SPAN("[Help]"), _class="tooltip", _title=T("Distribution Group|The Group of People to whom this Message should be sent."))),
                    ondelete = 'RESTRICT'
                    ))

    # Group<>User Many2Many
    resource = 'group_user'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, deletion_status,
                    Field('msg_group_id', db.msg_group),
                    person_id,
                    migrate=migrate)
    table.msg_group_id.requires = IS_ONE_OF(db, 'msg_group.id', '%(name)s')
    table.msg_group_id.represent = lambda msg_group_id: db(db.msg_group.id==msg_group_id).select()[0].name
    table.person_id.label = T('User')

    # Incoming SMS
    resource = 'sms_inbox'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('phone_number', 'integer', notnull=True),
                    Field('contents', length=700),  # length=140 omitted to handle multi-part SMS
                    #Field('smsc', 'integer'),
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % tablename)
    table.phone_number.requires = IS_NOT_EMPTY()
    table.phone_number.label = T('Phone Number')
    #table.phone_number.comment = SPAN("*", _class="req")
    table.contents.label = T('Contents')
    VIEW_SMS_INBOX = T('View SMS InBox')
    s3.crud_strings[tablename] = Storage(
        #title_create = T('Add Incoming SMS'),
        title_display = T('SMS Details'),
        title_list = VIEW_SMS_INBOX,
        #title_update = T('Edit SMS'),
        title_search = T('Search SMS InBox'),
        subtitle_list = T('SMS InBox'),
        label_list_button = VIEW_SMS_INBOX,
        #label_create_button = T('Add Incoming SMS'),
        #msg_record_created = T('SMS added'),
        #msg_record_modified = T('SMS updated'),
        msg_record_deleted = T('SMS deleted'),
        msg_list_empty = T('No SMS\'s currently in InBox'))

    # Outgoing SMS
    resource = 'sms_outbox'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, authorstamp, uuidstamp, deletion_status,
                    #Field('phone_number', 'integer', notnull=True),
                    msg_group_id,
                    Field('contents', length=700),  # length=140 omitted to handle multi-part SMS
                    #Field('smsc', 'integer'),
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % tablename)
    #table.phone_number.requires = IS_NOT_EMPTY()
    #table.phone_number.comment = SPAN("*", _class="req")
    table.contents.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Contents|If this is over 140 characters then it will be split into Multiple SMS's."))
    table.msg_group_id.label = T('Recipients')
    table.contents.label = T('Contents')
    SEND_SMS = T('Send SMS')
    VIEW_SMS_OUTBOX = T('View SMS OutBox')
    s3.crud_strings[tablename] = Storage(
        title_create = SEND_SMS,
        title_display = T('SMS Details'),
        title_list = VIEW_SMS_OUTBOX,
        title_update = T('Edit SMS'),
        title_search = T('Search SMS OutBox'),
        subtitle_create = SEND_SMS,
        subtitle_list = T('SMS OutBox'),
        label_list_button = VIEW_SMS_OUTBOX,
        label_create_button = T('Send SMS'),
        msg_record_created = T('SMS created'),
        msg_record_modified = T('SMS updated'),
        msg_record_deleted = T('SMS deleted'),
        msg_list_empty = T('No SMS\'s currently in OutBox'))

    resource = 'sms_sent'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, authorstamp, uuidstamp, deletion_status,
                    #Field('phone_number', 'integer', notnull=True),
                    msg_group_id,
                    Field('contents', length=700),  # length=140 omitted to handle multi-part SMS
                    #Field('smsc', 'integer'),
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % tablename)
    #table.phone_number.requires = IS_NOT_EMPTY()
    #table.phone_number.comment = SPAN("*", _class="req")
    table.msg_group_id.label = T('Recipients')
    table.contents.label = T('Contents')
    VIEW_SENT_SMS = T('View Sent SMS')
    s3.crud_strings[tablename] = Storage(
        #title_create = T('Send SMS'),
        title_display = T('SMS Details'),
        title_list = VIEW_SENT_SMS,
        #title_update = T('Edit SMS'),
        title_search = T('Search Sent SMS'),
        #subtitle_create = T('Send SMS'),
        subtitle_list = T('Sent SMS'),
        label_list_button = VIEW_SENT_SMS,
        #label_create_button = T('Send SMS'),
        #msg_record_created = T('SMS created'),
        #msg_record_modified = T('SMS updated'),
        msg_record_deleted = T('SMS deleted'),
        msg_list_empty = T('No SMS\'s currently in Sent'))

    # Incoming Email
    resource = 'email_inbox'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('sender', notnull=True),
                    Field('subject', length=78),    # RFC 2822
                    Field('body', 'text'),
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % tablename)
    table.sender.requires = IS_EMAIL()
    table.sender.label = T('Sender')
    #table.sender.comment = SPAN("*", _class="req")
    table.subject.label = T('Subject')
    table.body.label = T('Body')
    VIEW_EMAIL_INBOX = T('View Email InBox')
    s3.crud_strings[tablename] = Storage(
        #title_create = T('Add Incoming Email'),
        title_display = T('Email Details'),
        title_list = VIEW_EMAIL_INBOX,
        #title_update = T('Edit Email'),
        title_search = T('Search Email InBox'),
        subtitle_list = T('Email InBox'),
        label_list_button = VIEW_EMAIL_INBOX,
        #label_create_button = T('Add Incoming Email'),
        #msg_record_created = T('Email added'),
        #msg_record_modified = T('Email updated'),
        msg_record_deleted = T('Email deleted'),
        msg_list_empty = T('No Emails currently in InBox'))

    # Outgoing Email
    resource = 'email_outbox'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, authorstamp, uuidstamp, deletion_status,
                    #Field('recipient', notnull=True),
                    msg_group_id,
                    Field('subject', length=78),    # RFC 2822
                    Field('body', 'text'),
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % tablename)
    #table.recipient.requires = IS_EMAIL()
    #table.recipient.comment = SPAN("*", _class="req")
    table.msg_group_id.label = T('Recipients')
    table.subject.label = T('Subject')
    table.body.label = T('Body')
    SEND_EMAIL = T('Send Email')
    VIEW_EMAIL_OUTBOX = T('View Email OutBox')
    s3.crud_strings[tablename] = Storage(
        title_create = SEND_EMAIL,
        title_display = T('Email Details'),
        title_list = VIEW_EMAIL_OUTBOX,
        title_update = T('Edit Email'),
        title_search = T('Search Email OutBox'),
        subtitle_create = SEND_EMAIL,
        subtitle_list = T('Email OutBox'),
        label_list_button = VIEW_EMAIL_OUTBOX,
        label_create_button = T('Send Email'),
        msg_record_created = T('Email created'),
        msg_record_modified = T('Email updated'),
        msg_record_deleted = T('Email deleted'),
        msg_list_empty = T('No Emails currently in OutBox'))

    resource = 'email_sent'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, authorstamp, uuidstamp, deletion_status,
                    #Field('recipient', notnull=True),
                    msg_group_id,
                    Field('subject', length=78),    # RFC 2822
                    Field('body', 'text'),
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % tablename)
    #table.recipient.requires = IS_EMAIL()
    #table.recipient.comment = SPAN("*", _class="req")
    table.msg_group_id.label = T('Recipients')
    table.subject.label = T('Subject')
    table.body.label = T('Body')
    VIEW_SENT_EMAIL = T('View Sent Email')
    s3.crud_strings[tablename] = Storage(
        #title_create = T('Send Email'),
        title_display = T('Email Details'),
        title_list = VIEW_SENT_EMAIL,
        #title_update = T('Edit Email'),
        title_search = T('Search Sent Email'),
        #subtitle_create = T('Send Email'),
        subtitle_list = T('Sent Email'),
        label_list_button = VIEW_SENT_EMAIL,
        #label_create_button = T('Send Email'),
        #msg_record_created = T('Email created'),
        #msg_record_modified = T('Email updated'),
        msg_record_deleted = T('Email deleted'),
        msg_list_empty = T('No Emails currently in Sent'))

