# -*- coding: utf-8 -*-

module = 'pe'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                db.Field('audit_read', 'boolean'),
                db.Field('audit_write', 'boolean'),
                migrate = migrate)
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read = False,
        audit_write = False
    )

# Person Entity
resource = 'entity'
table = module + '_' + resource
db.define_table(table, uuidstamp,
                db.Field('opt_type'),
                db.Field('members', 'integer'),
                migrate = migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, 'pe_entity.uuid')
db[table].opt_type.requires = IS_IN_SET(['group','individual'])
db[table].members.requires = IS_NOT_EMPTY()
title_create = T('Add Person Entity')
title_display = T('Person Entities')
title_list = T('List Person Entities')
title_update = T('Edit Person Entities')
title_search = T('Search Person Entities')
subtitle_create = T('Add New Person Entity')
subtitle_list = T('Person Entities')
label_list_button = T('List Person Entities')
label_create_button = T('Add Person Entity')
msg_record_created = T('Person Entity added')
msg_record_modified = T('Person Entity updated')
msg_record_deleted = T('Person Entity deleted')
msg_list_empty = T('No Person Entities currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Association
resource = 'association'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                db.Field('pe1_id', db.pe_entity),
                db.Field('pe2_id', db.pe_entity),
                db.Field('name', length = 256),
                db.Field('valid_from', 'date'),
                db.Field('valid_till', 'date'),
                migrate = migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].pe1_id.requires = IS_IN_DB(db, 'pe_entity.uuid')
db[table].pe2_id.requires = IS_IN_DB(db, 'pe_entity.uuid')
db[table].name.requires = IS_NOT_EMPTY()
db[table].name.comment = SPAN("*", _class="req")
db[table].valid_from.requires = IS_DATE(T("%Y-%m-%d")) # Can use Translation to provide localised formatting
db[table].valid_till.requires = IS_DATE(T("%Y-%m-%d")) # Can use Translation to provide localised formatting
title_create = T('Add Person Entity Association')
title_display = T('Person Entity Associations')
title_list = T('List Person Entity Associations')
title_update = T('Edit Person Entity Associations')
title_search = T('Search Person Entity Associations')
subtitle_create = T('Add New Person Entity Association')
subtitle_list = T('Person Entity Associations')
label_list_button = T('List Person Entity Associations')
label_create_button = T('Add Person Entity Association')
msg_record_created = T('Person Entity Association added')
msg_record_modified = T('Person Entity Association updated')
msg_record_deleted = T('Person Entity Association deleted')
msg_list_empty = T('No Person Entity Associations currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Contact Type
resource = 'contact_type'
table = module+ '_' +resource
db.define_table(table,
                db.Field('description'),
                migrate = migrate)
db[table].description.requires = IS_NOT_IN_DB(db, '%s.description' % table)
# Populate table with required options
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        description = 'Email'
    )
   db[table].insert(
        description = 'phone'
    )
   db[table].insert(
        description = 'fax'
    )
   db[table].insert(
        description = 'other'
    )
