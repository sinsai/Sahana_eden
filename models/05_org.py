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
def shn_sector_represent(sector_ids):
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
                           represent = shn_sector_represent,
                           label = T("Sector"),
                           comment = DIV(A(ADD_SECTOR, _class="colorbox", _href=URL(r=request, c="org", f="sector", args="create", vars=dict(format="popup")), _target="top", _title=ADD_SECTOR), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Sector|The Sector(s) this organisation works in. Multiple values can be selected by holding down the 'Control' key."))),
                           ondelete = "RESTRICT"
                          ))

# -----------------------------------------------------------------------------
# Organizations
#
org_organisation_type_opts = {
    1:T("Government"),
    2:T("Embassy"),
    3:T("International NGO"),
    4:T("Donor"),               # Don't change this number without chaging organisation_popup.html
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
                pr_pe_fieldset,                         # Person Entity Field Set
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
                Field("twitter"),   # deprecated by pe_contact component
                Field("donation_phone"),
                shn_comments_field,
                source_id,
                migrate=migrate)

# Field settings
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
table.pr_pe_label.readable = False
table.pr_pe_label.writable = False
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.type.requires = IS_NULL_OR(IS_IN_SET(org_organisation_type_opts))
table.type.represent = lambda opt: org_organisation_type_opts.get(opt, UNKNOWN_OPT)
table.country.requires = IS_NULL_OR(IS_IN_SET(shn_list_of_nations))
table.country.represent = lambda opt: shn_list_of_nations.get(opt, UNKNOWN_OPT)
table.website.requires = IS_NULL_OR(IS_URL())
table.donation_phone.requires = shn_phone_requires

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
                      # Ensure that table is substituted when lambda defined not evaluated by using the default value
                      onaccept=lambda form, tab=table: shn_pentity_onaccept(form, table=tab, entity_type=5),
                      delete_onaccept=lambda form: shn_pentity_ondelete(form),
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
                pr_pe_fieldset,                         # Person Entity Field Set
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
table.pr_pe_label.readable = False
table.pr_pe_label.writable = False
#db[table].name.requires = IS_NOT_EMPTY()   # Office names don't have to be unique
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.type.requires = IS_NULL_OR(IS_IN_SET(org_office_type_opts))
table.type.represent = lambda opt: org_office_type_opts.get(opt, UNKNOWN_OPT)
table.parent.requires = IS_NULL_OR(IS_ONE_OF(db, "org_office.id", "%(name)s"))
table.parent.represent = lambda id: (id and [db(db.org_office.id == id).select(db.org_office.name, limitby=(0, 1)).first().name] or ["None"])[0]
table.phone1.requires = shn_phone_requires
table.phone2.requires = shn_phone_requires
table.fax.requires = shn_phone_requires
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
                      # Ensure that table is substituted when lambda defined not evaluated by using the default value
                      onaccept=lambda form, tab=table: shn_pentity_onaccept(form, table=tab, entity_type=6),
                      delete_onaccept=lambda form: shn_pentity_ondelete(form),
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

# Donors are a type of Organisation
def shn_donor_represent(donor_ids):
    if not donor_ids:
        return "None"
    elif "|" in str(donor_ids):
        donors = [db(db.org_donor.id == id).select(db.org_donor.name, limitby=(0, 1)).first().name for id in donor_ids.split("|") if id]
        return ", ".join(donors)
    else:
        return db(db.org_donor.id == donor_ids).select(db.org_donor.name, limitby=(0, 1)).first().name

