# -*- coding: utf-8 -*-

#
# Person Registry (VITA)
#
# created 2009-07-15 by nursix
#

module = 'pr'
#
# Settings --------------------------------------------------------------------
#
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read = False,
        audit_write = False
    )

#
# Person Entity ---------------------------------------------------------------
#
resource = 'pentity'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('is_group', 'boolean', default=False),
                migrate=migrate)

# Reusable field for other tables to reference
pentity_id = SQLTable(None, 'pentity_id',
                Field('pentity_id', db.pr_pentity,
                requires = IS_IN_DB(db, 'pr_pentity.id'),
                ondelete = 'RESTRICT'
                ))

#
# Person Entity Status (Sahana legacy)
#
resource = 'pentity_status'
table = module + '_' + resource
db.define_table(table, timestamp,
                pentity_id,
                Field('role'),
                Field('status'),
                migrate=migrate)

#
# Persons ---------------------------------------------------------------------
#
resource='sex'
table=module+'_'+resource
db.define_table(table,
                db.Field('name', notnull=True)
               )
db[table].name.requires=IS_NOT_IN_DB(db, '%s.name' % table)

if not len(db().select(db[table].ALL)):
   db[table].insert(name = "female")
   db[table].insert(name = "male")
   db[table].insert(name = "unknown")

# Reusable field for other tables to reference
opt_pr_sex = SQLTable(None, 'opt_pr_sex',
                    db.Field('opt_pr_sex', db.pr_sex,
                    requires = IS_NULL_OR(IS_IN_DB(db, 'pr_sex.id', 'pr_sex.name')),
                    represent = lambda id: (id and [db(db.pr_sex.id==id).select()[0].name] or ["None"])[0],
                    comment = None,
                    ondelete = 'RESTRICT'
                    ))

resource='age_group'
table=module+'_'+resource
db.define_table(table,
                db.Field('name', notnull=True)
               )
db[table].name.requires=IS_NOT_IN_DB(db, '%s.name' % table)

if not len(db().select(db[table].ALL)):
   db[table].insert(name = "unknown")
   db[table].insert(name = "infant (0-1)")
   db[table].insert(name = "child (2-11)")
   db[table].insert(name = "adolescent (12-20)")
   db[table].insert(name = "adult (21-50)")
   db[table].insert(name = "senior (50+)")

# Reusable field for other tables to reference
opt_pr_age_group = SQLTable(None, 'opt_pr_age_group',
                            db.Field('opt_pr_age_group', db.pr_age_group,
                            requires = IS_NULL_OR(IS_IN_DB(db, 'pr_age_group.id', 'pr_age_group.name')),
                            represent = lambda id: (id and [db(db.pr_age_group.id==id).select()[0].name] or ["None"])[0],
                            comment = None,
                            ondelete = 'RESTRICT'
                            ))

#
# Person
#
resource = 'person'
table = module + '_' + resource
db.define_table(table, timestamp,
                pentity_id,                             # person entity reference
                Field('first_name', notnull=True),      # first or only name
                Field('middle_name'),                   # middle name
                Field('last_name'),                     # last name
                Field('preferred_name'),                # how the person uses to be called
                opt_pr_sex,                             # sex
                opt_pr_age_group,                       # age group
                Field('email', unique=True),            # Needed for AAA (change this!)
                Field('mobile_phone'),                  # Needed for SMS (change this!)
                Field('comment'),                       # comment
                migrate=migrate)

