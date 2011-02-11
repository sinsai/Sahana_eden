# -*- coding: utf-8 -*-

"""
    Organisation Registry
"""

module = "org"

# -----------------------------------------------------------------------------
# Site
#
# Site is a generic type for any facility (office, hospital, shelter,
# warehouse, etc.) and serves the same purpose as pentity does for person
# entity types:  It provides a common join key name across all types of
# sites, with a unique value for each sites.  This allows other types that
# are useful to any sort of site to have a common way to join to any of
# them.  It's especially useful for component types.
#
# This is currently being added so people can discuss it, and to get
# inventories quickly associated with shelters without adding shelter_id
# to inventory_store, or attempting to join on location_id.  It is in
# org because that's relatively generic and has one of the site types.
# You'll note that it is a slavish copy of pentity with the names changed.

org_site_types = Storage(
    cr_shelter = T("Shelter"),
    org_office = T("Office"),
    hms_hospital = T("Hospital"),
    inventory_store = T("Inventory Store"),
)

resource = "site"
tablename = "%s_%s" % (module, resource)
table = super_entity(tablename, "site_id", org_site_types, migrate=migrate)

# -----------------------------------------------------------------------------
def shn_site_represent(id, default_label="[no label]"):

    """ Represent a site in option fields or list views """

    site_str = T("None (no such record)")

    site_table = db.org_site
    site = db(site_table.site_id == id).select(site_table.instance_type,
                                               limitby=(0, 1)).first()
    if not site:
        return site_str

    instance_type = site.instance_type
    instance_type_nice = site_table.instance_type.represent(instance_type)

    table = db.get(instance_type, None)
    if not table:
        return site_str

    # All the current types of sites have a required "name" field that can
    # serve as their representation.
    record = db(table.site_id == id).select(table.name, limitby=(0, 1)).first()

    if record:
        site_str = "%s (%s)" % (record.name, instance_type_nice)
    else:
        # Since name is notnull for all types so far, this won't be reached.
        site_str = "[site %d] (%s)" % (id, instance_type_nice)

    return site_str


# -----------------------------------------------------------------------------
# Cluster
# @ToDo Allow easy changing between the term 'Cluster' (UN) & 'Sector' (everywhere else)
resourcename = "cluster"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        Field("abrv", length=64, notnull=True, unique=True),
                        Field("name", length=128, notnull=True, unique=True),
                        migrate=migrate, *s3_meta_fields()
                        )

# CRUD strings
ADD_CLUSTER = T("Add Sector")
LIST_CLUSTER = T("List Sector")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_CLUSTER,
    title_display = T("Sector Details"),
    title_list = LIST_CLUSTER,
    title_update = T("Edit Sector"),
    title_search = T("Search Sectors"),
    subtitle_create = T("Add New Sector"),
    subtitle_list = T("Sectors"),
    label_list_button = LIST_CLUSTER,
    label_create_button = ADD_CLUSTER,
    label_delete_button = T("Delete Sector"),
    msg_record_created = T("Sector added"),
    msg_record_modified = T("Sector updated"),
    msg_record_deleted = T("Sector deleted"),
    msg_list_empty = T("No Sectors currently registered"))

def shn_org_cluster_represent(id):
    return shn_get_db_field_value(db = db,
                                  table = "org_cluster",
                                  field = "abrv",
                                  look_up = id)

cluster_id = S3ReusableField("cluster_id", db.org_cluster, sortby="abrv",
                                   requires = IS_NULL_OR(IS_ONE_OF(db, "org_cluster.id","%(abrv)s", sort=True)),
                                   represent = shn_org_cluster_represent,
                                   label = T("Sector"),
                                   #comment = Script to filter the cluster_subsector drop down
                                   ondelete = "RESTRICT"
                                   )

# -----------------------------------------------------------------------------
# Cluster Subsector
resourcename = "cluster_subsector"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        cluster_id(),
                        Field("abrv", length=64, notnull=True, unique=True),
                        Field("name", length=128),
                        migrate=migrate, *s3_meta_fields()
                        )