title_create=T('Add Contact Type')
title_display = T('Contact Types')
title_list=T('List Contact Types')
title_update=T('Edit Contact Types')
title_search=T('Search Contact Types')
subtitle_create=T('Add New Contact Type')
subtitle_list=T('Contact Types')
label_list_button = T('List Contact Types')
label_create_button = T('Add Contact Type')
msg_record_created = T('Contact Type added')
msg_record_modified = T('Contact Type updated')
msg_record_deleted = T('Contact Type deleted')
msg_list_empty = T('No Contact Types currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Contact
resource = 'contact'
table=module+ '_' +resource
db.define_table(table, timestamp, uuidstamp,
                db.Field('opt_type', db.pe_contact_type),   # Contact type
                db.Field('value'),
                migrate = migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].opt_type.requires = IS_IN_DB(db, 'pe_contact_type.description')
db[table].value.requires = IS_NOT_EMPTY()
db[table].value.comment = SPAN("*", _class="req")
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
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Contacts to Person Entity
resource = 'contact_to_pe'
table = module+ '_' +resource
db.define_table(table, timestamp,
                db.Field('pe_id', db.pe_entity),
                db.Field('contact_id', db.pe_contact),
                migrate = migrate)
db[table].pe_id.label = 'Person Entity'
db[table].pe_id.requires = IS_IN_DB(db, 'pe_pe_entity.pe_id')
db[table].contact_id.requires = IS_IN_DB(db, 'pe_contact.id')
db[table].contact_id.label = 'Contact Detail'

# Individual Type
resource = 'individual_type'
table = module+ '_' +resource
db.define_table(table,
                db.Field('description'),
                migrate = migrate)
db[table].description.requires = IS_NOT_IN_DB(db, '%s.description' % table)
if not len(db().select(db[table].ALL)):
   db[table].insert(
        description = 'relief worker'
    )
   db[table].insert(
        description = 'victim'
    )
   db[table].insert(
        description = 'administrator'
    )
   db[table].insert(
        description = 'user'
    )
title_create = T('Add Individual Type')
title_display = T('Individual Types')
title_list = T('List Individual Types')
title_update = T('Edit Individual Types')
title_search = T('Search Individual Types')
subtitle_create = T('Add New Individual Type')
subtitle_list = T('Individual Types')
label_list_button = T('List Individual Types')
label_create_button = T('Add Individual Type')
msg_record_created = T('Individual Type added')
msg_record_modified = T('Individual Type updated')
msg_record_deleted = T('Individual Type deleted')
msg_list_empty = T('No Individual Types currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Individual
resource = 'individual'
table = module+ '_' +resource
db.define_table(table, timestamp, uuidstamp,   # Person Entity
                db.Field('opt_status_type', db.pe_individual_type),
                migrate = migrate)
db[table].opt_status_type.requires = IS_IN_DB(db, 'pe_individual_type.id', '%(id)s: %(description)s')
db[table].opt_status_type.comment = DIV(A(T('Add Name'), _class='popup', _href=URL(r=request, c='pe', f='name', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Name|The Individual's Name")))
title_create = T('Add Individual Detail')
title_display = T('Individual Details')
title_list = T('List Individual Details')
title_update = T('Edit Individual Detail')
title_search = T('Search Individual Details')
subtitle_create = T('Add New Individual Detail')
subtitle_list = T('Individual Details')
label_list_button = T('List Individual Details')
label_create_button = T('Add Individual Detail')
msg_record_created = T('Individual Detail added')
msg_record_modified = T('Individual Detail updated')
msg_record_deleted = T('Individual Detail deleted')
msg_list_empty = T('No Individual Details currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Individual Identity Type
resource = 'identity_type'
table = module+ '_' +resource
db.define_table(table,
                db.Field('description'),
                migrate = migrate)
db[table].description.requires = IS_NOT_IN_DB(db, '%s.description' % table)

if not len(db().select(db[table].ALL)):
   db[table].insert(
        description = 'Passport'
    )
   db[table].insert(
        description = 'VoterID'
    )
   db[table].insert(
        description = 'Driving License'
    )
   db[table].insert(
        description = 'Social Security Number'
    )
# Individual Identity
# Modules: dvr, mpr
resource = 'individual_identity'
table = module+ '_' +resource
db.define_table(table, timestamp,
                db.Field('pe_id', length = 64),
                db.Field('opt_id_type', db.pe_identity_type),       # ID card, Passport, Driving License, etc
                db.Field('id_value'),
                migrate = migrate)
db[table].pe_id.requires = IS_IN_DB(db, 'pe_individual.uuid')
db[table].opt_id_type.requires = IS_IN_DB(db, 'pe_identity_type.description')

# Individual Name Type
resource = 'name_type'
table = module+ '_' +resource
db.define_table(table,
                db.Field('description'),
                migrate = migrate)
db[table].description.requires = IS_NOT_IN_DB(db, '%s.description' % table)
if not len(db().select(db[table].ALL)):
   db[table].insert(
        description = 'First Name'
    )
   db[table].insert(
        description = 'Middle Name'
    )
   db[table].insert(
        description = 'Last Name'
    )
   db[table].insert(
        description = 'Preffered Name'
    )

# Individual Name
# Modules: cr, dvr, mpr
resource = 'individual_name'
table = module+ '_' +resource
db.define_table(table, timestamp,
                db.Field('pe_id', length = 64),
                db.Field('opt_name_type', db.pe_name_type),
                db.Field('name'),
                migrate = migrate)
db[table].pe_id.requires = IS_IN_DB(db, 'pe_individual.uuid')
db[table].opt_name_type.requires = IS_IN_DB(db, 'pe_name_type.description')
db[table].name.comment = DIV(A(T('Add Identity'), _class='popup', _href=URL(r=request, c='pe', f='identity', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Name|The Individual's Name")))


# Group Type
resource = 'group_type'
table=module+ '_' +resource
db.define_table(table,
                db.Field('description'),
                migrate = migrate)
db[table].description.requires=IS_NOT_IN_DB(db, '%s.description' % table)
if not len(db().select(db[table].ALL)):
   db[table].insert(
        description = 'family'
    )
   db[table].insert(
        description = 'team'
    )
   db[table].insert(
        description = 'friends'
    )
   db[table].insert(
        description = 'tourists'
    )
    
# Person Group
# Modules: dvr, mpr
resource = 'group'
table = module+ '_' +resource
db.define_table(table, timestamp, uuidstamp,
                db.Field('name'),
                db.Field('opt_group_type', db.pe_group_type),
                db.Field('no_of_adult_males', 'integer'),
                db.Field('no_of_adult_females', 'integer'),
                db.Field('no_of_children_males', 'integer'),
                db.Field('no_of_children_females', 'integer'),
                db.Field('comments', length = 256),
                migrate = migrate)
db[table].opt_group_type.requires = IS_IN_DB(db, 'pe_group_type.description')

# Reusable field
individual_id = SQLTable(None, 'individual_id',
            db.Field('individual_id', db.pe_individual_name,
                requires = IS_NULL_OR(IS_IN_DB(db,'pe_individual_name.pe_id','%(pe_id)s: %(name)s')),
                represent = lambda id: (id and [db(db.pe_individual_name.pe_id==id & db.pe_individual_name.opt_name_type=='First Name').select()[0].name] or ["None"])[0],
                comment = DIV(A(T('Add Contact'), _class='popup', _href=URL(r=request, c='pe', f='contact', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Contact|The Individual to contact for this."))),
                ondelete = 'RESTRICT'
                ))
