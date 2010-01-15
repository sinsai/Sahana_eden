# -*- coding: utf-8 -*-

"""
    DVI - Management of Dead Bodies and Disaster Victim Identification

    @author: khushbu
    @author: nursix
"""

module = 'dvi'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)

#
# Option fields ---------------------------------------------------------------
#
dvi_task_status_opts = {
    1:T('New'),
    2:T('Assigned'),
    3:T('In Progress'),
    4:T('Completed'),
    5:T('Not Applicable'),
    6:T('Not Possible')
    }

opt_dvi_task_status = db.Table(None, 'opt_dvi_task_status',
                    db.Field('opt_dvi_task_status','integer',
                    requires = IS_IN_SET(dvi_task_status_opts),
                    default = 1,
                    label = T('Task Status'),
                    represent = lambda opt: opt and dvi_task_status_opts[opt]))

#
# Find ------------------------------------------------------------------------
#
resource = 'find'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('find_date', 'datetime'),                 # Date and time of find
                location_id,                                    # Place of find
                Field('location_details'),                      # Details on location
                person_id,                                      # Finder
                Field('description'),                           # Description of find
                Field('bodies_est', 'integer', default=1),      # Estimated number of dead bodies
                opt_dvi_task_status,                            # Task status
                Field('bodies_rcv', 'integer', default=0),      # Number of bodies recovered
                migrate=migrate)

# Settings and Restrictions
#db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

# Labels
db[table].find_date.label = T('Date and time of find')
db[table].location_id.label = T('Place of find')
db[table].person_id.label = T('Finder')
db[table].bodies_est.label = T('Bodies found')
db[table].opt_dvi_task_status.label = T('Task status')
db[table].bodies_rcv.label = T('Bodies recovered')

# Representations

# CRUD Strings
# TODO: check language and spelling
title_create = T('New Body Find')
title_display = T('Find Details')
title_list = T('List Body Finds')
title_update = T('Update Find Report')
title_search = T('Search Find Report')
subtitle_create = T('Add New Find Report')
subtitle_list = T('Body Finds')
label_list_button = T('List Finds')
label_create_button = T('Add Find Report')
msg_record_created = T('Find Report added')
msg_record_modified = T('Find Report updated')
msg_record_deleted = T('Find Report deleted')
msg_list_empty = T('No finds currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

dvi_find_id = db.Table(None, 'dvi_find_id',
                Field('dvi_find_id', db.dvi_find,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'dvi_find.id', '[%(id)s] %(find_date)s: %(bodies_est)s bodies')),
                represent = lambda id: (id and [DIV(A(db(db.dvi_find.id==id).select()[0].id, _class='popup', _href=URL(r=request, c='hrm', f='find', args=['read', str(id).strip()], vars=dict(format='plain')), _target='top', _title=s3.crud_strings.dvi_find.label_create_button))] or ["None"])[0],
                comment = DIV(A(s3.crud_strings.dvi_find.label_create_button, _class='thickbox', _href=URL(r=request, c='hrm', f='find', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=s3.crud_strings.dvi_find.label_create_button), A(SPAN("[Help]"), _class="tooltip", _title=T("Find report|Add new report on body find)."))),
                ondelete = 'RESTRICT'
                ))

#
# Body ------------------------------------------------------------------------
#
resource = 'body'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status, #uuidstamp,
                pr_pe_fieldset,                             # Person Entity Fieldset
                dvi_find_id,                                # Associated find report (if any)
                Field('date_of_recovery', 'datetime'),      # Date/Time of recovery
                location_id,                                # Place of Recovery
                Field('recovery_details','text'),           # Details of the Recovery
                db.Field('has_major_outward_damage','boolean'), # Khushbu, TODO: elaborate
                db.Field('is_burned_or_charred','boolean'),     # Khushbu, TODO: elaborate
                db.Field('is_decayed','boolean'),               # Khushbu, TODO: elaborate
                db.Field('is_incomplete','boolean'),            # Khushbu, TODO: elaborate
                opt_pr_gender,                                  # from VITA
                opt_pr_age_group,                               # from VITA
                migrate = migrate)

