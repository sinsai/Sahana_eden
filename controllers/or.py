# -*- coding: utf-8 -*-

module = 'or'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select().first().name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Dashboard'), False, URL(r=request, f='dashboard')],
    [T('Organisations'), False, URL(r=request, f='organisation'),[
        [T('Add Organisation'), False, URL(r=request, f='organisation', args='create')],
        #[T('List Organisations'), False, URL(r=request, f='organisation')],
        #[T('Search Organisations'), False, URL(r=request, f='organisation', args='search')]
    ]],
    [T('Offices'), False, URL(r=request, f='office'),[
        [T('Add Office'), False, URL(r=request, f='office', args='create')],
        #[T('List Offices'), False, URL(r=request, f='office')],
        #[T('Search Offices'), False, URL(r=request, f='office', args='search')]
    ]],
    [T('Contacts'), False, URL(r=request, f='contact'),[
        [T('Add Contact'), False, URL(r=request, f='contact', args='create')],
        #[T('List Offices'), False, URL(r=request, f='office')],
        #[T('Search Offices'), False, URL(r=request, f='office', args='search')]
    ]],	
    [T('Activities'), False, URL(r=request, f='activity'),[
        [T('Add Activity'), False, URL(r=request, f='activity', args='create')],
        #[T('List Offices'), False, URL(r=request, f='office')],
        #[T('Search Offices'), False, URL(r=request, f='office', args='search')]
    ]]	
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def sector():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'sector', listadd=False)

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def organisation():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'organisation', listadd=False, onaccept=lambda form: organisation_onaccept(form))

def organisation_onaccept(form):
    session.flash = T('Submission Succesful')
    redirect(URL(r=request, f='dashboard', args=form.vars.id))
    
@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def office():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'office', listadd=False, pheader=shn_office_pheader)

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def contact():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'contact', listadd=False)
	
@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def activity():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'activity', listadd=False)	
    
    
def org_sub_table( table , org_id):              
    fields = []
    headers = {}
    for field in db[table]:
        if field.readable and field.name <> "organisation_id" and field.name <> "admin":
            headers[field.name] = str(field.label)
            fields.append(field.name)
    
    return crud.select(table, query = db[table].organisation_id == org_id, fields = fields, headers = headers, truncate=48, _id = table + '_list', _class="display")
    
	
def dashboard():
    #print "args: " 
    #print request.args
    #print "len a:" + str(len(request.args))
    #print "vars:"
    #print request.vars
    
    # Get Organization to display from Var or Arg or Default
    if len(request.args) > 0:
        #print "bugger"
        org_id = request.args[0]
        try:
            org_name = db(db.or_organisation.id == org_id).select(db.or_organisation.name)[0]["name"]
        except:
            session.error = T('Invalid Organisation ID!')
            redirect(URL(r=request, c='or', f='index'))
    elif "name" in request.vars:
        org_name = request.vars["name"]
        try:
            org_id = db(db.or_organisation.name == org_name).select(db.or_organisation.id)[0]["id"]
        except:
            session.error = T('Invalid Organisation ID!')
            redirect(URL(r=request, c='or', f='index'))
    else:
        org_id = 1
        try:
            org_name = db(db.or_organisation.id == org_id).select(db.or_organisation.name)[0].name
        except:
            session.warning = T('No Organisations registered!')
            redirect(URL(r=request, c='or', f='index'))

    org_list = []	
    for row in db(db.or_organisation.id > 0).select(orderby = db.or_organisation.name):	
        org_list.append(row.name)
    organisation_select = SELECT(org_list, id = 'organisation_select', value = org_name)
    
    org_details = crud.read("or_organisation", org_id)

    office_list = org_sub_table("or_office", org_id)
    contact_list = org_sub_table("or_contact", org_id)
    activity_list = org_sub_table("or_activity", org_id)	

    but_add_org = A(T('Add Organization'),
                        _class='thickbox',
                        _href=URL(r=request, 
                            c='or', f='organisation', args='create', 
                            vars=dict(format='popup', KeepThis='true')) + "&TB_iframe=true&mode=new",
                            _target='top', _title=T('Add Organization'))	

    but_edit_org = A(T('Edit Organization'),
                        _href=URL(r=request, 
                            c='or', f='organisation', args=['update', organisation_id]))	

    but_add_office = A(T('Add Office'),
                        _class='thickbox',
                        _href=URL(r=request, 
                            c='or', f='office', args='create', 
                            vars=dict(format='popup', KeepThis='true')) + "&TB_iframe=true&mode=new",
                            _target='top', _title=T('Add Office'))	
							
    but_add_contact = A(T('Add Contact'),
                        _class='thickbox',
                        _href=URL(r=request, 
                            c='or', f='contact', args='create', 
                            vars=dict(format='popup', KeepThis='true')) + "&TB_iframe=true&mode=new",
                            _target='top', _title=T('Add Contact'))			

    but_add_activity = A(T('Add Activity'),
                        _class='thickbox',
                        _href=URL(r=request, 
                            c='or', f='activity', args='create', 
                            vars=dict(format='popup', KeepThis='true')) + "&TB_iframe=true&mode=new",
                            _target='top', _title=T('Add Activity'))										
							
    session.s3.organisation_id = org_id

    return dict(organisation_id = org_id, organisation_select = organisation_select, org_details = org_details, office_list = office_list, contact_list = contact_list, activity_list = activity_list, but_add_org =but_add_org, but_edit_org =but_edit_org, but_add_office = but_add_office, but_add_contact = but_add_contact, but_add_activity = but_add_activity)
	
def shn_office_pheader(resource, record_id, representation, next=None, same=None):

    if representation == "html":

        if next:
            _next = next
        else:
            _next = URL(r=request, f=resource, args=['read'])

        if same:
            _same = same
        else:
            _same = URL(r=request, f=resource, args=['read', '[id]'])

        office = db(db.or_office.id == record_id).select()[0]
        organisation = db(db.or_organisation.id == office.organisation_id).select()[0]
            
        pheader = TABLE(
            TR(
                TH(T('Name: ')),
                office.name,
                TH(T('Type: ')),
                office.type,
            TR(
                TH(T('Organisation: ')),
                organisation.name
                ),
                TH(T('Sector: ')),
                db(db.or_sector.id == organisation.sector_id).select()[0].name
                ),
            TR(
                TH(A(T('Edit Office'),
                    _href=URL(r=request, c='or', f='office', args=['update', record_id], vars={'_next': _next})))
                )
        )
        return pheader

    else:
        return None
    
