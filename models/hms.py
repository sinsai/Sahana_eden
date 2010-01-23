# -*- coding: utf-8 -*-

"""
    HMS Hospital Management System

    @author: nursix
"""

module = 'hms'

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
# Hospitals
#
hms_facility_status_opts = {
    1: T('Normal'),
    2: T('Compromised'),
    3: T('Evacuating'),
    4: T('Closed')
}

hms_clinical_status_opts = {
    1: T('Normal'),
    2: T('Full'),
    3: T('Closed')
}

hms_morgue_status_opts = {
    1: T('Open'),
    2: T('Full'),
    3: T('Exceeded'),
    4: T('Closed')
}

hms_security_status_opts = {
    1: T('Normal'),
    2: T('Elevated'),
    3: T('Restricted Access'),
    4: T('Lockdown'),
    5: T('Quarantine'),
    6: T('Closed')
}

hms_resource_status_opts = {
    1: T('Adequate'),
    2: T('Insufficient')
}

hms_ems_traffic_opts = {
    1: T('Normal'),
    2: T('Advisory'),
    3: T('Closed'),
    4: T('Not Applicable')
}


resource = 'hospital'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', notnull=True),
                organisation_id,
                location_id,
                Field('address'),
                Field('postcode'),
                Field('city'),
                Field('phone_business'),
                Field('phone_emergency'),
                Field('email'),
                Field('fax'),
                Field('total_beds', 'integer'),         # Total Beds
                Field('available_beds', 'integer'),     # Available Beds
                Field('ems_status', 'integer',
                      requires = IS_NULL_OR(IS_IN_SET(hms_ems_traffic_opts)),
                      label = T('EMS Traffic Status'),
                      represent = lambda opt: hms_ems_traffic_opts.get(opt, T('Unknown'))),
                Field('ems_reason', length=128),
                Field('facility_status', 'integer',
                      requires = IS_NULL_OR(IS_IN_SET(hms_facility_status_opts)),
                      label = T('Facility Status'),
                      represent = lambda opt: hms_facility_status_opts.get(opt, T('Unknown'))),
                Field('clinical_status', 'integer',
                      requires = IS_NULL_OR(IS_IN_SET(hms_clinical_status_opts)),
                      label = T('Clinical Status'),
                      represent = lambda opt: hms_clinical_status_opts.get(opt, T('Unknown'))),
                Field('morgue_status', 'integer',
                      requires = IS_NULL_OR(IS_IN_SET(hms_morgue_status_opts)),
                      label = T('Morgue Status'),
                      represent = lambda opt: hms_clinical_status_opts.get(opt, T('Unknown'))),
                Field('morgue_units', 'integer'),
                Field('security_status', 'integer',
                      requires = IS_NULL_OR(IS_IN_SET(hms_security_status_opts)),
                      label = T('Security Status'),
                      represent = lambda opt: hms_security_status_opts.get(opt, T('Unknown'))),
                Field('doctors', 'integer'),            # Number of Doctors
                Field('nurses', 'integer'),             # Number of Nurses
                Field('non_medical_staff', 'integer'),  # Number of Non-Medical Staff
                Field('patients', 'integer'),           # Current Number of Patients
                Field('admissions24', 'integer'),       # Admissions in the past 24 hours
                Field('discharges24', 'integer'),       # Discharges in the past 24 hours
                Field('deaths24', 'integer'),           # Deaths in the past 24 hours
                Field('staffing', 'integer',
                      requires = IS_NULL_OR(IS_IN_SET(hms_resource_status_opts)),
                      label = T('Staffing'),
                      represent = lambda opt: hms_resource_status_opts.get(opt, T('Unknown'))),
                Field('facility_operations', 'integer',
                      requires = IS_NULL_OR(IS_IN_SET(hms_resource_status_opts)),
                      label = T('Facility Operations'),
                      represent = lambda opt: hms_resource_status_opts.get(opt, T('Unknown'))),
                Field('clinical_operations', 'integer',
                      requires = IS_NULL_OR(IS_IN_SET(hms_resource_status_opts)),
                      label = T('Clinical Operations'),
                      represent = lambda opt: hms_resource_status_opts.get(opt, T('Unknown'))),
                #Field('services', 'text'),              # Services Available, TODO: make component
                #Field('needs', 'text'),                 # Needs, TODO: make component
                #Field('damage', 'text'),                # Damage, TODO: make component
                shn_comments_field,
                migrate=migrate)