# Settings and Restrictions
#db[table].pr_pe_parent.readable = True         # not visible in body registration form
#db[table].pr_pe_parent.writable = True         # not visible in body registration form
#db[table].pr_pe_parent.requires = IS_NULL_OR(IS_ONE_OF(db,'pr_pentity.id',shn_pentity_represent,filterby='opt_pr_entity_type',filter_opts=(3,)))

# Labels
db[table].dvi_find_id.label = T('Find report')
db[table].opt_pr_gender.label=T('Apparent Gender')
db[table].opt_pr_age_group.label=T('Apparent Age')
db[table].location_id.label=T('Place of Recovery')

# Representations
db[table].has_major_outward_damage.represent = lambda has_major_outward_damage: (has_major_outward_damage and ["yes"] or [""])[0]
db[table].is_burned_or_charred.represent = lambda is_burned_or_charred: (is_burned_or_charred and ["yes"] or [""])[0]
db[table].is_decayed.represent = lambda is_decayed: (is_decayed and ["yes"] or [""])[0]
db[table].is_incomplete.represent = lambda is_incomplete: (is_incomplete and ["yes"] or [""])[0]

# CRUD Strings
title_create = T('Add Recovery Report')
title_display = T('Dead Body Details')
title_list = T('Body Recovery Reports')
title_update = T('Edit Recovery Details')
title_search = T('Find Recovery Report')
subtitle_create = T('Add New Report')
subtitle_list = T('Available Recovery Reports')
label_list_button = T('List Reports')
label_create_button = T('Add Recovery Report')
msg_record_created = T('Recovery report added')
msg_record_modified = T('Recovery report updated')
msg_record_deleted = T('Recovery report deleted')
msg_list_empty = T('No recovery reports available')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

#
# Functions -------------------------------------------------------------------
#
def shn_dvi_pheader(resource, record_id, representation, next=None, same=None):

    if resource == "body":
        if representation == "html":
            if next:
                _next = next
            else:
                _next = URL(r=request, f=resource, args=['read'])

            if same:
                _same = same
            else:
                _same = URL(r=request, f=resource, args=['read', '[id]'])

            body = db.dvi_body[record_id]

            if body:
                pheader = TABLE(
                    TR(
                        TH(T('ID Label: ')),
                        "%(pr_pe_label)s" % body,
                        TH(A(T('Clear Selection'),
                            _href=URL(r=request, f='body', args='clear', vars={'_next': _same})))
                        ),
                    TR(
                        TH(T('Gender: ')),
                        "%s" % pr_person_gender_opts[body.opt_pr_gender],
                        TH(""),
                        ),
                    TR(
                        TH(T('Age Group: ')),
                        "%s" % pr_person_age_group_opts[body.opt_pr_age_group],
                        TH(A(T('Edit Record'),
                            _href=URL(r=request, f='body', args=['update', record_id], vars={'_next': _next})))
                        )
                )
                return pheader

    return None


def shn_dvi_get_body_id(label, fields=None, filterby=None):

    if fields and isinstance(fields, (list,tuple)):
        search_fields = []
        for f in fields:
            if db.dvi_body.has_key(f):     # TODO: check for field type?
                search_fields.append(f)
        if not len(search_fields):
            # Error: none of the specified search fields exists
            return None
    else:
        # No search fields specified at all => fallback
        search_fields = ['pr_pe_label']

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
                    query = (db.dvi_body[f].like(_l)) | query
                else:
                    query = (db.dvi_body[f].like(_l))

            # undeleted records only
            query = (db.dvi_body.deleted==False) & (query)
            # restrict to prior results (AND)
            if len(results):
                query = (db.dvi_body.id.belongs(results)) & query
            if filterby:
                query = (filterby) & (query)
            records = db(query).select(db.dvi_body.id)
            # rebuild result list
            results = [r.id for r in records]
            # any results left?
            if not len(results):
                return None
        return results
    else:
        # no label given or wrong parameter type
        return None


