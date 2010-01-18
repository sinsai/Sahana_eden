# -*- coding: utf-8 -*-

module = 'rms'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Request Aid'), False, URL(r=request, f='request_aid'),[
        [T('Request Aid'), False, URL(r=request, f='request_aid', args='create')],
    ]],
    [T('Pledge Aid'), False, URL(r=request, f='pledge_aid'),[
        [T('Pledge Aid'), False, URL(r=request, f='pledge_aid', args='create')],
    ]],
    [T('SMS Request'), False, URL(r=request, f='sms_request'),[
        [T('SMS Request'), False, URL(r=request, f='sms_request', args='create')],
    ]]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def request_aid():
    "RESTlike CRUD controller"
#    return shn_rest_controller(module, 'request_aid', pheader=shn_rms_pheader)
    return shn_rest_controller(module, 'request_aid')

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def pledge_aid():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'pledge_aid')

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def sms_request():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'sms_request', editable=False, listadd=False)
    
    
#def shn_rms_pheader(resource, record_id, representation, next=None, same=None):

#    if representation == "html":

#        if next:
#            _next = next
#        else:
#            _next = URL(r=request, f=resource, args=['read'])

#        if same:
#            _same = same
#        else:
#            _same = URL(r=request, f=resource, args=['read', '[id]'])

#        request_item = db(db.rms_request_item.id == record_id).select()[0]
#        request_aid = db(db.rms_request_aid.id == request_item.rms_request_aid_id).select()[0]
            
#        pheader = TABLE(
#            TR(
#                TH(T('Type: ')),
#                request_item.type,
#            TR(
#                TH(T('Request Aid: ')),
#                request_aid.name
#                )

#                )
#        )
#        return pheader

#    else:
#        return None
