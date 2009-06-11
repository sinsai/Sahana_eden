module = 'or'

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

# Organisations
resource = 'organisation'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                #db.Field('privacy', 'integer', default=0),
                #db.Field('archived', 'boolean', default=False),
                db.Field('name', notnull=True, unique=True),
                db.Field('acronym', length=8),
                db.Field('type'),
                admin_id,
                db.Field('registration'),	# Registration Number
                db.Field('website'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.comment = SPAN("*", _class="req")
db[table].type.requires = IS_NULL_OR(IS_IN_SET(['Government', 'International Governmental Organization', 'International NGO', 'Misc', 'National Institution', 'National NGO', 'United Nations']))
db[table].website.requires = IS_NULL_OR(IS_URL())
title_create = T('Add Organisation')
title_display = T('Organisation Details')
title_list = T('List Organisations')
title_update = T('Edit Organisation')
title_search = T('Search Organisations')
subtitle_create = T('Add New Organisation')
subtitle_list = T('Organisations')
label_list_button = T('List Organisations')
label_create_button = T('Add Organisation')
msg_record_created = T('Organisation added')
msg_record_modified = T('Organisation updated')
msg_record_deleted = T('Organisation deleted')
msg_list_empty = T('No Organisations currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Offices
resource = 'office'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                db.Field('name', notnull=True),
                db.Field('organisation', db.or_organisation),
                db.Field('type'),
                admin_id,
                location_id,
                db.Field('parent', 'reference or_office'),   # This form of hierarchy may not work on all Databases
                db.Field('address', 'text'),
                db.Field('postcode'),
                db.Field('phone1'),
                db.Field('phone2'),
                db.Field('email'),
                db.Field('fax'),
                db.Field('national_staff', 'integer'),
                db.Field('international_staff', 'integer'),
                db.Field('number_of_vehicles', 'integer'),
                db.Field('vehicle_types'),
                db.Field('equipment'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()   # Office names don't have to be unique
db[table].name.comment = SPAN("*", _class="req")
db[table].organisation.requires = IS_IN_DB(db, 'or_organisation.id', 'or_organisation.name')
db[table].organisation.represent = lambda id: (id and [db(db.or_organisation.id==id).select()[0].name] or ["None"])[0]
db[table].organisation.comment = DIV(A(s3.crud_strings.or_organisation.label_create_button, _class='popup', _href=URL(r=request, c='or', f='organisation', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Organisation|The Organisation this Office belongs to.")))
db[table].parent.requires = IS_NULL_OR(IS_IN_DB(db, 'or_office.id', 'or_office.name'))
db[table].parent.represent = lambda id: (id and [db(db.or_office.id==id).select()[0].name] or ["None"])[0]
db[table].type.requires = IS_NULL_OR(IS_IN_SET(['Headquarters', 'Regional', 'Country', 'Satellite Office']))
db[table].national_staff.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
db[table].international_staff.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
db[table].number_of_vehicles.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
title_create = T('Add Office')
title_display = T('Office Details')
title_list = T('List Offices')
title_update = T('Edit Office')
title_search = T('Search Offices')
subtitle_create = T('Add New Office')
subtitle_list = T('Offices')
label_list_button = T('List Offices')
label_create_button = T('Add Office')
msg_record_created = T('Office added')
msg_record_modified = T('Office updated')
msg_record_deleted = T('Office deleted')
msg_list_empty = T('No Offices currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Contacts
# Many-to-Many Persons to Offices with also the Title & Manager that the person has in this context
# ToDo: Build an Organigram out of this data?
resource = 'contact'
table = module + '_' + resource
db.define_table(table, timestamp,
                person_id,
                db.Field('office_id', db.or_office),
                db.Field('title'),
                db.Field('manager_id', db.pr_person),
                migrate=migrate)
db[table].person_id.label = 'Contact'
db[table].office_id.requires = IS_IN_DB(db, 'or_office.id', 'or_office.name')
db[table].office_id.label = 'Office'
db[table].title.comment = A(SPAN("[Help]"), _class="popupLink", _id="tooltip", _title=T("Title|The Role this person plays within this Office."))
db[table].manager_id.requires = IS_NULL_OR(IS_IN_DB(db, 'pr_person.id', 'pr_person.name'))
db[table].manager_id.label = 'Manager'
db[table].manager_id.comment = A(SPAN("[Help]"), _class="popupLink", _id="tooltip", _title=T("Manager|The person's manager within this Office."))
title_create = T('Add Contact')
title_display = T('Contact Details')
title_list = T('List Contacts')
title_update = T('Edit Contact')
title_search = T('Search Contacts')
subtitle_create = T('Add New Contact')
subtitle_list = T('Contacts')
label_list_button = T('List Contacts')
label_create_button = T('Add Contact')
msg_record_created = T('Contact added')
msg_record_modified = T('Contact updated')
msg_record_deleted = T('Contact deleted')
msg_list_empty = T('No Contacts currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Offices to Organisations
#resource='organisation_offices'
resource = 'office_to_organisation'
table = module + '_' + resource
db.define_table(table, timestamp,
                db.Field('office_id', db.or_office),
                db.Field('organisation_id', db.or_organisation),
                migrate=migrate)
db[table].office_id.requires = IS_IN_DB(db, 'or_office.id', 'or_office.name')
db[table].office_id.label = 'Office'
db[table].organisation_id.requires = IS_IN_DB(db, 'or_organisation.id', 'or_organisation.name')
db[table].organisation_id.label = 'Organisation'

# Contacts to Organisations
# Do we want to allow contacts which are affiliated to an organisation but not to an office?
# default can be HQ office
#resource='contact_to_organisation'
#table=module+'_'+resource
#db.define_table(table,timestamp,
#                db.Field('contact_id',db.or_contact),
#                db.Field('organisation_id',db.or_organisation))
#db[table].contact_id.requires=IS_IN_DB(db,'or_office.id','or_office.name')
#db[table].organisation_id.requires=IS_IN_DB(db,'or_organisation.id','or_organisation.name')

