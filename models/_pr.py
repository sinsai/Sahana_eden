module='pr'

# Menu Options
table='%s_menu_option' % module
db.define_table(table,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('access',db.s3_role),  # Hide menu options if users don't have the required access level
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db['%s' % table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name' % table)]
db['%s' % table].function.requires=IS_NOT_EMPTY()
db['%s' % table].access.requires=IS_NULL_OR(IS_IN_DB(db,'s3_role.id','s3_role.name'))
db['%s' % table].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.priority' % table)]
if not len(db().select(db['%s' % table].ALL)):
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
	enabled='True'
	)
	db['%s' % table].insert(
        name="List People",
	function="person",
	priority=2,
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
if not len(db().select(db['%s' % table].ALL)): 
   db['%s' % table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read=False,
        audit_write=False
    )

# People
# Modules: cr,dvr,mpr
resource='person'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('family_name'),
                SQLField('l10_name'))
exec("s3.fields.%s=['name','family_name','l10_name']" % table)
db['%s' % table].exposes=s3.fields['%s' % table]
# Moved to Controller - allows us to redefine for different scenarios (& also better MVC separation)
#db['%s' % table].displays=s3.fields['%s' % table]
# NB Beware of lambdas & %s substitution as they get evaluated when called, not when defined! 
#db['%s' % table].represent=lambda table:shn_list_item(table,resource='person',action='display',display='table.name')
db['%s' % table].name.requires=IS_NOT_EMPTY()
db['%s' % table].name.label=T("Full Name")
db['%s' % table].name.comment=SPAN("*",_class="req")
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
exec('s3.crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % table)
            
# Person Contacts
# Modules: cr,dvr,mpr
resource='person_contact'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('pr_person',length=64),
                SQLField('opt_contact_type'),	# mobile, home phone, email, IM, etc
                SQLField('contact_value'))
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person Identity
# Modules: dvr,mpr
resource='person_identity'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('pr_person',length=64),
                SQLField('opt_id_type'),		# ID card, Passport, Driving License, etc
                SQLField('id_value'))
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')

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
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')
db['%s' % table].next_kin.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')
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
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')

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
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')

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
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')

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
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')

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
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')
db['%s' % table].reporter.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')

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
db['%s' % table].head.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person to Group
# (A pr_person can belong to multiple groups)
# Modules: dvr,mpr
resource='person_to_group'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('pr_person',length=64),
                SQLField('pr_person_group',length=64))
db['%s' % table].pr_person.requires=IS_IN_DB(db,'pr_person.uuid','pr_person.name')
db['%s' % table].pr_person_group.requires=IS_IN_DB(db,'pr_person_group.uuid')
