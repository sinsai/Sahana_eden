# -*- coding: utf-8 -*-

module = 'rms'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)
 
# -------------------------------
# Load lists/dictionaries for drop down menus

rms_priority_opts = {
    1:T('High'),
    2:T('Medium'),
    3:T('Low')
}

rms_status_opts = {
    1:T('Pledged'),
    2:T('In Transit'),
    3:T('Delivered'),
    }

rms_type_opts = {
    1:T('Food'),
    2:T('Find'),
    3:T('Water'),
    4:T('Medicine'),
    5:T('Shelter'),
    6:T('Report'),
    }

rms_req_source_type = { 1 : 'Manual',
                        2 : 'SMS',
                        3 : 'Tweet' }

# -----------------
# Requests table (Combined SMS, Tweets & Manual entry)

def shn_req_aid_represent(id): 
    return  A(T('Make Pledge'), _href=URL(r=request, f='req', args=[id, 'pledge']))

resource = 'req'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
   Field("message", "text"),
   location_id,
   Field("timestamp", "datetime"),
   Field("type", "integer"),
   Field("priority", "integer"),
   Field("verified", "boolean"),
   Field("city", "string"),
   Field("completion_status", "boolean"),
   Field("source_type", "integer"),
   Field("source_id", "integer"),
   Field("actionable", "boolean"),
    migrate=migrate)

db.rms_req.id.represent = lambda id: shn_req_aid_represent(id)

#label the fields for the view
db[table].timestamp.label = T('Date & Time')

#Hide fields from user:
db[table].verified.readable = db[table].verified.writable = False
db[table].source_id.writable = db[table].source_id.readable = False
db[table].completion_status.writable = db[table].completion_status.readable = False
db[table].actionable.writable = db[table].actionable.readable = False
db[table].source_type.writable = db[table].source_type.readable = False

#set default values
db[table].actionable.default = 1
db[table].source_type.default = 1

db[table].message.requires = IS_NOT_EMPTY()
db[table].message.comment = SPAN("*", _class="req")

db[table].priority.requires = IS_NULL_OR(IS_IN_SET(rms_priority_opts))
db[table].priority.represent = lambda prior: prior and rms_priority_opts[prior]
db[table].priority.label = T('Priority Level')

db[table].type.requires = IS_NULL_OR(IS_IN_SET(rms_type_opts))
db[table].type.represent = lambda type: type and rms_type_opts[type]
db[table].type.label = T('Request Type')

db[table].source_type.requires = IS_NULL_OR(IS_IN_SET(rms_req_source_type))
db[table].source_type.represent = lambda stype: stype and rms_req_source_type[stype]
db[table].source_type.label = T(' Source Type')



s3.crud_strings[table] = Storage(title_create        = "Add Aid Request", 
                                 title_display       = "Aid Request Details", 
                                 title_list          = "List Aid Requests", 
                                 title_update        = "Edit Aid Request",  
                                 title_search        = "Search Aid Requests",
                                 subtitle_create     = "Add New Aid Request",
                                 subtitle_list       = "Aid Requests",
                                 label_list_button   = "List Aid Requests",
                                 label_create_button = "Add Aid Request",
                                 msg_record_created  = "Aid request added",
                                 msg_record_modified = "Aid request updated",
                                 msg_record_deleted  = "Aid request deleted",
                                 msg_list_empty      = "No aid requests currently available")

#
# shn_rms_get_req --------------------------------------------------------
# copied from pr.py
def shn_rms_get_req(label, fields=None, filterby=None):
    """
        Finds a request by Message string
    """

    if fields and isinstance(fields, (list,tuple)):
        search_fields = []
        for f in fields:
            if db.rms_req.has_key(f):     # TODO: check for field type?
                search_fields.append(f)
        if not len(search_fields):
            # Error: none of the specified search fields exists
            return None
    else:
        # No search fields specified at all => fallback
        search_fields = ['message']

    if label and isinstance(label, str):
        labels = label.split()
        results = []
        query = None
        # TODO: make a more sophisticated search function (levenshtein?)
        for l in labels:

            # append wildcards
            wc = "%"
            _l = "%s%s%s" % (wc, l, wc)

            # build query
            for f in search_fields:
                if query:
                    query = (db.rms_req[f].like(_l)) | query
                else:
                    query = (db.rms_req[f].like(_l))

            # undeleted records only
            query = (db.rms_req.deleted==False) & (query)
            # restrict to prior results (AND)
            if len(results):
                query = (db.rms_req.id.belongs(results)) & query
            if filterby:
                query = (filterby) & (query)
            records = db(query).select(db.rms_req.id)
            # rebuild result list
            results = [r.id for r in records]
            # any results left?
            if not len(results):
                return None
        return results
    else:
        # no label given or wrong parameter type
        return None

