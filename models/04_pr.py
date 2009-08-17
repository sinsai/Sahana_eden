# -*- coding: utf-8 -*-

#
# Sahanapy VITA - Part 04_pr: Person Tracking and Tracing
#
# created 2009-07-23 by nursix
#

module = 'pr'

#
# Option Fields ---------------------------------------------------------------
#

pr_image_type_opts = {
    1:T('Photograph'),
    2:T('Sketch'),
    3:T('Fingerprint'),
    4:T('X-Ray'),
    5:T('Document Scan'),
    99:T('other')
    }

opt_pr_image_type = SQLTable(None, 'opt_pr_image_type',
                    db.Field('opt_pr_image_type','integer',
                    requires = IS_IN_SET(pr_image_type_opts),
                    default = 1,
                    label = T('Image Type'),
                    represent = lambda opt: opt and pr_image_type_opts[opt]))

pr_presence_condition_opts = {
    1:T('Check-In'),                # Don't change - VITA: Check-In to a location (e.g. accommodation/storage)
    2:T('Check-Out'),               # Don't change - VITA: Check-Out from a location
    3:T('Reconfirmation'),          # Don't change - VITA: Reconfirmation of continuous presence
    4:T('Procedure'),               # Don't change - VITA: Presence for a procedure (temporary)
    5:T('Transfer'),                # Don't change - VITA: Transfer from/to different location
    6:T('Transit'),                 # Don't change - VITA: Transit via the current location
    7:T('Missing'),                 # Don't change - VITA: Missing from a location
    8:T('Lost'),                    # Don't change - VITA: Finally lost, e.g. destroyed/disposed
    9:T('Changed'),                 # Don't change - VITA: Changed tracking item (e.g. Person deceased)
    10:T('Checkpoint'),             # Don't change - VITA: Passing a checkpoint
    99:T('Found')                   # Don't change - VITA: Found (general presence)
    }

opt_pr_presence_condition = SQLTable(None, 'opt_pr_presence_condition',
                        db.Field('opt_pr_presence_condition','integer',
                        requires = IS_IN_SET(pr_presence_condition_opts),
                        default = 99,
                        label = T('Presence Condition'),
                        represent = lambda opt: opt and pr_presence_condition_opts[opt]))

#
# Images ----------------------------------------------------------------------
#
resource = 'image'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_id,
                opt_pr_image_type,
                Field('title'),
                Field('image', 'upload', autodelete=True),
                Field('description'),
                Field('comment'),
                migrate=migrate)

db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

db[table].image.represent = lambda image: DIV(IMG(_src=URL(r=request, c='default', f='download', args=image),_height=60))

title_create = T('Image')
title_display = T('Image Details')
title_list = T('List Images')
title_update = T('Edit Image Details')
title_search = T('Search Images')
subtitle_create = T('Add New Image')
subtitle_list = T('Images')
label_list_button = T('List Images')
label_create_button = T('Add Image')
msg_record_created = T('Image added')
msg_record_modified = T('Image updated')
msg_record_deleted = T('Image deleted')
msg_list_empty = T('No images currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

#
# Presence --------------------------------------------------------------------
#
resource = 'presence'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_id,                           # Personal Entity Reference
                Field('observer'),                  # Person observing
                Field('reporter'),                  # Person reporting
                location_id,                        # Named Location Reference
                Field('location_details'),          # Details on Location
                Field('lat'),                       # Latitude
                Field('lon'),                       # Longitude
                Field('time', 'datetime'),          # Time
                opt_pr_presence_condition,          # Presence Condition
                Field('procedure'),                 # Procedure description (for procedure) TODO: replace by option field?
                Field('origin'),                    # Origin (for transfer and transit) TODO: replace by location reference?
                Field('destination'),               # Destination (for transfer and transit) TODO: replace by location reference?
                Field('comment'),                   # a comment (optional)
                migrate=migrate)
#
# Settings and Restrictions
#
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

