# -*- coding: utf-8 -*-

module = 'gis'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read = False,
        audit_write = False
    )

# GIS Markers (Icons)
resource = 'marker'
table = module + '_' + resource
db.define_table(table, timestamp,
                #uuidstamp, # Markers don't sync
                Field('name', notnull=True, unique=True),
                #Field('height', 'integer'), # In Pixels, for display purposes
                #Field('width', 'integer'),  # Not needed since we get size client-side using Javascript's Image() class
                Field('image', 'upload', autodelete = True),
                migrate=migrate)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].image.label = T('Image')
db[table].image.uploadfolder = os.path.join(request.folder, "static/img/markers")
# Populate table with Default options
# Can't do sub-folders :/
# need a script to read in the list of default markers from the filesystem, copy/rename & populate the DB 1 by 1
if not len(db().select(db[table].ALL)):
    # We want to start at ID 1
    db[table].truncate() 
    db[table].insert(
        name = "marker",
        image = "gis_marker.image.marker.png"
    )
    #db[table].insert(
    #    name = "marker_r1",
    #    image = "marker_r1.png"
    #)
    db[table].insert(
        name = "shelter",
        image = "gis_marker.image.Emergency_Shelters_S1.png"
    )
title_create = T('Add Marker')
title_display = T('Marker Details')
title_list = T('List Markers')
title_update = T('Edit Marker')
title_search = T('Search Markers')
subtitle_create = T('Add New Marker')
subtitle_list = T('Markers')
label_list_button = T('List Markers')
label_create_button = T('Add Marker')
msg_record_created = T('Marker added')
msg_record_modified = T('Marker updated')
msg_record_deleted = T('Marker deleted')
msg_list_empty = T('No Markers currently available')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
# Reusable field for other tables to reference
marker_id = SQLTable(None, 'marker_id',
            Field('marker', db.gis_marker,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'gis_marker.id', '%(name)s')),
                represent = lambda id: DIV(A(IMG(_src=URL(r=request, c='default', f='download', args=(id and [db(db.gis_marker.id==id).select()[0].image] or ["None"])[0]), _height=40), _class='zoom', _href='#zoom-gis_config-marker-%s' % id), DIV(IMG(_src=URL(r=request, c='default', f='download', args=(id and [db(db.gis_marker.id==id).select()[0].image] or ["None"])[0]),_width=600), _id='zoom-gis_config-marker-%s' % id, _class='hidden')),
                label = T('Marker'),
                comment = DIV(A(T('Add Marker'), _class='popup', _href=URL(r=request, c='gis', f='marker', args='create', vars=dict(format='plain')), _target='top', _title=T('Add Marker')), A(SPAN("[Help]"), _class="tooltip", _title=T("Marker|Defines the icon used for display of features."))),
                ondelete = 'RESTRICT'
                ))

# GIS Projections
resource = 'projection'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('name', notnull=True, unique=True),
                Field('epsg', 'integer', notnull=True),
                Field('maxExtent', length=64, notnull=True),
                Field('maxResolution', 'double', notnull=True),
                Field('units', notnull=True),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].epsg.requires = IS_NOT_EMPTY()
db[table].epsg.label = "EPSG"
db[table].epsg.comment = SPAN("*", _class="req")
db[table].maxExtent.requires = IS_NOT_EMPTY()
db[table].maxExtent.label = T('maxExtent')
db[table].maxExtent.comment = SPAN("*", _class="req")
db[table].maxResolution.requires = IS_NOT_EMPTY()
db[table].maxResolution.label = T('maxResolution')
db[table].maxResolution.comment = SPAN("*", _class="req")
db[table].units.requires = IS_IN_SET(['m', 'degrees'])
db[table].units.label = T('Units')
# Populate table with Default options
if not len(db().select(db[table].ALL)): 
   # We want to start at ID 1
   db[table].truncate() 
   db[table].insert(
        uuid = uuid.uuid4(),
        name = "Spherical Mercator",
        epsg = 900913,
        maxExtent = "-20037508, -20037508, 20037508, 20037508.34",
        maxResolution = 156543.0339,
        units = "m"
    )
   db[table].insert(
        uuid = uuid.uuid4(),
        name = "WGS84",
        epsg = 4326,
        maxExtent = "-180,-90,180,90",
        maxResolution = 1.40625,
        units = "degrees"
    )