#
# shn_rms_req_search_simple -------------------------------------------------
# copied from pr.py
def shn_rms_req_search_simple(xrequest, onvalidation=None, onaccept=None):
    """
        Simple search form for persons
    """

    if not shn_has_permission('read', db.rms_req):
        session.error = UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, args='search_simple', vars=request.vars)}))

    if xrequest.representation=="html":
        # Check for redirection
        if request.vars._next:
            next = str.lower(request.vars._next)
        else:
            next = str.lower(URL(r=request, f='req', args='[id]'))

        # Custom view
        response.view = '%s/req_search.html' % xrequest.prefix

        # Title and subtitle
        title = T('Search for a Request')
        subtitle = T('Matching Records')

        # Select form
        form = FORM(TABLE(
                TR(T('Text in Message: '),
                   INPUT(_type="text", _name="label", _size="40"),
                   A(SPAN("[Help]"), _class="tooltip", _title=T("Text in Message|To search for a request, enter some of the text that you are looking for. You may use % as wildcard. Press 'Search' without input to list all requests."))),
                TR("", INPUT(_type="submit", _value="Search"))
                ))

        output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

        # Accept action
        items = None
        if form.accepts(request.vars, session):

            if form.vars.label == "":
                form.vars.label = "%"

            results = shn_rms_get_req(form.vars.label)

            if results and len(results):
                rows = db(db.rms_req.id.belongs(results)).select()
            else:
                rows = None

            # Build table rows from matching records
            if rows:
                records = []
                for row in rows:
                    href = next.replace('%5bid%5d', '%s' % row.id)
                    records.append(TR(
                        row.completion_status,
                        row.message,
                        row.timestamp,
                        row.location_id and shn_gis_location_represent(row.location_id) or 'unknown',
                        ))
                items=DIV(TABLE(THEAD(TR(
                    TH("Completion Status"),
                    TH("Message"),
                    TH("Time"),
                    TH("Location"),
                    )),
                    TBODY(records), _id='list', _class="display"))
            else:
                items = T('None')

        try:
            label_create_button = s3.crud_strings['rms_req'].label_create_button
        except:
            label_create_button = s3.crud_strings.label_create_button

        add_btn = A(label_create_button, _href=URL(r=request, f='req', args='create'), _id='add-btn')

        output.update(dict(items=items, add_btn=add_btn))
        return output

    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

# Plug into REST controller
s3xrc.model.set_method(module, resource, method='search_simple', action=shn_rms_req_search_simple )

# ------------------
# Create pledge table

resource = 'pledge'
table = module + '_' + resource
db.define_table(table, timestamp, authorstamp, uuidstamp, deletion_status,
   Field('submitted_on', 'datetime'), 
   Field("req_id", db.rms_req),
   Field("status", "integer"),
   organisation_id,
   person_id,
#   Field('submitted_by', db.auth_user),
#   location_id,
#   Field('comment_id', db.comment),
   migrate=migrate)

# autofill submitted_by forms & make read only
#db[table].submitted_by.default = auth.user.id if auth.user else 0
#db[table].submitted_by.writable = False

# hide unnecessary fields
db[table].req_id.writable = db[table].req_id.readable = False

# set pledge default
db[table].status.default = 1

# auto fill posted_on field and make it readonly
db[table].submitted_on.default = request.now
db[table].submitted_on.writable = False

