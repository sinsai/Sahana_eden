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
# Create request table

resource = 'request_aid'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
    person_id,
    organisation_id,
    location_id,
    Field("priority", "integer"),
    Field("comment","text"),
    Field("pubdate","datetime"),
    Field("verified","boolean"),
    Field("numserved", "integer"),
    migrate=migrate)

# Automatically fill in the posting time:
db[table].pubdate.default  = request.now
db[table].pubdate.writable = False
db[table].pubdate.label    = T("Date/Time")

# Hide the verified field:
db[table].verified.readable = False
db[table].verified.writable = False

db[table].priority.requires = IS_NULL_OR(IS_IN_SET(rms_priority_opts))
db[table].priority.represent = lambda prior: prior and rms_priority_opts[prior]
db[table].priority.label = T('Priority Level')

s3.crud_strings[table] = Storage( title_create        = "Add Aid Request", 
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

# ------------------------------ #    
# Create the Request Items Database

resource = 'request_item'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
    Field("type", "integer"),
    Field("quantity", "double"),
    Field("unit","string"),
    Field("status","integer"),
    Field("req_id", db.rms_request_aid),
    migrate=migrate)
    
#Joined resource (component) for request items subfield
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(rms_request_aid = 'req_id'),
    deletable=True,
    editable=True,
    list_fields = ['id', 'type', 'quantity', 'unit', 'status'])


db[table].status.requires = IS_NULL_OR(IS_IN_SET(rms_status_opts))
db[table].status.represent = lambda status: status and rms_status_opts[status]
db[table].status.label = T('Status')

db[table].type.requires = IS_NULL_OR(IS_IN_SET(rms_type_opts))
db[table].type.represent = lambda opt: rms_type_opts[opt]
db[table].type.label = T('Aid type')

# ------------------------------ #    
# Create the Pledge Aid Database
    
resource = 'pledge_aid'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
    person_id,
    organisation_id,
    location_id,
    Field("priority", "integer"),
    Field("comment","text"),
    Field("pubdate","datetime"),
    Field("verified","boolean"),
    migrate=migrate)


# Automatically fill in the posting time:
db[table].pubdate.default  = request.now
db[table].pubdate.writable = False
db[table].pubdate.label    = T("Date/Time")

# Hide Verified:
db[table].verified.readable = False
db[table].verified.writable = False


db[table].priority.requires = IS_NULL_OR(IS_IN_SET(rms_priority_opts))
db[table].priority.represent = lambda prior: prior and rms_priority_opts[prior]
db[table].priority.label = T('Priority Level')


s3.crud_strings[table] = Storage( title_create        = "Add Pledge of Aid", 
                                  title_display       = "Pledge Details", 
                                  title_list          = "List Pledges", 
                                  title_update        = "Edit Pledges",  
                                  title_search        = "Search Pledges",
                                  subtitle_create     = "Add New Pledge of Aid",
                                  subtitle_list       = "Pledges",
                                  label_list_button   = "List Pledges",
                                  label_create_button = "Add Pledge",
                                  msg_record_created  = "Pledge added",
                                  msg_record_modified = "Pledge updated",
                                  msg_record_deleted  = "Pledge deleted",
                                  msg_list_empty      = "No pledges currently available")

# ------------------
# Create the Pledge Items Database
                             
resource = 'pledge_item'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
    Field("type", "integer"),
    Field("quantity", "double"),
    Field("unit","string"),
    Field("pledge_id", db.rms_pledge_aid),
    migrate=migrate)
       
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(rms_pledge_aid = 'pledge_id'),
    deletable=True,
    editable=True,
    list_fields = ['id', 'type', 'quantity', 'unit'])

db[table].type.requires = IS_NULL_OR(IS_IN_SET(rms_type_opts))
db[table].type.represent = lambda opt: rms_type_opts[opt]
db[table].type.label = T('Aid type')

# ------------------
# Create the table for sms_request for Ushahidi

resource = 'sms_request'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
    Field("sms", "string"),
    Field("notes", "string"),
    Field("phone", "string"), 
    Field("ush_id", "string"), 
    Field("updated", "datetime"),
    Field("title", "string"),
    Field("categorization", "string"), 
    location_id,
    Field("smsrec", "integer"), 
    Field("author", "string"),
    Field("category_term", "string"),
    Field("firstname"), 
    Field("lastname"), 
    Field("status", "string"), 
    Field("address", "text"), 
    Field("city", "string"), 
    Field("department", "string"), 
    Field("summary", "string"), 
    Field("link", "string"),
    migrate=migrate)

# Relable Field Names:
db[table]["sms"      ].label = T("SMS Message")
db[table]["firstname"].label = T("First Name")
db[table]["lastname" ].label = T("Last Name")


# Make some fields invisible:
db[table].ush_id.writable = db[table].ush_id.readable = False
db[table].author.writable = db[table].author.readable = False
db[table]["title"        ].writeable = db[table]["title"        ].readable = False
db[table]["category_term"].writeable = db[table]["category_term"].readable = False
db[table]["smsrec"       ].writeable = db[table]["smsrec"       ].readable = False
db[table]["summary"      ].writeable = db[table]["summary"      ].readable = False
db[table]["link"         ].writeable = db[table]["link"         ].readable = False


if not auth.is_logged_in():
    db[table]["phone"    ].writeable = db[table]["phone"    ].readable = False
    db[table]["firstname"].writeable = db[table]["firstname"].readable = False
    db[table]["lastname" ].writeable = db[table]["lastname" ].readable = False


s3.crud_strings[table] = Storage( title_create        = "Add SMS Request", 
                                  title_display       = "SMS Request Details", 
                                  title_list          = "List SMS Requests", 
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

#db[table].writeable = False
