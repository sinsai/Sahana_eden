# -*- coding: utf-8 -*-

module = 'msg'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
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
db[table].inbound_mail_type.requires = IS_IN_SET(['imap', 'pop3'])
db[table].inbound_mail_port.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Port|For POP-3 this is usually 110 (995 for SSL), for IMAP this is usually 143 (993 for IMAP)."))
db[table].inbound_mail_delete.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Delete|If this is set to True then mails will be deleted from the server after downloading."))
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        inbound_mail_server = 'imap.gmail.com',
        inbound_mail_type = 'imap',
        inbound_mail_ssl = True,
        inbound_mail_port = '993',
        inbound_mail_username = 'username',
        inbound_mail_password = 'password',
        inbound_mail_delete = False,
        #outbound_mail_server = 'mail:25',
        #outbound_mail_from = 'demo@sahanapy.org',
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read = False,
        audit_write = False
    )

# Status
resource = 'email_inbound_status'
table = module + '_' + resource
db.define_table(table,
                Field('status'),
                migrate=migrate)

# Group
msg_group_type_opts = {
    1:T('Email'),
    2:T('SMS'),
    3:T('Both')
    }
opt_msg_group_type = SQLTable(None, 'opt_msg_group_type',
                    db.Field('group_type', 'integer', notnull=True,
                    requires = IS_IN_SET(msg_group_type_opts),
                    default = 1,
                    label = T('Type'),
                    represent = lambda opt: opt and msg_group_type_opts[opt]))

resource = 'group'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', notnull=True),
                opt_msg_group_type,
                Field('comments'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].comments.label = T('Comments')
