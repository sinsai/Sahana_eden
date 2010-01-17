# -*- coding: utf-8 -*-

module = 'rms'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)

# Request Aid
rms_request_aid_type_opts = {
    1:T('Food'),
    2:T('Find'),
    3:T('Water'),
    4:T('Medicine'),
    5:T('Shelter'),
    6:T('Report'),
    }

resource = 'request_aid'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', length=128, notnull=True, unique=True),
                Field('type', 'integer'),
                migrate=migrate)

db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].type.requires = IS_NULL_OR(IS_IN_SET(rms_request_aid_type_opts))
db[table].type.represent = lambda opt: opt and rms_request_aid_type_opts[opt]
db[table].type.label = T('Type')

ADD_REQUEST_AID = T('Request Aid')
title_create = T('Add Aid Request')
title_display = T('Aid Reqest Details')
title_list = T('List Aid Requests')
title_update = T('Edit Aid Request')
title_search = T('Search Aid Request')
subtitle_create = T('Add New Aid Request')
subtitle_list = T('Aid Requests')
label_list_button = T('List Aid Requests')
label_create_button = ADD_REQUEST_AID
msg_record_created = T('Aid request added')
msg_record_modified = T('Aid request updated')
msg_record_deleted = T('Aid request deleted')
msg_list_empty = T('No aid requests available')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Pledge Aid
rms_pledge_aid_type_opts = rms_request_aid_type_opts

resource = 'pledge_aid'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', notnull=True),
                Field('type', 'integer'),
                migrate=migrate)

db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].type.requires = IS_NULL_OR(IS_IN_SET(rms_pledge_aid_type_opts))
db[table].type.represent = lambda opt: opt and rms_pledge_aid_type_opts[opt]
db[table].type.label = T('Type')

title_create = T('Add Pledge of Aid')
title_display = T('Pledge Details')
title_list = T('List Pledges')
title_update = T('Edit Pledges')
title_search = T('Search Pledges')
subtitle_create = T('Add New Pledge of Aid')
subtitle_list = T('Pledges')
label_list_button = T('List Pledges')
label_create_button = T('Add Pledge')
msg_record_created = T('Pledge added')
msg_record_modified = T('Pledge updated')
msg_record_deleted = T('Pledge deleted')
msg_list_empty = T('No pledges currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