db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

db[table].organisation_id.represent = lambda id: (id and [db(db.or_organisation.id==id).select()[0].acronym] or ["None"])[0]

db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")

db[table].address.label = T('Address')
db[table].postcode.label = T('Postcode')
db[table].phone_business.label = T('Phone/Business')
db[table].phone_emergency.label = T('Phone/Emergency')
db[table].email.requires = IS_NULL_OR(IS_EMAIL())
db[table].email.label = T('Email')
db[table].fax.label = T('FAX')

db[table].total_beds.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
db[table].total_beds.label = T('Total Beds')
db[table].total_beds.writable = False
db[table].total_beds.comment = A(SPAN("[Help]"), _class="tooltip",
    _title=T("Total Beds|Total number of beds in this hospital. Automatically updated from unit reports."))
db[table].available_beds.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
db[table].available_beds.label = T('Available Beds')
db[table].available_beds.writable = False
db[table].available_beds.comment = A(SPAN("[Help]"), _class="tooltip",
    _title=T("Available Beds|Number of vacant/available beds in this hospital. Automatically updated from unit reports."))

db[table].ems_status.comment = A(SPAN("[Help]"), _class="tooltip",
    _title=T("EMS Status|Status of operations of the emergency department of this hospital."))
db[table].ems_reason.comment = A(SPAN("[Help]"), _class="tooltip",
    _title=T("EMS Reason|Report the contributing factors for the current EMS status."))

db[table].facility_status.comment = A(SPAN("[Help]"), _class="tooltip",
    _title=T("Facility Status|Status of general operation of the facility."))
db[table].clinical_status.comment = A(SPAN("[Help]"), _class="tooltip",
    _title=T("Clinical Status|Status of clinical operation of the facility."))
db[table].morgue_status.comment = A(SPAN("[Help]"), _class="tooltip",
    _title=T("Morgue Status|Status of morgue capacity."))
db[table].security_status.comment = A(SPAN("[Help]"), _class="tooltip",
    _title=T("Security Status|Status of security procedures/access restrictions in the hospital."))
db[table].morgue_units.comment =  A(SPAN("[Help]"), _class="tooltip",
    _title=T("Morgue Units Available|Number of vacant/available units to which victims can be transported immediately."))

db[table].morgue_units.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
db[table].morgue_units.label = T('Morgue Units Available')

db[table].doctors.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
db[table].doctors.label = T('Number of doctors')
db[table].nurses.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
db[table].nurses.label = T('Number of nurses')
db[table].non_medical_staff.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
db[table].non_medical_staff.label = T('Number of non-medical staff')

db[table].patients.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
db[table].patients.label = T('Number of Patients')
db[table].admissions24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
db[table].admissions24.label = T('Admissions/24hrs')
db[table].discharges24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
db[table].discharges24.label = T('Discharges/24hrs')
db[table].deaths24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
db[table].deaths24.label = T('Deaths/24hrs')

#db[table].services.label = T('Services available')
#db[table].needs.label = T('Needs')
#db[table].damage.label = T('Damage')

