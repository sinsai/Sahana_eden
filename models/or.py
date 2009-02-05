module='or'

# Menu Options
table='%s_menu_option' % module
db.define_table(table,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('access',db.auth_group),  # Hide menu options if users don't have the required access level
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db[table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name' % table)]
db[table].function.requires=IS_NOT_EMPTY()
db[table].access.requires=IS_NULL_OR(IS_IN_DB(db,'auth_group.id','auth_group.role'))
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
        name="Add Organisation",
	function="organisation/create",
	priority=1,
	description="Add an Organisation's details to Sahana",
	enabled='True'
	)
	db[table].insert(
        name="List Organisations",
	function="organisation",
	priority=2,
	description="View a list of registered organisations. Their details can be viewed / edited by clicking on the appropriate links",
	enabled='True'
	)
	db[table].insert(
        name="Search Organisations",
	function="organisation/search",
	priority=3,
	description="Search the list of registered organisations. Their details can be viewed / edited by clicking on the appropriate links",
	enabled='True'
	)
	db[table].insert(
        name="Add Office",
	function="office/create",
	priority=4,
	description="Add an Office's details to Sahana",
	enabled='True'
	)
	db[table].insert(
        name="List Offices",
	function="office",
	priority=5,
	description="View a list of registered offices. Their details can be viewed / edited by clicking on the appropriate links",
	enabled='True'
	)
	db[table].insert(
        name="Search Offices",
	function="office/search",
	priority=6,
	description="Search the list of registered offices. Their details can be viewed / edited by clicking on the appropriate links",
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

# Organisations
resource='organisation'
table=module+'_'+resource
db.define_table(table,timestamp,uuidstamp,
                #SQLField('privacy','integer',default=0),
                #SQLField('archived','boolean',default=False),
                SQLField('name'),
                SQLField('acronym',length=8),
                SQLField('type'),
                admin_id,
                SQLField('registration'),	# Registration Number
                SQLField('website'))
db[table].uuid.requires=IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name' % table)]
db[table].name.comment=SPAN("*",_class="req")
db[table].type.requires=IS_NULL_OR(IS_IN_SET(['Government','International Governmental Organization','International NGO','Misc','National Institution','National NGO','United Nations']))
db[table].admin.comment=DIV(A(T('Add Role'),_href=URL(r=request,c='default',f='role',args='create'),_target='_blank'),A(SPAN("[Help]"),_class="tooltip",_title=T("Admin|The Role whose members can edit all details within this Organisation.")))
db[table].website.requires=IS_NULL_OR(IS_URL())
title_create=T('Add Organisation')
title_display=T('Organisation Details')
title_list=T('List Organisations')
title_update=T('Edit Organisation')
title_search=T('Search Organisations')
subtitle_create=T('Add New Organisation')
subtitle_list=T('Organisations')
label_list_button=T('List Organisations')
label_create_button=T('Add Organisation')
msg_record_created=T('Organisation added')
msg_record_modified=T('Organisation updated')
msg_record_deleted=T('Organisation deleted')
msg_list_empty=T('No Organisations currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Offices
resource='office'
table=module+'_'+resource
db.define_table(table,timestamp,uuidstamp,
                SQLField('name'),
                SQLField('type'),
                admin_id,
                location_id,
                SQLField('address','text'),
                SQLField('postcode'),
                SQLField('phone1'),
                SQLField('phone2'),
                SQLField('email'),
                SQLField('fax'),
                SQLField('national_staff','integer'),
                SQLField('international_staff','integer'),
                SQLField('number_of_vehicles','integer'),
                SQLField('vehicle_types'),
                SQLField('equipment'))
db[table].uuid.requires=IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].admin.comment=DIV(A(T('Add Role'),_href=URL(r=request,c='default',f='role',args='create'),_target='_blank'),A(SPAN("[Help]"),_class="tooltip",_title=T("Admin|The Role whose members can edit all details within this Office.")))
db[table].name.requires=IS_NOT_EMPTY()   # Office names don't have to be unique
db[table].name.comment=SPAN("*",_class="req")
db[table].type.requires=IS_NULL_OR(IS_IN_SET(['Headquarters','Regional','Country','Satellite Office']))
db[table].location.display=lambda id: (id and [db(db.gis_location.id==id).select()[0].name] or ["None"])[0]
db[table].location.comment=DIV(A(s3.crud_strings.gis_location.label_create_button,_href=URL(r=request,c='gis',f='location',args='create'),_target='_blank'),A(SPAN("[Help]"),_class="tooltip",_title=T("Location|The Location of this Office, which can be general (for Reporting) or precise (for displaying on a Map).")))
db[table].national_staff.requires=IS_NULL_OR(IS_INT_IN_RANGE(0,99999))
db[table].international_staff.requires=IS_NULL_OR(IS_INT_IN_RANGE(0,9999))
db[table].number_of_vehicles.requires=IS_NULL_OR(IS_INT_IN_RANGE(0,9999))
title_create=T('Add Office')
title_display=T('Office Details')
title_list=T('List Offices')
title_update=T('Edit Office')
title_search=T('Search Offices')
subtitle_create=T('Add New Office')
subtitle_list=T('Offices')
label_list_button=T('List Offices')
label_create_button=T('Add Office')
msg_record_created=T('Office added')
msg_record_modified=T('Office updated')
msg_record_deleted=T('Office deleted')
msg_list_empty=T('No Offices currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Contacts
# Many-to-Many Persons to Offices with also the Title & Manager that the person has in this context
# ToDo: Build an Organigram out of this data?
resource='contact'
table=module+'_'+resource
db.define_table(table,timestamp,
                person_id,
                SQLField('office_id',db.or_office),
                SQLField('title'),
                SQLField('manager_id',db.pr_person))
db[table].person_id.label='Contact'
db[table].office_id.requires=IS_IN_DB(db,'or_office.id','or_office.name')
db[table].office_id.label='Office'
db[table].title.comment=A(SPAN("[Help]"),_class="popupLink",_id="tooltip",_title=T("Title|The Role this person plays within this Office."))
db[table].manager_id.requires=IS_NULL_OR(IS_IN_DB(db,'pr_person.id','pr_person.name'))
db[table].manager_id.label='Manager'
db[table].manager_id.comment=A(SPAN("[Help]"),_class="popupLink",_id="tooltip",_title=T("Manager|The person's manager within this Office."))
title_create=T('Add Contact')
title_display=T('Contact Details')
title_list=T('List Contacts')
title_update=T('Edit Contact')
title_search=T('Search Contacts')
subtitle_create=T('Add New Contact')
subtitle_list=T('Contacts')
label_list_button=T('List Contacts')
label_create_button=T('Add Contact')
msg_record_created=T('Contact added')
msg_record_modified=T('Contact updated')
msg_record_deleted=T('Contact deleted')
msg_list_empty=T('No Contacts currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Offices to Organisations
#resource='organisation_offices'
resource='office_to_organisation'
table=module+'_'+resource
db.define_table(table,timestamp,
                SQLField('office_id',db.or_office),
                SQLField('organisation_id',db.or_organisation))
db[table].office_id.requires=IS_IN_DB(db,'or_office.id','or_office.name')
db[table].office_id.label='Office'
db[table].organisation_id.requires=IS_IN_DB(db,'or_organisation.id','or_organisation.name')
db[table].organisation_id.label='Organisation'

# Contacts to Organisations
# Do we want to allow contacts which are affiliated to an organisation but not to an office?
# default can be HQ office
#resource='contact_to_organisation'
#table=module+'_'+resource
#db.define_table(table,timestamp,
#                SQLField('contact_id',db.or_contact),
#                SQLField('organisation_id',db.or_organisation))
#db[table].contact_id.requires=IS_IN_DB(db,'or_office.id','or_office.name')
#db[table].organisation_id.requires=IS_IN_DB(db,'or_organisation.id','or_organisation.name')