title_create = T('Add Projection')
title_display = T('Projection Details')
title_list = T('List Projections')
title_update = T('Edit Projection')
title_search = T('Search Projections')
subtitle_create = T('Add New Projection')
subtitle_list = T('Projections')
label_list_button = T('List Projections')
label_create_button = T('Add Projection')
msg_record_created = T('Projection added')
msg_record_modified = T('Projection updated')
msg_record_deleted = T('Projection deleted')
msg_list_empty = T('No Projections currently defined')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
# Reusable field for other tables to reference
projection_id = SQLTable(None, 'projection_id',
            Field('projection', db.gis_projection,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'gis_projection.id', '%(name)s')),
                represent = lambda id: db(db.gis_projection.id==id).select()[0].name,
                label = T('Projection'),
                comment = '',
                ondelete = 'RESTRICT'    
                ))

# GIS Config
# id=1 = Default settings
# separated from Framework settings above
# ToDo Extend for per-user Profiles - this is the WMC
resource = 'config'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
				Field('lat', 'double'),
				Field('lon', 'double'),
				Field('zoom', 'integer'),
				projection_id,
				marker_id,
				Field('map_height', 'integer', notnull=True),
				Field('map_width', 'integer', notnull=True),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].lat.requires = IS_LAT()
db[table].lat.label = T('Latitude')
db[table].lat.comment = DIV(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Latitude|Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere.")))
db[table].lon.requires = IS_LON()
db[table].lon.label = T('Longitude')
db[table].lon.comment = DIV(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Longitude|Longitude is West - East (sideways). Longitude is zero on the prime meridian (Greenwich Mean Time) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas.")))
db[table].zoom.requires = IS_INT_IN_RANGE(0,19)
db[table].zoom.label = T('Zoom')
db[table].zoom.comment = DIV(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Zoom|How much detail is seen. A high Zoom level means lot of detail, but not a wide area. A low Zoom level means seeing a wide area, but not a high level of detail.")))
db[table].marker.label = T('Default Marker')
db[table].map_height.requires = [IS_NOT_EMPTY(), IS_ALPHANUMERIC()]
db[table].map_height.label = T('Map Height')
db[table].map_height.comment = SPAN("*", _class="req")
db[table].map_width.requires = [IS_NOT_EMPTY(), IS_ALPHANUMERIC()]
db[table].map_width.label = T('Map Width')
db[table].map_width.comment = SPAN("*", _class="req")
# Populate table with Default options
if not len(db().select(db[table].ALL)): 
   # We want to start at ID 1
   db[table].truncate() 
   db[table].insert(
        lat = "6",
        lon = "79.4",
        zoom = 7,
        # Doesn't work on Postgres!
        projection = 1,
        marker = 1,
        map_height = 600,
        map_width = 800
    )
title_create = T('Add Config')
title_display = T('Config Details')
title_list = T('List Configs')
title_update = T('Edit Config')
title_search = T('Search Configs')
subtitle_create = T('Add New Config')
subtitle_list = T('Configs')
label_list_button = T('List Configs')
label_create_button = T('Add Config')
msg_record_created = T('Config added')
msg_record_modified = T('Config updated')
msg_record_deleted = T('Config deleted')
msg_list_empty = T('No Configs currently defined')
s3.crud_strings[table] = Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, title_search=title_search, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)
            
# GIS Features
resource = 'feature_class'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', notnull=True, unique=True),
                Field('description'),
                marker_id,
                Field('module'),    # Used to build Edit URL
                Field('resource'),   # Used to build Edit URL & to provide Attributes to Display
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].description.label = T('Description')
db[table].module.requires = IS_ONE_OF(db((db.s3_module.enabled=='True') & (~db.s3_module.name.like('default'))),'s3_module.name','%(name_nice)s')
db[table].module.label = T('Module')
# FIXME!
db[table].resource.requires = IS_NULL_OR(IS_IN_SET(['resource']))
db[table].resource.label = T('Resource')
title_create = T('Add Feature Class')
title_display = T('Feature Class Details')
title_list = T('List Feature Classes')
title_update = T('Edit Feature Class')
title_search = T('Search Feature Class')
subtitle_create = T('Add New Feature Class')
subtitle_list = T('Feature Classes')
label_list_button = T('List Feature Classes')
label_create_button = T('Add Feature Class')
msg_record_created = T('Feature Class added')
msg_record_modified = T('Feature Class updated')
msg_record_deleted = T('Feature Class deleted')
msg_list_empty = T('No Feature Classes currently defined')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
# Reusable field for other tables to reference
feature_class_id = SQLTable(None, 'feature_class_id',
            Field('feature_class_id', db.gis_feature_class,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'gis_feature_class.id', '%(name)s')),
                represent = lambda id: (id and [db(db.gis_feature_class.id==id).select()[0].name] or ["None"])[0],
                label = T('Feature Class'),
                comment = DIV(A(T('Add Feature Class'), _class='popup', _href=URL(r=request, c='gis', f='feature_class', args='create', vars=dict(format='plain')), _target='top', _title=T('Add Feature Class')), A(SPAN("[Help]"), _class="tooltip", _title=T("Feature Class|Defines the marker used for display & the attributes visible in the popup."))),
                ondelete = 'RESTRICT'
                ))
