# -*- coding: utf-8 -*-

"""
    Shelter Registry - Controllers
"""
# @ToDo Search shelters by type, services, location, available space
# @ToDo Tie in assessments from RAT and requests from RMS.
# @ToDo Associate persons with shelters (via presence loc == shelter loc?)

module = request.controller
resourcename = request.function

if module not in deployment_settings.modules:
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
        List / add shelter services (e.g. medical, housing, food,...)
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
                          args=["[id]", "presence"]),
        create_onvalidation = shn_shelter_onvalidation,
        update_onvalidation = shn_shelter_onvalidation)

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

    tabs = [(T("Basic Details"), None),
            (T("People"), "presence"),
            (T("Staff"), "staff"),
            (T("Assessments"), "rat"),
            (T("Requests"), "req")]

    rheader = lambda r: shn_shelter_rheader(r,
                                            tabs=tabs + shn_show_inv_tabs(r))
    output = s3_rest_controller(module, resourcename, rheader=rheader)

    return output


# -----------------------------------------------------------------------------
"""
    The school- and hospital-specific fields are guarded by checkboxes in
    the form.  If the "is_school" or "is_hospital" checkbox was checked,
    we use the corresponding field values, else we discard them.  Presence
    of a non-empty value for school_code or hospital_id is what determines
    later whether a shelter record is a school or hospital, as the is_school
    and is_hospital values are not in the table.

    Note we clear the unused hospital value *before* validation, because
    there is a (small) possibility that someone deleted the chosen hospital
    record while this request was in flight.  If the user doesn't want the
    hospital they selected, there's no reason to make sure it's in the database.

    The check for a missing school code or hospital id value is in an
    onvalidation function.  Web2py short-circuits validation, so if there are
    other errors, the check on school code and hospital id won't be called.
    If the user corrects their other errors but has a mistake in school code
    or hospital id, they'll do another round trip through fixing an error.

    We don't just clear the fields in the form if the user unchecks the
    checkbox because they might do that accidentally, and it would not be
    nice to make them re-enter the info.
"""

def shn_shelter_prep(r):
    """
        If the "is_school" or "is_hospital" checkbox was checked, we use the
        corresponding field values, else we clear them so no attempt is made
        to validate them.
    """

    # Note the checkbox inputs that guard the optional data are inserted in
    # the view and are not database fields, so are not in request.post_vars
    # (or, after validation, in form.vars), only in request.vars.

    # Likewise, these controls won't be present for, e.g., xml import, so
    # restrict to html and popup.  The hospital_id field won't be present
    # at all if the hms module is not enabled.  When we later get to
    # onvalidation, we need to know if this was html or popup, so save that
    # in request.vars in a variable that won't be used to carry any real
    # form data.

    if r.component and r.component.name == "presence":
        r.resource.add_filter(db.pr_presence.closed == False)

    if r.interactive:
        # Don't send the locations list to client (pulled by AJAX instead)
        r.table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db,
                                                                  "gis_location.id"))

        # Cascade the organisation_id from the shelter to the staff
        if r.record:
            db.org_staff.organisation_id.default = r.record.organisation_id
            db.org_staff.organisation_id.writable = False

        # Remember this is html or popup.
        response.cr_shelter_request_was_html_or_popup = True

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

            elif r.component.name == "req":
                # Hide the Implied fields
                db.rms_req.hospital_id.writable = db.rms_req.hospital_id.readable = False
                db.rms_req.location_id.writable = False
                db.rms_req.location_id.default = r.record.location_id
                db.rms_req.location_id.comment = ""
                # Set defaults
                db.rms_req.datetime.default = request.utcnow
                db.rms_req.person_id.default = s3_logged_in_person()

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

        if r.http == "POST":

            #if not "is_school" in request.vars:
            #    request.post_vars.school_code = None
            #    request.post_vars.school_pf = None

            if not "is_hospital" in request.vars and \
               "hospital_id" in request.post_vars:
                request.post_vars.hospital_id = None

    elif r.representation == "aadata" and r.component and r.component.name == "req":
        # Hide the Implied fields here too to make columns match
        db.rms_req.hospital_id.readable = False

    return True

# -----------------------------------------------------------------------------
def shn_shelter_onvalidation(form):
    """
        If the user checked is_school, but there is no school_code, add a
        form.error for that field, to fail the submission and get an error
        message into the page.  Likewise for is_hospital and hospital_id.
    """

    if response.cr_shelter_request_was_html_or_popup:
        # Get rid of that before anyone else sees it...
        response.cr_shelter_request_was_html_or_popup = None

        #if "is_school" in request.vars and not form.vars.school_code:
        #    # Indicate that this is a school by setting a value that no school uses.
        #    form.vars.school_code = 1

        # Note the form is defective if there's an is_hospital checkbox
        # but no hospital_id field...
        if "is_hospital" in request.vars and not form.vars.hospital_id:
            form.errors.hospital_id = T(
                "Please select a hospital or don't check 'Is this a hospital?'")

    return

# -----------------------------------------------------------------------------
def shn_shelter_rheader(r, tabs=[]):

    """ Resource Headers """

    if r.representation == "html":
        record = r.record
        if record:
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
