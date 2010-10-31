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
    [T("Pledges"), False, URL(r=request, f="pledge"), [
        [T("List"), False, URL(r=request, f="pledge")],
        [T("Add"), False, URL(r=request, f="pledge", args="create")],
        # @ToDo Search by status, location, organisation
        #[T("Search"), False, URL(r=request, f="pledge", args="search")],
    ]],
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
    #return dict(module_name=module_name, a=1)


def req():

    """ RESTful CRUD controller """

    resourcename = request.function # check again in case we're coming from index()
    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    # Pre-processor
    def prep(r):
        if r.representation in shn_interactive_view_formats and r.method != "delete":
            # Don't send the locations list to client (pulled by AJAX instead)
            r.table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

            #if r.method == "create" and not r.component:
            # listadd arrives here as method=None
            if not r.component:
                table.timestmp.default = request.utcnow
                person = session.auth.user.id if auth.is_logged_in() else None
                if person:
                    person_uuid = db(db.auth_user.id == person).select(db.auth_user.person_uuid, limitby=(0, 1)).first().person_uuid
                    person = db(db.pr_person.uuid == person_uuid).select(db.pr_person.id, limitby=(0, 1)).first().id
                    table.person_id.default = person
                # If we hide this field then the dataTables columns don't match up
                #table.pledge_status.readable = False

            elif r.component.name == "pledge":
                db.rms_pledge.submitted_on.default = request.utcnow
                person = session.auth.user.id if auth.is_logged_in() else None
                if person:
                    person_uuid = db(db.auth_user.id == person).select(db.auth_user.person_uuid, limitby=(0, 1)).first().person_uuid
                    person = db(db.pr_person.uuid == person_uuid).select(db.pr_person.id, limitby=(0, 1)).first().id
                    db.rms_pledge.person_id.default = person
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
                    dict(label=str(T("Pledge")), _class="action-btn", url=str(URL(r=request, args=["[id]", "pledge"])))
                ]
            elif r.component_name == "pledge":
                response.s3.actions = [
                    dict(label=T("Details"), _class="action-btn", url=str(URL(r=request, args=["[id]", "pledge"])))
                ]

        return output
    response.s3.postp = postp

    s3xrc.model.configure(table,
                          #listadd=False,
                          editable=True)

    return s3_rest_controller(prefix, resourcename, rheader=shn_rms_rheader)


def ritem():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    #rheader = lambda r: shn_item_rheader(r,
    #                                      tabs = [(T("Requests for Item"), None),
    #                                              (T("Inventories with Item"), "location_item"),
    #                                              (T("Requests for Item"), "req"),
    #                                             ]
    #                                     )

    s3.crud_strings[tablename].label_create_button = None

    s3xrc.model.configure(table, listadd=False)
    return s3_rest_controller(prefix, resourcename) #, rheader=rheader)


def pledge():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    # Pre-processor
    def prep(r):
        if r.representation in shn_interactive_view_formats:
            if r.method == "create":
                # auto fill posted_on field and make it readonly
                table.submitted_on.default = request.now
                table.submitted_on.writable = False

                person = session.auth.user.id if auth.is_logged_in() else None
                if person:
                    person_uuid = db(db.auth_user.id == person).select(db.auth_user.person_uuid, limitby=(0, 1)).first().person_uuid
                    person = db(db.pr_person.uuid == person_uuid).select(db.pr_person.id, limitby=(0, 1)).first().id
                table.person_id.default = person
        return True
    response.s3.prep = prep

    # Change the request status to completed when pledge delivered
    # (this is necessary to close the loop)
    #pledges = db(db.rms_pledge.status == 3).select()
    #for pledge in pledges:
    #    req = db(db.rms_req.id == pledge.req_id).update(completion_status = True)
    #db.commit()

    def postp(r, output):
        if r.representation in shn_interactive_view_formats:
            if not r.component:
                response.s3.actions = [
                    dict(label=str(READ), _class="action-btn", url=str(URL(r=request, args=["[id]", "read"])))
                ]
        return output
    response.s3.postp = postp

    s3xrc.model.configure(table,
                          #listadd=False,
                          editable=True)

    return s3_rest_controller(prefix, resourcename)


def shn_rms_rheader(r):

    """ @todo: fix docstring """

    if r.representation == "html":

        _next = r.here()
        _same = r.same()

        if r.name == "req":
            aid_request = r.record
            if aid_request:
                try:
                    location = db(db.gis_location.id == aid_request.location_id).select(limitby=(0, 1)).first()
                    location_represent = shn_gis_location_represent(location.id)
                except:
                    location_represent = None

                rheader_tabs = shn_rheader_tabs( r,
                                                 [(T("Edit Details"), None),
                                                  (T("Items"), "ritem"),
                                                  (T("Pledge"), "pledge"),
                                                  ]
                                                 )

                rheader = DIV( TABLE(TR(TH(T("Message") + ": "),
                                TD(aid_request.message, _colspan=3)),
                                TR(TH(T("Priority") + ": "),
                                aid_request.priority,
                                #TH(T("Source Type") + ": "),
                                #rms_req_source_type.get(aid_request.source_type, T("unknown"))),
                                TH(T("Document") + ": "),
                                document_represent(aid_request.document_id)),
                                TR(TH(T("Time of Request") + ": "),
                                aid_request.timestmp,
                                TH(T("Verified") + ": "),
                                aid_request.verified),
                                TR(TH(T("Location") + ": "),
                                location_represent,
                                TH(T("Actionable") + ": "),
                                aid_request.actionable)),
                                rheader_tabs
                                )

                return rheader

    return None
