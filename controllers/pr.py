# -*- coding: utf-8 -*-

#
# Person Registry, Identification, Tracking and Tracing system
#
# created 2009-07-24 by nursix
#

module = 'pr'

# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Search for a Person'), False, URL(r=request, f='person', args='search_simple')],
    [T('View/Edit Person Details'), False, URL(r=request, f='person', args='read'),[
        [T('Basic Details'), False, URL(r=request, f='person', args='read')],
        [T('Images'), False, URL(r=request, f='person', args='image')],
        [T('Identity'), False, URL(r=request, f='person', args='identity')],
        [T('Address'), False, URL(r=request, f='person', args='address')],
        [T('Contact Data'), False, URL(r=request, f='person', args='contact')],
        [T('Presence Log'), False, URL(r=request, f='person', args='presence')],
#        [T('Roles'), False, URL(r=request, f='person', args='role')],
#        [T('Status'), False, URL(r=request, f='person', args='status')],
        [T('Group Memberships'), False, URL(r=request, f='person', args='group_membership')],
    ]],
    [T('Add Person'), False, URL(r=request, f='person', args='create')],
    [T('Add Group'), False, URL(r=request, f='group', args='create')],
    [T('List Persons'), False, URL(r=request, f='person')],
    [T('List Groups'), False, URL(r=request, f='group')]
]

# S3 framework functions
def index():
    "Module's Home Page"
    gender = []
    for g_opt in pr_person_gender_opts:
        count = db((db.pr_person.deleted==False) & (db.pr_person.opt_pr_gender==g_opt)).count()
        gender.append([str(pr_person_gender_opts[g_opt]),count])
    age = []
    for a_opt in pr_person_age_group_opts:
        count = db((db.pr_person.deleted==False) & (db.pr_person.opt_pr_age_group==a_opt)).count()
        age.append([str(pr_person_age_group_opts[a_opt]),count])
    total = db(db.pr_person.deleted==False).count()
    return dict(module_name=module_name, gender=gender, age=age, total=total)

# Main controller functions
def person():
    crud.settings.delete_onaccept=shn_pentity_ondelete
    return shn_rest_controller(module, 'person', main='first_name', extra='last_name',
        pheader=shn_pr_pheader,
        list_fields=['id', 'first_name', 'middle_name', 'last_name', 'date_of_birth', 'opt_pr_nationality'],
        rss=dict(
            title=shn_pr_person_represent,
            description="ID Label: %(pr_pe_label)s\n%(comment)s"
        ),
        onaccept=lambda form: shn_pentity_onaccept(form, table=db.pr_person, entity_type=1))

def group():
    response.s3.filter = (db.pr_group.system==False) # do not show system groups
    crud.settings.delete_onaccept=shn_pentity_ondelete
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'group', main='group_name', extra='group_description',
        pheader=shn_pr_pheader,
        onaccept=lambda form: shn_pentity_onaccept(form, table=db.pr_group, entity_type=2),
        deletable=False)

def image():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'image')

def contact():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'contact')

def address():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'address')

def presence():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'presence')

def identity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'identity')

def group_membership():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'group_membership')

def pentity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'pentity')

#
# Interactive functions -------------------------------------------------------
#
def download():
    "Download a file."
    return response.download(request, db)

def tooltip():
    if 'formfield' in request.vars:
        response.view='pr/ajaxtips/%s.html' % request.vars.formfield
    return dict(module_name=module_name)
