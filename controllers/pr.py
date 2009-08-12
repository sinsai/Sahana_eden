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
    [T('Search for a Person'), False, URL(r=request, f='person_search')],
    [T('Register Persons'), False, URL(r=request, f='person'),[
        [T('Add Individual'), False, URL(r=request, f='person', args='create')],
        [T('Register Presence'), False, URL(r=request, f='presence_person', args='create')],
        [T('Add Group'), False, URL(r=request, f='group', args='create')],
        [T('Add Group Membership'), False, URL(r=request, f='group_membership', args='create')],
    ]],
    [T('Person Details'), False, URL(r=request, f='person_details'),[
        [T('Add Details'), False, URL(r=request, f='person_details', args='create')],
        [T('Add Image'), False, URL(r=request, f='image_person', args='create')],
        [T('Add Identity'), False, URL(r=request, f='identity', args='create')],
    ]],
#        [T('Add Image'), False, URL(r=request, f='image_person', args='create')],
#        [T('Add Identity'), False, URL(r=request, f='identity', args='create')],
#        [T('List Persons'), False, URL(r=request, f='person')],
#        [T('List Images'), False, URL(r=request, f='image_person')],
#        [T('List Identities'), False, URL(r=request, f='identity')]
    [T('List Persons'), False, URL(r=request, f='person'),[
        [T('List Individuals'), False, URL(r=request, f='person')],
        [T('List Person Details'), False, URL(r=request, f='person_details')],
        [T('List Person Images'), False, URL(r=request, f='image_person')],
        [T('List Identities'), False, URL(r=request, f='identity')],
        [T('List Groups'), False, URL(r=request, f='group')],
        [T('List Group Memberships'), False, URL(r=request, f='group_membership')],
        [T('List Presence Records'), False, URL(r=request, f='presence_person')],
    ]],
    # Person Entities Menu is to be removed!
#    [T('Person Entities'), False, '#',[
#        [T('List Entities'), False, URL(r=request, f='pentity')],
#        [T('Add Image To Entity'), False, URL(r=request, f='image', args='create')],
#        [T('List Images'), False, URL(r=request, f='image')],
#        [T('Add Presence Record'), False, URL(r=request, f='presence', args='create')],
#        [T('List Presence Records'), False, URL(r=request, f='presence')]
#    ]]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

# RESTlike CRUD functions
def person():
    crud.settings.delete_onvalidation=shn_pentity_ondelete
    "RESTlike CRUD controller"
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

def person_search():
    "Find a person by name or ID tag label."

    response.view = '%s/person_search.html' % module

    title = T('Search for a Person')
    subtitle = T('Matching Records')

    form = FORM(TABLE(
            TR(T('Name and/or Label'),INPUT(_type="text",_name="label",_size="40")),
            TR("",INPUT(_type="submit",_value="Search"))
            ))

    items = None
    
    if form.accepts(request.vars,session):
        #rows = shn_pr_person_find(form.vars.label, form.vars.first_name, form.vars.last_name)
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
#                    row.id,
                    row.pr_pe_label or '[no label]',
                    A(row.first_name, _href=URL(r=request, c='pr', f='person', args='%s' % row.id)),
                    row.middle_name,
                    row.last_name,
                    row.opt_pr_gender and pr_person_gender_opts[row.opt_pr_gender] or 'unknown',
                    row.opt_pr_age_group and pr_person_age_group_opts[row.opt_pr_age_group] or 'unknown',
                    row.date_of_birth or 'unknown'
                    ))
                
            items=DIV(TABLE(THEAD(TR(
#                TH("ID"),
                TH("ID Label"),
                TH("First Name"),
                TH("Middle Name"),
                TH("Last Name"),
                TH("Gender"),
                TH("Age Group"),
                TH("Date of Birth"))),
                TBODY(records), _id='list', _class="display"))

    return dict(title=title,subtitle=subtitle,form=form,vars=form.vars,items=items)