db[table].status.requires = IS_IN_SET(rms_status_opts)
db[table].status.represent = lambda status: status and rms_status_opts[status]
db[table].status.label = T('Pledge Status')



# Pledges as a component of requests
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(rms_req = 'req_id'),
    deletable=True,
    editable=True,
    list_fields = ['id', 'organisation_id', 'person_id', 'submitted_on', 'status'])

s3.crud_strings[table] = Storage(title_create        = "Add Pledge", 
                                 title_display       = "Pledge Details", 
                                 title_list          = "List Pledges", 
                                 title_update        = "Edit Pledge",  
                                 title_search        = "Search Pledges",
                                 subtitle_create     = "Add New Pledge",
                                 subtitle_list       = "Pledges",
                                 label_list_button   = "List Pledges",
                                 label_create_button = "Add Pledge",
                                 msg_record_created  = "Pledge added",
                                 msg_record_modified = "Pledge updated",
                                 msg_record_deleted  = "Pledge deleted",
                                 msg_list_empty      = "No Pledges currently available")


    
# ------------------
# Create the table for sms_request for Ushahidi
# Deprecated by combined table
resource = 'sms_request'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
    person_id,
    organisation_id,
    Field("pledge", "integer"),
    Field("sms", "string"),
    Field("notes", "string"),
    Field("phone", "string"),
    Field("ush_id", "string"), 
    Field("updated", "datetime"),
    Field("title", "string"),
    Field("categorization", "string"), 
    location_id,
    Field("status", "string"), 
    Field("smsrec", "integer"), 
    Field("author", "string"),
    Field("category_term", "string"),
    Field("firstname"), 
    Field("lastname"), 
    Field("address", "text"), 
    Field("city", "string"), 
    Field("department", "string"), 
    Field("summary", "string"), 
    Field("link", "string"),
    Field("actionable", "boolean"),
    migrate=migrate)

# for reusable
ADD_SMS_REQUEST = T('Add SMS Request')

db[table].pledge.requires = IS_NULL_OR(IS_IN_SET(rms_status_opts))
db[table].pledge.represent = lambda pledge: pledge and rms_status_opts[pledge]
db[table].pledge.label = T('Pledge Status')

# Relabel Field Names:
db[table]["sms"      ].label = T("SMS Message")
db[table]["firstname"].label = T("First Name")
db[table]["lastname" ].label = T("Last Name")
db[table][person_id].label = T("Pledge Name")
db[table][organisation_id].label = T("Pledge Organisation")

# Make some fields invisible:
db[table].ush_id.writable = db[table].ush_id.readable = False
db[table].author.writable = db[table].author.readable = False
db[table]["title"        ].writable = db[table]["title"        ].readable = False
db[table]["category_term"].writable = db[table]["category_term"].readable = False
db[table]["smsrec"       ].writable = db[table]["smsrec"       ].readable = False
db[table]["summary"      ].writable = db[table]["summary"      ].readable = False
db[table]["link"         ].writable = db[table]["link"         ].readable = False

# make all fields read only
db[table]["sms"           ].writable = False
db[table]["notes"         ].writable = False
db[table]["phone"         ].writable = False
db[table]["updated"       ].writable = False
db[table]["categorization"].writable = False
db[table]["status"        ].writable = False
db[table]["address"       ].writable = False
db[table]["city"          ].writable = False
db[table]["department"    ].writable = False
db[table][location_id     ].writable = False
db[table]["actionable"    ].writeble = False

db[table]["phone"      ].writable = False
db[table]["firstname"  ].writable = False
db[table]["lastname"   ].writable = False

# Unauthenticated users shoudln't be able to access personal details
if not auth.is_logged_in():
    db[table]["phone"    ].readable = False
    db[table]["firstname"].readable = False
    db[table]["lastname" ].readable = False
    db[table][person_id  ].writable = db[table][person_id  ].readable = False
    db[table][organisation_id].writable = db[table][organisation_id].readable = False

