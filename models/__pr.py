module='pr'

# Menu Options
table='%s_menu_option' % module
db.define_table(table,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('access',db.t2_group),  # Hide menu options if users don't have the required access level
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db[table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name' % table)]
db[table].function.requires=IS_NOT_EMPTY()
db[table].access.requires=IS_NULL_OR(IS_IN_DB(db,'t2_group.id','t2_group.name'))
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
        name="Add Person",
	function="person/create",
	priority=1,
	enabled='True'
	)
	db[table].insert(
        name="List People",
	function="person",
	priority=2,
	enabled='True'
	)
	db[table].insert(
        name="Search People",
	function="person/search",
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

# People
resource='person'
table=module+'_'+resource
db.define_table(table,timestamp,uuidstamp,
                SQLField('name'),       # Known As (could be Full Name)
                SQLField('first_name'),
                SQLField('last_name'),  # Family Name
                #SQLField('l10_name'),
                SQLField('email'),      # Needed for AAA
                SQLField('mobile_phone'),     # Needed for SMS
                SQLField('address','text'),
                SQLField('postcode'),
                SQLField('website'))
exec("s3.crud_fields.%s=['name','first_name','last_name','email','mobile_phone','address','postcode','website']" % table)
db[table].exposes=s3.crud_fields[table]
db[table].uuid.requires=IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires=IS_NOT_EMPTY()   # People don't have to have unique names
#db[table].name.label=T("Full Name")
db[table].name.comment=SPAN("*",_class="req")
db[table].last_name.label=T("Family Name")
db[table].email.requires=IS_NOT_IN_DB(db,'%s.email' % table)     # Needs to be unique as used for AAA
db[table].email.requires=IS_NULL_OR(IS_EMAIL())
db[table].email.comment=A(SPAN("[Help]"),_class="tooltip",_title=T("Email|This gets used both for signing-in to the system & for receiving alerts/updates."))
db[table].mobile_phone.requires=IS_NOT_IN_DB(db,'%s.mobile' % table)   # Needs to be unique as used for AAA
db[table].mobile_phone.label=T("Mobile Phone #")
db[table].mobile_phone.comment=A(SPAN("[Help]"),_class="tooltip",_title=T("Mobile Phone No|This gets used both for signing-in to the system & for receiving alerts/updates."))
db[table].website.requires=IS_NULL_OR(IS_URL())
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
exec('s3.crud_strings.%s=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)' % table)
# Reusable field for other tables to reference
person_id=SQLTable(None,'person_id',
            SQLField('person',
                db.pr_person,requires=IS_NULL_OR(IS_IN_DB(db,'pr_person.id','pr_person.name')),
                #represent=lambda id: (id and [db(db.pr_person.id==id).select()[0].name] or ["None"])[0],
                comment=''))
# Unfortunately SQLTABLE can't yet handle:
#represent
# Unfortunately T2 can't yet handle:
#comment

# Contacts
resource='contact'
table=module+'_'+resource
db.define_table(table,timestamp,uuidstamp,
                SQLField('name'),   # Contact type
                SQLField('value'))
db[table].uuid.requires=IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires=IS_IN_SET(['phone','fax','skype','msn','yahoo'])
db[table].value.requires=IS_NOT_EMPTY()
title_create=T('Add Contact Detail')
title_display=T('Contact Details')
title_list=T('List Contact Details')
title_update=T('Edit Contact Detail')
title_search=T('Search Contact Details')
subtitle_create=T('Add New Contact Detail')
subtitle_list=T('Contact Details')
label_list_button=T('List Contact Details')
label_create_button=T('Add Contact Detail')
msg_record_created=T('Contact Detail added')
msg_record_modified=T('Contact Detail updated')
msg_record_deleted=T('Contact Detail deleted')
msg_list_empty=T('No Contact Details currently registered')
exec('s3.crud_strings.%s=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)' % table)

# Contacts to People
resource='contact_to_person'
table=module+'_'+resource
db.define_table(table,timestamp,
                SQLField('contact_id',db.pr_contact),
                SQLField('person_id',db.pr_person))
db[table].contact_id.requires=IS_IN_DB(db,'pr_contact.id','pr_contact.name')
db[table].contact_id.label='Contact'
db[table].person_id.requires=IS_IN_DB(db,'pr_person.id','pr_person.name')
db[table].person_id.label='Person'



# Person Identity
# Modules: dvr,mpr
#resource='person_identity'
#table=module+'_'+resource
#db.define_table(table,timestamp,
#                SQLField('pr_person',length=64),
#                SQLField('opt_id_type'),		# ID card, Passport, Driving License, etc
#                SQLField('id_value'))
#db[table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person Details
# Modules: cr,dvr,mpr
#resource='person_details'
#table=module+'_'+resource
#db.define_table(table,timestamp,
#                SQLField('pr_person',length=64),
#                SQLField('next_kin',length=64),
#                SQLField('birth_date','date'),
#                SQLField('opt_age_group'),
#                SQLField('relation'),
#                SQLField('opt_country'),
#                SQLField('opt_race'),
#                SQLField('opt_religion'),
#                SQLField('opt_marital_status'),
#                SQLField('opt_gender'),
#                SQLField('occupation'))
#db[table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')
#db[table].next_kin.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')
#db[table].birth_date.requires=IS_DATE(T("%Y-%m-%d")) # Can use Translation to provide localised formatting

# Person Status
# Modules: dvr,mpr
#resource='person_status'
#table=module+'_'+resource
#db.define_table(table,timestamp,
#                SQLField('pr_person',length=64),
#                SQLField('isReliefWorker','boolean',default=False),
#                SQLField('isVictim','boolean',default=True),
#                SQLField('opt_status'),	# missing, injured, etc. customizable
#                SQLField('id_value'))
#db[table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person Physical
# Modules: dvr,mpr
#resource='person_physical'
#table=module+'_'+resource
#db.define_table(table,timestamp,
#                SQLField('pr_person',length=64),
#                SQLField('height'),
#                SQLField('weight'),
#                SQLField('opt_blood_type'),
#                SQLField('opt_eye_color'),
#                SQLField('opt_skin_color'),
#                SQLField('opt_hair_color'),
#                SQLField('injuries'),
#                SQLField('comments',length=256))
#db[table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person Missing
# Modules: dvr,mpr
#resource='person_missing'
#table=module+'_'+resource
#db.define_table(table,timestamp,
#                SQLField('pr_person',length=64),
#                SQLField('last_seen'),
#                SQLField('last_clothing'),
#                SQLField('comments',length=256))
#db[table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person Deceased
# Modules: dvr,mpr
#resource='person_deceased'
#table=module+'_'+resource
#db.define_table(table,timestamp,
#                SQLField('pr_person',length=64),
#                SQLField('details'),
#                SQLField('date_of_death','date'),
#                SQLField('place_of_death'),
#                SQLField('comments',length=256))
#db[table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person Reporter
# (The pr_person who reported about this pr_person)
# Modules: dvr,mpr
#resource='person_report'
#table=module+'_'+resource
#db.define_table(table,timestamp,
#                SQLField('pr_person',length=64),
#                SQLField('reporter',length=64),
#                SQLField('relation'))
#db[table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')
#db[table].reporter.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person Group
# Modules: dvr,mpr
#resource='person_group'
#table=module+'_'+resource
#db.define_table(table,timestamp,
#                SQLField('uuid',length=64,default=uuid.uuid4()),
#                SQLField('name'),
#                SQLField('opt_group_type'))

# Person Group Details
# Modules: dvr,mpr
#resource='person_group_details'
#table=module+'_'+resource
#db.define_table(table,timestamp,
#                SQLField('pr_person_group',length=64),
#                SQLField('head',length=64),
#                SQLField('no_of_adult_males','integer'),
#                SQLField('no_of_adult_females','integer'),
#                SQLField('no_of_children','integer'),
#                SQLField('no_displaced','integer'),
#                SQLField('no_missing','integer'),
#                SQLField('no_dead','integer'),
#                SQLField('no_rehabilitated','integer'),
#                SQLField('checklist'),
#                SQLField('description',length=256))
#db[table].pr_person_group.requires=IS_IN_DB(db,'pr_person_group.uuid')
#db[table].head.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person to Group
# (A pr_person can belong to multiple groups)
# Modules: dvr,mpr
#resource='person_to_group'
#table=module+'_'+resource
#db.define_table(table,timestamp,
#                SQLField('pr_person',length=64),
#                SQLField('pr_person_group',length=64))
#db[table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')
#db[table].pr_person_group.requires=IS_IN_DB(db,'pr_person_group.uuid')

