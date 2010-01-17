# -*- coding: utf-8 -*-

module = 'or'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)

# Organizations
or_organisation_type_opts = {
    1:T('Government'),
    2:T('International Governmental Organization'),
    3:T('International NGO'),
    4:T('Misc'),
    5:T('National Institution'),
    6:T('National NGO'),
    7:T('United Nations')
    }
resource = 'organisation'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                #Field('privacy', 'integer', default=0),
                #Field('archived', 'boolean', default=False),
                Field('name', length=128, notnull=True, unique=True),
                Field('acronym', length=8),
                Field('type', 'integer'),
                admin_id,
                #Field('registration', label=T('Registration')),	# Registration Number
                Field('country', 'integer'),
                Field('website'),
                source_id,
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].acronym.label = T('Acronym')
db[table].type.requires = IS_NULL_OR(IS_IN_SET(or_organisation_type_opts))
db[table].type.represent = lambda opt: opt and or_organisation_type_opts[opt]
db[table].type.label = T('Type')
db[table].country.requires=IS_IN_SET(shn_list_of_nations)
db[table].country.represent = lambda opt: opt and shn_list_of_nations[opt]
db[table].country.label = T('Home Country')
db[table].website.requires = IS_NULL_OR(IS_URL())
db[table].website.label = T('Website')
ADD_ORGANISATION = T('Add Organization')
title_create = T('Add Organization')
title_display = T('Organization Details')
title_list = T('List Organizations')
title_update = T('Edit Organization')
title_search = T('Search Organizations')
subtitle_create = T('Add New Organization')
subtitle_list = T('Organizations')
label_list_button = T('List Organizations')
label_create_button = ADD_ORGANISATION
msg_record_created = T('Organization added')
msg_record_modified = T('Organization updated')
msg_record_deleted = T('Organization deleted')
msg_list_empty = T('No Organizations currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
# Reusable field for other tables to reference
organisation_id = SQLTable(None, 'organisation_id',
            Field('organisation_id', db.or_organisation,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'or_organisation.id', '%(name)s')),
                represent = lambda id: (id and [db(db.or_organisation.id==id).select()[0].name] or ["None"])[0],
                label = T('Organization'),
                comment = DIV(A(ADD_ORGANISATION, _class='thickbox', _href=URL(r=request, c='or', f='organisation', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_ORGANISATION), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Organization|The Organization this record is associated with."))),
                ondelete = 'RESTRICT'
                ))

# Offices
or_office_type_opts = {
    1:T('Headquarters'),
    2:T('Regional'),
    3:T('Country'),
    4:T('Satellite Office')
    }
resource = 'office'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', notnull=True),
                organisation_id,
                Field('type', 'integer'),
                admin_id,
                location_id,
                Field('parent', 'reference or_office'),   # This form of hierarchy may not work on all Databases
                Field('address', 'text'),
                Field('postcode'),
                Field('phone1'),
                Field('phone2'),
                Field('email'),
                Field('fax'),
                Field('national_staff', 'integer'),
                Field('international_staff', 'integer'),
                Field('number_of_vehicles', 'integer'),
                Field('vehicle_types'),
                Field('equipment'),
                source_id,
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()   # Office names don't have to be unique
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].parent.requires = IS_NULL_OR(IS_ONE_OF(db, 'or_office.id', '%(name)s'))
db[table].parent.represent = lambda id: (id and [db(db.or_office.id==id).select()[0].name] or ["None"])[0]
db[table].type.requires = IS_NULL_OR(IS_IN_SET(or_office_type_opts))
db[table].type.represent = lambda opt: opt and or_office_type_opts[opt]
db[table].type.label = T('Type')
db[table].parent.label = T('Parent')
db[table].address.label = T('Address')
db[table].postcode.label = T('Postcode')
db[table].phone1.label = T('Phone 1')
db[table].phone2.label = T('Phone 2')
db[table].email.label = T('Email')
db[table].fax.label = T('FAX')
db[table].national_staff.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
db[table].national_staff.label = T('National Staff')
db[table].international_staff.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
db[table].international_staff.label = T('International Staff')
db[table].number_of_vehicles.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
db[table].number_of_vehicles.label = T('Number of Vehicles')
db[table].vehicle_types.label = T('Vehicle Types')
db[table].equipment.label = T('Equipment')
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

# Offices as component of Orgs
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(or_organisation='organisation_id'),
    deletable=True,
    editable=True,
    list_fields = ['id', 'name', 'phone1', 'email'])

# Contacts
# Many-to-Many Persons to Offices with also the Title & Manager that the person has in this context
# ToDo: Build an Organigram out of this data?
resource = 'contact'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                person_id,
                Field('office_id', db.or_office),
                Field('title'),
                Field('manager_id', db.pr_person),
                source_id,
                migrate=migrate)
db[table].person_id.label = T('Contact')
db[table].office_id.requires = IS_NULL_OR(IS_ONE_OF(db, 'or_office.id', '%(name)s'))
db[table].office_id.label = T('Office')
db[table].title.label = T('Title')
db[table].title.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Title|The Role this person plays within this Office."))
db[table].manager_id.requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_person.id', shn_pr_person_represent))
db[table].manager_id.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
db[table].manager_id.label = T('Manager')
db[table].manager_id.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Manager|The person's manager within this Office."))
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

# Offices to Organizations
#resource='organisation_offices'
#resource = 'office_to_organisation'
#table = module + '_' + resource
#db.define_table(table, timestamp, deletion_status,
#                Field('office_id', db.or_office),
#                Field('organisation_id', db.or_organisation),
#                migrate=migrate)
#db[table].office_id.requires = IS_ONE_OF(db, 'or_office.id', '%(name)s')
#db[table].office_id.label = T('Office')
#db[table].organisation_id.requires = IS_ONE_OF(db, 'or_organisation.id', '%(name)s')
#db[table].organisation_id.label = T('Organization')

# Contacts to Organizations
# Do we want to allow contacts which are affiliated to an organisation but not to an office?
# default can be HQ office
#resource='contact_to_organisation'
#table=module+'_'+resource
#db.define_table(table,timestamp,
#                Field('contact_id',db.or_contact),
#                Field('organisation_id',db.or_organisation))
#db[table].contact_id.requires=IS_ONE_OF(db,'or_office.id','%(name)s')
#db[table].organisation_id.requires=IS_ONE_OF(db,'or_organisation.id','%(name)s')

