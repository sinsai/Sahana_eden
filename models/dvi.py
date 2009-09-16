# -*- coding: utf-8 -*-

#
# DVI Disaster Victim Identification
#
# created 2009-08-06 by nursix
#

module = 'dvi'

# Settings
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
dvi_task_status_opts = {
    1:T('New'),
    2:T('Assigned'),
    3:T('In Progress'),
    4:T('Completed')
    }

opt_dvi_task_status = SQLTable(None, 'opt_dvi_task_status',
                    db.Field('opt_dvi_task_status','integer',
                    requires = IS_IN_SET(dvi_task_status_opts),
                    default = 1,
                    label = T('Task Status'),
                    represent = lambda opt: opt and dvi_task_status_opts[opt]))

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
                pr_pe_id,
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
db[table].recovery.requires = IS_IN_SET(dvi_task_status_opts)
db[table].personal_effects.requires = IS_IN_SET(dvi_task_status_opts)
db[table].body_radiology.requires = IS_IN_SET(dvi_task_status_opts)
db[table].fingerprints.requires = IS_IN_SET(dvi_task_status_opts)
db[table].anthropology.requires = IS_IN_SET(dvi_task_status_opts)
db[table].pathology.requires = IS_IN_SET(dvi_task_status_opts)
db[table].embalming.requires = IS_IN_SET(dvi_task_status_opts)
db[table].dna.requires = IS_IN_SET(dvi_task_status_opts)
db[table].dental.requires = IS_IN_SET(dvi_task_status_opts)

#comments
db[table].personal_effects.comment = DIV(A(T('Add Details'), _class='thickbox', _href=URL(r=request, c='dvi', f='personal_effects', args='create', vars=dict(format='popup')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Personal Effects|Record data about personal belongings")))
db[table].body_radiology.comment = DIV(A(T("Add Details"), _class='thickbox', _href=URL(r=request, c='dvi', f='radiology', args='create', vars=dict(format='popup')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Radiology|Record Radiology data.")))
db[table].fingerprints.comment = DIV(A(T("Add Details"), _class='thickbox', _href=URL(r=request, c='dvi', f='fingerprints', args='create', vars=dict(format='popup')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Fingerprints Details|Record fingerprint data .")))
db[table].anthropology.comment = DIV(A(T("Add Details"), _class='thickbox', _href=URL(r=request, c='dvi', f='anthropology', args='create', vars=dict(format='popup')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Anthroplogy|Record Anthropology details.")))
db[table].pathology.comment = DIV(A(T("Add Details"), _class='thickbox', _href=URL(r=request, c='dvi', f='pathology', args='create', vars=dict(format='popup')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Pathology|Record Pathology Details.")))
db[table].dna.comment = DIV(A(T("Add Details"), _class='thickbox', _href=URL(r=request, c='dvi', f='dna', args='create', vars=dict(format='popup')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("DNA Exam|Record DNA Exam Details.")))
db[table].dental.comment = DIV(A(T("Add Details"), _class='thickbox', _href=URL(r=request, c='dvi', f='dental', args='create', vars=dict(format='popup')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Dental|Record Dental Examination Details.")))