def shn_dvi_body_search_simple(xrequest, onvalidation=None, onaccept=None):

    if not shn_has_permission('read', db.dvi_body):
        session.error = UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, args='search_simple', vars=request.vars)}))

    if xrequest.representation=="html":
        # Check for redirection
        if request.vars._next:
            next = str.lower(request.vars._next)
        else:
            next = str.lower(URL(r=request, f='body', args='[id]'))

        # Custom view
        response.view = '%s/body_search.html' % xrequest.prefix

        # Title and subtitle
        title = T('Find Recovery Report')
        subtitle = T('Matching Records')

        # Select form
        form = FORM(TABLE(
                TR(T('ID Label: '),
                   INPUT(_type="text", _name="label", _size="40"),
                   A(SPAN("[Help]"), _class="tooltip", _title=T("ID Label|To search for a body, enter the ID label of the body. You may use % as wildcard. Press 'Search' without input to list all bodies."))),
                TR("", INPUT(_type="submit", _value="Search"))
                ))

        output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

        # Accept action
        items = None
        if form.accepts(request.vars, session):

            if form.vars.label == "":
                form.vars.label = "%"

            results = shn_dvi_get_body_id(form.vars.label)

            if results and len(results):
                rows = db(db.dvi_body.id.belongs(results)).select()
            else:
                rows = None

            # Build table rows from matching records
            if rows:
                records = []
                for row in rows:
                    href = next.replace('%5bid%5d', '%s' % row.id)
                    records.append(TR(
                        A(row.pr_pe_label or '[no label]', _href=href),
                        row.opt_pr_gender and pr_person_gender_opts[row.opt_pr_gender] or 'unknown',
                        row.opt_pr_age_group and pr_person_age_group_opts[row.opt_pr_age_group] or 'unknown',
                        row.date_of_recovery,
                        (row.location_id and [db.gis_location[row.location_id].name] or [''])[0],
#                        location_id.location_id.represent(row.location_id)
                        ))
                items=DIV(TABLE(THEAD(TR(
                    TH("ID Label"),
                    TH("Gender"),
                    TH("Age Group"),
                    TH("Recovery Date"),
                    TH("Recovery Site"))),
                    TBODY(records), _id='list', _class="display"))
            else:
                items = T('None')

        try:
            label_create_button = s3.crud_strings['dvi_body'].label_create_button
        except:
            label_create_button = s3.crud_strings.label_create_button

        add_btn = A(label_create_button, _href=URL(r=request, f='body', args='create'), _id='add-btn')

        output.update(dict(items=items, add_btn=add_btn))
        return output

    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

# Plug into REST controller
s3xrc.model.set_method(module, 'body', method='search_simple', action=shn_dvi_body_search_simple )

#
# Checklist of operations -----------------------------------------------------
#
resource = 'checklist'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_id,
                db.Field('personal_effects'),
                db.Field('body_radiology'),
                db.Field('fingerprints'),
                db.Field('anthropology'),
                db.Field('pathology'),
                db.Field('embalming'),
                db.Field('dna'),
                db.Field('dental'),
                migrate = migrate)

# Setting and restrictions
db[table].personal_effects.requires = IS_IN_SET(dvi_task_status_opts)
db[table].body_radiology.requires = IS_IN_SET(dvi_task_status_opts)
db[table].fingerprints.requires = IS_IN_SET(dvi_task_status_opts)
db[table].anthropology.requires = IS_IN_SET(dvi_task_status_opts)
db[table].pathology.requires = IS_IN_SET(dvi_task_status_opts)
db[table].embalming.requires = IS_IN_SET(dvi_task_status_opts)
db[table].dna.requires = IS_IN_SET(dvi_task_status_opts)
db[table].dental.requires = IS_IN_SET(dvi_task_status_opts)

db[table].personal_effects.label = 'Inventory of Effects'
db[table].body_radiology.label = 'Radiology'
db[table].fingerprints.label = 'Fingerprinting'
db[table].anthropology.label = 'Anthropolgy'
db[table].pathology.label = 'Pathology'
db[table].embalming.label = 'Embalming'
db[table].dna.label = 'DNA Profiling'
db[table].dental.label = 'Dental Examination'

# CRUD Strings
title_create = T('Create Checklist')
title_display = T('Checklist of Operations')
title_list = T('List Checklists')
title_update = T('Update Checklist')
title_search = T('Search Checklists')
subtitle_create = T('Create New Checklist')
subtitle_list = T('Checklist of Operations')
label_list_button = T('Show Checklist')
label_create_button = T('Create Checklist')
msg_record_created = T('Checklist created')
msg_record_modified = T('Checklist updated')
msg_record_deleted = T('Checklist deleted')
msg_list_empty = T('No Checklist available')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Joined Resource
s3xrc.model.add_component(module, resource,
    multiple = False,
    joinby = 'pr_pe_id',
    deletable = True,
    editable = True,
    list_fields = ['id'])

