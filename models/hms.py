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
hms_hospital_status_opts = {
    1: T('operative 100%'),
    2: T('operative 75%'),
    3: T('operative 50%'),
    4: T('operative 25%'),
    5: T('not operative')
}
resource = 'hospital'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', notnull=True),
                location_id,
                Field('address', 'text'),               # Address
                Field('postcode'),
                Field('phone1'),                        # Contact Number
                Field('phone2'),
                Field('email'),
                Field('fax'),
                Field('status', 'integer',              # Status
                      requires = IS_IN_SET(hms_hospital_status_opts),
                      default = 99,
                      label = T('Status'),
                      represent = lambda opt: opt and hms_hospital_status_opts[opt]),
                Field('doctors', 'integer'),            # Number of Doctors
                Field('nurses', 'integer'),             # Number of Nurses
                Field('non_medical_staff', 'integer'),  # Number of Non-Medical Staff
                Field('total_beds', 'integer'),         # Total Beds
                Field('available_beds', 'integer'),     # Available Beds
                Field('patients', 'integer'),           # Number of Patients
                Field('services', 'text'),              # Services Available
                Field('needs', 'text'),                 # Needs
                Field('damage', 'text'),                # Damage
                migrate=migrate)

db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")

db[table].address.label = T('Address')
db[table].postcode.label = T('Postcode')
db[table].phone1.label = T('Phone 1')
db[table].phone2.label = T('Phone 2')
db[table].email.requires = IS_NULL_OR(IS_EMAIL())
db[table].email.label = T('Email')
db[table].fax.label = T('FAX')

db[table].doctors.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
db[table].doctors.label = T('Number of doctors')
db[table].nurses.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
db[table].nurses.label = T('Number of nurses')
db[table].non_medical_staff.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
db[table].non_medical_staff.label = T('Number of non-medical staff')

db[table].total_beds.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
db[table].total_beds.label = T('Total number of beds')
db[table].available_beds.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
db[table].available_beds.label = T('Number of beds available')

db[table].patients.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
db[table].patients.label = T('Number of patients')

db[table].services.label = T('Services available')
db[table].needs.label = T('Needs')
db[table].damage.label = T('Damage')

title_create = T('Add Hospital')
title_display = T('Hospital Details')
title_list = T('List Hospitals')
title_update = T('Edit Hospital')
title_search = T('Search Hospitals')
subtitle_create = T('Add New Hospital')
subtitle_list = T('Hospitals')
label_list_button = T('List Hospitals')
label_create_button = T('Add Hospital')
msg_record_created = T('Hospital added')
msg_record_modified = T('Hospital updated')
msg_record_deleted = T('Hospital deleted')
msg_list_empty = T('No hospitals currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

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
        return "<b>%s</b>: <br/>Location: %s [Lat: %.6f Lon: %.6f]<br/>Status: %s<br/>Beds available: %s" % (
            record.name,
            location_name,
            lat,
            lon,
            record.status and hms_hospital_status_opts[record.status] or T("unknown"),
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
db[table].title.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Title|The Role this person plays within this hospital."))

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
msg_record_created = T('Contact added')
msg_record_modified = T('Contact updated')
msg_record_deleted = T('Contact deleted')
msg_list_empty = T('No contacts currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# -----------------------------------------------------------------------------
# Shortages
#
hms_shortage_type_opts = {
    1: T('Water'),
    2: T('Power'),
    3: T('Food'),
    4: T('Medicines'),
    5: T('Materials'),
    6: T('Medical Staff'),
    7: T('Non-medical Staff'),
    8: T('Security'),
    9: T('Transport'),
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
db.define_table(table, timestamp, deletion_status,
                hospital_id,
                Field('date','datetime'),
                Field('type', 'integer',
                      requires = IS_IN_SET(hms_shortage_type_opts),
                      default = 99,
                      label = T('Type'),
                      represent = lambda opt: opt and hms_shortage_type_opts[opt]),
                Field('impact', 'integer',
                      requires = IS_IN_SET(hms_shortage_impact_opts),
                      default = 3,
                      label = T('Impact'),
                      represent = lambda opt: opt and hms_shortage_impact_opts[opt]),
                Field('priority', 'integer',
                      requires = IS_IN_SET(hms_shortage_priority_opts),
                      default = 4,
                      label = T('Priority'),
                      represent = lambda opt: opt and hms_shortage_priority_opts[opt]),
                Field('subject'),
                Field('description', 'text'),
                Field('status', 'integer',
                      requires = IS_IN_SET(hms_shortage_status_opts),
                      default = 1,
                      label = T('Status'),
                      represent = lambda opt: opt and hms_shortage_status_opts[opt]),
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
                        TH(T('Total Beds: ')),
                        hospital.total_beds,
                        TH(A(T('Clear Selection'),
                            _href=URL(r=request, f='hospital', args='clear', vars={'_next': _same})))
                        ),
                    TR(
                        TH(T('Location: ')),
                        db.gis_location[hospital.location_id] and db.gis_location[hospital.location_id].name or "unknown",
                        TH(T('Available Beds: ')),
                        hospital.available_beds,
                        TH(""),
                        ),
                    TR(
                        TH(T('Status: ')),
                        "%s" % hms_hospital_status_opts[hospital.status],
                        TH(""),
                        "",
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
                        result.status and hms_hospital_status_opts[result.status] or "unknown",
                        ))
                items=DIV(TABLE(THEAD(TR(
                    TH("Name"),
                    TH("Status"))),
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
                        row.phone1,
                        row.fax,
                        row.status and hms_hospital_status_opts[row.status] or "unknown",
                        row.total_beds,
                        row.available_beds
                        ))
                items=DIV(TABLE(THEAD(TR(
                    TH("Name"),
                    TH("Location"),
                    TH("Phone"),
                    TH("Fax"),
                    TH("Status"),
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
