# -*- coding: utf-8 -*-

module = 'or'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Organisations'), False, URL(r=request, f='organisation'),[
        [T('Add Organisation'), False, URL(r=request, f='organisation', args='create')],
        #[T('List Organisations'), False, URL(r=request, f='organisation')],
        #[T('Search Organisations'), False, URL(r=request, f='organisation', args='search')]
    ]],
    [T('Offices'), False, URL(r=request, f='office'),[
        [T('Add Office'), False, URL(r=request, f='office', args='create')],
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
    return shn_rest_controller(module, 'organisation', listadd=False)

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
    