s3.crud_strings[table] = Storage( title_create        = "Add SMS Request", 
                                  title_display       = "SMS Request Details", 
                                  title_list          = "List SMS Requests (please login and click a request id to make a pledge)", 
                                  title_update        = "Edit SMS Requests",  
                                  title_search        = "Search SMS Requests",
                                  subtitle_create     = "Add New SMS Request",
                                  subtitle_list       = "SMS Requests",
                                  label_list_button   = "List SMS Requests",
                                  label_create_button = "Add SMS Request",
                                  msg_record_created  = "SMS Request Aded",
                                  msg_record_modified = "SMS request updated",
                                  msg_record_deleted  = "SMS request deleted",
                                  msg_list_empty      = "No SMS requests currently available")

#Reusable field for other tables
sms_request_id = SQLTable(None, 'sms_request_id',
            Field('sms_request_id', db.rms_sms_request,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'rms_sms_request.id', '%(updated)s')),
                represent = lambda id: (id and [db(db.rms_sms_request.id==id).select()[0].updated] or ["None"])[0],
                label = T('SMS Request'),
                comment = DIV(A(ADD_SMS_REQUEST, _class='thickbox', _href=URL(r=request, c='rms', f='sms_request', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_SMS_REQUEST), A(SPAN("[Help]"), _class="tooltip", _title=T("ADD Request|The Request this record is associated with."))),
                ondelete = 'RESTRICT'
                ))

# ------------------
# Create the table for tweet_request for Tweak the Tweet
# Deprecated by combined table
resource = 'tweet_request'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
    person_id,
    organisation_id,
    Field("pledge", "integer"),
    Field("details", "string"), 
    Field("tweet", "string"),
    Field("author", "string"), 
    #Field("updated", 'datetime'), 
    Field("updated", "string"), 
    Field("link", "string"),
    Field("ttt_id", "string"), 
    migrate=migrate)

db[table].pledge.requires = IS_NULL_OR(IS_IN_SET(rms_status_opts))
db[table].pledge.represent = lambda pledge: pledge and rms_status_opts[pledge]
db[table].pledge.label = T('Pledge Status')

# Relabel Field Names:
db[table].tweet.label = T("Tweet")
db[table].person_id.label = T("Pledge Name")
db[table].organisation_id.label = T("Pledge Organisation")
db[table].details.label = T("Pledge Details")

# Make some fields invisible:
db[table].ttt_id.writable = db[table].ttt_id.readable = False

# make all fields read only
db[table].author.writable = False
db[table].updated.writable = False
db[table].link.writable = False
db[table].tweet.writable = False

db[table].link.represent = lambda url: A(url, _href=url, _target='blank')

ADD_TWEET_REQUEST = T('Add Tweet Request')
s3.crud_strings[table] = Storage( title_create        = ADD_TWEET_REQUEST, 
                                  title_display       = "Tweet Request Details", 
                                  title_list          = "List Tweet Requests (please login and click a request id to make a pledge)", 
                                  title_update        = "Edit Tweet Requests",  
                                  title_search        = "Search Tweet Requests",
                                  subtitle_create     = "Add New Tweet Request",
                                  subtitle_list       = "Tweet Requests",
                                  label_list_button   = "List Tweet Requests",
                                  label_create_button = ADD_TWEET_REQUEST,
                                  msg_record_created  = "Tweet Request Aded",
                                  msg_record_modified = "Tweet request updated",
                                  msg_record_deleted  = "Tweet request deleted",
                                  msg_list_empty      = "No Tweet requests currently available")


#Reusable field for other tables
tweet_request_id = SQLTable(None, 'tweet_request_id',
            Field('tweet_request_id', db.rms_tweet_request,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'rms_tweet_request.id', '%(description)s')),
                represent = lambda id: (id and [db(db.rms_tweet_request.id==id).select().first().updated] or ["None"])[0],
                label = T('Tweet Request'),
                comment = DIV(A(ADD_TWEET_REQUEST, _class='thickbox', _href=URL(r=request, c='rms', f='tweet_request', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_TWEET_REQUEST), A(SPAN("[Help]"), _class="tooltip", _title=T("ADD Request|The Request this record is associated with."))),
                ondelete = 'RESTRICT'
                ))


