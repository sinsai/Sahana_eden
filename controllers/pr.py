# -*- coding: utf-8 -*-

#
# VITA - Person Registry, Identification, Tracking and Tracing system
#
# created 2009-07-24 by nursix
#

module = 'pr'

# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Search for a Person'), False, URL(r=request, f='person', args='search_simple')],
    [T('Person Details'), False, URL(r=request, f='person_details'),[
        [T('Basic Details'), False, URL(r=request, f='person', args='view')],
        [T('Adress'), False, URL(r=request, f='person', args='address')],
        [T('Contact Data'), False, URL(r=request, f='person', args='contact')],
        [T('Images'), False, URL(r=request, f='person', args='image')],
        [T('Groups'), False, URL(r=request, f='person', args='group')],
        [T('Status'), False, URL(r=request, f='person', args='status')],
        [T('Presence'), False, URL(r=request, f='person', args='presence')],
    ]],
    [T('Register Persons'), False, URL(r=request, f='person'),[
        [T('Add Individual'), False, URL(r=request, f='person', args='create')],
        [T('Register Presence'), False, URL(r=request, f='presence_person', args='create')],
        [T('Add Group'), False, URL(r=request, f='group', args='create')],
        [T('Add Group Membership'), False, URL(r=request, f='group_membership', args='create')],
    ]],
    [T('List Persons'), False, URL(r=request, f='person'),[
        [T('List Individuals'), False, URL(r=request, f='person')],
#        [T('List Person Details'), False, URL(r=request, f='person_details')],
        [T('List Person Images'), False, URL(r=request, f='image_person')],
        [T('List Identities'), False, URL(r=request, f='identity')],
        [T('List Groups'), False, URL(r=request, f='group')],
        [T('List Group Memberships'), False, URL(r=request, f='group_membership')],
        [T('List Presence Records'), False, URL(r=request, f='presence_person')],
    ]],
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

