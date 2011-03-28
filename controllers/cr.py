# -*- coding: utf-8 -*-

"""
    Shelter Registry - Controllers
"""
# @ToDo Search shelters by type, services, location, available space
# @ToDo Tie in assessments from RAT and requests from RMS.
# @ToDo Associate persons with shelters (via presence loc == shelter loc?)

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
def shn_menu():
    menu = [
        [T("Shelters"), False, aURL(r=request, f="shelter"), [
            [T("List"), False, aURL(r=request, f="shelter")],
            [T("Add"), False, aURL(p="create", r=request, f="shelter", args="create")],
            # @ToDo Search by type, services, location, available space
            #[T("Search"), False, URL(r=request, f="shelter", args="search")],
        ]],
    ]
    if s3_has_role("Editor"):
        menu_editor = [
            [T("Shelter Types and Services"), False, URL(r=request, f="#"), [
                [T("List / Add Services"), False, URL(r=request, f="shelter_service")],
                [T("List / Add Types"), False, URL(r=request, f="shelter_type")],
            ]],
        ]
        menu.extend(menu_editor)
    response.menu_options = menu

shn_menu()

# S3 framework functions
# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def shelter_type():

    """
        RESTful CRUD controller
        List / add shelter types (e.g. NGO-operated, Government evacuation center,
        School, Hospital -- see Agasti opt_camp_type.)
    """

    tabs = [(T("Basic Details"), None),
            (T("Shelters"), "shelter")]

    rheader = lambda r: shn_shelter_rheader(r,
                                            tabs=tabs)

    # @ToDo: Shelters per type display is broken -- always returns none.
    output = s3_rest_controller(module, resourcename,
                                rheader=rheader)
    return output

# -----------------------------------------------------------------------------
def shelter_service():

    """
        RESTful CRUD controller
        List / add shelter services (e.g. medical, housing, food, ...)
    """

    tabs = [(T("Basic Details"), None),
            (T("Shelters"), "shelter")]

    rheader = lambda r: shn_shelter_rheader(r,
                                            tabs=tabs)

    output = s3_rest_controller(module, resourcename,
                                rheader=rheader)
    return output

# -----------------------------------------------------------------------------
def shelter():

    """ RESTful CRUD controller

    >>> resource="shelter"
    >>> from applications.sahana.modules.s3_test import WSGI_Test
    >>> test=WSGI_Test(db)
    >>> "200 OK" in test.getPage("/sahana/%s/%s" % (module,resource))
    True
    >>> test.assertHeader("Content-Type", "text/html")
    >>> test.assertInBody("List Shelters")
    >>> "200 OK" in test.getPage("/sahana/%s/%s/create" % (module,resource))    #doctest: +SKIP
    True
    >>> test.assertHeader("Content-Type", "text/html")                          #doctest: +SKIP
    >>> test.assertInBody("Add Shelter")                                        #doctest: +SKIP
    >>> "200 OK" in test.getPage("/sahana/%s/%s?format=json" % (module,resource))
    True
    >>> test.assertHeader("Content-Type", "text/html")
    >>> test.assertInBody("[")
    >>> "200 OK" in test.getPage("/sahana/%s/%s?format=csv" % (module,resource))
    True
    >>> test.assertHeader("Content-Type", "text/csv")

    """

    tablename = "%s_%s" % (module,
                           resourcename)
    table = db[tablename]

    # Make pr_presence.pe_id visible:
    pe_id = db.pr_presence.pe_id
    pe_id.readable = True
    pe_id.writable = True

    # Usually, the pe_id field is an invisible foreign key, therefore it
    # has no default representation/requirements => need to add this here:
    pe_id.label = T("Person/Group")
    pe_id.represent = lambda val: shn_pentity_represent(val)
    pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                              shn_pentity_represent,
                                              filterby="instance_type",
                                              orderby="instance_type",
                                              filter_opts=("pr_person",
                                                           "pr_group"))
    
    s3xrc.model.configure(db.pr_presence,
                          # presence not deletable in this view! (need to register a check-out
                          # for the same person instead):
                          deletable=False,
                          list_fields=["id",
                                       "pe_id",
                                       "datetime",
                                       "presence_condition",
                                       "proc_desc"])

    s3xrc.model.configure(table,
                          # Go to People check-in for this shelter after creation
                          create_next = URL(r=request, c="cr", f="shelter",
                                            args=["[id]", "presence"]))

    # Pre-processor
    response.s3.prep = shn_shelter_prep

    # Post-processor
    def postp(r, output):

        if r.component_name == "staff" and \
                deployment_settings.get_aaa_has_staff_permissions():
            addheader = "%s %s." % (STAFF_HELP,
                                    T("Shelter"))
            output.update(addheader=addheader)

        return output
    response.s3.postp = postp

    rheader = lambda r: shn_shelter_rheader(r)
    output = s3_rest_controller(module, resourcename, rheader=rheader)

    return output


