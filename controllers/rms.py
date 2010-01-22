# -*- coding: utf-8 -*-

module = 'rms'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select().first().name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('View Requests & Pledge Aid'), False, URL(r=request, f='req')],
    #[T('Pledge Aid'), False, URL(r=request, f='req', args='pledge')],
    #[T('View Tweet Requests and Pledge Aid'), False, URL(r=request, f='tweet_request')],
    #[T('View SMS Requests and Pledge Aid'), False, URL(r=request, f='sms_request')],
#    [T('Search Requests'), False, URL(r=request, f='req', args='search')]
    
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name, a=1)

def test():
    "Module's Home Page"
    return dict(module_name=module_name, a=1)

def req():
    "RESTlike CRUD controller"
    
    resource = 'req'
    
    # Filter out non-actionable SMS requests:
    response.s3.filter = (db.rms_req.actionable == True) | (db.rms_req.source_type != 2)
    #response.s3.filter = (db.rms_req.actionable == True)
    
    # Uncomment to enable Server-side pagination:
    if request.args(0) and request.args(0) == 'search_simple':
        pass
    else:
        #response.s3.pagination = True
        pass
    
    #return shn_rest_controller(module, resource, editable=False, pheader=shn_rms_req_pheader)
    return shn_rest_controller(module, resource, editable=False)

def pledge():
    "RESTlike CRUD controller"
    
    resource = 'pledge'
    
    # Uncomment to enable Server-side pagination:
    #response.s3.pagination = True
    
    return shn_rest_controller(module, resource)

def shn_rms_req_pheader(resource, record_id, representation, next=None, same=None):
    if representation == "html":

        if next:
            _next = next
        else:
            _next = URL(r=request, f=resource, args=['read'])

        if same:
            _same = same
        else:
            _same = URL(r=request, f=resource, args=['read', '[id]'])

        aid_request = db(db.rms_req.id == record_id).select().first()
        try:
            location = db(db.gis_location.id == aid_request.location_id).select().first()
            location_represent = shn_gis_location_represent(location.id)
        except:
            location_represent = None
        
        pheader = TABLE(
                    TR(
                        TH(T('Message: ')),
                        aid_request.message,
                        TH(T('Source Type: ')),
                        rms_req_source_type[aid_request.source_type],
                        ),
                    TR(
                        TH(T('Priority: ')),
                        aid_request.priority,
                        TH(T('Verified: ')),
                        aid_request.verified,
                        ),
                    TR(
                        TH(T('Time of Request: ')),
                        aid_request.timestamp,
                        TH(T('Actionable: ')),
                        aid_request.actionable,
                        ),
                    TR(
                        TH(T('Location: ')),
                        location_represent,
                        TH(T('Completion status: ')),
                        aid_request.completion_status,
                        ),
                )
        return pheader

    else:
        return None

    
    
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

def sms_request():
    "RESTlike CRUD controller"
    
    # Don't provide ability to add Locations here
    db.gis_location.comment = ''
    
    # Uncomment to filter out non-actionable requests:
    response.s3.filter = (db.rms_sms_request.actionable == True)
    
    # Uncomment to enable Server-side pagination:
    #response.s3.pagination = True
    
    return shn_rest_controller(module, 'sms_request', editable=False, listadd=False)

def tweet_request():
    "RESTlike CRUD controller"
    
    # Uncomment to enable Server-side pagination:
    #response.s3.pagination = True
    
    return shn_rest_controller(module, 'tweet_request', editable=False, listadd=False)

@auth.requires_login()
def make_pledge():
    req_id = request.args(0) or redirect(URL(r=request,f="index"))
    db.rms_pledge.req_id.default = req_id
    db.rms_pledge.req_id.writable = False
   #db.pledge.req_id.writable = db.pledge.req_id.readable = False
    form1 = crud.read(db.rms_req, req_id)
    pledges = db(db.rms_pledge.req_id==req_id).select(orderby=db.rms_pledge.submitted_on)
    form2 = crud.create(db.rms_pledge)
    return dict(form1=form1, pledges=pledges, form2=form2)


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
