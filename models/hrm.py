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
                    represent = lambda opt: opt and hrm_task_status_opts[opt]))

#
# Find ------------------------------------------------------------------------
#
resource = 'find'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('find_date', 'datetime'),         # Date and time of find
                location_id,                            # Place of find
                Field('location_details'),              # Details on location
                person_id,                              # Finder
                Field('description'),                   # Description of find
                Field('bodies_est', 'integer', default=1),      # Estimated number of dead bodies
                opt_hrm_task_status,                    # Task status
                Field('bodies_rcv', 'integer', default=0),      # Number of bodies recovered
                migrate=migrate)

db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

db[table].find_date.label = T('Date and time of find')
db[table].location.label = T('Place of find')
db[table].person_id.label = T('Finder')
db[table].bodies_est.label = T('Estimated number of bodies found')
db[table].opt_hrm_task_status.label = T('Task status')
db[table].bodies_rcv.label = T('Number of bodies recovered so far')

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
                requires = IS_NULL_OR(IS_IN_DB(db, 'hrm_find.id', '%(find_date)s: %(location_details)s, %(bodies_est)s bodies')),
                represent = lambda id: (id and [DIV(A(db(db.hrm_find.id==id).select()[0].id, _class='popup', _href=URL(r=request, c='hrm', f='find', args='read'+"/"+str(id).strip(), vars=dict(format='plain')), _target='top'))] or ["None"])[0],
                comment = DIV(A(s3.crud_strings.hrm_find.label_create_button, _class='popup', _href=URL(r=request, c='hrm', f='find', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Find report|Add new report on body find)."))),
                ondelete = 'RESTRICT'
                ))

# Body ------------------------------------------------------------------------
#

resource = 'body'
table = module + '_' + resource
db.define_table(table, timestamp, #uuidstamp,
                pentity_field_set,
#                db.Field('date_of_find', 'date'),
                hrm_find_id,                                # Associated find report (if any)
                db.Field('date_of_recovery', 'date'),
                db.Field('has_major_outward_damage','boolean'),
                db.Field('is_burned_or_charred','boolean'),
                db.Field('is_decayed','boolean'),
                db.Field('is_incomplete','boolean'),
                opt_pr_gender,                              # from VITA
                opt_pr_age_group,                           # from VITA
                migrate = migrate)

#db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].pentity_id.readable = False
db[table].pentity_id.writable = False
db[table].opt_pr_tag_type.label = T('Tag type')
db[table].hrm_find_id.label = T('Find report')
db[table].opt_pr_gender.label=T('Apparent Gender')
db[table].opt_pr_age_group.label=T('Apparent Age')

db[table].has_major_outward_damage.represent = lambda has_major_outward_damage: (has_major_outward_damage and ["yes"] or [""])[0]
db[table].is_burned_or_charred.represent = lambda is_burned_or_charred: (is_burned_or_charred and ["yes"] or [""])[0]
db[table].is_decayed.represent = lambda is_decayed: (is_decayed and ["yes"] or [""])[0]
db[table].is_incomplete.represent = lambda is_incomplete: (is_incomplete and ["yes"] or [""])[0]

