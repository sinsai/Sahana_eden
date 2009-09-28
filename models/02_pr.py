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
# Import VITA
#
exec('from applications.%s.modules.vita import *' % request.application)
# Faster for Production (where app-name won't change):
#from applications.sahana.modules.vita import *

vita = Vita(globals(), db)

# *****************************************************************************
# PersonEntity (pentity)

# -----------------------------------------------------------------------------
# Entity types
#
opt_pr_entity_type = SQLTable(None, 'opt_pr_entity_type',
                    Field('opt_pr_entity_type', 'integer',
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

        if entity_type == 1:
            person = vita.person(record)
            pentity_str = '%s [%s] (%s)' % (
                vita.fullname(person),
                record.label or 'no label',
                vita.trackable_types[entity_type]
            )

        elif entity_type == 2:
            group = vita.group(record)
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
db.define_table(table, timestamp, uuidstamp, authorstamp, deletion_status,
                    Field('parent'),                # Parent Entity
                    opt_pr_entity_type,             # Entity class
                    Field('label', unique=True),    # Recognition Label
                    migrate=migrate)

# Field validation
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].label.requires = IS_NULL_OR(IS_NOT_IN_DB(db, 'pr_pentity.label'))
db[table].parent.requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_pentity.id', shn_pentity_represent))

# Field representation
#db[table].deleted.readable = True

# Field labels
db[table].parent.label = T('belongs to')

# CRUD Strings

#
# Reusable field for other tables to reference --------------------------------
#
pr_pe_id = SQLTable(None, 'pr_pe_id',
                Field('pr_pe_id', db.pr_pentity,
                    requires =  IS_NULL_OR(IS_ONE_OF(db, 'pr_pentity.id', shn_pentity_represent)),
                    represent = lambda id: (id and [shn_pentity_represent(id)] or ["None"])[0],
                    ondelete = 'RESTRICT',
                    label = T('ID')
                ))

#
# Person Entity Field Set -----------------------------------------------------
#
pr_pe_fieldset = SQLTable(None, 'pr_pe_fieldset',
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
                    Field('opt_pr_gender', 'integer',
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
                    Field('opt_pr_age_group', 'integer',
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
                        Field('opt_pr_marital_status', 'integer',
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
                    Field('opt_pr_religion', 'integer',
                        requires = IS_IN_SET(pr_religion_opts),
                        default = 1,
                        label = T('Religion'),
                        represent = lambda opt: opt and pr_religion_opts[opt]))

#
# Nationality and Country of Residence ----------------------------------------
#
pr_nationality_opts = shn_list_of_nations

opt_pr_nationality = SQLTable(None, 'opt_pr_nationality',
                        Field('opt_pr_nationality', 'integer',
                            requires = IS_IN_SET(pr_nationality_opts),
                            default = 999, # unknown
                            label = T('Nationality'),
                            represent = lambda opt: opt and pr_nationality_opts[opt]))

opt_pr_country = SQLTable(None, 'opt_pr_country',
                        Field('opt_pr_country', 'integer',
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
db.define_table(table, timestamp, uuidstamp, authorstamp, deletion_status,
                pr_pe_fieldset,                         # Person Entity Field Set
                Field('first_name', notnull=True),      # first or only name
                Field('middle_name'),                   # middle name
                Field('last_name'),                     # last name
                Field('preferred_name'),                # how the person uses to be called
                Field('local_name'),                    # name in local language and script, Sahana legacy
                opt_pr_gender,
                opt_pr_age_group,
                Field('email', unique=True),            # Needed for AAA (change this!)
                Field('mobile_phone', 'integer'),       # Needed for SMS (change this!)
                # Person Details
                Field('date_of_birth', 'date'),         # Sahana legacy
                opt_pr_nationality,                     # Nationality
                opt_pr_country,                         # Country of residence
                opt_pr_religion,                        # Sahana legacy
                opt_pr_marital_status,                  # Sahana legacy
                Field('occupation'),                    # Sahana legacy
                Field('comment'),                       # comment
                migrate=migrate)

# Field validation
db[table].date_of_birth.requires = IS_NULL_OR(IS_DATE())
db[table].first_name.requires = IS_NOT_EMPTY()   # People don't have to have unique names, some just have a single name
db[table].email.requires = IS_NOT_IN_DB(db, '%s.email' % table)     # Needs to be unique as used for AAA
db[table].email.requires = IS_NULL_OR(IS_EMAIL())
db[table].mobile_phone.requires = IS_NULL_OR(IS_NOT_IN_DB(db, '%s.mobile_phone' % table))   # Needs to be unique as used for AAA

# Field representation
db[table].pr_pe_label.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("ID Label|Number or Label on the identification tag this person is wearing (if any)."))
db[table].first_name.comment = SPAN(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("First name|The first or only name of the person (mandatory).")))
db[table].preferred_name.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Preferred Name|The name to be used when calling for or directly addressing the person (optional)."))
db[table].local_name.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Local Name|Name of the person in local language and script (optional)."))
db[table].email.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Email|This gets used both for signing-in to the system & for receiving alerts/updates."))
db[table].mobile_phone.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Mobile Phone No|This gets used both for signing-in to the system & for receiving alerts/updates."))
db[table].opt_pr_nationality.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Nationality|Nationality of the person."))
db[table].opt_pr_country.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Country of Residence|The country the person usually lives in."))

# Field labels
db[table].opt_pr_gender.label = T('Gender')
db[table].opt_pr_age_group.label = T('Age group')
db[table].mobile_phone.label = T("Mobile Phone #")

# CRUD Strings
title_create = T('Add a Person')
title_display = T('Person Details')
title_list = T('List Persons')
title_update = T('Edit Person Details')
title_search = T('Search Persons')
subtitle_create = T('Add Person')
subtitle_list = T('Persons')
label_list_button = T('List Persons')
label_create_button = T('Add Person')
msg_record_created = T('Person added')
msg_record_modified = T('Person details updated')
msg_record_deleted = T('Person deleted')
msg_list_empty = T('No Persons currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

#
# person_id: reusable field for other tables to reference ---------------------
#
person_id = SQLTable(None, 'person_id',
                Field('person_id', db.pr_person,
                    requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_person.id', shn_pr_person_represent)),
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
                    db.Field('opt_pr_group_type', 'integer',
                        requires = IS_IN_SET(pr_group_type_opts),
                        default = 4,
                        label = T('Group Type'),
                        represent = lambda opt: opt and pr_group_type_opts[opt]))

#
# group table -----------------------------------------------------------------
#
resource = 'group'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, authorstamp, deletion_status,
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

# Field validation

# Field representation
db[table].pr_pe_label.readable = False
db[table].pr_pe_label.writable = False
db[table].system.readable = False
db[table].system.writable = False

# Field labels
db[table].opt_pr_group_type.label = T("Group type")
db[table].group_name.label = T("Group name")
db[table].group_description.label = T("Group description")

# CRUD Strings
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
# Error messages
#
PR_UNAUTHORIZED = T('Not Authorized!')
PR_BADFORMAT = T('Unsupported Format!')

# *****************************************************************************
# Functions:

#
# shn_pentity_ondelete --------------------------------------------------------
#
def shn_pentity_ondelete(record):
    """
    Minimalistic callback function for CRUD controller, deletes a pentity record
    when the corresponding subclass record gets deleted.

    Use as setting in the calling controller:

        crud.settings.delete_onvalidation = shn_pentity_ondelete
    """

    if request.vars.format:
        representation = str.lower(request.vars.format)
    else:
        representation = "html"

    if 'pr_pe_id' in record:
        pr_pe_id = record.pr_pe_id

        delete_onvalidation = crud.settings.delete_onvalidation
        delete_onaccept = crud.settings.delete_onaccept

        crud.settings.delete_onvalidation = None
        crud.settings.delete_onaccept = None

        if shn_has_permission('delete', db.pr_pentity, pr_pe_id):
            shn_audit_delete('pr_pentity', pr_pe_id, 'plain')
            if db(db.s3_setting.id==1).select()[0].archive_not_delete:
                db(db.pr_pentity.id == pr_pe_id).update(deleted = True)
            else:
                crud.delete(db.pr_pentity, pr_pe_id)

        # TODO: delete joined resources!?

        crud.settings.delete_onvalidation = delete_onvalidation
        crud.settings.delete_onaccept = delete_onaccept

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
            pr_pe_id = db['pr_pentity'].insert(opt_pr_entity_type=entity_class, label=subentity_label)
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
        search_fields = ['pr_pe_label', 'first_name', 'middle_name', 'last_name']

    if label and isinstance(label,str):
        labels = label.split()
        results = []
        query = None
        # TODO: make a more sophisticated search function (levenshtein?)
        for l in labels:

            # append wildcards
            wc = "%"
            _l = "%s%s%s" % (wc, l, wc)

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
# shn_pr_person_search_simple -------------------------------------------------
#
def shn_pr_person_search_simple(module, resource, record_id, method,
    jmodule=None,
    jresource=None,
    jrecord_id=None,
    joinby=None,
    multiple=True,
    representation="html",
    onvalidation=None,
    onaccept=None):
    """
        Simple search form for persons
    """

    if not shn_has_permission('read', db.pr_person):
        session.error = PR_UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, args='search_simple', vars=request.vars)}))

    if representation=="html":
        # Check for redirection
        if request.vars._next:
            next = str.lower(request.vars._next)
        else:
            next = str.lower(URL(r=request, f='person', args='[id]'))

        # Custom view
        response.view = '%s/person_search.html' % module

        # Title and subtitle
        title = T('Search for a Person')
        subtitle = T('Matching Records')

        # Select form
        form = FORM(TABLE(
                TR(T('Name and/or ID Label: '), INPUT(_type="text", _name="label", _size="40"), A(SPAN("[Help]"), _class="tooltip", _title=T("Name and/or ID Label|To search for a person, enter any of the first, middle or last names and/or the ID label of a person, separated by spaces. You may use % as wildcard."))),
                TR("", INPUT(_type="submit", _value="Search"))
                ))

        output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

        # Accept action
        items = None
        if form.accepts(request.vars, session):

            results = shn_pr_get_person_id(form.vars.label)

            if results and len(results):
                rows = db(db.pr_person.id.belongs(results)).select()
            else:
                rows = None

            # Build table rows from matching records
            if rows:
                records = []
                for row in rows:
                    href = next.replace('%5bid%5d', '%s' % row.id)
                    records.append(TR(
                        row.pr_pe_label or '[no label]',
                        A(vita.fullname(row), _href=href),
                        row.opt_pr_gender and pr_person_gender_opts[row.opt_pr_gender] or 'unknown',
                        row.opt_pr_age_group and pr_person_age_group_opts[row.opt_pr_age_group] or 'unknown',
                        row.opt_pr_nationality and pr_nationality_opts[row.opt_pr_nationality] or 'unknown',
                        row.date_of_birth or 'unknown'
                        ))
                items=DIV(TABLE(THEAD(TR(
                    TH("ID Label"),
                    TH("Name"),
                    TH("Gender"),
                    TH("Age Group"),
                    TH("Nationality"),
                    TH("Date of Birth"))),
                    TBODY(records), _id='list', _class="display"))
            else:
                items = T('None')

        try:
            label_create_button = s3.crud_strings['pr_person'].label_create_button
        except:
            label_create_button = s3.crud_strings.label_create_button

        add_btn = A(label_create_button, _href=URL(r=request, f='person', args='create'), _id='add-btn')

        output.update(dict(items=items, add_btn=add_btn))
        return output

    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

# Plug into REST controller
jrlayer.set_method(module, 'person', None, None, 'search_simple', shn_pr_person_search_simple )

#
# shn_pr_pheader --------------------------------------------------------------
#
def shn_pr_pheader(resource, record_id, representation, next=None, same=None):

    if resource == "person":

        if representation == "html":

            if next:
                _next = next
            else:
                _next = URL(r=request, f='resource', args=['read'])

            if same:
                _same = same
            else:
                _same = URL(r=request, f='resource', args=['read', '[id]'])

            person = vita.person(record_id)

            if person:
                pheader = TABLE(
                    TR(
                        TH(T('Name: ')),
                        vita.fullname(person),
                        TH(T('ID Label: ')),
                        "%(pr_pe_label)s" % person,
                        TH(A(T('Clear Selection'),
                            _href=URL(r=request, f='person', args='clear', vars={'_next': _same})))
                        ),
                    TR(
                        TH(T('Date of Birth: ')),
                        "%s" % (person.date_of_birth or T('unknown')),
                        TH(T('Gender: ')),
                        "%s" % pr_person_gender_opts[person.opt_pr_gender],
                        TH(""),
                        ),
                    TR(
                        TH(T('Nationality: ')),
                        "%s" % pr_nationality_opts[person.opt_pr_nationality],
                        TH(T('Age Group: ')),
                        "%s" % pr_person_age_group_opts[person.opt_pr_age_group],
                        TH(A(T('Edit Person'),
                            _href=URL(r=request, f='person', args=['update', record_id], vars={'_next': _next})))
                        )
                )
                return pheader

        else:
            pass

    elif resource == "group":
        pass
    else:
        pass

    return None

# END
# *****************************************************************************
