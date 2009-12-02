# -*- coding: utf-8 -*-

#
# Sahanapy Person Registry
#
# created 2009-07-23 by nursix
#
# This part defines PR joined resources:
#       - Address
#       - Contact
#       - Image
#       - Presence Log
#       - Physical Descriptions
#       - Identity
#       - Role
#       - Group Membership
#       - Network (network)
#       - Network Membership
#       - Case
#       - Finding

module = 'pr'

# *****************************************************************************
# Address (address)
#
pr_address_type_opts = {
    1:T('Home Address'),
    2:T('Office Address'),
    3:T('Holiday Address'),
    99:T('other')
    }

opt_pr_address_type = SQLTable(None, 'opt_pr_address_type',
                        Field('opt_pr_address_type','integer',
                            requires = IS_IN_SET(pr_address_type_opts),
                            default = 99,
                            label = T('Address Type'),
                            represent = lambda opt: opt and pr_address_type_opts[opt]))

#
# address table ---------------------------------------------------------------
#
resource = 'address'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                    pr_pe_id,                           # Person Entity ID
                    opt_pr_address_type,                # Address type
                    Field('co_name'),                   # c/o Name
                    Field('street1'),                   # Street Address 1
                    Field('street2'),                   # Street Address 2
                    Field('postcode'),                  # ZIP or postal code
                    Field('city'),                      # City
                    Field('state'),                     # State or Province
                    opt_pr_country,                     # Country
                    location_id,                        # Link to GIS location
                    Field('lat'),                       # Latitude
                    Field('lon'),                       # Longitude
                    Field('comment'),                   # Comment
                    migrate=migrate)

# Joined Resource
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby='pr_pe_id',
    deletable=True,
    editable=True,
    list_fields = ['id', 'opt_pr_address_type', 'co_name', 'street1', 'postcode', 'city', 'opt_pr_country'])

# Field validation
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].pr_pe_id.requires = IS_ONE_OF(db, 'pr_pentity.id', shn_pentity_represent, filterby='opt_pr_entity_type', filter_opts=(1, 2))
db[table].lat.requires = IS_NULL_OR(IS_LAT())
db[table].lon.requires = IS_NULL_OR(IS_LON())

# Field representation

# Field labels
db[table].co_name.label = T('c/o Name')
db[table].street1.label = T('Street')
db[table].street2.label = T('Street (add.)')
db[table].postcode.label = T('ZIP/Postcode')
db[table].opt_pr_country.label = T('Country')

# CRUD Strings
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

# *****************************************************************************
# Contact (contact)
#

#
# Contact Methods -------------------------------------------------------------
#
pr_contact_method_opts = {
    1:T('E-Mail'),
    2:T('Telephone'),
    3:T('Mobile Phone'),
    4:T('Fax'),
    99:T('other')
    }

opt_pr_contact_method = SQLTable(None, 'opt_pr_contact_method',
                        Field('opt_pr_contact_method', 'integer',
                            requires = IS_IN_SET(pr_contact_method_opts),
                            default = 99,
                            label = T('Contact Method'),
                            represent = lambda opt: opt and pr_contact_method_opts[opt]))

#
# contact table ---------------------------------------------------------------
#
resource = 'contact'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_id,                               # Person Entity ID
                Field('name'),                          # Contact name (optional)
                opt_pr_contact_method,                  # Contact Method
                Field('person_name'),                   # Contact person name
                Field('priority'),                      # Priority
                Field('value', notnull=True),
                Field('comment'),                       # Comment
                migrate=migrate)

# Joined Resource
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby='pr_pe_id',
    deletable=True,
    editable=True,
    list_fields = ['id', 'name', 'person_name', 'opt_pr_contact_method', 'value', 'priority'])

# Field validation
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].pr_pe_id.requires = IS_ONE_OF(db, 'pr_pentity.id', shn_pentity_represent, filterby='opt_pr_entity_type', filter_opts=(1, 2))
db[table].value.requires = IS_NOT_EMPTY()
db[table].priority.requires = IS_IN_SET([1,2,3,4,5,6,7,8,9])

# Field representation

# Field labels

# CRUD Strings
title_create = T('Add Contact')
title_display = T('Contact Details')
title_list = T('List Contacts')
title_update = T('Edit Contact')
title_search = T('Search Contacts')
subtitle_create = T('Add New Contact')
subtitle_list = T('Contacts')
label_list_button = T('List Contacts')
label_create_button = T('Add Contact')
msg_record_created = T('Contact added')
msg_record_modified = T('Contact updated')
msg_record_deleted = T('Contact deleted')
msg_list_empty = T('No Contacts currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# *****************************************************************************
# Image (image)
#

#
# Image Types -----------------------------------------------------------------
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
                    db.Field('opt_pr_image_type', 'integer',
                    requires = IS_IN_SET(pr_image_type_opts),
                    default = 1,
                    label = T('Image Type'),
                    represent = lambda opt: opt and pr_image_type_opts[opt]))

#
# image table -----------------------------------------------------------------
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

# Joined Resource
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby='pr_pe_id',
    deletable=True,
    editable=True,
    list_fields = ['id', 'opt_pr_image_type', 'image', 'title','description'])

# Field validation
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

# Field representation
db[table].image.represent = lambda image: DIV(IMG(_src=URL(r=request, c='default', f='download', args=image),_height=60))

# Field labels

# CRUD Strings
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
msg_list_empty = T('No Images currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# *****************************************************************************
# Presence Log (presence)
#

#
# Presence Conditions ---------------------------------------------------------
#
pr_presence_condition_opts = vita.presence_conditions

opt_pr_presence_condition = SQLTable(None, 'opt_pr_presence_condition',
                        Field('opt_pr_presence_condition', 'integer',
                            requires = IS_IN_SET(pr_presence_condition_opts),
                            default = vita.DEFAULT_PRESENCE,
                            label = T('Presence Condition'),
                            represent = lambda opt: opt and pr_presence_condition_opts[opt]))

#
# presence table --------------------------------------------------------------
#
resource = 'presence'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_id,                           # Personal Entity Reference
                Field('observer', db.pr_person),    # Person observing
                Field('reporter', db.pr_person),    # Person reporting
                location_id,                        # Named Location Reference
                Field('location_details'),          # Details on Location
                Field('lat'),                       # Latitude
                Field('lon'),                       # Longitude
                Field('time', 'datetime'),          # Time
                opt_pr_presence_condition,          # Presence Condition
                Field('proc_desc'),                 # Procedure description (for procedure) TODO: replace by option field?
                Field('origin'),                    # Origin (for transfer and transit) TODO: replace by location reference?
                Field('destination'),               # Destination (for transfer and transit) TODO: replace by location reference?
                Field('comment'),                   # a comment (optional)
                migrate=migrate)

# RSS
def shn_pr_presence_rss(record):
    if record:
        if record.location_details and len(record.location_details.strip())>0:
            location_details = record.location_details.strip()
        else:
            location_details = None
        return "<b>%s</b>: %s %s<br/>[Lat: %s Lon: %s]<br/>%s" % (
            pr_presence_condition_opts[record.opt_pr_presence_condition],
            record.location and location_id.location.represent(record.location) or "Unknown location",
            location_details and "/ %s" % location_details or "",
            record.lat and "Lat: %s " % record.lat or "",
            record.lon and "Lon: %s " % record.lon or "",
#            opt_pr_presence_condition.opt_pr_presence_condition.represent(record.opt_pr_presence_condition),
            record.proc_desc or "-")
    else:
        return None

# Joined Resource
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby='pr_pe_id',
    deletable=True,
    editable=True,
    main='time', extra='location_details',
    rss=dict(
        title="%(time)s",
        description=shn_pr_presence_rss
    ),
    list_fields = ['id','time','location','location_details','lat','lon','opt_pr_presence_condition','origin','destination'])

# Field validation
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].lat.requires = IS_NULL_OR(IS_LAT())
db[table].lon.requires = IS_NULL_OR(IS_LON())

