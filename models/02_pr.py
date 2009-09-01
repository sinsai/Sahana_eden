# -*- coding: utf-8 -*-

#
# Sahanapy Person Registry
#
# created 2009-07-15 by nursix
#
# This part defines:
#       - PersonEntity (pentity)    - a person entity
#       - Person (person)           - an individual person
#       - Group (group)             - a group of persons
#       - Network (network)         - a social network layer of a person

module = 'pr'

# *****************************************************************************
# Settings
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

# *****************************************************************************
# Error messages
#
NONEXISTENT_RECORD = T('Nonexistent Record')
INVALID_FUNCTION = T('Invalid Function')

# *****************************************************************************
# Import VITA
#
exec('from applications.%s.modules.vita import *' % request.application)
# Faster for Production (where app-name won't change):
#from applications.sahana.modules.vita import *

vita = Vita(globals(),db)

# *****************************************************************************
# PersonEntity (pentity)

# -----------------------------------------------------------------------------
# Entity types
#
opt_pr_entity_type = SQLTable(None, 'opt_pr_entity_type',
                    db.Field('opt_pr_entity_type','integer',
                    requires = IS_IN_SET(vita.trackable_types),
                    default = vita.DEFAULT_TRACKABLE,
                    label = T('Entity Type'),
                    represent = lambda opt: opt and vita.trackable_types[opt]))

# -----------------------------------------------------------------------------
# shn_pentity_represent
#
def shn_pentity_represent(pentity):
    """
        Represent a Person Entity in option fields or list views
    """

    default = T('None (no such record)')

    try:
        record = vita.pentity(pentity)
        entity_type = record.opt_pr_entity_type

        if entity_type==1:
            person=vita.person(record)
            pentity_str = '%s [%s] (%s)' % (
                vita.fullname(person),
                record.label or 'no label',
                vita.trackable_types[entity_type]
            )

        elif entity_type==2:
            group=vita.group(record)
            pentity_str = '%s (%s)' % (
                group.group_name,
                vita.trackable_types[entity_type]
            )

        else:
            pentity_str = '[%s] (%s)' % (
                record.label or 'no label',
                vita.trackable_types[entity_type]
            )

        return pentity_str

    except:
        return default

#
# pentity table ---------------------------------------------------------------
#
resource = 'pentity'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('parent'),                    # Parent Entity
                opt_pr_entity_type,                 # Entity class
                Field('label', unique=True),        # Recognition Label
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].label.requires = IS_NULL_OR(IS_NOT_IN_DB(db, 'pr_pentity.label'))
db[table].parent.requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_pentity.id', shn_pentity_represent))
db[table].parent.label = T('belongs to')
db[table].deleted.readable = True

#
# Reusable field for other tables to reference --------------------------------
#
pr_pe_id = SQLTable(None, 'pe_id',
                Field('pr_pe_id', db.pr_pentity,
                requires =  IS_NULL_OR(IS_ONE_OF(db, 'pr_pentity.id', shn_pentity_represent)),
                represent = lambda id: (id and [shn_pentity_represent(id)] or ["None"])[0],
                ondelete = 'RESTRICT',
                label = T('ID')
                ))

#
# Person Entity Field Set -----------------------------------------------------
#
pr_pe_fieldset = SQLTable(None, 'pe_fieldset',
                    Field('pr_pe_id', db.pr_pentity,
                    requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_pentity.id', shn_pentity_represent)),
                    represent = lambda id: (id and [shn_pentity_represent(id)] or ["None"])[0],
                    ondelete = 'RESTRICT',
                    readable = False,   # should be invisible in (most) forms
                    writable = False    # should be invisible in (most) forms
                    ),
                    Field('pr_pe_parent', db.pr_pentity,
                    requires =  IS_NULL_OR(IS_ONE_OF(db, 'pr_pentity.id', shn_pentity_represent)),
                    represent = lambda id: (id and [shn_pentity_represent(id)] or ["None"])[0],
                    ondelete = 'RESTRICT',
                    label = T('belongs to'),
                    readable = False,   # should be invisible in (most) forms
                    writable = False    # should be invisible in (most) forms
                    ),
                    Field('pr_pe_label',
                    label = T('ID Label'),
                    requires = IS_NULL_OR(IS_NOT_IN_DB(db, 'pr_pentity.label'))
                    ))

# *****************************************************************************
# Person (person)
#

