# -*- coding: utf-8 -*-

module = 'mpr'

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

resource = 'person'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                person_id,
                Field('last_seen'),
                Field('last_clothing'),
                Field('comments', length=256),
                migrate=migrate)
db[table].person_id.label = 'Person'
title_create = T('Add Person')
title_display = T('Person Details')
title_list = T('List People')
title_update = T('Edit Person')
title_search = T('Search People')
subtitle_create = T('Add New Person')
subtitle_list = T('People')
label_list_button = T('List People')
label_create_button = T('Add Person')
msg_record_created = T('Person added')
msg_record_modified = T('Person updated')
msg_record_deleted = T('Person deleted')
msg_list_empty = T('No People currently registered')
s3.crud_strings[table] = Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, title_search=title_search, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)
