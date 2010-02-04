# -*- coding: utf-8 -*-

"""
    SahanaPy Person Registry

    @author: nursix

    @see: U{http://trac.sahanapy.org/wiki/BluePrintVITA}
"""

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
                        represent = lambda opt: vita.trackable_types.get(opt, T('Unknown'))))

# -----------------------------------------------------------------------------
# shn_pentity_represent
#
def shn_pentity_represent(id):
    """
        Represent a Person Entity in option fields or list views
    """

    pentity_str = default = T('None (no such record)')

    table = db.pr_pentity
    pentity = db(table.id==id).select(
        table.opt_pr_entity_type,
        table.label,
        limitby=(0,1)).first()
    if not pentity:
        return default
    entity_type = pentity.opt_pr_entity_type
    label = pentity.label or "no label"

    etype = lambda entity_type: vita.trackable_types[entity_type]

    if entity_type == 1:
        table = db.pr_person
        person = db(table.pr_pe_id==id).select(
                    table.first_name,
                    table.middle_name,
                    table.last_name,
                    limitby=(0,1))
        if person:
            person = person[0]
            pentity_str = '%s [%s] (%s)' % (
                vita.fullname(person),
                label,
                etype(entity_type)
            )

    elif entity_type == 2:
        table = db.pr_group
        group = db(table.pr_pe_id==id).select(
                    table.group_name,
                    limitby=(0,1))
        if group:
            group = group[0]
            pentity_str = '%s (%s)' % (
                group.group_name,
                vita.trackable_types[entity_type]
            )

    else:
        pentity_str = '[%s] (%s)' % (
            label,
            vita.trackable_types[entity_type]
        )

    return pentity_str

#
# pentity table ---------------------------------------------------------------
#
resource = 'pentity'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, authorstamp, deletion_status,
#                    Field('parent'),                # Parent Entity
                    opt_pr_entity_type,              # Entity class
                    Field('label', length=128),      # Recognition Label
                    migrate=migrate)

# Field validation
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
#db[table].label.requires = IS_NULL_OR(IS_NOT_IN_DB(db, 'pr_pentity.label'))
#db[table].parent.requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_pentity.id', shn_pentity_represent))

# Field representation
#db[table].deleted.readable = True

# Field labels
#db[table].parent.label = T('belongs to')

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
#                    Field('pr_pe_parent', db.pr_pentity,
#                        requires =  IS_NULL_OR(IS_ONE_OF(db, 'pr_pentity.id', shn_pentity_represent)),
#                        represent = lambda id: (id and [shn_pentity_represent(id)] or ["None"])[0],
#                        ondelete = 'RESTRICT',
#                        label = T('belongs to'),
#                        readable = False,   # should be invisible in (most) forms
#                        writable = False    # should be invisible in (most) forms
#                    ),
                    Field('pr_pe_label', length=128,
                        label = T('ID Label'),
                        requires = IS_NULL_OR(IS_NOT_IN_DB(db, 'pr_pentity.label'))
                    )) # Can't be unique if we allow Null!

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
                        represent = lambda opt: pr_person_gender_opts.get(opt, T('Unknown'))))

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
                        represent = lambda opt: pr_person_age_group_opts.get(opt, T('Unknown'))))

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
                            requires = IS_NULL_OR(IS_IN_SET(pr_marital_status_opts)),
                            default = 1,
                            label = T('Marital Status'),
                            represent = lambda opt: opt and pr_marital_status_opts.get(opt, T('Unknown'))))

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
                        requires = IS_NULL_OR(IS_IN_SET(pr_religion_opts)),
                        # default = 1,
                        label = T('Religion'),
                        represent = lambda opt: pr_religion_opts.get(opt, T('Unknown'))))

#
# Nationality and Country of Residence ----------------------------------------
#
pr_nationality_opts = shn_list_of_nations

opt_pr_nationality = SQLTable(None, 'opt_pr_nationality',
                        Field('opt_pr_nationality', 'integer',
                            requires = IS_NULL_OR(IS_IN_SET(pr_nationality_opts)),
                            # default = 999, # unknown
                            label = T('Nationality'),
                            represent = lambda opt: pr_nationality_opts.get(opt, T('Unknown'))))

opt_pr_country = SQLTable(None, 'opt_pr_country',
                        Field('opt_pr_country', 'integer',
                            requires = IS_NULL_OR(IS_IN_SET(pr_nationality_opts)),
                            # default = 999, # unknown
                            label = T('Country of Residence'),
                            represent = lambda opt: pr_nationality_opts.get(opt, T('Unknown'))))

#
# shn_pr_person_represent -----------------------------------------------------
#
def shn_pr_person_represent(id):
    table = db.pr_person
    person = db(table.id==id).select(
                table.first_name,
                table.middle_name,
                table.last_name,
                limitby=(0,1))
    if person:
        return vita.fullname(person[0])
    else:
        return None

