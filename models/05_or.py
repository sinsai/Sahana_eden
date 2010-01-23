# -*- coding: utf-8 -*-

module = 'or'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)

# Services
resource = 'service'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', length=128, notnull=True, unique=True),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
ADD_SERVICE = T('Add Service')
title_create = T('Add Service')
title_display = T('Service Details')
title_list = T('List Services')
title_update = T('Edit Service')
title_search = T('Search Services')
subtitle_create = T('Add New Service')
subtitle_list = T('Services')
label_list_button = T('List Services')
label_create_button = ADD_SERVICE
msg_record_created = T('Service added')
msg_record_modified = T('Service updated')
msg_record_deleted = T('Service deleted')
msg_list_empty = T('No Services currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
# Reusable field for other tables to reference
def service_represent(service_ids):
    if not service_ids:
        return "None"
    elif "|" in str(service_ids):
        services = [db(db.or_service.id==id).select()[0].name for id in service_ids.split('|') if id]
        return ", ".join(services)
    else:
        return db(db.or_service.id==service_ids).select()[0].name

service_id = SQLTable(None, 'service_id',
            Field('service_id',
                requires = IS_NULL_OR(IS_ONE_OF(db, 'or_service.id', '%(name)s', multiple=True)),
                represent = service_represent,
                label = T('Service'),
                comment = DIV(A(ADD_SERVICE, _class='thickbox', _href=URL(r=request, c='or', f='service', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_SERVICE), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Service|The Service(s) this organisation works in. Multiple values can be selected by holding down the 'Control' key"))),
                ondelete = 'RESTRICT'
                ))

# Sectors (to be renamed as Clusters)
resource = 'sector'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', length=128, notnull=True, unique=True),
                service_id,
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
ADD_SECTOR = T('Add Sector')
title_create = T('Add Sector')
title_display = T('Sector Details')
title_list = T('List Sectors')
title_update = T('Edit Sector')
title_search = T('Search Sectors')
subtitle_create = T('Add New Sector')
subtitle_list = T('Sectors')
label_list_button = T('List Sectors')
label_create_button = ADD_SECTOR
msg_record_created = T('Sector added')
msg_record_modified = T('Sector updated')
msg_record_deleted = T('Sector deleted')
msg_list_empty = T('No Sectors currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
# Reusable field for other tables to reference
def sector_represent(sector_ids):
    if not sector_ids:
        return "None"
    elif "|" in str(sector_ids):
        sectors = [db(db.or_sector.id==id).select()[0].name for id in sector_ids.split('|') if id]
        return ", ".join(sectors)
    else:
        return db(db.or_sector.id==sector_ids).select()[0].name

sector_id = SQLTable(None, 'sector_id',
            Field('sector_id',
                requires = IS_NULL_OR(IS_ONE_OF(db, 'or_sector.id', '%(name)s', multiple=True)),
                represent = sector_represent,
                label = T('Sector'),
                comment = DIV(A(ADD_SECTOR, _class='thickbox', _href=URL(r=request, c='or', f='sector', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_SECTOR), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Sector|The Sector(s) this organisation works in. Multiple values can be selected by holding down the 'Control' key"))),
                ondelete = 'RESTRICT'
                ))
                

# Organizations
or_organisation_type_opts = {
    1:T('Government'),
    2:T('Embassy'),
    3:T('International NGO'),
    4:T('Donor'),
    6:T('National NGO'),
    7:T('UN'),
    8:T('International Organization'),
    9:T('MINUSTAH'),
    10:T('Military'),
    11:T('Private')
    }
resource = 'organisation'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                #Field('privacy', 'integer', default=0),
                #Field('archived', 'boolean', default=False),
                Field('name', length=128, notnull=True, unique=True),
                Field('acronym', length=8),
                Field('type', 'integer'),
                sector_id,
                admin_id,
                #Field('registration', label=T('Registration')),	# Registration Number
                Field('country', 'integer'),
                Field('website'),
                Field('donation_phone'), 
                shn_comments_field,
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
db[table].donation_phone.label = T('Donation Phone #')
db[table].donation_phone.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Donation Phone #|Phone number to donate to this organization's relief efforts."))
db[table].country.requires = IS_NULL_OR(IS_IN_SET(shn_list_of_nations))
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

# Orgs as component of Clusters
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(or_sector='sector_id'),
    deletable=True,
    editable=True,
    list_fields = ['id', 'name', 'acronym', 'type', 'country'])

# Offices
or_office_type_opts = {
    1:T('Satellite Office'),
    2:T('Country'),
    3:T('Regional'),
    4:T('Headquarters')
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
                shn_comments_field,
                source_id,
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
#db[table].name.requires = IS_NOT_EMPTY()   # Office names don't have to be unique
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
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
db[table].email.requires = IS_NULL_OR(IS_EMAIL())
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
ADD_OFFICE = T('Add Office')
title_create = ADD_OFFICE
title_display = T('Office Details')
title_list = T('List Offices')
title_update = T('Edit Office')
title_search = T('Search Offices')
subtitle_create = T('Add New Office')
subtitle_list = T('Offices')
label_list_button = T('List Offices')
label_create_button = ADD_OFFICE
msg_record_created = T('Office added')
msg_record_modified = T('Office updated')
msg_record_deleted = T('Office deleted')
msg_list_empty = T('No Offices currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
# Reusable field for other tables to reference
office_id = SQLTable(None, 'office_id',
            Field('office_id', db.or_office,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'or_office.id', '%(name)s')),
                represent = lambda id: (id and [db(db.or_office.id==id).select()[0].name] or ["None"])[0],
                label = T('Office'),
                comment = DIV(A(ADD_OFFICE, _class='thickbox', _href=URL(r=request, c='or', f='office', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_OFFICE), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Office|The Office this record is associated with."))),
                ondelete = 'RESTRICT'
                ))

# JOINed resource (component)
s3xrc.model.add_component('gis', 'location',
    multiple = False,
    joinby =  dict(or_office='location_id'),
    deletable = False,
    editable = True,
    list_fields = ['id', 'lat', 'lon', 'marker_id'])

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
				organisation_id,
                office_id,
                Field('title'),
                Field('manager_id', db.pr_person),
				Field('focal_point', 'boolean'),
                source_id,
                migrate=migrate)
db[table].person_id.label = T('Contact')
db[table].title.label = T('Job Title')
db[table].title.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Title|The Role this person plays within this Office."))
db[table].manager_id.requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_person.id', shn_pr_person_represent))
db[table].manager_id.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
db[table].manager_id.label = T('Manager')
db[table].manager_id.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Manager|The person's manager within this Office."))
shn_pr_person_represent
#or_contact_focal_point_represent = {
#    0:T('-'),
#    1:T('Focal Point'),
#    }
def represent_focal_point(is_focal_point): 
    if is_focal_point: 
        return "Focal Point" 
    else: 
        return "-"
db[table].focal_point.represent = lambda focal_point: represent_focal_point(focal_point)
#opt: opt and or_office_type_opts[opt]
db[table].focal_point.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Focal Point|The contact person for this organization."))
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

# Contacts as component of Orgs
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(or_organisation='organisation_id'),
    deletable=True,
    editable=True,
    list_fields = ['id', 'person_id', 'office_id', 'title', 'manager_id', 'focal_point'])

# Projects
# The projects which each orgnaization is engaged in 
resource = 'project'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
				organisation_id,
				location_id,
				sector_id,
				Field('title'),
				Field('description'),
				Field('beneficiaries', 'integer'),
				Field('start_date', 'date'),
				Field('end_date', 'date'),
				Field('funded', 'boolean'),
                Field('budgeted_cost', 'double'),
                migrate=migrate)
db[table].budgeted_cost.requires = IS_NULL_OR(IS_FLOAT_IN_RANGE(0, 999999999))				
title_create = T('Add Project')
title_display = T('Project Details')
title_list = T('Projects Report')
title_update = T('Edit Project')
title_search = T('Search Projects')
subtitle_create = T('Add New Project')
subtitle_list = T('Projects')
label_list_button = T('List Projects')
label_create_button = T('Add Project')
msg_record_created = T('Project added')
msg_record_modified = T('Project updated')
msg_record_deleted = T('Project deleted')
msg_list_empty = T('No Projects currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)				

#"Organization Name", "Sector\Cluster Name" , "Sub Sector Name", "Country Name", "Admin 1 Name", "Admin 2 Name", "Admin 3 Name", "Admin 4 Name", "Place Name", "Project Title", "Project Objective", "Project Description", "Primary Beneficiary", "Number of Primary Beneficiaries", "Secondary Beneficiary (separated by , )", "Number of Secondary Beneficiaries", "Implementing Partners (separated by , )", "Project Type", "Project Status", "Project Theme", "CAP #", "Estimated Start Date (dd/mm/yyyy)", "Estimated End Date (dd/mm/yyyy)", "Funding Amount", "Funding Currency", "Funding Type", "Funding Status", "Funding Reported to FTS (Yes or No)", "Organization Funding Details For each organization funding the project, the details include: Organization Name,Amount Funded,Funding Currency;(separate the data by comma ,) (For multiple organizations separate each Organization's Dataset by a semi-colon ;) Example: "Org1,100000,US$ ; Org2,20000,Pound"" (end of line) 
				
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

