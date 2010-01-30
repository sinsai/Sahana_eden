# -*- coding: utf-8 -*-

module = 'cr'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)

# Shelters
resource = 'shelter'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', notnull=True),
                Field('description'),
                admin_id,
                location_id,
                person_id,
                Field('address', 'text'),
                Field('capacity', 'integer'),
                Field('dwellings', 'integer'),
                Field('persons_per_dwelling', 'integer'),
                Field('area'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()   # Shelters don't have to have unique names
db[table].name.label = T('Shelter Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].description.label = T('Description')
db[table].admin.label = T('Shelter Manager')
db[table].person_id.label = T('Contact Person')
db[table].address.label = T('Address')
db[table].capacity.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999))
db[table].capacity.label = T('Capacity')
db[table].dwellings.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
db[table].dwellings.label = T('Dwellings')
db[table].persons_per_dwelling.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999))
db[table].persons_per_dwelling.label = T('Persons per Dwelling')
db[table].area.label = T('Area')
ADD_SHELTER = T('Add Shelter')
LIST_SHELTERS = T('List Shelters')
s3.crud_strings[table] = Storage(
    title_create = T('Add Shelter'),
    title_display = ADD_SHELTER,
    title_list = LIST_SHELTERS,
    title_update = T('Edit Shelter'),
    title_search = T('Search Shelters'),
    subtitle_create = T('Add New Shelter'),
    subtitle_list = T('Shelters'),
    label_list_button = LIST_SHELTERS,
    label_create_button = ADD_SHELTER,
    msg_record_created = T('Shelter added'),
    msg_record_modified = T('Shelter updated'),
    msg_record_deleted = T('Shelter deleted'),
    msg_list_empty = T('No Shelters currently registered'))

shelter_id = SQLTable(None, 'shelter_id',
                      Field('shelter_id', db.pr_pentity,
                            requires = IS_NULL_OR(IS_ONE_OF(db, 'cr_shelter.id', "%(name)s")),
                            represent = lambda id: (id and [db.cr_shelter[id].name] or ["None"])[0],
                            ondelete = 'RESTRICT',
                            label = T('Shelter')
                           )
                     )