#
# Gender ----------------------------------------------------------------------
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
# Age Group -------------------------------------------------------------------
#
pr_person_age_group_opts = {
    1:T('unknown'),
    2:T('Infant (0-1)'),
    3:T('Child (2-11)'),
    4:T('Adolescent (12-20)'),
    5:T('Adult (21-50)'),
    6:T('Senior (50+)')
    }

opt_pr_age_group = SQLTable(None, 'opt_pr_age_group',
                    db.Field('opt_pr_age_group','integer',
                    requires = IS_IN_SET(pr_person_age_group_opts),
                    default = 1,
                    label = T('Age Group'),
                    represent = lambda opt: opt and pr_person_age_group_opts[opt]))

#
# Marital Status --------------------------------------------------------------
#
pr_marital_status_opts = {
    1:T('unknown'),
    2:T('single'),
    3:T('married'),
    4:T('separated'),
    5:T('divorced'),
    6:T('widowed'),
    99:T('other')
}

opt_pr_marital_status = SQLTable(None, 'opt_pr_marital_status',
                        db.Field('opt_pr_marital_status','integer',
                        requires = IS_IN_SET(pr_marital_status_opts),
                        default = 1,
                        label = T('Marital Status'),
                        represent = lambda opt: opt and pr_marital_status_opts[opt]))

#
# Religion --------------------------------------------------------------------
#
pr_religion_opts = {
    1:T('none'),
    2:T('Christian'),
    3:T('Muslim'),
    4:T('Jew'),
    5:T('Bhuddist'),
    6:T('Hindu'),
    99:T('other')
    }

opt_pr_religion = SQLTable(None, 'opt_pr_religion',
                    db.Field('opt_pr_religion','integer',
                    requires = IS_IN_SET(pr_religion_opts),
                    default = 1,
                    label = T('Religion'),
                    represent = lambda opt: opt and pr_religion_opts[opt]))

#
# Nationality and Country of Residence ----------------------------------------
#
pr_nationality_opts = shn_list_of_nations

opt_pr_nationality = SQLTable(None, 'opt_pr_nationality',
                        db.Field('opt_pr_nationality','integer',
                        requires = IS_IN_SET(pr_nationality_opts),
                        default = 999, # unknown
                        label = T('Nationality'),
                        represent = lambda opt: opt and pr_nationality_opts[opt]))

opt_pr_country = SQLTable(None, 'opt_pr_country',
                        db.Field('opt_pr_country','integer',
                        requires = IS_IN_SET(pr_nationality_opts),
                        default = 999, # unknown
                        label = T('Country of Residence'),
                        represent = lambda opt: opt and pr_nationality_opts[opt]))

#
# shn_pr_person_represent -----------------------------------------------------
#
def shn_pr_person_represent(id):
    person = vita.person(id)
    if person:
        return vita.fullname(person)
    else:
        return None

#
# person table ----------------------------------------------------------------
#
resource = 'person'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                pr_pe_fieldset,                         # Person Entity Field Set
#                Field('name_unknown', 'boolean', default=False),
                Field('first_name', notnull=True),      # first or only name
                Field('middle_name'),                   # middle name
                Field('last_name'),                     # last name
                Field('preferred_name'),                # how the person uses to be called
                Field('local_name'),                    # name in local language and script, Sahana legacy
                opt_pr_gender,
                opt_pr_age_group,
                Field('email', unique=True),            # Needed for AAA (change this!)
                Field('mobile_phone','integer'),        # Needed for SMS (change this!)
                # Person Details
                Field('date_of_birth','date'),          # Sahana legacy
                opt_pr_nationality,                     # Nationality
                opt_pr_country,                         # Country of residence
#                Field('town'),                          # Town of Origin, Sahana legacy
#                Field('race'),                          # Sahana legacy
#                Field('ethnicity'),                     # by nursix - TODO: add option field
                opt_pr_religion,                        # Sahana legacy
                opt_pr_marital_status,                  # Sahana legacy
                Field('occupation'),                    # Sahana legacy
                Field('comment'),                       # comment
                migrate=migrate)

db[table].pr_pe_label.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("ID Label|Number or Label on the identification tag this person is wearing (if any)."))
#db[table].name_unknown.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Name unknown|Please tag here if the name of the person is unknown (e.g. due to unconsciousness), and repeat the ID label or enter a placeholder (e.g. [unknown]) into the first name field."))

