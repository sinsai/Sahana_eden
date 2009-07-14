# -*- coding: utf-8 -*-

module = 'cr'

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

# Shelters
resource = 'shelter'
table = module + '_' + resource
db.define_table(table,timestamp,uuidstamp,
                Field('name', notnull=True),
                Field('description', length=256),
                admin_id,
                location_id,
                person_id,
                Field('address', 'text'),
                Field('capacity', 'integer'),
                Field('dwellings', 'integer'),
                Field('persons_per_dwelling', 'integer'),
                Field('area'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()   # Shelters don't have to have unique names
db[table].name.label = T("Shelter Name")
db[table].name.comment = SPAN("*", _class="req")
db[table].admin.label = T("Shelter Manager")
db[table].person_id.label = T("Contact Person")
db[table].capacity.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999))
db[table].dwellings.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
db[table].persons_per_dwelling.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999))
title_create = T('Add Shelter')
title_display = T('Shelter Details')
title_list = T('List Shelters')
title_update = T('Edit Shelter')
title_search = T('Search Shelters')
subtitle_create = T('Add New Shelter')
subtitle_list = T('Shelters')
label_list_button = T('List Shelters')
label_create_button = T('Add Shelter')
msg_record_created = T('Shelter added')
msg_record_modified = T('Shelter updated')
msg_record_deleted = T('Shelter deleted')
msg_list_empty = T('No Shelters currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
