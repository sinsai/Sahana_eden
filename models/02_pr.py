# -*- coding: utf-8 -*-

#
# Sahanapy VITA - Part 02_pr: Person Registry
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
# Option fields ---------------------------------------------------------------
#

#
# Gender ------------------------------
#

pr_person_gender_opts = {
    1:T('unknown'),
    2:T('female'),
    3:T('male')
    }

opt_pr_gender = SQLTable(None, 'opt_pr_gender',
                    db.Field('opt_pr_gender','integer',
                    requires = IS_IN_SET(pr_person_gender_opts),
                    default = 1,
                    label = T('Gender'),
                    represent = lambda opt: opt and pr_person_gender_opts[opt]))

#
# Age Groups --------------------------
#

pr_person_age_group_opts = {
    1:T('unknown'),
    2:T('infant (0-1)'),
    3:T('child (2-11)'),
    4:T('adolescent (12-20)'),
    5:T('adult (21-50)'),
    6:T('senior (50+)')
    }

opt_pr_age_group = SQLTable(None, 'opt_pr_age_group',
                    db.Field('opt_pr_age_group','integer',
                    requires = IS_IN_SET(pr_person_age_group_opts),
                    default = 1,
                    label = T('Age Group'),
                    represent = lambda opt: opt and pr_person_age_group_opts[opt]))

#
# ID Types ----------------------------
#

pr_id_type_opts = {
    1:T('Passport'),
    2:T('National ID Card'),
    3:T('Driving License'),
    4:T('Other')
    }

opt_pr_id_type = SQLTable(None, 'opt_pr_id_type',
                    db.Field('opt_pr_id_type','integer',
                    requires = IS_IN_SET(pr_id_type_opts),
                    default = 1,
                    label = T('ID type'),
                    represent = lambda opt: opt and pr_id_type_opts[opt]))

#
# Group types -------------------------
#
pr_group_type_opts = {
    1:T('Family'),
    2:T('Tourist Group'),
    3:T('Relief Team'),
    4:T('Other')
    }

opt_pr_group_type = SQLTable(None, 'opt_pr_group_type',
                    db.Field('opt_pr_group_type','integer',
                    requires = IS_IN_SET(pr_group_type_opts),
                    default = 4,
                    label = T('Group Type'),
                    represent = lambda opt: opt and pr_group_type_opts[opt]))

#
# PersonEntity classes ----------------
#
pr_pentity_class_opts = {
    1:T('Person'),
    2:T('Group'),
    3:T('Dead Body'),
    4:T('Personal Belongings')
    }

opt_pr_pentity_class = SQLTable(None, 'opt_pr_pentity_class',
                    db.Field('opt_pr_pentity_class','integer',
                    requires = IS_IN_SET(pr_pentity_class_opts),
                    default = 1,
                    represent = lambda opt: opt and pr_pentity_class_opts[opt]))

#
# Tag types ---------------------------
#
pr_tag_type_opts = {
    1:T('None'),
    2:T('Number Tag'),
    3:T('Barcode Label')
    }

opt_pr_tag_type = SQLTable(None, 'opt_pr_tag_type',
                    db.Field('opt_pr_tag_type','integer',
                    requires = IS_IN_SET(pr_tag_type_opts),
                    default = 1,
                    label = T('Tag Type'),
                    represent = lambda opt: opt and pr_tag_type_opts[opt]))

#
# Person-Entity ---------------------------------------------------------------
#
resource = 'pentity'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                opt_pr_pentity_class,               # Entity class
                opt_pr_tag_type,                    # Tag type
                Field('pr_tag_label'),              # Tag Label
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

#
#
#
def shn_pentity_id_represent(pentity_id):
    record = db(db.pr_pentity.id==pentity_id).select()[0]
    if record:
        pr_pentity_type = record.opt_pr_pentity_class
        if pr_pentity_type==1:
            person_record = db(db.pr_person.pentity_id==pentity_id).select()[0]
            return person_record.first_name + " " + person_record.last_name + " (" + record.pr_tag_label + ")"
        elif pr_pentity_type==2:
            group_record = db(db.pr_group.pentity_id==pentity_id).select()[0]
            return group_record.name + " (" + str(pentity_id) + ")"
        else:
            return str(pr_pentity_class_opts[pr_pentity_type]) + ": " + record.pr_tag_label + " (" + str(pentity_id) + ")"
    else:
        return('None')

#
# Reusable field for other tables to reference
#
pentity_id = SQLTable(None, 'pentity_id',
                Field('pentity_id', db.pr_pentity,
                requires = IS_NULL_OR(IS_IN_DB(db, 'pr_pentity.id', '%(pr_tag_label)s (%(id)s)')),
                represent = lambda id: (id and [shn_pentity_id_represent(id)] or ["None ("+str(id)+")"])[0],
#                comment = DIV(A(T('Add Entity'), _class='popup', _href=URL(r=request, c='pr', f='pentity', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Entity|New Personal Presence, Body or Item."))),
                ondelete = 'RESTRICT',
                readable = False,
                writable = False
                ))

