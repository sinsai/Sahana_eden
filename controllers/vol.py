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
    menu_persons = [
        [T("Persons"), False, URL(r=request, f="person", args=["search_simple"], vars={"_next":URL(r=request, f="person", args=["[id]", "volunteer"])})]
    ]
    menu.extend(menu_persons)
    if session.rcvars and "pr_person" in session.rcvars:
        selection = db.pr_person[session.rcvars["pr_person"]]
        if selection:
            selection = shn_pr_person_represent(selection.id)
            menu_person = [
                ["%s %s" % (T("Person:"), selection), False, URL(r=request, f="person"),[
                    [T("Volunteer Status"), False, URL(r=request, f="person", args="volunteer")],
                    [T("Resources"), False, URL(r=request, f="person", args="resource")],
                    [T("Address"), False, URL(r=request, f="person", args="address")],
                    [T("Contact"), False, URL(r=request, f="person", args="pe_contact")],
                    [T("Identity"), False, URL(r=request, f="person", args="identity")],
                    [T("Skill"), False, URL(r=request, f="person", args="skill")],
                    [T("Presence"), False, URL(r=request, f="person", args="presence")],   
                    [T("View Map"), False, URL(r=request, f="view_map")],                 
                ]]
            ]
            menu.extend(menu_person)
    if auth.user is not None:
        menu_user = [
            [T("My Tasks"), False, URL(r=request, f="task", args="")],
            [T("Skill Type"), False, URL(r=request, f="skill_types")],
        ]
        menu.extend(menu_user)
    response.menu_options = menu

shn_menu()


def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice

    return dict(module_name=module_name)


def person():

    """ Person Controller """

    resource = request.function
    
    db.pr_person.missing.default = False

    response.s3.pagination = True
    response.files.append(URL(r=request,c='static/multiselect',f='jquery.multiSelect.js'))
    response.files.append(URL(r=request,c='static/multiselect',f='jquery.multiSelect.css'))

    output = shn_rest_controller("pr", resource, main="first_name", extra="last_name",
        rheader=shn_pr_rheader,
        sticky=True,
        rss=dict(
            title=shn_pr_person_represent,
            description="ID Label: %(pr_pe_label)s\n%(comment)s"
        ))

    shn_menu()
    return output


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

def task():
    """ Manage current user's tasks """

    resource = request.function

    my_person_id = None

    if auth.user is not None and auth.user.person_uuid:
        my_person_id = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.id, limitby=(0,1))
        if my_person_id:
            my_person_id = my_person_id.first()

    if not my_person_id:
        session.error = T("No person record found for current user.")
        redirect(URL(r=request, f="index"))

    db.org_task.person_id.default = my_person_id
    #db.org_task.person_id.writable = False

    response.s3.filter = (db.org_task.person_id == my_person_id)

    s3.crud_strings["org_task"].title_list = T("My Tasks")
    s3.crud_strings["org_task"].subtitle_list = T("Task List")

    response.s3.pagination = True

    return shn_rest_controller("org", resource, listadd=False)

 
def skill_types():
    return shn_rest_controller(module, 'skill_types')

def view_map():
    "Map Location of Volunteer"

    volunteer = {"feature_group" : "People"}
    html = gis.show_map(
                feature_overlays = [volunteer],
                wms_browser = {"name" : "Risk Maps", "url" : "http://preview.grid.unep.ch:8080/geoserver/ows?service=WMS&request=GetCapabilities"},
                catalogue_overlays = True,
                catalogue_toolbar = True,
                toolbar = True,
                search = True,
                window = True,
                )

    return dict(map=html)
