# -*- coding: utf-8 -*-

module='vtt'

# Settings
resource='setting'
table=module+'_'+resource
db.define_table(table,
                db.Field('audit_read','boolean'),
                db.Field('audit_write','boolean'))
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read=False,
        audit_write=False
    )

# Person Item Type
resource='item_type'
table=module+'_'+resource
db.define_table(table,
                db.Field('description')
               )
db[table].description.requires=IS_NOT_IN_DB(db, '%s.description' % table)
title_create=T('Add Person Item Type')
title_display=T('Person Item Types')
title_list=T('List Person Item Types')
title_update=T('Edit Person Item Types')
title_search=T('Search Person Item Types')
subtitle_create=T('Add New Person Item Type')
subtitle_list=T('Person Item Types')
label_list_button=T('List Person Item Types')
label_create_button=T('Add Person Item Type')
msg_record_created=T('Person Item Type added')
msg_record_modified=T('Person Item Type updated')
msg_record_deleted=T('Person Item Type deleted')
msg_list_empty=T('No Person Item Types currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Person Item
resource='item'
table=module+'_'+resource
db.define_table(table,uuidstamp,
                db.Field('opt_type', db.vtt_item_type),
               )
db[table].uuid.requires=IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].opt_type.requires=IS_IN_DB(db, 'vtt_item_type.id', 'vtt_item_type.description')
title_create=T('Add Person Item')
title_display=T('Person Items')
title_list=T('List Person Items')
title_update=T('Edit Person Items')
title_search=T('Search Person Items')
subtitle_create=T('Add New Person Item')
subtitle_list=T('Person Items')
label_list_button=T('List Person Items')
label_create_button=T('Add Person Item')
msg_record_created=T('Person Item added')
msg_record_modified=T('Person Item updated')
msg_record_deleted=T('Person Item deleted')
msg_list_empty=T('No Person Items currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Tag Type
resource='tag_type'
table=module+'_'+resource
db.define_table(table,
                db.Field('description')
               )
db[table].description.requires=IS_NOT_IN_DB(db, '%s.description' % table)
title_create=T('Add Tag Type')
title_display=T('Tag Types')
title_list=T('List Tag Types')
title_update=T('Edit Tag Types')
title_search=T('Search Tag Types')
subtitle_create=T('Add New Tag Type')
subtitle_list=T('Tag Types')
label_list_button=T('List Tag Types')
label_create_button=T('Add Tag Type')
msg_record_created=T('Tag Type added')
msg_record_modified=T('Tag Type updated')
msg_record_deleted=T('Tag Type deleted')
msg_list_empty=T('No Tag Types currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Tag
resource='tag'
table=module+'_'+resource
db.define_table(table,
                db.Field('opt_type',db.vtt_tag_type),
                db.Field('label',length=256), #value assigned for the tag
                db.Field('item_id', db.vtt_item)
               )
db[table].opt_type.requires=IS_IN_DB(db, 'vtt_tag_type.id', 'vtt_tag_type.description')
db[table].item_id.requires=IS_IN_DB(db, 'vtt_item.uuid')
title_create=T('Add Tag')
title_display=T('Tags')
title_list=T('List Tags')
title_update=T('Edit Tags')
title_search=T('Search Tags')
subtitle_create=T('Add New Tag')
subtitle_list=T('Tags')
label_list_button=T('List Tags')
label_create_button=T('Add Tag')
msg_record_created=T('Tag added')
msg_record_modified=T('Tag updated')
msg_record_deleted=T('Tag deleted')
msg_list_empty=T('No Tags currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Person Entity To Person Item
resource='item_to_pe'
table=module+'_'+resource
db.define_table(table,timestamp,
                db.Field('pe_id',db.pe_entity),
                db.Field('item_id',db.vtt_item))
db[table].pe_id.label='Person Entity'
db[table].item_id.requires=IS_IN_DB(db,'vtt_item.id')
db[table].item_id.label='Person Item'

# Composition
resource='item_to_item'
table=module+'_'+resource
db.define_table(table,timestamp,
                db.Field('item_id',db.vtt_item),
                db.Field('item_belongsto_id',db.vtt_item))
db[table].item_id.label='Person Item'
db[table].item_id.requires=IS_IN_DB(db,'vtt_item.uuid')
db[table].item_belongsto_id.requires=IS_IN_DB(db,'vtt_item.uuid')
db[table].item_belongsto_id.label='Belongs to Person Item'


# Observer Type
resource='observer_type'
table=module+'_'+resource
db.define_table(table,
                db.Field('description')
               )
db[table].description.requires=IS_NOT_IN_DB(db, '%s.description' % table)
title_create=T('Add Observer Type')
title_display=T('Observer Types')
title_list=T('List Observer Types')
title_update=T('Edit Observer Types')
title_search=T('Search Observer Types')
subtitle_create=T('Add New Observer Type')
subtitle_list=T('Observer Types')
label_list_button=T('List Observer Types')
label_create_button=T('Add Observer Type')
msg_record_created=T('Observer Type added')
msg_record_modified=T('Observer Type updated')
msg_record_deleted=T('Observer Type deleted')
msg_list_empty=T('No Observer Types currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Observer
resource='observer'
table=module+'_'+resource
db.define_table(table,uuidstamp,
                db.Field('opt_type',db.vtt_observer_type),
                individual_id,
                db.Field('service')
               )
db[table].opt_type.requires=IS_IN_DB(db, 'vtt_observer_type.id', 'vtt_tag_type.description')
#db[table].pe_id.requires=IS_IN_DB(db, 'pe_entity.uuid')
title_create=T('Add Observer')
title_display=T('Observers')
title_list=T('List Observers')
title_update=T('Edit Observers')
title_search=T('Search Observers')
subtitle_create=T('Add New Observer')
subtitle_list=T('Observers')
label_list_button=T('List Observers')
label_create_button=T('Add Observer')
msg_record_created=T('Observer added')
msg_record_modified=T('Observer updated')
msg_record_deleted=T('Observer deleted')
msg_list_empty=T('No Observers currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Reporter Type
resource='reporter_type'
table=module+'_'+resource
db.define_table(table,
                db.Field('description')
               )
db[table].description.requires=IS_NOT_IN_DB(db, '%s.description' % table)
title_create=T('Add Reporter Type')
title_display=T('Reporter Types')
title_list=T('List Reporter Types')
title_update=T('Edit Reporter Types')
title_search=T('Search Reporter Types')
subtitle_create=T('Add New Reporter Type')
subtitle_list=T('Reporter Types')
label_list_button=T('List Reporter Types')
label_create_button=T('Add Reporter Type')
msg_record_created=T('Reporter Type added')
msg_record_modified=T('Reporter Type updated')
msg_record_deleted=T('Reporter Type deleted')
msg_list_empty=T('No Reporter Types currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Reporter
resource='reporter'
table=module+'_'+resource
db.define_table(table,uuidstamp,
                db.Field('opt_type',db.vtt_reporter_type),
                individual_id,
                db.Field('service')
               )
db[table].opt_type.requires=IS_IN_DB(db, 'vtt_reporter_type.id', 'vtt_tag_type.description')
#db[table].pe_id.requires=IS_IN_DB(db, 'pe_entity.uuid')
title_create=T('Add Reporter')
title_display=T('Reporters')
title_list=T('List Reporters')
title_update=T('Edit Reporters')
title_search=T('Search Reporters')
subtitle_create=T('Add New Reporter')
subtitle_list=T('Reporters')
label_list_button=T('List Reporters')
label_create_button=T('Add Reporter')
msg_record_created=T('Reporter added')
msg_record_modified=T('Reporter updated')
msg_record_deleted=T('Reporter deleted')
msg_list_empty=T('No Reporters currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Presence
resource='presence'
table=module+'_'+resource
db.define_table(table,timestamp,
                db.Field('item',db.vtt_item),
                location_id,
                db.Field('currentness'),
                db.Field('time_start', 'date'),
                db.Field('time_end','date'),
                db.Field('observer',db.vtt_observer),
                db.Field('reporter',db.vtt_reporter),
                db.Field('obs_time','date'),
                db.Field('rep_time','date'),
                db.Field('location_radius'),
                db.Field('condition')
               )
db[table].item.requires=IS_IN_DB(db,'vtt_item.uuid')
db[table].currentness.requires=IS_IN_SET(['past','current','planned'])
db[table].time_start.requires=IS_DATE(T("%Y-%m-%d")) # Can use Translation to provide localised formatting
db[table].time_end.requires=IS_DATE(T("%Y-%m-%d")) # Can use Translation to provide localised formatting
db[table].observer.requires=IS_IN_DB(db,'vtt_observer.uuid')
db[table].reporter.requires=IS_IN_DB(db,'vtt_reporter.uuid')
db[table].obs_time.requires=IS_DATE(T("%Y-%m-%d")) # Can use Translation to provide localised formatting
db[table].rep_time.requires=IS_DATE(T("%Y-%m-%d")) # Can use Translation to provide localised formatting
db[table].condition.requires=IS_IN_SET(['recovery','registration','transit','processing','accomodation','disposal'])
title_create=T('Add Presence')
title_display=T('Presences')
title_list=T('List Presences')
title_update=T('Edit Presences')
title_search=T('Search Presences')
subtitle_create=T('Add New Presence')
subtitle_list=T('Presences')
label_list_button=T('List Presences')
label_create_button=T('Add Presence')
msg_record_created=T('Presence added')
msg_record_modified=T('Presence updated')
msg_record_deleted=T('Presence deleted')
msg_list_empty=T('No Presences currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Role
resource='role'
table=module+'_'+resource
db.define_table(table,
                db.Field('description')
               )
db[table].description.requires=IS_NOT_IN_DB(db, '%s.description' % table)
title_create=T('Add Role')
title_display=T('Roles')
title_list=T('List Roles')
title_update=T('Edit Roles')
title_search=T('Search Roles')
subtitle_create=T('Add New Role')
subtitle_list=T('Roles')
label_list_button=T('List Role')
label_create_button=T('Add Role')
msg_record_created=T('Role added')
msg_record_modified=T('Role updated')
msg_record_deleted=T('Role deleted')
msg_list_empty=T('No Roles currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Process
resource='process'
table=module+'_'+resource
db.define_table(table,
                db.Field('description')
               )
db[table].description.requires=IS_NOT_IN_DB(db, '%s.description' % table)
title_create=T('Add Process')
title_display=T('Processes')
title_list=T('List Processes')
title_update=T('Edit Processes')
title_search=T('Search Processes')
subtitle_create=T('Add New Process')
subtitle_list=T('Processes')
label_list_button=T('List Processes')
label_create_button=T('Add Process')
msg_record_created=T('Process added')
msg_record_modified=T('Process updated')
msg_record_deleted=T('Process deleted')
msg_list_empty=T('No Process currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Status Transition
resource='status_transition'
table=module+'_'+resource
db.define_table(table,
                db.Field('old_status'),
                db.Field('new_status')
               )
title_create=T('Add Status Transition')
title_display=T('Status Transitions')
title_list=T('List Status Transitions')
title_update=T('Edit Status Transitions')
title_search=T('Search Status Transitions')
subtitle_create=T('Add New Status Transition')
subtitle_list=T('Status Transitions')
label_list_button=T('List Status Transitions')
label_create_button=T('Add Status Transition')
msg_record_created=T('Status Transition added')
msg_record_modified=T('Status Transition updated')
msg_record_deleted=T('Status Transition deleted')
msg_list_empty=T('No Status Transition currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Item To Role
resource='item_to_role'
table=module+'_'+resource
db.define_table(table,timestamp,
                db.Field('role_id',db.vtt_role),
                db.Field('item_id',db.vtt_item))
db[table].item_id.requires=IS_IN_DB(db,'vtt_item.id')
db[table].role_id.requires=IS_IN_DB(db,'vtt_role.id')

# Role To Process
resource='role_to_process'
table=module+'_'+resource
db.define_table(table,timestamp,
                db.Field('role_id',db.vtt_role),
                db.Field('process_id',db.vtt_item))
db[table].process_id.requires=IS_IN_DB(db,'vtt_process.id')
db[table].role_id.requires=IS_IN_DB(db,'vtt_role.id')

# Process To Status Transition
resource='process_to_st'
table=module+'_'+resource
db.define_table(table,timestamp,
                db.Field('st_id',db.vtt_status_transition),
                db.Field('process_id',db.vtt_item))
db[table].process_id.requires=IS_IN_DB(db,'vtt_process.id')
db[table].st_id.requires=IS_IN_DB(db,'vtt_status_transition.id','vtt_status_transition.old_status', 'vtt_status_transition.new_status')


# Transition AT Presence
resource='transition_at_presence'
table=module+'_'+resource
db.define_table(table,timestamp,
                db.Field('transition_id',db.vtt_process_to_st),
                db.Field('presence_id',db.vtt_presence))
db[table].transition_id.requires=IS_IN_DB(db,'vtt_process_to_st.id')
db[table].presence_id.requires=IS_IN_DB(db,'vtt_presence.id')