ADD_DONOR = T("Add Donor")
donor_id = db.Table(None, "donor_id",
            FieldS3("donor_id", db.org_organisation, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id", "%(name)s", multiple=True, filterby="type", filter_opts=[4])),
                represent = shn_donor_represent,
                label = T("Donor"),
                comment = DIV(A(ADD_DONOR, _class="colorbox", _href=URL(r=request, c="org", f="organisation", args="create", vars=dict(format="popup", child="donor_id")), _target="top", _title=ADD_DONOR), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Donor|The Donor(s) for this project. Multiple values can be selected by holding down the 'Control' key."))),
                ondelete = "RESTRICT"
                ))

# -----------------------------------------------------------------------------
# Projects:
#   the projects which each organization is engaged in
#
org_project_status_opts = {
    1: T('active'),
    2: T('completed'),
    99: T('inactive')
    }
resource = "project"
tablename = module + "_" + resource
table = db.define_table(tablename, timestamp, deletion_status,
                Field("code"),
                Field("name"),
                organisation_id,
                location_id,
                sector_id,
                Field('status', 'integer',
                        requires = IS_IN_SET(org_project_status_opts, zero=None),
                        # default = 99,
                        label = T('Project Status'),
                        represent = lambda opt: org_project_status_opts.get(opt, UNKNOWN_OPT)),
                Field("description", "text"),
                Field("beneficiaries", "integer"),
                Field("start_date", "date"),
                Field("end_date", "date"),
                Field("funded", "boolean"),
                donor_id,
                Field("budgeted_cost", "double"),
                migrate=migrate)

# Field settings
table.code.requires = [IS_NOT_EMPTY(error_message=T("Please fill this!")),
                         IS_NOT_IN_DB(db, "org_project.code")]
table.start_date.requires = IS_NULL_OR(IS_DATE())
table.end_date.requires = IS_NULL_OR(IS_DATE())
table.budgeted_cost.requires = IS_NULL_OR(IS_FLOAT_IN_RANGE(0, 999999999))

# Project Resource called from multiple controllers
# - so we define strings in the model
table.code.label = T("Code")
table.code.comment = SPAN("*", _class="req")
table.name.label = T("Title")
table.start_date.label = T("Start date")
table.end_date.label = T("End date")
table.description.label = T("Description")
#table.description.comment = SPAN("*", _class="req")
table.status.label = T("Status")
table.status.comment = SPAN("*", _class="req")

ADD_PROJECT = T("Add Project")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_PROJECT,
    title_display = T("Project Details"),
    title_list = T("List Projects"),
    title_update = T("Edit Project"),
    title_search = T("Search Projects"),
    subtitle_create = T("Add New Project"),
    subtitle_list = T("Projects"),
    label_list_button = T("List Projects"),
    label_create_button = ADD_PROJECT,
    label_delete_button = T("Delete Project"),
    msg_record_created = T("Project added"),
    msg_record_modified = T("Project updated"),
    msg_record_deleted = T("Project deleted"),
    msg_list_empty = T("No Projects currently registered"))

# Reusable field
project_id = db.Table(None, "project_id",
                        FieldS3("project_id", db.org_project, sortby="name",
                        requires = IS_NULL_OR(IS_ONE_OF(db, "org_project.id", "%(code)s")),
                        represent = lambda id: (id and [db.org_project[id].code] or ["None"])[0],
                        comment = DIV(A(ADD_PROJECT, _class="colorbox", _href=URL(r=request, c="org", f="project", args="create", vars=dict(format="popup")), _target="top", _title=ADD_PROJECT), A(SPAN("[Help]"), _class="tooltip", _title=T("Project|Add new project)."))),
                        label = "Project",
                        ondelete = "RESTRICT"
                        ))

# Projects as component of Orgs
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby=dict(org_organisation="organisation_id"),
                          deletable=True,
                          editable=True)

s3xrc.model.configure(table,
                      list_fields=["id",
                                   "organisation_id",
                                   "location_id",
                                   "sector_id",
                                   "name",
                                   "status",
                                   "start_date",
                                   "end_date",
                                   "budgeted_cost"])

# org_position (component of org_project)
#   describes a position in a project
#
org_position_type_opts = {
    1: T("Site Manager"),
    2: T("Team Leader"),
    3: T("Assistant"),
    99: T("Other")
}

resource = "position"
tablename = module + "_" + resource
table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                project_id,
                Field("type", "integer",
                    requires = IS_IN_SET(org_position_type_opts, zero=None),
                    # default = 99,
                    label = T("Position type"),
                    represent = lambda opt: org_position_type_opts.get(opt, UNKNOWN_OPT)),
                Field("title", length=30),
                Field("description", "text"),
                Field("slots", "integer", default=1),
                Field("payrate", "double", default=0.0),
                #Field("status")?
                migrate=migrate)

# CRUD Strings
ADD_POSITION = T("Add Position")
POSITIONS = T("Positions")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_POSITION,
    title_display = T("Position Details"),
    title_list = POSITIONS,
    title_update = T("Edit Position"),
    title_search = T("Search Positions"),
    subtitle_create = T("Add New Position"),
    subtitle_list = POSITIONS,
    label_list_button = T("List Positions"),
    label_create_button = ADD_POSITION,
    msg_record_created = T("Position added"),
    msg_record_modified = T("Position updated"),
    msg_record_deleted = T("Position deleted"),
    msg_list_empty = T("No positions currently registered"))

# Reusable field
org_position_id = db.Table(None, "org_position_id",
                        FieldS3("org_position_id", db.org_position, sortby="title",
                        requires = IS_NULL_OR(IS_ONE_OF(db, "org_position.id", "%(title)s")),
                        represent = lambda id: lambda id: (id and [db.org_position[id].title] or ["None"])[0],
                        comment = DIV(A(ADD_POSITION, _class="colorbox", _href=URL(r=request, c="org", f="project", args="create", vars=dict(format="popup")), _target="top", _title=ADD_POSITION), A(SPAN("[Help]"), _class="tooltip", _title=T("Position|Add new position)."))),
                        ondelete = "RESTRICT"
                        ))