# Populate table with Default options
if not len(db().select(db[table].ALL)):
	db[table].insert(
        name = 'Shelter',
        marker = db(db.gis_marker.name=='shelter').select()[0].id,
        module = 'cr',
        resource = 'shelter'
	)

resource = 'feature_metadata'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, authorstamp, deletion_status,
                Field('description'),
                person_id,
                Field('source'),
                Field('accuracy'),       # Drop-down on a IS_IN_SET[]?
                Field('sensitivity'),    # Should be turned into a drop-down by referring to AAA's sensitivity table
                Field('event_time', 'datetime'),
                Field('expiry_time', 'datetime'),
                Field('url'),
                Field('image', 'upload'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].description.label = T('Description')
db[table].person_id.label = T("Contact")
db[table].source.label = T('Source')
db[table].accuracy.label = T('Accuracy')
db[table].sensitivity.label = T('Sensitivity')
db[table].event_time.requires = IS_NULL_OR(IS_DATETIME())
db[table].event_time.label = T('Event Time')
db[table].expiry_time.requires = IS_NULL_OR(IS_DATETIME())
db[table].expiry_time.label = T('Expiry Time')
db[table].url.requires = IS_NULL_OR(IS_URL())
db[table].url.label = 'URL'
db[table].image.label = T('Image')
title_create = T('Add Feature Metadata')
title_display = T('Feature Metadata Details')
title_list = T('List Feature Metadata')
title_update = T('Edit Feature Metadata')
title_search = T('Search Feature Metadata')
subtitle_create = T('Add New Feature Metadata')
subtitle_list = T('Feature Metadata')
label_list_button = T('List Feature Metadata')
label_create_button = T('Add Feature Metadata')
msg_record_created = T('Feature Metadata added')
msg_record_modified = T('Feature Metadata updated')
msg_record_deleted = T('Feature Metadata deleted')
msg_list_empty = T('No Feature Metadata currently defined')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

gis_feature_type_opts = {
    1:T('Point'),
    2:T('Line'),
    3:T('Polygon')
    }