title_create = T('Add Hospital')
title_display = T('Hospital Details')
title_list = T('List Hospitals')
title_update = T('Edit Hospital')
title_search = T('Search Hospitals')
subtitle_create = T('Add New Hospital')
subtitle_list = T('Hospitals')
label_list_button = T('List Hospitals')
label_create_button = T('Add Hospital')
label_delete_button = T('Delete Hospital')
msg_record_created = T('Hospital information added')
msg_record_modified = T('Hospital information updated')
msg_record_deleted = T('Hospital information deleted')
msg_list_empty = T('No hospitals currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,label_delete_button=label_delete_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Reusable field for other tables to reference
hospital_id = SQLTable(None, 'hospital_id',
                       Field('hospital_id', db.hms_hospital,
                             requires = IS_NULL_OR(IS_ONE_OF(db, 'hms_hospital.id', '%(name)s')),
                             represent = lambda id: (id and [db(db.hms_hospital.id==id).select()[0].name] or ["None"])[0],
                             label = T('Hospital'),
                             comment = DIV(A(title_create, _class='thickbox', _href=URL(r=request, c='hms', f='hospital', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=title_create), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Hospital|The hospital this record is associated with."))),
                             ondelete = 'RESTRICT'))

# RSS
def shn_hms_hospital_rss(record):
    if record:
        if record.location_id:
            location = db.gis_location[record.location_id]
            if location:
                lat = location.lat
                lon = location.lon
                location_name = location.name
            else:
                lat = lon = T("unknown")
                location_name = T("unknown")
        return "<b>%s</b>: <br/>Location: %s [Lat: %.6f Lon: %.6f]<br/>Facility Status: %s<br/>Clinical Status: %s<br/>Morgue Status: %s<br/>Security Status: %s<br/>Beds available: %s" % (
            record.name,
            location_name,
            lat,
            lon,
            record.facility_status and hms_facility_status_opts[record.facility_status] or T("unknown"),
            record.clinical_status and hms_clinical_status_opts[record.clinical_status] or T("unknown"),
            record.morgue_status and hms_morgue_status_opts[record.morgue_status] or T("unknown"),
            record.security_status and hms_security_status_opts[record.security_status] or T("unknown"),
            (record.available_beds is not None) and record.available_beds or T("unknown")
            )
    else:
        return None

# -----------------------------------------------------------------------------
# Contacts
#
resource = 'contact'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                hospital_id,
                person_id,
                Field('title'),
                Field('phone1'),
                Field('phone2'),
                Field('email'),
                Field('fax'),
                Field('skype'),
                migrate=migrate)

db[table].person_id.label = T('Contact')
db[table].title.label = T('Job Title')
db[table].title.comment = A(SPAN("[Help]"), _class="tooltip",
    _title=T("Title|The Role this person plays within this hospital."))

db[table].phone1.label = T('Phone 1')
db[table].phone2.label = T('Phone 2')
db[table].email.requires = IS_NULL_OR(IS_EMAIL())
db[table].email.label = T('Email')
db[table].fax.label = T('FAX')
db[table].skype.label = T('Skype ID')

s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(hms_hospital='hospital_id'),
    deletable=True,
    editable=True,
    main='person_id', extra='title',
    list_fields = ['id', 'person_id', 'title', 'phone1', 'phone2', 'email', 'fax', 'skype'])

# CRUD Strings
title_create = T('Add Contact')
title_display = T('Contact Details')
title_list = T('Contacts')
title_update = T('Edit Contact')
title_search = T('Search Contacts')
subtitle_create = T('Add New Contact')
subtitle_list = T('Contacts')
label_list_button = T('List Contacts')
label_create_button = T('Add Contact')
msg_record_created = T('Contact information added')
msg_record_modified = T('Contact information updated')
msg_record_deleted = T('Contact information deleted')
msg_list_empty = T('No contacts currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# -----------------------------------------------------------------------------
# Bed Capacity (multiple)
#
hms_bed_type_opts = {
    1: T('Adult ICU'),
    2: T('Pediatric ICU'),
    3: T('Neonatal ICU'),
    4: T('Emergency Department'),
    5: T('Nursery Beds'),
    6: T('General Medical/Surgical'),
    7: T('Rehabilitation/Long Term Care'),
    8: T('Burn ICU'),
    9: T('Pediatrics'),
    10: T('Adult Psychiatric'),
    11: T('Pediatric Psychiatric'),
    12: T('Negative Flow Isolation'),
    13: T('Other Isolation'),
    14: T('Operating Rooms'),
    99: T('Other')
}

resource = 'bed_capacity'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, authorstamp, deletion_status,
                hospital_id,
                Field('unit_name', length=64),
                Field('bed_type', 'integer',
                      requires = IS_IN_SET(hms_bed_type_opts),
                      default = 6,
                      label = T('Bed Type'),
                      represent = lambda opt: hms_bed_type_opts.get(opt, T('Unknown'))),
                Field('date', 'datetime'),
                Field('beds_baseline', 'integer'),
                Field('beds_available', 'integer'),
                Field('beds_add24', 'integer'),
                Field('comment', length=128),
                migrate=migrate)

db[table].unit_name.label = T('Department/Unit Name')
db[table].date.label = T('Date of Report')

db[table].beds_baseline.label = T('Baseline Number of Beds')
db[table].beds_available.label = T('Available Beds')
db[table].beds_add24.label = T('Additional Beds / 24hrs')

db[table].beds_baseline.comment = A(SPAN("[Help]"), _class="tooltip",
    _title=T("Baseline Number of Beds|Baseline number of beds of that type in this unit."))
db[table].beds_available.comment = A(SPAN("[Help]"), _class="tooltip",
    _title=T("Available Beds|Number of available/vacant beds of that type in this unit at the time of reporting."))
db[table].beds_add24.comment = A(SPAN("[Help]"), _class="tooltip",
    _title=T("Additional Beds / 24hrs|Number of additional beds of that type expected to become available in this unit within the next 24 hours."))

# -----------------------------------------------------------------------------
# shn_hms_bedcount_update:
#   updates the number of total/available beds of a hospital
#
def shn_hms_bedcount_update(form):

    query = ((db.hms_bed_capacity.id==form.vars.id) &
             (db.hms_hospital.id==db.hms_bed_capacity.hospital_id))
    hospital = db(query).select(db.hms_hospital.id, limitby=(0, 1))

    if hospital:
        hospital=hospital[0]

        a_beds = db.hms_bed_capacity.beds_available.sum()
        t_beds = db.hms_bed_capacity.beds_baseline.sum()
        count = db(db.hms_bed_capacity.hospital_id==hospital.id).select(a_beds, t_beds)
        if count:
            a_beds = count[0]._extra[a_beds]
            t_beds = count[0]._extra[t_beds]

        db(db.hms_hospital.id==hospital.id).update(
            total_beds=t_beds,
            available_beds=a_beds)

# -----------------------------------------------------------------------------
# add as component
#
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(hms_hospital='hospital_id'),
    deletable=True,
    editable=True,
    onaccept=shn_hms_bedcount_update,
    main='hospital_id', extra='id',
    list_fields = ['id', 'unit_name', 'bed_type', 'date', 'beds_baseline', 'beds_available', 'beds_add24'])