s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby=dict(org_project="project_id"),
                          deletable=True,
                          editable=True,
                          main="title", extra="description")

s3xrc.model.configure(table,
                      list_fields=["type",
                                   "title",
                                   "description",
                                   "slots",
                                   "payrate"])

# -----------------------------------------------------------------------------
# shn_project_search_location:
#   form function to search projects by location
#
def shn_project_search_location(xrequest, **attr):

    if attr is None:
        attr = {}

    if not shn_has_permission("read", db.org_project):
        session.error = UNAUTHORISED
        redirect(URL(r=request, c="default", f="user", args="login", vars={"_next":URL(r=request, args="search_location", vars=request.vars)}))

    if xrequest.representation == "html":
        # Check for redirection
        if request.vars._next:
            next = str.lower(request.vars._next)
        else:
            next = str.lower(URL(r=request, c="org", f="project", args="[id]"))

        # Custom view
        response.view = "%s/project_search.html" % xrequest.prefix

        # Title and subtitle
        title = T("Search for a Project")
        subtitle = T("Matching Records")

        # Select form:
        l_opts = [OPTION(_value="")]
        l_opts += [OPTION(location.name, _value=location.id)
                for location in db(db.gis_location.deleted == False).select(db.gis_location.ALL, cache=(cache.ram, 3600))]
        form = FORM(TABLE(
                TR(T("Location: "),
                SELECT(_name="location", *l_opts, **dict(name="location", requires=IS_NULL_OR(IS_IN_DB(db, "gis_location.id"))))),
                TR("", INPUT(_type="submit", _value="Search"))
                ))

        output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

        # Accept action
        items = None
        if form.accepts(request.vars, session):

            table = db.org_project
            query = (table.deleted == False)

            if form.vars.location is None:
                results = db(query).select(table.ALL)
            else:
                query = query & (table.location_id == form.vars.location)
                results = db(query).select(table.ALL)

            if results and len(results):
                records = []
                for result in results:
                    href = next.replace("%5bid%5d", "%s" % result.id)
                    records.append(TR(
                        A(result.name, _href=href),
                        result.start_date or "None",
                        result.end_date or "None",
                        result.description or "None",
                        result.status and org_project_status_opts[result.status] or "unknown",
                        ))
                items=DIV(TABLE(THEAD(TR(
                    TH("Name"),
                    TH("Start date"),
                    TH("End date"),
                    TH("Description"),
                    TH("Status"))),
                    TBODY(records), _id="list", _class="display"))
            else:
                    items = T("None")

        try:
            label_create_button = s3.crud_strings["org_project"].label_create_button
        except:
            label_create_button = s3.crud_strings.label_create_button

        add_btn = A(label_create_button, _href=URL(r=request, f="project", args="create"), _class="action-btn")

        output.update(dict(items=items, add_btn=add_btn))

        return output

    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

# Plug into REST controller
s3xrc.model.set_method(module, "project", method="search_location", action=shn_project_search_location )

# -----------------------------------------------------------------------------
def shn_project_rheader(jr, tabs=[]):

    if jr.representation == "html":
        
        rheader_tabs = shn_rheader_tabs(jr, tabs)
        
        if jr.name == "project":

            _next = jr.here()
            _same = jr.same()

            project = jr.record
            
            sectors = re.split("\|", project.sector_id)[1:-1]
            _sectors = TABLE()
            for sector in sectors:
                _sectors.append(TR(db(db.org_sector.id == sector).select(db.org_sector.name, limitby=(0, 1)).first().name))
                        
            if project:
                rheader = DIV(TABLE(
                    TR(
                        TH(T("Code: ")),
                        project.code,
                        TH(A(T("Clear Selection"),
                            _href=URL(r=request, f="project", args="clear", vars={"_next": _same})))
                        ),
                    TR(
                        TH(T("Name: ")),
                        project.name,
                        TH(T("Location: ")),
                        location_id.location_id.represent(project.location_id),
                        ),
                    TR(
                        TH(T("Status: ")),
                        "%s" % org_project_status_opts[project.status],
                        TH(T("Sector(s): ")),
                        _sectors
                        #TH(A(T("Edit Project"),
                        #    _href=URL(r=request, f="project", args=[jr.id, "update"], vars={"_next": _next})))
                        )
                ), rheader_tabs)
                return rheader

    return None

# -----------------------------------------------------------------------------