# Main controller functions
def person():

    if request.vars.format:
        representation = str.lower(request.vars.format)
    else:
        representation = "html"

    if representation=="html":
        if len(request.args) > 0:
            if not request.args[0].isdigit():
                method = str.lower(request.args[0])
                try:
                    record_id = request.args[1]
                except:
                    record_id = None
                if method=="search_simple":
                    if request.vars.next:
                        next = str.lower(request.vars.next)
                    else:
                        next = "view"
                    response.view = '%s/person_search.html' % module
                    title = T('Search for a Person')
                    subtitle = T('Matching Records')
                    form = FORM(TABLE(
                            TR(T('Name and/or ID Label: '),INPUT(_type="text",_name="label",_size="40")),
                            TR("",INPUT(_type="submit",_value="Search"))
                            ))
                    items = None
                    if form.accepts(request.vars,session):
                        results = shn_pr_get_person_id(form.vars.label)
                        rows = None
                        if results:
                            rows = db(db.pr_person.id.belongs(results)).select(
                                db.pr_person.id,
                                db.pr_person.pr_pe_label,
                                db.pr_person.first_name,
                                db.pr_person.middle_name,
                                db.pr_person.last_name,
                                db.pr_person.opt_pr_gender,
                                db.pr_person.opt_pr_age_group,
                                db.pr_person.date_of_birth)
                        if rows:
                            records = []
                            for row in rows:
                                records.append(TR(
                                    row.pr_pe_label or '[no label]',
                                    A(row.first_name, _href=URL(r=request, c='pr', f='person', args='%s/%s' % (next, row.id))),
                                    row.middle_name,
                                    row.last_name,
                                    row.opt_pr_gender and pr_person_gender_opts[row.opt_pr_gender] or 'unknown',
                                    row.opt_pr_age_group and pr_person_age_group_opts[row.opt_pr_age_group] or 'unknown',
                                    row.date_of_birth or 'unknown'
                                    ))
                            items=DIV(TABLE(THEAD(TR(
                                TH("ID Label"),
                                TH("First Name"),
                                TH("Middle Name"),
                                TH("Last Name"),
                                TH("Gender"),
                                TH("Age Group"),
                                TH("Date of Birth"))),
                                TBODY(records), _id='list', _class="display"))
                    return dict(title=title,subtitle=subtitle,form=form,vars=form.vars,items=items)

                elif method=="clear":
                    # Clear current selection
                    del session['pr_person']
                    redirect(URL(r=request, c='pr', f='person', args='search_simple'))
                elif method=="view":
                    # view person record (the most interesting information)
                    shn_pr_select_person(record_id)
                    if not session.pr_person:
                        redirect(URL(r=request, c='pr', f='person', args='search_simple'))

                    response.view = '%s/person.html' % module

                    title='Personal Data'
                    subtitle='Details'
                    return dict(title=title, subtitle=subtitle, pheader=shn_pr_person_header(session.pr_person))
                elif method=="edit":
                    # Edit basic details
                    shn_pr_select_person(record_id)
                    if not session.pr_person:
                        request.vars.next=method
                        redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))

                    response.view = '%s/person.html' % module

                    title=('Person Details')
                    subtitle='Details'
                    return dict(title=title, subtitle=subtitle, pheader=shn_pr_person_header(session.pr_person))
                elif method=="presence":
                    # View, edit or add presence information
                    shn_pr_select_person(record_id)
                    if not session.pr_person:
                        request.vars.next=method
                        redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))

                    response.view = '%s/person.html' % module

                    title=('Tracing data of Person %s' % session.pr_person)
                    subtitle='Details'
                    return dict(title=title, subtitle=subtitle, pheader=shn_pr_person_header(session.pr_person))
                elif method=="image":
                    # View, edit or add images
                    shn_pr_select_person(record_id)
                    if not session.pr_person:
                        request.vars.next=method
                        redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))

                    response.view = '%s/person.html' % module

                    title=('Images of Person %s' % session.pr_person)
                    subtitle='Details'
                    return dict(title=title, subtitle=subtitle, pheader=shn_pr_person_header(session.pr_person))
                elif method=="identity":
                    # View, edit or add identities
                    shn_pr_select_person(record_id)
                    if not session.pr_person:
                        request.vars.next=method
                        redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))

                    response.view = '%s/person.html' % module

                    title=('Identities of Person %s' % session.pr_person)
                    subtitle='Details'
                    return dict(title=title, subtitle=subtitle, pheader=shn_pr_person_header(session.pr_person))
                elif method=="address":
                    # View, edit or add addresses
                    shn_pr_select_person(record_id)
                    if not session.pr_person:
                        request.vars.next=method
                        redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))

                    response.view = '%s/person.html' % module

                    title=('Addresses of Person %s' % session.pr_person)
                    subtitle='Details'
                    return dict(title=title, subtitle=subtitle, pheader=shn_pr_person_header(session.pr_person))
                elif method=="contact":
                    # View, edit or add contact information
                    shn_pr_select_person(record_id)
                    if not session.pr_person:
                        request.vars.next=method
                        redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))

                    response.view = '%s/person.html' % module

                    title=('Contact information of Person %s' % session.pr_person)
                    subtitle='Details'
                    return dict(title=title, subtitle=subtitle, pheader=shn_pr_person_header(session.pr_person))
                elif method=="status":
                    # View, edit or add status information
                    shn_pr_select_person(record_id)
                    if not session.pr_person:
                        request.vars.next=method
                        redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))

                    response.view = '%s/person.html' % module

                    title=('Status information of Person %s' % session.pr_person)
                    subtitle='Details'
                    return dict(title=title, subtitle=subtitle, pheader=shn_pr_person_header(session.pr_person))
                elif method=="group":
                    # View, edit or add group memberships
                    shn_pr_select_person(record_id)
                    if not session.pr_person:
                        request.vars.next=method
                        redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))

                    response.view = '%s/person.html' % module

                    title=('Group Memberships of Person %s' % session.pr_person)
                    subtitle='Details'
                    return dict(title=title, subtitle=subtitle, pheader=shn_pr_person_header(session.pr_person))
                else:
                    # other method => fallback to Rest controller
                    pass
        else:
            # no method => default to list action via REST
            pass
    else:
        # representation other than HTML
        pass

    # Default CRUD action: forward to REST controller
    crud.settings.delete_onvalidation=shn_pentity_ondelete
    return shn_rest_controller(module, 'person', main='first_name', extra='last_name', onvalidation=lambda form: shn_pentity_onvalidation(form, table='pr_person', entity_class=1))

def group():
    crud.settings.delete_onvalidation=shn_pentity_ondelete
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'group', main='group_name', extra='group_description', onvalidation=lambda form: shn_pentity_onvalidation(form, table='pr_group', entity_class=2))

def person_details():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'person_details')

def image():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'image')
def image_person():
    db.pr_image.pr_pe_id.requires = IS_NULL_OR(IS_PE_ID(db, pr_pentity_class_opts, filter_opts=(1,)))
    request.filter=(db.pr_image.pr_pe_id==db.pr_pentity.id)&(db.pr_pentity.opt_pr_pentity_class==1)
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'image')

def identity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'identity')

def presence():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'presence')
def presence_person():
    db.pr_presence.pr_pe_id.requires = IS_NULL_OR(IS_PE_ID(db, pr_pentity_class_opts, filter_opts=(1,)))
    request.filter=(db.pr_presence.pr_pe_id==db.pr_pentity.id)&(db.pr_pentity.opt_pr_pentity_class==1)
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'presence')

def group_membership():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'group_membership')

#def image():
#    "RESTlike CRUD controller"
#    return shn_rest_controller(module, 'image')
#def presence():
#    "RESTlike CRUD controller"
#    return shn_rest_controller(module, 'presence')
#def pentity():
#    "RESTlike CRUD controller"
#    return shn_rest_controller(module, 'pentity', main='tag_label', listadd=False, deletable=False, editable=False)

#
# Interactive functions -------------------------------------------------------
#
def download():
    "Download a file."
    return response.download(request, db) 