title_create = T('Add Unit')
title_display = T('Unit Bed Capacity')
title_list = T('List Units')
title_update = T('Update Unit')
title_search = T('Search Units')
subtitle_create = T('Add Unit')
subtitle_list = T('Bed Capacity per Unit')
label_list_button = T('List Units')
label_create_button = T('Add Unit')
label_delete_button = T('Delete Unit')
msg_record_created = T('Unit added')
msg_record_modified = T('Unit updated')
msg_record_deleted = T('Unit deleted')
msg_list_empty = T('No units currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,label_delete_button=label_delete_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# -----------------------------------------------------------------------------
# Services
#
resource = 'services'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, authorstamp, deletion_status,
                hospital_id,
                Field('burn', 'boolean', default=False),
                Field('card', 'boolean', default=False),
                Field('dial', 'boolean', default=False),
                Field('emsd', 'boolean', default=False),
                Field('infd', 'boolean', default=False),
                Field('neon', 'boolean', default=False),
                Field('neur', 'boolean', default=False),
                Field('pedi', 'boolean', default=False),
                Field('surg', 'boolean', default=False),
                Field('labs', 'boolean', default=False),
                Field('tran', 'boolean', default=False),
                Field('tair', 'boolean', default=False),
                Field('trac', 'boolean', default=False),
                Field('psya', 'boolean', default=False),
                Field('psyp', 'boolean', default=False),
                Field('obgy', 'boolean', default=False),
                migrate=migrate)

