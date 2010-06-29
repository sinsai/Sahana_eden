# -*- coding: utf-8 -*-

"""
    Organisation Registry
"""

module = "org"

# -----------------------------------------------------------------------------
# Settings
#
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("audit_read", "boolean"),
                Field("audit_write", "boolean"),
                migrate=migrate)

# -----------------------------------------------------------------------------
# Sectors (to be renamed as Clusters)
#
resource = "sector"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                Field("name", length=128, notnull=True, unique=True),
                migrate=migrate)

# Field settings
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]


# Functions
def sector_represent(sector_ids):
    if not sector_ids:
        return "None"
    elif "|" in str(sector_ids):
        sectors = [db(db.org_sector.id == id).select(db.org_sector.name, limitby=(0, 1)).first().name for id in sector_ids.split("|") if id]
        return ", ".join(sectors)
    else:
        return db(db.org_sector.id == sector_ids).select(db.org_sector.name, limitby=(0, 1)).first().name

# Reusable field
ADD_SECTOR = T("Add Sector")
sector_id = db.Table(None, "sector_id",
                     FieldS3("sector_id", sortby="name",
                           requires = IS_NULL_OR(IS_ONE_OF(db, "org_sector.id", "%(name)s", multiple=True)),
                           represent = sector_represent,
                           label = T("Sector"),
                           comment = DIV(A(ADD_SECTOR, _class="colorbox", _href=URL(r=request, c="org", f="sector", args="create", vars=dict(format="popup")), _target="top", _title=ADD_SECTOR), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Sector|The Sector(s) this organisation works in. Multiple values can be selected by holding down the 'Control' key"))),
                           ondelete = "RESTRICT"
                          ))

# -----------------------------------------------------------------------------
# Organizations
#
org_organisation_type_opts = {
    1:T("Government"),
    2:T("Embassy"),
    3:T("International NGO"),
    4:T("Donor"),
    6:T("National NGO"),
    7:T("UN"),
    8:T("International Organization"),
    9:T("Military"),
    10:T("Private")
    #12:T("MINUSTAH")   Haiti-specific
}

resource = "organisation"
tablename = module + "_" + resource
table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                #Field("privacy", "integer", default=0),
                #Field("archived", "boolean", default=False),
                Field("name", length=128, notnull=True, unique=True),
                Field("acronym", length=8),
                Field("type", "integer"),
                sector_id,
                admin_id,
                #Field("registration", label=T("Registration")),    # Registration Number
                Field("country", "integer"),
                Field("website"),
                Field("twitter"),
                Field("donation_phone"),
                shn_comments_field,
                source_id,
                migrate=migrate)

# Field settings
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.type.requires = IS_NULL_OR(IS_IN_SET(org_organisation_type_opts))
table.type.represent = lambda opt: org_organisation_type_opts.get(opt, UNKNOWN_OPT)
table.country.requires = IS_NULL_OR(IS_IN_SET(shn_list_of_nations))
table.country.represent = lambda opt: shn_list_of_nations.get(opt, UNKNOWN_OPT)
table.website.requires = IS_NULL_OR(IS_URL())

# Reusable field
ADD_ORGANIZATION = T("Add Organization")
organisation_popup_url = URL(r=request, c="org", f="organisation", args="create", vars=dict(format="popup"))
shn_organisation_comment = DIV(A(ADD_ORGANIZATION,
                           _class="colorbox",
                           _href=organisation_popup_url,
                           _target="top",
                           _title=ADD_ORGANIZATION),
                         DIV(DIV(_class="tooltip",
                                 _title=T("Add Organization|The Organization this record is associated with."))))
organisation_id = db.Table(None, "organisation_id",
                           FieldS3("organisation_id", db.org_organisation, sortby="name",
                           requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id", "%(name)s")),
                           represent = lambda id: (id and [db(db.org_organisation.id == id).select(db.org_organisation.name, limitby=(0, 1)).first().name] or ["None"])[0],
                           label = T("Organization"),
                           comment = shn_organisation_comment,
                           ondelete = "RESTRICT"
                          ))

# Orgs as component of Clusters
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby=dict(org_sector="sector_id"),
                          deletable=True,
                          editable=True)

s3xrc.model.configure(table,
                      list_fields = ["id",
                                     "name",
                                     "acronym",
                                     "type",
                                     "country",
                                     "website"])

# -----------------------------------------------------------------------------
# Offices
#
org_office_type_opts = {
    1:T("Satellite Office"),
    2:T("Country"),
    3:T("Regional"),
    4:T("Headquarters")
}

