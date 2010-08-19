# -*- coding: utf-8 -*-

"""
    Shelter Registry - Controllers
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Add Shelter"), False, URL(r=request, f="shelter", args="create")],
    [T("List Shelters"), False, URL(r=request, f="shelter"), [
        [T("Services"), False, URL(r=request, f="shelter_service")],
        [T("Types"), False, URL(r=request, f="shelter_type")],
    ]],
    #[T("Search Shelters"), False, URL(r=request, f="shelter", args="search")]
]

# S3 framework functions
def index():

    """ Module's Home Page """
    
    module_name = deployment_settings.modules[module].name_nice
    
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def shelter_type():

    """ RESTful CRUD controller """

    resource = request.function

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, listadd=False,
                                 rheader=lambda r: \
                                         shn_shelter_rheader(r,
                                            tabs = [(T("Basic Details"), None),
                                                    (T("Shelters"), "shelter")]),
                                                    sticky=True)
    return output

# -----------------------------------------------------------------------------
def shelter_service():

    """ RESTful CRUD controller """

    resource = request.function

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, listadd=False,
                                 rheader=lambda r: \
                                         shn_shelter_rheader(r,
                                            tabs = [(T("Basic Details"), None),
                                                    (T("Shelters"), "shelter")]),
                                                    sticky=True)
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

    resource = request.function

    response.s3.pagination = True

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, listadd=False)

    return output

# -----------------------------------------------------------------------------
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