#
# person table ----------------------------------------------------------------
#
resource = 'person'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, authorstamp, deletion_status,
                pr_pe_fieldset,                         # Person Entity Field Set
                Field('missing', 'boolean', default=False), # Missing?
                Field('first_name', notnull=True),      # first or only name
                Field('middle_name'),                   # middle name
                Field('last_name'),                     # last name
                Field('preferred_name'),                # how the person uses to be called
                Field('local_name'),                    # name in local language and script, Sahana legacy
                opt_pr_gender,
                opt_pr_age_group,
                #Field('email', length=128, unique=True), # Needed for AAA (change this!)
                Field('email', length=128), # Needed for AAA (change this!)
                Field('mobile_phone'),                   # Needed for SMS (change this!)
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
db[table].date_of_birth.requires = IS_NULL_OR(IS_DATE_IN_RANGE(maximum=request.utcnow.date(),
                                        error_message="%s " % T("Enter a date before") + "%(max)s!"))
db[table].first_name.requires = IS_NOT_EMPTY()   # People don't have to have unique names, some just have a single name
db[table].email.requires = IS_NOT_IN_DB(db, '%s.email' % table)     # Needs to be unique as used for AAA
db[table].email.requires = IS_NULL_OR(IS_EMAIL())
db[table].mobile_phone.requires = IS_NULL_OR(IS_NOT_IN_DB(db, '%s.mobile_phone' % table))   # Needs to be unique as used for AAA
db[table].pr_pe_label.requires = IS_NULL_OR(IS_NOT_IN_DB(db, 'pr_person.pr_pe_label'))

# Field representation
db[table].pr_pe_label.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("ID Label|Number or Label on the identification tag this person is wearing (if any)."))
db[table].first_name.comment = SPAN(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("First name|The first or only name of the person (mandatory).")))
db[table].preferred_name.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Preferred Name|The name to be used when calling for or directly addressing the person (optional)."))
db[table].local_name.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Local Name|Name of the person in local language and script (optional)."))
db[table].email.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Email|This gets used both for signing-in to the system & for receiving alerts/updates."))
db[table].mobile_phone.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Mobile Phone No|This gets used both for signing-in to the system & for receiving alerts/updates."))
db[table].opt_pr_nationality.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Nationality|Nationality of the person."))
db[table].opt_pr_country.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Country of Residence|The country the person usually lives in."))

db[table].missing.represent = lambda missing: (missing and ['missing'] or [''])[0]

# Field labels
db[table].opt_pr_gender.label = T('Gender')
db[table].opt_pr_age_group.label = T('Age group')
db[table].mobile_phone.label = T("Mobile Phone #")

# CRUD Strings
ADD_PERSON = T('Add Person')
LIST_PERSONS = T('List Persons')
s3.crud_strings[table] = Storage(
    title_create = T('Add a Person'),
    title_display = T('Person Details'),
    title_list = LIST_PERSONS,
    title_update = T('Edit Person Details'),
    title_search = T('Search Persons'),
    subtitle_create = ADD_PERSON,
    subtitle_list = T('Persons'),
    label_list_button = LIST_PERSONS,
    label_create_button = ADD_PERSON,
    label_delete_button = T('Delete Person'),
    msg_record_created = T('Person added'),
    msg_record_modified = T('Person details updated'),
    msg_record_deleted = T('Person deleted'),
    msg_list_empty = T('No Persons currently registered'))

