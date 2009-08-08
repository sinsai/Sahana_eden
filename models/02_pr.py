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
# Nationalities -----------------------
#

pr_nationality_opts = { # TODO: add all major nationalities
    1:T('unknown'),
    2:T('Germany'),
    3:T('Great Britain'),
    4:T('India')
    }

opt_pr_nationality = SQLTable(None, 'opt_pr_nationality',
                        db.Field('opt_pr_nationality','integer',
                        requires = IS_IN_SET(pr_nationality_opts),
                        default = 1,
                        label = T('Nationality'),
                        represent = lambda opt: opt and pr_nationality_opts[opt]))

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
# PersonEntity classes ----------------
#
pr_pentity_class_opts = {
    1:T('Person'),                  # used in PR  - don't change
    2:T('Group'),                   # used in PR  - don't change
    3:T('Body'),                    # used in HRM - don't change
    4:T('Personal Belongings'),     # used in HRM - don't change
    5:T('Missing Person')           # used in MPR - don't change
    }

opt_pr_pentity_class = SQLTable(None, 'opt_pr_pentity_class',
                    db.Field('opt_pr_pentity_class','integer',
                    requires = IS_IN_SET(pr_pentity_class_opts),
                    default = 1,
                    label = T('Entity Class'),
                    represent = lambda opt: opt and pr_pentity_class_opts[opt]))

#
# Person-Entity ---------------------------------------------------------------
#
# includes:
#   pr_pentity.id                       - Record ID
#   pr_pentity.opt_pr_pentity_class     - Entity Class
#   pr_pentity.label                    - Recognition Label
#
resource = 'pentity'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('parent'),                    # Parent Entity
                opt_pr_pentity_class,               # Entity class
                Field('label', unique=True),        # Recognition Label
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].label.requires = IS_NULL_OR(IS_NOT_IN_DB(db, 'pr_pentity.label'))
db[table].parent.requires = IS_NULL_OR(IS_PE_ID(db, pr_pentity_class_opts))
db[table].parent.label = T('belongs to')
db[table].deleted.readable = True

#
# shn_pentity_represent:
def shn_pentity_represent(pentity):
    if pentity and pentity.opt_pr_pentity_class==1:
        subentity_record=db(db.pr_person.pr_pe_id==pentity.id).select()[0]
        if subentity_record:
            pentity_str = '%s %s [%s] (%s %s)' % (
                subentity_record.first_name,
                subentity_record.last_name or '',
                subentity_record.pr_pe_label or 'no label',
                pr_pentity_class_opts[1],
                subentity_record.id
            )
        else:
            pentity_str = '[%s] (%s PE=%s)' % (
                pentity.label or 'no label',
                pr_pentity_class_opts[1],
                pentity.id
            )
    elif pentity and pentity.opt_pr_pentity_class==2:
        subentity_record=db(db.pr_group.pr_pe_id==pentity.id).select()[0]
        if subentity_record:
            pentity_str = '%s (%s %s)' % (
                subentity_record.group_name,
                pr_pentity_class_opts[2],
                subentity_record.id
            )
        else:
            pentity_str = '(%s PE=%s)' % (
                pr_pentity_class_opts[2],
                pentity.id
            )
    elif pentity and pentity.opt_pr_pentity_class==3:
        subentity_record=db(db.hrm_body.pr_pe_id==pentity.id).select()[0]
        if subentity_record:
            pentity_str = '[%s] (%s %s)' % (
                subentity_record.pr_pe_label or 'no label',
                pr_pentity_class_opts[3],
                subentity_record.id
            )
        else:
            pentity_str = '[%s] (%s PE=%s)' % (
                pentity.label or 'no label',
                pr_pentity_class_opts[3],
                pentity.id
            )
    elif pentity:
        pentity_str = '[%s] (%s PE=%s)' % (
            pentity.label or 'no label',
            pr_pentity_class_opts[pentity.opt_pr_pentity_class],
            pentity.id
        )
    return pentity_str

#
# Person Entity Field Set -------------
#
# for other Person Entity Tables to reference
#
pr_pe_fieldset = SQLTable(None, 'pe_fieldset',
                    Field('pr_pe_id', db.pr_pentity,
                    requires =  IS_NULL_OR(IS_PE_ID(db, pr_pentity_class_opts)),
                    represent = lambda id: (id and [shn_pentity_represent(db(db.pr_pentity.id==id).select()[0])] or ["None"])[0],
                    ondelete = 'RESTRICT',
                    readable = False,   # should be invisible in (most) forms
                    writable = False    # should be invisible in (most) forms
                    ),
                    Field('pr_pe_parent', db.pr_pentity,
                    requires =  IS_NULL_OR(IS_PE_ID(db, pr_pentity_class_opts)),
                    represent =  lambda id: (id and [shn_pentity_represent(db(db.pr_pentity.id==id).select()[0])] or ["None"])[0],
                    ondelete = 'RESTRICT',
                    label = T('belongs to'),
                    readable = False,   # should be invisible in (most) forms
                    writable = False    # should be invisible in (most) forms
                    ),
                    Field('pr_pe_label',
                    label = T('Recognition Label'),
                    requires = IS_NULL_OR(IS_NOT_IN_DB(db, 'pr_pentity.label'))
                    ))

