# -*- coding: utf-8 -*-

"""
    OR Organisation Registry
"""

module = 'or'

# -----------------------------------------------------------------------------
# Settings
#
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)

# -----------------------------------------------------------------------------
# Services
resource = 'service'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', length=128, notnull=True, unique=True),
                migrate=migrate)

# Field settings
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")

# CRUD strings
ADD_SERVICE = T('Add Service')
LIST_SERVICES = T('List Services')

s3.crud_strings[table] = Storage(
    title_create = ADD_SERVICE,
    title_display = T('Service Details'),
    title_list = LIST_SERVICES,
    title_update = T('Edit Service'),
    title_search = T('Search Services'),
    subtitle_create = T('Add New Service'),
    subtitle_list = T('Services'),
    label_list_button = LIST_SERVICES,
    label_create_button = ADD_SERVICE,
    msg_record_created = T('Service added'),
    msg_record_modified = T('Service updated'),
    msg_record_deleted = T('Service deleted'),
    msg_list_empty = T('No Services currently registered'))

# Functions
def service_represent(service_ids):

    if not service_ids:
        return "None"
    elif "|" in str(service_ids):
        services = [db(db.or_service.id==id).select()[0].name for id in service_ids.split('|') if id]
        return ", ".join(services)
    else:
        return db(db.or_service.id==service_ids).select()[0].name

