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
# Create the Request Aid Database
rms_request_aid_type_opts = {
    "1"  : T('1: Emergency'),
    "1A" : T('1A: Collapsed Structure'),
    "1B" : T('1B: Fire'),
    "1C" : T('1C: People Trapped'),
    "1D" : T('1D: Contaminated Water Supply'),
    "1E" : T('1E: Earthquake and Aftershocks'),
    "1F" : T('1F: Medical Emergency'),
    
    "2"  : T('2: Threats'),
    "2A" : T('2A: Structures at Risk'),
    "2B" : T('2B: Looting'),
    
    "3"  : T('3: Vital Lines'),
    "3A" : T('3A: Water Shortage'),
    "3B" : T('3B: Road Blocked'),
    "3C" : T('3C: Power Outage'),
    
    "4"  : T('4: Response'),
    "4A" : T('4A: Health Services'),
    "4B" : T('4B: USAR Search and Rescue'),
    "4C" : T('4C: Shelter'),
    "4D" : T('4D: Food Distribution'),
    "4E" : T('4E: Water Sanitation and Hygiene Promotion'),
    "4F" : T('4F: Non Food Items'),
    "4G" : T('4G: Rubble Removal'),
    "4H" : T('4H: Dead Bodies Management'),

    "5"  : T('5: Other'),
    
    "6"  : T('6: Persons News'),
    "6A" : T('6A: Deaths'),
    "6B" : T('6B: Missing Persons'),
    }

rms_request_aid_type_opts = [
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

rms_source_opts = {
    1:T('Ushahiti'),
    2:T('Sahana'),
    }

resource = 'request_aid'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
    Field("title","string"),
    person_id,
    organisation_id,
    location_id,
    Field("link","string"),
    Field("type", "string"),
    Field("priority", "integer"),
    Field("comment","text"),
    Field("pubdate","datetime"),
    Field("guid","string"),
    Field("verified","boolean"),
    Field("source", "integer"),
    Field("numserved", "integer"),
    Field("item", "string"),
    Field("quantity", "double"),
    Field("unit","string"),
    Field("status", "integer"),
    Field("georss", "string"),
    migrate=migrate)

#db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
#db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
#db[table].name.label = T('Name')
#db[table].name.comment = SPAN("*", _class="req")

#db[table].title.requires = IS_NOT_EMPTY()
#db[table].title.comment = SPAN("*", _class="req")

db[table].type.requires = IS_NULL_OR(IS_IN_SET(rms_request_aid_type_opts))
#db[table].type.represent = lambda opt: opt and rms_request_aid_type_opts[opt]
db[table].type.represent = lambda opt: opt.split(':')[0]
db[table].type.label = T('Aid type')

#db[table].location.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Manager|The person's manager within this Office."))
#db[table].location.comment=A(SPAN("[Help]"), _class="tooltip", _title=T("Location|Enter any available location information, such as street, city, neighborhood, etc."))

# Automatically fill in the posting time:
#db[table].pubdate.default  = request.now
#db[table].pubdate.writable = False
#db[table].pubdate.label    = T("Date/Time")

# Hide the verified field:
db[table].verified.readable = False
db[table].verified.writable = False


db[table].priority.requires = IS_NULL_OR(IS_IN_SET(rms_priority_opts))
db[table].priority.represent = lambda prior: prior and rms_priority_opts[prior]
db[table].priority.label = T('Priority Level')

db[table].status.requires = IS_NULL_OR(IS_IN_SET(rms_status_opts))
db[table].status.represent = lambda status: status and rms_status_opts[status]
db[table].status.label = T('Status')

db[table].source.requires = IS_NULL_OR(IS_IN_SET(rms_source_opts))
#db[table].source.represent = lambda source: source and rms_source_opts[source]
db[table].source.represent = True
db[table].source.label = T('Request Source')

# Hide Source:
db[table].source.readable = False
db[table].source.writable = False

# Hide Guid:
db[table].guid.readable = False
db[table].guid.writable = False

# Hide Link:
db[table].link.readable = False
db[table].link.writable = False

# Hide Status:
db[table].status.readable = False
db[table].status.writable = False

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
# Create the Pledge Aid Database
rms_pledge_aid_type_opts = rms_request_aid_type_opts

resource = 'pledge_aid'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
#    Field('type', 'integer'),
    Field("title","string"),
    person_id,
    organisation_id,
    location_id,
    Field("description","text"),
    Field("pubdate","datetime"),
    Field("guid","string"),
    Field("verified","boolean"),
    Field("source", "integer"),
    Field("item", "string"),
    Field("quantity", "double"),
    Field("unit","string"),
    Field("link","string"),
    migrate=migrate)

#db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
#db[table].name.requires = IS_NOT_EMPTY()
#db[table].name.label = T('Name')
#db[table].name.comment = SPAN("*", _class="req")
#db[table].type.requires = IS_NULL_OR(IS_IN_SET(rms_pledge_aid_type_opts))
#db[table].type.represent = lambda opt: opt and rms_pledge_aid_type_opts[opt]
#db[table].type.label = T('Type')    
 

#db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
#db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
#db[table].name.label = T('Name')
#db[table].name.comment = SPAN("*", _class="req")

#db[table].title.requires = IS_NOT_EMPTY()
#db[table].title.comment = SPAN("*", _class="req")

# db[table].type.requires = IS_NULL_OR(IS_IN_SET(rms_request_aid_type_opts))
# db[table].type.represent = lambda opt: opt and rms_request_aid_type_opts[opt]
# db[table].type.label = T('Aid type')

#db[table].location.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Manager|The person's manager within this Office."))
#db[table].location.comment=A(SPAN("[Help]"), _class="tooltip", _title=T("Location|Enter any available location information, such as street, city, neighborhood, etc."))

# Automatically fill in the posting time:
#db[table].pubdate.default  = request.now
#db[table].pubdate.writable = False
#db[table].pubdate.label    = T("Date/Time")

# Hide Link:
db[table].link.readable = False
db[table].link.writable = False

# Hide Guid:
db[table].guid.readable = False
db[table].guid.writable = False

# Hide Verified:
db[table].verified.readable = False
db[table].verified.writable = False


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

db[table].writeable = False
