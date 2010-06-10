# -*- coding: utf-8 -*-

"""
    Request Management System - Controllers
"""

module = "rms"

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Request Aid'), False, URL(r=request, f='req', args='create')],
    [T('View Requests & Pledge Aid'), False, URL(r=request, f='req')],
    [T('View & Edit Pledges'),False, URL(r=request, f='pledge')]
#    [T('Search Requests'), False, URL(r=request, f='req', args='search')] #disabled due to problems with pagination

]

# S3 framework functions
def index():
    "Module's Home Page"

    module_name = s3.modules[module]["name_nice"]

    return dict(module_name=module_name, a=1)

def req(): #aid requests
    "RESTlike CRUD controller"

    resource = 'req' # pulls from table of combined aid request feeds (sms, tweets, manual)

    # Filter out non-actionable SMS requests:
#    response.s3.filter = (db.rms_req.actionable == True) | (db.rms_req.source_type != 2) # disabled b/c Ushahidi no longer updating actionaable fielde

    if request.args(0) and request.args(0) == 'search_simple':
        pass
    else:
        # Uncomment to enable Server-side pagination:
        response.s3.pagination = True

    def req_postp(jr, output):
        if jr.representation in ("html", "popup") and not jr.component:
            response.s3.actions = [
                dict(label=str(T("Pledge")), _class="action-btn", url=str(URL(r=request, args=['[id]', 'pledge'])))
            ]
        return output
    response.s3.postp = req_postp

    output = shn_rest_controller(module, resource,
                                 editable=False,
                                 listadd=False,
                                 pheader=shn_rms_req_pheader)
                                 # call pheader to act as parent header for parent/child forms (layout defined below)

    return output


def req_detail(): #arbitrary key:value pairs for aid requests
    "RESTlike CRUD controller"

    resource = 'req_detail' #an optional unconnected list of all the arbitrary key-values for requests

        # Uncomment to enable Server-side pagination:
        #response.s3.pagination = True #commented due to display problems

    return shn_rest_controller( module , resource, editable=False, listadd=False)


def pledge(): #pledges from agencies
    "RESTlike CRUD controller"

    resource = 'pledge'

    # Uncomment to enable Server-side pagination:
    #response.s3.pagination = True  #commented due to display problems

    pledges = db(db.rms_pledge.status == 3).select() # changes the request status to completed when pledge delivered
                                                     # this is necessary to close the loop
    for pledge in pledges:
        req = db(db.rms_req.id == pledge.req_id).update(completion_status = True)

    db.commit()

    return shn_rest_controller(module, resource, editable = True, listadd=False)

def shn_rms_req_pheader(resource, record_id, representation, next=None, same=None): #parent header for child/parent forms
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
                        TD(aid_request.message, _colspan=3),
                        ),
                    TR(
                        TH(T('Priority: ')),
                        aid_request.priority,
                        TH(T('Source Type: ')),
                        rms_req_source_type[aid_request.source_type],
                        ),
                    TR(
                        TH(T('Time of Request: ')),
                        aid_request.timestamp,
                        TH(T('Verified: ')),
                        aid_request.verified,
                        ),
                    TR(
                        TH(T('Location: ')),
                        location_represent,
                        TH(T('Actionable: ')),
                        aid_request.actionable,
                        TH(T('Completion status: ')),
                        aid_request.completion_status,
                        ),
#Todo - Create a link for editing the arbitrary key-value args
#                    TR(
#                        TH(A(T('Edit Request Details'), _href=URL(r=request, f='req_detail', args=[id])))
#                        ),

                )
        return pheader

    else:
        return None

def sms_complete(): #contributes to RSS feed for closing the loop with Ushahidi

    def t(record):
        return "Sahana Record Number: " + str(record.id)

    def d(record):
        ush_id = db(db.rms_sms_request.id == record.id).select("ush_id")[0]["ush_id"]
        smsrec = db(db.rms_sms_request.id == record.id).select("smsrec")[0]["smsrec"]

        return \
            "Ushahidi Link: " + A(ush_id, _href=ush_id).xml() + '<br>' + \
            "SMS Record: " + str(smsrec)

    rss = { "title" : t , "description" : d }
    response.s3.filter = (db.rms_req.completion_status == True) & (db.rms_req.source_type == 2)
    return shn_rest_controller(module, 'req', editable=False, listadd=False, rss=rss)


def tweet_complete(): #contributes to RSS feed for closing the loop with TtT

    def t(record):
        return "Sahana Record Number: " + str(record.id)

    def d(record):
        ttt_id = db(db.rms_tweet_request.id == record.id).select("ttt_id")[0]["ttt_id"]
        return "Twitter: " + ttt_id

    rss = { "title" : t , "description" : d }
    response.s3.filter = (db.rms_req.completion_status == True) & (db.rms_req.source_type == 3)
    return shn_rest_controller(module, 'req', editable=False, listadd=False, rss = rss)
