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
    if session.rcvars and "org_project" in session.rcvars:
        selection = db.org_project[session.rcvars["org_project"]]
        if selection:
            menu_project = [
                ["%s %s" % (T("Project:"), selection.name), False, URL(r=request, f="project", args=[selection.id]),[
                    [T("Tasks"), False, URL(r=request, f="project", args=[str(selection.id), "task"])],
                    [T("Positions"), False, URL(r=request, f="project", args=[str(selection.id), "position"])],
                ]]
            ]
            menu.extend(menu_project)

    menu_teams = [
        [T("Teams"), False, URL(r=request, f="group"),[
            [T("List"), False, URL(r=request, f="group")],
            [T("Add"), False, URL(r=request, f="group", args="create", vars={"_next":URL(r=request, args=request.args, vars=request.vars)})],
        ]]
    ]
    menu.extend(menu_teams)
    if session.rcvars and "pr_group" in session.rcvars:
        selection = db.pr_group[session.rcvars["pr_group"]]
        if selection:
            selection = shn_pr_group_represent(selection.id)
            menu_teams = [
                ["%s %s" % (T("Team:"), selection), False, URL(r=request, f="group", args="read")],
            ]
            menu.extend(menu_teams)

    menu_persons = [
        [T("Persons"), False, URL(r=request, f="person", args=["search_simple"], vars={"_next":URL(r=request, f="person", args=["[id]", "volunteer"])}),[
            [T("List"), False, URL(r=request, f="person")],
            [T("Add"), False, URL(r=request, f="person", args="create")],
        ]]
    ]
    menu.extend(menu_persons)
    if session.rcvars and "pr_person" in session.rcvars:
        selection = db.pr_person[session.rcvars["pr_person"]]
        if selection:
            selection = shn_pr_person_represent(selection.id)
            menu_person = [
                ["%s %s" % (T("Person:"), selection), False, URL(r=request, f="person", args="read"),[
                    [T("Volunteer Data"), False, URL(r=request, f="volunteer")],
                    [T("Person Data"), False, URL(r=request, f="person")],
                    [T("View Map"), False, URL(r=request, f="view_map")],
                ]],
            ]
            menu.extend(menu_person)
    menu_skills = [
        [T("Skill Types"), False, URL(r=request, f="skill_types")],
    ]
    menu.extend(menu_skills)
    if auth.user is not None:
        menu_user = [
            [T("My Tasks"), False, URL(r=request, f="task", args="")],
        ]
        menu.extend(menu_user)
    response.menu_options = menu

shn_menu()


def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice

    return dict(module_name=module_name)


# -----------------------------------------------------------------------------
def person():

    """ Person Controller """

    db.pr_group_membership.group_id.label = T("Team Id")
    db.pr_group_membership.group_head.label = T("Team Head")

    resource = request.function
    
    db.pr_person.missing.default = False

    response.s3.pagination = True
    response.files.append(URL(r=request,c='static/multiselect',f='jquery.multiSelect.js'))
    response.files.append(URL(r=request,c='static/multiselect',f='jquery.multiSelect.css'))

    s3xrc.model.configure(db.pr_group_membership,
                          list_fields=["id",
                                       "group_id",
                                       "group_head",
                                       "description"])

    def person_postp(jr, output):
        if jr.representation in ("html", "popup"):
            if not jr.component:
                label = T("Details")
            else:
                label = T("Update")
            linkto = shn_linkto(jr, sticky=True)("[id]")
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=linkto)
            ]
        return output
    response.s3.postp = person_postp

    output = shn_rest_controller("pr", resource, 
        main="first_name", 
        extra="last_name",
        rheader=lambda jr: shn_pr_rheader(jr,
            tabs = [(T("Basic Details"), None),
                    (T("Images"), "image"),
                    (T("Identity"), "identity"),
                    (T("Address"), "address"),
                    (T("Contact Data"), "pe_contact"),
                    (T("Memberships"), "group_membership"),
                    (T("Presence Log"), "presence")]),
        sticky=True,
        rss=dict(
            title=shn_pr_person_represent,
            description="ID Label: %(pr_pe_label)s\n%(comment)s"
        ))

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def project():
    "RESTful CRUD controller"
    resource = request.function
    tablename = "org_%s" % (resource)
    table = db[tablename]
    
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
                                                                           ]
                                                                   ),
                                 sticky=True
                                )
    
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
    return shn_rest_controller(module, "skill_types")


# -----------------------------------------------------------------------------
def view_map():
    "Map Location of Volunteer"

    volunteer = {"feature_group" : "People"}
    html = gis.show_map(
                feature_groups = [volunteer],
                wms_browser = {"name" : "Risk Maps", "url" : "http://preview.grid.unep.ch:8080/geoserver/ows?service=WMS&request=GetCapabilities"},
                catalogue_overlays = True,
                catalogue_toolbar = True,
                toolbar = True,
                search = True,
                window = True,
                )

    return dict(map=html)


# -----------------------------------------------------------------------------
def volunteer():

    response.s3.pagination = True

    output = shn_rest_controller(module , "resource",
        rheader = lambda jr: shn_vol_volunteer_rheader(jr,
            tabs=[
                (T("Status Report"), None),
                (T("Resources"), "resource"),
                (T("Availablity"), "volunteer"),
                (T("Skills"), "skill")]),
        sticky=True)

    shn_menu()

    return output

def shn_vol_volunteer_rheader(jr, tabs=[]):

    if jr.name == "resource":
        if jr.representation == "html":
            _next = jr.here()
            _same = jr.same()
            rheader_tabs = shn_rheader_tabs(jr, tabs)
            resource = jr.record
            if resource:
                rheader = DIV(TABLE(), rheader_tabs)
                return rheader
    return None


# -----------------------------------------------------------------------------
def group():

    """ RESTful CRUD controller """
    resource = "group"
    table = "pr" + "_" + resource

    db.pr_group.opt_pr_group_type.label = T("Team Type")
    db.pr_group.group_description.label = T("Team Description")
    db.pr_group.group_name.label = T("Team Name")
    db.pr_group_membership.group_id.label = T("Team Id")
    db.pr_group_membership.group_head.label = T("Team Head")
 
    # CRUD Strings
    ADD_TEAM = T("Add Team")
    LIST_TEAMS = T("List Teams")
    s3.crud_strings[table] = Storage(
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
                label = T("Details")
            else:
                label = T("Update")
            linkto = shn_linkto(jr, sticky=True)("[id]")
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=linkto)
            ]
        return output
    response.s3.postp = group_postp

    output = shn_rest_controller("pr", "group",
        main="group_name",
        extra="group_description",
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
    "RESTlike CRUD controller"
    return shn_rest_controller(module, "skill")


# -----------------------------------------------------------------------------
def resource():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, "resource")