db[table].burn.label = T('Burn')
db[table].card.label = T('Cardiology')
db[table].dial.label = T('Dialysis')
db[table].emsd.label = T('Emergency Department')
db[table].infd.label = T('Infectious Diseases')
db[table].neon.label = T('Neonatology')
db[table].neur.label = T('Neurology')
db[table].pedi.label = T('Pediatrics')
db[table].surg.label = T('Surgery')
db[table].labs.label = T('Clinical Laboratory')
db[table].tran.label = T('Ambulance Service')
db[table].tair.label = T('Air Transport Service')
db[table].trac.label = T('Trauma Center')
db[table].psya.label = T('Psychiatrics/Adult')
db[table].psyp.label = T('Psychiatrics/Pediatric')
db[table].obgy.label = T('Obstetrics/Gynecology')

title_create = T('Add Service Profile')
title_display = T('Services Available')
title_list = T('Services Available')
title_update = T('Update Service Profile')
title_search = T('Search Service Profiles')
subtitle_create = T('Add Service Profile')
subtitle_list = T('Services Available')
label_list_button = T('List Service Profiles')
label_create_button = T('Add Service Profile')
label_delete_button = T('Delete Service Profile')
msg_record_created = T('Service profile added')
msg_record_modified = T('Service profile updated')
msg_record_deleted = T('Service profile deleted')
msg_list_empty = T('No service profile available')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,label_delete_button=label_delete_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

s3xrc.model.add_component(module, resource,
    multiple=False,
    joinby=dict(hms_hospital='hospital_id'),
    deletable=True,
    editable=True,
    main='hospital_id', extra='id',
    list_fields = ['id'])

# -----------------------------------------------------------------------------
# Resources (multiple) - TODO: this incomplete
#
resource = 'resources'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, authorstamp, deletion_status,
                hospital_id,
                Field('type'),
                Field('description'),
                Field('quantity'),
                Field('comment'),
                migrate=migrate)

# CRUD Strings
title_create = T('Report Resource')
title_display = T('Resource Details')
title_list = T('Resources')
title_update = T('Edit Resource')
title_search = T('Search Resources')
subtitle_create = T('Add New Resource')
subtitle_list = T('Resources')
label_list_button = T('List Resources')
label_create_button = T('Add Resource')
label_delete_button = T('Delete Resource')
msg_record_created = T('Resource added')
msg_record_modified = T('Resource updated')
msg_record_deleted = T('Resource deleted')
msg_list_empty = T('No resources currently reported')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,label_delete_button=label_delete_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Add as component
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(hms_hospital='hospital_id'),
    deletable=True,
    editable=True,
    main='hospital_id', extra='id',
    list_fields = ['id'])

# -----------------------------------------------------------------------------
# Shortages
#
hms_shortage_type_opts = {
    1: T('Water'),
    2: T('Power'),
    3: T('Food'),
    4: T('Medical Supplies'),
    5: T('Medical Staff'),
    6: T('Non-medical Staff'),
    7: T('Security'),
    8: T('Transport'),
    9: T('Fuel'),
    99: T('Other')
}

hms_shortage_impact_opts = {
    1: T('highly critical'),
    2: T('critical'),
    3: T('not critical'),
}