# CRUD strings
ADD_CLUSTER_SUBSECTOR = T("Add Cluster Subsector")
LIST_CLUSTER_SUBSECTOR = T("List Cluster Subsectors")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_CLUSTER_SUBSECTOR,
    title_display = T("Cluster Subsector Details"),
    title_list = LIST_CLUSTER_SUBSECTOR,
    title_update = T("Edit Cluster Subsector"),
    title_search = T("Search Cluster Subsectors"),
    subtitle_create = T("Add New Cluster Subsector"),
    subtitle_list = T("Cluster Subsectors"),
    label_list_button = LIST_CLUSTER_SUBSECTOR,
    label_create_button = ADD_CLUSTER_SUBSECTOR,
    label_delete_button = T("Delete Cluster Subsector"),
    msg_record_created = T("Cluster Subsector added"),
    msg_record_modified = T("Cluster Subsector updated"),
    msg_record_deleted = T("Cluster Subsector deleted"),
    msg_list_empty = T("No Cluster Subsectors currently registered"))

def shn_org_cluster_subsector_represent(id):
    record = db(db.org_cluster_subsector.id == id).select(db.org_cluster_subsector.cluster_id,
                                                          db.org_cluster_subsector.abrv,
                                                          limitby=(0, 1)).first()
    return shn_org_cluster_subsector_requires_represent( record)

def shn_org_cluster_subsector_requires_represent(record):
    """ Used to generate text for the Select """
    if record:
        cluster_record = db(db.org_cluster.id == record.cluster_id).select(db.org_cluster.abrv,
                                                                           limitby=(0, 1)).first()
        if cluster_record:
            cluster = cluster_record.abrv
        else:
            cluster = NONE
        return "%s:%s" %(cluster,record.abrv)
    else:
        return NONE

cluster_subsector_id = S3ReusableField("cluster_subsector_id", db.org_cluster_subsector, sortby="abrv",
                                       requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                       "org_cluster_subsector.id",
                                                                       shn_org_cluster_subsector_requires_represent,
                                                                       sort=True)),
                                       represent = shn_org_cluster_subsector_represent,
                                       label = T("Cluster Subsector"),
                                       #comment = Script to filter the cluster_subsector drop down
                                       ondelete = "RESTRICT"
                                      )

# -----------------------------------------------------------------------------
# Organizations
#
org_organisation_type_opts = {
    1:T("Government"),
    2:T("Embassy"),
    3:T("International NGO"),
    4:T("Donor"),               # Don't change this number without changing organisation_popup.html
    6:T("National NGO"),
    7:"UN",
    8:T("International Organization"),
    9:T("Military"),
    10:T("Private"),
    11:T("Intergovernmental Organisation"),
    12:T("Institution"),
    #12:"MINUSTAH"   Haiti-specific
}

resourcename = "organisation"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        super_link(db.pr_pentity), # pe_id
                        #Field("privacy", "integer", default=0),
                        #Field("archived", "boolean", default=False),
                        Field("name", length=128, notnull=True, unique=True),
                        Field("acronym", length=8),
                        Field("type", "integer"),
                        cluster_id(),
                        #Field("registration", label=T("Registration")),    # Registration Number
                        Field("country", "string", length=2),
                        Field("website"),
                        Field("twitter"),   # deprecated by pe_contact component
                        Field("donation_phone"),
                        comments(),
                        #document_id(), # Not yet defined
                        migrate=migrate, *s3_meta_fields())

# Field settings
table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % tablename)]
table.type.requires = IS_NULL_OR(IS_IN_SET(org_organisation_type_opts))
table.type.represent = lambda opt: org_organisation_type_opts.get(opt, UNKNOWN_OPT)
table.country.requires = IS_NULL_OR(IS_IN_SET(s3_list_of_nations, sort=True))
table.country.represent = lambda opt: s3_list_of_nations.get(opt, UNKNOWN_OPT)
table.website.requires = IS_NULL_OR(IS_URL())
table.donation_phone.requires = shn_phone_requires
table.name.label = T("Name")
table.acronym.label = T("Acronym")
table.acronym.comment = DIV( _class = "tooltip", 
                             _title = T("Acronym") + "|" +
                                      T("Acronym of the organization's name, eg. IFRC.")
                            ) 