title_create = T('Add Group')
title_display = T('Group Details')
title_list = T('List Groups')
title_update = T('Edit Group')
title_search = T('Search Groups')
subtitle_create = T('Add New Group')
subtitle_list = T('Groups')
label_list_button = T('List Groups')
label_create_button = T('Add Group')
msg_record_created = T('Group added')
msg_record_modified = T('Group updated')
msg_record_deleted = T('Group deleted')
msg_list_empty = T('No Groups currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
# Reusable field for other tables to reference
msg_group_id = SQLTable(None, 'msg_group_id',
            Field('msg_group_id', db.msg_group,
                requires = IS_ONE_OF(db, 'msg_group.id', '%(name)s'),
                represent = lambda id: (id and [db(db.msg_group.id==id).select()[0].name] or ["None"])[0],
                label = T('Group'),
                comment = DIV(A(T('Add Group'), _class='thickbox', _href=URL(r=request, c='msg', f='group', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=T('Add Group')), A(SPAN("[Help]"), _class="tooltip", _title=T("Distribution Group|The Group of People to whom this Message should be sent."))),
                ondelete = 'RESTRICT'
                ))

# Group<>User Many2Many
resource = 'group_user'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                Field('msg_group_id', db.msg_group),
                person_id,
                migrate=migrate)
db[table].msg_group_id.requires = IS_ONE_OF(db, 'msg_group.id', '%(name)s')
db[table].msg_group_id.represent = lambda msg_group_id: db(db.msg_group.id==msg_group_id).select()[0].name
db[table].person_id.label = T('User')

# Incoming SMS
resource = 'sms_inbox'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('phone_number', 'integer', notnull=True),
                Field('contents', length=700),  # length=140 omitted to handle multi-part SMS
                #Field('smsc', 'integer'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].phone_number.requires = IS_NOT_EMPTY()
db[table].phone_number.label = T('Phone Number')
#db[table].phone_number.comment = SPAN("*", _class="req")
db[table].contents.label = T('Contents')
#title_create = T('Add Incoming SMS')
title_display = T('SMS Details')
title_list = T('View SMS InBox')
#title_update = T('Edit SMS')
title_search = T('Search SMS InBox')
subtitle_list = T('SMS InBox')
label_list_button = T('View SMS InBox')
#label_create_button = T('Add Incoming SMS')
#msg_record_created = T('SMS added')
#msg_record_modified = T('SMS updated')
msg_record_deleted = T('SMS deleted')
msg_list_empty = T('No SMS\'s currently in InBox')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Outgoing SMS
resource = 'sms_outbox'
table = module + '_' + resource
db.define_table(table, timestamp, authorstamp, uuidstamp, deletion_status,
                #Field('phone_number', 'integer', notnull=True),
                msg_group_id,
                Field('contents', length=700),  # length=140 omitted to handle multi-part SMS
                #Field('smsc', 'integer'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
#db[table].phone_number.requires = IS_NOT_EMPTY()
#db[table].phone_number.comment = SPAN("*", _class="req")
db[table].contents.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Contents|If this is over 140 characters then it will be split into Multiple SMS's."))
db[table].msg_group_id.label = T('Recipients')
db[table].contents.label = T('Contents')
title_create = T('Send SMS')
title_display = T('SMS Details')
title_list = T('View SMS OutBox')
title_update = T('Edit SMS')
title_search = T('Search SMS OutBox')
subtitle_create = T('Send SMS')
subtitle_list = T('SMS OutBox')
label_list_button = T('View SMS OutBox')
label_create_button = T('Send SMS')
msg_record_created = T('SMS created')
msg_record_modified = T('SMS updated')
msg_record_deleted = T('SMS deleted')
msg_list_empty = T('No SMS\'s currently in OutBox')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

resource = 'sms_sent'
table = module + '_' + resource
db.define_table(table, timestamp, authorstamp, uuidstamp, deletion_status,
                #Field('phone_number', 'integer', notnull=True),
                msg_group_id,
                Field('contents', length=700),  # length=140 omitted to handle multi-part SMS
                #Field('smsc', 'integer'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
#db[table].phone_number.requires = IS_NOT_EMPTY()
#db[table].phone_number.comment = SPAN("*", _class="req")
db[table].msg_group_id.label = T('Recipients')
db[table].contents.label = T('Contents')
#title_create = T('Send SMS')
title_display = T('SMS Details')
title_list = T('View Sent SMS')
#title_update = T('Edit SMS')
title_search = T('Search Sent SMS')
#subtitle_create = T('Send SMS')
subtitle_list = T('Sent SMS')
label_list_button = T('View Sent SMS')
#label_create_button = T('Send SMS')
#msg_record_created = T('SMS created')
#msg_record_modified = T('SMS updated')
msg_record_deleted = T('SMS deleted')
msg_list_empty = T('No SMS\'s currently in Sent')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Incoming Email
resource = 'email_inbox'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('sender', notnull=True),
                Field('subject', length=78),    # RFC 2822
                Field('body', 'text'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].sender.requires = IS_EMAIL()
db[table].sender.label = T('Sender')
#db[table].sender.comment = SPAN("*", _class="req")
db[table].subject.label = T('Subject')
db[table].body.label = T('Body')
#title_create = T('Add Incoming Email')
title_display = T('Email Details')
title_list = T('View Email InBox')
#title_update = T('Edit Email')
title_search = T('Search Email InBox')
subtitle_list = T('Email InBox')
label_list_button = T('View Email InBox')
#label_create_button = T('Add Incoming Email')
#msg_record_created = T('Email added')
#msg_record_modified = T('Email updated')
msg_record_deleted = T('Email deleted')
msg_list_empty = T('No Emails currently in InBox')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Outgoing Email
resource = 'email_outbox'
table = module + '_' + resource
db.define_table(table, timestamp, authorstamp, uuidstamp, deletion_status,
                #Field('recipient', notnull=True),
                msg_group_id,
                Field('subject', length=78),    # RFC 2822
                Field('body', 'text'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
#db[table].recipient.requires = IS_EMAIL()
#db[table].recipient.comment = SPAN("*", _class="req")
db[table].msg_group_id.label = T('Recipients')
db[table].subject.label = T('Subject')
db[table].body.label = T('Body')
title_create = T('Send Email')
title_display = T('Email Details')
title_list = T('View Email OutBox')
title_update = T('Edit Email')
title_search = T('Search Email OutBox')
subtitle_create = T('Send Email')
subtitle_list = T('Email OutBox')
label_list_button = T('View Email OutBox')
label_create_button = T('Send Email')
msg_record_created = T('Email created')
msg_record_modified = T('Email updated')
msg_record_deleted = T('Email deleted')
msg_list_empty = T('No Emails currently in OutBox')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

resource = 'email_sent'
table = module + '_' + resource
db.define_table(table, timestamp, authorstamp, uuidstamp, deletion_status,
                #Field('recipient', notnull=True),
                msg_group_id,
                Field('subject', length=78),    # RFC 2822
                Field('body', 'text'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
#db[table].recipient.requires = IS_EMAIL()
#db[table].recipient.comment = SPAN("*", _class="req")
db[table].msg_group_id.label = T('Recipients')
db[table].subject.label = T('Subject')
db[table].body.label = T('Body')
#title_create = T('Send Email')
title_display = T('Email Details')
title_list = T('View Sent Email')
#title_update = T('Edit Email')
title_search = T('Search Sent Email')
#subtitle_create = T('Send Email')
subtitle_list = T('Sent Email')
label_list_button = T('View Sent Email')
#label_create_button = T('Send Email')
#msg_record_created = T('Email created')
#msg_record_modified = T('Email updated')
msg_record_deleted = T('Email deleted')
msg_list_empty = T('No Emails currently in Sent')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