# Reusable field
service_id = SQLTable(None, 'service_id',
                      Field('service_id',
                            requires = IS_NULL_OR(IS_ONE_OF(db, 'or_service.id', '%(name)s', multiple=True)),
                            represent = service_represent,
                            label = T('Service'),
                            comment = DIV(A(ADD_SERVICE, _class='thickbox', _href=URL(r=request, c='or', f='service', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_SERVICE), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Service|The Service(s) this organisation works in. Multiple values can be selected by holding down the 'Control' key"))),
                            ondelete = 'RESTRICT'
                           ))

# -----------------------------------------------------------------------------
# Sectors (to be renamed as Clusters)
#
resource = 'sector'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', length=128, notnull=True, unique=True),
                service_id,
                migrate=migrate)

# Field settings
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")

# CRUD strings
ADD_SECTOR = T('Add Sector')
LIST_SECTORS = T('List Sectors')

s3.crud_strings[table] = Storage(
    title_create = ADD_SECTOR,
    title_display = T('Sector Details'),
    title_list = LIST_SECTORS,
    title_update = T('Edit Sector'),
    title_search = T('Search Sectors'),
    subtitle_create = T('Add New Sector'),
    subtitle_list = T('Sectors'),
    label_list_button = LIST_SECTORS,
    label_create_button = ADD_SECTOR,
    msg_record_created = T('Sector added'),
    msg_record_modified = T('Sector updated'),
    msg_record_deleted = T('Sector deleted'),
    msg_list_empty = T('No Sectors currently registered'))

# Functions
def sector_represent(sector_ids):
    if not sector_ids:
        return "None"
    elif "|" in str(sector_ids):
        sectors = [db(db.or_sector.id==id).select()[0].name for id in sector_ids.split('|') if id]
        return ", ".join(sectors)
    else:
        return db(db.or_sector.id==sector_ids).select()[0].name

# Reusable field
sector_id = SQLTable(None, 'sector_id',
                     Field('sector_id',
                           requires = IS_NULL_OR(IS_ONE_OF(db, 'or_sector.id', '%(name)s', multiple=True)),
                           represent = sector_represent,
                           label = T('Sector'),
                           comment = DIV(A(ADD_SECTOR, _class='thickbox', _href=URL(r=request, c='or', f='sector', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_SECTOR), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Sector|The Sector(s) this organisation works in. Multiple values can be selected by holding down the 'Control' key"))),
                           ondelete = 'RESTRICT'
                          ))

# -----------------------------------------------------------------------------
# Organizations
#
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
                #Field('registration', label=T('Registration')),    # Registration Number
                Field('country', 'integer'),
                Field('website'),
                Field('twitter'),
                Field('donation_phone'),
                shn_comments_field,
                source_id,
                migrate=migrate)

# Field settings
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")

db[table].acronym.label = T('Acronym')

db[table].type.requires = IS_NULL_OR(IS_IN_SET(or_organisation_type_opts))
db[table].type.represent = lambda opt: or_organisation_type_opts.get(opt, UNKNOWN_OPT)
db[table].type.label = T('Type')

db[table].donation_phone.label = T('Donation Phone #')
db[table].donation_phone.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Donation Phone #|Phone number to donate to this organization's relief efforts."))

db[table].country.requires = IS_NULL_OR(IS_IN_SET(shn_list_of_nations))
db[table].country.represent = lambda opt: shn_list_of_nations.get(opt, UNKNOWN_OPT)
db[table].country.label = T('Home Country')

db[table].website.requires = IS_NULL_OR(IS_URL())
db[table].website.label = T('Website')

db[table].twitter.label = T('Twitter')
db[table].twitter.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Twitter|Twitter ID or #hashtag"))

# CRUD strings
ADD_ORGANISATION = T('Add Organization')
LIST_ORGANIZATIONS = T('List Organizations')

s3.crud_strings[table] = Storage(
    title_create = ADD_ORGANISATION,
    title_display = T('Organization Details'),
    title_list = LIST_ORGANIZATIONS,
    title_update = T('Edit Organization'),
    title_search = T('Search Organizations'),
    subtitle_create = T('Add New Organization'),
    subtitle_list = T('Organizations'),
    label_list_button = LIST_ORGANIZATIONS,
    label_create_button = ADD_ORGANISATION,
    msg_record_created = T('Organization added'),
    msg_record_modified = T('Organization updated'),
    msg_record_deleted = T('Organization deleted'),
    msg_list_empty = T('No Organizations currently registered'))

# Reusable field
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

# -----------------------------------------------------------------------------
# Offices
#
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
                source_id,
                shn_comments_field,
                migrate=migrate)

# Field settings
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

#db[table].name.requires = IS_NOT_EMPTY()   # Office names don't have to be unique
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")

db[table].parent.label = T('Parent')
db[table].parent.requires = IS_NULL_OR(IS_ONE_OF(db, 'or_office.id', '%(name)s'))
db[table].parent.represent = lambda id: (id and [db(db.or_office.id==id).select()[0].name] or ["None"])[0]

db[table].type.requires = IS_NULL_OR(IS_IN_SET(or_office_type_opts))
db[table].type.represent = lambda opt: or_office_type_opts.get(opt, UNKNOWN_OPT)
db[table].type.label = T('Type')

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

# CRUD strings
ADD_OFFICE = T('Add Office')
LIST_OFFICES = T('List Offices')

s3.crud_strings[table] = Storage(
    title_create = ADD_OFFICE,
    title_display = T('Office Details'),
    title_list = LIST_OFFICES,
    title_update = T('Edit Office'),
    title_search = T('Search Offices'),
    subtitle_create = T('Add New Office'),
    subtitle_list = T('Offices'),
    label_list_button = LIST_OFFICES,
    label_create_button = ADD_OFFICE,
    msg_record_created = T('Office added'),
    msg_record_modified = T('Office updated'),
    msg_record_deleted = T('Office deleted'),
    msg_list_empty = T('No Offices currently registered'))

# Reusable field for other tables to reference
office_id = SQLTable(None, 'office_id',
            Field('office_id', db.or_office,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'or_office.id', '%(name)s')),
                represent = lambda id: (id and [db(db.or_office.id==id).select()[0].name] or ["None"])[0],
                label = T('Office'),
                comment = DIV(A(ADD_OFFICE, _class='thickbox', _href=URL(r=request, c='or', f='office', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_OFFICE), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Office|The Office this record is associated with."))),
                ondelete = 'RESTRICT'
                ))

# Locations as component of offices
s3xrc.model.add_component('gis', 'location',
    multiple = False,
    joinby = dict(or_office='location_id'),
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

# -----------------------------------------------------------------------------
# Contacts
# Many-to-Many Persons to Offices with also the Title & Manager that the person has in this context
# ToDo: Build an Organigram out of this data?
#
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
                shn_comments_field,
                migrate=migrate)

# Field settings
db[table].person_id.label = T('Contact')

db[table].title.label = T('Job Title')
db[table].title.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Title|The Role this person plays within this Office."))

db[table].manager_id.requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_person.id', shn_pr_person_represent))
db[table].manager_id.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
db[table].manager_id.label = T('Manager')
db[table].manager_id.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Manager|The person's manager within this Office."))

# Functions
def represent_focal_point(is_focal_point):
    if is_focal_point:
        return "Focal Point"
    else:
        return "-"

def shn_or_contact_represent(contact_id):
    person = db((db.or_contact.id==contact_id) &
                (db.pr_person.id==db.or_contact.person_id)).select(db.pr_person.ALL)
    if person:
        return vita.fullname(person[0])
    else:
        return None
 
db[table].focal_point.represent = lambda focal_point: represent_focal_point(focal_point)
db[table].focal_point.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Focal Point|The contact person for this organization."))

def shn_orgs_to_person(person_id):

    orgs = []
    if person_id:
        contacts = db((db.or_contact.person_id==person_id)&
                      (db.or_contact.deleted==False)).select(db.or_contact.organisation_id)
        if contacts:
            for c in contacts:
                orgs.append(c.organisation_id)
    return orgs

# CRUD strings
ADD_CONTACT = T('Add Contact')
LIST_CONTACTS = T('List Contacts')

s3.crud_strings[table] = Storage(
    title_create = ADD_CONTACT,
    title_display = T('Contact Details'),
    title_list = LIST_CONTACTS,
    title_update = T('Edit Contact'),
    title_search = T('Search Contacts'),
    subtitle_create = T('Add New Contact'),
    subtitle_list = T('Contacts'),
    label_list_button = LIST_CONTACTS,
    label_create_button = ADD_CONTACT,
    msg_record_created = T('Contact added'),
    msg_record_modified = T('Contact updated'),
    msg_record_deleted = T('Contact deleted'),
    msg_list_empty = T('No Contacts currently registered'))

# Contacts as component of Orgs
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(or_organisation='organisation_id'),
    deletable=True,
    editable=True,
    list_fields = ['id', 'person_id', 'office_id', 'title', 'manager_id', 'focal_point'])

# -----------------------------------------------------------------------------
# Projects:
#   the projects which each organization is engaged in
#
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

# Field settings
db[table].budgeted_cost.requires = IS_NULL_OR(IS_FLOAT_IN_RANGE(0, 999999999))

# CRUD strings
ADD_PROJECT = T('Add Project')

s3.crud_strings[table] = Storage(
    title_create = ADD_PROJECT,
    title_display = T('Project Details'),
    title_list = T('Projects Report'),
    title_update = T('Edit Project'),
    title_search = T('Search Projects'),
    subtitle_create = T('Add New Project'),
    subtitle_list = T('Projects'),
    label_list_button = T('List Projects'),
    label_create_button = ADD_PROJECT,
    msg_record_created = T('Project added'),
    msg_record_modified = T('Project updated'),
    msg_record_deleted = T('Project deleted'),
    msg_list_empty = T('No Projects currently registered'))

# -----------------------------------------------------------------------------
