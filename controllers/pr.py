# -*- coding: utf-8 -*-

"""
    Person Registry, controllers

    @author: nursix
"""
from lxml import *
#exec("import applications.%s.modules.s3xrc " %(request.application))
module = "pr"

module = request.controller

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
        ]]]
    menu_selected = []
    if session.rcvars and "pr_group" in session.rcvars:
        group = db.pr_group
        query = (group.id == session.rcvars["pr_group"])
        record = db(query).select(group.id, group.group_name, limitby=(0, 1)).first()
        if record:
            name = record.group_name
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

    """ Module"s Home Page """

    try:
        module_name = deployment_settings.modules[module].name_nice
    except:
        module_name = T("Person Registry")

    gender = []
    for g_opt in pr_person_gender_opts:
        count = db((db.pr_person.deleted == False) & \
                   (db.pr_person.opt_pr_gender == g_opt)).count()
        gender.append([str(pr_person_gender_opts[g_opt]), int(count)])

    age = []
    for a_opt in pr_person_age_group_opts:
        count = db((db.pr_person.deleted == False) & \
                   (db.pr_person.opt_pr_age_group == a_opt)).count()
        age.append([str(pr_person_age_group_opts[a_opt]), int(count)])

    total = int(db(db.pr_person.deleted == False).count())
    f=file("/home/shikhar/Desktop/newimport.xml","rb")
    xmlstr=f.read()
    k=etree.fromstring(xmlstr)
    try:
    	    s3xrc.import_xml('pr','person',2,k)
	    stat='success'
    except:
	    stat='failure'
    '''l=list()
    for s in k:
	    l.append(s)
    
    #k=l
    k=XRequest()
    import_xml(k)'''
    return dict(k=k,stat=stat,xmlstr=xmlstr,module_name=module_name, gender=gender, age=age, total=total)


# -----------------------------------------------------------------------------
def person():

    """ RESTful CRUD controller """

    resource = request.function
    
    response.s3.pagination = True

    s3xrc.model.configure(db.pr_group_membership,
                          list_fields=["id",
                                       "group_id",
                                       "group_head",
                                       "description"])

    def person_postp(jr, output):
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
    response.s3.postp = person_postp

    output = shn_rest_controller(module, resource,
                main="first_name",
                extra="last_name",
                rheader=lambda jr: shn_pr_rheader(jr,
                    tabs = [(T("Basic Details"), None),
                            (T("Images"), "image"),
                            (T("Identity"), "identity"),
                            (T("Address"), "address"),
                            (T("Contact Data"), "pe_contact"),
                            (T("Memberships"), "group_membership"),
                            (T("Presence Log"), "presence"),
                            (T("Subscriptions"), "pe_subscription")
                            ]),
                sticky=True)

    shn_menu()
    return output

# -----------------------------------------------------------------------------
def group():

    """ RESTful CRUD controller """

    resource = request.function
    
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

    output = shn_rest_controller(module, resource,
                main="group_name",
                extra="group_description",
                rheader=lambda jr: shn_pr_rheader(jr,
                    tabs = [(T("Group Details"), None),
                            (T("Address"), "address"),
                            (T("Contact Data"), "pe_contact"),
                            (T("Members"), "group_membership")]),
                sticky=True,
                deletable=False)

    shn_menu()
    return output

# -----------------------------------------------------------------------------
def image():
    "RESTful CRUD controller"
    resource = request.function
    return shn_rest_controller(module, resource)

# -----------------------------------------------------------------------------
def pe_contact():
    "RESTful CRUD controller"
    resource = request.function
    return shn_rest_controller(module, resource)

# -----------------------------------------------------------------------------
def address():
    "RESTful CRUD controller"
    resource = request.function
    return shn_rest_controller(module, resource)

# -----------------------------------------------------------------------------
def presence():
    "RESTful CRUD controller"
    resource = request.function
    return shn_rest_controller(module, resource)

# -----------------------------------------------------------------------------
def identity():
    "RESTful CRUD controller"
    resource = request.function
    return shn_rest_controller(module, resource)

# -----------------------------------------------------------------------------
def group_membership():
    "RESTful CRUD controller"
    resource = request.function
    return shn_rest_controller(module, resource)

# -----------------------------------------------------------------------------
def pentity():
    "RESTful CRUD controller"
    resource = request.function
    return shn_rest_controller(module, resource)

# -----------------------------------------------------------------------------
def download():

    """ Download a file. """

    return response.download(request, db)

# -----------------------------------------------------------------------------
def tooltip():

    """ Ajax tooltips """

    if "formfield" in request.vars:
        response.view = "pr/ajaxtips/%s.html" % request.vars.formfield
    return dict()

#
# -----------------------------------------------------------------------------
