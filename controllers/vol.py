# -*- coding: utf-8 -*-

module = 'vol'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice

# Options Menu (available in all Functions)
response.menu_options = [
    [T('Projects'), False, URL(r=request, f='project'),[
        [T('Add Project'), False, URL(r=request, f='project', args='create')],
        [T('Search by Location'), False, URL(r=request, f='project', args='search_location')],
    ]],
    [T('Selected Project'), False, URL(r=request, f='project', args='read'),[
        [T('Positions'), False, URL(r=request, f='project', args='position')],
        [T('Tasks'), False, URL(r=request, f='project', args='task')],
    ]],
    [T('Select Person'), False,  URL(r=request, f='person', args=['search_simple'],
                                     vars={"_next":URL(r=request, f='person', args=['[id]','volunteer'])})],
    [T('Selected Person'), False, URL(r=request, f='person', args='read'),[
        [T('Volunteer Status'), False, URL(r=request, f='person', args='volunteer')],
        [T('Skills'), False, URL(r=request, f='person', args='skills')],
        [T('Address'), False, URL(r=request, f='person', args='address')],
        [T('Contact Info'), False, URL(r=request, f='person', args='contact')],
        [T('Identity'), False, URL(r=request, f='person', args='identity')],
    ]],
#        [T('Positions'), False, URL(r=request, f='position'),[
#            [T('Add Position'), False, URL(r=request, f='position', args='create')],
#        ]],
#        [T('Volunteers'), False, URL(r=request, f='volunteer'),[
#            [T('Add Volunteer'), False, URL(r=request, f='volunteer', args='create')],
#        ]],
#        [T('Skills'), False, URL(r=request, f='skills'),[
#            [T('Add Skills'), False, URL(r=request, f='skills', args='create')],
#        ]],
#        [T('Hours'), False, URL(r=request, f='hours'),[
#            [T('Add Hours'), False, URL(r=request, f='hours', args='create')],
#        ]],
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def project():
    return shn_rest_controller( module , 'project', pheader=shn_vol_project_pheader)

# Main controller functions
def person():
    db.pr_pd_general.est_age.readable=False
    db.pr_person.missing.default = False
    crud.settings.delete_onaccept = shn_pentity_ondelete
    return shn_rest_controller('pr', 'person', main='first_name', extra='last_name',
        pheader=shn_pr_pheader,
        list_fields=['id', 'first_name', 'middle_name', 'last_name', 'date_of_birth', 'opt_pr_nationality'],
        rss=dict(
            title=shn_pr_person_represent,
            description="ID Label: %(pr_pe_label)s\n%(comment)s"
        ),
        onaccept=lambda form: shn_pentity_onaccept(form, table=db.pr_person, entity_type=1))

def position():
    return shn_rest_controller( module , 'position')

def volunteer():
    return shn_rest_controller( module , 'volunteer')

def skills():
    return shn_rest_controller( module , 'skills')

def hours():
    return shn_rest_controller( module , 'hours')