# Observer
db[table].observer.requires = IS_NULL_OR(IS_IN_DB(db, 'pr_person.id', '%(id)s: %(first_name)s %(last_name)s'))
db[table].observer.represent = lambda id: (id and [db(db.pr_person.id==id).select()[0].first_name] or ["None"])[0]
db[table].observer.comment = DIV(A(T('Add Person'), _class='popup', _href=URL(r=request, c='pr', f='person', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Create Person Entry|Create a person entry in the registry."))),
db[table].observer.ondelete = 'RESTRICT'

# Reporter
db[table].reporter.requires = IS_NULL_OR(IS_IN_DB(db, 'pr_person.id', '%(id)s: %(first_name)s %(last_name)s'))
db[table].reporter.represent = lambda id: (id and [db(db.pr_person.id==id).select()[0].first_name] or ["None"])[0]
db[table].reporter.comment = DIV(A(T('Add Person'), _class='popup', _href=URL(r=request, c='pr', f='person', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Create Person Entry|Create a person entry in the registry."))),
db[table].reporter.ondelete = 'RESTRICT'

db[table].lat.requires = IS_NULL_OR(IS_LAT())
db[table].lon.requires = IS_NULL_OR(IS_LON())

#
# Labels
#
db[table].time.label = T('Date/Time')

#
# CRUD Strings
#
title_create = T('Presence')
title_display = T('Presence Details')
title_list = T('List Presence Records')
title_update = T('Edit Presence Details')
title_search = T('Search Presence Records')
subtitle_create = T('Add New Presence Record')
subtitle_list = T('Presence Records')
label_list_button = T('List Presence Records')
label_create_button = T('Add Presence Record')
msg_record_created = T('Presence Record added')
msg_record_modified = T('Presence Record updated')
msg_record_deleted = T('Presence Record deleted')
msg_list_empty = T('No presence records currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

#
# Address ---------------------------------------------------------------------
#
resource = 'address'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_id,                               # Person Entity ID
                Field('address_type'),                  # TODO: make option field
                Field('co_name'),                       # c/o Name
                Field('street1'),                       # Street Address 1
                Field('street2'),                       # Street Address 2
                Field('postcode'),                      # ZIP or postal code
                Field('city'),                          # City
                Field('state'),                         # State or Province
                Field('country'),                       # Country TODO: make option field
                location_id,                            # Link to GIS location
                Field('lat'),                           # Latitude
                Field('lon'),                           # Longitude
                Field('comment'),                       # Comment
                migrate=migrate)

db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

db[table].co_name.label = T('c/o Name')
db[table].street1.label = T('Street')
db[table].street2.label = T('Street (add.)')
db[table].postcode.label = T('ZIP/Postcode')

db[table].lat.requires = IS_NULL_OR(IS_LAT())
db[table].lon.requires = IS_NULL_OR(IS_LON())

title_create = T('Add Address')
title_display = T('Address Details')
title_list = T('List Addresses')
title_update = T('Edit Address')
title_search = T('Search Addresses')
subtitle_create = T('Add New Address')
subtitle_list = T('Addresses')
label_list_button = T('List Addresses')
label_create_button = T('Add Address')
msg_record_created = T('Address added')
msg_record_modified = T('Address updated')
msg_record_deleted = T('Address deleted')
msg_list_empty = T('No Addresses currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

#
# Case ------------------------------------------------------------------------
#
resource = 'case'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('description'),               # Short Description
                Field('details','text'),            # Detailed Description
                Field('comment'),                   # a comment (optional)
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

# Reusable field for other tables to reference
pcase_id = SQLTable(None, 'pcase_id',
                Field('pcase_id', db.pr_case,
                requires = IS_NULL_OR(IS_IN_DB(db, 'pr_case.id', '%(description)s')),
                represent = lambda id: (id and [db(db.pr_case.id==id).select()[0].description] or ["None"])[0],
                comment = DIV(A(T('Add Case'), _class='popup', _href=URL(r=request, c='pr', f='case', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Case|Add new case."))),
                ondelete = 'RESTRICT'
                ))

#
# Findings --------------------------------------------------------------------
#
resource = 'finding'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_id,                      # about which entity?
#                opt_pr_findings_type,           # Finding type
                Field('description'),           # Descriptive title
                Field('module'),                # Access module
                Field('resource'),              # Access resource
                Field('resource_id'),           # Access ID
                migrate=migrate)

db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].module.requires = IS_NULL_OR(IS_IN_DB(db, 's3_module.name', '%(name_nice)s'))
db[table].module.represent = lambda name: (name and [db(db.s3_module.name==name).select()[0].name_nice] or ["None"])[0]

#
# Callback functions ----------------------------------------------------------
#

#
# Other functions -------------------------------------------------------------
#