resource = "office"
tablename = module + "_" + resource
table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                Field("name", notnull=True),
                organisation_id,
                Field("type", "integer"),
                admin_id,
                location_id,
                Field("parent", "reference org_office"),   # This form of hierarchy may not work on all Databases
                Field("address", "text"),
                Field("postcode"),
                Field("phone1"),
                Field("phone2"),
                Field("email"),
                Field("fax"),
                Field("national_staff", "integer"),
                Field("international_staff", "integer"),
                Field("number_of_vehicles", "integer"),
                Field("vehicle_types"),
                Field("equipment"),
                source_id,
                shn_comments_field,
                migrate=migrate)

# Field settings
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
#db[table].name.requires = IS_NOT_EMPTY()   # Office names don't have to be unique
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.parent.requires = IS_NULL_OR(IS_ONE_OF(db, "org_office.id", "%(name)s"))
table.parent.represent = lambda id: (id and [db(db.org_office.id == id).select(db.org_office.name, limitby=(0, 1)).first().name] or ["None"])[0]
table.type.requires = IS_NULL_OR(IS_IN_SET(org_office_type_opts))
table.type.represent = lambda opt: org_office_type_opts.get(opt, UNKNOWN_OPT)
table.email.requires = IS_NULL_OR(IS_EMAIL())
table.national_staff.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
table.international_staff.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
table.number_of_vehicles.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))

# Reusable field for other tables to reference
ADD_OFFICE = T("Add Office")
office_id = db.Table(None, "office_id",
            FieldS3("office_id", db.org_office, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "org_office.id", "%(name)s")),
                represent = lambda id: (id and [db(db.org_office.id == id).select(db.org_office.name, limitby=(0, 1)).first().name] or ["None"])[0],
                label = T("Office"),
                comment = DIV(A(ADD_OFFICE, _class="colorbox", _href=URL(r=request, c="org", f="office", args="create", vars=dict(format="popup")), _target="top", _title=ADD_OFFICE), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Office|The Office this record is associated with."))),
                ondelete = "RESTRICT"
                ))

# Offices as component of Orgs
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby=dict(org_organisation="organisation_id"),
                          deletable=True,
                          editable=True)

s3xrc.model.configure(table,
                      list_fields=["id",
                                   "name",
                                   "organisation_id",   # Filtered in Component views
                                   "location_id",
                                   "phone1",
                                   "email"])

# -----------------------------------------------------------------------------
# Contacts
# Many-to-Many Persons to Offices with also the Title & Manager that the person has in this context
# ToDo: Build an Organigram out of this data?
#
resource = "contact"
tablename = module + "_" + resource
table = db.define_table(tablename, timestamp, deletion_status,
                person_id,
                organisation_id,
                office_id,
                Field("title"),
                Field("manager_id", db.pr_person),
                Field("focal_point", "boolean"),
                source_id,
                shn_comments_field,
                migrate=migrate)

# Field settings
# Over-ride the default IS_NULL_OR as Contact doesn't make sense without an associated Organisation
table.organisation_id.requires = IS_ONE_OF(db, "org_organisation.id", "%(name)s")
table.manager_id.requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id", shn_pr_person_represent))
table.manager_id.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]

# Functions
def represent_focal_point(is_focal_point):
    if is_focal_point:
        return "Focal Point"
    else:
        return "-"

def shn_org_contact_represent(contact_id):
    person = db((db.org_contact.id == contact_id) &
                (db.pr_person.id == db.org_contact.person_id)).select(db.pr_person.ALL)
    if person:
        return vita.fullname(person[0])
    else:
        return None

table.focal_point.represent = lambda focal_point: represent_focal_point(focal_point)

def shn_orgs_to_person(person_id):
    orgs = []
    if person_id:
        contacts = db((db.org_contact.person_id == person_id) &
                      (db.org_contact.deleted == False)).select(db.org_contact.organisation_id)
        if contacts:
            for c in contacts:
                orgs.append(c.organisation_id)
    return orgs

# Contacts as component of Orgs
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby=dict(org_organisation="organisation_id"),
                          deletable=True,
                          editable=True)

s3xrc.model.configure(table,
                      list_fields=["id",
                                   "person_id",
                                   "office_id",
                                   "title",
                                   "manager_id",
                                   "focal_point"])

# -----------------------------------------------------------------------------
# Projects:
#   the projects which each organization is engaged in
#
resource = "project"
tablename = module + "_" + resource
table = db.define_table(tablename, timestamp, deletion_status,
                organisation_id,
                location_id,
                sector_id,
                Field("title"),
                Field("description"),
                Field("beneficiaries", "integer"),
                Field("start_date", "date"),
                Field("end_date", "date"),
                Field("funded", "boolean"),
                Field("budgeted_cost", "double"),
                migrate=migrate)

# Field settings
table.budgeted_cost.requires = IS_NULL_OR(IS_FLOAT_IN_RANGE(0, 999999999))

# -----------------------------------------------------------------------------
