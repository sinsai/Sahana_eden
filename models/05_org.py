# -*- coding: utf-8 -*-

"""
    Organisation Registry
"""
#==============================================================================
module = "org"

#==============================================================================
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

#==============================================================================
# Cluster
# @ToDo: Allow easy changing between the term 'Cluster' (UN) & 'Sector' (everywhere else)
# Use Organisation groups?
resourcename = "cluster"
tablename = "org_cluster"
table = db.define_table(tablename,
                        Field("abrv", length=64, notnull=True, unique=True,
                              label=T("Abbreviation")),
                        Field("name", length=128, notnull=True, unique=True,
                              label=T("Name")),
                        migrate=migrate, *s3_meta_fields()
                        )

# CRUD strings
ADD_CLUSTER = T("Add Sector")
LIST_CLUSTERS = T("List Sectors")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_CLUSTER,
    title_display = T("Sector Details"),
    title_list = LIST_CLUSTERS,
    title_update = T("Edit Sector"),
    title_search = T("Search Sectors"),
    subtitle_create = T("Add New Sector"),
    subtitle_list = T("Sectors"),
    label_list_button = LIST_CLUSTERS,
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

#==============================================================================
# Cluster Subsector
resourcename = "cluster_subsector"
tablename = "org_cluster_subsector"
table = db.define_table(tablename,
                        cluster_id(),
                        Field("abrv", length=64, notnull=True, unique=True,
                              label=T("Abbreviation")),
                        Field("name", length=128, label=T("Name")),
                        migrate=migrate, *s3_meta_fields()
                        )

# CRUD strings
ADD_CLUSTER_SUBSECTOR = T("Add Cluster Subsector")
LIST_CLUSTER_SUBSECTORS = T("List Cluster Subsectors")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_CLUSTER_SUBSECTOR,
    title_display = T("Cluster Subsector Details"),
    title_list = LIST_CLUSTER_SUBSECTORS,
    title_update = T("Edit Cluster Subsector"),
    title_search = T("Search Cluster Subsectors"),
    subtitle_create = T("Add New Cluster Subsector"),
    subtitle_list = T("Cluster Subsectors"),
    label_list_button = LIST_CLUSTER_SUBSECTORS,
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

#==============================================================================
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
    11:T("Intergovernmental Organization"),
    12:T("Institution"),
    #12:"MINUSTAH"   Haiti-specific
}

resourcename = "organisation"
tablename = "org_organisation"
table = db.define_table(tablename,
                        super_link(db.pr_pentity), # pe_id
                        #Field("privacy", "integer", default=0),
                        #Field("archived", "boolean", default=False),
                        Field("name", length=128, notnull=True, unique=True,
                              label = T("Name")),
                        Field("acronym", length=8, label = T("Acronym")),
                        Field("type", "integer", label = T("Type")),
                        cluster_id(),
                        #Field("registration", label=T("Registration")),    # Registration Number
                        Field("country", "string", length=2,
                              label = T("Home Country"),
                              requires = IS_NULL_OR(IS_IN_SET(s3_list_of_nations,
                                                              sort=True)),
                              represent = lambda opt: s3_list_of_nations.get(opt,
                                                                             UNKNOWN_OPT)),
                        Field("website", label = T("Website"),
                              requires = IS_NULL_OR(IS_URL()),
                              represent = shn_url_represent),
                        Field("twitter"),   # deprecated by contact component
                        Field("donation_phone", label = T("Donation Phone #"),
                              requires = shn_phone_requires),
                        comments(),
                        #document_id(), # Not yet defined
                        migrate=migrate, *s3_meta_fields())

# Field settings
table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % tablename)]
table.type.requires = IS_NULL_OR(IS_IN_SET(org_organisation_type_opts))
table.type.represent = lambda opt: org_organisation_type_opts.get(opt, UNKNOWN_OPT)
table.acronym.comment = DIV( _class="tooltip",
                             _title="%s|%s" % (T("Acronym"),
                                               T("Acronym of the organization's name, eg. IFRC.")))