title_create = T('Add Dead Body')
title_display = T('Dead Body Details')
title_list = T('List Dead Bodies')
title_update = T('Edit Dead Body')
title_search = T('Search Dead Body')
subtitle_create = T('Add New Entry')
subtitle_list = T('Dead Bodies')
label_list_button = T('List Bodies')
label_create_button = T('Add Body')
msg_record_created = T('Body added')
msg_record_modified = T('Body updated')
msg_record_deleted = T('Body deleted')
msg_list_empty = T('No bodies currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

#
# Recovery Record -------------------------------------------------------------
# ...to be removed
#
# Recovery means organization of the search and recovery of dead bodies from the scene
# (including Messaging and GIS parts)
# When remains are found, the recovery team gets deployed.
# Data capture for that: Location, type of remains, photograph, environment information - has to be reported to the team coordinator.
#resource = 'recovery'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp,
#                db.Field('case_id', length = 64),        # For Case Management            
#                pitem_id,
#                db.Field('date_of_recovery', 'date'),
#                person_id,                               # Recovered by     
#                group_id,                                # For recovery Team
#                location_id,                             # Site Location (to be integrated with 'lms' module)
#                db.Field('description',length=256),
#                db.Field('trasported_to'),               # morgue or some collection point (can be integrated with 'or' or 'lms' module)
#                migrate = migrate)
#db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
#db[table].case_id.requires = IS_NOT_IN_DB(db, '%s.case_id' %table)
#db[table].pitem_id.label = T("Tag Label")
#db[table].date_of_recovery.requires = IS_DATE(T("%Y-%m-%d"))
#db[table].person_id.label = T("Recovered By")
#db[table].group_id.label = T("Recovery Team")
#db[table].location_id.label = T("Location")
#title_create = T('Add Record')
#title_display = T('Record Details')
#title_list = T('List Record')
#title_update = T('Edit Record')
#title_search = T('Search Record')
#subtitle_create = T('Add New Record')
#subtitle_list = T('Record')
#label_list_button = T('List Record')
#label_create_button = T('Add Record')
#msg_record_created = T('Record added')
#msg_record_modified = T('Record updated')
#msg_record_deleted = T('Record deleted')
#msg_list_empty = T('No Record currently registered')
#s3.crud_strings[table] = Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, title_search=title_search, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty

#Reusable field for other tables
#Redefine for Case Management
#case_id = SQLTable(None, 'case_id',
#                Field('case_id', db.hrm_recovery,
#                requires = IS_NULL_OR(IS_IN_DB(db, 'hrm_recovery.id', '%(case_id)s: %(description)s')),
#                represent = lambda id: (id and [db(db.hrm_recovery.id==id).select()[0].case_id] or ["None"])[0],
#                comment = None,
#                ondelete = 'RESTRICT'
#                ))

#
# Movement --------------------------------------------------------------------
# ...to be removed
# Any movement of a body (or other item) will be observed
# and recorded in the database until the final release for burial or issuance to relatives.
#resource = 'movement'
#table = module + '_' + resource
#db.define_table(table, timestamp, #uuidstamp,
#                pitem_id,
#                db.Field('moved_on','date'),
#                db.Field('destination'),                      # presence_id
#                db.Field('reason',length=256),
#                db.Field('transport_condition',length=256),    #requires refinement
#                migrate = migrate)
#db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
#title_create = T('Add Movement Details')
#title_display = T('Movement Details')
#title_list = T('List Movement Details')
#title_update = T('Edit Movement Details')
#title_search = T('Search Movement Details')
#subtitle_create = T('Add New Entry')
#subtitle_list = T('Movement Details')
#label_list_button = T('List Movements')
#label_create_button = T('Add Movement Details')
#msg_record_created = T('Movement Details added')
#msg_record_modified = T('Movement Details updated')
#msg_record_deleted = T('Movement Details deleted')
#msg_list_empty = T('No details currently registered')
#s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Storage Type
#resource = 'storage_type'
#table = module + '_' + resource
#db.define_table(table,
#                db.Field('name', notnull = True))
#db[table].name.requires=IS_NOT_IN_DB(db, '%s.name' % table)

#if not len(db().select(db[table].ALL)):
#   db[table].insert(name = "Temporary Burial")
#   db[table].insert(name = "Refrigeration")
#   db[table].insert(name = "Dry Ice")
#   db[table].insert(name = "Ice")
#   db[table].insert(name = "Long-Term Burial")

#opt_storage_type = SQLTable(None, 'opt_storage_type',
#                    db.Field('opt_storage_type', db.hrm_storage_type,
#                    requires = IS_NULL_OR(IS_IN_DB(db, 'hrm_storage_type.id', 'hrm_storage_type.name')),
#                    represent = lambda id: (id and [db(db.hrm_storage_type.id==id).select()[0].name] or ["None"])[0],
#                    comment = None,
#                    ondelete = 'RESTRICT'
#                    )) 
# Storage
# The bodies and items are stored after recovery before Investigations and
# after Identification till it is released or Unidentified  
#resource = 'storage'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp,
#                case_id,
#                opt_storage_type,
#                location_id,
#                db.Field('storage_site', db.lms_storage_loc),            # waiting for lms module 
#                db.Field('storage_bin', db.lms_storage_bin),             # waiting for lms module
#                db.Field('status_before_storage', length=256),
#                db.Field('reason', length=256),
#                person_id,
#                migrate=migrate )
#db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
#db[table].opt_storage_type.label = T("Storage Type")
#db[table].person_id.label = T("Contact")

# Management
# Each case is registered and assigned to someone for investigation
#resource = 'management'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp,
#                case_id,
#                person_id,
#                db.Field('assigned_on', 'date'),
#                db.Field('processing_status', length = 256),
#                db.Field('description', length = 256),
#                migrate = migrate)
#db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
#db[table].person_id.label = T("person-in-charge")

# Checklist of Operation
# To report the progress of processing
#resource = 'operation_checklist'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp,
#                case_id,
#                db.Field('personal_effects'),
#                db.Field('photography'),
#                db.Field('body_radiology'),
#                db.Field('fingerprints'),
#                db.Field('anthropology'),
#                db.Field('pathology'),
#                db.Field('embalming'),
#                db.Field('dna'),
#                db.Field('dental'),
#                db.Field('exit_morgue'),
#                migrate = migrate)
#db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
#db[table].personal_effects.requires = IS_IN_SET(['Assigned', 'Completed', 'Unachievable', 'Not Applicable'])
#db[table].body_radiology.requires = IS_IN_SET(['Assigned', 'Completed', 'Unachievable', 'Not Applicable'])
#db[table].photography.requires = IS_IN_SET(['Assigned', 'Completed', 'Unachievable', 'Not Applicable'])
#db[table].fingerprints.requires = IS_IN_SET(['Assigned', 'Completed', 'Unachievable', 'Not Applicable'])
#db[table].anthropology.requires = IS_IN_SET(['Assigned', 'Completed', 'Unachievable', 'Not Applicable'])
#db[table].pathology.requires = IS_IN_SET(['Assigned', 'Completed', 'Unachievable', 'Not Applicable'])
#db[table].embalming.requires = IS_IN_SET(['Assigned', 'Completed', 'Unachievable', 'Not Applicable'])
#db[table].dna.requires = IS_IN_SET(['Assigned', 'Completed', 'Unachievable', 'Not Applicable'])
#db[table].dental.requires = IS_IN_SET(['Assigned', 'Completed', 'Unachievable', 'Not Applicable'])
#db[table].exit_morgue.requires = IS_IN_SET(['Assigned', 'Completed', 'Unachievable', 'Not Applicable'])
# ---------- Pending ----------------------------------------------------
#db[table].personal_effects.comment = DIV(A(T("Add Details")))
#db[table].body_radiology.comment = DIV(A(T("Add Details")))
#db[table].photography.comment = DIV(A(T("Add Details")))
#db[table].fingerprints.comment = DIV(A(T("Add Details")))
#db[table].anthropology.comment = DIV(A(T("Add Details")))
#db[table].pathology.comment = DIV(A(T("Add Details")))
#db[table].embalming.comment = DIV(A(T("Add Details")))
#db[table].dna.comment = DIV(A(T("Add Details")))
#db[table].dental.comment = DIV(A(T("Add Details")))
#db[table].exit_morgue.comment = DIV(A(T("Add Details")))