#
# Reusable field for other tables to reference
#
pr_pe_id = SQLTable(None, 'pe_id',
                Field('pr_pe_id', db.pr_pentity,
                requires =  IS_NULL_OR(IS_PE_ID(db, pr_pentity_class_opts)),
                represent = lambda id: (id and [shn_pentity_represent(db(db.pr_pentity.id==id).select()[0])] or ["None"])[0],
                ondelete = 'RESTRICT',
                label = T('Entity ID')
                ))

#
# Person ----------------------------------------------------------------------
#
resource = 'person'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                pr_pe_fieldset,                         # Person Entity Field Set
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

db[table].opt_pr_gender.label = T('Gender')
db[table].opt_pr_age_group.label = T('Age group')
db[table].first_name.requires = IS_NOT_EMPTY()   # People don't have to have unique names, some just have a single name
db[table].first_name.comment = SPAN("*", _class="req")
db[table].email.requires = IS_NOT_IN_DB(db, '%s.email' % table)     # Needs to be unique as used for AAA
db[table].email.requires = IS_NULL_OR(IS_EMAIL())
db[table].email.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Email|This gets used both for signing-in to the system & for receiving alerts/updates."))
db[table].mobile_phone.requires = IS_NULL_OR(IS_NOT_IN_DB(db, '%s.mobile_phone' % table))   # Needs to be unique as used for AAA
db[table].mobile_phone.label = T("Mobile Phone #")
db[table].mobile_phone.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Mobile Phone No|This gets used both for signing-in to the system & for receiving alerts/updates."))
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
# Person Details (Sahana legacy) ----------------------------------------------
#
resource = 'person_details'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                person_id,
                Field('birth_date','date'),             # Sahana legacy
#                Field('country'),                       # Sahana legacy
                opt_pr_nationality,                     # by nursix
#                Field('race'),                          # Sahana legacy
                Field('ethnicity'),                     # by nursix
                Field('religion'),                      # Sahana legacy - TODO: make option field
                Field('marital_status'),                # Sahana legacy - TODO: make option field
                Field('occupation'),                    # Sahana legacy
                migrate=migrate)

db[table].birth_date.requires=IS_NULL_OR(IS_DATE())
title_create = T('Add Person Details')
title_display = T('Person Details')
title_list = T('List Person Details')
title_update = T('Edit Person Details')
title_search = T('Search Person Details')
subtitle_create = T('Add Person Details')
subtitle_list = T('Person Details')
label_list_button = T('List Person Details')
label_create_button = T('Add Person Details')
msg_record_created = T('Person Details added')
msg_record_modified = T('Person Details updated')
msg_record_deleted = T('Person Details deleted')
msg_list_empty = T('No Person Details currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

#
# Health Information (nursix) -------------------------------------------------
#
resource = 'person_health'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                person_id,
                # consciousness
                Field('unconscious', 'boolean', default=False),
                # senses
                Field('blind', 'boolean', default=False),
                Field('deaf', 'boolean', default=False),
                # acute injuries and diseases
                Field('injured', 'boolean', default=False),
                Field('injuries'),
                Field('diseased', 'boolean', default=False),
                Field('acute_diseases'),
                # handicaps
                Field('physically_handicapped', 'boolean', default=False),
                Field('physical_handicaps'),
                Field('mentally_handicapped', 'boolean', default=False),
                Field('mental_handicaps'),
                # chronical diseases
                Field('chronically_ill', 'boolean', default=False),
                Field('chronic_diseases'),
                # support needed
                Field('needs_assistance', 'boolean', default=False),
                Field('assistance_needed', 'text'),
                Field('needs_medicine', 'boolean', default=False),
                Field('medicine_needed', 'text'),
                Field('needs_medical_support', 'boolean', default=False),
                Field('medical_support_needed'),
                Field('needs_special_transport', 'boolean', default=False),
                Field('transport_requirements'),
                Field('needs_attendance', 'boolean', default=False),
                Field('needs_supervision', 'boolean', default=False),
                migrate=migrate)

#
# Person Physical (Sahana legacy) ---------------------------------------------
#
resource = 'person_physical'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                person_id,
                Field('description','text'),
                migrate=migrate)

