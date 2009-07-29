# -*- coding: utf-8 -*-

module = 'lms'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                db.Field('audit_read', 'boolean'),
                db.Field('audit_write', 'boolean'),
                migrate=migrate)
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read = False,
        audit_write = False
    )
# Sites Category
#resource = 'site_category'
#table = module + '_' + resource
#db.define_table(table,timestamp,uuidstamp,
#                db.Field('name', notnull=True),
#                db.Field('description', length=256),
#                db.Field('comments', 'text'),
#                migrate=migrate)
#db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
#db[table].name.requires = IS_NOT_EMPTY()   # Sites don't have to have unique names
#db[table].name.label = T("Site Category")
#db[table].name.comment = SPAN("*", _class="req")
#title_create = T('Add Site Category')
#title_display = T('Site Category Details')
#title_list = T('List Categories')
#title_update = T('Edit Category')
#title_search = T('Search Category(s)')
#subtitle_create = T('Add New Site Category')
#subtitle_list = T('Site Categories')
#label_list_button = T('List Categories')
#label_create_button = T('Add Site Category')
#msg_record_created = T('Category  added')
#msg_record_modified = T('Category updated')
#msg_record_deleted = T('Category deleted')
#msg_list_empty = T('No Categories currently registered')
#s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Sites
resource = 'site'
table = module + '_' + resource
db.define_table(table,timestamp,uuidstamp,
                db.Field('name', notnull=True),
                db.Field('description', length=256),
                db.Field('category'),
                admin_id,
                location_id,
                person_id,
                db.Field('address', 'text'),
                db.Field('comments'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()   # Sites don't have to have unique names
# db[table].site_category_id.requires = IS_IN_DB(db, 'lms_site_category.id', 'lms_site_category.name')
db[table].category.requires=IS_IN_SET(['warehouse'])
# db[table].site_category_id.comment = DIV(A(T('Add Category'), _class='popup', _href=URL(r=request, c='lms', f='site_category', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Site Category|The Category of Site.")))
db[table].name.label = T("Site Name")
db[table].name.comment = SPAN("*", _class="req")
db[table].admin.label = T("Site Manager")
db[table].person_id.label = T("Contact Person")
title_create = T('Add Site ')
title_display = T('Site Details')
title_list = T('List Sites')
title_update = T('Edit Site')
title_search = T('Search Site(s)')
subtitle_create = T('Add New Site')
subtitle_list = T('Sites')
label_list_button = T('List Sites')
label_create_button = T('Add Site')
msg_record_created = T('Site added')
msg_record_modified = T('Site updated')
msg_record_deleted = T('Site deleted')
msg_list_empty = T('No Sites currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Storage Locations
resource = 'storage_loc'
table = module + '_' + resource
db.define_table(table,timestamp,uuidstamp,
                db.Field('name', notnull=True),
                db.Field('description', length=256),
                db.Field('site_id', db.lms_site),
                location_id,
                db.Field('dimension'),
                db.Field('area'),
                db.Field('height'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()   # Storage Locations don't have to have unique names
db[table].site_id.requires = IS_IN_DB(db, 'lms_site.id', 'lms_storage_loc.name')
db[table].site_id.comment = DIV(A(T('Add Site'), _class='popup', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Site|Add the main Warehouse/Site information where this Storage location is.")))
db[table].name.label = T("Storage Location Name")
db[table].name.comment = SPAN("*", _class="req")
title_create = T('Add Storage Location ')
title_display = T('Storage Location Details')
title_list = T('List Storage Location')
title_update = T('Edit Storage Location')
title_search = T('Search Storage Location(s)')
subtitle_create = T('Add New Site')
subtitle_list = T('Storage Locations')
label_list_button = T('List Storage Locations')
label_create_button = T('Add Storage Location')
msg_record_created = T('Storage Location added')
msg_record_modified = T('Storage Location updated')
msg_record_deleted = T('Storage Location deleted')
msg_list_empty = T('No Storage Locations currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Storage Bins
resource = 'storage_bin'
table = module + '_' + resource
db.define_table(table,timestamp,uuidstamp,
                db.Field('number', notnull=True),
                db.Field('bin_type'),
                db.Field('storage_id', db.lms_storage_loc),
                db.Field('total_capacity', length=256),
                db.Field('max_weight'),
                db.Field('comments', 'text'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].number.requires = IS_NOT_EMPTY()   # Storage Bin Numbers don't have to have unique names
db[table].storage_id.requires = IS_IN_DB(db, 'lms_storage_loc.id', 'lms_storage_loc.name')
db[table].storage_id.comment = DIV(A(T('Add Storage Location'), _class='popup', _href=URL(r=request, c='lms', f='storage_loc', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Site|Add the Storage Location where this bin is located.")))
db[table].number.label = T("Storage Bin Number")
db[table].number.comment = SPAN("*", _class="req")
title_create = T('Add Storage Bin ')
title_display = T('Storage Bin Details')
title_list = T('List Storage Bins')
title_update = T('Edit Storage Bins')
title_search = T('Search Storage Bin(s)')
subtitle_create = T('Add New Bin')
subtitle_list = T('Storage Bins')
label_list_button = T('List Storage Bins')
label_create_button = T('Add Storage Bins')
msg_record_created = T('Storage Bin added')
msg_record_modified = T('Storage Bin updated')
msg_record_deleted = T('Storage Bin deleted')
msg_list_empty = T('No Storage Bins currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