hms_shortage_priority_opts = {
    1: T('immediately'),
    2: T('urgent'),
    3: T('high'),
    4: T('normal'),
    5: T('low')
}

hms_shortage_status_opts = {
    1: T('open'),
    2: T('compensated'),
    3: T('feedback'),
    4: T('remedied')
}

from datetime import datetime

resource = 'shortage'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, authorstamp, deletion_status,
                hospital_id,
                Field('date','datetime'),
                Field('type', 'integer',
                      requires = IS_IN_SET(hms_shortage_type_opts),
                      default = 99,
                      label = T('Type'),
                      represent = lambda opt: hms_shortage_type_opts.get(opt, T('Unknown'))),
                Field('impact', 'integer',
                      requires = IS_IN_SET(hms_shortage_impact_opts),
                      default = 3,
                      label = T('Impact'),
                      represent = lambda opt: hms_shortage_impact_opts.get(opt, T('Unknown'))),
                Field('priority', 'integer',
                      requires = IS_IN_SET(hms_shortage_priority_opts),
                      default = 4,
                      label = T('Priority'),
                      represent = lambda opt: hms_shortage_priority_opts.get(opt, T('Unknown'))),
                Field('subject'),
                Field('description', 'text'),
                Field('status', 'integer',
                      requires = IS_IN_SET(hms_shortage_status_opts),
                      default = 1,
                      label = T('Status'),
                      represent = lambda opt: hms_shortage_status_opts.get(opt, T('Unknown'))),
                Field('feedback', 'text'),
                migrate=migrate)

db[table].date.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(), allow_future=False)
db[table].date.represent = lambda value: shn_as_local_time(value)

db[table].subject.requires = IS_NOT_EMPTY()

s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(hms_hospital='hospital_id'),
    deletable=True,
    editable=True,
    main='hospital_id', extra='subject',
    list_fields = ['id', 'hospital_id', 'type', 'impact', 'priority', 'subject', 'status'])

# CRUD Strings
title_create = T('Report Shortage')
title_display = T('Shortage Details')
title_list = T('Shortages')
title_update = T('Edit Shortage')
title_search = T('Search Shortages')
subtitle_create = T('Add New Shortage')
subtitle_list = T('Shortages')
label_list_button = T('List Shortages')
label_create_button = T('Add Shortage')
label_delete_button = T('Delete Shortage')
msg_record_created = T('Shortage added')
msg_record_modified = T('Shortage updated')
msg_record_deleted = T('Shortage deleted')
msg_list_empty = T('No shortages currently reported')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,label_delete_button=label_delete_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# -----------------------------------------------------------------------------
# shn_hms_hospital_pheader:
#   Page Header for hospitals
#
def shn_hms_hospital_pheader(resource, record_id, representation, next=None, same=None):

    if resource == "hospital":
        if representation == "html":

            if next:
                _next = next
            else:
                _next = URL(r=request, f=resource, args=['read'])

            if same:
                _same = same
            else:
                _same = URL(r=request, f=resource, args=['read', '[id]'])

            hospital = db.hms_hospital[record_id]
            if hospital:
                pheader = TABLE(
                    TR(
                        TH(T('Name: ')),
                        hospital.name,
                        TH(T('EMS Status: ')),
                        "%s" % hms_ems_traffic_opts[hospital.ems_status],
                        TH(A(T('Clear Selection'),
                            _href=URL(r=request, f='hospital', args='clear', vars={'_next': _same})))
                        ),
                    TR(
                        TH(T('Location: ')),
                        db.gis_location[hospital.location_id] and db.gis_location[hospital.location_id].name or "unknown",
                        TH(T('Facility Status: ')),
                        "%s" % hms_facility_status_opts[hospital.facility_status],
                        TH(""),
                        "",
                      ),
                    TR(
                        TH(T('Total Beds: ')),
                        hospital.total_beds,
                        TH(T('Clinical Status: ')),
                        "%s" % hms_clinical_status_opts[hospital.clinical_status],
                        TH(""),
                        "",
                      ),
                    TR(
                        TH(T('Available Beds: ')),
                        hospital.available_beds,
                        TH(T('Security Status: ')),
                        "%s" % hms_security_status_opts[hospital.security_status],
                        TH(A(T('Edit Hospital'),
                            _href=URL(r=request, f='hospital', args=['update', record_id], vars={'_next': _next})))
                        )
                )
                return pheader

    return None