table.donation_phone.comment = DIV( _class="tooltip",
                                    _title="%s|%s" % (T("Donation Phone #"),
                                                      T("Phone number to donate to this organization's relief efforts.")))
table.twitter.comment = DIV( _class="tooltip",
                             _title="%s|%s" % (T("Twitter"),
                                               T("Twitter ID or #hashtag")))
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
            organisation_represent = "%s (%s)" % (organisation_represent,
                                                  row.acronym)
    else:
        organisation_represent = "-"

    return organisation_represent

organisation_popup_url = URL(r=request, c="org", f="organisation",
                             args="create",
                             vars=dict(format="popup"))

organisation_comment = DIV(A(ADD_ORGANIZATION,
                           _class="colorbox",
                           _href=organisation_popup_url,
                           _target="top",
                           _title=ADD_ORGANIZATION),
                         DIV(DIV(_class="tooltip",
                                 _title="%s|%s" % (ADD_ORGANIZATION,
                                                   T("Enter some characters to bring up a list of possible matches.")))))
                                                   # Replace with this one if using dropdowns & not autocompletes
                                                   #T("If you don't see the Organization in the list, you can add a new one by clicking link 'Add Organization'.")))))

organisation_id = S3ReusableField("organisation_id", db.org_organisation, sortby="name",
                                  requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id",
                                                                  shn_organisation_represent,
                                                                  orderby="org_organisation.name",
                                                                  sort=True)
                                                        ),
                                  represent = shn_organisation_represent,
                                  label = T("Organization"),
                                  comment = organisation_comment,
                                  ondelete = "RESTRICT",
                                  # Comment this to use a Dropdown & not an Autocomplete
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

# Donors are a type of Organisation
def shn_donor_represent(donor_ids):
    if not donor_ids:
        return NONE
    elif "|" in str(donor_ids):
        query = (db.org_organisation.id == id)
        donors = [db(query).select(db.org_organisation.name,
                                   limitby=(0, 1)).first().name for id in donor_ids.split("|") if id]
        return ", ".join(donors)
    else:
        query = (db.org_organisation.id == donor_ids)
        return db(query).select(db.org_organisation.name,
                                limitby=(0, 1)).first().name

ADD_DONOR = T("Add Donor")
ADD_DONOR_HELP = T("The Donor(s) for this project. Multiple values can be selected by holding down the 'Control' key.")
donor_id = S3ReusableField("donor_id", db.org_organisation, sortby="name",
                           requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id",
                                                           "%(name)s",
                                                           multiple=True,
                                                           filterby="type",
                                                           filter_opts=[4])),
                           represent = shn_donor_represent,
                           label = T("Funding Organization"),
                           comment = DIV(A(ADD_DONOR,
                                           _class="colorbox",
                                           _href=URL(r=request, c="org",
                                                     f="organisation",
                                                     args="create",
                                                     vars=dict(format="popup",
                                                               child="donor_id")),
                                           _target="top",
                                           _title=ADD_DONOR),
                                        DIV( _class="tooltip",
                                             _title="%s|%s" % (ADD_DONOR,
                                                               ADD_DONOR_HELP))),
                           ondelete = "RESTRICT"
                           )

#==============================================================================
def staff_roles_create_func(tablename):
    """
        If the setting is enabled, returns an onaccept function to create roles
        for a record which can have staff as a component join
    """
    if deployment_settings.get_aaa_has_staff_permissions():
        return lambda form, tablename = tablename: \
                   shn_create_record_roles(form, tablename)
    else:
        return None
# -----------------------------------------------------------------------------
def staff_roles_update_func(tablename):
    """
        If the setting is enabled, returns an onaccept function to rename roles
        for a record which can have staff as a component join
    """
    if deployment_settings.get_aaa_has_staff_permissions():
        return lambda form, tablename = tablename: \
                   shn_update_record_roles(form, tablename)
    else:
        return None