#db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].pentity_id.readable = False
db[table].pentity_id.writable = False
db[table].first_name.requires = IS_NOT_EMPTY()   # People don't have to have unique names, some just have a single name
db[table].first_name.comment = SPAN("*", _class="req")
#db[table].last_name.label = T("Family Name")
db[table].opt_pr_sex.label = T("Sex")
db[table].opt_pr_age_group.label = T("Age Group")
db[table].email.requires = IS_NOT_IN_DB(db, '%s.email' % table)     # Needs to be unique as used for AAA
db[table].email.requires = IS_NULL_OR(IS_EMAIL())
db[table].email.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Email|This gets used both for signing-in to the system & for receiving alerts/updates."))
db[table].mobile_phone.requires = IS_NULL_OR(IS_NOT_IN_DB(db, '%s.mobile_phone' % table))   # Needs to be unique as used for AAA
db[table].mobile_phone.label = T("Mobile Phone #")
db[table].mobile_phone.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Mobile Phone No|This gets used both for signing-in to the system & for receiving alerts/updates."))
#db[table].website.requires = IS_NULL_OR(IS_URL())
title_create = T('Add Person')
title_display = T('Person Details')
title_list = T('List Persons')
title_update = T('Edit Person')
title_search = T('Search Persons')
subtitle_create = T('Add New Person')
subtitle_list = T('Persons')
label_list_button = T('List Persons')
label_create_button = T('Add Person')
msg_record_created = T('Person added')
msg_record_modified = T('Person updated')
msg_record_deleted = T('Person deleted')
msg_list_empty = T('No Persons currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Reusable field for other tables to reference
person_id = SQLTable(None, 'person_id',
                Field('person_id', db.pr_person,
                requires = IS_NULL_OR(IS_IN_DB(db, 'pr_person.id', '%(id)s: %(first_name)s %(last_name)s')),
                represent = lambda id: (id and [db(db.pr_person.id==id).select()[0].first_name] or ["None"])[0],
                comment = DIV(A(T('Add Person'), _class='popup', _href=URL(r=request, c='pr', f='person', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Create Person Entry|Create a person entry in the registry."))),
                ondelete = 'RESTRICT'
                ))

#
# Person Details (Sahana legacy)
#
resource = 'person_details'
table = module + '_' + resource
db.define_table(table, timestamp,
                person_id,
                Field('birth_date','date'),             # Sahana legacy
                Field('country'),                       # Sahana legacy
                Field('race'),                          # Sahana legacy
                Field('religion'),                      # Sahana legacy
                Field('marital_status'),                # Sahana legacy
                Field('occupation'),                    # Sahana legacy
                migrate=migrate)

#
# Person Physical (Sahana legacy)
#
resource = 'person_physical'
table = module + '_' + resource
db.define_table(table, timestamp,
                person_id,
                Field('description','text'),
                migrate=migrate)

#
# Missing Person (Sahana legacy)
#
resource = 'person_missing'
table = module + '_' + resource
db.define_table(table, timestamp,
                person_id,
                Field('description','text'),
                migrate=migrate)

#
# Deceased Person (Sahana legacy)
#
resource = 'person_deceased'
table = module + '_' + resource
db.define_table(table, timestamp,
                person_id,
                Field('description','text'),
                migrate=migrate)

#
# Identities ------------------------------------------------------------------
#
resource='id_type'
table=module+'_'+resource
db.define_table(table,
                db.Field('name', notnull=True)
               )
db[table].name.requires=IS_NOT_IN_DB(db, '%s.name' % table)

if not len(db().select(db[table].ALL)):
   db[table].insert(name = "Passport")
   db[table].insert(name = "National ID Card")
   db[table].insert(name = "Driving License")

# Reusable field for other tables to reference
opt_pr_id_type = SQLTable(None, 'opt_id_type',
                    db.Field('id_type', db.pr_id_type,
                    requires = IS_NULL_OR(IS_IN_DB(db, 'pr_id_type.id', 'pr_id_type.name')),
                    represent = lambda id: (id and [db(db.pr_id_type.id==id).select()[0].name] or ["None"])[0],
                    comment = None,
                    ondelete = 'RESTRICT'
                    ))

#
# Identity
#
resource = 'identity'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                person_id,                          # Reference to person
                opt_pr_id_type,                     # ID type
                Field('value'),                     # ID value
                Field('ia_name'),                   # Name of issuing authority
#                Field('ia_subdivision'),            # Name of issuing authority subdivision
#                Field('ia_code'),                   # Code of issuing authority (if any)
                Field('comment'))                   # a comment (optional)

db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].ia_name.label = T("Issuing Authority")

#
# Groups ----------------------------------------------------------------------
#
resource='group_type'
table=module+'_'+resource
db.define_table(table,
                db.Field('name')
               )
db[table].name.requires=IS_NOT_IN_DB(db, '%s.name' % table)

if not len(db().select(db[table].ALL)):         # TODO: should be refined!
    db[table].insert(name = "Family")
    db[table].insert(name = "Tourists")
    db[table].insert(name = "Other")

# Reusable field for other tables to reference
opt_pr_group_type = SQLTable(None, 'opt_pr_group_type',
                    Field('opt_pr_group_type', db.pr_group_type,
                    requires = IS_NULL_OR(IS_IN_DB(db, 'pr_group_type.id', 'pr_group_type.name')),
                    represent = lambda id: (id and [db(db.pr_group_type.id==id).select()[0].name] or ["None"])[0],
                    comment = None,
                    ondelete = 'RESTRICT'
                    ))

#
# Group
#
resource = 'group'
table = module + '_' + resource
db.define_table(table, timestamp,
                Field('is_group', 'boolean', default=True),     # necessary??
                pentity_id,                                     # pentity reference
                opt_pr_group_type,                              # group type
                Field('group_name'),                            # Group name (optional?)
                Field('group_description'),                     # Group short description
#                Field('group_head'),                           # Sahana legacy
                Field('no_of_adult_males','integer'),           # Sahana legacy
                Field('no_of_adult_females','integer'),         # Sahana legacy
#                Field('no_of_children', 'integer'),            # Sahana legacy
                Field('no_of_children_males','integer'),        # by Khushbu
                Field('no_of_children_females','integer'),      # by Khushbu
#                Field('no_of_displaced', 'integer'),           # Sahana legacy
#                Field('no_of_missing', 'integer'),             # Sahana legacy
#                Field('no_of_dead', 'integer'),                # Sahana legacy
#                Field('no_of_rehabilitated', 'integer'),       # Sahana legacy
#                Field('checklist', 'text'),                    # Sahana legacy
#                Field('description', 'text'),                  # Sahana legacy
                Field('comment'),                               # optional comment
                migrate=migrate)

db[table].opt_pr_group_type.label = T("Group type")
# TODO: restrictions and requirements
db[table].is_group.readable = False
db[table].is_group.writable = False
db[table].pentity_id.readable = False
db[table].pentity_id.writable = False
# TODO: CRUD strings
# TODO: reusable id field
# Reusable field for other tables to reference
group_id = SQLTable(None, 'group_id',
                Field('group_id', db.pr_group,
                requires = IS_NULL_OR(IS_IN_DB(db, 'pr_group.id', '%(id)s: %(group_name)s')),
                represent = lambda id: (id and [db(db.pr_group.id==id).select()[0].group_name] or ["None"])[0],
                comment = DIV(A(T('Add Group'), _class='popup', _href=URL(r=request, c='pr', f='group', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Create Group Entry|Create a group entry in the registry."))),
                ondelete = 'RESTRICT'
                ))
#
# Group members
#
resource = 'group_member'
table = module + '_' + resource
db.define_table(table, timestamp,
                group_id,
                person_id,
                Field('group_head', 'boolean', default=False),
                Field('description'),
                Field('comment'),
                migrate=migrate)

db[table].group_head.represent = lambda group_head: (group_head and ["yes"] or [""])[0]
#
# Contact ---------------------------------------------------------------------
#
resource = 'contact'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('name'),                          # Contact type
                Field('value', notnull=True),
                migrate=migrate)

db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = IS_IN_SET(['phone', 'fax', 'skype', 'msn', 'yahoo'])
db[table].value.requires = IS_NOT_EMPTY()

#
# Contacts to People ----------------------------------------------------------
#
resource = 'contact_to_person'
table = module + '_' + resource
db.define_table(table,timestamp,
                person_id,                              # current, too keep it working
#                pentity_id,                            # future
                Field('contact_id', db.pr_contact),     # modify into reusable field
                migrate=migrate)
db[table].person_id.label = 'Person'
db[table].contact_id.requires = IS_IN_DB(db, 'pr_contact.id', 'pr_contact.name')
db[table].contact_id.label = 'Contact Detail'

#
# Network ---------------------------------------------------------------------
#
resource='sn_type'
table=module+'_'+resource
db.define_table(table,
                db.Field('name')
               )
db[table].name.requires=IS_NOT_IN_DB(db, '%s.name' % table)

if not len(db().select(db[table].ALL)):
    db[table].insert(name = "Family")
    db[table].insert(name = "Friends")
    db[table].insert(name = "Colleagues")

# Reusable field for other tables to reference
opt_sn_type = SQLTable(None, 'opt_sn_type',
                db.Field('network_type', db.pr_sn_type,
                requires = IS_NULL_OR(IS_IN_DB(db, 'pr_sn_type.id', 'pr_sn_type.name')),
                represent = lambda id: (id and [db(db.pr_sn_type.id==id).select()[0].name] or ["None"])[0],
                comment = None,
                ondelete = 'RESTRICT'
                ))

#
# Network
#
resource = 'network'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                person_id,                          # Reference to person
                opt_sn_type,                        # ID type
                Field('comment'))                   # a comment (optional)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

#
# Forms -----------------------------------------------------------------------
#

#
# Callback functions ----------------------------------------------------------
#

#
# Create Person Entity:
#   for on-validation callback in person/create or group/create through
#   RESTlike CRUD controller, creates a person entity as needed
#
def shn_create_pentity(form):
    return