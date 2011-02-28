# -*- coding: utf-8 -*-

""" HMS Hospital Status Assessment and Request Management System

    @author: nursix

"""

module = "hms"
if deployment_settings.has_module(module):

    from gluon.sql import Row

    # -----------------------------------------------------------------------------
    # Hospitals
    #

    # Use government-assigned UUIDs instead of internal UUIDs
    HMS_HOSPITAL_USE_GOVUUID = True

    hms_facility_type_opts = {
        1: T("Hospital"),
        2: T("Field Hospital"),
        3: T("Specialized Hospital"),
        11: T("Health center"),
        12: T("Health center with beds"),
        13: T("Health center without beds"),
        21: T("Dispensary"),
        98: T("Other"),
        99: T("Unknown type of facility"),
    } #: Facility Type Options

    hms_facility_status_opts = {
        1: T("Normal"),
        2: T("Compromised"),
        3: T("Evacuating"),
        4: T("Closed")
    } #: Facility Status Options

    hms_clinical_status_opts = {
        1: T("Normal"),
        2: T("Full"),
        3: T("Closed")
    } #: Clinical Status Options

    hms_morgue_status_opts = {
        1: T("Open"),
        2: T("Full"),
        3: T("Exceeded"),
        4: T("Closed")
    } #: Morgue Status Options

    hms_security_status_opts = {
        1: T("Normal"),
        2: T("Elevated"),
        3: T("Restricted Access"),
        4: T("Lockdown"),
        5: T("Quarantine"),
        6: T("Closed")
    } #: Security Status Options

    hms_resource_status_opts = {
        1: T("Adequate"),
        2: T("Insufficient")
    } #: Resource Status Options

    hms_ems_traffic_opts = {
        1: T("Normal"),
        2: T("Advisory"),
        3: T("Closed"),
        4: T("Not Applicable")
    } #: EMS Traffic Options

    hms_or_status_opts = {
        1: T("Normal"),
        #2: T("Advisory"),
        3: T("Closed"),
        4: T("Not Applicable")
    } #: Operating Room Status Options

    resourcename = "hospital"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                    super_link(db.org_site),
                    # PAHO UID
                    Field("paho_uuid", unique=True, length=128),
                    # UID assigned by Local Government
                    Field("gov_uuid", unique=True, length=128),
                    # Alternate ids found in data feeds
                    Field("other_ids", length=128),
                    Field("name", notnull=True),                # Name of the facility
                    Field("aka1"),                              # Alternate name, or name in local language
                    Field("aka2"),                              # Alternate name, or name in local language
                    Field("facility_type", "integer",           # Type of facility
                          requires = IS_NULL_OR(IS_IN_SET(hms_facility_type_opts)),
                          default = 1,
                          label = T("Facility Type"),
                          represent = lambda opt: hms_facility_type_opts.get(opt, T("not specified"))),
                    organisation_id(),
                    location_id(),
                    Field("address"),      # @ToDo: Deprecate these & use location_id in HAVE exporter
                    Field("postcode"),     # @ToDo: Deprecate these & use location_id in HAVE exporter
                    Field("city"),         # @ToDo: Deprecate these & use location_id in HAVE exporter
                    Field("phone_exchange", requires = shn_phone_requires), # Switchboard
                    Field("phone_business", requires = shn_phone_requires),
                    Field("phone_emergency", requires = shn_phone_requires),
                    Field("website", requires = IS_NULL_OR(IS_URL())),
                    Field("email"),
                    Field("fax", requires = shn_phone_requires),
                    Field("total_beds", "integer"),             # Total Beds
                    Field("available_beds", "integer"),         # Available Beds
                    Field("ems_status", "integer",              # Emergency Room Status
                          requires = IS_NULL_OR(IS_IN_SET(hms_ems_traffic_opts)),
                          label = T("ER Status"),
                          represent = lambda opt: hms_ems_traffic_opts.get(opt, UNKNOWN_OPT)),
                    Field("ems_reason", length=128,             # Reason for EMS Status
                          label = T("ER Status Reason")),
                    Field("or_status", "integer",               # Operating Room Status
                          requires = IS_NULL_OR(IS_IN_SET(hms_or_status_opts)),
                          label = T("OR Status"),
                          represent = lambda opt: hms_or_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("or_reason", length=128,              # Reason for OR Status
                          label = T("OR Status Reason")),
                    Field("facility_status", "integer",         # Facility Status
                          requires = IS_NULL_OR(IS_IN_SET(hms_facility_status_opts)),
                          label = T("Facility Status"),
                          represent = lambda opt: hms_facility_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("clinical_status", "integer",         # Clinical Status
                          requires = IS_NULL_OR(IS_IN_SET(hms_clinical_status_opts)),
                          label = T("Clinical Status"),
                          represent = lambda opt: hms_clinical_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("morgue_status", "integer",           # Morgue Status
                          requires = IS_NULL_OR(IS_IN_SET(hms_morgue_status_opts)),
                          label = T("Morgue Status"),
                          represent = lambda opt: hms_clinical_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("morgue_units", "integer"),           # Number of available/vacant morgue units
                    Field("security_status", "integer",         # Security status
                          requires = IS_NULL_OR(IS_IN_SET(hms_security_status_opts)),
                          label = T("Security Status"),
                          represent = lambda opt: hms_security_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("doctors", "integer"),                # Number of Doctors
                    Field("nurses", "integer"),                 # Number of Nurses
                    Field("non_medical_staff", "integer"),      # Number of Non-Medical Staff
                    Field("staffing", "integer",                # Staffing status
                          requires = IS_NULL_OR(IS_IN_SET(hms_resource_status_opts)),
                          label = T("Staffing"),
                          represent = lambda opt: hms_resource_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("facility_operations", "integer",     # Facility Operations Status
                          requires = IS_NULL_OR(IS_IN_SET(hms_resource_status_opts)),
                          label = T("Facility Operations"),
                          represent = lambda opt: hms_resource_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("clinical_operations", "integer",     # Clinical Operations Status
                          requires = IS_NULL_OR(IS_IN_SET(hms_resource_status_opts)),
                          label = T("Clinical Operations"),
                          represent = lambda opt: hms_resource_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("access_status"),                     # Access Status
                    document_id(),                              # Information Source
                    comments(),
                    migrate=migrate, *(s3_meta_fields() +
                                      (meta_record_status(), meta_duplicate_uid())))

    table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
    table.paho_uuid.label = T("PAHO UID")
    table.paho_uuid.requires = IS_NULL_OR(IS_NOT_ONE_OF(db, "%s.paho_uuid" % tablename))
    table.gov_uuid.label = T("Government UID")
    table.gov_uuid.requires = IS_NULL_OR(IS_NOT_ONE_OF(db, "%s.gov_uuid" % tablename))
    table.name.label = T("Name")
    # Hospital names do not have to be unique (same name, different locations/IDs)
    #table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % tablename)]
    table.name.requires = IS_NOT_EMPTY()
    table.aka1.label = T("Other Name")
    table.aka2.label = T("Other Name")
    table.address.label = T("Address")
    table.postcode.label = T("Postcode")
    table.phone_exchange.label = T("Phone/Exchange")
    table.phone_business.label = T("Phone/Business")
    table.phone_emergency.label = T("Phone/Emergency")
    table.email.label = T("Email")
    table.fax.label = T("Fax")
    table.website.represent = shn_url_represent
    table.email.requires = IS_NULL_OR(IS_EMAIL())
    table.total_beds.label = T("Total Beds")
    table.total_beds.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.total_beds.readable = False
    table.total_beds.writable = False
    table.available_beds.label = T("Available Beds")
    table.available_beds.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.available_beds.readable = False
    table.available_beds.writable = False
    table.morgue_units.label = T("Morgue Units Available")
    table.morgue_units.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
    table.doctors.label = T("Number of doctors")
    table.doctors.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
    table.nurses.label = T("Number of nurses")
    table.nurses.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
    table.non_medical_staff.label = T("Number of non-medical staff")
    table.non_medical_staff.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
    table.access_status.label = T("Road Conditions")

    # Reusable field for other tables to reference
    ADD_HOSPITAL = T("Add Hospital")
    shn_hospital_id_comment = DIV(A(ADD_HOSPITAL,
                                    _class="colorbox",
                                    _href=URL(r=request,
                                              c="hms",
                                              f="hospital",
                                              args="create",
                                              vars=dict(format="popup")),
                                    _target="top",
                                    _title=ADD_HOSPITAL),
                                  DIV(DIV(_class="tooltip",
                                          _title=T("Hospital") + "|" + T("The hospital this record is associated with."))))
    hospital_id = S3ReusableField("hospital_id", db.hms_hospital, sortby="name",
                                  requires = IS_NULL_OR(IS_ONE_OF(db, "hms_hospital.id", "%(name)s")),
                                  represent = lambda id: (id and
                                              [db(db.hms_hospital.id == id).select(db.hms_hospital.name, limitby=(0, 1)).first().name] or
                                              ["None"])[0],
                                  label = T("Hospital"),
                                  comment = shn_hospital_id_comment,
                                  ondelete = "RESTRICT")

    s3xrc.model.configure(table,
                          super_entity=db.org_site,
                          list_fields=["id",
                                       "gov_uuid",
                                       "name",
                                       "organisation_id",
                                       "location_id",
                                       "phone_exchange",
                                       "ems_status",
                                       "facility_status",
                                       "clinical_status",
                                       "security_status",
                                       "total_beds",
                                       "available_beds"])

    # -----------------------------------------------------------------------------
    # Contacts
    #
    resourcename = "contact"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            hospital_id(),
                            person_id(label = T("Contact"),
                                      requires = IS_ONE_OF(db, "pr_person.id",
                                                           shn_pr_person_represent,
                                                           orderby="pr_person.first_name",
                                                           sort=True)),
                            Field("title"),
                            Field("phone"),
                            Field("mobile"),
                            Field("email"),
                            Field("fax"),
                            Field("skype"),
                            Field("website"),
                            migrate=migrate,
                            *(s3_timestamp() + s3_deletion_status()))

    table.title.label = T("Job Title")
    table.title.comment = DIV(DIV(_class="tooltip",
        _title=T("Title") + "|" + T("The Role this person plays within this hospital.")))

    table.phone.label = T("Phone")
    table.phone.requires = shn_phone_requires
    table.mobile.label = T("Mobile")
    table.mobile.requires = shn_phone_requires
    table.email.requires = IS_NULL_OR(IS_EMAIL())
    table.email.label = T("Email")
    table.fax.label = T("Fax")
    table.fax.requires = shn_phone_requires
    table.skype.label = T("Skype ID")

    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(hms_hospital="hospital_id"))

    s3xrc.model.configure(table,
                          mark_required = ["person_id"],
                          list_fields=["id",
                                       "person_id",
                                       "title",
                                       "phone",
                                       "mobile",
                                       "email",
                                       "fax",
                                       "skype"],
                          main="person_id", extra="title")

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Contact"),
        title_display = T("Contact Details"),
        title_list = T("Contacts"),
        title_update = T("Edit Contact"),
        title_search = T("Search Contacts"),
        subtitle_create = T("Add New Contact"),
        subtitle_list = T("Contacts"),
        label_list_button = T("List Contacts"),
        label_create_button = T("Add Contact"),
        msg_record_created = T("Contact information added"),
        msg_record_modified = T("Contact information updated"),
        msg_record_deleted = T("Contact information deleted"),
        msg_list_empty = T("No contacts currently registered"))

    # -----------------------------------------------------------------------------
    # Activity
    #
    resourcename = "activity"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            hospital_id(),
                            Field("date", "datetime", unique=True), # Date&Time the entry applies to
                            Field("patients", "integer"),           # Current Number of Patients
                            Field("admissions24", "integer"),       # Admissions in the past 24 hours
                            Field("discharges24", "integer"),       # Discharges in the past 24 hours
                            Field("deaths24", "integer"),           # Deaths in the past 24 hours
                            Field("comment", length=128),
                            migrate=migrate, *s3_meta_fields())


    table.date.label = T("Date & Time")
    table.date.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(),
                                          allow_future=False)
    table.date.represent = lambda value: shn_as_local_time(value)
    table.date.comment = DIV(DIV(_class="tooltip",
        _title=T("Date & Time") + "|" + T("Date and time this report relates to.")))

    table.patients.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.patients.default = 0
    table.patients.label = T("Number of Patients")
    table.patients.comment = DIV(DIV(_class="tooltip",
        _title=T("Patients") + "|" + T("Number of in-patients at the time of reporting.")))

    table.admissions24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.admissions24.default = 0
    table.admissions24.label = T("Admissions/24hrs")
    table.admissions24.comment = DIV(DIV(_class="tooltip",
        _title=T("Admissions/24hrs") + "|" + T("Number of newly admitted patients during the past 24 hours.")))

    table.discharges24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.discharges24.default = 0
    table.discharges24.label = T("Discharges/24hrs")
    table.discharges24.comment = DIV(DIV(_class="tooltip",
        _title=T("Discharges/24hrs") + "|" + T("Number of discharged patients during the past 24 hours.")))

    table.deaths24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.deaths24.default = 0
    table.deaths24.label = T("Deaths/24hrs")
    table.deaths24.comment = DIV(DIV(_class="tooltip",
        _title=T("Deaths/24hrs") + "|" + T("Number of deaths during the past 24 hours.")))

    def hms_activity_onaccept(form):

        table = db.hms_activity
        query = ((table.id == form.vars.id) & (db.hms_hospital.id == table.hospital_id))
        hospital = db(query).select(db.hms_hospital.id,
                                    db.hms_hospital.modified_on,
                                    limitby=(0, 1)).first()
        timestmp = form.vars.date
        if hospital and hospital.modified_on < timestmp:
            hospital.update_record(modified_on=timestmp)

    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(hms_hospital="hospital_id"))

    s3xrc.model.configure(table,
                          onaccept = lambda form: hms_activity_onaccept(form),
                          list_fields=["id",
                                       "date",
                                       "patients",
                                       "admissions24",
                                       "discharges24",
                                       "deaths24",
                                       "comment"],
                          main="hospital_id", extra="id")

    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Activity Report"),
        title_display = T("Activity Report"),
        title_list = T("Activity Reports"),
        title_update = T("Update Activity Report"),
        title_search = T("Search Activity Report"),
        subtitle_create = T("Add Activity Report"),
        subtitle_list = T("Activity Reports"),
        label_list_button = T("List Reports"),
        label_create_button = T("Add Report"),
        label_delete_button = T("Delete Report"),
        msg_record_created = T("Report added"),
        msg_record_modified = T("Report updated"),
        msg_record_deleted = T("Report deleted"),
        msg_list_empty = T("No reports currently available"))

    # -----------------------------------------------------------------------------
    # Bed Capacity
    #
    hms_bed_type_opts = {
        1: T("Adult ICU"),
        2: T("Pediatric ICU"),
        3: T("Neonatal ICU"),
        4: T("Emergency Department"),
        5: T("Nursery Beds"),
        6: T("General Medical/Surgical"),
        7: T("Rehabilitation/Long Term Care"),
        8: T("Burn ICU"),
        9: T("Pediatrics"),
        10: T("Adult Psychiatric"),
        11: T("Pediatric Psychiatric"),
        12: T("Negative Flow Isolation"),
        13: T("Other Isolation"),
        14: T("Operating Rooms"),
        15: T("Cholera Treatment"),
        99: T("Other")
    }

    resourcename = "bed_capacity"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            hospital_id(),
                            Field("unit_id", length=128, unique=True),
                            Field("bed_type", "integer",
                                requires = IS_IN_SET(hms_bed_type_opts, zero=None),
                                default = 6,
                                label = T("Bed Type"),
                                represent = lambda opt: hms_bed_type_opts.get(opt, UNKNOWN_OPT)),
                            Field("date", "datetime"),
                            Field("beds_baseline", "integer"),
                            Field("beds_available", "integer"),
                            Field("beds_add24", "integer"),
                            Field("comment", length=128),
                            migrate=migrate, *s3_meta_fields())


    table.unit_id.readable = False
    table.unit_id.writable = False

    table.bed_type.comment =  DIV(DIV(_class="tooltip",
        _title=T("Bed Type") + "|" + T("Specify the bed type of this unit.")))

    table.date.label = T("Date of Report")
    table.date.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(),
                                          allow_future=False)
    table.date.represent = lambda value: shn_as_local_time(value)

    table.beds_baseline.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.beds_baseline.default = 0
    table.beds_baseline.label = T("Baseline Number of Beds")
    table.beds_available.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.beds_available.default = 0
    table.beds_available.label = T("Available Beds")
    table.beds_add24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.beds_add24.default = 0
    table.beds_add24.label = T("Additional Beds / 24hrs")

    table.beds_baseline.comment = DIV(DIV(_class="tooltip",
        _title=T("Baseline Number of Beds") + "|" + T("Baseline number of beds of that type in this unit.")))
    table.beds_available.comment = DIV(DIV(_class="tooltip",
        _title=T("Available Beds") + "|" + T("Number of available/vacant beds of that type in this unit at the time of reporting.")))
    table.beds_add24.comment = DIV(DIV(_class="tooltip",
        _title=T("Additional Beds / 24hrs") + "|" + T("Number of additional beds of that type expected to become available in this unit within the next 24 hours.")))

    def hms_bed_capacity_onvalidation(form):

        """ Bed Capacity Validation """

        table = db.hms_bed_capacity
        hospital_id = table.hospital_id.update
        bed_type = form.vars.bed_type
        row = db((table.hospital_id == hospital_id) &
                 (table.bed_type == bed_type)).select(table.id,
                                                      limitby=(0, 1)).first()
        if row and str(row.id) != request.post_vars.id:
            form.errors["bed_type"] = T("Bed type already registered")
        elif "unit_id" not in form.vars:
            hospitals = db.hms_hospital
            hospital = db(hospitals.id == hospital_id).select(hospitals.uuid,
                                                              limitby=(0, 1)).first()
            if hospital:
                form.vars.unit_id = "%s-%s" % (hospital.uuid, bed_type)

    def hms_bed_capacity_onaccept(form):

        """ Updates the number of total/available beds of a hospital """

        if isinstance(form, Row):
            formvars = form
        else:
            formvars = form.vars

        table = db.hms_bed_capacity
        query = ((table.id == formvars.id) &
                 (db.hms_hospital.id == table.hospital_id))
        hospital = db(query).select(db.hms_hospital.id, limitby=(0, 1))

        if hospital:
            hospital = hospital.first()

            a_beds = table.beds_available.sum()
            t_beds = table.beds_baseline.sum()
            query = (table.hospital_id == hospital.id) & (table.deleted == False)
            count = db(query).select(a_beds, t_beds)
            if count:
               a_beds = count[0]._extra[a_beds]
               t_beds = count[0]._extra[t_beds]

            db(db.hms_hospital.id == hospital.id).update(
                total_beds=t_beds,
                available_beds=a_beds)

    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(hms_hospital="hospital_id"))

    s3xrc.model.configure(table,
                          onvalidation = lambda form: \
                                         hms_bed_capacity_onvalidation(form),
                          onaccept = lambda form: \
                                     hms_bed_capacity_onaccept(form),
                          ondelete = lambda row: \
                                     hms_bed_capacity_onaccept(row),
                          list_fields=["id",
                                       "unit_name",
                                       "bed_type",
                                       "date",
                                       "beds_baseline",
                                       "beds_available",
                                       "beds_add24"],
                          main="hospital_id", extra="id")

    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Bed Type"),
        title_display = T("Bed Capacity"),
        title_list = T("Bed Capacity"),
        title_update = T("Update Unit"),
        title_search = T("Search Units"),
        subtitle_create = T("Add Unit"),
        subtitle_list = T("Bed Capacity per Unit"),
        label_list_button = T("List Units"),
        label_create_button = T("Add Unit"),
        label_delete_button = T("Delete Unit"),
        msg_record_created = T("Unit added"),
        msg_record_modified = T("Unit updated"),
        msg_record_deleted = T("Unit deleted"),
        msg_list_empty = T("No units currently registered"))

    # -----------------------------------------------------------------------------
    # Services
    #
    resourcename = "services"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            hospital_id(),
                            Field("burn", "boolean", default=False),
                            Field("card", "boolean", default=False),
                            Field("dial", "boolean", default=False),
                            Field("emsd", "boolean", default=False),
                            Field("infd", "boolean", default=False),
                            Field("neon", "boolean", default=False),
                            Field("neur", "boolean", default=False),
                            Field("pedi", "boolean", default=False),
                            Field("surg", "boolean", default=False),
                            Field("labs", "boolean", default=False),
                            Field("tran", "boolean", default=False),
                            Field("tair", "boolean", default=False),
                            Field("trac", "boolean", default=False),
                            Field("psya", "boolean", default=False),
                            Field("psyp", "boolean", default=False),
                            Field("obgy", "boolean", default=False),
                            migrate=migrate, *s3_meta_fields())

    table.burn.label = T("Burn")
    table.card.label = T("Cardiology")
    table.dial.label = T("Dialysis")
    table.emsd.label = T("Emergency Department")
    table.infd.label = T("Infectious Diseases")
    table.neon.label = T("Neonatology")
    table.neur.label = T("Neurology")
    table.pedi.label = T("Pediatrics")
    table.surg.label = T("Surgery")
    table.labs.label = T("Clinical Laboratory")
    table.tran.label = T("Ambulance Service")
    table.tair.label = T("Air Transport Service")
    table.trac.label = T("Trauma Center")
    table.psya.label = T("Psychiatrics/Adult")
    table.psyp.label = T("Psychiatrics/Pediatric")
    table.obgy.label = T("Obstetrics/Gynecology")

    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Service Profile"),
        title_display = T("Services Available"),
        title_list = T("Services Available"),
        title_update = T("Update Service Profile"),
        title_search = T("Search Service Profiles"),
        subtitle_create = T("Add Service Profile"),
        subtitle_list = T("Services Available"),
        label_list_button = T("List Service Profiles"),
        label_create_button = T("Add Service Profile"),
        label_delete_button = T("Delete Service Profile"),
        msg_record_created = T("Service profile added"),
        msg_record_modified = T("Service profile updated"),
        msg_record_deleted = T("Service profile deleted"),
        msg_list_empty = T("No service profile available"))

    s3xrc.model.add_component(module, resourcename,
                              multiple=False,
                              joinby=dict(hms_hospital="hospital_id"))

    s3xrc.model.configure(table,
                          list_fields = ["id"],
                          main="hospital_id", extra="id")

    # -----------------------------------------------------------------------------
    # Cholera Treatment Capability
    #
    hms_problem_types = {
        1: T("Security problems"),
        2: T("Hygiene problems"),
        3: T("Sanitation problems"),
        4: T("Improper handling of dead bodies"),
        5: T("Improper decontamination"),
        6: T("Understaffed"),
        7: T("Lack of material"),
        8: T("Communication problems"),
        9: T("Information gaps")
    }
    resourcename = "ctc_capability"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            hospital_id(),
                            Field("ctc", "boolean", default=False),
                            Field("number_of_patients", "integer", default=0),
                            Field("cases_24", "integer", default=0),
                            Field("deaths_24", "integer", default=0),
                            #Field("staff_total", "integer", default=0),
                            Field("icaths_available", "integer", default=0),
                            Field("icaths_needed_24", "integer", default=0),
                            Field("infusions_available", "integer", default=0),
                            Field("infusions_needed_24", "integer", default=0),
                            #Field("infset_available", "integer", default=0),
                            #Field("infset_needed_24", "integer", default=0),
                            Field("antibiotics_available", "integer", default=0),
                            Field("antibiotics_needed_24", "integer", default=0),
                            Field("problem_types", "list:integer"),
                            Field("problem_details", "text"),
                            comments(),
                            migrate=migrate, *s3_meta_fields())

    table.modified_on.label = T("Last updated on")
    table.modified_on.readable = True

    table.modified_by.label = T("Last updated by")
    table.modified_by.readable = True

    table.ctc.label = T("Cholera-Treatment-Center")
    table.ctc.represent = lambda opt: opt and T("yes") or T("no")
    table.ctc.comment = DIV(DIV(_class="tooltip",
        _title=T("Cholera Treatment Center") + "|" + T("Does this facility provide a cholera treatment center?")))

    table.number_of_patients.label = T("Current number of patients")
    table.number_of_patients.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999))
    table.number_of_patients.comment = DIV(DIV(_class="tooltip",
        _title=T("Current number of patients") + "|" + T("How many patients with the disease are currently hospitalized at this facility?")))

    table.cases_24.label = T("New cases in the past 24h")
    table.cases_24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999))
    table.cases_24.comment = DIV(DIV(_class="tooltip",
        _title=T("New cases in the past 24h") + "|" + T("How many new cases have been admitted to this facility in the past 24h?")))

    table.deaths_24.label = T("Deaths in the past 24h")
    table.deaths_24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999))
    table.deaths_24.comment = DIV(DIV(_class="tooltip",
        _title=T("Deaths in the past 24h") + "|" + T("How many of the patients with the disease died in the past 24h at this facility?")))

    table.icaths_available.label = T("Infusion catheters available")
    table.icaths_available.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999))
    table.icaths_available.comment = DIV(DIV(_class="tooltip",
        _title=T("Infusion catheters available") + "|" + T("Specify the number of available sets")))

    table.icaths_needed_24.label = T("Infusion catheters needed per 24h")
    table.icaths_needed_24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999))
    table.icaths_needed_24.comment = DIV(DIV(_class="tooltip",
        _title=T("Infusion catheters need per 24h") + "|" + T("Specify the number of sets needed per 24h")))

    table.infusions_available.label = T("Infusions available")
    table.infusions_available.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999))
    table.infusions_available.comment = DIV(DIV(_class="tooltip",
        _title=T("Infusions available") + "|" + T("Specify the number of available units (litres) of Ringer-Lactate or equivalent solutions")))

    table.infusions_needed_24.label = T("Infusions needed per 24h")
    table.infusions_needed_24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999))
    table.infusions_needed_24.comment = DIV(DIV(_class="tooltip",
        _title=T("Infusions needed per 24h") + "|" + T("Specify the number of units (litres) of Ringer-Lactate or equivalent solutions needed per 24h")))

    table.antibiotics_available.label = T("Antibiotics available")
    table.antibiotics_available.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999))
    table.antibiotics_available.comment = DIV(DIV(_class="tooltip",
        _title=T("Antibiotics available") + "|" + T("Specify the number of available units (adult doses)")))

    table.antibiotics_needed_24.label = T("Antibiotics needed per 24h")
    table.antibiotics_needed_24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999))
    table.antibiotics_needed_24.comment = DIV(DIV(_class="tooltip",
        _title=T("Antibiotics needed per 24h") + "|" + T("Specify the number of units (adult doses) needed per 24h")))

    table.problem_types.label = T("Current problems, categories")
    table.problem_types.requires = IS_EMPTY_OR(IS_IN_SET(hms_problem_types, zero=None, multiple=True))
    table.problem_types.represent = lambda optlist: optlist and ", ".join(map(str,optlist)) or T("N/A")
    table.problem_types.comment = DIV(DIV(_class="tooltip",
        _title=T("Current problems, categories") + "|" + T("Select all that apply")))

    table.problem_details.label = T("Current problems, details")
    table.problem_details.comment = DIV(DIV(_class="tooltip",
        _title=T("Current problems, details") + "|" + T("Please specify any problems and obstacles with the proper handling of the disease, in detail (in numbers, where appropriate). You may also add suggestions the situation could be improved.")))

    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Cholera Treatment Capability Information"),
        title_display = T("Cholera Treatment Capability"),
        title_list = T("Cholera Treatment Capability"),
        title_update = T("Update Cholera Treatment Capability Information"),
        title_search = T("Search Status"),
        subtitle_create = T("Add Status"),
        subtitle_list = T("Current Status"),
        label_list_button = T("List Status"),
        label_create_button = T("Add Status"),
        label_delete_button = T("Delete Status"),
        msg_record_created = T("Status added"),
        msg_record_modified = T("Status updated"),
        msg_record_deleted = T("Status deleted"),
        msg_list_empty = T("No status information available"))

    s3xrc.model.add_component(module, resourcename,
                              multiple=False,
                              joinby=dict(hms_hospital="hospital_id"))

    s3xrc.model.configure(table,
        list_fields = ["id"],
        subheadings = {
            "Activities": "ctc",
            "Medical Supplies Availability": "icaths_available",
            "Current Problems": "problem_types",
            "Comments": "comments"})

    # -----------------------------------------------------------------------------
    # Images
    #
    hms_image_type_opts = {
        1:T("Photograph"),
        2:T("Map"),
        3:T("Document Scan"),
        99:T("other")
    }

    resourcename = "image"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            hospital_id(),
                            #Field("title"),
                            Field("type", "integer",
                                requires = IS_IN_SET(hms_image_type_opts, zero=None),
                                default = 1,
                                label = T("Image Type"),
                                represent = lambda opt: hms_image_type_opts.get(opt, T("not specified"))),
                            Field("image", "upload", autodelete=True),
                            Field("url"),
                            Field("description"),
                            Field("tags"),
                            migrate=migrate, *s3_meta_fields())


    # Field validation
    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)

    table.image.label = T("Image Upload")
    table.image.represent = lambda image: image and \
            DIV(A(IMG(_src=URL(r=request, c="default", f="download", args=image),_height=60, _alt=T("View Image")),
                _href=URL(r=request, c="default", f="download", args=image))) or \
            T("No Image")

    table.url.label = T("URL")
    table.url.represent = lambda url: url and DIV(A(IMG(_src=url, _height=60), _href=url)) or T("None")

    table.tags.label = T("Tags")
    table.tags.comment = DIV(DIV(_class="tooltip",
                            _title=T("Image Tags") + "|" + T("Enter tags separated by commas.")))

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Image"),
        title_display = T("Image Details"),
        title_list = T("List Images"),
        title_update = T("Edit Image Details"),
        title_search = T("Search Images"),
        subtitle_create = T("Add New Image"),
        subtitle_list = T("Images"),
        label_list_button = T("List Images"),
        label_create_button = T("Add Image"),
        label_delete_button = T("Delete Image"),
        msg_record_created = T("Image added"),
        msg_record_modified = T("Image updated"),
        msg_record_deleted = T("Image deleted"),
        msg_list_empty = T("No Images currently registered")
    )

    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(hms_hospital="hospital_id"))

    s3xrc.model.configure(table,
                          list_fields=["id",
                                       "type",
                                       "image",
                                       "url",
                                       "description",
                                       "tags"])

    # -----------------------------------------------------------------------------
    # Resources (multiple) - TODO: to be completed!
    #
    resourcename = "resources"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            hospital_id(),
                            Field("type"),
                            Field("description"),
                            Field("quantity"),
                            Field("comment"),   # ToDo: Change to comments()
                            migrate=migrate, *s3_meta_fields())


    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Report Resource"),
        title_display = T("Resource Details"),
        title_list = T("Resources"),
        title_update = T("Edit Resource"),
        title_search = T("Search Resources"),
        subtitle_create = T("Add New Resource"),
        subtitle_list = T("Resources"),
        label_list_button = T("List Resources"),
        label_create_button = T("Add Resource"),
        label_delete_button = T("Delete Resource"),
        msg_record_created = T("Resource added"),
        msg_record_modified = T("Resource updated"),
        msg_record_deleted = T("Resource deleted"),
        msg_list_empty = T("No resources currently reported"))

    # Add as component
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(hms_hospital="hospital_id"))

    s3xrc.model.configure(table,
                          list_fields=["id"],
                          main="hospital_id", extra="id")

    # -----------------------------------------------------------------------------
    # Hospital Search Method
    #
    hms_hospital_search = s3base.S3Find(
        #name="hospital_search_simple",
        #label=T("Name and/or ID"),
        #comment=T("To search for a hospital, enter any of the names or IDs of the hospital, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all hospitals."),
        #field=["gov_uuid", "name", "aka1", "aka2"],
        advanced=(s3base.S3SearchSimpleWidget(
                    name="hospital_search_advanced",
                    label=T("Name, Org and/or ID"),
                    comment=T("To search for a hospital, enter any of the names or IDs of the hospital, or the organisation name or acronym, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all hospitals."),
                    field=["gov_uuid", "name", "aka1", "aka2",
                        "organisation_id$name", "organisation_id$acronym"]
                  ),
                  # for testing:
                  #s3base.S3SearchMinMaxWidget(
                    #name="hospital_search_bedcount",
                    #method="range",
                    #label=T("Total Beds"),
                    #comment=T("Select a range for the number of total beds"),
                    #field=["total_beds"]
                  #)
        ))

    # Set as standard search method for hospitals
    s3xrc.model.configure(db.hms_hospital, search_method=hms_hospital_search)