# -----------------------------------------------------------------------------
s3xrc.model.configure(table,
                      # Create roles for each organisation
                      create_onaccept = staff_roles_create_func(tablename),
                      # Rename roles if record name changes
                      update_onaccept = staff_roles_update_func(tablename))

#==============================================================================
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
#
# @ToDo: Move the staff_roles_onaccept here:
#   # Create roles for each sitee
#   create_onaccept = staff_roles_create_func(tablename),
#   # Rename roles if record name changes
#   update_onaccept = staff_roles_update_func(tablename),

org_site_types = auth.org_site_types

resource = "site"
tablename = "org_site"
table = super_entity(tablename,
                     "site_id",
                     org_site_types,
                     Field("name", label=T("Name")),
                     location_id(),
                     organisation_id(),
                     *s3_ownerstamp(),
                     migrate=migrate)

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
site_id = super_link( db.org_site, 
                      writable = True,
                      readable = True,
                      label = T("Site"),
                      represent = shn_site_represent
                      )

# -----------------------------------------------------------------------------
def shn_create_record_roles(form, tablename):
    """
        Function to be called at create_onaccept by a record which can have
        org_staff as components, eg. Organisations & Site instances (Offices,
        Hospitals and Shelters).

        Creates:
         - a staff role (acl = deployment_settings.get_aaa_staff_acl())
         - a supervisor role (acl = deployment_settings.get_aaa_supervisor_acl())

        Sets the record's owned_by_role = staff role

        The current user is given membership of both staff & supervisor roles
    """

    id = form.vars.id
    table = db[tablename]
    try:
        record = db(table.id == id).select(table.name,
                                           limitby=(0, 1)).first()
        recordname = record.name
    except:
        recordname = ""
    staff_acl = deployment_settings.get_aaa_staff_acl()
    supervisor_acl = deployment_settings.get_aaa_supervisor_acl()
    cf = tablename.split("_")
    c = cf[0]
    f = cf[1]

    url = "%s/%s" % (deployment_settings.get_base_public_url(),
                     URL(r = request,
                         c = c,
                         f = f,
                         args = [id]) )

    # Create the Staff Role for this resource
    staff_role_id = auth.s3_create_role( "%s_%s Staff of %s" % (tablename,
                                                                id,
                                                                recordname),
                                         "Staff Role for record id %s in table %s (%s)" % (id,
                                                                                           tablename,
                                                                                           url),
                                         dict(c=c, f=f,
                                              uacl=acl.NONE, oacl=staff_acl)
                                        )
    # Create the Supervisor Role for this resource
    supervisor_role_id = auth.s3_create_role( "%s_%s Supervisors of %s" % (tablename,
                                                                           id,
                                                                           recordname),
                                              "Supervisor Role for record id %s in table %s (%s)" % (id,
                                                                                                     tablename,
                                                                                                     url),
                                              dict(c=c, f=f,
                                                   uacl=acl.NONE,
                                                   oacl=supervisor_acl)
                                            )
    # Set the resource's owned_by_role to the staff role
    db(table.id == id).update(owned_by_role = staff_role_id)
    # Update owned_by_role in site super_entity
    s3xrc.model.update_super(table, {"id":id}) 


    # Add user to the staff & supervisor roles
    auth.add_membership(staff_role_id)
    auth.add_membership(supervisor_role_id)

    # Create a record in the staff table
    # Removed as they may well not be a staff of this Organisation/Site
    #person_id = auth.person_id()
    #if person_id:
    #    if tablename == "org_organisation":
    #        # This record is an organisation
    #        site_id = None
    #        organisation_id = id
    #    elif tablename in org_site_types:
    #        # This record is an instance of a site (office/hospital/shelter)
    #        record = table[id]
    #        site_id = record.site_id
    #        organisation_id = record.organisation_id
    #
    #    db.org_staff.insert(site_id = site_id,
    #                        person_id = person_id,
    #                        organisation_id = organisation_id,
    #                        supervisor = True,
    #                        owned_by_user = auth.user.id,
    #                        owned_by_role = staff_role_id,
    #                        )