# ------------------
# Create comments table TODO

#db.define_table('comment',
#Field('pledge_id'),
#Field('body'),
#Field('timestamp', 'datetime')
#)




# ------------------
# Create request table

#resource = 'request_aid'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp, deletion_status,
#    person_id,
#    organisation_id,
#    location_id,
#    Field("priority", "integer"),
#    Field("comment","text"),
#    Field("pubdate","datetime"),
#    Field("verified","boolean"),
#    Field("numserved", "integer"),
#    migrate=migrate)

# Automatically fill in the posting time:
#db[table].pubdate.default  = request.now
#db[table].pubdate.writable = False
#db[table].pubdate.label    = T("Date/Time")

# Hide the verified field:
#db[table].verified.readable = False
#db[table].verified.writable = False
#
#db[table].priority.requires = IS_NULL_OR(IS_IN_SET(rms_priority_opts))
#db[table].priority.represent = lambda prior: prior and rms_priority_opts[prior]
#db[table].priority.label = T('Priority Level')

#s3.crud_strings[table] = Storage( title_create        = "Add Aid Request", 
#                                  title_display       = "Aid Request Details", 
#                                  title_list          = "List Aid Requests", 
#                                  title_update        = "Edit Aid Request",  
#                                  title_search        = "Search Aid Requests",
#                                  subtitle_create     = "Add New Aid Request",
#                                  subtitle_list       = "Aid Requests",
#                                  label_list_button   = "List Aid Requests",
#                                  label_create_button = "Add Aid Request",
#                                  msg_record_created  = "Aid request added",
#                                  msg_record_modified = "Aid request updated",
#                                  msg_record_deleted  = "Aid request deleted",
#                                  msg_list_empty      = "No aid requests currently available")


# ------------------------------ #    
# Create the Pledge Aid Database

#resource = 'pledge_aid'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp, deletion_status,
#    sms_request_id,
#    person_id,
#    organisation_id,
#    location_id,
#    Field("priority", "integer"),
#    Field("comment","text"),
#    Field("pubdate","datetime"),
#    Field("verified","boolean"),
#    migrate=migrate)


# Automatically fill in the posting time:
#db[table].pubdate.default  = request.now
#db[table].pubdate.writable = False
#db[table].pubdate.label    = T("Date/Time")

# Hide Verified:
#db[table].verified.readable = False
#db[table].verified.writable = False


#db[table].priority.requires = IS_NULL_OR(IS_IN_SET(rms_priority_opts))
#db[table].priority.represent = lambda prior: prior and rms_priority_opts[prior]
#db[table].priority.label = T('Priority Level')


#s3.crud_strings[table] = Storage( title_create        = "Add Pledge of Aid", 
#                                  title_display       = "Pledge Details", 
#                                  title_list          = "List Pledges", 
#                                  title_update        = "Edit Pledges",  
#                                  title_search        = "Search Pledges",
#                                  subtitle_create     = "Add New Pledge of Aid",
#                                  subtitle_list       = "Pledges",
#                                  label_list_button   = "List Pledges",
#                                  label_create_button = "Add Pledge",
#                                  msg_record_created  = "Pledge added",
#                                  msg_record_modified = "Pledge updated",
#                                  msg_record_deleted  = "Pledge deleted",
#                                  msg_list_empty      = "No pledges currently available")#

# ------------------
# Create the Pledge Items Database
                             
#resource = 'pledge_item'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp, deletion_status,
#    Field("type", "integer"),
#    Field("quantity", "double"),
#    Field("unit","string"),
#    Field("pledge_id", db.rms_pledge_aid),
#    migrate=migrate)
       
#s3xrc.model.add_component(module, resource,
#    multiple=True,
#    joinby=dict(rms_pledge_aid = 'pledge_id'),
#    deletable=True,
#    editable=True,
#    list_fields = ['id', 'type', 'quantity', 'unit'])

#db[table].type.requires = IS_NULL_OR(IS_IN_SET(rms_type_opts))
#db[table].type.represent = lambda opt: rms_type_opts[opt]
#db[table].type.label = T('Aid type')