# Field representation
db[table].observer.requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_person.id', shn_pr_person_represent))
db[table].observer.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
db[table].observer.comment = shn_person_comment
db[table].observer.ondelete = 'RESTRICT'

db[table].reporter.requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_person.id', shn_pr_person_represent))
db[table].reporter.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
db[table].reporter.comment = shn_person_comment
db[table].reporter.ondelete = 'RESTRICT'

db[table].time.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(), allow_future=False)
db[table].time.represent = lambda value: shn_as_local_time(value)

# Field labels
db[table].time.label = T('Date/Time')

# CRUD Strings
title_create = T('Add Log Entry')
title_display = T('Log Entry Details')
title_list = T('Presence Log')
title_update = T('Edit Log Entry')
title_search = T('Search Log Entry')
subtitle_create = T('Add New Log Entry')
subtitle_list = T('Current Log Entries')
label_list_button = T('List Log Entries')
label_create_button = T('Add Log Entry')
msg_record_created = T('Log entry added')
msg_record_modified = T('Log entry updated')
msg_record_deleted = T('Log entry deleted')
msg_list_empty = T('No Presence Log Entries currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# *****************************************************************************
# Physical Description (pd_xxx)
#   - for identification purposes
#   - following Interpol DVI Forms http://www.interpol.int/Public/DisasterVictim/Forms
#   - appliable for both Missing Persons and Dead Bodies
#
#   TODO: elaborate on field types and field options!
#

pr_pe_id2 = SQLTable(None, 'pr_pe_id',
                    Field('pr_pe_id', db.pr_pentity,
                    requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_pentity.id', shn_pentity_represent, filterby='opt_pr_entity_type', filter_opts=[1,3])),
                    represent = lambda id: (id and [shn_pentity_represent(id)] or ["None"])[0],
                    ondelete = 'RESTRICT',
                    label = T('ID')
                ))
#
# Field options ---------------------------------------------------------------
#
pr_pd_bodily_constitution_opts = {
    1:T('light'),
    2:T('medium'),
    3:T('heavy'),
    99:T('Data not available')
    }
# D2-44/01 Lips, Shape
# D2-39/03 Eyes, Distance between Eyes
# D2-40/01 Nose, size
# D2-42/01 Ears, size
# D2-43/01 Mouth, Size
# D3-47/01 Chin, Size
# D3-49/01 Hands, Size
pr_pd_size_opts = {
    1:T('small'),
    2:T('medium'),
    3:T('large'),
    99:T('Data not available')
    }
# D3-48/01 Neck, Length
# D3-49/02 Hands, Nail length
pr_pd_length_opts = {
    1:T('short'),
    2:T('medium'),
    3:T('long'),
    99:T('Data not available')
    }
# D3-48/01 Neck, Shape
# D1-36/05 Hair of the head, Thickness
# D2-38/01 Eyebrows, Thickness
pr_pd_thickness_opts = {
    1:T('thin'),
    2:T('medium'),
    3:T('thick'),
    99:T('Data not available')
    }
# D1-36/03 Hair of the head, Colour
# D2-41/02 Facial hair, Colour
# D3-51/02 Body hair, Colour
# D3-52/02 Pubic hair, Colour
pr_pd_hair_colour_opts = {
    1:T('blond'),
    2:T('brown'),
    3:T('black'),
    4:T('red'),
    5:T('grey'),
    6:T('white'),
    99:T('Data not available')
    }
pr_pd_race_group_opts = {                    # D1-35/01 Race, group
    1:T('caucasoid'),
    2:T('mongoloid'),
    3:T('negroid'),
    99:T('Data not available')
    }
pr_pd_race_complexion_opts = {               # D1-35/01 Race, complexion
    1:T('light'),
    2:T('medium'),
    3:T('dark'),
    99:T('Data not available')
    }
pr_pd_head_form_front_opts = {               # D1-34/02 Head form, front
    1:T('oval'),
    2:T('pointheaded'),
    3:T('pyramidal'),
    4:T('circular'),
    5:T('rectangular'),
    6:T('quadrangular'),
    99:T('Data not available')
    }
pr_pd_head_form_profile_opts = {             # D1-34/03 Head form, profile
    1:T('shallow'),
    2:T('medium'),
    3:T('deep'),
    99:T('Data not available')
    }
pr_pd_hair_head_type_opts = {                # D1-36/01 Hair of the head, Type
    1:T('natural'),
    2:T('artificial'),
    3:T('Hair-piece'),
    4:T('Wig'),
    5:T('braided'),
    6:T('implanted'),
    99:T('Data not available')
    }
pr_pd_hair_head_length_opts = {              # D1-36/02 Hair of the head, Length
    1:T('short<6cm'),
    2:T('medium<12cm'),
    3:T('long>12cm'),
    4:T('shaved'),
    99:T('Data not available')
    }
pr_pd_hair_head_shade_opts = {               # D1-36/04 Hair of the head, Shade of colour
    1:T('light'),
    2:T('medium'),
    3:T('dark'),
    4:T('turning grey'),
    5:T('dyed'),
    6:T('streaked'),
    99:T('Data not available')
    }
pr_pd_hair_head_style_opts = {               # D1-36/06 Hair of the head, Style
    1:T('straight'),
    2:T('wavy'),
    3:T('curly'),
    99:T('Data not available')
    }
pr_pd_hair_head_parting_opts = {             # D1-36/06 Hair of the head, Parting
    1:T('left'),
    2:T('right'),
    3:T('middle'),
    99:T('Data not available')
    }
pr_pd_hair_head_baldness_ext_opts = {        # D1-36/07 Hair of the head, Baldness (extent)
    1:T('beginning'),
    2:T('advanced'),
    3:T('total'),
    99:T('Data not available')
    }
pr_pd_hair_head_baldness_loc_opts = {        # D1-36/07 Hair of the head, Baldness (location)
    1:T('forehead'),
    2:T('sides'),
    3:T('tonsure'),
    99:T('Data not available')
    }
pr_pd_forehead_height_opts = {               # D2-37/01 Forehead, Height
    1:T('low'),
    2:T('medium'),
    3:T('high'),
    99:T('Data not available')
    }
pr_pd_forehead_width_opts = {                # D2-37/01 Forehead, Width
    1:T('narrow'),
    2:T('medium'),
    3:T('wide'),
    99:T('Data not available')
    }
pr_pd_forehead_inclination_opts = {          # D2-37/02 Forehead, Inclination
    1:T('protruding'),
    2:T('vertical'),
    3:T('slightly receding'),
    4:T('clearly receding'),
    99:T('Data not available')
    }
pr_pd_eyebrows_shape_opts = {                # D2-38/01 Eyebrows, Shape
    1:T('straight'),
    2:T('arched'),
    3:T('joining'),
    99:T('Data not available')
    }
pr_pd_eyebrows_peculiarities_opts = {        # D2-38/02 Eyebrows, Peculiarities
    1:T('plucked'),
    2:T('tattooed'),
    99:T('Data not available')
    }
pr_pd_eyes_colour_opts = {                   # D2-39/01 Eyes, Colour
    1:T('blue'),
    2:T('grey'),
    3:T('green'),
    4:T('brown'),
    5:T('black'),
    99:T('Data not available')
    }
pr_pd_eyes_shade_opts = {                    # D2-39/02 Eyes, Shade
    1:T('light'),
    2:T('medium'),
    3:T('dark'),
    4:T('mixed'),
    99:T('Data not available')
    }
pr_pd_eyes_peculiarities_opts = {            # D2-39/04 Eyes, Peculiarities
    1:T('cross-eyed'),
    2:T('squint-eyed'),
    3:T('Artificial eye left'),
    4:T('Artificial eye right'),
    99:T('Data not available')
    }
pr_pd_nose_shape_opts = {                    # D2-40/01 Nose, shape
    1:T('pointed'),
    2:T('Roman'),
    3:T('Alcoholics'),
    4:T('misshapen'),
    99:T('Data not available')
    }
pr_pd_nose_curve_opts = {                    # D2-40/03 Nose, Curve
    1:T('concave'),
    2:T('straight'),
    3:T('convex'),
    99:T('Data not available')
    }
pr_pd_nose_angle_opts = {                    # D2-40/03 Nose, Angle
    1:T('turned down'),
    2:T('horizontal'),
    3:T('turned up'),
    99:T('Data not available')
    }
pr_pd_hair_facial_type_opts = {              # D2-41/01 Facial hair, Type
    1:T('No beard'),
    2:T('Moustache'),
    3:T('Goatee'),
    4:T('Whiskers'),
    5:T('Full beard'),
    99:T('Data not available')
    }
pr_pd_ears_angle_opts = {                    # D2-42/01 Ears, angle
    1:T('close-set'),
    2:T('medium'),
    3:T('protruding'),
    99:T('Data not available')
    }
pr_pd_chin_inclination_opts = {              # D3-47/01 Chin, Inclination
    1:T('receding'),
    2:T('medium'),
    3:T('protruding'),
    99:T('Data not available')
    }
pr_pd_chin_shape_opts = {                    # D3-47/02 Chin, Shape
    1:T('pointed'),
    2:T('round'),
    3:T('angular'),
    4:T('Cleft chin'),
    5:T('groove'),
    99:T('Data not available')
    }
# D2-45/02 Teeth, Gaps between front teeth
# D2-45/02 Teeth, Missing teeth
# D2-45/02 Teeth, Toothless
pr_pd_ul_opts = {
    1:T('upper'),
    2:T('lower'),
    3:T('upper+lower'),
    99:T('Data not available')
    }
pr_pd_teeth_dentures_lower_opts = {          # D2-45/03 Teeth, Dentures
    1:T('part'),
    2:T('full'),
    99:T('Data not available')
    }
pr_pd_teeth_dentures_upper_opts = {          # D2-45/03 Teeth, Dentures
    1:T('part'),
    2:T('full'),
    99:T('Data not available')
    }
pr_pd_neck_peculiarities_opts = {            # D3-48/02 Neck, Peculiarities
    1:T('Goitre'),
    2:T('Prominent Adams apple'),
    99:T('Data not available')
    }
pr_pd_hands_shape_opts = {                   # D3-49/01 Hands, Shape
    1:T('slender'),
    2:T('medium'),
    3:T('broad'),
    99:T('Data not available')
    }
pr_pd_hands_nails_peculiarities_opts = {     # D3-49/03 Hands, Nail peculiarities
    1:T('bitten short'),
    2:T('manicured'),
    3:T('painted'),
    4:T('artificial'),
    99:T('Data not available')
    }
pr_pd_hands_nicotine_opts = {                # D3-49/03 Hands, Nicotine
    1:T('left'),
    2:T('right'),
    99:T('Data not available')
    }
pr_pd_feet_shape_opts = {                    # D3-50/01 Feet, Shape
    1:T('slender'),
    2:T('medium'),
    3:T('broad'),
    4:T('flatfooted'),
    5:T('arched'),
    99:T('Data not available')
    }
pr_pd_feet_condition_opts = {                # D3-50/02 Feet, Condition
    1:T('Bunion'),
    2:T('Corn'),
    99:T('Data not available')
    }
pr_pd_feet_nails_opts = {                    # D3-50/02 Feet, Nails
    1:T('painted'),
    2:T('defective'),
    99:T('Data not available')
    }
pr_pd_hair_body_extent_opts = {              # D3-51/01 Body hair, Extent
    1:T('none'),
    2:T('slight'),
    3:T('medium'),
    4:T('pronounced'),
    99:T('Data not available')
    }
pr_pd_hair_pubic_extent_opts = {             # D3-52/01 Pubic hair, Extent
    1:T('none'),
    2:T('slight'),
    3:T('medium'),
    4:T('pronounced'),
    5:T('shaved'),
    99:T('Data not available')
    }
pr_pd_smoking_habits_opts = {                # D2-46/01 Smoking Habits, Type
    1:T('none'),
    2:T('Cigarettes'),
    3:T('Cigars'),
    4:T('Pipe'),
    5:T('Chewing tobacco'),
    99:T('Data not available')
    }

opt_pr_pd_bodily_constitution = SQLTable(None, 'opt_pr_pd_bodily_constitution',
                                db.Field('opt_pr_pd_bodily_constitution', 'integer',
                                requires = IS_IN_SET(pr_pd_bodily_constitution_opts),
                                default = 99,
                                label = T('Bodily Constitution'),
                                represent = lambda opt: opt and pr_pd_bodily_constitution_opts[opt]))

opt_pr_pd_race_group = SQLTable(None, 'opt_pr_pd_race_group',
                                db.Field('opt_pr_pd_race_group', 'integer',
                                requires = IS_IN_SET(pr_pd_race_group_opts),
                                default = 99,
                                label = T('Race group'),
                                represent = lambda opt: opt and pr_pd_race_group_opts[opt]))

opt_pr_pd_race_complexion = SQLTable(None, 'opt_pr_pd_race_complexion',
                                db.Field('opt_pr_pd_race_complexion', 'integer',
                                requires = IS_IN_SET(pr_pd_race_complexion_opts),
                                default = 99,
                                label = T('Race, complexion'),
                                represent = lambda opt: opt and pr_pd_race_complexion_opts[opt]))

opt_pr_pd_head_form_front = SQLTable(None, 'opt_pr_pd_head_form_front',
                                db.Field('opt_pr_pd_head_form_front', 'integer',
                                requires = IS_IN_SET(pr_pd_head_form_front_opts),
                                default = 99,
                                label = T('Head form, front'),
                                represent = lambda opt: opt and pr_pd_head_form_front_opts[opt]))

opt_pr_pd_head_form_profile = SQLTable(None, 'opt_pr_pd_head_form_profile',
                                db.Field('opt_pr_pd_head_form_profile', 'integer',
                                requires = IS_IN_SET(pr_pd_head_form_profile_opts),
                                default = 99,
                                label = T('Head form, profile'),
                                represent = lambda opt: opt and pr_pd_head_form_profile_opts[opt]))

opt_pr_pd_hair_head_type = SQLTable(None, 'opt_pr_pd_hair_head_type',
                                db.Field('opt_pr_pd_hair_head_type', 'integer',
                                requires = IS_IN_SET(pr_pd_hair_head_type_opts),
                                default = 99,
                                label = T('Hair of the head, Type'),
                                represent = lambda opt: opt and pr_pd_hair_head_type_opts[opt]))

opt_pr_pd_hair_head_length = SQLTable(None, 'opt_pr_pd_hair_head_length',
                                db.Field('opt_pr_pd_hair_head_length', 'integer',
                                requires = IS_IN_SET(pr_pd_hair_head_length_opts),
                                default = 99,
                                label = T('Hair of the head, Length'),
                                represent = lambda opt: opt and pr_pd_hair_head_length_opts[opt]))

opt_pr_pd_hair_head_colour = SQLTable(None, 'opt_pr_pd_hair_head_colour',
                                db.Field('opt_pr_pd_hair_head_colour', 'integer',
                                requires = IS_IN_SET(pr_pd_hair_colour_opts),
                                default = 99,
                                label = T('Hair of the head, Colour'),
                                represent = lambda opt: opt and pr_pd_hair_colour_opts[opt]))

opt_pr_pd_hair_head_shade = SQLTable(None, 'opt_pr_pd_hair_head_shade',
                                db.Field('opt_pr_pd_hair_head_shade', 'integer',
                                requires = IS_IN_SET(pr_pd_hair_head_shade_opts),
                                default = 99,
                                label = T('Hair of the head, Shade of colour'),
                                represent = lambda opt: opt and pr_pd_hair_head_shade_opts[opt]))

opt_pr_pd_hair_head_thickness = SQLTable(None, 'opt_pr_pd_hair_head_thickness',
                                db.Field('opt_pr_pd_hair_head_thickness', 'integer',
                                requires = IS_IN_SET(pr_pd_thickness_opts),
                                default = 99,
                                label = T('Hair of the head, Thickness'),
                                represent = lambda opt: opt and pr_pd_thickness_opts[opt]))

opt_pr_pd_hair_head_style = SQLTable(None, 'opt_pr_pd_hair_head_style',
                                db.Field('opt_pr_pd_hair_head_style', 'integer',
                                requires = IS_IN_SET(pr_pd_hair_head_style_opts),
                                default = 99,
                                label = T('Hair of the head, Style'),
                                represent = lambda opt: opt and pr_pd_hair_head_style_opts[opt]))

opt_pr_pd_hair_head_parting = SQLTable(None, 'opt_pr_pd_hair_head_parting',
                                db.Field('opt_pr_pd_hair_head_parting', 'integer',
                                requires = IS_IN_SET(pr_pd_hair_head_parting_opts),
                                default = 99,
                                label = T('Hair of the head, Parting'),
                                represent = lambda opt: opt and pr_pd_hair_head_parting_opts[opt]))

opt_pr_pd_hair_head_baldness_ext = SQLTable(None, 'opt_pr_pd_hair_head_baldness_ext',
                                db.Field('opt_pr_pd_hair_head_baldness_ext', 'integer',
                                requires = IS_IN_SET(pr_pd_hair_head_baldness_ext_opts),
                                default = 99,
                                label = T('Hair of the head, Baldness (extent)'),
                                represent = lambda opt: opt and pr_pd_hair_head_baldness_ext_opts[opt]))

opt_pr_pd_hair_head_baldness_loc = SQLTable(None, 'opt_pr_pd_hair_head_baldness_loc',
                                db.Field('opt_pr_pd_hair_head_baldness_loc', 'integer',
                                requires = IS_IN_SET(pr_pd_hair_head_baldness_loc_opts),
                                default = 99,
                                label = T('Hair of the head, Baldness (location)'),
                                represent = lambda opt: opt and pr_pd_hair_head_baldness_loc_opts[opt]))

opt_pr_pd_forehead_height = SQLTable(None, 'opt_pr_pd_forehead_height',
                                db.Field('opt_pr_pd_forehead_height', 'integer',
                                requires = IS_IN_SET(pr_pd_forehead_height_opts),
                                default = 99,
                                label = T('Forehead, Height'),
                                represent = lambda opt: opt and pr_pd_forehead_height_opts[opt]))

opt_pr_pd_forehead_width = SQLTable(None, 'opt_pr_pd_forehead_width',
                                db.Field('opt_pr_pd_forehead_width', 'integer',
                                requires = IS_IN_SET(pr_pd_forehead_width_opts),
                                default = 99,
                                label = T('Forehead, Width'),
                                represent = lambda opt: opt and pr_pd_forehead_width_opts[opt]))

opt_pr_pd_forehead_inclination = SQLTable(None, 'opt_pr_pd_forehead_inclination',
                                db.Field('opt_pr_pd_forehead_inclination', 'integer',
                                requires = IS_IN_SET(pr_pd_forehead_inclination_opts),
                                default = 99,
                                label = T('Forehead, Inclination'),
                                represent = lambda opt: opt and pr_pd_forehead_inclination_opts[opt]))

opt_pr_pd_eyebrows_shape = SQLTable(None, 'opt_pr_pd_eyebrows_shape',
                                db.Field('opt_pr_pd_eyebrows_shape', 'integer',
                                requires = IS_IN_SET(pr_pd_eyebrows_shape_opts),
                                default = 99,
                                label = T('Eyebrows, Shape'),
                                represent = lambda opt: opt and pr_pd_eyebrows_shape_opts[opt]))

opt_pr_pd_eyebrows_thickness = SQLTable(None, 'opt_pr_pd_eyebrows_thickness',
                                db.Field('opt_pr_pd_eyebrows_thickness', 'integer',
                                requires = IS_IN_SET(pr_pd_thickness_opts),
                                default = 99,
                                label = T('Eyebrows, Thickness'),
                                represent = lambda opt: opt and pr_pd_thickness_opts[opt]))

opt_pr_pd_eyebrows_peculiarities = SQLTable(None, 'opt_pr_pd_eyebrows_peculiarities',
                                db.Field('opt_pr_pd_eyebrows_peculiarities', 'integer',
                                requires = IS_IN_SET(pr_pd_eyebrows_peculiarities_opts),
                                default = 99,
                                label = T('Eyebrows, Peculiarities'),
                                represent = lambda opt: opt and pr_pd_eyebrows_peculiarities_opts[opt]))

opt_pr_pd_eyes_colour = SQLTable(None, 'opt_pr_pd_eyes_colour',
                                db.Field('opt_pr_pd_eyes_colour', 'integer',
                                requires = IS_IN_SET(pr_pd_eyes_colour_opts),
                                default = 99,
                                label = T('Eyes, Colour'),
                                represent = lambda opt: opt and pr_pd_eyes_colour_opts[opt]))

opt_pr_pd_eyes_shade = SQLTable(None, 'opt_pr_pd_eyes_shade',
                                db.Field('opt_pr_pd_eyes_shade', 'integer',
                                requires = IS_IN_SET(pr_pd_eyes_shade_opts),
                                default = 99,
                                label = T('Eyes, Shade'),
                                represent = lambda opt: opt and pr_pd_eyes_shade_opts[opt]))

opt_pr_pd_eyes_distance = SQLTable(None, 'opt_pr_pd_eyes_distance',
                                db.Field('opt_pr_pd_eyes_distance', 'integer',
                                requires = IS_IN_SET(pr_pd_size_opts),
                                default = 99,
                                label = T('Eyes, Distance between Eyes'),
                                represent = lambda opt: opt and pr_pd_size_opts[opt]))

opt_pr_pd_eyes_peculiarities = SQLTable(None, 'opt_pr_pd_eyes_peculiarities',
                                db.Field('opt_pr_pd_eyes_peculiarities', 'integer',
                                requires = IS_IN_SET(pr_pd_eyes_peculiarities_opts),
                                default = 99,
                                label = T('Eyes, Peculiarities'),
                                represent = lambda opt: opt and pr_pd_eyes_peculiarities_opts[opt]))

opt_pr_pd_nose_size = SQLTable(None, 'opt_pr_pd_nose_size',
                                db.Field('opt_pr_pd_nose_size', 'integer',
                                requires = IS_IN_SET(pr_pd_size_opts),
                                default = 99,
                                label = T('Nose, size'),
                                represent = lambda opt: opt and pr_pd_size_opts[opt]))

opt_pr_pd_nose_shape = SQLTable(None, 'opt_pr_pd_nose_shape',
                                db.Field('opt_pr_pd_nose_shape', 'integer',
                                requires = IS_IN_SET(pr_pd_nose_shape_opts),
                                default = 99,
                                label = T('Nose, shape'),
                                represent = lambda opt: opt and pr_pd_nose_shape_opts[opt]))

opt_pr_pd_nose_curve = SQLTable(None, 'opt_pr_pd_nose_curve',
                                db.Field('opt_pr_pd_nose_curve', 'integer',
                                requires = IS_IN_SET(pr_pd_nose_curve_opts),
                                default = 99,
                                label = T('Nose, Curve'),
                                represent = lambda opt: opt and pr_pd_nose_curve_opts[opt]))

opt_pr_pd_nose_angle = SQLTable(None, 'opt_pr_pd_nose_angle',
                                db.Field('opt_pr_pd_nose_angle', 'integer',
                                requires = IS_IN_SET(pr_pd_nose_angle_opts),
                                default = 99,
                                label = T('Nose, Angle'),
                                represent = lambda opt: opt and pr_pd_nose_angle_opts[opt]))

opt_pr_pd_hair_facial_type = SQLTable(None, 'opt_pr_pd_hair_facial_type',
                                db.Field('opt_pr_pd_hair_facial_type', 'integer',
                                requires = IS_IN_SET(pr_pd_hair_facial_type_opts),
                                default = 99,
                                label = T('Facial hair, Type'),
                                represent = lambda opt: opt and pr_pd_hair_facial_type_opts[opt]))

opt_pr_pd_hair_facial_colour = SQLTable(None, 'opt_pr_pd_hair_facial_colour',
                                db.Field('opt_pr_pd_hair_facial_colour', 'integer',
                                requires = IS_IN_SET(pr_pd_hair_colour_opts),
                                default = 99,
                                label = T('Facial hair, Colour'),
                                represent = lambda opt: opt and pr_pd_hair_colour_opts[opt]))

opt_pr_pd_ears_size = SQLTable(None, 'opt_pr_pd_ears_size',
                                db.Field('opt_pr_pd_ears_size', 'integer',
                                requires = IS_IN_SET(pr_pd_size_opts),
                                default = 99,
                                label = T('Ears, size'),
                                represent = lambda opt: opt and pr_pd_size_opts[opt]))

opt_pr_pd_ears_angle = SQLTable(None, 'opt_pr_pd_ears_angle',
                                db.Field('opt_pr_pd_ears_angle', 'integer',
                                requires = IS_IN_SET(pr_pd_ears_angle_opts),
                                default = 99,
                                label = T('Ears, angle'),
                                represent = lambda opt: opt and pr_pd_ears_angle_opts[opt]))

opt_pr_pd_mouth_size = SQLTable(None, 'opt_pr_pd_mouth_size',
                                db.Field('opt_pr_pd_mouth_size', 'integer',
                                requires = IS_IN_SET(pr_pd_size_opts),
                                default = 99,
                                label = T('Mouth, Size'),
                                represent = lambda opt: opt and pr_pd_size_opts[opt]))

opt_pr_pd_lips_shape = SQLTable(None, 'opt_pr_pd_lips_shape',
                                db.Field('opt_pr_pd_lips_shape', 'integer',
                                requires = IS_IN_SET(pr_pd_thickness_opts),
                                default = 99,
                                label = T('Lips, Shape'),
                                represent = lambda opt: opt and pr_pd_thickness_opts[opt]))

opt_pr_pd_chin_size = SQLTable(None, 'opt_pr_pd_chin_size',
                                db.Field('opt_pr_pd_chin_size', 'integer',
                                requires = IS_IN_SET(pr_pd_size_opts),
                                default = 99,
                                label = T('Chin, Size'),
                                represent = lambda opt: opt and pr_pd_size_opts[opt]))

opt_pr_pd_chin_inclination = SQLTable(None, 'opt_pr_pd_chin_inclination',
                                db.Field('opt_pr_pd_chin_inclination', 'integer',
                                requires = IS_IN_SET(pr_pd_chin_inclination_opts),
                                default = 99,
                                label = T('Chin, Inclination'),
                                represent = lambda opt: opt and pr_pd_chin_inclination_opts[opt]))

opt_pr_pd_chin_shape = SQLTable(None, 'opt_pr_pd_chin_shape',
                                db.Field('opt_pr_pd_chin_shape', 'integer',
                                requires = IS_IN_SET(pr_pd_chin_shape_opts),
                                default = 99,
                                label = T('Chin, Shape'),
                                represent = lambda opt: opt and pr_pd_chin_shape_opts[opt]))

opt_pr_pd_teeth_gaps = SQLTable(None, 'opt_pr_pd_teeth_gaps',
                                db.Field('opt_pr_pd_teeth_gaps', 'integer',
                                requires = IS_IN_SET(pr_pd_ul_opts),
                                default = 99,
                                label = T('Teeth, Gaps between front teeth'),
                                represent = lambda opt: opt and pr_pd_ul_opts[opt]))

opt_pr_pd_teeth_missing = SQLTable(None, 'opt_pr_pd_teeth_missing',
                                db.Field('opt_pr_pd_teeth_missing', 'integer',
                                requires = IS_IN_SET(pr_pd_ul_opts),
                                default = 99,
                                label = T('Teeth, Missing teeth'),
                                represent = lambda opt: opt and pr_pd_ul_opts[opt]))

opt_pr_pd_teeth_toothless = SQLTable(None, 'opt_pr_pd_teeth_toothless',
                                db.Field('opt_pr_pd_teeth_toothless', 'integer',
                                requires = IS_IN_SET(pr_pd_ul_opts),
                                default = 99,
                                label = T('Teeth, Toothless'),
                                represent = lambda opt: opt and pr_pd_ul_opts[opt]))

opt_pr_pd_teeth_dentures_lower = SQLTable(None, 'opt_pr_pd_teeth_dentures_lower',
                                db.Field('opt_pr_pd_teeth_dentures_lower', 'integer',
                                requires = IS_IN_SET(pr_pd_teeth_dentures_lower_opts),
                                default = 99,
                                label = T('Teeth, Dentures'),
                                represent = lambda opt: opt and pr_pd_teeth_dentures_lower_opts[opt]))

opt_pr_pd_teeth_dentures_upper = SQLTable(None, 'opt_pr_pd_teeth_dentures_upper',
                                db.Field('opt_pr_pd_teeth_dentures_upper', 'integer',
                                requires = IS_IN_SET(pr_pd_teeth_dentures_upper_opts),
                                default = 99,
                                label = T('Teeth, Dentures'),
                                represent = lambda opt: opt and pr_pd_teeth_dentures_upper_opts[opt]))

opt_pr_pd_neck_length = SQLTable(None, 'opt_pr_pd_neck_length',
                                db.Field('opt_pr_pd_neck_length', 'integer',
                                requires = IS_IN_SET(pr_pd_length_opts),
                                default = 99,
                                label = T('Neck, Length'),
                                represent = lambda opt: opt and pr_pd_length_opts[opt]))

opt_pr_pd_neck_shape = SQLTable(None, 'opt_pr_pd_neck_shape',
                                db.Field('opt_pr_pd_neck_shape', 'integer',
                                requires = IS_IN_SET(pr_pd_thickness_opts),
                                default = 99,
                                label = T('Neck, Shape'),
                                represent = lambda opt: opt and pr_pd_thickness_opts[opt]))

opt_pr_pd_neck_peculiarities = SQLTable(None, 'opt_pr_pd_neck_peculiarities',
                                db.Field('opt_pr_pd_neck_peculiarities', 'integer',
                                requires = IS_IN_SET(pr_pd_neck_peculiarities_opts),
                                default = 99,
                                label = T('Neck, Peculiarities'),
                                represent = lambda opt: opt and pr_pd_neck_peculiarities_opts[opt]))

opt_pr_pd_hands_shape = SQLTable(None, 'opt_pr_pd_hands_shape',
                                db.Field('opt_pr_pd_hands_shape', 'integer',
                                requires = IS_IN_SET(pr_pd_hands_shape_opts),
                                default = 99,
                                label = T('Hands, Shape'),
                                represent = lambda opt: opt and pr_pd_hands_shape_opts[opt]))

opt_pr_pd_hands_size = SQLTable(None, 'opt_pr_pd_hands_size',
                                db.Field('opt_pr_pd_hands_size', 'integer',
                                requires = IS_IN_SET(pr_pd_size_opts),
                                default = 99,
                                label = T('Hands, Size'),
                                represent = lambda opt: opt and pr_pd_size_opts[opt]))

opt_pr_pd_hands_nails_length = SQLTable(None, 'opt_pr_pd_hands_nails_length',
                                db.Field('opt_pr_pd_hands_nails_length', 'integer',
                                requires = IS_IN_SET(pr_pd_length_opts),
                                default = 99,
                                label = T('Hands, Nail length'),
                                represent = lambda opt: opt and pr_pd_length_opts[opt]))

opt_pr_pd_hands_nails_peculiarities = SQLTable(None, 'opt_pr_pd_hands_nails_peculiarities',
                                db.Field('opt_pr_pd_hands_nails_peculiarities', 'integer',
                                requires = IS_IN_SET(pr_pd_hands_nails_peculiarities_opts),
                                default = 99,
                                label = T('Hands, Nail peculiarities'),
                                represent = lambda opt: opt and pr_pd_hands_nails_peculiarities_opts[opt]))

opt_pr_pd_hands_nicotine = SQLTable(None, 'opt_pr_pd_hands_nicotine',
                                db.Field('opt_pr_pd_hands_nicotine', 'integer',
                                requires = IS_IN_SET(pr_pd_hands_nicotine_opts),
                                default = 99,
                                label = T('Hands, Nicotine'),
                                represent = lambda opt: opt and pr_pd_hands_nicotine_opts[opt]))

opt_pr_pd_feet_shape = SQLTable(None, 'opt_pr_pd_feet_shape',
                                db.Field('opt_pr_pd_feet_shape', 'integer',
                                requires = IS_IN_SET(pr_pd_feet_shape_opts),
                                default = 99,
                                label = T('Feet, Shape'),
                                represent = lambda opt: opt and pr_pd_feet_shape_opts[opt]))

opt_pr_pd_feet_condition = SQLTable(None, 'opt_pr_pd_feet_condition',
                                db.Field('opt_pr_pd_feet_condition', 'integer',
                                requires = IS_IN_SET(pr_pd_feet_condition_opts),
                                default = 99,
                                label = T('Feet, Condition'),
                                represent = lambda opt: opt and pr_pd_feet_condition_opts[opt]))

opt_pr_pd_feet_nails = SQLTable(None, 'opt_pr_pd_feet_nails',
                                db.Field('opt_pr_pd_feet_nails', 'integer',
                                requires = IS_IN_SET(pr_pd_feet_nails_opts),
                                default = 99,
                                label = T('Feet, Nails'),
                                represent = lambda opt: opt and pr_pd_feet_nails_opts[opt]))

opt_pr_pd_hair_body_extent = SQLTable(None, 'opt_pr_pd_hair_body_extent',
                                db.Field('opt_pr_pd_hair_body_extent', 'integer',
                                requires = IS_IN_SET(pr_pd_hair_body_extent_opts),
                                default = 99,
                                label = T('Body hair, Extent'),
                                represent = lambda opt: opt and pr_pd_hair_body_extent_opts[opt]))

opt_pr_pd_hair_body_colour = SQLTable(None, 'opt_pr_pd_hair_body_colour',
                                db.Field('opt_pr_pd_hair_body_colour', 'integer',
                                requires = IS_IN_SET(pr_pd_hair_colour_opts),
                                default = 99,
                                label = T('Body hair, Colour'),
                                represent = lambda opt: opt and pr_pd_hair_colour_opts[opt]))

opt_pr_pd_hair_pubic_extent = SQLTable(None, 'opt_pr_pd_hair_pubic_extent',
                                db.Field('opt_pr_pd_hair_pubic_extent', 'integer',
                                requires = IS_IN_SET(pr_pd_hair_pubic_extent_opts),
                                default = 99,
                                label = T('Pubic hair, Extent'),
                                represent = lambda opt: opt and pr_pd_hair_pubic_extent_opts[opt]))

opt_pr_pd_hair_pubic_colour = SQLTable(None, 'opt_pr_pd_hair_pubic_colour',
                                db.Field('opt_pr_pd_hair_pubic_colour', 'integer',
                                requires = IS_IN_SET(pr_pd_hair_colour_opts),
                                default = 99,
                                label = T('Pubic hair, Colour'),
                                represent = lambda opt: opt and pr_pd_hair_colour_opts[opt]))

opt_pr_pd_smoking_habits = SQLTable(None, 'opt_pr_pd_smoking_habits',
                                db.Field('opt_pr_pd_smoking_habits', 'integer',
                                requires = IS_IN_SET(pr_pd_smoking_habits_opts),
                                default = 99,
                                label = T('Smoking habits'),
                                represent = lambda opt: opt and pr_pd_smoking_habits_opts[opt]))

#
# Physical Description Tables -------------------------------------------------
#

#
# pd_general table ------------------------------------------------------------
#
resource = 'pd_general'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_id2,
                Field('est_age'),                       # D1-31A   Estimated Age
                Field('height'),                        # D1-32    Height
                Field('weight'),                        # D1-33    Weight
                opt_pr_pd_bodily_constitution,          # D1-34/01 Bodily Constitution
                opt_pr_pd_race_group,                   # D1-35/01 Race, group
                Field('race_type'),                     # D1-35/01 Race, type
                opt_pr_pd_race_complexion,              # D1-35/01 Race, complexion
                Field('other_peculiarities', 'text'),   # D3-55    Other Peculiarities
                #Field('body_sketch'),                   # D4       Body Sketch
                migrate=migrate)