db[table].opt_pr_gender.label = T('Gender')
db[table].opt_pr_age_group.label = T('Age group')

db[table].date_of_birth.requires = IS_NULL_OR(IS_DATE())

db[table].first_name.requires = IS_NOT_EMPTY()   # People don't have to have unique names, some just have a single name
db[table].first_name.comment = SPAN(SPAN("*", _class="req"),A(SPAN("[Help]"), _class="tooltip", _title=T("First name|The first or only name of the person (mandatory).")))

db[table].preferred_name.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Preferred Name|The name to be used when calling for or directly addressing the person (optional)."))
db[table].local_name.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Local Name|Name of the person in local language and script (optional)."))

db[table].email.requires = IS_NOT_IN_DB(db, '%s.email' % table)     # Needs to be unique as used for AAA
db[table].email.requires = IS_NULL_OR(IS_EMAIL())
db[table].email.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Email|This gets used both for signing-in to the system & for receiving alerts/updates."))
db[table].mobile_phone.requires = IS_NULL_OR(IS_NOT_IN_DB(db, '%s.mobile_phone' % table))   # Needs to be unique as used for AAA
db[table].mobile_phone.label = T("Mobile Phone #")
db[table].mobile_phone.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Mobile Phone No|This gets used both for signing-in to the system & for receiving alerts/updates."))

db[table].opt_pr_nationality.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Nationality|Nationality of the person."))
db[table].opt_pr_country.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Country of Residence|The country the person usually lives in."))

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