resource = 'feature'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', notnull=True),
                feature_class_id,
                marker_id,
                Field('metadata', db.gis_feature_metadata),      # NB This can have issues with sync unless going via CSV
                Field('feature_type', 'integer', default=1, notnull=True),
                Field('lat', 'double'),    # Only needed for Points
                Field('lon', 'double'),    # Only needed for Points
                Field('wkt'),  # WKT is auto-calculated from lat/lon for Points
                #Field('resource_id', 'integer', ondelete = 'RESTRICT'), # Used to build Edit URL for Feature Class.
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].metadata.requires = IS_NULL_OR(IS_ONE_OF(db, 'gis_feature_metadata.id', '%(id)s'))
db[table].metadata.represent = lambda id: (id and [db(db.gis_feature_metadata.id==id).select()[0].description] or ["None"])[0]
db[table].metadata.label = T('Metadata')
db[table].metadata.comment = DIV(A(T('Add Metadata'), _class='popup', _href=URL(r=request, c='gis', f='feature_metadata', args='create', vars=dict(format='plain')), _target='top', _title=T('Add Metadata')), A(SPAN("[Help]"), _class="tooltip", _title=T("Metadata|Additional attributes associated with this Feature.")))
db[table].feature_type.requires = IS_IN_SET(gis_feature_type_opts)
db[table].feature_type.represent = lambda opt: opt and gis_feature_type_opts[opt]
db[table].feature_type.label = T('Type')
db[table].lat.requires = IS_NULL_OR(IS_LAT())
db[table].lat.label = T('Latitude')
db[table].lat.comment = DIV(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Latitude|Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere.")))
db[table].lon.requires = IS_NULL_OR(IS_LON())
db[table].lon.label = T('Longitude')
db[table].lon.comment = DIV(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Longitude|Longitude is West - East (sideways). Longitude is zero on the prime meridian (Greenwich Mean Time) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas.")))
# WKT validation is done in the onvalidation callback
#db[table].wkt.requires=IS_NULL_OR(IS_WKT())
db[table].wkt.label = T('Well-Known Text')
db[table].wkt.comment = DIV(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("WKT|The <a href='http://en.wikipedia.org/wiki/Well-known_text' target=_blank>Well-Known Text</a> representation of the Polygon/Line.")))
title_create = T('Add Feature')
title_display = T('Feature Details')
title_list = T('List Features')
title_update = T('Edit Feature')
title_search = T('Search Features')
subtitle_create = T('Add New Feature')
subtitle_list = T('Features')
label_list_button = T('List Features')
label_create_button = T('Add Feature')
msg_record_created = T('Feature added')
msg_record_modified = T('Feature updated')
msg_record_deleted = T('Feature deleted')
msg_list_empty = T('No Features currently defined')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
# Reusable field for other tables to reference
feature_id = SQLTable(None, 'feature_id',
            Field('feature', db.gis_feature,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'gis_feature.id', '%(name)s')),
                represent = lambda id: (id and [db(db.gis_feature.id==id).select()[0].name] or ["None"])[0],
                label = T('Feature'),
                comment = DIV(A(T('Add Feature'), _class='popup', _href=URL(r=request, c='gis', f='feature', args='create', vars=dict(format='plain')), _target='top', _title=T('Add Feature')), A(SPAN("[Help]"), _class="tooltip", _title=T("Feature|The centre Point or Polygon used to display this Location on a Map."))),
                ondelete = 'RESTRICT'
                ))
    
