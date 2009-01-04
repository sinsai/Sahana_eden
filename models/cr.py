module='cr'

# Menu Options
db.define_table('%s_menu_option' % module,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db['%s_menu_option' % module].name.requires=IS_NOT_IN_DB(db,'%s_menu_option.name' % module)
db['%s_menu_option' % module].name.requires=IS_NOT_EMPTY()
db['%s_menu_option' % module].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s_menu_option.priority' % module)]


# Shelters
resource='shelter'
table=module+'_'+resource
single=resource.capitalize()
# NB May need manual fixing!
plural=single+'s'
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('address','text'),
                SQLField('capacity','integer'),
                SQLField('dwellings','integer'),
                SQLField('persons_per_dwelling','integer'),
                SQLField('area'),
                SQLField('contact',length=64),
                SQLField('location',length=64))
db['%s' % table].exposes=['name','description','address','capacity','dwellings','area','persons_per_dwelling','contact','location']
db['%s' % table].displays=['name','description','address','capacity','dwellings','area','persons_per_dwelling','contact','location']
# NB Beware of lambdas & %s substitution as they get evaluated when called, not when defined! 
db['%s' % table].represent=lambda table:shn_list_item(table,resource='shelter',action='display')
db['%s' % table].name.requires=IS_NOT_EMPTY()
db['%s' % table].name.label=T("Shelter Name")
db['%s' % table].name.comment=SPAN("*",_class="req")
db['%s' % table].capacity.requires=IS_NULL_OR(IS_INT_IN_RANGE(0,999999))
db['%s' % table].dwellings.requires=IS_NULL_OR(IS_INT_IN_RANGE(0,99999))
db['%s' % table].persons_per_dwelling.requires=IS_NULL_OR(IS_INT_IN_RANGE(0,999))
db['%s' % table].contact.requires=IS_NULL_OR(IS_IN_DB(db,'pr_person.uuid','pr_person.full_name'))
db['%s' % table].contact.display=lambda uuid: (uuid and [db(db.pr_person.uuid==uuid).select()[0].full_name] or ["None"])[0]
db['%s' % table].contact.label=T("Contact Person")
db['%s' % table].location.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature.uuid','gis_feature.name'))
db['%s' % table].location.display=lambda uuid: (uuid and [db(db.gis_feature.uuid==uuid).select()[0].name] or ["None"])[0]
db['%s' % table].location.comment=A(SPAN("[Help]"),_class="popupLink",_id="tooltip",_title=T("Location|The GIS Feature associated with this Shelter."))
#title_create=T('Kill %s',single)
title_create=T('Add %s',single)
title_display=T('%s Details' % single)
title_list=T('List %s' % plural)
title_update=T('Edit %s' % single)
subtitle_create=T('Add New %s' % single)
subtitle_list=T('%s' % plural)
label_list_button=T('List %s' % plural)
label_create_button=T('Add %s' % single)
msg_record_created=T('%s added' % single)
msg_record_modified=T('%s updated' % single)
msg_record_deleted=T('%s deleted' % single)
msg_list_empty=T('No %s currently registered' % plural)
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
