# -*- coding: utf-8 -*-

""" Request Management System - Controllers """

prefix = request.controller
resourcename = request.function

if prefix not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
menu = [
    [T("Home"), False, URL(r=request, f="index")],
    [T("Requests"), False, URL(r=request, f="req"), [
        [T("List"), False, URL(r=request, f="req")],
        [T("Add"), False, URL(r=request, f="req", args="create")],
        # @ToDo Search by priority, status, location
        #[T("Search"), False, URL(r=request, f="req", args="search")],
    ]],
    [T("All Requested Items"), False, URL(r=request, f="ritem")],
]
if session.rcvars:
    if "hms_hospital" in session.rcvars:
        hospital = db.hms_hospital
        query = (hospital.id == session.rcvars["hms_hospital"])
        selection = db(query).select(hospital.id, hospital.name, limitby=(0, 1)).first()
        if selection:
            menu_hospital = [
                [selection.name, False, URL(r=request, c="hms", f="hospital", args=[selection.id])]
            ]
            menu.extend(menu_hospital)
    if "cr_shelter" in session.rcvars:
        shelter = db.cr_shelter
        query = (shelter.id == session.rcvars["cr_shelter"])
        selection = db(query).select(shelter.id, shelter.name, limitby=(0, 1)).first()
        if selection:
            menu_shelter = [
                [selection.name, False, URL(r=request, c="cr", f="shelter", args=[selection.id])]
            ]
            menu.extend(menu_shelter)

response.menu_options = menu


def index():

    """ Module's Home Page

        Default to the rms_req list view.

    """

    request.function = "req"
    request.args = []
    return req()

    #module_name = deployment_settings.modules[prefix].name_nice
    #response.title = module_name
    #return dict(module_name=module_name, a=1)


def req():

    """ RESTful CRUD controller """

    resourcename = request.function # check again in case we're coming from index()
    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    # Pre-processor
    def prep(r):
        response.s3.cancel = r.here()
        if r.representation in shn_interactive_view_formats and r.method != "delete":
            # Don't send the locations list to client (pulled by AJAX instead)
            r.table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

            #if r.method == "create" and not r.component:
            # listadd arrives here as method=None
            if not r.component:
                table.datetime.default = request.utcnow
                table.person_id.default = s3_logged_in_person()

                # @ToDo Default the Organisation too

        return True
    response.s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.representation in shn_interactive_view_formats:
            #if r.method == "create" and not r.component:
            # listadd arrives here as method=None
            if r.method != "delete" and not r.component:
                # Redirect to the Assessments tabs after creation
                r.next = r.other(method="ritem", record_id=s3xrc.get_session(prefix, resourcename))

            # Custom Action Buttons
            if not r.component:
                response.s3.actions = [
                    dict(label=str(T("Open")), _class="action-btn", url=str(URL(r=request, args=["[id]", "update"]))),
                    dict(label=str(T("Items")), _class="action-btn", url=str(URL(r=request, args=["[id]", "ritem"]))),
                ]

        return output
    response.s3.postp = postp

    s3xrc.model.configure(table,
                          #listadd=False, #@todo: List add is causing errors with JS - FIX
                          editable=True)

    return s3_rest_controller(prefix,
                              resourcename,
                              rheader=shn_rms_req_rheader)

def shn_rms_req_rheader(r):

    """ Resource Header for Requests """

    if r.representation == "html":
        if r.name == "req":
            req_record = r.record
            if req_record:
                _next = r.here()
                _same = r.same()

                try:
                    location = db(db.gis_location.id == req_record.location_id).select(limitby=(0, 1)).first()
                    location_represent = shn_gis_location_represent(location.id)
                except:
                    location_represent = None

                rheader_tabs = shn_rheader_tabs( r,
                                                 [(T("Edit Details"), None),
                                                  (T("Items"), "ritem"),
                                                  ]
                                                 )

                rheader = DIV( TABLE(
                                   TR( TH( T("Message") + ": "),
                                       TD(req_record.message, _colspan=3)
                                      ),
                                   TR( TH( T("Time of Request") + ": "),
                                       req_record.datetime,
                                       TH( T( "Location") + ": "),
                                       location_represent,
                                      ),
                                   TR( TH( T("Priority") + ": "),
                                       req_record.priority,
                                       TH( T("Document") + ": "),
                                       document_represent(req_record.document_id)
                                      ),
                                     ),
                                rheader_tabs
                                )

                return rheader
    return None



def ritem():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    s3xrc.model.configure(table, insertable=False)
    return s3_rest_controller(prefix, resourcename)


def store_for_req():

    store_table = None

    return dict(store_table = store_table)