def shn_update_record_roles(form, tablename):
    """
        Function to be called at update_onaccept by a record which can have
        org_staff as components, eg. Organisations & Site instances (Offices,
        Hospitals and Shelters).

        Ensures that the Role names are kept synced to Record names
    """

    try:
        name = form.vars.name
    except:
        # No Name field in the table
        return

    id = form.vars.id
    table = db[tablename]
    record = db(table.id == id).select(table.owned_by_role,
                                       limitby=(0, 1)).first()
    owned_by_role = record.owned_by_role

    table = db[auth.settings.table_group]
    staff_role_id = owned_by_role
    staff_role_name_old = table[staff_role_id].role
    prefix, throw = staff_role_name_old.split(" Staff of ", 1)
    staff_role_name = "%s Staff of %s" % (prefix,
                                          name)
    supervisor_role_name_old = staff_role_name_old.replace("Staff",
                                                           "Supervisors")
    supervisor_role_name = "%s Supervisors of %s" % (prefix,
                                                     name)
    # Rename the roles
    db(table.id == staff_role_id).update(role=staff_role_name)
    db(table.role == supervisor_role_name_old).update(role=supervisor_role_name)

# -----------------------------------------------------------------------------
def shn_component_copy_role(form,
                            component_name, resource_name, fk,  pk  = "id" ):
    """
        Generic onaccept function to copy a component's "owned_by_role"
        from the main resource's "owned_by_role"
        For example, allowing other components of a record which has staff as a
        component (org + site instances) to have the same permissions as the
        primary record.
        @ToDo: integrate this with s3xrc?
    """
    component_id = session.rcvars[component_name]
    fk_id = db[component_name][component_id][fk]

    if pk == "id":
        primary_record = db[resource_name][fk_id]
    else:
        query = (db[resource_name][pk] == fk_id)
        primary_record = db(query).select(db[resource_name].owned_by_role,
                                          limitby = (0, 1)).first()
    try:
        role_id = primary_record.owned_by_role
        db[component_name][component_id] = dict(owned_by_role = role_id)
    except:
        pass

# -----------------------------------------------------------------------------
def shn_component_copy_role_func(component_name, resource_name, fk, pk = "id"):
    """
        Wrapper function to check settings and return the function
        @ToDo: this could use a separate deployment_setting
    """
    if deployment_settings.get_aaa_has_staff_permissions():
        return lambda form, component_name = component_name, \
                      resource_name = resource_name, fk = fk, pk = pk: \
                    shn_component_copy_role(form,
                                            component_name, resource_name,
                                            fk, pk )
    else:
        return None

STAFF_HELP = T("If Staff have login accounts then they are given access to edit the details of the")

# -----------------------------------------------------------------------------
def shn_site_based_permissions( table,
                                error_msg = T("You do not have permission for any site to perform this action.")):
    """
        Sets the site_id validator limited to sites which the current user 
        has update permission for
        If there are no sites that the user has permission for, 
        prevents create & update & gives an warning if the user tries to 
    """
    q = auth.s3_accessible_query("update", db.org_site)
    rows = db(q).select(db.org_site.site_id)
    filter_opts = [row.site_id for row in rows]
    if filter_opts:
        table.site_id.requires = IS_ONE_OF(db, "org_site.site_id", 
                                           shn_site_represent,
                                           filterby = "site_id",
                                           filter_opts = filter_opts
                                           )
    else:
        if "update" in request.args or "create" in request.args:
            # Trying to create or update 
            # If they do no have permission to any sites
            session.error = T("%s Create a new site or ensure that you have permissions for an existing site.")\
                            % error_msg 
            redirect(URL(r = request,
                         c = "default",
                         f = "index"
                         )
                     )
        else:
            # Remove the list add button  
            s3xrc.model.configure(table, insertable = False)
