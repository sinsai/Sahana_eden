# -*- coding: utf-8 -*-

module = 'or'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select().first().name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Dashboard'), False, URL(r=request, f='dashboard')],
    [T('Organizations'), False, URL(r=request, f='organisation'),[
        [T('Add Organization'), False, URL(r=request, f='organisation', args='create')],
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
        #[T('List Contacts'), False, URL(r=request, f='contact')],
        #[T('Search Contacts'), False, URL(r=request, f='contact', args='search')]
    ]],	
    [T('Projects'), False, URL(r=request, f='project'),[
        [T('Add Project'), False, URL(r=request, f='project', args='create')],
        #[T('List Projects'), False, URL(r=request, f='project')],
        #[T('Search Projects'), False, URL(r=request, f='project', args='search')]
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
    # ServerSidePagination
    response.s3.pagination = True
    return shn_rest_controller(module, 'organisation', listadd=False, onaccept=lambda form: organisation_onaccept(form))

def organisation_onaccept(form):
    session.flash = T('Submission Succesful')
    if request.vars.format == 'popup':
        redirect(organisation_popup_url + '&caller=' + request.vars.caller)
    else:
        f='dashboard'
        redirect(URL(r=request, f=f, args=form.vars.id))
    
@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def office():
    "RESTlike CRUD controller"
    resource = 'office'
    table = "%s_%s" % (module, resource)
    if isinstance(request.vars.organisation_id,list):
        request.vars.organisation_id = request.vars.organisation_id[0]
    if session.s3.security_policy == 1:
        # Hide the Admin row for simple security_policy
        db[table].admin.readable = db[table].admin.writable = False
    # ServerSidePagination
    response.s3.pagination = True

    # the update forms are not ready. when they will - uncomment this and comment the next one
    #if request.args(0) in ('create','update'):
    if request.args(0) == 'create':
        db[table].organisation_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, 'or_organisation.id'))
        if request.vars.organisation_id:
            session.s3.organisation_id = request.vars.organisation_id
            # Organisation name should be displayed on the form if organisation_id is pre-selected
            session.s3.organisation_name = db(db.or_organisation.id == int(session.s3.organisation_id)).select(db.or_organisation.name)[0]["name"]
    return shn_rest_controller(module, resource, listadd=False, pheader=shn_office_pheader)

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def contact():
    "RESTlike CRUD controller"
    resource = 'contact'
    table = '%s_%s' % (module, resource)
    
    # ServerSidePagination
    response.s3.pagination = True
    
    # No point in downloading large dropdowns which we hide, so provide a smaller represent

    # the update forms are not ready. when they will - uncomment this and comment the next one
    #if request.args(0) in ('create','update'):
    if request.args(0) == 'create':
        # person_id mandatory for a contact!
        db[table].person_id.requires = IS_ONE_OF_EMPTY(db, 'pr_person.id')
        db[table].organisation_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, 'or_organisation.id'))
        db[table].office_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, 'or_office.id'))
    
    return shn_rest_controller(module, resource, listadd=False)
	
    
@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def project():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'project', listadd=False)		
    
def office_table_linkto(field):
    return URL(r=request, f = "office",  args=['read',field],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})
def office_table_linkto_update(field):
    return URL(r=request, f = "office", args=['update',field],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})    
                
def contact_table_linkto(field):
    return URL(r=request, f = "contact",  args=['read',field],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})                
def contact_table_linkto_update(field):
    return URL(r=request, f = "contact", args=['update',field],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)}) 

def project_table_linkto(field):
    return URL(r=request, f = "project",  args=['read',field],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})
def project_table_linkto_update(field):
    return URL(r=request, f = "project", args=['update',field],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})                 
               
def org_sub_list( table , org_id):              
    fields = []
    headers = {}

    for field in db[table]:
        if field.readable and field.name <> "organisation_id" and field.name <> "admin":        
            headers[str(field)] = str(field.label)        
            fields.append(field)   
            
    table_linkto_update = dict( \
    or_office = office_table_linkto_update,
    or_contact =  contact_table_linkto_update,
    or_project = project_table_linkto_update,
    )

    table_linkto = dict( \
    or_office = office_table_linkto,
    or_contact = contact_table_linkto,
    or_project = project_table_linkto,
    )            
            
    authorised = shn_has_permission('update', table)
    if authorised:
        linkto = table_linkto_update[table]
    else:
        linkto = table_linkto[table]           
           
    query = db[table].organisation_id == org_id
    
    list =  crud.select(table, query = db[table].organisation_id == org_id, fields = fields, headers = headers, linkto = linkto, truncate=48, _id = table + '_list', _class="display")
    
    #Required so that there is a table with an ID for the refresh after add
    if list == None:
        list = TABLE("None", _id = table + '_list')

    return list
	
def dashboard():
    
    # Get Organization to display from Var or Arg or Default
    if len(request.args) > 0:
        org_id = int(request.args[0])
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
        table = db.or_organisation
        query  = (table.id > 0) & ((table.deleted==False) | (table.deleted==None))
        try:
            org_name = db(query).select(limitby=(0,1))[0]['name']
            org_id = 0
        except:
            session.warning = T('No Organisations registered!')
            redirect(URL(r=request, c='or', f='index'))

    o_opts = []
    first_option = True;
    # if we keep the dropdown - it will better be in alphabetic order
    # that way the user will find things easier
    for organisation in db(db.or_organisation.deleted==False).select(db.or_organisation.ALL,orderby = db.or_organisation.name):
        if (org_id == 0 and first_option) or organisation.id == org_id:
            first_option = False
            if org_id == 0:
                org_id = organisation.id
            o_opts += [OPTION(organisation.name, _value=organisation.id, _selected='')]
        else:
            o_opts += [OPTION(organisation.name, _value=organisation.id)]

    organisation_select = SELECT(_name="org", *o_opts, **dict(name="org", requires=IS_NULL_OR(IS_IN_DB(db,'or_organisation.id')), _id = 'organisation_select'))
    
    org_details = crud.read("or_organisation", org_id)

    office_list = org_sub_list("or_office", org_id)
    contact_list = org_sub_list("or_contact", org_id)
    project_list = org_sub_list("or_project", org_id)	

    but_add_org = A(T('Add Organization'),
                        _class='thickbox',
                        _href=URL(r=request, 
                            c='or', f='organisation', args='create', 
                            vars=dict(format='popup', KeepThis='true')) + "&TB_iframe=true&mode=new",
                            _target='top', _title=T('Add Organization'))	

    but_edit_org = A(T('Edit Organization'),
                        _href=URL(r=request, 
                            c='or', f='organisation', args=['update', org_id]))	

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

    but_add_project = A(T('Add Project'),
                        _class='thickbox',
                        _href=URL(r=request, 
                            c='or', f='project', args='create', 
                            vars=dict(format='popup', KeepThis='true')) + "&TB_iframe=true&mode=new",
                            _target='top', _title=T('Add Project'))										
							
    session.s3.organisation_id = org_id

    return dict(organisation_id = org_id, organisation_select = organisation_select, org_details = org_details, office_list = office_list, contact_list = contact_list, project_list = project_list, but_add_org =but_add_org, but_edit_org =but_edit_org, but_add_office = but_add_office, but_add_contact = but_add_contact, but_add_project = but_add_project)

def who_what_where_when():
    project_list = crud.select("or_project", query = db.or_project.id > 0)
    #print project_list
    return dict(project_list = project_list)
	
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
    