table.type.label = T("Type")
table.donation_phone.label = T("Donation Phone #")
table.donation_phone.comment = DIV( _class="tooltip", _title=T("Donation Phone #") + "|" + T("Phone number to donate to this organization's relief efforts."))
table.country.label = T("Home Country")
table.website.label = T("Website")
# Should be visible to the Dashboard
table.website.represent = shn_url_represent
table.twitter.label = T("Twitter")
table.twitter.comment = DIV( _class="tooltip", _title=T("Twitter") + "|" + T("Twitter ID or #hashtag"))
# CRUD strings
ADD_ORGANIZATION = T("Add Organization")
LIST_ORGANIZATIONS = T("List Organizations")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_ORGANIZATION,
    title_display = T("Organization Details"),
    title_list = LIST_ORGANIZATIONS,
    title_update = T("Edit Organization"),
    title_search = T("Search Organizations"),
    subtitle_create = T("Add New Organization"),
    subtitle_list = T("Organizations"),
    label_list_button = LIST_ORGANIZATIONS,
    label_create_button = ADD_ORGANIZATION,
    label_delete_button = T("Delete Organization"),
    msg_record_created = T("Organization added"),
    msg_record_modified = T("Organization updated"),
    msg_record_deleted = T("Organization deleted"),
    msg_list_empty = T("No Organizations currently registered"))

# Reusable field
def shn_organisation_represent(id):
    row = db(db.org_organisation.id == id).select(db.org_organisation.name,
                                                  db.org_organisation.acronym,
                                                  limitby = (0, 1)).first()
    if row:
        organisation_represent = row.name
        if row.acronym:
            organisation_represent = organisation_represent + " (" + row.acronym + ")"
    else:
        organisation_represent = "-"

    return organisation_represent

organisation_popup_url = URL(r=request, c="org", f="organisation", args="create", vars=dict(format="popup"))

shn_organisation_comment = DIV(A(ADD_ORGANIZATION,
                           _class="colorbox",
                           _href=organisation_popup_url,
                           _target="top",
                           _title=ADD_ORGANIZATION),
                         DIV(DIV(_class="tooltip",
                                 _title=ADD_ORGANIZATION + "|" + T("The Organization this record is associated with."))))

organisation_id = S3ReusableField("organisation_id", db.org_organisation, sortby="name",
                                  requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id",
                                                                  shn_organisation_represent,
                                                                  orderby="org_organisation.name",
                                                                  sort=True)
                                                        ),
                                  represent = shn_organisation_represent,
                                  label = T("Organization"),
                                  comment = shn_organisation_comment,
                                  ondelete = "RESTRICT",
                                  widget = S3AutocompleteWidget(request, module, resourcename)
                                 )

# Orgs as component of Clusters
# doesn't work - component join keys cannot be 1-to-many (=a component record can only belong to one primary record)
#s3xrc.model.add_component(module, resourcename,
                          #multiple=True,
                          #joinby=dict(org_sector="sector_id"))

s3xrc.model.configure(table,
                      #listadd=False,
                      super_entity=db.pr_pentity,
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
    1:T("Headquarters"),
    2:T("Regional"),
    3:T("Country"),
    4:T("Satellite Office")
}

