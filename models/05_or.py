# -*- coding: utf-8 -*-

module = 'or'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)

# Sectors
resource = 'sector'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', length=128, notnull=True, unique=True),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
ADD_ORGANISATION = T('Add Sector')
title_create = T('Add Sector')
title_display = T('Sector Details')
title_list = T('List Sectors')
title_update = T('Edit Sector')
title_search = T('Search Sectors')
subtitle_create = T('Add New Sector')
subtitle_list = T('Sectors')
label_list_button = T('List Sectors')
label_create_button = ADD_ORGANISATION
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
        return [db(db.or_sector.id==sector_ids).select()[0].name]

sector_id = SQLTable(None, 'sector_id',
            Field('sector_id',
                requires = IS_NULL_OR(IS_ONE_OF(db, 'or_sector.id', '%(name)s', multiple=True)),
                represent = sector_represent,
                label = T('Sector'),
                comment = DIV(A(ADD_ORGANISATION, _class='thickbox', _href=URL(r=request, c='or', f='sector', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_ORGANISATION), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Sector|The Sector(s) this organisation works in. Multiple values can be selected by holding down the 'Control' key"))),
                ondelete = 'RESTRICT'
                ))
                
# Organisations
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
                sector_id,
                admin_id,
                Field('registration'),	# Registration Number
                Field('website'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].acronym.label = T('Acronym')
db[table].type.requires = IS_NULL_OR(IS_IN_SET(or_organisation_type_opts))
db[table].type.represent = lambda opt: opt and or_organisation_type_opts[opt]
db[table].type.label = T('Type')
db[table].registration.label = T('Registration')
db[table].website.requires = IS_NULL_OR(IS_URL())
db[table].website.label = T('Website')
ADD_ORGANISATION = T('Add Organisation')
title_create = T('Add Organisation')
title_display = T('Organisation Details')
title_list = T('List Organisations')
title_update = T('Edit Organisation')
title_search = T('Search Organisations')
subtitle_create = T('Add New Organisation')
subtitle_list = T('Organisations')
label_list_button = T('List Organisations')
label_create_button = ADD_ORGANISATION
msg_record_created = T('Organisation added')
msg_record_modified = T('Organisation updated')
msg_record_deleted = T('Organisation deleted')
msg_list_empty = T('No Organisations currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
# Reusable field for other tables to reference
organisation_id = SQLTable(None, 'organisation_id',
            Field('organisation_id', db.or_organisation,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'or_organisation.id', '%(name)s')),
                represent = lambda id: (id and [db(db.or_organisation.id==id).select()[0].name] or ["None"])[0],
                label = T('Organisation'),
                comment = DIV(A(ADD_ORGANISATION, _class='thickbox', _href=URL(r=request, c='or', f='organisation', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_ORGANISATION), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Organisation|The Organisation this record is associated with."))),
                ondelete = 'RESTRICT'
                ))

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
# JOINed resource (component)
s3xrc.model.add_component('gis', 'location',
    multiple = False,
    joinby =  dict(or_office='location_id'),
    deletable = False,
    editable = True,
    list_fields = ['id', 'lat', 'lon', 'marker_id'])

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
                migrate=migrate)
db[table].person_id.label = T('Contact')
db[table].office_id.requires = IS_ONE_OF(db, 'or_office.id', '%(name)s')
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

# Offices to Organisations
#resource='organisation_offices'
resource = 'office_to_organisation'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                Field('office_id', db.or_office),
                Field('organisation_id', db.or_organisation),
                migrate=migrate)
db[table].office_id.requires = IS_ONE_OF(db, 'or_office.id', '%(name)s')
db[table].office_id.label = T('Office')
db[table].organisation_id.requires = IS_ONE_OF(db, 'or_organisation.id', '%(name)s')
db[table].organisation_id.label = T('Organisation')

# Contacts to Organisations
# Do we want to allow contacts which are affiliated to an organisation but not to an office?
# default can be HQ office
#resource='contact_to_organisation'
#table=module+'_'+resource
#db.define_table(table,timestamp,
#                Field('contact_id',db.or_contact),
#                Field('organisation_id',db.or_organisation))
#db[table].contact_id.requires=IS_ONE_OF(db,'or_office.id','%(name)s')
#db[table].organisation_id.requires=IS_ONE_OF(db,'or_organisation.id','%(name)s')