# -----------------------------------------------------------------------------
# shn_hms_hospital_search_location:
#   form function to search hospitals by location
#
def shn_hms_hospital_search_location(xrequest, onvalidation=None, onaccept=None):

    if not shn_has_permission('read', db.hms_hospital):
        session.error = UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, args='search_location', vars=request.vars)}))

    if xrequest.representation=="html":
        # Check for redirection
        if request.vars._next:
            next = str.lower(request.vars._next)
        else:
            next = str.lower(URL(r=request, f='hospital', args='[id]'))

        # Custom view
        response.view = '%s/hospital_search.html' % xrequest.prefix

        # Title and subtitle
        title = T('Search for a Hospital')
        subtitle = T('Matching Records')

        # Select form:
        l_opts = [OPTION(_value='')]
        l_opts += [OPTION(location.name, _value=location.id)
                  for location in db(db.gis_location.deleted==False).select(db.gis_location.ALL)]
        form = FORM(TABLE(
                TR(T('Location: '),
                SELECT(_name="location", *l_opts, **dict(name="location", requires=IS_NULL_OR(IS_IN_DB(db,'gis_location.id'))))),
                TR("", INPUT(_type="submit", _value="Search"))
                ))

        output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

        # Accept action
        items = None
        if form.accepts(request.vars, session):

            table = db.hms_hospital
            query = (table.deleted==False)

            if form.vars.location is None:
                results = db(query).select(table.ALL)
            else:
                query = query & (table.location_id==form.vars.location)
                results = db(query).select(table.ALL)

            if results and len(results):
                records = []
                for result in results:
                    href = next.replace('%5bid%5d', '%s' % result.id)
                    records.append(TR(
                        A(result.name, _href=href),
                        result.ems_status and hms_ems_traffic_opts[result.ems_status] or "unknown",
                        result.facility_status and hms_facility_status_opts[result.facility_status] or "unknown",
                        result.clinical_status and hms_clinical_status_opts[result.clinical_status] or "unknown",
                        result.security_status and hms_security_status_opts[result.security_status] or "unknown",
                        ))
                items=DIV(TABLE(THEAD(TR(
                    TH("Name"),
                    TH("EMS Status"),
                    TH("Facility Status"),
                    TH("Clinical Status"),
                    TH("Security Status"))),
                    TBODY(records), _id='list', _class="display"))
            else:
                    items = T('None')

        try:
            label_create_button = s3.crud_strings['hms_hospital'].label_create_button
        except:
            label_create_button = s3.crud_strings.label_create_button

        add_btn = A(label_create_button, _href=URL(r=request, f='hospital', args='create'), _id='add-btn')

        output.update(dict(items=items, add_btn=add_btn))

        return output

    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

# Plug into REST controller
s3xrc.model.set_method(module, 'hospital', method='search_location', action=shn_hms_hospital_search_location )