resourcename = "office"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        super_link(db.pr_pentity), # pe_id
                        super_link(db.org_site), # site_id
                        Field("name", notnull=True),
                        organisation_id(),
                        Field("type", "integer"),
                        Field("parent", "reference org_office"),   # This form of hierarchy may not work on all Databases
                        location_id(),
                        Field("address", "text", label=T("Address"), writable=False), # Populated from location_id
                        Field("L4", label=deployment_settings.get_gis_locations_hierarchy("L4"), writable=False), # Populated from location_id
                        Field("L3", label=deployment_settings.get_gis_locations_hierarchy("L3"), writable=False), # Populated from location_id
                        Field("L2", label=deployment_settings.get_gis_locations_hierarchy("L2"), writable=False), # Populated from location_id
                        Field("L1", label=deployment_settings.get_gis_locations_hierarchy("L1"), writable=False), # Populated from location_id
                        Field("L0", label=deployment_settings.get_gis_locations_hierarchy("L0"), writable=False), # Populated from location_id
                        Field("postcode", label=T("Postcode"), writable=False), # Populated from location_id
                        Field("phone1"),
                        Field("phone2"),
                        Field("email"),
                        Field("fax"),
                        Field("national_staff", "integer"),
                        Field("international_staff", "integer"),
                        Field("number_of_vehicles", "integer"),
                        Field("vehicle_types"),
                        Field("equipment"),
                        #document_id,   # Not yet defined
                        comments(),
                        migrate=migrate, *s3_meta_fields())

# Field settings
table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
#db[table].name.requires = IS_NOT_EMPTY()   # Office names don't have to be unique
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % tablename)]
table.type.requires = IS_NULL_OR(IS_IN_SET(org_office_type_opts))
table.type.represent = lambda opt: org_office_type_opts.get(opt, UNKNOWN_OPT)
table.parent.requires = IS_NULL_OR(IS_ONE_OF(db, "org_office.id", "%(name)s"))
table.parent.represent = lambda id: (id and [db(db.org_office.id == id).select(db.org_office.name, limitby=(0, 1)).first().name] or [NONE])[0]
table.phone1.requires = shn_phone_requires
table.phone2.requires = shn_phone_requires
table.fax.requires = shn_phone_requires
table.email.requires = IS_NULL_OR(IS_EMAIL())
table.national_staff.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
table.international_staff.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
table.number_of_vehicles.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
table.name.label = T("Name")
table.parent.label = T("Parent Office")
table.type.label = T("Type")
table.phone1.label = T("Phone 1")
table.phone2.label = T("Phone 2")
table.email.label = T("Email")
table.fax.label = T("Fax")
table.national_staff.label = T("# of National Staff")
table.international_staff.label = T("# of International Staff")
table.number_of_vehicles.label = T("# of Vehicles")
table.vehicle_types.label = T("Vehicle Types")
table.equipment.label = T("Equipment")

# CRUD strings
ADD_OFFICE = T("Add Office")
LIST_OFFICES = T("List Offices")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_OFFICE,
    title_display = T("Office Details"),
    title_list = LIST_OFFICES,
    title_update = T("Edit Office"),
    title_search = T("Search Offices"),
    subtitle_create = T("Add New Office"),
    subtitle_list = T("Offices"),
    label_list_button = LIST_OFFICES,
    label_create_button = ADD_OFFICE,
    label_delete_button = T("Delete Office"),
    msg_record_created = T("Office added"),
    msg_record_modified = T("Office updated"),
    msg_record_deleted = T("Office deleted"),
    msg_list_empty = T("No Offices currently registered"))

# Reusable field for other tables to reference
office_id = S3ReusableField("office_id", db.org_office, sortby="default/indexname",
                requires = IS_NULL_OR(IS_ONE_OF(db, "org_office.id", "%(name)s")),
                represent = lambda id: (id and [db(db.org_office.id == id).select(db.org_office.name, limitby=(0, 1)).first().name] or [NONE])[0],
                label = T("Office"),
                comment = DIV(A(ADD_OFFICE, _class="colorbox", _href=URL(r=request, c="org", f="office", args="create", vars=dict(format="popup")), _target="top", _title=ADD_OFFICE),
                          DIV( _class="tooltip", _title=ADD_OFFICE + "|" + T("The Office this record is associated with."))),
                ondelete = "RESTRICT"
                )

