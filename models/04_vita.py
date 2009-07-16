# -*- coding: utf-8 -*-

#
# Person Tracking and Tracing (VITA)
#
# created 2009-07-14 by nursix
#

module = 'vita'

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
# Person-Item
# An person item represents a physical appearance of a person entity, either its bodily
# appearance (personal presence or dead body), or any item that belongs to it (clothes,
# luggage, personal effects etc.) Every person item can be tracked separately, if
# necessary - if not, then it is tracked together with the super-item it is part of
#
resource='item_class'
table=module+'_'+resource
db.define_table(table,
                db.Field('name')
               )
db[table].name.requires=IS_NOT_IN_DB(db, '%s.name' % table)

if not len(db().select(db[table].ALL)):
   db[table].insert(name = "Personal Presence")
   db[table].insert(name = "Dead Body")
   db[table].insert(name = "Personal Belongings")

# Reusable field for other tables to reference
opt_item_class = SQLTable(None, 'opt_item_class',
                 db.Field('item_class', db.vita_item_class,
                 requires = IS_NULL_OR(IS_IN_DB(db, 'vita_item_class.id', 'vita_item_class.name')),
                 represent = lambda id: (id and [db(db.vita_item_class.id==id).select()[0].name] or ["None"])[0],
                 comment = None,
                 ondelete = 'RESTRICT'
                 ))

resource='tag_type'
table=module+'_'+resource
db.define_table(table,
                db.Field('name')
               )
db[table].name.requires=IS_NOT_IN_DB(db, '%s.name' % table)

if not len(db().select(db[table].ALL)):
   db[table].insert(name = "Barcode Label")
   db[table].insert(name = "Number Tag")

# Reusable field for other tables to reference
opt_tag_type = SQLTable(None, 'opt_tag_type',
                 db.Field('tag_type', db.vita_tag_type,
                 requires = IS_NULL_OR(IS_IN_DB(db, 'vita_tag_type.id', 'vita_tag_type.name')),
                 represent = lambda id: (id and [db(db.vita_tag_type.id==id).select()[0].name] or ["None"])[0],
                 comment = None,
                 ondelete = 'RESTRICT'
                 ))

resource = 'pitem'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                opt_tag_type,                       # Tag Type
                Field('tag_label'),                 # Tag Label
                opt_item_class,                     # Item Class
                Field('description'),               # Short Description
                Field('details','text'),            # Detailed Description
                Field('comment'))                   # a comment (optional)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

title_create = T('Add Item')
title_display = T('Item Details')
title_list = T('List Items')
title_update = T('Edit Item')
title_search = T('Search Items')
subtitle_create = T('Add New Item')
subtitle_list = T('Items')
label_list_button = T('List Items')
label_create_button = T('Add Item')
msg_record_created = T('Item added')
msg_record_modified = T('Item updated')
msg_record_deleted = T('Item deleted')
msg_list_empty = T('No items currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Reusable field for other tables to reference
pitem_id = SQLTable(None, 'pitem_id',
                Field('pitem_id', db.vita_pitem,
                requires = IS_NULL_OR(IS_IN_DB(db, 'vita_pitem.id', '%(tag_label)s: %(description)s')),
                represent = lambda id: (id and [db(db.vita_pitem.id==id).select()[0].tag_label] or ["None"])[0],
                comment = DIV(A(T('Add Item'), _class='popup', _href=URL(r=request, c='vita', f='pitem', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Item|New Personal Presence, Body or Item."))),
                ondelete = 'RESTRICT'
                ))

#
# Presence
# A presence is a documented sighting of a personal item, and tracks locations over time
# as well as status changes of a person or their belongings
#

resource = 'presence'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                pitem_id,                           # Personal Item Reference
                Field('description'),               # Short Description
                Field('details','text'),            # Detailed Description
                Field('comment'))                   # a comment (optional)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
