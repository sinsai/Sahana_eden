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
                requires = IS_NULL_OR(IS_IN_DB(db, 'hrm_find.id', '%(find_date)s: %(location_details)s, %(bodies_est)s bodies')),
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
db[table].pr_pe_parent.requires = IS_NULL_OR(IS_PE_ID(db, pr_pentity_class_opts, filter_opts=(3,)))

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

#
# Personal Effects ------------------------------------------------------------------------
#

resource = 'personal_effects'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status, 
                pr_pe_id,
#                pcase_id,
                person_id,
                db.Field('clothing'),    #TODO: elaborate
                db.Field('jewellery'),   #TODO: elaborate  
                db.Field('footwear'),    #TODO: elaborate
                db.Field('watch'),       #TODO: elaborate
                db.Field('other'),
                migrate = migrate)

# Settings and Restrictions

# Labels
db[table].person_id.label = T('Observer')

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

#
# Radiology ------------------------------------------------------------------------
#

resource = 'radiology'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status, 
                pr_pe_id,
#               pcase_id,
                person_id,
                db.Field('number_of_images', 'integer'),
                db.Field('findings'),    #TODO: elaborate  
                db.Field('conclusion'),    #TODO: elaborate
                db.Field('date', 'date'),       #TODO: elaborate
                db.Field('other_details'),       #TODO: elaborate
                migrate = migrate)
# Restrictions

# Labels
db[table].person_id.label = T('Radiologist')
db[table].date.label = T('Date of Examination')

# CRUD Strings
title_create = T('Add Radiology Details')
title_display = T('Radiology Details')
title_list = T('List Radiology Details')
title_update = T('Edit Radiology Details')
title_search = T('Search Radiology')
subtitle_create = T('Add New Entry')
subtitle_list = T('Radiology')
label_list_button = T('List Records')
label_create_button = T('Add Radiology')
msg_record_created = T('Record added')
msg_record_modified = T('Record updated')
msg_record_deleted = T('Record deleted')
msg_list_empty = T('No Details currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

resource = 'fingerprints'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status, 
                pr_pe_id,
#               pcase_id,
                person_id,
                db.Field('condition_of_hands'),
                db.Field('finger_printed'),    #TODO: elaborate  
                db.Field('conclusion'),    #TODO: elaborate
                db.Field('date', 'date'),       #TODO: elaborate
                db.Field('other_details'),       #TODO: elaborate
                migrate = migrate)
# Restrictions

# Labels
db[table].person_id.label = T('Examiner')
db[table].date.label = T('Date of Examination')

# CRUD Strings
title_create = T('Add Fingerprint Details')
title_display = T('Fingerprint Details')
title_list = T('List Fingerprint Details')
title_update = T('Edit Fingerprint Details')
title_search = T('Search Fingerprint')
subtitle_create = T('Add New Entry')
subtitle_list = T('Fingerprint')
label_list_button = T('List Records')
label_create_button = T('Add Fingerprint')
msg_record_created = T('Record added')
msg_record_modified = T('Record updated')
msg_record_deleted = T('Record deleted')
msg_list_empty = T('No Details currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

resource = 'anthropology'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status, 
                pr_pe_id,
#               pcase_id,
                person_id,
                db.Field('condition_of_remains'),
                db.Field('report'),         #TODO: elaborate  
                db.Field('cause_of_death'), #TODO: elaborate
                db.Field('manner_of_death'),    #TODO: elaborate
                db.Field('other_details'),      #TODO: elaborate
                db.Field('date', 'date'),
                migrate = migrate)
# Restrictions

# Labels
db[table].person_id.label = T('Examiner')
db[table].date.label = T('Date of Examination')

# CRUD Strings
title_create = T('Add Anthropology Details')
title_display = T('Anthropology Details')
title_list = T('List Anthropology Details')
title_update = T('Edit Anthropology Details')
title_search = T('Search Anthropology')
subtitle_create = T('Add New Entry')
subtitle_list = T('Anthropology')
label_list_button = T('List Records')
label_create_button = T('Add Anthropology')
msg_record_created = T('Record added')
msg_record_modified = T('Record updated')
msg_record_deleted = T('Record deleted')
msg_list_empty = T('No Details currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

resource = 'pathology'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status, 
                pr_pe_id,
#               pcase_id,
                person_id,
                db.Field('condition_of_remains'),
                db.Field('physical_description'), #TODO: elaborate  
                db.Field('details'),      #TODO: elaborate
                db.Field('unique_features'),  #TODO: elaborate
                db.Field('other_details'),        #TODO: elaborate
                db.Field('date', 'date'),
                migrate = migrate)
# Restrictions

# Labels
db[table].person_id.label = T('Pathologist')
db[table].date.label = T('Date of Examination')