# Joined Resource
s3xrc.model.add_component(module, resource, multiple=False, joinby='pr_pe_id', deletable=False, editable=True)

# Field validation

# Field representation

# Field labels

# CRUD Strings

#
# pd_head table ---------------------------------------------------------------
#
resource = 'pd_head'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_id2,
                opt_pr_pd_head_form_front,               # D1-34/02 Head form, front
                opt_pr_pd_head_form_profile,             # D1-34/03 Head form, profile
                opt_pr_pd_hair_head_type,                # D1-36/01 Hair of the head, Type
                opt_pr_pd_hair_head_length,              # D1-36/02 Hair of the head, Length
                opt_pr_pd_hair_head_colour,              # D1-36/03 Hair of the head, Colour
                opt_pr_pd_hair_head_shade,               # D1-36/04 Hair of the head, Shade of colour
                opt_pr_pd_hair_head_thickness,           # D1-36/05 Hair of the head, Thickness
                opt_pr_pd_hair_head_style,               # D1-36/06 Hair of the head, Style
                opt_pr_pd_hair_head_parting,             # D1-36/06 Hair of the head, Parting
                opt_pr_pd_hair_head_baldness_ext,        # D1-36/07 Hair of the head, Baldness (extent)
                opt_pr_pd_hair_head_baldness_loc,        # D1-36/07 Hair of the head, Baldness (location)
                Field('hair_head_other'),               # D1-36/08 Hair of the head, Other information
                migrate=migrate)