# Offices as component of Orgs & Locations
s3xrc.model.add_component(module, resourcename,
                          multiple=True,
                          #joinby=dict(org_organisation="organisation_id", gis_location="location_id"),
                          joinby=dict(org_organisation="organisation_id"))

s3xrc.model.configure(table,
                      super_entity=(db.pr_pentity, db.org_site),
                      onvalidation=lambda form: address_onvalidation(form),
                      list_fields=[
                        "id",
                        "name",
                        "organisation_id",   # Filtered in Component views
                        #"L4",
                        "L3",
                        "L2",
                        "L1",
                        "L0",
                        "phone1",
                        "email"
                    ])

# Donors are a type of Organisation
def shn_donor_represent(donor_ids):
    if not donor_ids:
        return NONE
    elif "|" in str(donor_ids):
        donors = [db(db.org_organisation.id == id).select(db.org_organisation.name, limitby=(0, 1)).first().name for id in donor_ids.split("|") if id]
        return ", ".join(donors)
    else:
        return db(db.org_organisation.id == donor_ids).select(db.org_organisation.name, limitby=(0, 1)).first().name

ADD_DONOR = T("Add Donor")
donor_id = S3ReusableField("donor_id", db.org_organisation, sortby="name",
                    requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id", "%(name)s", multiple=True, filterby="type", filter_opts=[4])),
                    represent = shn_donor_represent,
                    label = T("Funding Organization"),
                    comment = DIV(A(ADD_DONOR, _class="colorbox", _href=URL(r=request, c="org", f="organisation", args="create", vars=dict(format="popup", child="donor_id")), _target="top", _title=ADD_DONOR),
                              DIV( _class="tooltip", _title=ADD_DONOR + "|" + T("The Donor(s) for this project. Multiple values can be selected by holding down the 'Control' key."))),
                    ondelete = "RESTRICT"
                   )

# -----------------------------------------------------------------------------
# Staff
# Many-to-Many Persons to Offices & Projects with also the Title & Manager that the person has in this context
# @ToDo: Build an Organigram out of this data
#
resourcename = "staff"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        Field("title"),
                        organisation_id(empty=False),
                        office_id(),
                        Field("manager_id", "reference org_staff", ondelete = "RESTRICT"),   # This form of hierarchy may not work on all Databases
                        Field("focal_point", "boolean"),
                        person_id(),
                        #project_id(),
                        #Field("slots", "integer", default=1),
                        #Field("payrate", "double", default=0.0), # Wait for Bugeting integration
                        comments(),
                        migrate=migrate, *s3_meta_fields())

def shn_org_staff_represent(staff_id):
    staff = db(db.org_staff.id == staff_id).select(db.org_staff.title,
                                                   db.org_office.name,
                                                   db.pr_person.first_name,
                                                   db.pr_person.middle_name,
                                                   db.pr_person.last_name,
                                                   left = [db.pr_person.on(db.pr_person.id == db.org_staff.person_id),
                                                           db.org_office.on(db.org_office.id == db.org_staff.office_id)]
                                                  ).first()
    if staff:
        title = staff.org_staff.title
        office = staff.org_office.name
        person = vita.fullname(staff.pr_person)
    else:
        return None

    if person:
        return "%s (%s)" % (title, person)
    elif office:
        return "%s (%s)" % (title, office)
    else:
        return title

# Field settings
table.title.requires = IS_NOT_EMPTY()
table.manager_id.requires = IS_NULL_OR(IS_ONE_OF(db, "org_staff.id", shn_org_staff_represent, orderby="org_staff.title"))
table.manager_id.represent = lambda id: (id and [shn_org_staff_represent(id)] or [NONE])[0]
table.person_id.comment = DIV( _class="tooltip", _title=T("Person") + "|" + T("The Person currently filling this Role."))

# Staff Resource called from multiple controllers
# - so we define strings in the model
table.title.label = T("Job Title")
table.title.comment = DIV( _class="tooltip", _title=T("Title") + "|" + T("The Title of this Role."))
table.manager_id.label = T("Manager")
table.manager_id.comment = DIV( _class="tooltip", _title=T("Manager") + "|" + T("The Role to which this Role reports."))
table.focal_point.comment = DIV( _class="tooltip", _title=T("Focal Point") + "|" + T("The contact person for this organization."))

