# -*- coding: utf-8 -*-

""" S3 Person Registry, controllers

    @author: nursix

"""

prefix = request.controller
resourcename = request.function

# -----------------------------------------------------------------------------
# Options Menu (available in all Functions' Views)
def shn_menu():
    response.menu_options = [
        [T("Home"), False, URL(r=request, f="index")],
        [T("Search for a Person"), False, URL(r=request, f="person", args="search_simple")],
        [T("Persons"), False, URL(r=request, f="person"), [
            [T("List"), False, URL(r=request, f="person")],
            [T("Add"), False, URL(r=request, f="person", args="create")],
        ]],
        [T("Groups"), False, URL(r=request, f="group"), [
            [T("List"), False, URL(r=request, f="group")],
            [T("Add"), False, URL(r=request, f="group", args="create")],
        ]]]
    menu_selected = []
    if session.rcvars and "pr_group" in session.rcvars:
        group = db.pr_group
        query = (group.id == session.rcvars["pr_group"])
        record = db(query).select(group.id, group.name, limitby=(0, 1)).first()
        if record:
            name = record.name
            menu_selected.append(["%s: %s" % (T("Group"), name), False,
                                 URL(r=request, f="group", args=[record.id])])
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
        module_name = deployment_settings.modules[prefix].name_nice
    except:
        module_name = T("Person Registry")

    def prep(r):
        if r.representation == "html":
            if not r.id:
                r.method = "search_simple"
                r.custom_action = shn_pr_person_search_simple
            else:
               redirect(URL(r=request, f="person", args=[r.id]))
        return True
    response.s3.prep = prep

    def postp(r, output):
        if isinstance(output, dict):
            gender = []
            for g_opt in pr_gender_opts:
                count = db((db.pr_person.deleted == False) & \
                        (db.pr_person.gender == g_opt)).count()
                gender.append([str(pr_gender_opts[g_opt]), int(count)])

            age = []
            for a_opt in pr_age_group_opts:
                count = db((db.pr_person.deleted == False) & \
                        (db.pr_person.age_group == a_opt)).count()
                age.append([str(pr_age_group_opts[a_opt]), int(count)])

            total = int(db(db.pr_person.deleted == False).count())
            output.update(module_name=module_name, gender=gender, age=age, total=total)
        if r.representation in shn_interactive_view_formats:
            if not r.component:
                label = READ
            else:
                label = UPDATE
            linkto = r.resource.crud._linkto(r)("[id]")
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=str(linkto))
            ]
        r.next = None
        return output
    response.s3.postp = postp

    output = s3_rest_controller("pr", "person")
    response.view = "pr/index.html"

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def person():

    """ RESTful CRUD controller """

    def prep(r):
        if r.component_name == "config":
            _config = db.gis_config
            defaults = db(_config.id == 1).select(limitby=(0, 1)).first()
            for key in defaults.keys():
                if key not in ["id", "uuid", "mci", "update_record", "delete_record"]:
                    _config[key].default = defaults[key]
        if r.representation == "popup":
            # Hide "pe_label" and "missing" fields in person popups
            r.table.pe_label.readable = False
            r.table.pe_label.writable = False
            r.table.missing.readable = False
            r.table.missing.writable = False
        return True
    response.s3.prep = prep

    s3xrc.model.configure(db.pr_group_membership,
                          list_fields=["id",
                                       "group_id",
                                       "group_head",
                                       "description"])

    table = db.pr_person
    s3xrc.model.configure(table, listadd = False, insertable = True)

    output = s3_rest_controller(prefix, resourcename,
                                main="first_name",
                                extra="last_name",
                                rheader=lambda r: shn_pr_rheader(r,
                                    tabs = [(T("Basic Details"), None),
                                            (T("Images"), "image"),
                                            (T("Identity"), "identity"),
                                            (T("Address"), "address"),
                                            (T("Contact Data"), "pe_contact"),
                                            (T("Memberships"), "group_membership"),
                                            (T("Presence Log"), "presence"),
                                            (T("Subscriptions"), "pe_subscription"),
                                            (T("Map Settings"), "config")
                                            ]))

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def group():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    response.s3.filter = (db.pr_group.system == False) # do not show system groups

    s3xrc.model.configure(db.pr_group_membership,
                          list_fields=["id",
                                       "person_id",
                                       "group_head",
                                       "description"])

    output = s3_rest_controller(prefix, resourcename,
                rheader=lambda r: shn_pr_rheader(r,
                    tabs = [(T("Group Details"), None),
                            (T("Address"), "address"),
                            (T("Contact Data"), "pe_contact"),
                            (T("Members"), "group_membership")]))

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def image():

    """ RESTful CRUD controller """

    return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
def pe_contact():

    """ RESTful CRUD controller """

    return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
#def group_membership():

    #""" RESTful CRUD controller """

    #return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
def pentity():

    """ RESTful CRUD controller """

    return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
def download():

    """ Download a file.

        @todo: deprecate? (individual download handler probably not needed)

    """

    return response.download(request, db)


# -----------------------------------------------------------------------------
def tooltip():

    """ Ajax tooltips """

    if "formfield" in request.vars:
        response.view = "pr/ajaxtips/%s.html" % request.vars.formfield
    return dict()


# -----------------------------------------------------------------------------
