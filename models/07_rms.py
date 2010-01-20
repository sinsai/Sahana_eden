# -*- coding: utf-8 -*-

module = 'rms'

# this is code is for a simple flat table linked directly to sms_request
# relational code in development


# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)
 
# -------------------------------
# Load lists/dictionaries for drop down menus


rms_request_aid_type_opts = [ # this list is from the Ushahidi RSS (not used here)
    T('1: Emergency'),
    T('1A: Collapsed Structure'),
    T('1B: Fire'),
    T('1C: People Trapped'),
    T('1D: Contaminated Water Supply'),
    T('1E: Earthquake and Aftershocks'),
    T('1F: Medical Emergency'),
    T(''),
    T('2: Threats'),
    T('2A: Structures at Risk'),
    T('2B: Looting'),
    T(''),
    T('3: Vital Lines'),
    T('3A: Water Shortage'),
    T('3B: Road Blocked'),
    T('3C: Power Outage'),
    T(''),
    T('4: Response'),
    T('4A: Health Services'),
    T('4B: USAR Search and Rescue'),
    T('4C: Shelter'),
    T('4D: Food Distribution'),
    T('4E: Water Sanitation and Hygiene Promotion'),
    T('4F: Non Food Items'),
    T('4G: Rubble Removal'),
    T('4H: Dead Bodies Management'),
    T(''),
    T('5: Other'),
    T(''),
    T('6: Persons News'),
    T('6A: Deaths'),
    T('6B: Missing Persons'),
    ]

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

# ------------------
# Create the table for sms_request for Ushahidi

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

db[table]["phone"      ].writable = False
db[table]["firstname"  ].writable = False
db[table]["lastname"   ].writable = False

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
                                  label_list_button   = "List SMS Request",
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

#resource = 'sms_request'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp, deletion_status,
#    person_id,
#    organisation_id,
#    Field("pledge", "integer"),
#    Field("title", "string"),
#    Field("author", "string"),
#    Field("link", "string"),
#    Field("description", "string"),
#    Field("updated", "datetime"),
#    Field("guid", "string"),
#    migrate=migrate)


# ------------------
# Create the table for tweet_request for Tweak the Tweet

resource = 'tweet_request'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
    person_id,
    organisation_id,
    Field("pledge", "integer"),
    Field("description", "string"), 
    Field("author", "string"), 
    #Field("updated", 'datetime'), 
    Field("updated", "string"), 
    Field("link", "string"),
    Field("tweet", "string"),
    Field("ttt_id", "string"), 
    migrate=migrate)

db[table].pledge.requires = IS_NULL_OR(IS_IN_SET(rms_status_opts))
db[table].pledge.represent = lambda pledge: pledge and rms_status_opts[pledge]
db[table].pledge.label = T('Pledge Status')

# Relabel Field Names:
db[table].tweet.label = T("Tweet")
db[table].person_id.label = T("Pledge Name")
db[table].organisation_id.label = T("Pledge Organisation")

# Make some fields invisible:
db[table].ttt_id.writable = db[table].ttt_id.readable = False

# make all fields read only
db[table].author.writable = False
db[table].updated.writable = False
db[table].link.writable = False
db[table].tweet.writable = False

ADD_TWEET_REQUEST = T('Add Tweet Request')
s3.crud_strings[table] = Storage( title_create        = ADD_TWEET_REQUEST, 
                                  title_display       = "Tweet Request Details", 
                                  title_list          = "List Tweet Requests (please login and click a request id to make a pledge)", 
                                  title_update        = "Edit Tweet Requests",  
                                  title_search        = "Search Tweet Requests",
                                  subtitle_create     = "Add New Tweet Request",
                                  subtitle_list       = "Tweet Requests",
                                  label_list_button   = "List Tweet Request",
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
