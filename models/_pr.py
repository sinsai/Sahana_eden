module='pr'

# Menu Options
db.define_table('%s_menu_option' % module,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db['%s_menu_option' % module].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s_menu_option.name' % module)]
db['%s_menu_option' % module].name.requires=IS_NOT_EMPTY()
db['%s_menu_option' % module].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s_menu_option.priority' % module)]
if not len(db().select(db['%s_menu_option' % module].ALL)):
	table='%s_menu_option' % module
	
	db['%s' % table].insert(
        name="Home",
	function="index",
	priority=0,
	description="Home",
	enabled='True'
	)
	db['%s' % table].insert(
        name="Add Person",
	function="person/create",
	priority=1,
	description="",
	enabled='True'
	)
	db['%s' % table].insert(
        name="List People",
	function="person",
	priority=2,
	description="",
	enabled='True'
	)

# People
# Modules: cr,dvr,mpr
resource='person'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('full_name'),
                SQLField('family_name'),
                SQLField('l10_name'))
db['%s' % table].represent=lambda table:shn_list_item(table,resource='person',action='display',display='table.full_name')
db['%s' % table].exposes=['full_name','family_name','l10_name']
db['%s' % table].displays=['full_name','family_name','l10_name']
db['%s' % table].full_name.requires=IS_NOT_EMPTY()
title_create=T('Add Person')
title_display=T('Person Details')
title_list=T('List People')
title_update=T('Edit Person')
subtitle_create=T('Add New Person')
subtitle_list=T('People')
label_list_button=T('List People')
label_create_button=T('Add Person')
msg_record_created=T('Person added')
msg_record_modified=T('Person updated')
msg_record_deleted=T('Person deleted')
msg_list_empty=T('No People currently registered')
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
            
# Person Contacts
# Modules: cr,dvr,mpr
resource='person_contact'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('pr_person',length=64),
                SQLField('opt_contact_type'),	# mobile, home phone, email, IM, etc
                SQLField('contact_value'))
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.full_name')

# Person Identity
# Modules: dvr,mpr
resource='person_identity'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('pr_person',length=64),
                SQLField('opt_id_type'),		# ID card, Passport, Driving License, etc
                SQLField('id_value'))
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.full_name')

# Person Details
# Modules: cr,dvr,mpr
resource='person_details'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('pr_person',length=64),
                SQLField('next_kin',length=64),
                SQLField('birth_date','date'),
                SQLField('opt_age_group'),
                SQLField('relation'),
                SQLField('opt_country'),
                SQLField('opt_race'),
                SQLField('opt_religion'),
                SQLField('opt_marital_status'),
                SQLField('opt_gender'),
                SQLField('occupation'))
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.full_name')
db['%s' % table].next_kin.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.full_name')
db['%s' % table].birth_date.requires=IS_DATE(T("%Y-%m-%d")) # Can use Translation to provide localised formatting

# Person Status
# Modules: dvr,mpr
resource='person_status'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('pr_person',length=64),
                SQLField('isReliefWorker','boolean',default=False),
                SQLField('isVictim','boolean',default=True),
                SQLField('opt_status'),	# missing, injured, etc. customizable
                SQLField('id_value'))
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.full_name')

# Person Physical
# Modules: dvr,mpr
resource='person_physical'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('pr_person',length=64),
                SQLField('height'),
                SQLField('weight'),
                SQLField('opt_blood_type'),
                SQLField('opt_eye_color'),
                SQLField('opt_skin_color'),
                SQLField('opt_hair_color'),
                SQLField('injuries'),
                SQLField('comments',length=256))
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.full_name')

# Person Missing
# Modules: dvr,mpr
resource='person_missing'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('pr_person',length=64),
                SQLField('last_seen'),
                SQLField('last_clothing'),
                SQLField('comments',length=256))
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.full_name')

# Person Deceased
# Modules: dvr,mpr
resource='person_deceased'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('pr_person',length=64),
                SQLField('details'),
                SQLField('date_of_death','date'),
                SQLField('place_of_death'),
                SQLField('comments',length=256))
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.full_name')

# Person Reporter
# (The pr_person who reported about this pr_person)
# Modules: dvr,mpr
resource='person_report'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('pr_person',length=64),
                SQLField('reporter',length=64),
                SQLField('relation'))
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.full_name')
db['%s' % table].reporter.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.full_name')

# Person Group
# Modules: dvr,mpr
resource='person_group'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('opt_group_type'))

# Person Group Details
# Modules: dvr,mpr
resource='person_group_details'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('pr_person_group',length=64),
                SQLField('head',length=64),
                SQLField('no_of_adult_males','integer'),
                SQLField('no_of_adult_females','integer'),
                SQLField('no_of_children','integer'),
                SQLField('no_displaced','integer'),
                SQLField('no_missing','integer'),
                SQLField('no_dead','integer'),
                SQLField('no_rehabilitated','integer'),
                SQLField('checklist'),
                SQLField('description',length=256))
db['%s' % table].pr_person_group.requires=IS_IN_DB(db,'pr_person_group.uuid')
db['%s' % table].head.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.full_name')

# Person to Group
# (A pr_person can belong to multiple groups)
# Modules: dvr,mpr
resource='person_to_group'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('pr_person',length=64),
                SQLField('pr_person_group',length=64))
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.full_name')
db['%s' % table].pr_person_group.requires=IS_IN_DB(db,'pr_person_group.uuid')