# Joined Resource
s3xrc.model.add_component(module, resource, multiple=False, joinby='pr_pe_id', deletable=False, editable=True)

# Field validation

# Field representation
db[table].opt_pr_pd_head_form_front.comment = A(SPAN("[Help]"), _class="ajaxtip", _rel="/%s/pr/tooltip?formfield=head_form_front" % request.application )
# Field labels

# CRUD Strings

#
# pd_face table ---------------------------------------------------------------
#
resource = 'pd_face'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_id2,
                opt_pr_pd_forehead_height,               # D2-37/01 Forehead, Height
                opt_pr_pd_forehead_width,                # D2-37/01 Forehead, Width
                opt_pr_pd_forehead_inclination,          # D2-37/02 Forehead, Inclination
                opt_pr_pd_eyebrows_shape,                # D2-38/01 Eyebrows, Shape
                opt_pr_pd_eyebrows_thickness,            # D2-38/01 Eyebrows, Thickness
                opt_pr_pd_eyebrows_peculiarities,        # D2-38/02 Eyebrows, Peculiarities
                opt_pr_pd_eyes_colour,                   # D2-39/01 Eyes, Colour
                opt_pr_pd_eyes_shade,                    # D2-39/02 Eyes, Shade
                opt_pr_pd_eyes_distance,                 # D2-39/03 Eyes, Distance between Eyes
                opt_pr_pd_eyes_peculiarities,            # D2-39/04 Eyes, Peculiarities
                opt_pr_pd_nose_size,                     # D2-40/01 Nose, size
                opt_pr_pd_nose_shape,                    # D2-40/01 Nose, shape
                Field('nose_spectacle_marks', 'boolean', default=False),          # D2-40/02 Nose, Peculiarities - Marks of spectacles
                #Field('nose_misshapen'),                # D2-40/02 Nose, Peculiarities - Misshapen
                Field('nose_peculiarities'),            # D2-40/02 Nose, Peculiarities
                opt_pr_pd_nose_curve,                    # D2-40/03 Nose, Curve
                opt_pr_pd_nose_angle,                    # D2-40/03 Nose, Angle
                opt_pr_pd_hair_facial_type,              # D2-41/01 Facial hair, Type
                opt_pr_pd_hair_facial_colour,            # D2-41/02 Facial hair, Colour
                opt_pr_pd_ears_size,                     # D2-42/01 Ears, size
                opt_pr_pd_ears_angle,                    # D2-42/01 Ears, angle
                Field('ears_lobes_attached', 'boolean', default=False),           # D2-42/02 Ears, Ear Lobes
                Field('ears_piercings_left', 'integer', default=0),           # D2-42/02 Ears, Number of Piercings, left
                Field('ears_piercings_right', 'integer', default=0),          # D2-42/02 Ears, Number of Piercings, right
                opt_pr_pd_mouth_size,                    # D2-43/01 Mouth, Size
                Field('mouth_other'),                   # D2-43/01 Mouth, Other
                opt_pr_pd_lips_shape,                    # D2-44/01 Lips, Shape
                Field('lips_madeup', 'boolean', default=False), # D2.44/01 Lips, made-up
                Field('lips_other'),                    # D2-44/01 Lips, Other
                opt_pr_pd_chin_size,                     # D3-47/01 Chin, Size
                opt_pr_pd_chin_inclination,              # D3-47/01 Chin, Inclination
                opt_pr_pd_chin_shape,                    # D3-47/02 Chin, Shape
                migrate=migrate)

