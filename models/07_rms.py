# -*- coding: utf-8 -*-

module = 'rms'

# ----------------------- #
# Create nice looking dialog for adding organization info
organisation_id = SQLTable(None, 'organisation_id',
            Field('organisation_id', db.or_organisation,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'or_organisation.id', '%(name)s')),
                represent = lambda id: (id and [db(db.or_organisation.id==id).select()[0].name] or ["None"])[0],
                label = T('Organisation'),
                comment = DIV(A(ADD_ORGANISATION, _class='thickbox', _href=URL(r=request, c='or', f='organisation', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_ORGANISATION), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Organisation|The Organisation this record is associated with."))),
                ondelete = 'RESTRICT'
                ))

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
    1:T('Food'),
    2:T('Find'),
    3:T('Water'),
    4:T('Medicine'),
    5:T('Shelter'),
    6:T('Report'),
    }

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

resource = 'aid_request'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
    Field("title","string"),
    person_id,
    organisation_id,
    location_id,
    Field("link","string"),
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

#db[table].type.requires = IS_NULL_OR(IS_IN_SET(rms_request_aid_type_opts))
#db[table].type.represent = lambda opt: opt and rms_request_aid_type_opts[opt]
#db[table].type.label = T('Aid type')

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
db[table].source.represent = lambda source: source and rms_source_opts[source]
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