#
# person_id: reusable field for other tables to reference ---------------------
#
person_id = SQLTable(None, 'person_id',
                Field('person_id', db.pr_person,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_person.id', '%(id)s: %(first_name)s %(last_name)s')),
                represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0],
                comment = DIV(A(T('Add Person'), _class='popup', _href=URL(r=request, c='pr', f='person', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Create Person Entry|Create a person entry in the registry."))),
                ondelete = 'RESTRICT'
                ))

# *****************************************************************************
# Group (group)
#

#
# Group types -----------------------------------------------------------------
#
pr_group_type_opts = {
    1:T('Family'),
    2:T('Tourist Group'),
    3:T('Relief Team'),
    4:T('other')
    }

opt_pr_group_type = SQLTable(None, 'opt_pr_group_type',
                    db.Field('opt_pr_group_type','integer',
                    requires = IS_IN_SET(pr_group_type_opts),
                    default = 4,
                    label = T('Group Type'),
                    represent = lambda opt: opt and pr_group_type_opts[opt]))

#
# group table -----------------------------------------------------------------
#
resource = 'group'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                pr_pe_fieldset,                                 # Person Entity Field Set
                opt_pr_group_type,                              # group type
                Field('system','boolean',default=False),        # System internal? (e.g. users?)
                Field('group_name'),                            # Group name (optional? => No!)
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

db[table].system.readable = False
db[table].system.writable = False

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

#
# group_id: reusable field for other tables to reference ----------------------
#
group_id = SQLTable(None, 'group_id',
                Field('group_id', db.pr_group,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_group.id', '%(id)s: %(group_name)s', filterby='system', filter_opts=(False,))),
                represent = lambda id: (id and [db(db.pr_group.id==id).select()[0].group_name] or ["None"])[0],
                comment = DIV(A(T('Add Group'), _class='popup', _href=URL(r=request, c='pr', f='group', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Create Group Entry|Create a group entry in the registry."))),
                ondelete = 'RESTRICT'
                ))

# *****************************************************************************
# Network (network)
#
pr_network_type_opts = {
    1:T('Family'),
    2:T('Friends'),
    3:T('Colleagues'),
    99:T('other')
    }

opt_pr_network_type = SQLTable(None, 'opt_pr_network_type',
                    db.Field('opt_pr_network_type','integer',
                    requires = IS_IN_SET(pr_network_type_opts),
                    default = 99,
                    label = T('Network Type'),
                    represent = lambda opt: opt and pr_network_type_opts[opt]))
#
# network table ---------------------------------------------------------------
#
resource = 'network'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                person_id,                          # Reference to person (owner)
                opt_pr_network_type,                # Network type
                Field('comment'),                   # a comment (optional)
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

#
# network_id: reusable field for other tables to reference ----------------------
#
network_id = SQLTable(None, 'network_id',
                Field('network_id', db.pr_network,
                requires = IS_NULL_OR(IS_IN_DB(db, 'pr_network.id', '%(id)s')),
                represent = lambda id: (id and [db(db.pr_network.id==id).select()[0].id] or ["None"])[0],
                comment = DIV(A(T('Add Network'), _class='popup', _href=URL(r=request, c='pr', f='network', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Create Network|Create a social network layer for a person."))),
                ondelete = 'RESTRICT'
                ))

# *****************************************************************************
# Functions:
#

#
# shn_pentity_ondelete --------------------------------------------------------
#
def shn_pentity_ondelete(record):
    """
    Minimalistic callback function for CRUD controller, deletes a pentity record
    when the corresponding subclass record gets deleted.
     
    Use as setting in the calling controller:
    
    crud.settings.delete_onvalidation=shn_pentity_ondelete

    Also called by the shn_pentity_onvalidation function on deletion from update form
    """
    if request.vars.format:
        representation = str.lower(request.vars.format)
    else:
        representation = "html"

    if 'pr_pe_id' in record:
        pr_pe_id = record.pr_pe_id
        shn_delete('pr_pentity', 'pentity', pr_pe_id, representation)
    return

#
# shn_pentity_onvalidation ----------------------------------------------------
#
def shn_pentity_onvalidation(form, table=None, entity_class=1):
    """
    Callback function for RESTlike CRUD controller, creates or updates a pentity
    record when the corresponding subclass record gets created/updated.
     
    Passed to shn_rest_controller as:
    
    onvalidation=lambda form: shn_pentity_onvalidation(form, table='pr_person', entity_class=1)

    form            : the current form containing pr_pe_id and pr_pe_label (from pr_pe_fieldset)
    table           : the table containing the subclass entity
    entity_class    : the class of pentity to be created (from vita.trackable_types)
    """
    if form.vars:
        if (len(request.args) == 0 or request.args[0] == 'create') and entity_class in vita.trackable_types:
            # this is a create action either directly or from list view
            subentity_label = form.vars.get('pr_pe_label')
            pr_pe_id = db['pr_pentity'].insert(opt_pr_entity_type=entity_class,label=subentity_label)
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

#
# shn_pr_get_person_id --------------------------------------------------------
#
def shn_pr_get_person_id(label, fields=None, filterby=None):
    """
        Finds a person by any name and/or tag label
    """

    if fields and isinstance(fields, (list,tuple)):
        search_fields = []
        for f in fields:
            if db.pr_person.has_key(f):     # TODO: check for field type?
                search_fields.append(f)
        if not len(search_fields):
            # Error: none of the specified search fields exists
            return None
    else:
        # No search fields specified at all => fallback
        search_fields = ['pr_pe_label','first_name','middle_name','last_name']

    if label and isinstance(label,str):
        labels = label.split()
        results = []
        query = None
        # TODO: make a more sophisticated search function (levenshtein?)
        for l in labels:

            # append wildcards
            wc = "%"
            _l = "%s%s%s" % (wc,l,wc)

            # build query
            for f in search_fields:
                if query:
                    query = (db.pr_person[f].like(_l)) | query
                else:
                    query = (db.pr_person[f].like(_l))

            # undeleted records only
            query = (db.pr_person.deleted==False) & (query)
            # restrict to prior results (AND)
            if len(results):
                query = (db.pr_person.id.belongs(results)) & query
            if filterby:
                query = (filterby) & (query)
            records = db(query).select(db.pr_person.id)
            # rebuild result list
            results = [r.id for r in records]
            # any results left?
            if not len(results):
                return None
        return results
    else:
        # no label given or wrong parameter type
        return None
#
# shn_pr_select_person --------------------------------------------------------
#
def shn_pr_select_person(id):
    """
        Selects a person for this session
    """

    if not ('pr_person' in session):
        session.pr_person = None

    if id:
        session.pr_person = None
        person_id = id
    else:
        person_id = session.pr_person

    person = vita.person(person_id)

    if person:
        session.pr_person = person.id
    else:
        session.pr_person = None

    return

#
# shn_pr_person_header --------------------------------------------------------
#
def shn_pr_person_header(id, next=None):
    """
        Builds a header for person detail pages
    """

    # TODO: This requires read permission to the person table and
    #       audit/read for the person table
    person = vita.person(id)

    if person:

        if next: request.vars.next=next

        redirect = { "_next" : "%s" % URL(r=request, args=request.args, vars=request.vars)}

        # TODO: Internationalization!
        pheader = TABLE(
            TR(
                TH("Name: "),
                vita.fullname(person),
                TH("ID Label: "),
                "%(pr_pe_label)s" % person,
                TH(A("Clear Selection", _href=URL(r=request, c='pr', f='person', args='clear', vars=request.vars)))
                ),
            TR(
                TH("Date of Birth: "),
                "%s" % (person.date_of_birth or 'unknown'),
                TH("Gender: "),
                "%s" % pr_person_gender_opts[person.opt_pr_gender],
                "",
                ),
            TR(
                TH("Nationality"),
                "%s" % pr_nationality_opts[person.opt_pr_nationality],
                TH("Age Group: "),
                "%s" % pr_person_age_group_opts[person.opt_pr_age_group],
                TH(A("Edit Person", _href=URL(r=request, c='pr', f='person', args='update/%s' % id, vars=redirect)))
                )
        )
        return pheader
    else:
        return None

# -----------------------------------------------------------------------------
# shn_pr_pentity_details
#
def shn_pr_pentity_details_linkto(field):
    """
        Linkto helper for shn_pr_pentity_details
    """
    return URL(r=request, f=request.args[0], args="update/%s" % field, vars=dict(_next=URL(r=request, args=request.args, vars=request.vars)))

def shn_pr_pentity_details(
    request,
    module,
    entity,
    record,
    joinby='pr_pe_id',
    fields=None,
    representation='html',
    orderby=None,
    multiple=True):
    """
        Custom CRUD controller for person entity joined tables
    """

    resource = "%s_%s" % (module, entity)
    table = db[resource]

    # Get CRUD Strings
    try:
        title_create = s3.crud_strings[resource].subtitle_create
        title_display =  s3.crud_strings[resource].title_display
        title_list =  s3.crud_strings[resource].subtitle_list
        title_update =  s3.crud_strings[resource].title_update
        msg_created = s3.crud_strings[resource].msg_record_created
        msg_modified = s3.crud_strings[resource].msg_record_modified
        msg_empty = s3.crud_strings[resource].msg_list_empty
    except:
        title_create = s3.crud_strings.title_create
        title_display =  s3.crud_strings.title_display
        title_list =  s3.crud_strings.title_list
        title_update =  s3.crud_strings.title_update
        msg_created = s3.crud_strings.msg_record_created
        msg_modified = s3.crud_strings.msg_record_modified
        msg_empty = s3.crud_strings.msg_list_empty

    if not shn_has_permission('read',table):
        session.error = UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, args=request.args, vars=request.vars)}))

    output = {}

    # Query
    if joinby=='pr_pe_id':
        query = (table.pr_pe_id==record.pr_pe_id)
        _id = record.pr_pe_id
    else:
        query = (table[joinby]==record.id)
        _id = record.id

    if multiple: # multiple records of that type allowed

        # Filter for deletion status (not necessary if multiple==False)
        if 'deleted' in table:
            query = ((table.deleted==False) | (table.deleted==None)) & query

        # Add form
        if shn_has_permission('create',table):
            try:
                table[joinby].default = _id
                table[joinby].writable = False
                table[joinby].comment = None #avoid any Add XXXX links here

                form = SQLFORM(table)
                if form.accepts(request.vars,session):
                    shn_audit_create(form, resource, representation)
                    response.flash=msg_created
                elif form.errors:
                    response.flash="Error!" # should not happen
                output.update(form=form, formtitle=title_create)
            except:
                pass

        # Pagination
        if 'page' in request.vars:
            # Pagination at server-side (since no JS available)
            page = int(request.vars.page)
            start_record = (page - 1) * ROWSPERPAGE
            end_record = start_record + ROWSPERPAGE
            limitby = start_record, end_record
            totalpages = (db(query).count() / ROWSPERPAGE) + 1 # Fails on GAE
            label_search_button = T('Search')
            search_btn = A(label_search_button, _href=URL(r=request, f=resource, args='search'), _id='search-btn')
            output.update(dict(page=page, totalpages=totalpages, search_btn=search_btn))
        else:
            # No Pagination server-side (to allow it to be done client-side)
            limitby = ''
            # Redirect to a paginated version if JS not-enabled
            request.vars['page'] = 1
            response.refresh = '<noscript><meta http-equiv="refresh" content="0; url=' + URL(r=request, args=request.args, vars=request.vars) + '" /></noscript>'

        if not fields:
            fields = [table[f] for f in table.fields if table[f].readable]

        # Column labels
        headers = {}
        for field in fields:
            # Use custom or prettified label
            headers[str(field)] = field.label
    
        if shn_has_permission('update',table):
            linkto=shn_pr_pentity_details_linkto
        else:
            linkto=None

        # Audit
        shn_audit_read(operation='list', resource=resource, representation=representation)

        # Get List
        items = crud.select(
            table,
            query=query,
            fields=fields,
            limitby=limitby,
            headers=headers,
            truncate=48,
            linkto=linkto,
            orderby=orderby,
            _id='list', _class='display')

        if not items:
            items = T('None')

        output.update(items=items, subtitle=title_list)
        return output

    else: # only one record of that type per entity ID
        try:
            target_record = db(query).select(table.id)[0]
        except:
            target_record = None

        if not target_record:
            if shn_has_permission('create', table):
                table[joinby].default = _id
                table[joinby].writable = False
                table[joinby].comment = None #avoid any Add XXXX links here
                form = SQLFORM(table, showid=False)
                if form.accepts(request.vars,session):
                    shn_audit_create(form, resource, representation)
                    response.flash=msg_created
#                    form = SQLFORM(table, form.vars.id, showid=False)
                    redirect(URL(r=request, args=request.args)) # redirect here for update
                elif form.errors:
                    response.flash="Error!" # should not happen
                output.update(form=form, formtitle=title_create)
            else:
                # error message
                items=T('No data available')
                output.update(items=items, subtitle=title_display)
            return output

        if shn_has_permission('update', table):
            # create update form for the record
            table[joinby].default = _id
            table[joinby].writable = False
            table[joinby].comment = None #avoid any Add XXXX links here

            form = SQLFORM(table, target_record.id, showid=False)
            if form.accepts(request.vars,session):
                shn_audit_update(form, resource, representation)
                response.flash=msg_modified
                form = SQLFORM(table, target_record.id, showid=False)
            elif form.errors:
                response.flash="Error!" # should not happen
            output.update(form=form, formtitle=title_update)
        else:
            items = crud.read(table, target_record.id)
            output.update(items=items,subtitle=title_display)
        return output

    return None

# -----------------------------------------------------------------------------
# shn_pr_rest_controller
#
def shn_pr_rest_controller(module, resource,
    deletable=True,
    editable=True,
    listadd=True,
    main='name',
    extra=None,
    orderby=None,
    sortby=None,
    onvalidation=None,
    onaccept=None):

    jresources = dict(
        address=True,
        contact=True,
        image=True,
        identity=True,
        presence=True,
        role=False,
        status=False,
        network=True,
        group_membership=True,
        network_membership=False
    )

    # Get representation ------------------------------------------------------

    if request.vars.format:
        representation = str.lower(request.vars.format)
    else:
        representation = "html"

    # Identify action ---------------------------------------------------------

    if len(request.args)==0:

        # this is a list or read action on the main resource
        _method=None
        _jresource=None
        _id = None

    else:

        if request.args[0].isdigit():
            _id = request.args[0]
            if len(request.args)>1:
                # this is an action on a joint resource
                _jresource = str.lower(request.args[1])
                if _jresource in jresources:
                    if len(request.args)>2:
                        _method = str.lower(request.args[2])
                    else:
                        _method = None
                else:
                    session.error = INVALID_FUNCTION
                    redirect(URL(r=request, c=module, f='index'))
            else:
                # READ action on a main resource record
                _jresource = None
                _method = None

        elif str.lower(request.args[0]) in jresources:
            _id = None
            _jresource = str.lower(request.args[0])
            if len(request.args)>1:
                # <method> on joint resource
                _method = str.lower(request.args[1])
            else:
                # LIST action on joint resource
                _method = None

        else:
            # <method> on main resource or main resource record
            _method = str.lower(request.args[0])
            _jresource = None
            try:
                _id = request.args[1]
            except:
                _id = None


    # Identify main resource record -------------------------------------------

    tablename = "%s_%s" % (module,resource)
    table = db[tablename]

    if _id:
        query = (table.id==_id)
        if 'deleted' in table:
            query = ((table.deleted==False) | (table.deleted==None)) & query
        records = db(query).select(table.id)
        if records:
            _id = records[0].id
        else:
            session.error = NONEXISTENT_RECORD
            redirect(URL(r=request, c=module, f='index'))

    if not _id:
        if 'id_label' in request.vars:
            id_label = str.strip(request.vars.id_label)
            if 'pr_pe_label' in table:
                query = (table.pr_pe_label==id_label)
                if 'deleted' in table:
                    query = ((table.deleted==False) | (table.deleted==None)) & query
                records = db(query).select(table.id)
                if records:
                    _id = records[0].id
                else:
                    session.error = NONEXISTENT_RECORD
                    redirect(URL(r=request, c=module, f='index'))

    if not _id and _jresource:
        # Try previous selection
        if tablename in session:
            _id = session[tablename]
            query = (table.id==_id)
            if 'deleted' in table:
                query = ((table.deleted==False) | (table.deleted==None)) & query
            records = db(query).select(table.id)
            if records:
                _id = records[0].id
            else:
                # selected entry has probably been deleted:
                _id = None
                # This should automatically redirect to a search form if suitable:
                session[tablename] = None

    # Save _id in session:
    if _id:
        session[tablename] = _id

    # Identify join field -----------------------------------------------------

    if _jresource:

        jtablename = "pr_%s" % _jresource
        jtable = db[jtablename]

        if 'pr_pe_id' in table and 'pr_pe_id' in jtable:
            joinby = 'pr_pe_id'
        else:
            joinby = '%s_id' % resource
            if not joinby in jtable:
                joinby = 'pr_%s_id' % resource
                if not joinby in jtable:
                    session.error = INVALID_FUNCTION
                    redirect(URL(r=request, c=module, f='index'))

    else:
        jtablename = None
        jtable = None
        joinby = None

#    print "Main Resource: %s" % tablename
#    print "Joint Resource: %s" % (jtablename or "None")
#    print "Join by: %s" % (joinby or "None")
#    print "Main record ID: %s" % (_id or "None")
#    print "Method: %s" % (_method or "None")

    # Map action --------------------------------------------------------------

    if not _jresource:

        # Simple search and select on persons ---------------------------------
        if _method=="search_simple" and resource=="person":
            if representation=="html":

                if not shn_has_permission('read', db.pr_person):
                    session.error = UNAUTHORISED
                    redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, args='search_simple', vars=request.vars)}))

                # Check for redirection
                if request.vars.next:
                    next = str.lower(request.vars.next)
                else:
                    next = "view"

                # Custom view
                response.view = '%s/person_search.html' % module

                # Title and subtitle
                title = T('Search for a Person')
                subtitle = T('Matching Records')

                # Select form
                form = FORM(TABLE(
                        TR(T('Name and/or ID Label: '),INPUT(_type="text",_name="label",_size="40"), A(SPAN("[Help]"), _class="tooltip", _title=T("Name and/or ID Label|To search for a person, enter any of the first, middle or last names and/or the ID label of a person, separated by spaces. You may use % as wildcard."))),
                        TR("",INPUT(_type="submit",_value="Search"))
                        ))

                output = dict(title=title,subtitle=subtitle,form=form, vars=form.vars)

                # Accept action
                items = None
                if form.accepts(request.vars,session):

                    results = shn_pr_get_person_id(form.vars.label)

                    if results and len(results):
                        rows = db(db.pr_person.id.belongs(results)).select()
                    else:
                        rows = None

                    # Build table rows from matching records
                    if rows:
                        records = []
                        for row in rows:
                            records.append(TR(
                                row.pr_pe_label or '[no label]',
                                A(vita.fullname(row), _href=URL(r=request, c='pr', f='person', args='%s/%s' % (next, row.id))),
#                                A(row.first_name, _href=URL(r=request, c='pr', f='person', args='%s/%s' % (next, row.id))),
#                                row.middle_name,
#                                row.last_name,
                                row.opt_pr_gender and pr_person_gender_opts[row.opt_pr_gender] or 'unknown',
                                row.opt_pr_age_group and pr_person_age_group_opts[row.opt_pr_age_group] or 'unknown',
                                row.opt_pr_nationality and pr_nationality_opts[row.opt_pr_nationality] or 'unknown',
                                row.date_of_birth or 'unknown'
                                ))
                        items=DIV(TABLE(THEAD(TR(
                            TH("ID Label"),
                            TH("Name"),
#                            TH("First Name"),
#                            TH("Middle Name"),
#                            TH("Last Name"),
                            TH("Gender"),
                            TH("Age Group"),
                            TH("Nationality"),
                            TH("Date of Birth"))),
                            TBODY(records), _id='list', _class="display"))
                    else:
                        items = T('None')

                    output.update(dict(items=items))

                return output

            else: # other representation
                pass

        # Clear current selection ---------------------------------------------
        elif _method=="clear":

            session_var = 'pr_%s' % resource

            if session_var in session:
                del session[session_var]

            redirect(URL(r=request, c='pr', f=resource, args='search_simple', vars=request.vars))

        # View or edit basic person data --------------------------------------
        elif _method=="view" and resource=="person":
            if representation=="html":

                # Check for selected person or redirect to search form
                shn_pr_select_person(_id)
                if not session.pr_person:
                    request.vars.next=method
                    redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))
                else:
                    pheader = shn_pr_person_header(session.pr_person, next=_method)

                # Set response view
                response.view = '%s/person.html' % module

                # Add title and subtitle
                title=T('Person')
                output=dict(title=title, pheader=pheader)

                # Which fields into the list?
                fields = [
                        db.pr_person.id,
                        db.pr_person.pr_pe_label,
                        db.pr_person.first_name,
                        db.pr_person.middle_name,
                        db.pr_person.last_name
                ]

                record = vita.person(session.pr_person)

                _output = shn_pr_pentity_details(
                    request, 'pr', 'person', record, joinby='pr_pe_id', fields=fields, multiple=False)

                if _output:
                    output.update(_output)

                pheader = shn_pr_person_header(session.pr_person)
                output.update(pheader=pheader)

                return output

            else: # other representation
                pass
        else:
            # other method on main resource
            # Default CRUD action: forward to REST controller
            return shn_rest_controller(module, resource, main=main, extra=extra,onvalidation=onvalidation,onaccept=onaccept)

    else:
        if resource=="person" and representation=="html":
            # Check for selected person or redirect to search form
