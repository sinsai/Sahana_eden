module='dvi'

# Menu Options
table='%s_menu_option' % module
db.define_table(table,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('access',db.auth_group),  # Hide menu options if users don't have the required access level
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db[table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name' % table)]
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
        name="Add Body",
	function="dead_body/create",
	priority=1,
	enabled='True'
	)
	db[table].insert(
        name="List Bodies",
	function="dead_body",
	priority=2,
	enabled='True'
	)
	db[table].insert(
        name="Search Bodies",
	function="dead_body/search",
	priority=3,
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

# Dead bodies
resource='dead_body'
table=module+'_'+resource

db.define_table(table,timestamp,uuidstamp,
                SQLField('tag_label'),      # a unique label
                SQLField('age_group'),      # age group
                SQLField('sex'))            # sex

db[table].uuid.requires=IS_NOT_IN_DB(db,'%s.uuid' % table)

db[table].tag_label.label=T("Tag Label")
db[table].tag_label.requires=IS_NOT_IN_DB(db,'%s.tag_label' % table)
db[table].tag_label.requires=IS_NOT_EMPTY()
db[table].tag_label.comment=SPAN("*",_class="req")

db[table].age_group.label=T("Age Group")
db[table].age_group.requires=IS_NOT_EMPTY()
db[table].age_group.requires=IS_IN_SET(['Infant','Child','Adolescent','Adult','Elderly'])

db[table].sex.label=T("Sex")
db[table].sex.requires=IS_NOT_EMPTY()
db[table].sex.requires=IS_IN_SET(['Unknown','Female','Male'])

title_create=T('Add Dead Body')
title_display=T('Dead Body Details')
title_list=T('List Dead Bodies')
title_update=T('Edit Dead Body')
title_search=T('Search Dead Body')

subtitle_create=T('Add New Entry')
subtitle_list=T('Dead Bodies')

label_list_button=T('List Bodies')
label_create_button=T('Add Body')

msg_record_created=T('Body added')
msg_record_modified=T('Body updated')
msg_record_deleted=T('Body deleted')

msg_list_empty=T('No bodies currently registered')

s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)