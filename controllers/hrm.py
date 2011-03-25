# -*- coding: utf-8 -*-

"""
    Human Resource Management

    @author: Dominic König <dominic AT aidiq DOT com>

"""

prefix = request.controller
resourcename = request.function

if prefix not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# =============================================================================
@auth.requires_login()
def shn_menu():
    """ Application Menu """

    ADMIN = auth.permission.ADMIN
    roles = session.s3.roles or []

    # Session Org
    if session.hrm is None:
        session.hrm = Storage()
    if session.hrm.org is None:
        query = (db.hrm_human_resource.person_id == db.pr_person.id) & \
                (db.hrm_human_resource.admin == True) & \
                (db.pr_person.uuid == session.auth.user.person_uuid)
        hr = db(query).select(db.hrm_human_resource.organisation_id,
                            limitby=(0, 1)).first()
        if hr:
            session.hrm.org = hr.organisation_id

    # Module Name
    try:
        module_name = deployment_settings.modules[prefix].name_nice
    except:
        module_name = T("Human Resources Management")

    response.title = module_name

    # Menu
    mode = request.get_vars.get("mode", None)
    if mode == "personal" or \
       ADMIN not in roles and not session.hrm.org:
        menu = [
            [T("Personal"), False, None,[
                [T("Profile"),
                 False, None],
            ]],
            #[T("Planner"), False, None,[
                #[T("Tasks"),
                 #False, None],
                #[T("Roster"),
                 #False, None],
            #]],
            #[T("Job Market"), False, None,[
                #[T("Vacancies"),
                 #False, None],
                #[T("Applications"),
                 #False, None],
            #]],
        ]
        if session.hrm.org or ADMIN in session.s3.roles:
            menu.append([T("Organisation"),
                         True, aURL(r=request, f="index")])
    else:
        menu = [
            [T("Staff"), False, None,[
                [T("New"),
                 False, aURL(p="create", r=request, f="human_resource",
                             args="create",
                             vars=dict(group="staff"))],
                [T("Search"),
                 False, aURL(r=request, f="human_resource",
                             args="search",
                             vars=dict(group="staff"))],
                [T("List All"),
                 False, aURL(r=request, f="human_resource",
                             vars=dict(group="staff"))],
            ]],
            [T("Volunteers"), False, None,[
                [T("New"),
                 False, aURL(p="create", r=request, f="human_resource",
                             args="create",
                             vars=dict(group="volunteer"))],
                [T("Search"),
                 False, aURL(r=request, f="human_resource",
                             args="search",
                             vars=dict(group="volunteer"))],
                [T("List All"),
                 False, aURL(r=request, f="human_resource",
                             vars=dict(group="volunteer"))],
            ]],
            #[T("Teams"), False, None,[
                #[T("New"),
                 #False, None],
                #[T("Search"),
                 #False, None],
                #[T("List All"),
                 #False, None],
            #]],
            #[T("Projects"), False, None,[
                #[T("New"),
                 #False, None],
                #[T("Search"),
                 #False, None],
                #[T("List All"),
                 #False, None],
                ##[T("Roster"),
                 ##False, None],
            #]],
            #[T("Job Market"), False, None,[
                #[T("Vacancies"),
                 #False, None],
                #[T("Applications"),
                 #False, None],
            #]],
        ]
        if ADMIN in session.s3.roles:
            menu.append(
                [T("Skills"), False, None,[
                    [T("New"),
                    False, None],
                    [T("Manage"),
                    False, None],
                ]],
            )
        menu.append(
            [T("Personal"),
               True, aURL(r=request, f="index",
                          vars=dict(mode="personal"))],
        )
    response.menu_options = menu

shn_menu()


# =============================================================================
def index():
    """ Dashboard """

    return dict(module_name=response.title)

# =============================================================================
def human_resource():
    """ Human Resource Controller """

    table = db.hrm_human_resource

    group = request.get_vars.get("group", None)
    if group == "staff":
        response.s3.filter = (table.type == 1)
    elif group == "volunteer":
        response.s3.filter = (table.type == 2)

    s3xrc.model.configure(table,
        list_fields = ["id",
                       "organisation_id",
                       "person_id",
                       "job_title",
                       "status"],
        create_next = URL(r=request, c="hrm", f="person",
                          args=["human_resource"],
                          vars={"human_resource.id":"[id]",
                                "group":group}))

    def prep(r, group):
        
        if r.interactive and not r.component:
            if r.method in ("create", "update") and \
               group is not None:
                if group == "staff":
                    r.table.type.default = 1
                elif group == "volunteer":
                    r.table.type.default = 2
                r.table.type.readable = False
                r.table.type.writable = False
        return True
    response.s3.prep = lambda r, group=group: prep(r, group)

    output = s3_rest_controller(prefix, resourcename)
    return output


# =============================================================================
def person():
    """ Person Controller """

    s3xrc.model.add_component("hrm", "human_resource",
        joinby=dict(pr_person="person_id"),
        multiple=True)

    table = db.pr_person
    table.pe_label.readable = False
    table.pe_label.writable = False
    table.missing.readable = False
    table.missing.writable = False
    table.age_group.readable = False
    table.age_group.writable = False
    table.country.readable = False
    table.country.writable = False
    table.religion.readable = False
    table.religion.writable = False
    table.marital_status.readable = False
    table.marital_status.writable = False
    table.tags.readable = False
    table.tags.writable = False

    if request.get_vars.get("human_resource.id", False):
        s3xrc.model.configure(db.hrm_human_resource,
                              insertable = False)

    tabs = [
            (T("Person Details"), None),
            (T("Human Resource"), "human_resource"),
            (T("Images"), "image"),
            #(T("Identity"), "identity"),
            (T("Address"), "address"),
            (T("Contact Data"), "pe_contact"),
            (T("Teams"), "group_membership"),
           ]

    output = s3_rest_controller("pr", resourcename,
                                native=False,
                                rheader=lambda r, tabs=tabs: \
                                               hrm_rheader(r, tabs))
    return output


# =============================================================================
def organisation():
    """ Organization Controller """

    s3xrc.model.add_component("hrm", "human_resource",
        joinby=dict(org_organisation="organisation_id"),
        multiple=True)

    output = s3_rest_controller("org", resourcename, native=False)
    return output


# =============================================================================
def site():
    """ Site Controller """

    return dict()


# =============================================================================
def skill():
    """ Skills Controller """

    output = s3_rest_controller(prefix, resourcename)
    return output


# =============================================================================
def help_pages():
    """ Help Pages """

    return dict()


# =============================================================================
def hrm_rheader(r, tabs=[]):
    """ Resource header for component views """

    rheader = None
    rheader_tabs = shn_rheader_tabs(r, tabs)

    if r.representation == "html":


        if r.name == "person":
            # Person Controller
            person = r.record
            if person:
                rheader = DIV(TABLE(

                    TR(TH("%s: " % T("Name")),
                       vita.fullname(person),
                       TH(""),
                       ""),

                    TR(TH("%s: " % T("Date of Birth")),
                       "%s" % (person.date_of_birth or T("unknown")),
                       TH(""),
                       ""),

                    ), rheader_tabs)

                return rheader

        elif r.name == "human_resource":
            # Human Resource Controller
            hr = r.record
            if hr:
                pass
            pass

        elif r.name == "organisation":
            # Organisation Controller
            org = r.record
            if org:
                pass
            pass

    return rheader


# END =========================================================================
