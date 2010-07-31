# -*- coding: utf-8 -*-

"""
    Volunteer Management System
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions)
def shn_menu():
    menu = [
        [T("Projects"), False, URL(r=request, f="project"),[
            [T("Search"), False, URL(r=request, f="project", args="search_location")],
            [T("Add Project"), False, URL(r=request, f="project", args="create")],
        ]],
    ]

    menu_teams = [
        [T("Teams"), False, URL(r=request, f="group"),[
            [T("List"), False, URL(r=request, f="group")],
            [T("Add"), False, URL(r=request, f="group", args="create", vars={"_next":URL(r=request, args=request.args, vars=request.vars)})],
        ]]
    ]
    menu.extend(menu_teams)

    menu_persons = [
        [T("Persons"), False, URL(r=request, f="person", args=["search_simple"], vars={"_next":URL(r=request, f="person", args=["[id]", "volunteer"], vars={"vol_tabs":"volunteer"})}),[
            [T("List"), False, URL(r=request, f="person", vars={"_next":URL(r=request, f="person", args=["[id]", "volunteer"], vars={"vol_tabs":"volunteer"})})],
            [T("Add"), False, URL(r=request, f="person", args="create", vars={"_next":URL(r=request, f="person", args=["[id]", "volunteer"], vars={"vol_tabs":"volunteer"})})],
        ]]
    ]
    menu.extend(menu_persons)

    menu_skills = [
        [T("Skill Types"), False, URL(r=request, f="skill_types")],
    ]
    menu.extend(menu_skills)
    if auth.user is not None:
        if auth.user.person_uuid:
            set = db(db.pr_person.uuid == auth.user.person_uuid)
            me = set.select(db.pr_person.id, limitby=(0,1)).first()
            if me:
                menu_user = [
                    [T("My Volunteer Info"), False, URL(r=request, f="person", args=[me.id, "volunteer"])],
                    [T("My Tasks"), False, URL(r=request, f="task", args="")]
                ]
                menu.extend(menu_user)

    # Last selections:
    menu_selected = []
    if session.rcvars and "pr_person" in session.rcvars:
        person = db.pr_person
        query = (person.id == session.rcvars["pr_person"])
        record = db(query).select(person.id, limitby=(0, 1)).first()
        if record:
            name = shn_pr_person_represent(record.id)
            menu_selected.append(["%s: %s" % (T("Person"), name), False,
                                 URL(r=request, f="person", args=[record.id])])
    if session.rcvars and "org_project" in session.rcvars:
        project = db.org_project
        query = (project.id == session.rcvars["org_project"])
        record = db(query).select(project.id, project.code, limitby=(0, 1)).first()
        if record:
            code = record.code
            menu_selected.append(["%s: %s" % (T("Project"), code), False,
                                 URL(r=request, f="project", args=[record.id])])
    if session.rcvars and "pr_group" in session.rcvars:
        group = db.pr_group
        query = (group.id == session.rcvars["pr_group"])
        record = db(query).select(group.id, group.name, limitby=(0, 1)).first()
        if record:
            name = record.name
            menu_selected.append(["%s: %s" % (T("Team"), name), False,
                                 URL(r=request, f="group", args=[record.id])])
    if menu_selected:
        menu_selected = [T("Open recent"), True, None, menu_selected]
        menu.append(menu_selected)

    response.menu_options = menu

shn_menu()

def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice

    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def person():

    """ Personal Data of the volunteer """

    response.s3.pagination = True

    def prep(jr):
        if jr.representation == "html":
            if jr.component and jr.component_name in shn_vol_volunteer_data or \
               jr.method and jr.method == "view_map":
                # TODO: These files are for the multiselect widget used for skills.
                # Check if we still need them if we switch to a different widget.
                response.files.append(URL(r=request,
                                          c="static/scripts/S3",
                                          f="jquery.multiSelect.js"))
                response.files.append(URL(r=request,
                                          c="static/styles/S3",
                                          f="jquery.multiSelect.css"))

                db.pr_group_membership.group_id.label = T("Team Id")
                db.pr_group_membership.group_head.label = T("Team Head")

                s3xrc.model.configure(db.pr_group_membership,
                                        list_fields=["id",
                                                    "group_id",
                                                    "group_head",
                                                    "description"])
            else:
                db.pr_person.missing.default = False
        return True
    response.s3.prep = prep

    def postp(jr, output):
        if jr.representation in ("html", "popup"):
            if not jr.component:
                label = READ
            else:
                label = UPDATE
            linkto = shn_linkto(jr, sticky=True)("[id]")
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=linkto)
            ]
        return output
    response.s3.postp = postp

    resource = request.function
    output = shn_rest_controller("pr", resource,
        main="first_name",
        extra="last_name",
        rheader=lambda jr: shn_vol_rheader(jr),
        sticky=True,
        listadd=False)

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def project():
    "Project controller"

    resource = request.function

    def org_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = org_postp

    # ServerSidePagination
    response.s3.pagination = True

    output = shn_rest_controller("org", resource,
        listadd=False,
        main="code",
        rheader=lambda jr: shn_project_rheader(jr,
            tabs = [(T("Basic Details"), None),
                    (T("Staff"), "staff"),
                    (T("Tasks"), "task"),
                    #(T("Donors"), "organisation"),
                    #(T("Sites"), "site"),          # Ticket 195
                   ]),
        sticky=True)

    return output


# -----------------------------------------------------------------------------
def task():
    """ Manage current user's tasks """

    resource = request.function
    tablename = "org_%s" % (resource)
    table = db[tablename]

    my_person_id = None

    if auth.user is not None and auth.user.person_uuid:
        my_person_id = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.id, limitby=(0,1)).first()

    if not my_person_id:
        session.error = T("No person record found for current user.")
        redirect(URL(r=request, f="index"))

    table.person_id.default = my_person_id
    #table.person_id.writable = False

    response.s3.filter = (db.org_task.person_id == my_person_id)

    s3.crud_strings[tablename].title_list = T("My Tasks")
    s3.crud_strings[tablename].subtitle_list = T("Task List")

    response.s3.pagination = True

    return shn_rest_controller("org", resource, listadd=False)