# CRUD strings
ADD_STAFF = T("Add Staff")
LIST_STAFF = T("List Staff")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_STAFF,
    title_display = T("Staff Details"),
    title_list = LIST_STAFF,
    title_update = T("Edit Staff"),
    title_search = T("Search Staff"),
    subtitle_create = T("Add New Staff"),
    subtitle_list = T("Staff"),
    label_list_button = LIST_STAFF,
    label_create_button = ADD_STAFF,
    msg_record_created = T("Staff added"),
    msg_record_modified = T("Staff updated"),
    msg_record_deleted = T("Staff deleted"),
    msg_list_empty = T("No Staff currently registered"))

# Functions
def represent_focal_point(is_focal_point):
    if is_focal_point:
        return "Focal Point"
    else:
        return "-"

table.focal_point.represent = lambda focal_point: represent_focal_point(focal_point)

def shn_orgs_to_person(person_id):
    orgs = []
    if person_id:
        staff = db((db.org_staff.person_id == person_id) &
                      (db.org_staff.deleted == False)).select(db.org_staff.organisation_id)
        if staff:
            for s in staff:
                orgs.append(s.organisation_id)
    return orgs

# Reusable field
staff_id = S3ReusableField("staff_id", db.org_staff, sortby="name",
                        requires = IS_NULL_OR(IS_ONE_OF(db, "org_staff.id", shn_org_staff_represent, orderby="org_staff.id")),
                        represent = lambda id: shn_org_staff_represent(id),
                        comment = DIV(A(ADD_STAFF, _class="colorbox", _href=URL(r=request, c="org", f="staff", args="create", vars=dict(format="popup")), _target="top", _title=ADD_STAFF),
                                  DIV( _class="tooltip", _title=ADD_STAFF + "|" + T("Add new staff role."))),
                        label = T("Staff"),
                        ondelete = "RESTRICT"
                        )

# Staff as component of Orgs, Offices & Projects
s3xrc.model.add_component(module, resourcename,
                          multiple=True,
                          joinby=dict(org_organisation="organisation_id",
                                      org_office="office_id",
                                      #project_project="project_id"
                                      ))

# May wish to over-ride this in controllers
s3xrc.model.configure(table,
                      #listadd=False,
                      list_fields=["id",
                                   "person_id",
                                   "organisation_id",
                                   "office_id",
                                   "project_id",
                                   "title",
                                   "manager_id",
                                   "focal_point"
                                   #"description",
                                   #"slots",
                                   #"payrate"
                                   ])

org_menu = [
    [T("Organizations"), False, URL(r=request, c="org", f="organisation"),[
        [T("List"), False, URL(r=request, c="org", f="organisation")],
        [T("Add"), False, URL(r=request, c="org", f="organisation", args="create")],
        #[T("Search"), False, URL(r=request, f="organisation", args="search")]
    ]],
    [T("Offices"), False, URL(r=request, c="org", f="office"),[
        [T("List"), False, URL(r=request, c="org", f="office")],
        [T("Add"), False, URL(r=request,  c="org",f="office", args="create")],
        #[T("Search"), False, URL(r=request, f="office", args="search")]
    ]],
    [T("Staff"), False, URL(r=request,  c="org",f="staff"),[
        [T("List"), False, URL(r=request,  c="org",f="staff")],
        [T("Add"), False, URL(r=request,  c="org",f="staff", args="create")],
        #[T("Search"), False, URL(r=request, f="staff", args="search")]
    ]],
    #[T("Tasks"), False, URL(r=request,  c="org",f="task"),[
    #    [T("List"), False, URL(r=request,  c="org",f="task")],
    #    [T("Add"), False, URL(r=request,  c="org",f="task", args="create")],
        #[T("Search"), False, URL(r=request, f="task", args="search")]
    #]],
]
