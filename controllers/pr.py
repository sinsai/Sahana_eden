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
    [T('View/Edit Person Details'), False, URL(r=request, f='person', args='view'),[
#        [T('Basic Details'), False, URL(r=request, f='person', args='view')],
        [T('Images'), False, URL(r=request, f='person', args='image')],
        [T('Identity'), False, URL(r=request, f='person', args='identity')],
        [T('Address'), False, URL(r=request, f='person', args='address')],
        [T('Contact Data'), False, URL(r=request, f='person', args='contact')],
        [T('Presence Log'), False, URL(r=request, f='person', args='presence')],
#        [T('Roles'), False, URL(r=request, f='person', args='role')],
#        [T('Status'), False, URL(r=request, f='person', args='status')],
        [T('Group Memberships'), False, URL(r=request, f='person', args='group_membership')],
    ]],
#    [T('Add Person Details'), False, URL(r=request, f='person'),[
#        [T('Add Image'), False, URL(r=request, f='image_person', args='create')],
#        [T('Add Identity'), False, URL(r=request, f='identity', args='create')],
#        [T('Add Address'), False, URL(r=request, f='address', args='create')],
#        [T('Add Contact Information'), False, URL(r=request, f='contact', args='create')],
#        [T('Add Presence Log Entry'), False, URL(r=request, f='presence_person', args='create')],
#        [T('Add Group Membership'), False, URL(r=request, f='group_membership', args='create')],
#    ]],
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

    if request.vars.format:
        representation = str.lower(request.vars.format)
    else:
        representation = "html"

    if len(request.args) > 0 and not request.args[0].isdigit():
        # Check method
        method = str.lower(request.args[0])

        # Check if record_id is submitted
        try:
            record_id = request.args[1]
        except:
            record_id = None

        # Simple search and select --------------------------------------------
        if method=="search_simple":
            if representation=="html":

                # Check for redirection
                if request.vars.next:
                    next = str.lower(request.vars.next)
                else:
                    next = "view"

                # Custom view
                response.view = '%s/person_search.html' % module

                # Title and subtitle
                title = T('Search for a Person')
                subtitle = T('Matching Records')

                # Select form
                form = FORM(TABLE(
                        TR(T('Name and/or ID Label: '),INPUT(_type="text",_name="label",_size="40"), A(SPAN("[Help]"), _class="tooltip", _title=T("Name and/or ID Label|To search for a person, enter any of the first, middle or last names and/or the ID label of a person, separated by spaces. You may use % as wildcard."))),
                        TR("",INPUT(_type="submit",_value="Search"))
                        ))

                # Accept action
                items = None
                if form.accepts(request.vars,session):

                    # Get matching person ID's
                    results = shn_pr_get_person_id(form.vars.label)

                    # Read records for matching ID's
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

                    # Build table rows from matching records
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

                # Return to the view
                return dict(title=title,subtitle=subtitle,form=form,vars=form.vars,items=items)

            else: # other representation
                pass

        # Clear current selection ---------------------------------------------
        elif method=="clear":

            del session['pr_person']
            redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))

        # View or edit basic person data --------------------------------------
        elif method=="view":
            if representation=="html":

                # Check for selected person or redirect to search form
                shn_pr_select_person(record_id)
                if not session.pr_person:
                    request.vars.next=method
                    redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))
                else:
                    pheader = shn_pr_person_header(session.pr_person, next=method)

                # Set response view
                response.view = '%s/person.html' % module

                # Add title and subtitle
                title=T('Person')
                subtitle=T('Basic Details')
                output=dict(title=title, subtitle=subtitle, pheader=pheader)

                items=None

                output.update(dict(items=items))
                return output

            else: # other representation
                pass

        # View, add or edit presence information ------------------------------
        elif method=="presence":
            if representation=="html":

                # Check for selected person or redirect to search form
                shn_pr_select_person(record_id)
                if not session.pr_person:
                    request.vars.next=method
                    redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))
                else:
                    pheader = shn_pr_person_header(session.pr_person, next=method)

                # Set response view
                response.view = '%s/person.html' % module

                # Add title and subtitle
                title=T('Person')
                subtitle=T('Presence Log')
                output=dict(title=title, subtitle=subtitle, pheader=pheader)

                # Which fields?
                fields = [
                        db.pr_presence.id,
                        db.pr_presence.time,
                        db.pr_presence.location,
                        db.pr_presence.location_details,
                        db.pr_presence.lat,
                        db.pr_presence.lon,
                        db.pr_presence.opt_pr_presence_condition,
                        db.pr_presence.origin,
                        db.pr_presence.destination,
                ]

                form = shn_pr_add_details_to_person_form(session.pr_person,db.pr_presence)
                if form:
                    formtitle = T('Add Log Entry')
                    if form.accepts(request.vars,session):
                        shn_audit_create(form, 'pr_presence', representation)
                        response.flash="Log Entry added"
                    elif form.errors:
                        response.flash="Error in the form"

                    output.update(dict(formtitle=formtitle, form=form))

                # Get list
                sublist = shn_pr_person_sublist(request, 'presence', session.pr_person, fields=fields, orderby=~db.pr_presence.time)

                if sublist:
                    output.update(sublist)

                return output

            else: # other representation
                pass

        # View, add or edit images --------------------------------------------
        elif method=="image":
            if representation=="html":

                # Check for selected person or redirect to search form
                shn_pr_select_person(record_id)
                if not session.pr_person:
                    request.vars.next=method
                    redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))
                else:
                    pheader = shn_pr_person_header(session.pr_person, next=method)

                # Set response view
                response.view = '%s/person.html' % module

                # Add title and subtitle
                title=T('Person')
                subtitle=T('Available Images')
                output=dict(title=title, subtitle=subtitle, pheader=pheader)

                # Which fields?
                fields = [
                        db.pr_image.id,
                        db.pr_image.opt_pr_image_type,
                        db.pr_image.image,
                        db.pr_image.title,
                        db.pr_image.description,
                ]

                form = shn_pr_add_details_to_person_form(session.pr_person,db.pr_image)
                if form:
                    formtitle = T('Add Image')
                    if form.accepts(request.vars,session):
                        shn_audit_create(form, 'pr_image', representation)
                        response.flash="Image added"
                    elif form.errors:
                        response.flash="Error in the form"

                    output.update(dict(formtitle=formtitle, form=form))

                # Get list
                sublist = shn_pr_person_sublist(request, 'image', session.pr_person, fields=fields)

                if sublist:
                    output.update(sublist)

                return output

            else: # other representation
                pass

        # View, add or edit identity information ------------------------------
        elif method=="identity":
            if representation=="html":

                # Check for selected person or redirect to search form
                shn_pr_select_person(record_id)
                if not session.pr_person:
                    request.vars.next=method
                    redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))
                else:
                    pheader = shn_pr_person_header(session.pr_person, next=method)

                # Set response view
                response.view = '%s/person.html' % module

                # Add title and subtitle
                title=T('Person')
                subtitle=T('Known Identities')
                output=dict(title=title, subtitle=subtitle, pheader=pheader)

                # Which fields?
                fields = [
                        db.pr_identity.id,
                        db.pr_identity.opt_pr_id_type,
                        db.pr_identity.type,
                        db.pr_identity.value,
                        db.pr_identity.country_code,
                        db.pr_identity.ia_name,
                ]

                form = shn_pr_add_details_to_person_form(session.pr_person,db.pr_identity)
                if form:
                    formtitle = T('Add Identity')
                    if form.accepts(request.vars,session):
                        shn_audit_create(form, 'pr_identity', representation)
                        response.flash="Identity added"
                    elif form.errors:
                        response.flash="Error in the form"

                    output.update(dict(formtitle=formtitle, form=form))

                # Get list
                sublist = shn_pr_person_sublist(request, 'identity', session.pr_person, fields=fields)

                if sublist:
                    output.update(sublist)

                return output

            else: # other representation
                pass

        # View, add or edit addresses -----------------------------------------
        elif method=="address":
            if representation=="html":

                # Check for selected person or redirect to search form
                shn_pr_select_person(record_id)
                if not session.pr_person:
                    request.vars.next=method
                    redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))
                else:
                    pheader = shn_pr_person_header(session.pr_person, next=method)

                # Set response view
                response.view = '%s/person.html' % module

                # Add title and subtitle
                title=T('Person')
                subtitle=T('Addresses')
                output=dict(title=title, subtitle=subtitle, pheader=pheader)

                # Which fields?
                fields = [
                        db.pr_address.id,
                        db.pr_address.opt_pr_address_type,
                        db.pr_address.co_name,
                        db.pr_address.street1,
                        db.pr_address.postcode,
                        db.pr_address.city,
                        db.pr_address.opt_pr_country,
                ]

                form = shn_pr_add_details_to_person_form(session.pr_person,db.pr_address)
                if form:
                    formtitle = T('Add Address')
                    if form.accepts(request.vars,session):
                        shn_audit_create(form, 'pr_address', representation)
                        response.flash="Address added"
                    elif form.errors:
                        response.flash="Error in the form"

                    output.update(dict(formtitle=formtitle, form=form))

                # Get list
                sublist = shn_pr_person_sublist(request, 'address', session.pr_person, fields=fields)

                if sublist:
                    output.update(sublist)

                return output

            else: # other representation
                pass

        # View, add or edit contact information -------------------------------
        elif method=="contact":
            if representation=="html":

                # Check for selected person or redirect to search form
                shn_pr_select_person(record_id)
                if not session.pr_person:
                    request.vars.next=method
                    redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))
                else:
                    pheader = shn_pr_person_header(session.pr_person, next=method)

                # Set response view
                response.view = '%s/person.html' % module

                # Add title and subtitle
                title=T('Person')
                subtitle=T('Contact Information')
                output=dict(title=title, subtitle=subtitle, pheader=pheader)

                # Which fields?
                fields = [
                        db.pr_contact.id,
                        db.pr_contact.name,
                        db.pr_contact.person_name,
                        db.pr_contact.opt_pr_contact_method,
                        db.pr_contact.value,
                        db.pr_contact.priority,
                ]

                form = shn_pr_add_details_to_person_form(session.pr_person,db.pr_contact)
                if form:
                    formtitle = T('Add Contact Information')
                    if form.accepts(request.vars,session):
                        shn_audit_create(form, 'pr_contact', representation)
                        response.flash="Contact Information added"
                    elif form.errors:
                        response.flash="Error in the form"

                    output.update(dict(formtitle=formtitle, form=form))

                # Get list
                sublist = shn_pr_person_sublist(request, 'contact', session.pr_person, fields=fields)

                if sublist:
                    output.update(sublist)

                return output

            else: # other representation
                pass

        # View, add or edit roles ---------------------------------------------
        elif method=="role":
            if representation=="html":

                # Check for selected person or redirect to search form
                shn_pr_select_person(record_id)
                if not session.pr_person:
                    request.vars.next=method
                    redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))
                else:
                    pheader = shn_pr_person_header(session.pr_person, next=method)

                # Set response view
                response.view = '%s/person.html' % module

                # Add title and subtitle
                title=T('Person')
                subtitle=T('Roles')
                output=dict(title=title, subtitle=subtitle, pheader=pheader)

                items=None

                output.update(dict(items=items))
                return output

            else: # other representation
                pass

        # View, add or edit status information --------------------------------
        elif method=="status":
            if representation=="html":

                # Check for selected person or redirect to search form
                shn_pr_select_person(record_id)
                if not session.pr_person:
                    request.vars.next=method
                    redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))
                else:
                    pheader = shn_pr_person_header(session.pr_person, next=method)

                # Set response view
                response.view = '%s/person.html' % module

                # Add title and subtitle
                title=T('Person')
                subtitle=T('Status Information')
                output=dict(title=title, subtitle=subtitle, pheader=pheader)

                items=None
                form=None

                output.update(dict(items=items, form=form))
                return output

            else: # other representation
                pass

        # View, add or edit group memberships ---------------------------------
        elif method=="group_membership":
            if representation=="html":

                # Check for selected person or redirect to search form
                shn_pr_select_person(record_id)
                if not session.pr_person:
                    request.vars.next=method
                    redirect(URL(r=request, c='pr', f='person', args='search_simple', vars=request.vars))
                else:
                    pheader = shn_pr_person_header(session.pr_person, next=method)

                # Set response view
                response.view = '%s/person.html' % module

                # Add title and subtitle
                title=T('Person')
                subtitle=T('Group Memberships')
                output=dict(title=title, subtitle=subtitle, pheader=pheader)

                # Which fields?
                fields = [
                        db.pr_group_membership.id,
                        db.pr_group_membership.group_id,
                        db.pr_group_membership.group_head,
                        db.pr_group_membership.description,
                ]

                form = shn_pr_add_details_to_person_form(session.pr_person,db.pr_group_membership)
                if form:
                    formtitle = T('Add Group Membership')
                    if form.accepts(request.vars,session):
                        shn_audit_create(form, 'pr_group_membership', representation)
                        response.flash="Group Membership added"
                    elif form.errors:
                        response.flash="Error in the form"

                    output.update(dict(formtitle=formtitle, form=form))

                # Get list
                sublist = shn_pr_person_sublist(request, 'group_membership', session.pr_person, fields=fields)

                if sublist:
                    output.update(sublist)

                return output

            else: # other representation
                pass

        else: # other method --------------------------------------------------
            pass

    # Default CRUD action: forward to REST controller
    crud.settings.delete_onvalidation=shn_pentity_ondelete
    return shn_rest_controller(module, 'person', main='first_name', extra='last_name',
        onvalidation=lambda form: shn_pentity_onvalidation(form, table='pr_person', entity_class=1),
        onaccept=lambda form: shn_pr_select_person(form.vars.id))