#==============================================================================
# Offices
#
org_office_type_opts = {
    1:T("Headquarters"),
    2:T("Regional"),
    3:T("Country"),
    4:T("Satellite Office"),
    5:T("Warehouse"),       # Don't change this number, as it affects the Inv module
}

ADD_OFFICE = T("Add Office")
office_comment = DIV(A(ADD_OFFICE,
                       _class="colorbox",
                       _href=URL(r=request, c="org", f="office",
                                 args="create",
                                 vars=dict(format="popup")),
                       _target="top",
                       _title=ADD_OFFICE),
                     DIV( _class="tooltip",
                          _title="%s|%s" % (ADD_OFFICE,
                                            T("If you don't see the Office in the list, you can add a new one by clicking link 'Add Office'."))))

resourcename = "office"
tablename = "org_office"
table = db.define_table(tablename,
                        super_link(db.pr_pentity), # pe_id
                        super_link(db.org_site), # site_id
                        Field("name", notnull=True, label = T("Name")),
                        organisation_id(),
                        Field("type", "integer", label = T("Type")),
                        Field("office_id", "reference org_office", # This form of hierarchy may not work on all Databases
                              label = T("Parent Office"),
                              comment = office_comment),
                        location_id(),
                        Field("building_name", "text", label=T("Building Name"),
                              writable=False), # Populated from location_id
                        Field("address", "text", label=T("Address"),
                              writable=False), # Populated from location_id
                        Field("L4",
                              label=deployment_settings.get_gis_locations_hierarchy("L4"),
                              writable=False), # Populated from location_id
                        Field("L3",
                              label=deployment_settings.get_gis_locations_hierarchy("L3"),
                              writable=False), # Populated from location_id
                        Field("L2",
                              label=deployment_settings.get_gis_locations_hierarchy("L2"),
                              writable=False), # Populated from location_id
                        Field("L1",
                              label=deployment_settings.get_gis_locations_hierarchy("L1"),
                              writable=False), # Populated from location_id
                        Field("L0",
                              label=deployment_settings.get_gis_locations_hierarchy("L0"),
                              writable=False), # Populated from location_id
                        Field("postcode", label=T("Postcode"), writable=False), # Populated from location_id
                        Field("phone1", label = T("Phone 1"),
                              requires = shn_phone_requires),
                        Field("phone2", label = T("Phone 2"),
                              requires = shn_phone_requires),
                        Field("email", label = T("Email"),
                              requires = IS_NULL_OR(IS_EMAIL())),
                        Field("fax", label = T("Fax"),
                              requires = shn_phone_requires),
                        # @ToDo: Calculate automatically from org_staff (but still allow manual setting for a quickadd)
                        Field("international_staff", "integer",
                              label = T("# of National Staff"),
                              requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))),
                        Field("national_staff", "integer",
                              label = T("# of International Staff"),
                              requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))),
                        # @ToDo: Move to Fixed Assets
                        Field("number_of_vehicles", "integer",
                              label = T("# of Vehicles"),
                              requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))),
                        Field("vehicle_types", label = T("Vehicle Types")),
                        Field("equipment", label = T("Equipment")),
                        Field("obsolete",
                              "boolean",
                              label = T("Obsolete"),
                              represent = lambda bool: (bool and [T("Obsolete")] or [NONE])[0],
                              default = False
                              ),
                        #document_id,   # Not yet defined
                        comments(),
                        migrate=migrate, *s3_meta_fields())

