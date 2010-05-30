# -*- coding: utf-8 -*-

"""
    Volunteer Management Module
"""

module = 'vol'

# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select().first().name_nice

# Options Menu (available in all Functions)
def shn_menu():
    menu = [
        [T('Projects'), False, URL(r=request, f='project'),[
            [T('Search'), False, URL(r=request, f='project', args='search_location')],
            [T('Add Project'), False, URL(r=request, f='project', args='create')],
        ]],
    ]
    if session.rcvars and 'vol_project' in session.rcvars:
        selection = db.vol_project[session.rcvars['vol_project']]
        if selection:
            menu_project = [
                    ["%s %s" % (T('Project:'), selection.name), False, URL(r=request, f='project', args=['read', selection.id]),[
                        [T('Tasks'), False, URL(r=request, f='project', args=[str(selection.id), 'task'])],
                        [T('Positions'), False, URL(r=request, f='project', args=[str(selection.id), 'position'])],
                    ]]
            ]
            menu.extend(menu_project)
    menu_persons = [
        [T('Persons'), False, URL(r=request, f='person', args=['search_simple'], vars={"_next":URL(r=request, f='person', args=['[id]','volunteer'])})]
    ]
    menu.extend(menu_persons)
    if session.rcvars and 'pr_person' in session.rcvars:
        selection = db.pr_person[session.rcvars['pr_person']]
        if selection:
            selection = shn_pr_person_represent(selection.id)
            menu_person = [
                ["%s %s" % (T('Person:'), selection), False, URL(r=request, f='person', args='read'),[
                    [T('Volunteer Status'), False, URL(r=request, f='person', args='volunteer')],
                    [T('Resources'), False, URL(r=request, f='person', args='resource')],
                    [T('Address'), False, URL(r=request, f='person', args='address')],
                    [T('Contact'), False, URL(r=request, f='person', args='contact')],
                    [T('Identity'), False, URL(r=request, f='person', args='identity')],
                ]]
            ]
            menu.extend(menu_person)
    if auth.user is not None:
        menu_user = [
            [T('My Tasks'), False, URL(r=request, f='mytasks', args='')]
        ]
        menu.extend(menu_user)
    response.menu_options = menu

shn_menu()


def index():

    """ Module's Home Page """

    return dict(module_name=module_name)


def project():

    """ Project Controller """

    resource = 'project'
    tablename = module + '_' + resource
    table = db[tablename]
    table.name.comment = SPAN("*", _class="req")
    table.description.comment = SPAN("*", _class="req")
    table.status.comment = SPAN("*", _class="req")

    output = shn_rest_controller( module , resource, pheader=shn_vol_project_pheader)
    shn_menu()
    return output


def person():

    """ Person Controller """

    db.pr_person.missing.default = False

    output = shn_rest_controller('pr', 'person', main='first_name', extra='last_name',
        pheader=shn_pr_pheader,
        list_fields=['id', 'first_name', 'middle_name', 'last_name', 'date_of_birth', 'opt_pr_nationality'],
        rss=dict(
            title=shn_pr_person_represent,
            description="ID Label: %(pr_pe_label)s\n%(comment)s"
        ))

    shn_menu()
    return output


def mytasks():

    """ Manage current user's tasks """

    my_person_id = None

    if auth.user is not None and auth.user.person_uuid:
        my_person_id = db(db.pr_person.uuid==auth.user.person_uuid).select(db.pr_person.id, limitby=(0,1))
        if my_person_id:
            my_person_id = my_person_id[0]

    if not my_person_id:
        session.error = T('No person record found for current user.')
        redirect(URL(r=request, f='index'))

    db.vol_task.person_id.default = my_person_id
    #db.vol_task.person_id.writable = False

    response.s3.filter = (db.vol_task.person_id==my_person_id)

    s3.crud_strings['vol_task'].title_list = T('My Tasks')
    s3.crud_strings['vol_task'].subtitle_list = T('Task List')

    return shn_rest_controller(module, 'task', listadd=False,
        list_fields=['id', 'vol_project_id', 'subject', 'priority', 'status'])
