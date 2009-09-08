# -*- coding: utf-8 -*-

#
# Human Remains Management
#
# created 2009-07-24 by khushbu
# modified for Sahanapy-VITA 2009-07-29 by nursix
#

module = 'hrm'

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
hrm_task_status_opts = {
    1:T('New'),
    2:T('Assigned'),
    3:T('In Progress'),
    4:T('Completed')
    }

opt_hrm_task_status = SQLTable(None, 'opt_hrm_task_status',
                    db.Field('opt_hrm_task_status','integer',
                    requires = IS_IN_SET(hrm_task_status_opts),
                    default = 1,
                    label = T('Task Status'),
                    represent = lambda opt: opt and hrm_task_status_opts[opt]))

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
                opt_hrm_task_status,                            # Task status
                Field('bodies_rcv', 'integer', default=0),      # Number of bodies recovered
                migrate=migrate)

# Settings and Restrictions
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

# Labels
db[table].find_date.label = T('Date and time of find')
db[table].location.label = T('Place of find')
db[table].person_id.label = T('Finder')
db[table].bodies_est.label = T('Estimated number of bodies found')
db[table].opt_hrm_task_status.label = T('Task status')
db[table].bodies_rcv.label = T('Number of bodies recovered so far')

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

hrm_find_id = SQLTable(None, 'hrm_find_id',
                Field('hrm_find_id', db.hrm_find,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'hrm_find.id', '%(find_date)s: %(location_details)s, %(bodies_est)s bodies')),
                represent = lambda id: (id and [DIV(A(db(db.hrm_find.id==id).select()[0].id, _class='popup', _href=URL(r=request, c='hrm', f='find', args='read'+"/"+str(id).strip(), vars=dict(format='plain')), _target='top'))] or ["None"])[0],
                comment = DIV(A(s3.crud_strings.hrm_find.label_create_button, _class='popup', _href=URL(r=request, c='hrm', f='find', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Find report|Add new report on body find)."))),
                ondelete = 'RESTRICT'
                ))

#
# Body ------------------------------------------------------------------------
#

resource = 'body'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status, #uuidstamp,
                pr_pe_fieldset,                             # Person Entity Fieldset
#                db.Field('date_of_find', 'date'),          # from Khushbu
                hrm_find_id,                                # Associated find report (if any)
                db.Field('date_of_recovery', 'datetime'),       
                db.Field('has_major_outward_damage','boolean'), # Khushbu, TODO: elaborate
                db.Field('is_burned_or_charred','boolean'),     # Khushbu, TODO: elaborate
                db.Field('is_decayed','boolean'),               # Khushbu, TODO: elaborate
                db.Field('is_incomplete','boolean'),            # Khushbu, TODO: elaborate
                opt_pr_gender,                                  # from VITA
                opt_pr_age_group,                               # from VITA
                migrate = migrate)

# Settings and Restrictions
db[table].pr_pe_parent.readable = True         # not visible in body registration form
db[table].pr_pe_parent.writable = True         # not visible in body registration form
db[table].pr_pe_parent.requires = IS_NULL_OR(IS_ONE_OF(db,'pr_pentity.id',shn_pentity_represent,filterby='opt_pr_entity_type',filter_opts=(3,)))

# Labels
db[table].hrm_find_id.label = T('Find report')
db[table].opt_pr_gender.label=T('Apparent Gender')
db[table].opt_pr_age_group.label=T('Apparent Age')

# Representations
db[table].has_major_outward_damage.represent = lambda has_major_outward_damage: (has_major_outward_damage and ["yes"] or [""])[0]
db[table].is_burned_or_charred.represent = lambda is_burned_or_charred: (is_burned_or_charred and ["yes"] or [""])[0]
db[table].is_decayed.represent = lambda is_decayed: (is_decayed and ["yes"] or [""])[0]
db[table].is_incomplete.represent = lambda is_incomplete: (is_incomplete and ["yes"] or [""])[0]

# CRUD Strings
title_create = T('Add Body')
title_display = T('Body Details')
title_list = T('List Bodies')
title_update = T('Edit Body Details')
title_search = T('Search Body')
subtitle_create = T('Add New Entry')
subtitle_list = T('Dead Bodies')
label_list_button = T('List Records')
label_create_button = T('Add Body')
msg_record_created = T('Record added')
msg_record_modified = T('Record updated')
msg_record_deleted = T('Record deleted')
msg_list_empty = T('No bodies currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