def shn_shelter_prep(r):
    """
        Pre-processor for the REST Controller
    """

    if r.component and r.component.name == "presence":
        r.resource.add_filter(db.pr_presence.closed == False)

    # Filter out people which are already staff for this warehouse
    shn_staff_prep(r) 
    if deployment_settings.has_module("inv"):
        # Filter out items which are already in this inventory
        shn_inv_prep(r)
          
    # Cascade the organisation_id from the shelter to the staff
    if r.record:
        db.org_staff.organisation_id.default = r.record.organisation_id
        db.org_staff.organisation_id.writable = False

    if r.interactive:
        if r.method != "read":
            # Don't want to see in Create forms
            # inc list_create (list_fields over-rides)
           pr_address_hide(r.table)

        if r.component:
            if r.component.name == "rat":
                # Hide the Implied fields
                db.assess_rat.location_id.writable = False
                db.assess_rat.location_id.default = r.record.location_id
                db.assess_rat.location_id.comment = ""
                # Set defaults
                if auth.is_logged_in():
                    query = (db.pr_person.uuid == session.auth.user.person_uuid) & \
                            (db.org_staff.person_id == db.pr_person.id)
                    staff_id = db(query).select(db.org_staff.id,
                                                limitby=(0, 1)).first()
                    if staff_id:
                        db.assess_rat.staff_id.default = staff_id.id

            elif r.component.name == "presence":
                # Hide the Implied fields
                db.pr_presence.location_id.writable = False
                db.pr_presence.location_id.default = r.record.location_id
                db.pr_presence.location_id.comment = ""
                db.pr_presence.proc_desc.readable = db.pr_presence.proc_desc.writable = False
                # Set defaults
                db.pr_presence.datetime.default = request.utcnow
                db.pr_presence.observer.default = s3_logged_in_person()
                cr_shelter_presence_opts = {
                    vita.CHECK_IN: vita.presence_conditions[vita.CHECK_IN],
                    vita.CHECK_OUT: vita.presence_conditions[vita.CHECK_OUT]}
                db.pr_presence.presence_condition.requires = IS_IN_SET(
                    cr_shelter_presence_opts, zero=None)
                db.pr_presence.presence_condition.default = vita.CHECK_IN
                # Change the Labels
                s3.crud_strings.pr_presence = Storage(
                    title_create = T("Register Person"),
                    title_display = T("Registration Details"),
                    title_list = T("Registered People"),
                    title_update = T("Edit Registration"),
                    title_search = T("Search Registations"),
                    subtitle_create = T("Register Person into this Shelter"),
                    subtitle_list = T("Current Registrations"),
                    label_list_button = T("List Registrations"),
                    label_create_button = T("Register Person"),
                    msg_record_created = T("Registration added"),
                    msg_record_modified = T("Registration updated"),
                    msg_record_deleted = T("Registration entry deleted"),
                    msg_list_empty = T("No People currently registered in this shelter")
                )

            elif r.component.name == "req":
                if r.method != "update" and r.method != "read":
                    # Hide fields which don't make sense in a Create form
                    # inc list_create (list_fields over-rides)
                    shn_req_create_form_mods()

    return True

# -----------------------------------------------------------------------------
def shn_shelter_rheader(r, tabs=[]):

    """ Resource Headers """

    if r.representation == "html":
        record = r.record
        if record:
            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("People"), "presence"),
                        (T("Staff"), "staff"),
                    ]
                if deployment_settings.has_module("assess"):
                    tabs.append((T("Assessments"), "rat"))
                if deployment_settings.has_module("req"):
                    tabs.append((T("Requests"), "req"))
                if deployment_settings.has_module("inv"):
                    tabs = tabs + shn_show_inv_tabs(r)

            rheader_tabs = shn_rheader_tabs(r, tabs)

            if r.name == "shelter":
                location = shn_gis_location_represent(record.location_id)

                rheader = DIV(TABLE(
                                    TR(
                                        TH("%s: " % T("Name")), record.name
                                      ),
                                    TR(
                                        TH("%s: " % T("Location")), location
                                      ),
                                    ),
                              rheader_tabs)
            else:
                rheader = DIV(TABLE(
                                    TR(
                                        TH("%s: " % T("Name")), record.name
                                      ),
                                    ),
                              rheader_tabs)

            if r.component and r.component.name == "req":
                # Inject the helptext script
                rheader.append(req_helptext_script)

            return rheader
    return None

# -----------------------------------------------------------------------------
# This code provides urls of the form:
# http://.../eden/cr/call/<service>/rpc/<method>/<id>
# e.g.:
# http://.../eden/cr/call/jsonrpc/rpc/list/2
# It is not currently in use but left in as an example, and because it may
# be used in future for interoperating with or transferring data from Agasti
# which uses xml-rpc.  See:
# http://www.web2py.com/examples/default/tools#services
# http://groups.google.com/group/web2py/browse_thread/thread/53086d5f89ac3ae2
def call():
    "Call an XMLRPC, JSONRPC or RSS service"
    return service()

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def rpc(method, id=0):
    if method == "list":
        return db().select(db.cr_shelter.ALL).as_list()
    if method == "read":
        return db(db.cr_shelter.id == id).select().as_list()
    if method == "delete":
        status=db(db.cr_shelter.id == id).delete()
        if status:
            return "Success - record %d deleted!" % id
        else:
            return "Failed - no record %d!" % id
    else:
        return "Method not implemented!"

@service.xmlrpc
def create(name):
    # Need to do validation manually!
    id = db.cr_shelter.insert(name=name)
    return id

@service.xmlrpc
def update(id, name):
    # Need to do validation manually!
    status = db(db.cr_shelter.id == id).update(name=name)
    #@todo: audit!
    if status:
        return "Success - record %d updated!" % id
    else:
        return "Failed - no record %d!" % id