# Joined Resource
s3xrc.model.add_component(module, resource, multiple=False, joinby='pr_pe_id', deletable=False, editable=True)

# Field validation

# Field representation

# Field labels

# CRUD Strings

#
# pd_teeth table --------------------------------------------------------------
#
resource = 'pd_teeth'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_id2,
                Field('teeth_natural', 'boolean', default=True),        # D2-45/01 Teeth, Conditions
                Field('teeth_treated', 'boolean', default=False),       # D2-45/01 Teeth, Conditions
                Field('teeth_crowns', 'boolean', default=False),        # D2-45/01 Teeth, Conditions
                Field('teeth_bridges', 'boolean', default=False),       # D2-45/01 Teeth, Conditions
                Field('teeth_implants', 'boolean', default=False),      # D2-45/01 Teeth, Conditions
                opt_pr_pd_teeth_gaps,                    # D2-45/02 Teeth, Gaps between front teeth
                opt_pr_pd_teeth_missing,                 # D2-45/02 Teeth, Missing teeth
                opt_pr_pd_teeth_toothless,               # D2-45/02 Teeth, Toothless
                opt_pr_pd_teeth_dentures_lower,          # D2-45/03 Teeth, Dentures
                opt_pr_pd_teeth_dentures_upper,          # D2-45/03 Teeth, Dentures
                Field('teeth_dentures_id'),             # D2-45/03 Teeth, Dentures, ID-number
                migrate=migrate)