#
# Personal Effects ------------------------------------------------------------------------
#
resource = 'effects'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_id,
#                person_id,
                db.Field('clothing', 'text'),    #TODO: elaborate
                db.Field('jewellery', 'text'),   #TODO: elaborate
                db.Field('footwear', 'text'),    #TODO: elaborate
                db.Field('watch', 'text'),       #TODO: elaborate
                db.Field('other', 'text'),
                migrate = migrate)

# Settings and Restrictions

# Labels
#db[table].person_id.label = T('Reporter')

# CRUD Strings
title_create = T('Add Personal Effects')
title_display = T('Personal Effects Details')
title_list = T('List Personal Effects')
title_update = T('Edit Personal Effects Details')
title_search = T('Search Personal Effects')
subtitle_create = T('Add New Entry')
subtitle_list = T('Personal Effects')
label_list_button = T('List Records')
label_create_button = T('Add Personal Effects')
msg_record_created = T('Record added')
msg_record_modified = T('Record updated')
msg_record_deleted = T('Record deleted')
msg_list_empty = T('No Details currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Joined Resource
s3xrc.model.add_component(module, resource,
    multiple = False,
    joinby = 'pr_pe_id',
    deletable = True,
    editable = True,
    list_fields = ['id'])

#
# Identification --------------------------------------------------------------
#
dvi_id_status_opts = {
    1:T('Unidentified'),
    2:T('Preliminary'),
    3:T('Confirmed'),
    }

opt_dvi_id_status = db.Table(None, 'opt_dvi_id_status',
                    db.Field('opt_dvi_id_status','integer',
                    requires = IS_IN_SET(dvi_id_status_opts),
                    default = 1,
                    label = T('Identification Status'),
                    represent = lambda opt: opt and dvi_id_status_opts[opt]))

dvi_id_method_opts = {
    1:T('Visual Recognition'),
    2:T('Physical Description'),
    3:T('Fingerprints'),
    4:T('Dental Profile'),
    5:T('DNA Profile'),
    6:T('Combined Method'),
    99:T('Other Evidence')
    }

opt_dvi_id_method = db.Table(None, 'opt_dvi_id_method',
                    db.Field('opt_dvi_id_method','integer',
                    requires = IS_IN_SET(dvi_id_method_opts),
                    default = 99,
                    label = T('Method used'),
                    represent = lambda opt: opt and dvi_id_method_opts[opt]))

resource = 'identification'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_id,
                Field('identified_by', db.pr_person),  # Person identifying the body
                Field('reported_by', db.pr_person),    # Person reporting
                opt_dvi_id_status,                     # Identity status
                opt_dvi_id_method,                     # Method used
                Field('identity', db.pr_person),       # Identity of the body
                Field('comment', 'text'),              # Comment (optional)
                migrate = migrate)

# Settings and Restrictions
db[table].identified_by.requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_person.id', shn_pr_person_represent))
db[table].identified_by.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
db[table].identified_by.comment = shn_person_comment
db[table].identified_by.ondelete = 'RESTRICT'

db[table].reported_by.requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_person.id', shn_pr_person_represent))
db[table].reported_by.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
db[table].reported_by.comment = shn_person_comment
db[table].reported_by.ondelete = 'RESTRICT'

db[table].identity.requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_person.id', shn_pr_person_represent))
db[table].identity.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
db[table].identity.comment = shn_person_comment
db[table].identity.ondelete = 'RESTRICT'

# Labels

# CRUD Strings
title_create = T('Add Identification Report')
title_display = T('Identification Report')
title_list = T('List Reports')
title_update = T('Edit Identification Report')
title_search = T('Search Report')
subtitle_create = T('Add New Report')
subtitle_list = T('Identification Reports')
label_list_button = T('List Reports')
label_create_button = T('Add Identification Report')
msg_record_created = T('Report added')
msg_record_modified = T('Report updated')
msg_record_deleted = T('Report deleted')
msg_list_empty = T('No Identification Report Available')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Joined Resource
s3xrc.model.add_component(module, resource,
    multiple = False,
    joinby = 'pr_pe_id',
    deletable = True,
    editable = True,
    list_fields = ['id'])