# ************************************* TO BE REMOVED!
# Missing Person (Sahana legacy) ----------------------------------------------
#
#resource = 'person_missing'
#table = module + '_' + resource
#db.define_table(table, timestamp, deletion_status,
#                person_id,
#                Field('description','text'),
#                migrate=migrate)

# ************************************* TO BE REMOVED!
# Deceased Person (Sahana legacy) ---------------------------------------------
#
#resource = 'person_deceased'
#table = module + '_' + resource
#db.define_table(table, timestamp, deletion_status,
#                person_id,
#                Field('description','text'),
#                migrate=migrate)

#
# Identitiy -------------------------------------------------------------------
#
resource = 'identity'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                person_id,                          # Reference to person
                opt_pr_id_type,                     # ID type
                Field('value'),                     # ID value
                Field('country_code', length=4),    # Country Code (for National ID Cards)
                Field('ia_name'),                   # Name of issuing authority
#                Field('ia_subdivision'),            # Name of issuing authority subdivision
#                Field('ia_code'),                   # Code of issuing authority (if any)
                Field('comment'))                   # a comment (optional)

db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].ia_name.label = T("Issuing Authority")

#
# Group -----------------------------------------------------------------------
# TODO: elaborate!
#
resource = 'group'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                pr_pe_fieldset,                                 # Person Entity Field Set
                opt_pr_group_type,                              # group type
                Field('group_name'),                            # Group name (optional?)
                Field('group_description'),                     # Group short description
#                Field('group_head'),                           # Sahana legacy
#                Field('no_of_adult_males','integer'),           # Sahana legacy
#                Field('no_of_adult_females','integer'),         # Sahana legacy
#                Field('no_of_children', 'integer'),            # Sahana legacy
#                Field('no_of_children_males','integer'),        # by Khushbu
#                Field('no_of_children_females','integer'),      # by Khushbu
#                Field('no_of_displaced', 'integer'),           # Sahana legacy
#                Field('no_of_missing', 'integer'),             # Sahana legacy
#                Field('no_of_dead', 'integer'),                # Sahana legacy
#                Field('no_of_rehabilitated', 'integer'),       # Sahana legacy
#                Field('checklist', 'text'),                    # Sahana legacy
#                Field('description', 'text'),                  # Sahana legacy
                Field('comment'),                               # optional comment
                migrate=migrate)

db[table].pr_pe_label.readable=False
db[table].pr_pe_label.writable=False

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

def shn_pentity_ondelete(record):
    """
    VITA function:
    Minimalistic callback function for CRUD controller, deletes a pentity record
    when the corresponding subclass record gets deleted.
     
    Use as setting in the calling controller:
    
    crud.settings.delete_onvalidation=shn_pentity_ondelete

    Also called by the shn_pentity_onvalidation function on deletion from update form
    """
    if record.get('pr_pe_id'):
        # del db.pr_pentity[record.pr_pe_id]
        # Mark as deleted rather than really deleting
        db(db.pr_pentity.id == record.pr_pe_id).update(deleted = True)
    return

def shn_pentity_onvalidation(form, table=None, entity_class=1):
    """
    VITA function:
    Callback function for RESTlike CRUD controller, creates or updates a pentity
    record when the corresponding subclass record gets created/updated.
     
    Passed to shn_rest_controller as:
    
    onvalidation=lambda form: shn_pentity_onvalidation(form, table='pr_person', entity_class=1)

    form            : the current form containing pr_pe_id and pr_pe_label (from pr_pe_fieldset)
    table           : the table containing the subclass entity
    entity_class    : the class of pentity to be created (from pr_pentity_class_opts)
    """
    if form.vars:
        if (len(request.args) == 0 or request.args[0] == 'create') and entity_class in pr_pentity_class_opts.keys():
            # this is a create action either directly or from list view
            subentity_label = form.vars.get('pr_pe_label')
            pr_pe_id = db['pr_pentity'].insert(opt_pr_pentity_class=entity_class,label=subentity_label)
            if pr_pe_id: form.vars.pr_pe_id = pr_pe_id
        elif len(request.args) > 1 and request.args[0] == 'update' and form.vars.delete_this_record and table:
            # this is a delete action from update
            subentity_id = request.args[1]
            shn_pentity_ondelete(db[table][subentity_id])
        elif len(request.args) > 1 and request.args[0] == 'update' and table:
            # this is an update action
            subentity_id = request.args[1]
            subentity_record=db[table][subentity_id]
            if subentity_record and subentity_record.pr_pe_id:
                db(db.pr_pentity.id==subentity_record.pr_pe_id).update(label=form.vars.get('pr_pe_label'))
    return
