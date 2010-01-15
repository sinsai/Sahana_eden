# -*- coding: utf-8 -*-

#
# MPR Missing Person Registry (Sahana Legacy)
#
# created 2009-08-06 by nursix
#
module = 'mpr'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Search for a Person'), False,  URL(r=request, f='person', args=['search_simple'])],
    [T('View/Edit Person Details'), False, URL(r=request, f='person', args='read'),[
        [T('Basic Details'), False, URL(r=request, f='person', args='read')],
        [T('Images'), False, URL(r=request, f='person', args='image')],
        [T('Identity'), False, URL(r=request, f='person', args='identity')],
        [T('Address'), False, URL(r=request, f='person', args='address')],
        [T('Contact Data'), False, URL(r=request, f='person', args='contact')],
        [T('Presence Log'), False, URL(r=request, f='person', args='presence')],
    ]],
    [T('Physical Description'), False, URL(r=request, f='person', args=['pd_general']),[
        [T('Appearance'), False, URL(r=request, f='person', args=['pd_general'])],
        [T('Head'), False, URL(r=request, f='person', args=['pd_head'])],
        [T('Face'), False, URL(r=request, f='person', args=['pd_face'])],
        [T('Teeth'), False, URL(r=request, f='person', args=['pd_teeth'])],
        [T('Body'), False, URL(r=request, f='person', args=['pd_body'])],
    ]]
    #[T('Report a Missing Person'), False,  URL(r=request, f='report_missing')],
    #[T('Edit a Missing Person'), False,  URL(r=request, f='edit_missing')],
    #[T('Report a Found Person'), False,  URL(r=request, f='report_found')],
    #[T('Reports'), False,  URL(r=request, f='missing_persons'),[
    #    [T('List Missing People'), False, URL(r=request, f='missing_persons')],
    #    [T('List Found People'), False, URL(r=request, f='found_persons')]
    #]]
]

def index():
    "Module's Home Page"
    return dict(module_name=module_name)

# Main controller functions
def person():
    db.pr_pd_general.est_age.readable=False
    db.pr_person.missing.default = True
    crud.settings.delete_onaccept = shn_pentity_ondelete
    return shn_rest_controller('pr', 'person', main='first_name', extra='last_name',
        pheader=shn_pr_pheader,
        list_fields=['id', 'first_name', 'middle_name', 'last_name', 'date_of_birth', 'opt_pr_nationality'],
        rss=dict(
            title=shn_pr_person_represent,
            description="ID Label: %(pr_pe_label)s\n%(comment)s"
        ),
        onaccept=lambda form: shn_pentity_onaccept(form, table=db.pr_person, entity_type=1))

def person_search():
    "Module's Home Page"
    return dict(module_name=module_name)

def report_missing():
    "Module's Home Page"
    return dict(module_name=module_name)

def edit_missing():
    "Module's Home Page"
    return dict(module_name=module_name)

def report_found():
    "Module's Home Page"
    return dict(module_name=module_name)

def missing_persons():
    "Module's Home Page"
    return dict(module_name=module_name)
def found_persons():
    "Module's Home Page"
    return dict(module_name=module_name)
