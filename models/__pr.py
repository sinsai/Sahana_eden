module = 'pr'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                db.Field('audit_read', 'boolean'),
                db.Field('audit_write', 'boolean'))
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read = False,
        audit_write = False
    )

# People
resource = 'person'
table = module+'_'+resource
db.define_table(table,timestamp,uuidstamp,
                db.Field('first_name'),
                db.Field('last_name'),  # Family Name
                #db.Field('l10_name'),
                db.Field('email'),      # Needed for AAA
                db.Field('mobile_phone'),     # Needed for SMS
                db.Field('address', 'text'),
                db.Field('postcode'),
                db.Field('website'))
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].first_name.requires = IS_NOT_EMPTY()   # People don't have to have unique names, some just have a single name
db[table].first_name.comment = SPAN("*", _class="req")
db[table].last_name.label = T("Family Name")
db[table].email.requires = IS_NOT_IN_DB(db, '%s.email' % table)     # Needs to be unique as used for AAA
db[table].email.requires = IS_NULL_OR(IS_EMAIL())
db[table].email.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Email|This gets used both for signing-in to the system & for receiving alerts/updates."))
db[table].mobile_phone.requires = IS_NULL_OR(IS_NOT_IN_DB(db, '%s.mobile_phone' % table))   # Needs to be unique as used for AAA
db[table].mobile_phone.label = T("Mobile Phone #")
db[table].mobile_phone.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Mobile Phone No|This gets used both for signing-in to the system & for receiving alerts/updates."))
db[table].website.requires = IS_NULL_OR(IS_URL())
title_create = T('Add Person')
title_display = T('Person Details')
title_list = T('List People')
title_update = T('Edit Person')
title_search = T('Search People')
subtitle_create = T('Add New Person')
subtitle_list = T('People')
label_list_button = T('List People')
label_create_button = T('Add Person')
msg_record_created = T('Person added')
msg_record_modified = T('Person updated')
msg_record_deleted = T('Person deleted')
msg_list_empty = T('No People currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
# Reusable field for other tables to reference
person_id = SQLTable(None,'person_id',
            db.Field('person_id',
                db.pr_person,requires = IS_NULL_OR(IS_IN_DB(db, 'pr_person.id', '%(id)s: %(first_name)s %(last_name)s')),
                represent = lambda id: (id and [db(db.pr_person.id==id).select()[0].first_name] or ["None"])[0],
                comment = DIV(A(T('Add Contact'), _class='popup', _href=URL(r=request, c='pr', f='person', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Contact|The Person to contact for this.")))
                ))

# Contacts
resource = 'contact'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                db.Field('name'),   # Contact type
                db.Field('value'))
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = IS_IN_SET(['phone', 'fax', 'skype', 'msn', 'yahoo'])
db[table].value.requires = IS_NOT_EMPTY()
title_create = T('Add Contact Detail')
title_display = T('Contact Details')
title_list = T('List Contact Details')
title_update = T('Edit Contact Detail')
title_search = T('Search Contact Details')
subtitle_create = T('Add New Contact Detail')
subtitle_list = T('Contact Details')
label_list_button = T('List Contact Details')
label_create_button = T('Add Contact Detail')
msg_record_created = T('Contact Detail added')
msg_record_modified = T('Contact Detail updated')
msg_record_deleted = T('Contact Detail deleted')
msg_list_empty = T('No Contact Details currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Contacts to People
resource = 'contact_to_person'
table = module + '_' + resource
db.define_table(table,timestamp,
                db.Field('person_id', db.pr_person),
                db.Field('contact_id', db.pr_contact))
db[table].person_id.label = 'Person'
db[table].contact_id.requires = IS_IN_DB(db, 'pr_contact.id', 'pr_contact.name')
db[table].contact_id.label = 'Contact Detail'


# Person Identity
# Modules: dvr,mpr
#resource = 'person_identity'
#table = module+'_'+resource
#db.define_table(table,timestamp,
#                db.Field('pr_person',length=64),
#                db.Field('opt_id_type'),		# ID card, Passport, Driving License, etc
#                db.Field('id_value'))
#db[table].pr_person.requires = IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person Details
# Modules: cr,dvr,mpr
#resource = 'person_details'
#table = module+'_'+resource
#db.define_table(table,timestamp,
#                db.Field('pr_person',length=64),
#                db.Field('next_kin',length=64),
#                db.Field('birth_date','date'),
#                db.Field('opt_age_group'),
#                db.Field('relation'),
#                db.Field('opt_country'),
#                db.Field('opt_race'),
#                db.Field('opt_religion'),
#                db.Field('opt_marital_status'),
#                db.Field('opt_gender'),
#                db.Field('occupation'))
#db[table].pr_person.requires = IS_IN_DB(db,'pr_person.uuid','pr_person.name')
#db[table].next_kin.requires = IS_IN_DB(db,'pr_person.uuid','pr_person.name')
#db[table].birth_date.requires = IS_DATE(T("%Y-%m-%d")) # Can use Translation to provide localised formatting

# Person Status
# Modules: dvr,mpr
#resource = 'person_status'
#table = module+'_'+resource
#db.define_table(table,timestamp,
#                db.Field('pr_person',length=64),
#                db.Field('isReliefWorker','boolean',default=False),
#                db.Field('isVictim','boolean',default=True),
#                db.Field('opt_status'),	# missing, injured, etc. customizable
#                db.Field('id_value'))
#db[table].pr_person.requires = IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person Physical
# Modules: dvr,mpr
#resource = 'person_physical'
#table = module+'_'+resource
#db.define_table(table,timestamp,
#                db.Field('pr_person',length=64),
#                db.Field('height'),
#                db.Field('weight'),
#                db.Field('opt_blood_type'),
#                db.Field('opt_eye_color'),
#                db.Field('opt_skin_color'),
#                db.Field('opt_hair_color'),
#                db.Field('injuries'),
#                db.Field('comments',length=256))
#db[table].pr_person.requires = IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person Missing
# Modules: dvr,mpr
#resource = 'person_missing'
#table = module+'_'+resource
#db.define_table(table,timestamp,
#                db.Field('pr_person',length=64),
#                db.Field('last_seen'),
#                db.Field('last_clothing'),
#                db.Field('comments',length=256))
#db[table].pr_person.requires = IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person Deceased
# Modules: dvr,mpr
#resource = 'person_deceased'
#table = module+'_'+resource
#db.define_table(table,timestamp,
#                db.Field('pr_person',length=64),
#                db.Field('details'),
#                db.Field('date_of_death','date'),
#                db.Field('place_of_death'),
#                db.Field('comments',length=256))
#db[table].pr_person.requires = IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person Reporter
# (The pr_person who reported about this pr_person)
# Modules: dvr,mpr
#resource = 'person_report'
#table = module+'_'+resource
#db.define_table(table,timestamp,
#                db.Field('pr_person',length=64),
#                db.Field('reporter',length=64),
#                db.Field('relation'))
#db[table].pr_person.requires = IS_IN_DB(db,'pr_person.uuid','pr_person.name')
#db[table].reporter.requires = IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person Group
# Modules: dvr,mpr
#resource = 'person_group'
#table = module+'_'+resource
#db.define_table(table,timestamp,
#                db.Field('uuid',length=64,default=uuid.uuid4()),
#                db.Field('name'),
#                db.Field('opt_group_type'))

# Person Group Details
# Modules: dvr,mpr
#resource = 'person_group_details'
#table = module+'_'+resource
#db.define_table(table,timestamp,
#                db.Field('pr_person_group',length=64),
#                db.Field('head',length=64),
#                db.Field('no_of_adult_males','integer'),
#                db.Field('no_of_adult_females','integer'),
#                db.Field('no_of_children','integer'),
#                db.Field('no_displaced','integer'),
#                db.Field('no_missing','integer'),
#                db.Field('no_dead','integer'),
#                db.Field('no_rehabilitated','integer'),
#                db.Field('checklist'),
#                db.Field('description',length=256))
#db[table].pr_person_group.requires = IS_IN_DB(db,'pr_person_group.uuid')
#db[table].head.requires = IS_IN_DB(db,'pr_person.uuid','pr_person.name')

# Person to Group
# (A pr_person can belong to multiple groups)
# Modules: dvr,mpr
#resource = 'person_to_group'
#table = module+'_'+resource
#db.define_table(table,timestamp,
#                db.Field('pr_person',length=64),
#                db.Field('pr_person_group',length=64))
#db[table].pr_person.requires = IS_IN_DB(db,'pr_person.uuid','pr_person.name')
#db[table].pr_person_group.requires = IS_IN_DB(db,'pr_person_group.uuid')