# Joined Resource
s3xrc.model.add_component(module, resource, multiple=False, joinby='pr_pe_id', deletable=False, editable=True)

# Field validation

# Field representation

# Field labels

# CRUD Strings

#
# pd_body table ---------------------------------------------------------------
#
resource = 'pd_body'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_id2,
                opt_pr_pd_neck_length,                   # D3-48/01 Neck, Length
                opt_pr_pd_neck_shape,                    # D3-48/01 Neck, Shape
                opt_pr_pd_neck_peculiarities,            # D3-48/02 Neck, Peculiarities
                Field('neck_collar_size', length=10),              # D3-48/02 Neck, Collar Size
                Field('neck_circumference', length=10),            # D3-48/02 Neck, Circumference
                opt_pr_pd_hands_shape,                   # D3-49/01 Hands, Shape
                opt_pr_pd_hands_size,                    # D3-49/01 Hands, Size
                opt_pr_pd_hands_nails_length,            # D3-49/02 Hands, Nail length
                opt_pr_pd_hands_nails_peculiarities,     # D3-49/03 Hands, Nail peculiarities
                opt_pr_pd_hands_nicotine,                # D3-49/03 Hands, Nicotine
                opt_pr_pd_feet_shape,                    # D3-50/01 Feet, Shape
                Field('pd_feet_size'),                     # D3-50/01 Feet, Size
                opt_pr_pd_feet_condition,                # D3-50/02 Feet, Condition
                opt_pr_pd_feet_nails,                    # D3-50/02 Feet, Nails
                Field('feet_peculiarities'),            # D3-50/03 Feet, Peculiarities
                opt_pr_pd_hair_body_extent,              # D3-51/01 Body hair, Extent
                opt_pr_pd_hair_body_colour,              # D3-51/02 Body hair, Colour
                opt_pr_pd_hair_pubic_extent,             # D3-52/01 Pubic hair, Extent
                opt_pr_pd_hair_pubic_colour,             # D3-52/02 Pubic hair, Colour
                Field('circumcision', 'boolean', default=False),                  # D3-54    Circumcision
                opt_pr_pd_smoking_habits,                # D2-46/01 Smoking Habits, Type
                Field('smoking_stains_teeth', 'boolean', default=False),                # D2-46/01 Smoking Habits, Stains Found
                Field('smoking_stains_lips', 'boolean', default=False),                # D2-46/01 Smoking Habits, Stains Found
                Field('smoking_stains_moustache', 'boolean', default=False),                # D2-46/01 Smoking Habits, Stains Found
                Field('smoking_stains_hand_left', 'boolean', default=False),                # D2-46/01 Smoking Habits, Stains Found
                Field('smoking_stains_hand_right', 'boolean', default=False),                # D2-46/01 Smoking Habits, Stains Found
                Field('specific_details_head'),         # D3-53    Specific Details
                Field('specific_details_throat'),       # D3-53    Specific Details
                Field('specific_details_arm_left'),     # D3-53    Specific Details
                Field('specific_details_arm_right'),    # D3-53    Specific Details
                Field('specific_details_hand_left'),    # D3-53    Specific Details
                Field('specific_details_hand_right'),   # D3-53    Specific Details
                Field('specific_details_body_front'),   # D3-53    Specific Details
                Field('specific_details_body_back'),    # D3-53    Specific Details
                Field('specific_details_leg_left'),     # D3-53    Specific Details
                Field('specific_details_leg_right'),    # D3-53    Specific Details
                Field('specific_details_foot_left'),    # D3-53    Specific Details
                Field('specific_details_foot_right'),   # D3-53    Specific Details
                migrate=migrate)

