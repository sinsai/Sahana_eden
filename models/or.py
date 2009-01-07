module='or'

# Menu Options
db.define_table('%s_menu_option' % module,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db['%s_menu_option' % module].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s_menu_option.name' % module)]
db['%s_menu_option' % module].name.requires=IS_NOT_EMPTY()
db['%s_menu_option' % module].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s_menu_option.priority' % module)]
if not len(db().select(db['%s_menu_option' % module].ALL)):
	table='%s_menu_option' % module
	
	db['%s' % table].insert(
        name="Home",
	function="index",
	priority=0,
	description="Home",
	enabled='True'
	)
	db['%s' % table].insert(
        name="Add Organization",
	function="organisation/create",
	priority=1,
	description="Adds an Organisation's details to Sahana",
	enabled='True'
	)
	db['%s' % table].insert(
        name="List Organisations",
	function="organisation",
	priority=2,
	description="View a list of registered organizations. Their details can be viewed / edited by clicking on the appropriate links",
	enabled='True'
	)

# OR Organisation Types
# How do we deal with syncs? Don't want dupes, yet want to be able to add local.
# => Master refs must have same uuids?
table='or_organisation_type'
db.define_table(table,
				SQLField('name'),
				SQLField('description',length=256))
db['%s' % table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'or_organisation_type.name')]

# OR Organisations
resource='organisation'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('parent',length=64), # No need for 'db.or_organisation' here as this is only used for cascading deletions (if you delete the table it's referring it to it will delete all the corresponding records)
                SQLField('type', db.or_organisation_type),
                SQLField('registration'),	# Registration Number
                SQLField('manpower'),
                SQLField('equipment'),
                SQLField('privacy','integer',default=0),
                SQLField('archived','boolean',default=False),
                SQLField('address','text'),
                SQLField('contact',length=64),
                SQLField('location',length=64))
db['%s' % table].exposes=['name','parent','type','registration','manpower','equipment','address','contact','location']
db['%s' % table].displays=['name','parent','type','registration','manpower','equipment','address','contact','location']
# NB Beware of lambdas & %s substitution as they get evaluated when called, not when defined! 
db['%s' % table].represent=lambda table:shn_list_item(table,resource='organisation',action='display')
db['%s' % table].name.requires=IS_NOT_EMPTY()
db['%s' % table].name.comment=SPAN("*",_class="req")
db['%s' % table].type.requires=IS_NULL_OR(IS_IN_DB(db,'or_organisation_type.id','or_organisation_type.name'))
db['%s' % table].parent.requires=IS_NULL_OR(IS_IN_DB(db,'or_organisation.uuid','or_organisation.name'))
db['%s' % table].parent.display=lambda uuid: (uuid and [db(db.or_organisation.uuid==uuid).select()[0].name] or ["None"])[0]
db['%s' % table].contact.requires=IS_NULL_OR(IS_IN_DB(db,'pr_person.uuid','pr_person.full_name'))
db['%s' % table].contact.display=lambda uuid: (uuid and [db(db.pr_person.uuid==uuid).select()[0].full_name] or ["None"])[0]
db['%s' % table].contact.label=T("Contact Person")
db['%s' % table].location.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature.uuid','gis_feature.name'))
db['%s' % table].location.display=lambda uuid: (uuid and [db(db.gis_feature.uuid==uuid).select()[0].name] or ["None"])[0]
db['%s' % table].location.comment=A(SPAN("[Help]"),_class="popupLink",_id="tooltip",_title=T("Location|The GIS Feature associated with this Shelter."))
title_create=T('Add Organisation')
title_display=T('Organisation Details')
title_list=T('List Organisations')
title_update=T('Edit Organisation')
subtitle_create=T('Add New Organisation')
subtitle_list=T('Organisations')
label_list_button=T('List Organisations')
label_create_button=T('Add Organisation')
msg_record_created=T('Organisation added')
msg_record_modified=T('Organisation updated')
msg_record_deleted=T('Organisation deleted')
msg_list_empty=T('No Organisations currently registered')
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
