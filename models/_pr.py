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


# Persons
# Modules: cr,dvr,mpr
db.define_table('person',
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('full_name'),
                SQLField('family_name'),
                SQLField('l10_name'))
db.person.represent=lambda table:shn_list_item(table,resource='person',action='display',display='table.full_name')
db.person.exposes=['full_name','family_name','l10_name']
db.person.displays=['full_name','family_name','l10_name']
db.person.full_name.requires=IS_NOT_EMPTY()

# Person Contacts
# Modules: cr,dvr,mpr
db.define_table('person_contact',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('opt_contact_type'),	# mobile, home phone, email, IM, etc
                SQLField('contact_value'))
db.person_contact.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person Identity
# Modules: dvr,mpr
db.define_table('person_identity',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('opt_id_type'),		# ID card, Passport, Driving License, etc
                SQLField('id_value'))
db.person_identity.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person Details
# Modules: cr,dvr,mpr
db.define_table('person_details',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
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
db.person_details.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')
db.person_details.next_kin.requires=IS_IN_DB(db,'person.uuid','person.full_name')
db.person_details.birth_date.requires=IS_DATE(T("%Y-%m-%d")) # Can use Translation to provide localised formatting

# Person Status
# Modules: dvr,mpr
db.define_table('person_status',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('isReliefWorker','boolean',default=False),
                SQLField('isVictim','boolean',default=True),
                SQLField('opt_status'),	# missing, injured, etc. customizable
                SQLField('id_value'))
db.person_status.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person Physical
# Modules: dvr,mpr
db.define_table('person_physical',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('height'),
                SQLField('weight'),
                SQLField('opt_blood_type'),
                SQLField('opt_eye_color'),
                SQLField('opt_skin_color'),
                SQLField('opt_hair_color'),
                SQLField('injuries'),
                SQLField('comments',length=256))
db.person_physical.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person Missing
# Modules: dvr,mpr
db.define_table('person_missing',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('last_seen'),
                SQLField('last_clothing'),
                SQLField('comments',length=256))
db.person_missing.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person Deceased
# Modules: dvr,mpr
db.define_table('person_deceased',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('details'),
                SQLField('date_of_death','date'),
                SQLField('place_of_death'),
                SQLField('comments',length=256))
db.person_deceased.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person Reporter
# (The person who reported about this person)
# Modules: dvr,mpr
db.define_table('person_report',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('reporter',length=64),
                SQLField('relation'))
db.person_report.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')
db.person_report.reporter.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person Group
# Modules: dvr,mpr
db.define_table('person_group',
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('opt_group_type'))

# Person Group Details
# Modules: dvr,mpr
db.define_table('person_group_details',
                SQLField('modified_on','datetime',default=now),
                SQLField('person_group',length=64),
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
db.person_group_details.person_group.requires=IS_IN_DB(db,'person_group.uuid')
db.person_group_details.head.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person to Group
# (A person can belong to multiple groups)
# Modules: dvr,mpr
db.define_table('person_to_group',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('person_group',length=64))
db.person_to_group.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')
db.person_to_group.person_group.requires=IS_IN_DB(db,'person_group.uuid')