#
# Reusable field set for PersonEntity tables
# includes:
#   pentity_id          Person Entity ID      (should be invisible in forms)
#   opt_pr_tag_type     Tag Type
#   pr_tag_label        Tag Label
#
pentity_field_set = SQLTable(None, 'pentity_id',
                    Field('pentity_id', db.pr_pentity,
                    requires = IS_NULL_OR(IS_IN_DB(db, 'pr_pentity.id', '%(id)s (%(pr_tag_label)s)')),
                    represent = lambda id: (id and db(db.pr_pentity.id==id).select()[0].pr_tag_label and [db(db.pr_pentity.id==id).select()[0].pr_tag_label+" ("+str(id)+")"] or ["None ("+str(id)+")"])[0],
#                    comment = DIV(A(T('Add Entity'), _class='popup', _href=URL(r=request, c='pr', f='pentity', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Entity|New Personal Presence, Body or Item."))),
                    ondelete = 'RESTRICT',
                    readable = False,
                    writable = False),
                    opt_pr_tag_type,
                    Field('pr_tag_label', label = T('Tag Label')))

#
# Persons ---------------------------------------------------------------------
#
resource = 'person'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                pentity_field_set,
                Field('first_name', notnull=True),      # first or only name
                Field('middle_name'),                   # middle name
                Field('last_name'),                     # last name
                Field('preferred_name'),                # how the person uses to be called
                opt_pr_gender,
                opt_pr_age_group,
                Field('email', unique=True),            # Needed for AAA (change this!)
                Field('mobile_phone','integer'),        # Needed for SMS (change this!)
                Field('comment'),                       # comment
                migrate=migrate)

#db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].opt_pr_gender.label = T('Gender')
db[table].opt_pr_age_group.label = T('Age group')
#db[table].pentity_id.readable = False
#db[table].pentity_id.writable = False
db[table].first_name.requires = IS_NOT_EMPTY()   # People don't have to have unique names, some just have a single name
db[table].first_name.comment = SPAN("*", _class="req")
#db[table].last_name.label = T("Family Name")
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
db.define_table(table, timestamp, deletion_status,
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
db.define_table(table, timestamp, deletion_status,
                person_id,
                Field('description','text'),
                migrate=migrate)

#
# Missing Person (Sahana legacy)
#
resource = 'person_missing'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                person_id,
                Field('description','text'),
                migrate=migrate)

#
# Deceased Person (Sahana legacy)
#
resource = 'person_deceased'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                person_id,
                Field('description','text'),
                migrate=migrate)

#
# Identities ------------------------------------------------------------------
#

#
# Identity
#
resource = 'identity'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
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
# Group -----------------------------------------------------------------------
#
resource = 'group'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                pentity_field_set,                                # pentity reference
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

# TODO: restrictions and requirements
# TODO: CRUD strings
db[table].opt_pr_tag_type.readable=False
db[table].opt_pr_tag_type.writable=False
db[table].pr_tag_label.readable=False
db[table].pr_tag_label.writable=False

db[table].opt_pr_group_type.label = T("Group type")

db[table].group_name.label = T("Group name")
db[table].group_description.label = T("Group description")
title_create = T('Add Group')
title_display = T('Group Details')
title_list = T('List Groups')
title_update = T('Edit Group')
title_search = T('Search Groups')
subtitle_create = T('Add New Group')
subtitle_list = T('Groups')
label_list_button = T('List Groups')
label_create_button = T('Add Group')
msg_record_created = T('Group added')
msg_record_modified = T('Group updated')
msg_record_deleted = T('Group deleted')
msg_list_empty = T('No Groups currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
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
# Group membership ------------------------------------------------------------
#
resource = 'group_membership'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
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
db.define_table(table, timestamp, uuidstamp, deletion_status,
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
db.define_table(table, timestamp, deletion_status,
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
db.define_table(table, timestamp, uuidstamp, deletion_status,
                person_id,                          # Reference to person
                opt_sn_type,                        # ID type
                Field('comment'))                   # a comment (optional)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

#
# Callback functions ----------------------------------------------------------
#

#
# pentity_ondelete:
# Remove a pentity when the corresponding subclass item gets deleted
#
def shn_pentity_ondelete(record):
    if record.pentity_id:
        del db.pr_pentity[record.pentity_id]
    else:
        #ignore
        pass
    return

#
# pentity_onvalidation:
# Create/update a pentity when a corresponding subclass item gets created/updated
#
def shn_pentity_onvalidation(form, resource=None, entity_class=1):
    if form:
        if len(request.args) == 0 or request.args[0] == 'create':
            # this is a create action either directly or from list view
            if entity_class in pr_pentity_class_opts.keys():
                pentity_id = db['pr_pentity'].insert(
                    opt_pr_pentity_class=entity_class,
                    opt_pr_tag_type=form.vars.opt_pr_tag_type,
                    pr_tag_label=form.vars.pr_tag_label )
                if pentity_id:
                    form.vars.pentity_id = pentity_id
        elif len(request.args) > 0:
            if request.args[0] == 'update' and form.vars.delete_this_record:
                # this is a delete action from update
                if len(request.args) > 1:
                    my_id = request.args[1]
                    if resource:
                        shn_pentity_ondelete(db[resource][my_id])
            elif request.args[0] == 'update':
                if len(request.args) > 1:
                    my_id = request.args[1]
                    if resource:
                        db(db.pr_pentity.id==db[resource][my_id].pentity_id).update(
                            opt_pr_tag_type=form.vars.opt_pr_tag_type,
                            pr_tag_label=form.vars.pr_tag_label)
    return

