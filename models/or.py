module='or'

# Menu Options
table='%s_menu_option' % module
db.define_table(table,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('access',db.t2_group),  # Hide menu options if users don't have the required access level
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db['%s' % table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name' % table)]
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
        name="Add Organization",
	function="organisation/create",
	priority=1,
	description="Add an Organisation's details to Sahana",
	enabled='True'
	)
	db['%s' % table].insert(
        name="List Organisations",
	function="organisation",
	priority=2,
	description="View a list of registered organizations. Their details can be viewed / edited by clicking on the appropriate links",
	enabled='True'
	)
	db['%s' % table].insert(
        name="Add Office",
	function="office/create",
	priority=3,
	description="Add an Office's details to Sahana",
	enabled='True'
	)
	db['%s' % table].insert(
        name="List Offices",
	function="office",
	priority=4,
	description="View a list of registered offices. Their details can be viewed / edited by clicking on the appropriate links",
	enabled='True'
	)
	db['%s' % table].insert(
        name="Add Contact",
	function="contact/create",
	priority=5,
	description="Add a Contact's details to Sahana",
	enabled='True'
	)
	db['%s' % table].insert(
        name="List Contacts",
	function="contact",
	priority=6,
	description="View a list of registered contacts. Their details can be viewed / edited by clicking on the appropriate links",
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

# Organisations
resource='organisation'
table=module+'_'+resource
db.define_table(table,
                #SQLField('privacy','integer',default=0),
                #SQLField('archived','boolean',default=False),
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('acronym'),
                SQLField('type'),
                SQLField('registration'),	# Registration Number
                SQLField('website'),
                SQLField('national_staff','integer'),
                SQLField('international_staff','integer'),
                SQLField('number_of_vehicles','integer'),
                SQLField('vehicle_types'),
                SQLField('equipment'))
exec("s3.crud_fields.%s=['name','acronym','type','registration','website','national_staff','international_staff','number_of_vehicles','vehicle_types','equipment']" % table)
db['%s' % table].exposes=s3.crud_fields['%s' % table]
# Moved to Controller - allows us to redefine for different scenarios (& also better MVC separation)
#db['%s' % table].displays=s3.crud_fields['%s' % table]
# NB Beware of lambdas & %s substitution as they get evaluated when called, not when defined! 
#db['%s' % table].represent=lambda table:shn_list_item(table,resource='organisation',action='display')
db['%s' % table].name.requires=IS_NOT_EMPTY()
db['%s' % table].name.comment=SPAN("*",_class="req")
db['%s' % table].type.requires=IS_NULL_OR(IS_IN_SET(['Government','International Governmental Organization','International NGO','Misc','National Institution','National NGO','United Nations']))
db['%s' % table].website.requires=IS_NULL_OR(IS_URL())
db['%s' % table].national_staff.requires=IS_NULL_OR(IS_INT_IN_RANGE(0,99999))
db['%s' % table].international_staff.requires=IS_NULL_OR(IS_INT_IN_RANGE(0,9999))
db['%s' % table].number_of_vehicles.requires=IS_NULL_OR(IS_INT_IN_RANGE(0,9999))
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
exec('s3.crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % table)

# Offices
resource='office'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('type'),
                SQLField('address','text'),
                SQLField('postcode'),
                SQLField('phone1'),
                SQLField('phone2'),
                SQLField('email'),
                SQLField('fax'),
                SQLField('location',length=64))
exec("s3.crud_fields.%s=['name','type','address','postcode','phone1','phone2','email','fax','location']" % table)
db['%s' % table].exposes=s3.crud_fields['%s' % table]
# Moved to Controller - allows us to redefine for different scenarios (& also better MVC separation)
#db['%s' % table].displays=s3.crud_fields['%s' % table]
# NB Beware of lambdas & %s substitution as they get evaluated when called, not when defined! 
#db['%s' % table].represent=lambda table:shn_list_item(table,resource='office',action='display')
db['%s' % table].name.requires=IS_NOT_EMPTY()
db['%s' % table].name.comment=SPAN("*",_class="req")
db['%s' % table].type.requires=IS_NULL_OR(IS_IN_SET(['Headquarters','Regional','Country','Satellite Office']))
db['%s' % table].location.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature.uuid','gis_feature.name'))
db['%s' % table].location.display=lambda uuid: (uuid and [db(db.gis_feature.uuid==uuid).select()[0].name] or ["None"])[0]
db['%s' % table].location.comment=A(SPAN("[Help]"),_class="popupLink",_id="tooltip",_title=T("Location|The GIS Feature associated with this Shelter."))
title_create=T('Add Office')
title_display=T('Office Details')
title_list=T('List Offices')
title_update=T('Edit Office')
subtitle_create=T('Add New Office')
subtitle_list=T('Offices')
label_list_button=T('List Offices')
label_create_button=T('Add Office')
msg_record_created=T('Office added')
msg_record_modified=T('Office updated')
msg_record_deleted=T('Office deleted')
msg_list_empty=T('No Offices currently registered')
exec('s3.crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % table)

# Offices to Organisations
#resource='organisation_offices'
resource='office_to_organisation'
table=module+'_'+resource
db.define_table(table,
                SQLField('office_id',db.or_office),
                SQLField('organisation_id',db.or_organisation))
db['%s' % table].office_id.requires=IS_IN_DB(db,'or_office.id','or_office.name')
db['%s' % table].office_id.label='Office'
db['%s' % table].organisation_id.requires=IS_IN_DB(db,'or_organisation.id','or_organisation.name')
db['%s' % table].organisation_id.label='Organisation'

# Contacts
resource='contact'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('person_id',db.pr_person),
                SQLField('title'))
exec("s3.crud_fields.%s=['person','title']" % table)
db['%s' % table].exposes=s3.crud_fields['%s' % table]
# Moved to Controller - allows us to redefine for different scenarios (& also better MVC separation)
#db['%s' % table].displays=s3.crud_fields['%s' % table]
# NB Beware of lambdas & %s substitution as they get evaluated when called, not when defined! 
#db['%s' % table].represent=lambda table:shn_list_item(table,resource='contact',action='display')
db['%s' % table].person_id.requires=IS_IN_DB(db,'pr_person.id','pr_person.name')
title_create=T('Add Contact')
title_display=T('Contact Details')
title_list=T('List Contacts')
title_update=T('Edit Contact')
subtitle_create=T('Add New Contact')
subtitle_list=T('Contacts')
label_list_button=T('List Contacts')
label_create_button=T('Add Contact')
msg_record_created=T('Contact added')
msg_record_modified=T('Contact updated')
msg_record_deleted=T('Contact deleted')
msg_list_empty=T('No Contacts currently registered')
exec('s3.crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % table)

# Contacts to Offices
#resource='contact_office'
resource='contact_to_office'
table=module+'_'+resource
db.define_table(table,
                SQLField('contact_id',db.or_contact),
                SQLField('office_id',db.or_office))
#db['%s' % table].contact_id.requires=IS_IN_DB(db,'or_contact.id','pr_person.name')
db['%s' % table].contact_id.requires=IS_IN_DB(db,'or_contact.id','or_contact.person_id')
db['%s' % table].contact_id.label='Contact'
db['%s' % table].office_id.requires=IS_IN_DB(db,'or_office.id','or_office.name')
db['%s' % table].office_id.label='Office'

# Contacts to Organisations
# Do we want to allow contacts which are affiliated to an organisation but not to an office?
#resource='contact_to_organisation'
#table=module+'_'+resource
#db.define_table(table,
#                SQLField('contact_id',db.or_contact),
#                SQLField('organisation_id',db.or_organisation))
#db['%s' % table].contact_id.requires=IS_IN_DB(db,'or_office.id','or_office.name')
#db['%s' % table].organisation_id.requires=IS_IN_DB(db,'or_organisation.id','or_organisation.name')

