# -*- coding: utf-8 -*-

"""
    Missing Person Registry - Controllers

    @author: nursix
"""

module = "mpr"

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Search for a Person'), False,  URL(r=request, f='person', args=['search_simple'])],
    [T('View/Edit Person Details'), False, URL(r=request, f='person', args='read'),[
        [T('Basic Details'), False, URL(r=request, f='person', args='read')],
        [T('Images'), False, URL(r=request, f='person', args='image')],
        [T('Identity'), False, URL(r=request, f='person', args='identity')],
        [T('Address'), False, URL(r=request, f='person', args='address')],
        [T('Contact Data'), False, URL(r=request, f='person', args='pe_contact')],
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

    module_name = deployment_settings.modules[module].name_nice

    return dict(module_name=module_name)

# Main controller functions
def person():
    db.pr_pd_general.est_age.readable=False
    db.pr_person.missing.default = True
    return shn_rest_controller('pr', 'person', main='first_name', extra='last_name',
        rheader=shn_pr_rheader,
        rss=dict(
            title=shn_pr_person_represent,
            description="ID Label: %(pr_pe_label)s\n%(comment)s"
        ))

def person_search():
    ""
    return dict()

def report_missing():
    ""
    return dict()

def edit_missing():
    ""
    return dict()

def report_found():
    ""
    return dict()

def missing_persons():
    ""
    return dict()

def found_persons():
    ""
    return dict()