# Feature Groups
# Used to select a set of Features for either Display or Export
resource = 'feature_group'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, authorstamp, deletion_status,
                Field('name', notnull=True, unique=True),
                Field('description'),
                #Field('features', 'text'),        # List of features (to be replaced by many-to-many table)
                #Field('feature_classes', 'text'), # List of feature classes (to be replaced by many-to-many table)
                Field('display', 'boolean', default='True'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
#db[table].author.requires = IS_ONE_OF(db, 'auth_user.id','%(id)s: %(first_name)s %(last_name)s')
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].description.label = T('Description')
#db[table].features.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Multi-Select|Click Features to select, Click again to Remove. Dark Green is selected."))
#db[table].feature_classes.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Multi-Select|Click Features to select, Click again to Remove. Dark Green is selected."))
db[table].display.label = T('Display?')
title_create = T('Add Feature Group')
title_display = T('Feature Group Details')
title_list = T('List Feature Groups')
title_update = T('Edit Feature Group')
title_search = T('Search Feature Groups')
subtitle_create = T('Add New Feature Group')
subtitle_list = T('Feature Groups')
label_list_button = T('List Feature Groups')
label_create_button = T('Add Feature Group')
msg_record_created = T('Feature Group added')
msg_record_modified = T('Feature Group updated')
msg_record_deleted = T('Feature Group deleted')
msg_list_empty = T('No Feature Groups currently defined')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
# Reusable field for other tables to reference
feature_group_id = SQLTable(None, 'feature_group_id',
            Field('feature_group_id', db.gis_feature_group,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'gis_feature_group.id', '%(name)s')),
                represent = lambda id: (id and [db(db.gis_feature_group.id==id).select()[0].name] or ["None"])[0],
                label = T('Feature Group'),
                comment = '',
                ondelete = 'RESTRICT'
                ))

            
# Many-to-Many tables
resource = 'feature_to_feature_group'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                feature_group_id,
                feature_id,
                migrate=migrate)
                
resource = 'feature_class_to_feature_group'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                feature_group_id,
                feature_class_id,
                migrate=migrate)

gis_landmark_type_opts = {
    1:T('Church'),
    2:T('School'),
    3:T('Hospital')
    }
resource = 'landmark'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, authorstamp, deletion_status,
                Field('name', notnull=True),
                Field('landmark_type', 'integer'),
                Field('description'),
                Field('url'),
                Field('image', 'upload'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].landmark_type.requires = IS_NULL_OR(IS_IN_SET(gis_landmark_type_opts))
db[table].landmark_type.represent = lambda opt: opt and gis_landmark_type_opts[opt]
db[table].landmark_type.label = T('Type')
db[table].description.label = T('Description')
db[table].url.requires = IS_NULL_OR(IS_URL())
db[table].url.label = "URL"
db[table].image.label = T('Image')
title_create = T('Add Landmark')
title_display = T('Landmark Details')
title_list = T('List Landmarks')
title_update = T('Edit Landmark')
title_search = T('Search Landmarks')
subtitle_create = T('Add New Landmark')
subtitle_list = T('Landmarks')
label_list_button = T('List Landmarks')
label_create_button = T('Add Landmark')
msg_record_created = T('Landmark added')
msg_record_modified = T('Landmark updated')
msg_record_deleted = T('Landmark deleted')
msg_list_empty = T('No Landmarks currently defined')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# GIS Locations
gis_sector_opts = {
    1:T('Government'),
    2:T('Health')
    }
gis_level_opts = {
    1:T('Country'),
    2:T('Region'),
    3:T('District'),
    4:T('Town')
    }