#            shn_pr_select_person(_id)
#            if not session.pr_person:
            if not _id:
                request.vars.next=_method
                redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))
            else:
                pheader = shn_pr_person_header(_id, next=_method)

            record = vita.person(_id)

            # Set response view
            response.view = '%s/person.html' % module

            # Add title and subtitle
            title=T('Person')
            output=dict(title=title, pheader=pheader)
        else:
            # TODO: what comes here?
            output={}
            record=None

        if _jresource=="presence":
            # Which fields into the list?
            fields = [
                    db.pr_presence.id,
                    db.pr_presence.time,
                    db.pr_presence.location,
                    db.pr_presence.location_details,
                    db.pr_presence.lat,
                    db.pr_presence.lon,
                    db.pr_presence.opt_pr_presence_condition,
                    db.pr_presence.origin,
                    db.pr_presence.destination,
            ]
        elif _jresource=="image":
            # Which fields?
            fields = [
                    db.pr_image.id,
                    db.pr_image.opt_pr_image_type,
                    db.pr_image.image,
                    db.pr_image.title,
                    db.pr_image.description,
            ]
        elif _jresource=="identity":
            # Which fields?
            fields = [
                    db.pr_identity.id,
                    db.pr_identity.opt_pr_id_type,
                    db.pr_identity.type,
                    db.pr_identity.value,
                    db.pr_identity.country_code,
                    db.pr_identity.ia_name,
            ]
        elif _jresource=="address":
            # Which fields?
            fields = [
                    db.pr_address.id,
                    db.pr_address.opt_pr_address_type,
                    db.pr_address.co_name,
                    db.pr_address.street1,
                    db.pr_address.postcode,
                    db.pr_address.city,
                    db.pr_address.opt_pr_country,
            ]
        elif _jresource=="contact":
            fields = [
                    db.pr_contact.id,
                    db.pr_contact.name,
                    db.pr_contact.person_name,
                    db.pr_contact.opt_pr_contact_method,
                    db.pr_contact.value,
                    db.pr_contact.priority,
            ]
        elif _jresource=="group_membership":
            # Which fields?
            fields = [
                    db.pr_group_membership.id,
                    db.pr_group_membership.group_id,
                    db.pr_group_membership.group_head,
                    db.pr_group_membership.description,
            ]
        else:
            session.error = INVALID_FUNCTION
            redirect(URL(r=request,c=module,f='index'))

        _output = shn_pr_pentity_details(
            request, module, _jresource, record, joinby=joinby, fields=fields)

        if _output:
            output.update(_output)

        return output

    redirect(URL(r=request, c=module, f='index'))

# END
# *****************************************************************************