# -----------------------------------------------------------------------------
# shn_hms_get_hospital:
#   form function to search hospitals by name
#
def shn_hms_get_hospital(label, fields=None, filterby=None):

    if fields and isinstance(fields, (list,tuple)):
        search_fields = []
        for f in fields:
            if db.hms_hospital.has_key(f):
                search_fields.append(f)
        if not len(search_fields):
            return None
    else:
        search_fields = ['name', 'address']

    if label and isinstance(label,str):
        labels = label.split()
        results = []
        query = None
        for l in labels:

            # append wildcards
            wc = "%"
            _l = "%s%s%s" % (wc, l, wc)

            # build query
            for f in search_fields:
                if query:
                    query = (db.hms_hospital[f].like(_l)) | query
                else:
                    query = (db.hms_hospital[f].like(_l))

            # undeleted records only
            query = (db.hms_hospital.deleted==False) & (query)
            # restrict to prior results (AND)
            if len(results):
                query = (db.hms_hospital.id.belongs(results)) & query
            if filterby:
                query = (filterby) & (query)
            records = db(query).select(db.hms_hospital.id)
            # rebuild result list
            results = [r.id for r in records]
            # any results left?
            if not len(results):
                return None
        return results
    else:
        # no label given or wrong parameter type
        return None

# -----------------------------------------------------------------------------
# shn_hms_hospital_search_simple:
#   form function to search hospitals by name
#
def shn_hms_hospital_search_simple(xrequest, onvalidation=None, onaccept=None):
    """
        Simple search form for hospitals
    """

    if not shn_has_permission('read', db.hms_hospital):
        session.error = UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, args='search_simple', vars=request.vars)}))

    if xrequest.representation=="html":
        # Check for redirection
        if request.vars._next:
            next = str.lower(request.vars._next)
        else:
            next = str.lower(URL(r=request, f='hospital', args='[id]'))

        # Custom view
        response.view = '%s/hospital_search.html' % xrequest.prefix

        # Title and subtitle
        title = T('Search for a Hospital')
        subtitle = T('Matching Records')

        # Select form
        form = FORM(TABLE(
                TR(T('Name: '),
                   INPUT(_type="text", _name="label", _size="40"),
                   A(SPAN("[Help]"), _class="tooltip", _title=T("Name|To search for a hospital, enter any part of the name. You may use % as wildcard. Press 'Search' without input to list all hospitals."))),
                TR("", INPUT(_type="submit", _value="Search"))
                ))

        output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

        # Accept action
        items = None
        if form.accepts(request.vars, session):

            if form.vars.label == "":
                form.vars.label = "%"

            results = shn_hms_get_hospital(form.vars.label)

            if results and len(results):
                rows = db(db.hms_hospital.id.belongs(results)).select()
            else:
                rows = None

            # Build table rows from matching records
            if rows:
                records = []
                for row in rows:
                    href = next.replace('%5bid%5d', '%s' % row.id)
                    records.append(TR(
                        A(row.name, _href=href),
                        db.gis_location[row.location_id] and db.gis_location[row.location_id].name or "unknown",
                        row.phone_business,
                        row.ems_status and hms_ems_traffic_opts[row.ems_status] or "unknown",
                        row.facility_status and hms_facility_status_opts[row.facility_status] or "unknown",
                        row.clinical_status and hms_clinical_status_opts[row.clinical_status] or "unknown",
                        row.security_status and hms_security_status_opts[row.security_status] or "unknown",
                        row.total_beds,
                        row.available_beds
                        ))
                items=DIV(TABLE(THEAD(TR(
                    TH("Name"),
                    TH("Location"),
                    TH("Phone"),
                    TH("EMS Status"),
                    TH("Facility Status"),
                    TH("Clinical Status"),
                    TH("Security Status"),
                    TH("Total Beds"),
                    TH("Available Beds"))),
                    TBODY(records), _id='list', _class="display"))
            else:
                items = T('None')

        try:
            label_create_button = s3.crud_strings['hms_hospital'].label_create_button
        except:
            label_create_button = s3.crud_strings.label_create_button

        add_btn = A(label_create_button, _href=URL(r=request, f='hospital', args='create'), _id='add-btn')

        output.update(dict(items=items, add_btn=add_btn))
        return output

    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

# Plug into REST controller
s3xrc.model.set_method(module, 'hospital', method='search_simple', action=shn_hms_hospital_search_simple )