#
# person_id: reusable field for other tables to reference ---------------------
#
shn_person_comment = DIV(A(s3.crud_strings.pr_person.label_create_button, _class='thickbox', _href=URL(r=request, c='pr', f='person', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=s3.crud_strings.pr_person.label_create_button), A(SPAN("[Help]"), _class="tooltip", _title=T("Create Person Entry|Create a person entry in the registry.")))
person_id = SQLTable(None, 'person_id',
                Field('person_id', db.pr_person,
                    requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_person.id', shn_pr_person_represent)),
                    represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0],
                    comment = shn_person_comment,
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
                    Field('opt_pr_group_type', 'integer',
                        requires = IS_IN_SET(pr_group_type_opts),
                        default = 4,
                        label = T('Group Type'),
                        represent = lambda opt: pr_group_type_opts.get(opt, T('Unknown'))))

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
db[table].pr_pe_label.requires = IS_NULL_OR(IS_NOT_IN_DB(db, 'pr_group.pr_pe_label'))

# Field labels
db[table].opt_pr_group_type.label = T("Group type")
db[table].group_name.label = T("Group name")
db[table].group_description.label = T("Group description")

# CRUD Strings
ADD_GROUP = T('Add Group')
LIST_GROUPS = T('List Groups')
s3.crud_strings[table] = Storage(
    title_create = ADD_GROUP,
    title_display = T('Group Details'),
    title_list = LIST_GROUPS,
    title_update = T('Edit Group'),
    title_search = T('Search Groups'),
    subtitle_create = T('Add New Group'),
    subtitle_list = T('Groups'),
    label_list_button = LIST_GROUPS,
    label_create_button = ADD_GROUP,
    label_delete_button = T('Delete Group'),
    msg_record_created = T('Group added'),
    msg_record_modified = T('Group updated'),
    msg_record_deleted = T('Group deleted'),
    msg_list_empty = T('No Groups currently registered'))

#
# group_id: reusable field for other tables to reference ----------------------
#
group_id = SQLTable(None, 'group_id',
                Field('group_id', db.pr_group,
                    requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_group.id', '%(id)s: %(group_name)s', filterby='system', filter_opts=(False,))),
                    represent = lambda id: (id and [db(db.pr_group.id==id).select()[0].group_name] or ["None"])[0],
                    comment = DIV(A(s3.crud_strings.pr_group.label_create_button, _class='thickbox', _href=URL(r=request, c='pr', f='group', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=s3.crud_strings.pr_group.label_create_button), A(SPAN("[Help]"), _class="tooltip", _title=T("Create Group Entry|Create a group entry in the registry."))),
                    ondelete = 'RESTRICT'
                ))

# *****************************************************************************
# Functions:

#
# shn_pentity_ondelete --------------------------------------------------------
#
def shn_pentity_ondelete(record):

    """
        Deletes pr_pentity entries, when a subentity is deleted, used as
        delete_onaccept callback.

        crud.settings.delete_onaccept = shn_pentity_ondelete
    """

    if "pr_pe_id" in record:
        pr_pe_id = record.pr_pe_id

        delete_onvalidation = crud.settings.delete_onvalidation
        delete_onaccept = crud.settings.delete_onaccept

        crud.settings.delete_onvalidation = None
        crud.settings.delete_onaccept = None

        if db(db.s3_setting.id==1).select()[0].archive_not_delete:
            db(db.pr_pentity.id == pr_pe_id).update(deleted = True)
        else:
            crud.delete(db.pr_pentity, pr_pe_id)

        # TODO: delete joined resources!?

        crud.settings.delete_onvalidation = delete_onvalidation
        crud.settings.delete_onaccept = delete_onaccept

    return True

#
# shn_pentity_onaccept --------------------------------------------------------
#
def shn_pentity_onaccept(form, table=None, entity_type=1):

    """
        Adds or updates a pr_pentity entries as necessary, used as
        onaccept-callback for create/update of subentities.
    """

    if "pr_pe_id" in table.fields:
        record = db(table.id==form.vars.id).select(table.pr_pe_id, table.pr_pe_label).first()
        if record:
            pr_pe_id = record.pr_pe_id
            label = record.pr_pe_label
            if pr_pe_id:
                # update action
                db(db.pr_pentity.id==pr_pe_id).update(label=label)
            else:
                # create action
                pr_pe_id = db.pr_pentity.insert(opt_pr_entity_type=entity_type,
                                                label=label)
                if pr_pe_id:
                    db(table.id==form.vars.id).update(pr_pe_id=pr_pe_id)

    return True

#
# shn_pr_person_search_simple -------------------------------------------------
#
def shn_pr_person_search_simple(xrequest, onvalidation=None, onaccept=None):
    """
        Simple search form for persons
    """

    if not shn_has_permission('read', db.pr_person):
        session.error = UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, args='search_simple', vars=request.vars)}))

    if xrequest.representation=="html":
        # Check for redirection
        if request.vars._next:
            next = str.lower(request.vars._next)
        else:
            next = str.lower(URL(r=request, f='person', args='[id]'))

        # Custom view
        response.view = '%s/person_search.html' % xrequest.prefix

        # Title and subtitle
        title = T('Search for a Person')
        subtitle = T('Matching Records')

        # Select form
        form = FORM(TABLE(
                TR(T('Name and/or ID Label: '),
                   INPUT(_type="text", _name="label", _size="40"),
                   A(SPAN("[Help]"), _class="tooltip", _title=T("Name and/or ID Label|To search for a person, enter any of the first, middle or last names and/or the ID label of a person, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all persons."))),
                TR("", INPUT(_type="submit", _value="Search"))
                ))

        output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

        # Accept action
        items = None
        if form.accepts(request.vars, session):

            if form.vars.label == "":
                form.vars.label = "%"

            results = s3xrc.search_simple(db.pr_person,
                fields=['pr_pe_label', 'first_name', 'middle_name', 'last_name'],
                label=form.vars.label)

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
s3xrc.model.set_method(module, 'person', method='search_simple', action=shn_pr_person_search_simple )

#
# shn_pr_pheader --------------------------------------------------------------
#
def shn_pr_pheader(resource, record_id, representation, next=None, same=None):

    if resource == "person":

        if representation == "html":

            if next:
                _next = next
            else:
                _next = URL(r=request, f=resource, args=['read'])

            if same:
                _same = same
            else:
                _same = URL(r=request, f=resource, args=['read', '[id]'])

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