# Joined Resource
s3xrc.model.add_component(module, resource, multiple=False, joinby='pr_pe_id', deletable=False, editable=True)

# Field validation

# Field representation

# Field labels

# CRUD Strings

# *****************************************************************************
# Identity (identity)
#

#
# ID Types --------------------------------------------------------------------
#
pr_id_type_opts = {
    1:T('Passport'),
    2:T('National ID Card'),
    3:T('Driving License'),
    99:T('other')
    }

opt_pr_id_type = SQLTable(None, 'opt_pr_id_type',
                    Field('opt_pr_id_type', 'integer',
                        requires = IS_IN_SET(pr_id_type_opts),
                        default = 1,
                        label = T('ID type'),
                        represent = lambda opt: opt and pr_id_type_opts[opt]))

#
# identitiy table -------------------------------------------------------------
#
resource = 'identity'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                person_id,                          # Reference to person
                opt_pr_id_type,                     # ID type
                Field('type'),                      # Description for type 'Other'
                Field('value'),                     # ID value
                Field('country_code', length=4),    # Country Code (for National ID Cards)
                Field('ia_name'),                   # Name of issuing authority
#                Field('ia_subdivision'),            # Name of issuing authority subdivision
#                Field('ia_code'),                   # Code of issuing authority (if any)
                Field('comment'),                   # a comment (optional)
                migrate=migrate)

# Joined Resource
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(pr_person='person_id'),
    deletable=True,
    editable=True,
    list_fields = ['id', 'opt_pr_id_type', 'type', 'value', 'country_code', 'ia_name'])

# Field validation
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

# Field representation

# Field labels
db[table].ia_name.label = T("Issuing Authority")

