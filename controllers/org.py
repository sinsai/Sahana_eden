# -*- coding: utf-8 -*-

"""
    Organisation Registry - Controllers

    @author: Fran Boon
    @author: Michael Howden
"""

module = "org"

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

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def sector():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, "sector", listadd=False)

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def organisation():
    "RESTlike CRUD controller"
    # ServerSidePagination
    response.s3.pagination = True
    def organisation_prep(jr):
        if jr.representation == "html":
            crud.settings.create_next = URL(r=request, f="dashboard")
        return True
    response.s3.prep = organisation_prep
    output = shn_rest_controller(module, "organisation", listadd=False)
    return output

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def office():
    "RESTlike CRUD controller"
    resource = "office"
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    if isinstance(request.vars.organisation_id, list):
        request.vars.organisation_id = request.vars.organisation_id[0]
    if session.s3.security_policy == 1:
        # Hide the Admin row for simple security_policy
        table.admin.readable = table.admin.writable = False
    # ServerSidePagination
    response.s3.pagination = True

    # the update forms are not ready. when they will - uncomment this and comment the next one
    #if request.args(0) in ("create", "update"):
    if request.args(0) == "create":
        table.organisation_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "org_organisation.id"))
        if request.vars.organisation_id:
            session.s3.organisation_id = request.vars.organisation_id
            # Organisation name should be displayed on the form if organisation_id is pre-selected
            session.s3.organisation_name = db(db.org_organisation.id == int(session.s3.organisation_id)).select(db.org_organisation.name).first().name
    return shn_rest_controller(module, resource, listadd=False, rheader=shn_office_rheader)

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def contact():
    "RESTlike CRUD controller"
    resource = "contact"
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

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

    return shn_rest_controller(module, resource, listadd=False)


@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def project():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, "project", listadd=False)

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

    # Get Organization to display from Var or Arg or Default
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
        query  = (table.id > 0) & ((table.deleted == False) | (table.deleted == None))
        org_id = s3xrc.get_session(session, "org", "organisation") or 0
        if org_id:
            query = (table.id == org_id) & query
        try:
            org_name = db(query).select(limitby=(0, 1)).first().name
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

