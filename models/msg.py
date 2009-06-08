module = 'msg'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                db.Field('audit_read', 'boolean'),
                db.Field('audit_write', 'boolean'),
                migrate=migrate)
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read = False,
        audit_write = False
    )

# incoming SMS's
resource = 'incoming_sms'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                db.Field('phone', 'integer'),
                db.Field('contents', 'text'),
                db.Field('smsc', 'integer'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].phone.label = T("Phone number")
db[table].phone.comment = SPAN("*", _class="req")
title_create = T('Add Incoming SMS')
title_display = T('Incoming SMS Details')
title_list = T('List Incoming SMS\'s')
title_update = T('Edit Incoming SMS')
title_search = T('Search Incoming SMS\'s')
subtitle_create = T('Add New Incoming SMS')
subtitle_list = T('Incoming SMS\'s')
label_list_button = T('List Incoming SMS\'s')
label_create_button = T('Add Incoming SMS')
msg_record_created = T('Incoming SMS added')
msg_record_modified = T('Incoming SMS updated')
msg_record_deleted = T('Incoming SMS deleted')
msg_list_empty = T('No Incoming SMS\'s currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

#outgoing SMS's
resource = 'outgoing_sms'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                db.Field('phone', 'integer'),
                db.Field('contents', 'text'),
                db.Field('status'),
                db.Field('smsc', 'integer'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].phone.label = T("Phone number")
db[table].phone.comment = SPAN("*", _class="req")
title_create = T('Add Outgoing SMS')
title_display = T('Outgoing SMS Details')
title_list = T('List Outgoing SMS\'s')
title_update = T('Edit Outgoing SMS')
title_search = T('Search Outgoing SMS\'s')
subtitle_create = T('Add New Outgoing SMS')
subtitle_list = T('Outgoing SMS\'s')
label_list_button = T('List Outgoing SMS\'s')
label_create_button = T('Add Outgoing SMS')
msg_record_created = T('Outgoing SMS added')
msg_record_modified = T('Outgoing SMS updated')
msg_record_deleted = T('Outgoing SMS deleted')
msg_list_empty = T('No Outgoing SMS\'s currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
