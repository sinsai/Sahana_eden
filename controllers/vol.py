# -*- coding: utf-8 -*-

module = 'vol'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice

# Options Menu (available in all Functions)
response.menu_options = [
    [T('Projects'), False, URL(r=request, f='project'),[
        [T('Search'), False, URL(r=request, f='project', args='search_location')],
        [T('Add Project'), False, URL(r=request, f='project', args='create')],
    ]],
    [T('Persons'), False,  URL(r=request, f='person', args=['search_simple'],
                               vars={"_next":URL(r=request, f='person', args=['[id]','volunteer'])})],
]

def shn_vol_menu_ext():
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
                    ["%s %s" % (T('Project:'), selection.name), False, URL(r=request, f='project', args=['read', selection.name]),[
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
                    [T('Skills'), False, URL(r=request, f='person', args='skills')],
                    [T('Address'), False, URL(r=request, f='person', args='address')],
                    [T('Contact'), False, URL(r=request, f='person', args='contact')],
                    [T('Identity'), False, URL(r=request, f='person', args='identity')],
                ]]
            ]
            menu.extend(menu_person)
    response.menu_options = menu

shn_vol_menu_ext()

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def project():
    output = shn_rest_controller( module , 'project', pheader=shn_vol_project_pheader)
    shn_vol_menu_ext()
    return output

# Main controller functions
def person():
    db.pr_pd_general.est_age.readable=False
    db.pr_person.missing.default = False
    crud.settings.delete_onaccept = shn_pentity_ondelete
    output = shn_rest_controller('pr', 'person', main='first_name', extra='last_name',
        pheader=shn_pr_pheader,
        list_fields=['id', 'first_name', 'middle_name', 'last_name', 'date_of_birth', 'opt_pr_nationality'],
        rss=dict(
            title=shn_pr_person_represent,
            description="ID Label: %(pr_pe_label)s\n%(comment)s"
        ),
        onaccept=lambda form: shn_pentity_onaccept(form, table=db.pr_person, entity_type=1))
    shn_vol_menu_ext()
    return output

def position():
    return shn_rest_controller( module , 'position')

def volunteer():
    return shn_rest_controller( module , 'volunteer')

def skills():
    return shn_rest_controller( module , 'skills')

def hours():
    return shn_rest_controller( module , 'hours')
