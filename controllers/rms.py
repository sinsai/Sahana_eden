# -*- coding: utf-8 -*-

module = 'rms'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select().first().name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
#    [T('Request Aid'), False, URL(r=request, f='request_aid'),[
#        [T('Request Aid'), False, URL(r=request, f='request_aid', args='create')],
#    ]],
    [T('View SMS Requests and Pledge Aid'), False, URL(r=request, f='sms_request')],
#    [T('Pledge Aid'), False, URL(r=request, f='sms_request')],
#    [T('Search SMS Requests'), False, URL(r=request, f='sms_request', args='search')]
    
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name, a=1)

def test():
    "Module's Home Page"
    return dict(module_name=module_name, a=1)


#@service.jsonrpc
#@service.xmlrpc
#@service.amfrpc
#def request_aid():
#    "RESTlike CRUD controller"
#    return shn_rest_controller(module, 'request_aid', pheader=shn_rms_req_pheader)

#@service.jsonrpc
#@service.xmlrpc
#@service.amfrpc
#def pledge_aid():
#    "RESTlike CRUD controller"
#    return shn_rest_controller(module, 'pledge_aid', pheader=shn_rms_plg_pheader)

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def sms_request():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'sms_request', editable=False, listadd=False)

#def shn_rms_req_pheader(resource, record_id, representation, next=None, same=None):
#    if representation == "html":

#        if next:
#            _next = next
#        else:
#            _next = URL(r=request, f=resource, args=['read'])
#
#        if same:
#            _same = same
#        else:
#            _same = URL(r=request, f=resource, args=['read', '[id]'])

#        request_aid = db(db.rms_request_aid.id == record_id).select().first()

#        top_row = [
#                TH(T('Request Aid: ')),
#                A(T(str(request_aid.id)),
#                    _href=URL(r=request, f=resource, args=request_aid.id)),

#                TH(T('Priority: ')),
#                rms_priority_opts[request_aid.priority],
#                TH(T('Number Served: ')),
#                ]

#        bottom_row = []

#        person = db(db.pr_person.id==request_aid.person_id).select()
#        bottom_row += [ TH(T('Person: ')) ]
#        if len(person) > 0:
#            person = person[0]
#            bottom_row += [ A(T(person.first_name + " " + person.last_name), _href=URL(a='rms', c='pr', f='person', args=person.id)) ]
#        else:
#            bottom_row += ['']

#        org = db(db.or_organisation.id==request_aid.organisation_id).select()
#        bottom_row += [ TH(T('Organization: ')) ]
#        if len(org) > 0:
#            org = org[0]
#            bottom_row += [ A(T(org.name), _href=URL(a='rms', c='or', f='organisation', args=org.id)) ]
#        else:
#            bottom_row += ['None']

#        loc = db(db.gis_location.id==request_aid.location_id).select()
#        bottom_row += [ TH(T('Location: ')) ]
#        if len(loc) > 0:
#            loc = loc[0]
#            bottom_row += [ A(T(loc.name), _href=URL(a='rms', c='gis', f='location', args=loc.id)) ]
#        else:
#            bottom_row += ['None']

#        pheader = TABLE(
#            TR(top_row),
#            TR( bottom_row),
#        )
#        return pheader

#    else:
#        return None
        
        
def shn_rms_plg_pheader(resource, record_id, representation, next=None, same=None):
    if representation == "html":

        if next:
            _next = next
        else:
            _next = URL(r=request, f=resource, args=['read'])

        if same:
            _same = same
        else:
            _same = URL(r=request, f=resource, args=['read', '[id]'])

        pledge_aid = db(db.rms_pledge_aid.id == record_id).select().first()

        top_row = [
                TH(T('Pledge Aid: ')),
                A(T(str(pledge_aid.id)),
                    _href=URL(r=request, f=resource, args=pledge_aid.id)),
                TH(T('Priority: ')),
                rms_priority_opts[pledge_aid.priority],
                TH(T('')),
                ''
                ]

        bottom_row = []

        person = db(db.pr_person.id==pledge_aid.person_id).select()
        bottom_row += [ TH(T('Person: ')) ]
        if len(person) > 0:
            person = person[0]
            bottom_row += [ A(T(person.first_name + " " + person.last_name), _href=URL(a='rms', c='pr', f='person', args=person.id)) ]
        else:
            bottom_row += ['']

        org = db(db.or_organisation.id==pledge_aid.organisation_id).select()
        bottom_row += [ TH(T('Organization: ')) ]
        if len(org) > 0:
            org = org[0]
            bottom_row += [ A(T(org.name), _href=URL(a='rms', c='or', f='organisation', args=org.id)) ]
        else:
            bottom_row += ['None']

        loc = db(db.gis_location.id==pledge_aid.location_id).select()
        bottom_row += [ TH(T('Location: ')) ]
        if len(loc) > 0:
            loc = loc[0]
            bottom_row += [ A(T(loc.name), _href=URL(a='rms', c='gis', f='location', args=loc.id)) ]
        else:
            bottom_row += ['None']

        pheader = TABLE(
            TR(top_row),
            TR( bottom_row),
        )
        return pheader

    else:
        return None