resource = 'location'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', notnull=True),
                Field('level', 'integer'),
                feature_id,         # Either just a Point or a Polygon
                Field('parent', 'reference gis_location', ondelete = 'RESTRICT'),   # This form of hierarchy may not work on all Databases
                Field('sector', 'integer'),
                admin_id,
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()    # Placenames don't have to be unique
db[table].name.label = T('Name')
db[table].level.requires = IS_NULL_OR(IS_IN_SET(gis_level_opts))
db[table].level.represent = lambda opt: opt and gis_level_opts[opt]
db[table].level.label = T('Level')
db[table].feature.label = T('GIS Feature')
db[table].parent.requires = IS_NULL_OR(IS_ONE_OF(db, 'gis_location.id', '%(name)s'))
db[table].parent.represent = lambda id: (id and [db(db.gis_location.id==id).select()[0].name] or ["None"])[0]
db[table].parent.label = T('Parent')
db[table].sector.requires = IS_NULL_OR(IS_IN_SET(gis_sector_opts))
db[table].sector.represent = lambda opt: opt and gis_sector_opts[opt]
db[table].sector.label = T('Sector')
title_create = T('Add Location')
title_display = T('Location Details')
title_list = T('List Locations')
title_update = T('Edit Location')
title_search = T('Search Locations')
subtitle_create = T('Add New Location')
subtitle_list = T('Locations')
label_list_button = T('List Locations')
label_create_button = T('Add Location')
msg_record_created = T('Location added')
msg_record_modified = T('Location updated')
msg_record_deleted = T('Location deleted')
msg_list_empty = T('No Locations currently available')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
# Joined Resource
jrlayer.add_jresource(module, resource,
    multiple=True,
    joinby='feature_id',
    deletable=True,
    editable=True,
    list_fields = ['id', 'name', 'level'])
# Reusable field for other tables to reference
location_id = SQLTable(None, 'location_id',
            Field('location', db.gis_location,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'gis_location.id', '%(name)s')),
                represent = lambda id: (id and [db(db.gis_location.id==id).select()[0].name] or ["None"])[0],
                label = T('Location'),
                comment = DIV(A(s3.crud_strings.gis_location.label_create_button, _class='popup', _href=URL(r=request, c='gis', f='location', args='create', vars=dict(format='plain')), _target='top', _title=s3.crud_strings.gis_location.label_create_button), A(SPAN("[Help]"), _class="tooltip", _title=T("Location|The Location of this Site, which can be general (for Reporting) or precise (for displaying on a Map)."))),
                ondelete = 'RESTRICT'
                ))

# GIS Keys - needed for commercial mapping services
resource = 'apikey' # Can't use 'key' as this has other meanings for dicts!
table = module + '_' + resource
db.define_table(table, timestamp,
                Field('name', notnull=True),
                Field('apikey', length=128, notnull=True),
				Field('description'),
                migrate=migrate)
# FIXME
# We want a THIS_NOT_IN_DB here: http://groups.google.com/group/web2py/browse_thread/thread/27b14433976c0540/fc129fd476558944?lnk=gst&q=THIS_NOT_IN_DB#fc129fd476558944
db[table].name.requires = IS_IN_SET(['google', 'multimap', 'yahoo']) 
db[table].name.label = T("Service")
#db[table].apikey.requires = THIS_NOT_IN_DB(db(db[table].name==request.vars.name), 'gis_apikey.name', request.vars.name,'Service already in use')
db[table].apikey.requires = IS_NOT_EMPTY()
db[table].apikey.label = T("Key")
# Populate table with Default options
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        name = "google",
        apikey = "ABQIAAAAgB-1pyZu7pKAZrMGv3nksRRi_j0U6kJrkFvY4-OX2XYmEAa76BSH6SJQ1KrBv-RzS5vygeQosHsnNw",
        description = "localhost"
    )
   db[table].insert(
        name = "yahoo",
        apikey = "euzuro-openlayers",
        description = "trial - replace for Production use"
    )
   db[table].insert(
        name = "multimap",
        apikey = "metacarta_04",
        description = "trial - replace for Production use"
    )
