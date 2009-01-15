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
db[table].name.requires=IS_NOT_IN_DB(db,'%s.name' % table)
db[table].function.requires=IS_NOT_EMPTY()
db[table].access.requires=IS_NULL_OR(IS_IN_DB(db,'t2_group.id','t2_group.name'))
db[table].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.priority' % table)]
if not len(db().select(db[table].ALL)):
	db[table].insert(
        name="Home",
	function="index",
	priority=0,
	description="Home",
	enabled='True'
	)
	db[table].insert(
        name="Add Shelter",
	function="shelter/create",
	priority=1,
	description="Add a shelter to the database",
	enabled='True'
	)
	db[table].insert(
        name="List Shelters",
	function="shelter",
	priority=2,
	description="List information of all shelters",
	enabled='True'
	)
	db[table].insert(
        name="Search Shelters",
	function="shelter/search",
	priority=3,
	description="Search List of shelters",
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
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read=False,
        audit_write=False
    )

# Shelters
resource='shelter'
table=module+'_'+resource
db.define_table(table,timestamp,uuidstamp,
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('location',db.gis_location),
                SQLField('feature',db.gis_feature),
                SQLField('contact',db.pr_person),
                SQLField('address','text'),
                SQLField('capacity','integer'),
                SQLField('dwellings','integer'),
                SQLField('persons_per_dwelling','integer'),
                SQLField('area'))
exec("s3.crud_fields.%s=['name','description','address','capacity','dwellings','area','persons_per_dwelling','contact','location']" % table)
db[table].exposes=s3.crud_fields[table]
db[table].uuid.requires=IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires=IS_NOT_EMPTY()   # Shelters don't have to have unique names
db[table].name.label=T("Shelter Name")
db[table].name.comment=SPAN("*",_class="req")
db[table].location.requires=IS_NULL_OR(IS_IN_DB(db,'gis_location.id','gis_location.name'))
db[table].location.display=lambda id: (id and [db(db.gis_location.id==id).select()[0].name] or ["None"])[0]
db[table].location.comment=A(SPAN("[Help]"),_class="popupLink",_id="tooltip2",_title=T("Location|The General Location associated with this Office. For use in Reporting"))
db[table].feature.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature.id','gis_feature.name'))
db[table].feature.display=lambda id: (id and [db(db.gis_feature.id==id).select()[0].name] or ["None"])[0]
db[table].feature.comment=A(SPAN("[Help]"),_class="popupLink",_id="tooltip3",_title=T("Feature|The Exact Coordinates to use to display this Office on a Map."))
db[table].contact.requires=IS_NULL_OR(IS_IN_DB(db,'pr_person.id','pr_person.name'))
db[table].contact.display=lambda uuid: (uuid and [db(db.pr_person.id==id).select()[0].name] or ["None"])[0]
db[table].contact.label=T("Contact Person")
db[table].capacity.requires=IS_NULL_OR(IS_INT_IN_RANGE(0,999999))
db[table].dwellings.requires=IS_NULL_OR(IS_INT_IN_RANGE(0,99999))
db[table].persons_per_dwelling.requires=IS_NULL_OR(IS_INT_IN_RANGE(0,999))
title_create=T('Add Shelter')
title_display=T('Shelter Details')
title_list=T('List Shelters')
title_update=T('Edit Shelter')
title_search=T('Search Shelters')
subtitle_create=T('Add New Shelter')
subtitle_list=T('Shelters')
label_list_button=T('List Shelters')
label_create_button=T('Add Shelter')
msg_record_created=T('Shelter added')
msg_record_modified=T('Shelter updated')
msg_record_deleted=T('Shelter deleted')
msg_list_empty=T('No Shelters currently registered')
exec('s3.crud_strings.%s=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)' % table)
