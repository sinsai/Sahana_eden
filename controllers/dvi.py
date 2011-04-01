# -*- coding: utf-8 -*-

"""
    Disaster Victim Identification, Controllers

    @author: nursix
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# -----------------------------------------------------------------------------
# Only people with the DVI role should be able to access this module
if deployment_settings.modules[module].access:
    authorised = False
    groups = re.split("\|", _module.access)[1:-1]
    for group in groups:
        if s3_has_role(group):
            authorised = True
    if not authorised:
        unauthorised()

# -----------------------------------------------------------------------------
# Options Menu (available in all Functions" Views)
def shn_menu():
    response.menu_options = [
        #[T("Home"), False, URL(r=request, f="index")],
        [T("Recovery Requests"), False, None,[
            [T("New"),
             False, aURL(p="create", r=request, f="recreq",
                         args="create")],
            [T("List Current"),
             False, aURL(r=request, f="recreq",
                         vars={"recreq.status":"1,2,3"})],
            [T("List All"),
             False, aURL(r=request, f="recreq")],
        ]],
        [T("Dead Body"), False, None,[
            [T("New"),
             False, aURL(p="create", r=request, f="body",
                         args="create")],
            [T("Search"),
             False, aURL(r=request, f="body",
                         args="search")],
            [T("List all"),
             False, aURL(r=request, f="body")],
            [T("List unidentified"),
             False, aURL(r=request, f="body",
                         vars=dict(status="unidentified"))],
        ]],
        [T("Missing Persons"), False, None, [
            [T("List all"), False, aURL(r=request, f="person")],
        ]],
        [T("Help"), False, URL(r=request, f="index")]
    ]
    menu_selected = []
    if session.rcvars and "dvi_body" in session.rcvars:
        body = db.dvi_body
        query = (body.id == session.rcvars["dvi_body"])
        record = db(query).select(body.id, body.pe_label, limitby=(0,1)).first()
        if record:
            label = record.pe_label
            response.menu_options[-2][-1].append(
                [T("Candidate Matches for Body %s" % label),
                 False, URL(r=request, f="person",
                            vars=dict(match=record.id))]
            )
            menu_selected.append(
                ["%s: %s" % (T("Body"), label),
                 False, URL(r=request, f="body",
                            args=[record.id])]
            )
    if session.rcvars and "pr_person" in session.rcvars:
        person = db.pr_person
        query = (person.id == session.rcvars["pr_person"])
        record = db(query).select(person.id, limitby=(0, 1)).first()
        if record:
            name = shn_pr_person_represent(record.id)
            menu_selected.append(
                ["%s: %s" % (T("Person"), name),
                 False, URL(r=request, f="person",
                        args=[record.id])]
            )
    if menu_selected:
        menu_selected = [T("Open recent"), True, None, menu_selected]
        response.menu_options.append(menu_selected)

shn_menu()

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    try:
        module_name = deployment_settings.modules[module].name_nice
    except:
        module_name = T("Disaster Victim Identification")

    total = db(db.dvi_body.deleted == False).count()

    query = (db.dvi_body.deleted == False) & \
            (db.dvi_identification.pe_id == db.dvi_body.pe_id) & \
            (db.dvi_identification.deleted == False) & \
            (db.dvi_identification.status == 3)
    identified = db(query).count()

    status = [[str(T("identified")), int(identified)],
              [str(T("unidentified")), int(total-identified)]]

    response.title = module_name
    return dict(module_name=module_name,
                total=total,
                status=status)


# -----------------------------------------------------------------------------
def recreq():
    """ Recovery Requests List """

    resource = request.function

    db.dvi_recreq.person_id.default = s3_logged_in_person()
    output = s3_rest_controller(module, resource)

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def body():
    """ Dead Bodies Registry """

    resource = request.function

    db.pr_presence.presence_condition.default = vita.CHECK_IN

    status = request.get_vars.get("status", None)
    if status == "unidentified":
        query = (db.dvi_identification.deleted == False) & \
                (db.dvi_identification.status == 3)
        ids = db(query).select(db.dvi_identification.pe_id)
        ids = [i.pe_id for i in ids]
        if ids:
            response.s3.filter = (~(db.dvi_body.pe_id.belongs(ids)))

    s3xrc.model.configure(db.dvi_body, main="pe_label", extra="gender")

    dvi_tabs = [(T("Recovery"), ""),
                (T("Checklist"), "checklist"),
                (T("Images"), "image"),
                (T("Physical Description"), "physical_description"),
                (T("Effects Inventory"), "effects"),
                (T("Tracing"), "presence"),
                (T("Identification"), "identification")]

    output = s3_rest_controller(module, resource,
                                 rheader=lambda r: \
                                         shn_dvi_rheader(r, tabs=dvi_tabs))
    shn_menu()
    return output


# -----------------------------------------------------------------------------
def person():
    """ Missing Persons Registry (Match Finder) """

    resource = request.function

    s3.crud_strings["pr_person"].update(
        title_display = T("Missing Person Details"),
        title_list = T("Missing Persons"),
        subtitle_list = T("List of Missing Persons"),
        label_list_button = T("List Missing Persons"),
        msg_list_empty = T("No Persons found"),
        msg_no_match = T("No Persons currently reported missing"))

    s3xrc.model.configure(db.pr_group_membership,
                          list_fields=["id",
                                       "group_id",
                                       "group_head",
                                       "description"])

    s3xrc.model.configure(db.pr_person,
                          listadd=False,
                          editable=False,
                          deletable=False,
                          list_fields=["id",
                                       "first_name",
                                       "middle_name",
                                       "last_name",
                                       "picture",
                                       "gender",
                                       "age_group"])

    def prep(jr):
        if not jr.id and not jr.method and not jr.component:
            body_id = jr.request.get_vars.get("match", None)
            body = db(db.dvi_body.id == body_id).select(
                      db.dvi_body.pe_label, limitby=(0, 1)).first()
            label = body and body.pe_label or "#%s" % body_id
            if body_id:
                query = vita.match_query(body_id)
                jr.resource.add_filter(query)
                s3.crud_strings["pr_person"].update(
                    subtitle_list = T("Candidate Matches for Body %s" % label),
                    msg_no_match = T("No records matching the query"))
        person = s3_logged_in_person()
        if person:
            db.pr_presence.observer.default = person
            db.pr_presence.observer.writable = False
            db.pr_presence.observer.comment = None
            db.pf_missing_report.observer.default = person
            db.pf_missing_report.observer.writable = False
            db.pf_missing_report.observer.comment = None
        elif jr.component_name == "presence":
            condition = jr.request.vars.get("condition", None)
            if condition:
                try:
                    condition = int(condition)
                except:
                    pass
                else:
                    table = db.pr_presence
                    table.presence_condition.default = condition
                    table.presence_condition.readable = False
                    table.presence_condition.writable = False
                    table.orig_id.readable = False
                    table.orig_id.writable = False
                    table.dest_id.readable = False
                    table.dest_id.writable = False
                    table.observer.readable = False
                    table.observer.writable = False
        return True

    response.s3.prep = prep

    db.pr_person.missing.readable = False
    db.pr_person.missing.writable = False
    db.pr_person.missing.default = True

    db.pf_missing_report.person_id.readable = False
    db.pf_missing_report.person_id.writable = False

    # Show only missing persons in list views
    if len(request.args) == 0:
        response.s3.filter = (db.pr_person.missing == True)

    pf_tabs = [
                (T("Missing Report"), "missing_report"),
                (T("Person Details"), None),
                (T("Physical Description"), "physical_description"),
                (T("Images"), "image"),
                (T("Identity"), "identity"),
                (T("Address"), "address"),
                (T("Contact Data"), "contact"),
                (T("Presence Log"), "presence"),
               ]

    rheader = lambda r: shn_pr_rheader(r, tabs=pf_tabs)

    output = s3_rest_controller("pr", resource,
                                 main="first_name",
                                 extra="last_name",
                                 rheader=rheader)

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def download():
    """ File Download """

    return response.download(request, db)


# -----------------------------------------------------------------------------
def tooltip():
    """ Ajax Tooltips """

    formfield = request.vars.get("formfield", None)
    if formfield:
        response.view = "pr/ajaxtips/%s.html" % formfield
    return dict()


#
# -----------------------------------------------------------------------------