title_create = T('Add Key')
title_display = T('Key Details')
title_list = T('List Keys')
title_update = T('Edit Key')
title_search = T('Search Keys')
subtitle_create = T('Add New Key')
subtitle_list = T('Keys')
label_list_button = T('List Keys')
label_create_button = T('Add Key')
msg_record_created = T('Key added')
msg_record_modified = T('Key updated')
msg_record_deleted = T('Key deleted')
msg_list_empty = T('No Keys currently defined')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# GIS Layers
#gis_layer_types = ['features', 'georss', 'kml', 'gpx', 'shapefile', 'scan', 'bing', 'google', 'openstreetmap', 'wms', 'yahoo']
gis_layer_types = ['openstreetmap', 'google', 'yahoo', 'bing']
#gis_layer_openstreetmap_subtypes = ['Mapnik', 'Osmarender', 'Aerial']
gis_layer_openstreetmap_subtypes = ['Mapnik', 'Osmarender']
gis_layer_google_subtypes = ['Satellite', 'Maps', 'Hybrid', 'Terrain']
gis_layer_yahoo_subtypes = ['Satellite', 'Maps', 'Hybrid']
gis_layer_bing_subtypes = ['Satellite', 'Maps', 'Hybrid']
# Base table from which the rest inherit
gis_layer = SQLTable(db, 'gis_layer', timestamp,
            #uuidstamp, # Layers like OpenStreetMap, Google, etc shouldn't sync
            Field('name', notnull=True, label=T('Name')),
            Field('description', label=T('Description')),
            #Field('priority', 'integer', label=T('Priority')),    # System default priority is set in ol_layers_all.js. User priorities are set in WMC.
            Field('enabled', 'boolean', default=True, label=T('Enabled?')))
gis_layer.name.requires = IS_NOT_EMPTY()
for layertype in gis_layer_types:
    resource = 'layer_' + layertype
    table = module + '_' + resource
    title_create = T('Add Layer')
    title_display = T('Layer Details')
    title_list = T('List Layers')
    title_update = T('Edit Layer')
    title_search = T('Search Layers')
    subtitle_create = T('Add New Layer')
    subtitle_list = T('Layers')
    label_list_button = T('List Layers')
    label_create_button = T('Add Layer')
    msg_record_created = T('Layer added')
    msg_record_modified = T('Layer updated')
    msg_record_deleted = T('Layer deleted')
    msg_list_empty = T('No Layers currently defined')
    # Create Type-specific Layer tables
    if layertype == "openstreetmap":
        t = SQLTable(db, table,
            Field('subtype', label=T('Sub-type')),
            gis_layer)
        t.subtype.requires = IS_IN_SET(gis_layer_openstreetmap_subtypes)
        db.define_table(table, t)
        if not len(db().select(db[table].ALL)):
            # Populate table
            for subtype in gis_layer_openstreetmap_subtypes:
                db[table].insert(
                        name = 'OSM ' + subtype,
                        subtype = subtype
                    )
        # Customise CRUD strings if-desired
        label_list_button = T('List OpenStreetMap Layers')
        msg_list_empty = T('No OpenStreetMap Layers currently defined')
        s3.crud_strings[table] = Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, title_search=title_search, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)
    if layertype == "google":
        t = SQLTable(db, table,
            Field('subtype', label=T('Sub-type')),
            gis_layer)
        t.subtype.requires = IS_IN_SET(gis_layer_google_subtypes)
        db.define_table(table, t)
        if not len(db().select(db[table].ALL)):
            # Populate table
            for subtype in gis_layer_google_subtypes:
                db[table].insert(
                        name = 'Google ' + subtype,
                        subtype = subtype,
                        enabled = False
                    )
        # Customise CRUD strings if-desired
        label_list_button = T('List Google Layers')
        msg_list_empty = T('No Google Layers currently defined')
        s3.crud_strings[table] = Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, title_search=title_search, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)
    if layertype == "yahoo":
        t = SQLTable(db, table,
            Field('subtype', label=T('Sub-type')),
            gis_layer)
        t.subtype.requires = IS_IN_SET(gis_layer_yahoo_subtypes)
        db.define_table(table, t)
        if not len(db().select(db[table].ALL)):
            # Populate table
            for subtype in gis_layer_yahoo_subtypes:
                db[table].insert(
                        name = 'Yahoo ' + subtype,
                        subtype = subtype,
                        enabled = False
                    )
        # Customise CRUD strings if-desired
        label_list_button = T('List Yahoo Layers')
        msg_list_empty = T('No Yahoo Layers currently defined')
        s3.crud_strings[table] = Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, title_search=title_search, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)
    if layertype == "bing":
        t = SQLTable(db, table,
            Field('subtype', label=T('Sub-type')),
            gis_layer)
        t.subtype.requires = IS_IN_SET(gis_layer_bing_subtypes)
        db.define_table(table, t)
        if not len(db().select(db[table].ALL)):
            # Populate table
            for subtype in gis_layer_bing_subtypes:
                db[table].insert(
                        name = 'Bing ' + subtype,
                        subtype = subtype,
                        enabled = False
                    )
        # Customise CRUD strings if-desired
        label_list_button = T('List Bing Layers')
        msg_list_empty = T('No Bing Layers currently defined')
        s3.crud_strings[table] = Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, title_search=title_search, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)
    