# Field settings
table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
#db[table].name.requires = IS_NOT_EMPTY()   # Office names don't have to be unique
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % tablename)]
table.type.requires = IS_NULL_OR(IS_IN_SET(org_office_type_opts))
table.type.represent = lambda opt: org_office_type_opts.get(opt, UNKNOWN_OPT)
table.office_id.requires = IS_NULL_OR(IS_ONE_OF(db, "org_office.id", "%(name)s"))
table.office_id.represent = lambda id: (id and [db(db.org_office.id == id).select(db.org_office.name,
                                                                               limitby=(0, 1)).first().name] or [NONE])[0]

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
                represent = lambda id: (id and [db(db.org_office.id == id).select(db.org_office.name,
                                                                                  limitby=(0, 1)).first().name] or [NONE])[0],
                label = T("Office"),
                comment = office_comment,
                ondelete = "RESTRICT"
                )

# -----------------------------------------------------------------------------
# Offices as component of Orgs & Locations
s3xrc.model.add_component(module, resourcename,
                          multiple=True,
                          #joinby=dict(org_organisation="organisation_id", gis_location="location_id"),
                          joinby=dict(org_organisation="organisation_id"))

s3xrc.model.configure(table,
                      super_entity=(db.pr_pentity, db.org_site),
                      onvalidation=address_onvalidation,
                      # Create roles for each office
                      create_onaccept = staff_roles_create_func(tablename),
                      # Rename roles if record name changes
                      update_onaccept = staff_roles_update_func(tablename),
                      list_fields=[
                        "id",
                        "name",
                        "organisation_id",   # Filtered in Component views
                        "type",
                        #"L4",
                        "L3",
                        "L2",
                        "L1",
                        "L0",
                        "phone1",
                        "email"
                    ])

# -----------------------------------------------------------------------------
def shn_office_rheader(r, tabs=[]):

    """ Office/Warehouse page headers """

    if r.representation == "html":

        if r.record is None:
            # List or Create form: rheader makes no sense here
            return None

        tabs = [(T("Basic Details"), None),
                (T("Contact Data"), "contact"),
                (T("Staff"), "staff")
                ]
        
        if deployment_settings.has_module("req"):
            tabs.append((T("Requests"), "req"))
        if deployment_settings.has_module("inv"):
            tabs = tabs + shn_show_inv_tabs(r)

        rheader_tabs = shn_rheader_tabs(r, tabs)

        office = r.record
        if office:
            query = (db.org_organisation.id == office.organisation_id)
            organisation = db(query).select(db.org_organisation.name,
                                            limitby=(0, 1)).first()
            if organisation:
                org_name = organisation.name
            else:
                org_name = None

            rheader = DIV(TABLE(
                          TR(TH("%s: " % T("Name")),
                             office.name,
                             TH("%s: " % T("Type")),
                             org_office_type_opts.get(office.type,
                                                      UNKNOWN_OPT),
                             ),
                          TR(TH("%s: " % T("Organization")),
                             org_name,
                             TH("%s: " % T("Location")),
                             shn_gis_location_represent(office.location_id),
                             ),
                          #TR(TH(A(T("Edit Office"),
                          #        _href=URL(r=request, c="org", f="office",
                          #                  args=[r.id, "update"],
                          #                  vars={"_next": _next})))
                          #   )
                              ),
                          rheader_tabs)

            return rheader

    return None

#==============================================================================
# Staff
# Many-to-Many Persons to Offices & Projects with also the Title & Manager that
# the person has in this context
# @ToDo: Handle Shifts (e.g. Red Cross: 06:00-18:00 & 18:00-06:00)
# http://eden.sahanafoundation.org/wiki/BluePrintRoster
# @ToDo: Build an Organigram out of this data
#
resourcename = "staff"
tablename = "org_staff"