# -----------------------------------------------------------------------------
def skill_types():
    "Allow user to define new skill types."
    return shn_rest_controller(module, "skill_types")

# -----------------------------------------------------------------------------
def group():

    """
    Team controller -- teams use the group table from pr.
    """

    tablename = "pr_group"
    table = db[tablename]

    table.group_type.label = T("Team Type")
    table.description.label = T("Team Description")
    table.name.label = T("Team Name")
    db.pr_group_membership.group_id.label = T("Team Id")
    db.pr_group_membership.group_head.label = T("Team Head")

    # CRUD Strings
    ADD_TEAM = T("Add Team")
    LIST_TEAMS = T("List Teams")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_TEAM,
        title_display = T("Team Details"),
        title_list = LIST_TEAMS,
        title_update = T("Edit Team"),
        title_search = T("Search Teams"),
        subtitle_create = T("Add New Team"),
        subtitle_list = T("Teams"),
        label_list_button = LIST_TEAMS,
        label_create_button = ADD_TEAM,
        label_search_button = T("Search Teams"),
        msg_record_created = T("Team added"),
        msg_record_modified = T("Team updated"),
        msg_record_deleted = T("Team deleted"),
        msg_list_empty = T("No Items currently registered"))

    s3.crud_strings["pr_group_membership"] = Storage(
        title_create = T("Add Member"),
        title_display = T("Membership Details"),
        title_list = T("Team Members"),
        title_update = T("Edit Membership"),
        title_search = T("Search Member"),
        subtitle_create = T("Add New Member"),
        subtitle_list = T("Current Team Members"),
        label_list_button = T("List Members"),
        label_create_button = T("Add Group Member"),
        label_delete_button = T("Delete Membership"),
        msg_record_created = T("Team Member added"),
        msg_record_modified = T("Membership updated"),
        msg_record_deleted = T("Membership deleted"),
        msg_list_empty = T("No Members currently registered"))

    response.s3.filter = (db.pr_group.system == False) # do not show system groups
    response.s3.pagination = True

    s3xrc.model.configure(db.pr_group_membership,
                          list_fields=["id",
                                       "person_id",
                                       "group_head",
                                       "description"])

    def group_postp(jr, output):
        if jr.representation in ("html", "popup"):
            if not jr.component:
                label = READ
            else:
                label = UPDATE
            linkto = shn_linkto(jr, sticky=True)("[id]")
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=linkto)
            ]
        return output
    response.s3.postp = group_postp

    output = shn_rest_controller("pr", "group",
        main="name",
        extra="description",
        rheader=lambda jr: shn_pr_rheader(jr,
            tabs = [(T("Team Details"), None),
                    (T("Address"), "address"),
                    (T("Contact Data"), "pe_contact"),
                    (T("Members"), "group_membership")]),
        sticky=True,
	listadd=False,
        deletable=False)

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def skill():
    "Select skills a volunteer has."
    return shn_rest_controller(module, "skill")


# -----------------------------------------------------------------------------
# TODO: Is resource a bad name, due to possible confusion with other usage?
def resource():
    "Select resources a volunteer has."
    return shn_rest_controller(module, "resource")

# -----------------------------------------------------------------------------
def shn_vol_rheader(jr):

    """ Volunteer registry page headers """

    if jr.representation == "html":

        if jr.component and jr.component_name in shn_vol_volunteer_data or \
            jr.method and jr.method == "view_map":
            tabs = [(T("Availablity"), "volunteer"),
                    (T("Teams"), "group_membership"),
                    (T("Skills"), "skill"),
                    (T("Show Location on Map"), "view_map")]
            _href = URL(r=request, f="person", args=[jr.id])
            link = A(T("Personal Data"), _href=_href, _class="action-btn")
        else:
            tabs = [(T("Basic Details"), None),
                    (T("Images"), "image"),
                    (T("Identity"), "identity"),
                    (T("Address"), "address"),
                    (T("Contact Data"), "pe_contact"),
                    (T("Presence Log"), "presence")]
            _href = URL(r=request, f="person", args=[jr.id, "volunteer"])
            link = A(T("Volunteer Info"), _href=_href, _class="action-btn")

        rheader_tabs = shn_rheader_tabs(jr, tabs)

        if jr.name == "person":

            _next = jr.here()
            _same = jr.same()

            person = jr.record

            if person:
                rheader = DIV(TABLE(

                    TR(TH(T("Name: ")),
                       vita.fullname(person),
                       TH(T("ID Label: ")),
                       "%(pe_label)s" % person,
                       TH(link)),

                    TR(TH(T("Date of Birth: ")),
                       "%s" % (person.date_of_birth or T("unknown")),
                       TH(T("Gender: ")),
                       "%s" % pr_gender_opts.get(person.gender, T("unknown")),
                       TH("")),

                    TR(TH(T("Nationality: ")),
                       "%s" % pr_nations.get(person.nationality, T("unknown")),
                       TH(T("Age Group: ")),
                       "%s" % pr_age_group_opts.get(person.age_group, T("unknown")),
                       TH("")),

                    #))
                    ), rheader_tabs)

                return rheader

    return None