# CRUD Strings
title_create = T('Add Pathology Details')
title_display = T('Pathology Details')
title_list = T('List Pathology Details')
title_update = T('Edit Pathology Details')
title_search = T('Search Pathology')
subtitle_create = T('Add New Entry')
subtitle_list = T('Pathology')
label_list_button = T('List Records')
label_create_button = T('Add Pathology')
msg_record_created = T('Record added')
msg_record_modified = T('Record updated')
msg_record_deleted = T('Record deleted')
msg_list_empty = T('No Details currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

resource = 'dna'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status, 
                pr_pe_id,
#               pcase_id,
                person_id,
                db.Field('size_of_specimen'),
                db.Field('description_of_specimen'),  #TODO: elaborate  
                db.Field('notes'),            #TODO: elaborate
                db.Field('additional_information'),               #TODO: elaborate
                db.Field('other_details'),        #TODO: elaborate
                db.Field('date', 'date'),
                migrate = migrate)
# Restrictions

# Labels
db[table].person_id.label = T('Examiner')
db[table].date.label = T('Date of Examination')

# CRUD Strings
title_create = T('Add DNA Details')
title_display = T('DNA Details')
title_list = T('List DNA Details')
title_update = T('Edit DNA Details')
title_search = T('Search DNA Details')
subtitle_create = T('Add New Entry')
subtitle_list = T('DNA Details')
label_list_button = T('List Records')
label_create_button = T('Add DNA Details')
msg_record_created = T('Record added')
msg_record_modified = T('Record updated')
msg_record_deleted = T('Record deleted')
msg_list_empty = T('No Details currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)


resource = 'dental'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status, 
                pr_pe_id,
#               pcase_id,
                person_id,
                db.Field('dental_finding'),
                db.Field('specific_description'), #TODO: elaborate  
                db.Field('conclusion'),           #TODO: elaborate
                db.Field('additional_information'),               #TODO: elaborate
                db.Field('other_details'),        #TODO: elaborate
                db.Field('date', 'date'),
                migrate = migrate)
# Restrictions

# Labels
db[table].person_id.label = T('Examiner')
db[table].date.label = T('Date of Examination')

# CRUD Strings
title_create = T('Add Dental Details')
title_display = T('Dental Details')
title_list = T('List Dental Details')
title_update = T('Edit Dental Details')
title_search = T('Search Dental Details')
subtitle_create = T('Add New Entry')
subtitle_list = T('Dental Details')
label_list_button = T('List Records')
label_create_button = T('Add Dental Details')
msg_record_created = T('Record added')
msg_record_modified = T('Record updated')
msg_record_deleted = T('Record deleted')
msg_list_empty = T('No Details currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

#
# PM Data Collection 
#


#
# Checklist of Operation
# 
resource = 'operation_checklist'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_fieldset,
                pcase_id,
                db.Field('recovery'),
                db.Field('personal_effects'),
                db.Field('body_radiology'),
                db.Field('fingerprints'),
                db.Field('anthropology'),
                db.Field('pathology'),
                db.Field('embalming'),
                db.Field('dna'),
                db.Field('dental'),
                migrate = migrate)
# restrictions                
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].recovery.requires = IS_IN_SET(hrm_task_status_opts)
db[table].personal_effects.requires = IS_IN_SET(hrm_task_status_opts)
db[table].body_radiology.requires = IS_IN_SET(hrm_task_status_opts)
db[table].fingerprints.requires = IS_IN_SET(hrm_task_status_opts)
db[table].anthropology.requires = IS_IN_SET(hrm_task_status_opts)
db[table].pathology.requires = IS_IN_SET(hrm_task_status_opts)
db[table].embalming.requires = IS_IN_SET(hrm_task_status_opts)
db[table].dna.requires = IS_IN_SET(hrm_task_status_opts)
db[table].dental.requires = IS_IN_SET(hrm_task_status_opts)

#comments
db[table].personal_effects.comment =  comment = DIV(A(T('Add Details'), _class='popup', _href=URL(r=request, c='hrm', f='personal_effects', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Personal Effects|Record data about personal belongings")))
db[table].body_radiology.comment = DIV(A(T("Add Details"), _class='popup', _href=URL(r=request, c='hrm', f='radiology', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Radiology|Record Radiology data.")))
db[table].fingerprints.comment = DIV(A(T("Add Details"), _class='popup', _href=URL(r=request, c='hrm', f='fingerprints', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Fingerprints Details|Record fingerprint data .")))
db[table].anthropology.comment = DIV(A(T("Add Details"), _class='popup', _href=URL(r=request, c='hrm', f='anthropology', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Anthroplogy|Record Anthropology details.")))
db[table].pathology.comment = DIV(A(T("Add Details"), _class='popup', _href=URL(r=request, c='hrm', f='pathology', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Pathology|Record Pathology Details.")))
db[table].dna.comment = DIV(A(T("Add Details"), _class='popup', _href=URL(r=request, c='hrm', f='dna', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("DNA Exam|Record DNA Exam Details.")))
db[table].dental.comment = DIV(A(T("Add Details"), _class='popup', _href=URL(r=request, c='hrm', f='dental', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Dental|Record Dental Examination Details.")))