def group():
#    if request.vars.format:
#        representation = str.lower(request.vars.format)
#    else:
#        representation = "html"

#    if len(request.args) > 0 and not request.args[0].isdigit():
        # Check method
#        method = str.lower(request.args[0])

        # Check if record_id is submitted
#        try:
#            record_id = request.args[1]
#        except:
#            record_id = None

#        if method=="members":
#            if representation=="html":
#                pass
#            else:
                # other representation
#                pass
#        else:
            # other method
#            pass

    crud.settings.delete_onvalidation=shn_pentity_ondelete
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'group', main='group_name', extra='group_description', onvalidation=lambda form: shn_pentity_onvalidation(form, table='pr_group', entity_class=2), deletable=False)

def person_details():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'person_details')

def image():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'image')
def image_person():
    db.pr_image.pr_pe_id.requires = IS_NULL_OR(IS_ONE_OF(db,'pr_pentity.id',shn_pentity_represent,filterby='opt_pr_pentity_class',filter_opts=(1,)))
    request.filter=(db.pr_image.pr_pe_id==db.pr_pentity.id)&(db.pr_pentity.opt_pr_pentity_class==1)
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'image')

def identity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'identity')

def contact():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'contact')

def address():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'address')

def pentity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'pentity')

def presence():
    db.pr_presence.pr_pe_id.writable = False
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'presence')
def presence_person():
    db.pr_presence.pr_pe_id.writable = False
    db.pr_presence.pr_pe_id.requires = IS_NULL_OR(IS_ONE_OF(db,'pr_pentity.id',shn_pentity_represent,filterby='opt_pr_pentity_class',filter_opts=(1,)))
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