# CRUD Strings
title_create = T('Add Identity')
title_display = T('Identity Details')
title_list = T('Known Identities')
title_update = T('Edit Identity')
title_search = T('Search Identity')
subtitle_create = T('Add New Identity')
subtitle_list = T('Current Identities')
label_list_button = T('List Identities')
label_create_button = T('Add Identity')
msg_record_created = T('Identity added')
msg_record_modified = T('Identity updated')
msg_record_deleted = T('Identity deleted')
msg_list_empty = T('No Identities currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# *****************************************************************************
# Role (role)
#

#
# role table ------------------------------------------------------------------
#
resource = 'role'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                person_id,
                Field('description'),
                migrate=migrate)

# *****************************************************************************
# Group membership (group_membership)
#

#
# group_membership table ------------------------------------------------------
#
resource = 'group_membership'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                group_id,
                person_id,
                Field('group_head', 'boolean', default=False),
                Field('description'),
                Field('comment'),
                migrate=migrate)

# Joined Resource
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(pr_group='group_id', pr_person='person_id'),
    deletable=True,
    editable=True,
    list_fields = ['id', 'group_id', 'person_id', 'group_head', 'description'])

# Field validation

# Field representation
db[table].group_head.represent = lambda group_head: (group_head and [T('yes')] or [''])[0]

# Field labels

# CRUD Strings
title_create = T('Add Group Membership')
title_display = T('Group Membership Details')
title_list = T('Group Memberships')
title_update = T('Edit Membership')
title_search = T('Search Membership')
subtitle_create = T('Add New Group Membership')
subtitle_list = T('Current Group Memberships')
label_list_button = T('List All Group Memberships')
label_create_button = T('Add Group Membership')
msg_record_created = T('Group Membership added')
msg_record_modified = T('Group Membership updated')
msg_record_deleted = T('Group Membership deleted')
msg_list_empty = T('No Group Memberships currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# *****************************************************************************
# Network (network)
#
pr_network_type_opts = {
    1:T('Family'),
    2:T('Friends'),
    3:T('Colleagues'),
    99:T('other')
    }

opt_pr_network_type = SQLTable(None, 'opt_pr_network_type',
                    Field('opt_pr_network_type','integer',
                        requires = IS_IN_SET(pr_network_type_opts),
                        default = 99,
                        label = T('Network Type'),
                        represent = lambda opt: opt and pr_network_type_opts[opt]))

#
# network table ---------------------------------------------------------------
#
resource = 'network'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                person_id,                          # Reference to person (owner)
                opt_pr_network_type,                # Network type
                Field('comment'),                   # a comment (optional)
                migrate=migrate)

# Joined Resource
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(pr_person='person_id'),
    deletable=True,
    editable=True,
    list_fields = ['id', 'opt_pr_network_type', 'comment'])

# Field validation
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

# Field representation

# Field labels

# CRUD Strings

#
# network_id: reusable field for other tables to reference ----------------------
#
network_id = SQLTable(None, 'network_id',
                Field('network_id', db.pr_network,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_network.id', '%(id)s')),
                represent = lambda id: (id and [db(db.pr_network.id==id).select()[0].id] or ["None"])[0],
                comment = DIV(A(T('Add Network'), _class='thickbox', _href=URL(r=request, c='pr', f='network', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=T('Add Network')), A(SPAN("[Help]"), _class="tooltip", _title=T("Create Network|Create a social network layer for a person."))),
                ondelete = 'RESTRICT'
                ))

# *****************************************************************************
# Network membership (network_membership)
#

#
# network_membership table ----------------------------------------------------
#
resource = 'network_membership'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                network_id,
                person_id,
                Field('description'),
                Field('comment'),
                migrate=migrate)

# Joined Resource
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(pr_person='person_id'),
    deletable=True,
    editable=True,
    list_fields = ['id','network_id','person_id','description','comment'])

# Field validation

# Field representation

# Field labels

# CRUD Strings

# *****************************************************************************
# Case (case)
#

#
# case table ------------------------------------------------------------------
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
                requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_case.id', '%(description)s')),
                represent = lambda id: (id and [db(db.pr_case.id==id).select()[0].description] or ["None"])[0],
                comment = DIV(A(T('Add Case'), _class='thickbox', _href=URL(r=request, c='pr', f='case', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=T('Add Case')), A(SPAN("[Help]"), _class="tooltip", _title=T("Case|Add new case."))),
                ondelete = 'RESTRICT'
                ))

# *****************************************************************************
# Finding (finding)
#

#
# finding table ---------------------------------------------------------------
#
resource = 'finding'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                pr_pe_id,                      # about which entity?
#                opt_pr_findings_type,           # Finding type
                Field('description'),           # Descriptive title
                Field('module', db.s3_module),  # Access module
                Field('resource'),              # Access resource
                Field('resource_id'),           # Access ID
                migrate=migrate)

db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].module.requires = IS_NULL_OR(IS_ONE_OF(db, 's3_module.name', '%(name_nice)s'))
db[table].module.represent = lambda name: (name and [db(db.s3_module.name==name).select()[0].name_nice] or ["None"])[0]

# *****************************************************************************
# Functions:
#

#
# shn_pr_person_pfif ----------------------------------------------------------
#
def shn_pr_person_pfif(person, domain):

    domain = request.env.server_name

    if person:
        pe = vita.pentity(person)

        person_record_id = "%s/%s" % (domain, pe.uuid)
        pfif = dict(person_record_id=person_record_id)

        entry_date = str(person.modified_on)
        source_date = str(person.created_on)
        pfif.update(entry_date=entry_date, source_date=source_date)

        first_name = person.first_name.upper()
        last_name = person.last_name.upper()
        pfif.update(first_name=first_name, last_name=last_name)

        # Get home address of that person
        query = (db.pr_address.deleted==False)
        query = (db.pr_address.pr_pe_id==pe.id) & query
        query = (db.pr_address.opt_pr_address_type==1) & query

        rows = db(query).select(db.pr_address.ALL)
        if rows:
            home_address = rows[0]
            home_city = home_address.city
            if home_address.opt_pr_country == 184: # United States?
                home_state = home_address.state
            else:
                home_state = shn_list_of_nations[home_address.opt_pr_country]

            home_neighborhood = '' # not available
            home_street = home_address.street1
            home_zip = home_address.postcode
        else:
            home_city = ''
            home_state = ''
            home_neighborhood = ''
            home_street = ''
            home_zip = ''

        pfif.update(
            home_city = home_city,
            home_state = home_state,
            home_neighborhood = home_neighborhood,
            home_street = home_street,
            home_zip = home_zip
            )

        # Get photograph of that person
        query = (db.pr_image.deleted==False)
        query = (db.pr_image.pr_pe_id==pe.id) & query
        query = (db.pr_image.opt_pr_image_type==1) & query

        rows = db(query).select(db.pr_image.ALL)
        if rows:
            photo = rows[0]
            photo_url = "%s/%s/pr/download/%s" % (S3_PUBLIC_URL, request.application, photo.image)
        else:
            photo_url = ''

        pfif.update(photo_url=photo_url)

        # Get admin data
        try:
            admin_data = db(db.s3_setting.id==1).select(
                                    db.s3_setting.admin_name,
                                    db.s3_setting.admin_email,
                                    db.s3_setting.admin_tel)[0]

            author_name = admin_data.admin_name
            author_email = admin_data.admin_email
            author_phone = admin_data.admin_tel
        except:
            author_name = ''
            author_email = ''
            author_phone = ''

        pfif.update(author_name=author_name, author_email=author_email, author_phone=author_phone)

        # Add source data
        source_name = domain
        source_url = "%s/%s/%s/person/%s.pfif" % (S3_PUBLIC_URL, request.application, module, person.id)
        pfif.update(source_name=source_name, source_url=source_url)

        return dict(person=pfif)

    else:
        return None

#
# shn_pr_presence_pfif --------------------------------------------------------
#
def shn_pr_presence_pfif(record, domain):

    if record:
        note_record_id = "%s/%s" % (domain, record.uuid)
        pfif = dict(note_record_id=note_record_id)

        return dict(note=pfif)
    else:
        return None

#
# End
# *****************************************************************************
