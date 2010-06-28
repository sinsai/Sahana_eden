# -*- coding: utf-8 -*-

"""
    Organisation Registry - Controllers

    @author: Fran Boon
    @author: Michael Howden
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions" Views)
response.menu_options = [
    [T("Dashboard"), False, URL(r=request, f="dashboard")],
    [T("Organizations"), False, URL(r=request, f="organisation"),[
        [T("List"), False, URL(r=request, f="organisation")],
        [T("Add"), False, URL(r=request, f="organisation", args="create")],
        #[T("Search"), False, URL(r=request, f="organisation", args="search")]
    ]],
    [T("Offices"), False, URL(r=request, f="office"),[
        [T("List"), False, URL(r=request, f="office")],
        [T("Add"), False, URL(r=request, f="office", args="create")],
        #[T("Search"), False, URL(r=request, f="office", args="search")]
    ]],
    [T("Contacts"), False, URL(r=request, f="contact"),[
        [T("List"), False, URL(r=request, f="contact")],
        [T("Add"), False, URL(r=request, f="contact", args="create")],
        #[T("Search"), False, URL(r=request, f="contact", args="search")]
    ]],
    [T("Projects"), False, URL(r=request, f="project"),[
        [T("List"), False, URL(r=request, f="project")],
        [T("Add"), False, URL(r=request, f="project", args="create")],
        #[T("Search"), False, URL(r=request, f="project", args="search")]
    ]]
]

# S3 framework functions
def index():
    "Module's Home Page"

    module_name = deployment_settings.modules[module].name_nice

    return dict(module_name=module_name)

def sector():
    "RESTlike CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    table.name.label = T("Name")
    table.name.comment = SPAN("*", _class="req")

    # CRUD strings
    LIST_SECTORS = T("List Sectors")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SECTOR,
        title_display = T("Sector Details"),
        title_list = LIST_SECTORS,
        title_update = T("Edit Sector"),
        title_search = T("Search Sectors"),
        subtitle_create = T("Add New Sector"),
        subtitle_list = T("Sectors"),
        label_list_button = LIST_SECTORS,
        label_create_button = ADD_SECTOR,
        msg_record_created = T("Sector added"),
        msg_record_modified = T("Sector updated"),
        msg_record_deleted = T("Sector deleted"),
        msg_list_empty = T("No Sectors currently registered"))
    
    return shn_rest_controller(module, resource, listadd=False)

def organisation():
    "RESTlike CRUD controller"

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
   
    table.name.label = T("Name")
    table.name.comment = SPAN("*", _class="req")
    table.acronym.label = T("Acronym")
    table.type.label = T("Type")
    table.donation_phone.label = T("Donation Phone #")
    table.donation_phone.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Donation Phone #|Phone number to donate to this organization's relief efforts."))
    table.country.label = T("Home Country")
    table.website.label = T("Website")
    table.twitter.label = T("Twitter")
    table.twitter.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Twitter|Twitter ID or #hashtag"))

    # CRUD strings
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

    def org_prep(jr):
        if jr.representation == "html":
            # Redirect to Dashboard after adding/editing an Organisation to add Offices/Contacts/Projects
            crud.settings.create_next = URL(r=request, f="dashboard")
            crud.settings.update_next = URL(r=request, f="dashboard")
        return True
    response.s3.prep = org_prep

    def org_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = org_postp
    
    # ServerSidePagination
    response.s3.pagination = True
    
    output = shn_rest_controller(module, resource, listadd=False)
    
    return output

def office():
    "RESTlike CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    table.name.label = T("Name")
    table.name.comment = SPAN("*", _class="req")
    table.parent.label = T("Parent")
    table.type.label = T("Type")
    table.address.label = T("Address")
    table.postcode.label = T("Postcode")
    table.phone1.label = T("Phone 1")
    table.phone2.label = T("Phone 2")
    table.email.label = T("Email")
    table.fax.label = T("FAX")
    table.national_staff.label = T("National Staff")
    table.international_staff.label = T("International Staff")
    table.number_of_vehicles.label = T("Number of Vehicles")
    table.vehicle_types.label = T("Vehicle Types")
    table.equipment.label = T("Equipment")

    # CRUD strings
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

    if isinstance(request.vars.organisation_id, list):
        request.vars.organisation_id = request.vars.organisation_id[0]
    if session.s3.security_policy == 1:
        # Hide the Admin row for simple security_policy
        table.admin.readable = table.admin.writable = False
    
    def org_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = org_postp
    
    # ServerSidePagination
    response.s3.pagination = True

    # the update forms are not ready. when they will - uncomment this and comment the next one
    #if request.args(0) in ("create", "update"):
    if request.args(0) == "create":
        table.organisation_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "org_organisation.id"))
        if request.vars.organisation_id and request.vars.organisation_id != "None":
            session.s3.organisation_id = request.vars.organisation_id
            # Organisation name should be displayed on the form if organisation_id is pre-selected
            session.s3.organisation_name = db(db.org_organisation.id == int(session.s3.organisation_id)).select(db.org_organisation.name).first().name
    
    output = shn_rest_controller(module, resource, listadd=False, rheader=shn_office_rheader)
    
    return output

def contact():
    "RESTlike CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    table.person_id.label = T("Contact")
    table.title.label = T("Job Title")
    table.title.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Title|The Role this person plays within this Office."))
    table.manager_id.label = T("Manager")
    table.manager_id.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Manager|The person's manager within this Office."))
    table.focal_point.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Focal Point|The contact person for this organization."))

    # CRUD strings
    ADD_CONTACT = T("Add Contact")
    LIST_CONTACTS = T("List Contacts")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_CONTACT,
        title_display = T("Contact Details"),
        title_list = LIST_CONTACTS,
        title_update = T("Edit Contact"),
        title_search = T("Search Contacts"),
        subtitle_create = T("Add New Contact"),
        subtitle_list = T("Contacts"),
        label_list_button = LIST_CONTACTS,
        label_create_button = ADD_CONTACT,
        msg_record_created = T("Contact added"),
        msg_record_modified = T("Contact updated"),
        msg_record_deleted = T("Contact deleted"),
        msg_list_empty = T("No Contacts currently registered"))

    def org_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = org_postp
    
    # ServerSidePagination
    response.s3.pagination = True

    # No point in downloading large dropdowns which we hide, so provide a smaller represent

    # the update forms are not ready. when they will - uncomment this and comment the next one
    #if request.args(0) in ("create", "update"):
    if request.args(0) == "create":
        # person_id mandatory for a contact!
        table.person_id.requires = IS_ONE_OF_EMPTY(db, "pr_person.id")
        table.organisation_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "org_organisation.id"))
        table.office_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "org_office.id"))

    output = shn_rest_controller(module, resource, listadd=False)
    
    return output

def project():
    "RESTlike CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    # CRUD strings
    ADD_PROJECT = T("Add Project")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_PROJECT,
        title_display = T("Project Details"),
        title_list = T("Projects Report"),
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
    
    def org_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = org_postp
    
    # ServerSidePagination
    response.s3.pagination = True

    output = shn_rest_controller(module, resource, listadd=False)
    
    return output

def office_table_linkto(field):
    return URL(r=request, f = "office",  args=[field, "read"],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})
def office_table_linkto_update(field):
    return URL(r=request, f = "office", args=[field, "update"],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})

def contact_table_linkto(field):
    return URL(r=request, f = "contact",  args=[field, "read"],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})
def contact_table_linkto_update(field):
    return URL(r=request, f = "contact", args=[field, "update"],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})

def project_table_linkto(field):
    return URL(r=request, f = "project",  args=[field, "read"],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})
def project_table_linkto_update(field):
    return URL(r=request, f = "project", args=[field, "update"],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})

def org_sub_list(tablename, org_id):
    fields = []
    headers = {}
    table = db[tablename]
    
    for field in table:
        if field.readable and field.name <> "organisation_id" and field.name <> "admin":
            headers[str(field)] = str(field.label)
            fields.append(field)

    table_linkto_update = dict( \
        org_office = office_table_linkto_update,
        org_contact =  contact_table_linkto_update,
        org_project = project_table_linkto_update,
    )

    table_linkto = dict( \
        org_office = office_table_linkto,
        org_contact = contact_table_linkto,
        org_project = project_table_linkto,
    )

    authorised = shn_has_permission("update", tablename)
    if authorised:
        linkto = table_linkto_update[tablename]
    else:
        linkto = table_linkto[tablenname]

    query = (table.organisation_id == org_id)

    list =  crud.select(table, query = table.organisation_id == org_id, fields = fields, headers = headers, linkto = linkto, truncate=48, _id = tablename + "_list", _class="display")

    # Required so that there is a table with an ID for the refresh after add
    if list == None:
        list = TABLE("None", _id = tablename + "_list")

    return list

def dashboard():

    # Get Organization to display from Arg, Var, Session or Default
    if len(request.args) > 0:
        org_id = int(request.args[0])
        try:
            org_name = db(db.org_organisation.id == org_id).select(db.org_organisation.name, limitby=(0, 1)).first().name
        except:
            session.error = T("Invalid Organisation ID!")
            redirect(URL(r=request, c="org", f="index"))
    elif "name" in request.vars:
        org_name = request.vars["name"]
        try:
            org_id = db(db.org_organisation.name == org_name).select(db.org_organisation.id, limitby=(0, 1)).first().id
        except:
            session.error = T("Invalid Organisation ID!")
            redirect(URL(r=request, c="org", f="index"))
    else:
        table = db.org_organisation
        deleted  = ((table.deleted == False) | (table.deleted == None))
        org_id = s3xrc.get_session(session, "org", "organisation") or 0
        if org_id:
            query = (table.id == org_id) & deleted
        else:
            query = (table.id > 0) & deleted
        try:
            org_name = db(query).select(table.name, limitby=(0, 1)).first().name
        except:
            session.warning = T("No Organisations registered!")
            redirect(URL(r=request, c="org", f="index"))

    o_opts = []
    first_option = True;
    # if we keep the dropdown - it will better be in alphabetic order
    # that way the user will find things easier
    for organisation in db(db.org_organisation.deleted == False).select(db.org_organisation.ALL, orderby = db.org_organisation.name):
        if (org_id == 0 and first_option) or organisation.id == org_id:
            first_option = False
            if org_id == 0:
                org_id = organisation.id
            o_opts += [OPTION(organisation.name, _value=organisation.id, _selected="")]
        else:
            o_opts += [OPTION(organisation.name, _value=organisation.id)]

    organisation_select = SELECT(_name="org", *o_opts, **dict(name="org", requires=IS_NULL_OR(IS_IN_DB(db, "org_organisation.id")), _id = "organisation_select"))

    org_details = crud.read("org_organisation", org_id)

    office_list = org_sub_list("org_office", org_id)
    contact_list = org_sub_list("org_contact", org_id)
    project_list = org_sub_list("org_project", org_id)

    but_add_org = A(T("Add Organization"),
                        _class="colorbox",
                        _href=URL(r=request,
                            c="org", f="organisation", args="create",
                            vars=dict(format="popup", KeepThis="true")) + "&TB_iframe=true&mode=new",
                            _target="top", _title=T("Add Organization"))

    but_edit_org = A(T("Edit Organization"),
                        _href=URL(r=request,
                            c="org", f="organisation", args=[org_id, "update"]))

    but_add_office = A(T("Add Office"),
                        _class="colorbox",
                        _href=URL(r=request,
                            c="org", f="office", args="create",
                            vars=dict(format="popup", KeepThis="true")) + "&TB_iframe=true&mode=new",
                            _target="top", _title=T("Add Office"))

    but_add_contact = A(T("Add Contact"),
                        _class="colorbox",
                        _href=URL(r=request,
                            c="org", f="contact", args="create",
                            vars=dict(format="popup", KeepThis="true")) + "&TB_iframe=true&mode=new",
                            _target="top", _title=T("Add Contact"))

    but_add_project = A(T("Add Project"),
                        _class="colorbox",
                        _href=URL(r=request,
                            c="org", f="project", args="create",
                            vars=dict(format="popup", KeepThis="true")) + "&TB_iframe=true&mode=new",
                            _target="top", _title=T("Add Project"))

    session.s3.organisation_id = org_id

    return dict(organisation_id = org_id, organisation_select = organisation_select, org_details = org_details, office_list = office_list, contact_list = contact_list, project_list = project_list, but_add_org =but_add_org, but_edit_org =but_edit_org, but_add_office = but_add_office, but_add_contact = but_add_contact, but_add_project = but_add_project)

def who_what_where_when():
    project_list = crud.select("org_project", query = db.org_project.id > 0)
    #print project_list
    return dict(project_list = project_list)

def shn_office_rheader(jr):

    if jr.name == "office":
        if jr.representation == "html":

            _next = jr.here()
            _same = jr.same()

            office = jr.record
            organisation = db(db.org_organisation.id == office.organisation_id).select(db.org_organisation.name, limitby=(0, 1)).first()

            rheader = TABLE(
                TR(
                    TH(T("Name: ")),
                    office.name,
                    TH(T("Type: ")),
                    office.type,
                TR(
                    TH(T("Organisation: ")),
                    organisation.name
                    ),
                    TH(T("Sector: ")),
                    db(db.org_sector.id == organisation.sector_id).select(db.org_sector.name, limitby=(0, 1)).first().name
                    ),
                TR(
                    TH(A(T("Edit Office"),
                        _href=URL(r=request, c="org", f="office", args=[jr.id, "update"], vars={"_next": _next})))
                    )
            )
            return rheader

    return None

