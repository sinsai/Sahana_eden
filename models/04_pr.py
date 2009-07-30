# -*- coding: utf-8 -*-

#
# Sahanapy VITA - Part 04_pr: Person Tracking and Tracing
#
# created 2009-07-23 by nursix
#

module = 'pr'

#
# Option Fields ---------------------------------------------------------------
#

pr_pitem_class_opts = {
    1:T('Personal Presence'),
    2:T('Dead Body'),
    3:T('Personal Belongings')
    }

opt_pr_pitem_class = SQLTable(None, 'opt_pr_pitem_class',
                    db.Field('opt_pr_pitem_class','integer',
                    requires = IS_IN_SET(pr_pitem_class_opts),
                    default = 1,
                    represent = lambda opt: opt and pr_pitem_class_opts[opt]))

pr_tag_type_opts = {
    1:T('None'),
    2:T('Number Tag'),
    3:T('Barcode Label')
    }

opt_pr_tag_type = SQLTable(None, 'opt_pr_tag_type',
                    db.Field('opt_pr_tag_type','integer',
                    requires = IS_IN_SET(pr_tag_type_opts),
                    default = 1,
                    label = T('Tag Type'),
                    represent = lambda opt: opt and pr_tag_type_opts[opt]))

#
# Person-Item -----------------------------------------------------------------
#
resource = 'pitem'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                opt_pr_pitem_class,                 # Item class
                opt_pr_tag_type,                    # Tag type
                Field('pr_tag_label'),              # Tag Label
                Field('description'),               # Short Description
                Field('details','text'),            # Detailed Description
                Field('comment'),                   # a comment (optional)
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].opt_pr_pitem_class.label = T('Item Type')
db[table].opt_pr_tag_type.label = T('Tag Type')

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
                Field('pitem_id', db.pr_pitem,
                requires = IS_NULL_OR(IS_IN_DB(db, 'pr_pitem.id', '%(pr_tag_label)s: %(description)s')),
                represent = lambda id: (id and [db(db.pr_pitem.id==id).select()[0].id] or ["None"])[0],
                comment = DIV(A(T('Add Item'), _class='popup', _href=URL(r=request, c='pr', f='pitem', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Item|New Personal Presence, Body or Item."))),
                ondelete = 'RESTRICT'
                ))

#
# Reusable field set for PersonItem tables
# includes:
#   pitem               Person Item ID      (should be invisible in forms)
#   opt_pr_tag_type     Tag Type
#   pr_tag_label        Tag Label
#
pitem_field_set = SQLTable(None, 'pitem_id',
                    Field('pitem_id', db.pr_pitem,
                    requires = IS_NULL_OR(IS_IN_DB(db, 'pr_pitem.id', '%(pr_tag_label)s: %(description)s')),
                    represent = lambda id: (id and [db(db.pr_pitem.id==id).select()[0].id] or ["None"])[0],
                    comment = DIV(A(T('Add Item'), _class='popup', _href=URL(r=request, c='pr', f='pitem', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Item|New Personal Presence, Body or Item."))),
                    ondelete = 'RESTRICT'),
                    opt_pr_tag_type,
                    Field('pr_tag_label', label = T('Tag Label')))

#
# Images ----------------------------------------------------------------------
#
resource = 'image'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                pitem_id,
                Field('title'),
                Field('image', 'upload', autodelete=True),
                Field('description'),
                Field('comment'),
                migrate=migrate)

db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

#
# PItem to PEntity ------------------------------------------------------------
#
resource = 'pitem_to_pentity'
table = module + '_' + resource
db.define_table(table, timestamp,
                pentity_id,
                pitem_id,
                migrate=migrate)

#
# Presence --------------------------------------------------------------------
#

resource = 'presence'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                pitem_id,                           # Personal Item Reference
                location_id,                        # Location
                Field('time_start', 'datetime'),    # Start time
                Field('time_end', 'datetime'),      # End time
                Field('description'),               # Short Description
#                Field('details','text'),            # Detailed Description
                Field('comment'),                   # a comment (optional)
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

#
# Case ------------------------------------------------------------------------
#
resource = 'case'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('description'),               # Short Description
                Field('details','text'),            # Detailed Description
                Field('comment'),                   # a comment (optional)
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

# Reusable field for other tables to reference
pcase_id = SQLTable(None, 'pcase_id',
                Field('pcase_id', db.pr_case,
                requires = IS_NULL_OR(IS_IN_DB(db, 'pr_case.id', '%(description)s')),
                represent = lambda id: (id and [db(db.pr_case.id==id).select()[0].description] or ["None"])[0],
                comment = DIV(A(T('Add Case'), _class='popup', _href=URL(r=request, c='pr', f='case', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Case|Add new case."))),
                ondelete = 'RESTRICT'
                ))

#
# Findings --------------------------------------------------------------------
#
resource = 'finding'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                pitem_id,                       # about which item?
#                opt_pr_findings_type,           # Finding type
                Field('description'),           # Descriptive title
                Field('module'),                # Access module
                Field('resource'),              # Access resource
                Field('resource_id'),           # Access ID
                migrate=migrate)

db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].module.requires = IS_NULL_OR(IS_IN_DB(db, 's3_module.name', '%(name_nice)s'))
db[table].module.represent = lambda name: (name and [db(db.s3_module.name==name).select()[0].name_nice] or ["None"])[0]

#
# Callback functions ----------------------------------------------------------
#

#
# pitem_ondelete
#
def shn_pitem_ondelete(record):
    if record.pitem_id:
        del db.pr_pitem[record.pitem_id]
    else:
        #ignore
        pass
    return

#
# pitem_onvalidation
#

def shn_pitem_onvalidation(form, resource=None, item_class=1):
    if form:
        if len(request.args) == 0 or request.args[0] == 'create':
            # this is a create action either directly or from list view
            if item_class in pr_pitem_class_opts.keys():
                pitem_id = db['pr_pitem'].insert(
                    opt_pr_pitem_class=item_class,
                    opt_pr_tag_type=form.vars.opt_pr_tag_type,
                    pr_tag_label=form.vars.pr_tag_label )
                if pitem_id:
                    form.vars.pitem_id = pitem_id
        elif len(request.args) > 0:
            if request.args[0] == 'update' and form.vars.delete_this_record:
                # this is a delete action from update
                if len(request.args) > 1:
                    my_id = request.args[1]
                    if resource:
                        shn_pitem_ondelete(db[resource][my_id])
            elif request.args[0] == 'update':
                if len(request.args) > 1:
                    my_id = request.args[1]
                    if resource:
                        db(db.pr_pitem.id==db[resource][my_id].pitem_id).update(
                            opt_pr_tag_type=form.vars.opt_pr_tag_type,
                            pr_tag_label=form.vars.pr_tag_label)
    return

