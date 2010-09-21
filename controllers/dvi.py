# -*- coding: utf-8 -*-

""" DVI Module - Controllers

    @author: Dominic König

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
        if shn_has_role(group):
            authorised = True
    if not authorised:
        unauthorised()

# -----------------------------------------------------------------------------
# Options Menu (available in all Functions" Views)
def shn_menu():
    response.menu_options = [
        [T("Home"), False, URL(r=request, f="index")],
        [T("Recovery Requests"), False, URL(r=request, f="recreq"),[
            [T("List Requests"), False, URL(r=request, f="recreq")],
            [T("New Request"), False, URL(r=request, f="recreq", args="create")],
        ]],
        [T("Dead Body Reports"), False, URL(r=request, f="body"),[
            [T("List all"), False, URL(r=request, f="body")],
            [T("List unidentified"), False, URL(r=request, f="body", vars=dict(status="unidentified"))],
            [T("New Report"), False, URL(r=request, f="body", args="create")],
            [T("Search by ID Tag"), False, URL(r=request, f="body", args="search_simple")]
        ]],
        [T("Missing Persons"), False, URL(r=request, f="person")]
    ]
    menu_selected = []
    if session.rcvars and "dvi_body" in session.rcvars:
        body = db.dvi_body
        query = (body.id == session.rcvars["dvi_body"])
        record = db(query).select(body.id, body.pe_label, limitby=(0,1)).first()
        if record:
            label = record.pe_label
            menu_selected.append(["%s: %s" % (T("Body"), label), False,
                                 URL(r=request, f="body", args=[record.id])])
    if session.rcvars and "pr_person" in session.rcvars:
        person = db.pr_person
        query = (person.id == session.rcvars["pr_person"])
        record = db(query).select(person.id, limitby=(0, 1)).first()
        if record:
            name = shn_pr_person_represent(record.id)
            menu_selected.append(["%s: %s" % (T("Person"), name), False,
                                 URL(r=request, f="person", args=[record.id])])
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
            (db.dvi_identification.opt_dvi_id_status == 3)
    identified = db(query).count()

    status = [[str(T("identified")), int(identified)],
              [str(T("unidentified")), int(total-identified)]]

    return dict(module_name=module_name,
                total=total,
                status=status)


# -----------------------------------------------------------------------------
def recreq():

    """ RESTful CRUD controller """

    resource = request.function

    def recreq_postp(jr, output):
        if jr.representation in shn_interactive_view_formats:
            label = UPDATE
            linkto = shn_linkto(jr, sticky=True)("[id]")
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=str(linkto))
            ]
        return output
    response.s3.postp = recreq_postp

    response.s3.pagination = True
    output = shn_rest_controller(module, resource, listadd=False)

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def body():

    """ RESTful CRUD controller """

    resource = request.function

    status = request.get_vars.get("status", None)
    if status == "unidentified":
        query = (db.dvi_identification.deleted == False) & \
                (db.dvi_identification.opt_dvi_id_status == 3)
        ids = db(query).select(db.dvi_identification.pe_id)
        ids = [i.pe_id for i in ids]
        if ids:
            response.s3.filter = (~(db.dvi_body.pe_id.belongs(ids)))

    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 main="pe_label",
                                 extra="gender",
                                 rheader=lambda r: \
                                         shn_dvi_rheader(r, tabs=[
                                            (T("Recovery"), ""),
                                            (T("Checklist"), "checklist"),
                                            (T("Images"), "image"),
                                            (T("Physical Description"), "physical_description"),
                                            (T("Effects Inventory"), "effects"),
                                            (T("Tracing"), "presence"),
                                            (T("Identification"), "identification"),
                                         ]),
                                 listadd=False)
    shn_menu()
    return output


# -----------------------------------------------------------------------------
def person():

    """ RESTful CRUD controller """

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
        list_fields=["id",
                     "first_name",
                     "middle_name",
                     "last_name",
                     "gender",
                     "age_group"])

    def prep(jr):
        if auth.shn_logged_in():
            persons = db.pr_person
            person = db(persons.uuid == session.auth.user.person_uuid).select(persons.id, limitby=(0,1)).first()
            if person:
                db.pr_presence.reporter.default = person.id
                db.pr_presence.reporter.writable = False
                db.pr_presence.reporter.comment = None
                db.mpr_missing_report.reporter.default = person.id
                db.mpr_missing_report.reporter.writable = False
                db.mpr_missing_report.reporter.comment = None
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

    db.mpr_missing_report.person_id.readable = False
    db.mpr_missing_report.person_id.writable = False

    # Show only missing persons in list views
    if len(request.args) == 0:
        response.s3.filter = (db.pr_person.missing == True)

    mpr_tabs = [
                (T("Missing Report"), "missing_report"),
                (T("Person Details"), None),
                (T("Physical Description"), "physical_description"),
                (T("Images"), "image"),
                (T("Identity"), "identity"),
                (T("Address"), "address"),
                (T("Contact Data"), "pe_contact"),
                (T("Presence Log"), "presence"),
               ]

    rheader = lambda r: shn_pr_rheader(r, tabs=mpr_tabs)

    response.s3.pagination = True
    output = shn_rest_controller("pr", resource,
                                 main="first_name",
                                 extra="last_name",
                                 listadd=False,
                                 editable=False,
                                 deletable=False,
                                 rheader=rheader)

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def download():

    """ Download a file. """

    return response.download(request, db)


# -----------------------------------------------------------------------------
def tooltip():

    """ Ajax tooltips """

    formfield = request.vars.get("formfield", None)
    if formfield:
        response.view = "pr/ajaxtips/%s.html" % formfield
    return dict()

#
# -----------------------------------------------------------------------------
