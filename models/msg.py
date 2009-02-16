module='msg'

# Menu Options
table='%s_menu_option' % module
db.define_table(table,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('access',db.auth_group),  # Hide menu options if users don't have the required access level
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db[table].name.requires=IS_NOT_IN_DB(db,'%s.name' % table)
db[table].function.requires=IS_NOT_EMPTY()
db[table].access.requires=IS_NULL_OR(IS_IN_DB(db,'auth_group.id','auth_group.role'))
db[table].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.priority' % table)]
if not len(db().select(db[table].ALL)):
	db[table].insert(
        name="Home",
	function="index",
	priority=0,
	description="Home",
	enabled='True'
	)
	db[table].insert(
        name="Send SMS",
	function="outgoing_sms/create",
	priority=1,
	description="Send an SMS to a user or group",
	enabled='True'
	)
	db[table].insert(
        name="List Received SMS's",
	function="incoming_sms",
	priority=2,
	description="List received and incoming SMS's",
	enabled='True'
	)
	db[table].insert(
        name="List Sent SMS's",
	function="outgoing_sms",
	priority=2,
	description="List received and incoming SMS's",
	enabled='True'
	)
	db[table].insert(
        name="Search SMS's",
	function="message/search",
	priority=3,
	description="Search received and sent SMS's",
	enabled='True'
	)

# Settings
resource='setting'
table=module+'_'+resource
db.define_table(table,
                SQLField('audit_read','boolean'),
                SQLField('audit_write','boolean'))
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read=False,
        audit_write=False
    )

# incoming SMS's
resource='incoming_sms'
table=module+'_'+resource
db.define_table(table,timestamp,uuidstamp,
                SQLField('phone','integer'),
                SQLField('contents','text'),
                SQLField('smsc','integer'))
db[table].uuid.requires=IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].phone.label=T("Phone number")
db[table].phone.comment=SPAN("*",_class="req")
title_create=T('Add Incoming SMS')
title_display=T('Incoming SMS Details')
title_list=T('List Incoming SMS\'s')
title_update=T('Edit Incoming SMS')
title_search=T('Search Incoming SMS\'s')
subtitle_create=T('Add New Incoming SMS')
subtitle_list=T('Incoming SMS\'s')
label_list_button=T('List Incoming SMS\'s')
label_create_button=T('Add Incoming SMS')
msg_record_created=T('Incoming SMS added')
msg_record_modified=T('Incoming SMS updated')
msg_record_deleted=T('Incoming SMS deleted')
msg_list_empty=T('No Incoming SMS\'s currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

#outgoing SMS's
resource='outgoing_sms'
table=module+'_'+resource
db.define_table(table,timestamp,uuidstamp,
                SQLField('phone','integer'),
                SQLField('contents','text'),
                SQLField('status'),
                SQLField('smsc','integer'))
db[table].uuid.requires=IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].phone.label=T("Phone number")
db[table].phone.comment=SPAN("*",_class="req")
title_create=T('Add Outgoing SMS')
title_display=T('Outgoing SMS Details')
title_list=T('List Outgoing SMS\'s')
title_update=T('Edit Outgoing SMS')
title_search=T('Search Outgoing SMS\'s')
subtitle_create=T('Add New Outgoing SMS')
subtitle_list=T('Outgoing SMS\'s')
label_list_button=T('List Outgoing SMS\'s')
label_create_button=T('Add Outgoing SMS')
msg_record_created=T('Outgoing SMS added')
msg_record_modified=T('Outgoing SMS updated')
msg_record_deleted=T('Outgoing SMS deleted')
msg_list_empty=T('No Outgoing SMS\'s currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
