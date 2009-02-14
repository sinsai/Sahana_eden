module='mpr'

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
        enabled='True')
    db[table].insert(
        name="Search for a Person",
        function="person/search",
        priority=1,
        description="search for a person",
        enabled='True')
    db[table].insert(
        name="Reports",
        function="submenu",
        priority=2,                                                                                                       description="various reports",
        enabled='True')
    db[table].insert(
        name="Report a missing person",
        function="person/create",
        priority=3,                                                                                                            description="report a missing person",
        enabled='True')
    db[table].insert(
        name="Report a found person",
        function="person/update",
        priority=4,                                                                                                             description="report a found person",
        enabled='True')
    db[table].insert(
        name="Reports_end",
        function="submenu/end",
        priority=5,                                                                                                       description="various reports",
        enabled='True')

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

resource='person'
table=module+'_'+resource
db.define_table(table,timestamp,uuidstamp,
    person_id,
    SQLField('last_seen'),
    SQLField('last_clothing'),
    SQLField('comments',length=256))
db[table].person_id.label='Person'
title_create=T('Add Person')
title_display=T('Person Details')
title_list=T('List People')
title_update=T('Edit Person')
title_search=T('Search People')
subtitle_create=T('Add New Person')
subtitle_list=T('People')
label_list_button=T('List People')
label_create_button=T('Add Person')
msg_record_created=T('Person added')
msg_record_modified=T('Person updated')
msg_record_deleted=T('Person deleted')
msg_list_empty=T('No People currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
