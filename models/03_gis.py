# -*- coding: utf-8 -*-

module = 'gis'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)

# GIS Markers (Icons)
resource = 'marker'
table = module + '_' + resource
db.define_table(table, timestamp,
                #uuidstamp, # Markers don't sync
                Field('name', length=128, notnull=True, unique=True),
                #Field('height', 'integer'), # In Pixels, for display purposes
                #Field('width', 'integer'),  # Not needed since we get size client-side using Javascript's Image() class
                Field('image', 'upload', autodelete = True),
                migrate=migrate)
# upload folder needs to be visible to the download() function as well as the upload
db[table].image.uploadfolder = os.path.join(request.folder, "static/img/markers")
# Reusable field for other tables to reference
ADD_MARKER = T('Add Marker')
marker_id = SQLTable(None, 'marker_id',
            Field('marker_id', db.gis_marker,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'gis_marker.id', '%(name)s')),
                represent = lambda id: DIV(A(IMG(_src=URL(r=request, c='default', f='download', args=(id and [db(db.gis_marker.id==id).select()[0].image] or ["None"])[0]), _height=40), _class='zoom', _href='#zoom-gis_config-marker-%s' % id), DIV(IMG(_src=URL(r=request, c='default', f='download', args=(id and [db(db.gis_marker.id==id).select()[0].image] or ["None"])[0]),_width=600), _id='zoom-gis_config-marker-%s' % id, _class='hidden')),
                label = T('Marker'),
                comment = DIV(A(ADD_MARKER, _class='thickbox', _href=URL(r=request, c='gis', f='marker', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_MARKER), A(SPAN("[Help]"), _class="tooltip", _title=T("Marker|Defines the icon used for display of features."))),
                ondelete = 'RESTRICT'
                ))

# GIS Projections
resource = 'projection'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('name', length=128, notnull=True, unique=True),
                Field('epsg', 'integer', notnull=True),
                Field('maxExtent', length=64, notnull=True),
                Field('maxResolution', 'double', notnull=True),
                Field('units', notnull=True),
                migrate=migrate)
# Reusable field for other tables to reference
projection_id = SQLTable(None, 'projection_id',
            Field('projection_id', db.gis_projection,
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

# GIS Feature Classes
resource_opts = {
    'shelter':T('Shelter'),
    'office':T('Office'),
    }
# These are used in groups (for display/export), for icons & for URLs to edit data
resource = 'feature_class'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', length=128, notnull=True, unique=True),
                Field('description'),
                marker_id,
                Field('module'),    # Used to build Edit URL
                Field('resource'),  # Used to build Edit URL & to provide Attributes to Display
                migrate=migrate)
# Reusable field for other tables to reference
ADD_FEATURE_CLASS = T('Add Feature Class')
feature_class_id = SQLTable(None, 'feature_class_id',
            Field('feature_class_id', db.gis_feature_class,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'gis_feature_class.id', '%(name)s')),
                represent = lambda id: (id and [db(db.gis_feature_class.id==id).select()[0].name] or ["None"])[0],
                label = T('Feature Class'),
                comment = DIV(A(ADD_FEATURE_CLASS, _class='thickbox', _href=URL(r=request, c='gis', f='feature_class', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_FEATURE_CLASS), A(SPAN("[Help]"), _class="tooltip", _title=T("Feature Class|Defines the marker used for display & the attributes visible in the popup."))),
                ondelete = 'RESTRICT'
                ))

# GIS Locations
gis_feature_type_opts = {
    1:T('Point'),
    2:T('Line'),
    3:T('Polygon')
    }
resource = 'location'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', notnull=True),
                feature_class_id,
                #Field('resource_id', 'integer'), # ID in associated resource table. FIXME: Remove as link should be reversed?
                Field('parent', 'reference gis_location', ondelete = 'RESTRICT'),   # This form of hierarchy may not work on all Databases
                marker_id,
                Field('gis_feature_type', 'integer', default=1, notnull=True),
                Field('lat', 'double'), # Only needed for Points
                Field('lon', 'double'), # Only needed for Points
                Field('wkt'),           # WKT is auto-calculated from lat/lon for Points
                admin_id,
                migrate=migrate)
# Reusable field for other tables to reference
ADD_LOCATION = T('Add Location')
location_id = SQLTable(None, 'location_id',
            Field('location_id', db.gis_location,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'gis_location.id', '%(name)s')),
                represent = lambda id: (id and [db(db.gis_location.id==id).select()[0].name] or ["None"])[0],
                label = T('Location'),
                comment = DIV(A(ADD_LOCATION, _class='thickbox', _href=URL(r=request, c='gis', f='location', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_LOCATION), A(SPAN("[Help]"), _class="tooltip", _title=T("Location|The Location of this Site, which can be general (for Reporting) or precise (for displaying on a Map)."))),
                ondelete = 'RESTRICT'
                ))

# Feature Groups
# Used to select a set of Features for either Display or Export
resource = 'feature_group'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, authorstamp, deletion_status,
                Field('name', length=128, notnull=True, unique=True),
                Field('description'),
                Field('enabled', 'boolean', default=True, label=T('Enabled?')),
                migrate=migrate)
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
resource = 'location_to_feature_group'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                feature_group_id,
                location_id,
                migrate=migrate)

resource = 'feature_class_to_feature_group'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                feature_group_id,
                feature_class_id,
                migrate=migrate)

# GIS Keys - needed for commercial mapping services
resource = 'apikey' # Can't use 'key' as this has other meanings for dicts!
table = module + '_' + resource
db.define_table(table, timestamp,
                Field('name', notnull=True),
                Field('apikey', length=128, notnull=True),
				Field('description'),
                migrate=migrate)

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
    # Create Type-specific Layer tables
    if layertype == "openstreetmap":
        t = SQLTable(db, table,
            Field('subtype', label=T('Sub-type')),
            gis_layer)
        db.define_table(table, t, migrate=migrate)
    if layertype == "google":
        t = SQLTable(db, table,
            Field('subtype', label=T('Sub-type')),
            gis_layer)
        db.define_table(table, t, migrate=migrate)
    if layertype == "yahoo":
        t = SQLTable(db, table,
            Field('subtype', label=T('Sub-type')),
            gis_layer)
        db.define_table(table, t, migrate=migrate)
    if layertype == "bing":
        t = SQLTable(db, table,
            Field('subtype', label=T('Sub-type')),
            gis_layer)
        t.subtype.requires = IS_IN_SET(gis_layer_bing_subtypes)
        db.define_table(table, t, migrate=migrate)

# GPS Tracks (files in GPX format)
resource = 'track'
table = module + '_' + resource
db.define_table(table, timestamp,
                #uuidstamp, # Tracks don't sync
                Field('name', length=128, notnull=True, unique=True),
                Field('track', 'upload', autodelete = True),
                migrate=migrate)
# upload folder needs to be visible to the download() function as well as the upload
db[table].track.uploadfolder = os.path.join(request.folder, "uploads/tracks")
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].track.label = T('GPS Track File')
db[table].track.comment = DIV(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("GPS Track|A file in GPX format taken from a GPS whose timestamps can be correlated with the timestamps on the photos to locate them on the map.")))

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