table = db.define_table(tablename,
                        super_link(db.org_site),    # site_id
                        person_id(label=T("Name"),
                                  comment = shn_person_comment(T("Person"),
                                                               T("The Person currently filling this Role."))),
                        Field("title", label = T("Job Title")),
                        organisation_id(),
                        # This form of hierarchy may not work on all DBs
                        Field("manager_id",
                              "reference org_staff",
                              label = T("Manager"),
                              ondelete = "RESTRICT"),
                        Field("supervisor", "boolean", label=T("Supervisor"),
                              represent = lambda bool: (bool and [T("Supervisor")] or [NONE])[0],
                              comment = DIV( _class="tooltip",
                                             _title="%s|%s" % (T("Supervisor"),
                                                               T("Has additional rights to modify records relating to this Organization or Site.")))),
                        Field("no_access", "boolean", label=T("Read-only"),
                              represent = lambda bool: (bool and [T("Read-only")] or [NONE])[0],
                              comment = DIV( _class="tooltip",
                                             _title="%s|%s" % (T("Read-Only"),
                                                               T("Has only read-only access to records relating to this Organization or Site.")))),
                        Field("focal_point", "boolean",
                              label = T("Focal Point"),
                              represent = lambda bool: (bool and [T("Focal Point")] or [NONE])[0],
                              comment = DIV( _class="tooltip",
                                             _title="%s|%s" % (T("Focal Point"),
                                                               T("The contact person for this organization.")))),
                        #project_id(),
                        #Field("slots", "integer", default=1),
                        # Wait for Bugeting integration
                        #Field("payrate", "double", default=0.0),
                        comments(),
                        migrate=migrate, *s3_meta_fields())

# @ToDo: person_id shouldn't be mandatory for a staff? We should allow room for vacant positions
table.person_id.requires = IS_ONE_OF( db, "pr_person.id",
                                      shn_pr_person_represent,
                                      orderby="pr_person.first_name",
                                      sort=True,
                                      error_message="Person must be specified!")

