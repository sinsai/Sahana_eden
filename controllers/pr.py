# -*- coding: utf-8 -*-

"""
    Person Registry, controllers

    @author: nursix
"""

module = "pr"

# -----------------------------------------------------------------------------
# Options Menu (available in all Functions" Views)
def shn_menu():
    response.menu_options = [
        [T("Search for a Person"), False, URL(r=request, f="person", args="search_simple")],
        [T("Persons"), False, URL(r=request, f="person"), [
            [T("List"), False, URL(r=request, f="person")],
            [T("Add"), False, URL(r=request, f="person", args="create")],
        ]],
        [T("Groups"), False, URL(r=request, f="group"), [
            [T("List"), False, URL(r=request, f="group")],
            [T("Add"), False, URL(r=request, f="group", args="create")],
            [T("Group Memberships"), False, URL(r=request, f="group_membership")],
        ]]]
    if session.rcvars and "pr_person" in session.rcvars:
        selection = db.pr_person[session.rcvars["pr_person"]]
        if selection:
            selection = shn_pr_person_represent(selection.id)
            menu_person = [
                [str(T("Person:")) + " " + selection, False, URL(r=request, f="person", args="read"),[
                    [T("Basic Details"), False, URL(r=request, f="person", args="read")],
                    [T("Images"), False, URL(r=request, f="person", args="image")],
                    [T("Identity"), False, URL(r=request, f="person", args="identity")],
                    [T("Address"), False, URL(r=request, f="person", args="address")],
                    [T("Contact Data"), False, URL(r=request, f="person", args="pe_contact")],
                    [T("Presence Log"), False, URL(r=request, f="person", args="presence")],
            #        [T("Roles"), False, URL(r=request, f="person", args="role")],
            #        [T("Status"), False, URL(r=request, f="person", args="status")],
            #        [T("Group Memberships"), False, URL(r=request, f="person", args="group_membership")],
                ]]
            ]
            response.menu_options.extend(menu_person)

shn_menu()

# -----------------------------------------------------------------------------
def index():

    """ Module"s Home Page """

    try:
        module_name = s3.modules[module]["name_nice"]
    except:
        module_name = T("Person Registry")

    gender = []
    for g_opt in pr_person_gender_opts:
        count = db((db.pr_person.deleted==False) & (db.pr_person.opt_pr_gender==g_opt)).count()
        gender.append([str(pr_person_gender_opts[g_opt]), int(count)])

    age = []
    for a_opt in pr_person_age_group_opts:
        count = db((db.pr_person.deleted==False) & (db.pr_person.opt_pr_age_group==a_opt)).count()
        age.append([str(pr_person_age_group_opts[a_opt]), int(count)])

    total = int(db(db.pr_person.deleted==False).count())

    return dict(module_name=module_name, gender=gender, age=age, total=total)


# -----------------------------------------------------------------------------
def person():

    response.s3.pagination = True

    output = shn_rest_controller(module, "person",
        main="first_name",
        extra="last_name",
        rheader=shn_pr_rheader,
        rss=dict(
            title=shn_pr_person_represent,
            description="ID Label: %(pr_pe_label)s\n%(comment)s"
        ))

    shn_menu()
    return output

# -----------------------------------------------------------------------------
def group():
    response.s3.filter = (db.pr_group.system == False) # do not show system groups
    response.s3.pagination = True
    "RESTlike CRUD controller"
    return shn_rest_controller(module, "group",
                               main="group_name",
                               extra="group_description",
                               rheader=shn_pr_rheader,
                               deletable=False)

# -----------------------------------------------------------------------------
def image():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, "image")

# -----------------------------------------------------------------------------
def pe_contact():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, "pe_contact")

# -----------------------------------------------------------------------------
def address():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, "address")

# -----------------------------------------------------------------------------
def presence():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, "presence")

# -----------------------------------------------------------------------------
def identity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, "identity")

# -----------------------------------------------------------------------------
def group_membership():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, "group_membership")

# -----------------------------------------------------------------------------
def pentity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, "pentity")
# -----------------------------------------------------------------------------
def download():
    "Download a file."
    return response.download(request, db)

# -----------------------------------------------------------------------------
def tooltip():
    if "formfield" in request.vars:
        response.view = "pr/ajaxtips/%s.html" % request.vars.formfield
    return dict()

#
# -----------------------------------------------------------------------------