# GIS Styles: SLD
#db.define_table('gis_style', timestamp,
#                Field('name', notnull=True, unique=True))
#db.gis_style.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 'gis_style.name')]

# GIS WebMapContexts
# (User preferences)
# GIS Config's Defaults should just be the version for user=0?
#db.define_table('gis_webmapcontext', timestamp,
#                Field('user', db.auth_user))
#db.gis_webmapcontext.user.requires = IS_ONE_OF(db, 'auth_user.id', '%(email)s')

# Onvalidation callbacks
def wkt_centroid(form):
    """GIS
    If a Point has LonLat defined: calculate the WKT.
    If a Line/Polygon has WKT defined: validate the format & calculate the LonLat of the Centroid
    Centroid calculation is done using Shapely, which wraps Geos.
    A nice description of the algorithm is provided here: http://www.jennessent.com/arcgis/shapes_poster.htm
    """
    #shapely_error = str(A('Shapely', _href='http://pypi.python.org/pypi/Shapely/', _target='_blank')) + str(T(" library not found, so can't find centroid!"))
    shapely_error = T("Shapely library not found, so can't find centroid!")
    if form.vars.feature_type == '1':
        # Point
        if form.vars.lon == None:
            form.errors['lon'] = T("Invalid: Longitude can't be empty!")
            return
        if form.vars.lat == None:
            form.errors['lat'] = T("Invalid: Latitude can't be empty!")
            return
        form.vars.wkt = 'POINT(%(lon)f %(lat)f)' % form.vars
    elif form.vars.feature_type == '2':
        # Line
        try:
            from shapely.wkt import loads
            try:
                line = loads(form.vars.wkt)
            except:
                form.errors['wkt'] = T("Invalid WKT: Must be like LINESTRING(3 4,10 50,20 25)!")
                return
            centroid_point = line.centroid
            form.vars.lon = centroid_point.wkt.split('(')[1].split(' ')[0]
            form.vars.lat = centroid_point.wkt.split('(')[1].split(' ')[1][:1]
        except:
            form.errors['feature_type'] = shapely_error
    elif form.vars.feature_type == '3':
        # Polygon
        try:
            from shapely.wkt import loads
            try:
                polygon = loads(form.vars.wkt)
            except:
                form.errors['wkt'] = T("Invalid WKT: Must be like POLYGON((1 1,5 1,5 5,1 5,1 1),(2 2, 3 2, 3 3, 2 3,2 2))!")
                return
            centroid_point = polygon.centroid
            form.vars.lon = centroid_point.wkt.split('(')[1].split(' ')[0]
            form.vars.lat = centroid_point.wkt.split('(')[1].split(' ')[1][:1]
        except:
            form.errors['feature_type'] = shapely_error
    else:
        form.errors['feature_type'] = T('Unknown type!')
    return
