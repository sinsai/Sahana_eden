# -*- coding: utf-8 -*-

"""
    Shelter Registry - Controllers
"""
# @ToDo Search shelters by type, services, location, available space
# @ToDo Shelter reports -- occupancy, needs -- per time
# @ToDo Associate persons with shelters (via presence loc == shelter loc?)

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Shelters"), False, URL(r=request, f="shelter"), [
        [T("List"), False, URL(r=request, f="shelter")],
        [T("Add"), False, URL(r=request, f="shelter", args="create")],
        # @ToDo Search by type, services, location, available space
        #[T("Search"), False, URL(r=request, f="shelter", args="search")],
    ]],
    [T("Shelter Types and Services"), False, URL(r=request, f="#"), [
        [T("List / Add Services"), False, URL(r=request, f="shelter_service")],
        [T("List / Add Types"), False, URL(r=request, f="shelter_type")],
    ]],
]

# S3 framework functions
def index():

    """ Module's Home Page """
    
    module_name = deployment_settings.modules[module].name_nice
    
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def shelter_type():

    """
    List / add shelter types (e.g. NGO-operated, Government evacuation center,
    School, Hospital -- see Agasti opt_camp_type.)
    """

    resource = request.function

    # Don't provide delete button in list view
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    return shn_rest_controller(module, resource, sticky=True)

# -----------------------------------------------------------------------------
def shelter_service():

    """
    List / add shelter services (e.g. medical, housing, food,...)
    """

    resource = request.function

    # Don't provide delete button in list view
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    return shn_rest_controller(module, resource, sticky=True)

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

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Don't send the locations list to client (pulled by AJAX instead)
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    crud.settings.create_onvalidation = shelter_onvalidation
    crud.settings.update_onvalidation = shelter_onvalidation

    response.s3.pagination = True
    output = shn_rest_controller(module, resource, listadd=False)

    return output

def shelter_onvalidation(form):
    """
    The school- and hospital-specific fields are guarded by checkboxes in
    the form.  If the "is_school" or "is_hospital" checkbox was checked,
    we use the corresponding field values, else we discard them.  Presence
    of a non-empty value for school_code or hospital_id is what determines
    whether the shelter is a school or hospital.

    We don't just clear the fields in the form if the user unchecks the
    checkbox because they might do that accidentally, and it would not be
    nice to make them re-enter the info.
    """

    # Note the checkbox inputs that guard the optional data are inserted in
    # the view and are not database fields, so are not in form.vars, only in
    # request.vars.
    if not "is_school" in request.vars:
        form.vars.school_code = None
        form.vars.school_pf = None

    if not "is_hospital" in request.vars:
        form.vars.hospital_id = None


# -----------------------------------------------------------------------------
# ToDo  No longer in use.  If we don't find a use soon, can remove this.
def shn_shelter_rheader(r, tabs=[]):

    """ Resource Headers """

    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, tabs)

        record = r.record
        rheader = DIV(TABLE(
                        TR(
                            TH(Tstr("Name") + ": "), record.name
                          ),
                        ),
                      rheader_tabs)

        return rheader

    else:
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
def rpc(method,id=0):
    if method == "list":
        return db().select(db.cr_shelter.ALL).as_list()
    if method == "read":
        return db(db.cr_shelter.id==id).select().as_list()
    if method == "delete":
        status=db(db.cr_shelter.id==id).delete()
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
    if status:
        return "Success - record %d updated!" % id
    else:
        return "Failed - no record %d!" % id
