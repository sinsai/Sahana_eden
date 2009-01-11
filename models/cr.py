module='cr'

# Menu Options
table='%s_menu_option' % module
db.define_table(table,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('access',db.t2_group),  # Hide menu options if users don't have the required access level
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db['%s' % table].name.requires=IS_NOT_IN_DB(db,'%s.name' % table)
db['%s' % table].function.requires=IS_NOT_EMPTY()
db['%s' % table].access.requires=IS_NULL_OR(IS_IN_DB(db,'t2_group.id','t2_group.name'))
db['%s' % table].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.priority' % table)]
if not len(db().select(db['%s' % table].ALL)):
	db['%s' % table].insert(
        name="Home",
	function="index",
	priority=0,
	description="Home",
	enabled='True'
	)
	db['%s' % table].insert(
        name="Add Shelter",
	function="shelter/create",
	priority=1,
	description="Add a shelter to the database",
	enabled='True'
	)
	db['%s' % table].insert(
        name="List Shelters",
	function="shelter",
	priority=2,
	description="List information of all shelters",
	enabled='True'
	)

# Settings
resource='setting'
table=module+'_'+resource
db.define_table(table,
                SQLField('audit_read','boolean'),
                SQLField('audit_write','boolean'))
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db['%s' % table].ALL)): 
   db['%s' % table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read=False,
        audit_write=False
    )

# Shelters
resource='shelter'
table=module+'_'+resource
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
exec("s3.crud_fields.%s=['name','description','address','capacity','dwellings','area','persons_per_dwelling','contact','location']" % table)
db['%s' % table].exposes=s3.crud_fields['%s' % table]
# Moved to Controller - allows us to redefine for different scenarios (& also better MVC separation)
#db['%s' % table].displays=s3.crud_fields['%s' % table]
# NB Beware of lambdas & %s substitution as they get evaluated when called, not when defined! 
#db['%s' % table].represent=lambda table:shn_list_item(table,resource='shelter',action='display')
db['%s' % table].name.requires=IS_NOT_EMPTY()
db['%s' % table].name.label=T("Shelter Name")
db['%s' % table].name.comment=SPAN("*",_class="req")
db['%s' % table].capacity.requires=IS_NULL_OR(IS_INT_IN_RANGE(0,999999))
db['%s' % table].dwellings.requires=IS_NULL_OR(IS_INT_IN_RANGE(0,99999))
db['%s' % table].persons_per_dwelling.requires=IS_NULL_OR(IS_INT_IN_RANGE(0,999))
db['%s' % table].contact.requires=IS_NULL_OR(IS_IN_DB(db,'pr_person.uuid','pr_person.name'))
db['%s' % table].contact.display=lambda uuid: (uuid and [db(db.pr_person.uuid==uuid).select()[0].name] or ["None"])[0]
db['%s' % table].contact.label=T("Contact Person")
db['%s' % table].location.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature.uuid','gis_feature.name'))
db['%s' % table].location.display=lambda uuid: (uuid and [db(db.gis_feature.uuid==uuid).select()[0].name] or ["None"])[0]
db['%s' % table].location.comment=A(SPAN("[Help]"),_class="popupLink",_id="tooltip",_title=T("Location|The GIS Feature associated with this Shelter."))
title_create=T('Add Shelter')
title_display=T('Shelter Details')
title_list=T('List Shelters')
title_update=T('Edit Shelter')
subtitle_create=T('Add New Shelter')
subtitle_list=T('Shelters')
label_list_button=T('List Shelters')
label_create_button=T('Add Shelter')
msg_record_created=T('Shelter added')
msg_record_modified=T('Shelter updated')
msg_record_deleted=T('Shelter deleted')
msg_list_empty=T('No Shelters currently registered')
exec('s3.crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % table)