def shn_org_staff_represent(staff_id):
    staff = db(db.org_staff.id == staff_id).select(db.org_staff.title,
                                                   db.org_office.name,
                                                   db.pr_person.first_name,
                                                   db.pr_person.middle_name,
                                                   db.pr_person.last_name,
                                                   #@TODO: Fix this (use site_id not office_id)
                                                   #left = [db.pr_person.on(db.pr_person.id == db.org_staff.person_id),
                                                   #        db.org_office.on(db.org_office.id == db.org_staff.office_id)]
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

# Staff Resource called from multiple controllers
# - so we define strings in the model
table.manager_id.requires = IS_NULL_OR(IS_ONE_OF(db, "org_staff.id",
                                                 shn_org_staff_represent,
                                                 orderby="org_staff.title"))
table.manager_id.represent = lambda id: (id and [shn_org_staff_represent(id)] or [NONE])[0]
table.manager_id.comment = DIV( _class="tooltip",
                                _title="%s|%s" % (T("Manager"),
                                                  T("The Role to which this Role reports.")))

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
def shn_orgs_to_person(person_id):
    """
        Returns a list of organisations for which the person is staff
    """
    orgs = []
    if person_id:
        query = (db.org_staff.person_id == person_id) & \
                (db.org_staff.deleted == False)
        staff = db(query).select(db.org_staff.organisation_id)
        if staff:
            for s in staff:
                orgs.append(s.organisation_id)
    return orgs

# Reusable field
staff_id = S3ReusableField("staff_id", db.org_staff, sortby="name",
                           requires = IS_NULL_OR(IS_ONE_OF(db, "org_staff.id",
                                                           shn_org_staff_represent,
                                                           orderby="org_staff.id")),
                           represent = lambda id: shn_org_staff_represent(id),
                           comment = DIV(A(ADD_STAFF,
                                           _class="colorbox",
                                           _href=URL(r=request, c="org", f="staff",
                                                     args="create",
                                                     vars=dict(format="popup")),
                                           _target="top",
                                           _title=ADD_STAFF),
                                     DIV( _class="tooltip",
                                          _title="%s|%s" % (ADD_STAFF,
                                                            T("Add new staff role.")))),
                           label = T("Staff"),
                           ondelete = "RESTRICT"
                        )

# Staff as component of Orgs (& Projects)
s3xrc.model.add_component(module, resourcename,
                          multiple=True,
                          joinby=dict(org_organisation="organisation_id",
                                      #project_project="project_id"
                                      ))

# Staff as component of sites (inc Offices)
s3xrc.model.add_component(module, resourcename,
                          multiple=True,
                          joinby=super_key(db.org_site)
                          )

# -----------------------------------------------------------------------------
def shn_staff_onaccept(form):
    auth.s3_update_staff_membership(form)
    # Staff resources inherit permissions from sites not organisations,
    # because this is LESS permissive. This may need to be a deployment setting
    shn_component_copy_role_func(component_name = "org_staff",
                                 resource_name = "org_site",
                                 fk = "site_id",
                                 pk = "site_id")(form)

s3xrc.model.configure(table,
                      onaccept = shn_staff_onaccept,
                      ondelete = lambda form: auth.s3_update_staff_membership(form,
                                                                              delete=True)
                      )
# -----------------------------------------------------------------------------
def shn_staff_prep(r):
    # Filter out people which are already staff for this inventory
    # Make S3PersonAutocompleteWidget work with the filter criteria of the
    # field.requires
    # (this is required to ensure only unique staff can be added to each site)
    try:
        site_id = r.record.site_id
    except:
        site_id = None
    query = (db.org_staff.site_id == site_id) & \
            (db.org_staff.deleted == False)
    staff_rows = db(query).select(db.org_staff.person_id)
    person_ids = [r.person_id for r in staff_rows]
    db.org_staff.person_id.requires.set_filter(not_filterby = "id",
                                               not_filter_opts = person_ids)

#==============================================================================
# Domain table
# When users register their email address is checked against this list.
# If the Domain matches, then they are automatically assigned to the Organisation.
# If there is no Approvals email then the user is automatically approved.
# If there is an Approvals email then the approval request goes to this address
# If a user registers for an Organisation & the domain doesn't match (or isn't listed) then the approver gets the request
resourcename = "organisation"
tablename = "auth_organisation"

if deployment_settings.get_auth_registration_requests_organisation():
    ORG_HELP = T("If this field is populated then a user who specifies this Organization when signing up will be assigned as a Staff of this Organization unless their domain doesn't match the domain field.")
else:
    ORG_HELP = T("If this field is populated then a user with the Domain specified will automatically be assigned as a Staff of this Organization")

DOMAIN_HELP = T("If a user verifies that they own an Email Address with this domain, the Approver field is used to determine whether & by whom further approval is required.")
APPROVER_HELP = T("The Email Address to which approval requests are sent (normally this would be a Group mail rather than an individual). If the field is blank then requests are approved automatically if the domain matches.")
    
table = db.define_table(tablename,
                        organisation_id(comment=DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Organization"),
                                                                      ORG_HELP))),
                        Field("domain", label=T("Domain"),
                              comment=DIV(_class="tooltip",
                                          _title="%s|%s" % (T("Domain"),
                                                            DOMAIN_HELP))),
                        Field("approver", label=T("Approver"),
                              requires=IS_NULL_OR(IS_EMAIL()),
                              comment=DIV(_class="tooltip",
                                          _title="%s|%s" % (T("Approver"),
                                                            APPROVER_HELP))),
                        comments(),
                        migrate=migrate, *s3_meta_fields())

#==============================================================================
# Resource super-entity
#   - to link availability, deployment as common components

#org_resource_types = dict(
    #"hrm_human_resource": T("Human Resource")
#)

#resource = "resource"
#tablename = "org_resource"
#table = super_entity(tablename, "rsc_id", org_resource_types,
                     #organisation_id(), # mirrored field
                     #migrate=migrate)

#s3xrc.model.configure(table,
                      #editable=False,
                      #deletable=False,
                      #listadd=False)

# END -------------------------------------------------------------------------
