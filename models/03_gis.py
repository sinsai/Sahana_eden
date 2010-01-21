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
                represent = lambda id: (id and [DIV(IMG(_src=URL(r=request, c='default', f='download', args=db(db.gis_marker.id==id).select().first().image), _height=40))] or [''])[0],
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

# GIS Symbology
resource = 'symbology'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('name', length=128, notnull=True, unique=True),
                migrate=migrate)
# Reusable field for other tables to reference
symbology_id = SQLTable(None, 'symbology_id',
            Field('symbology_id', db.gis_symbology,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'gis_symbology.id', '%(name)s')),
                represent = lambda id: (id and [db(db.gis_symbology.id==id).select()[0].name] or ["None"])[0],
                label = T('Symbology'),
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
				symbology_id,
				marker_id,
				Field('map_height', 'integer', notnull=True),
				Field('map_width', 'integer', notnull=True),
                Field('zoom_levels', 'integer', default=16, notnull=True),
                migrate=migrate)

# GIS Feature Classes
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

# Symbology to Feature Class to Marker
resource = 'symbology_to_feature_class'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', length=128, notnull=True, unique=True),
                symbology_id,
                feature_class_id,
                marker_id,
                migrate=migrate)

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
                represent = lambda id: shn_gis_location_represent(id),
                label = T('Location'),
                comment = DIV(A(ADD_LOCATION, _class='thickbox', _href=URL(r=request, c='gis', f='location', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_LOCATION), A(SPAN("[Help]"), _class="tooltip", _title=T("Location|The Location of this Site, which can be general (for Reporting) or precise (for displaying on a Map)."))),
                ondelete = 'RESTRICT'
                ))

def shn_gis_location_represent(id):
    try:
        # Simple
        #represent = db(db.gis_location.id==id).select().first().name
        # Fancy Map
        #represent = A(db(db.gis_location.id==id).select().first().name, _href='#', _onclick='viewMap(' + str(id) +');return false')
        # Hyperlink
        location  = db(db.gis_location.id==id).select().first()
        represent = A(location.name, _href = S3_PUBLIC_URL + URL(r=request, c='gis', f='location', args=[location.id]))
        # ToDo: Convert to popup? (HTML again!)
        # Export Lat/Lon if available, otherwise name
        # tbc
    except:
        represent = None
    return represent
                
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
ADD_FG = T('Add Feature Group')
feature_group_id = SQLTable(None, 'feature_group_id',
            Field('feature_group_id', db.gis_feature_group,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'gis_feature_group.id', '%(name)s')),
                represent = lambda id: (id and [db(db.gis_feature_group.id==id).select()[0].name] or ["None"])[0],
                label = T('Feature Group'),
                comment = DIV(A(ADD_FG, _class='thickbox', _href=URL(r=request, c='gis', f='feature_group', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_FG), A(SPAN("[Help]"), _class="tooltip", _title=T("Feature Group|A collection of GIS locations which can be displayed together on a map or exported together."))),
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

# GPS Tracks (files in GPX format)
resource = 'track'
table = module + '_' + resource
db.define_table(table, timestamp,
                #uuidstamp, # Tracks don't sync
                Field('name', length=128, notnull=True, unique=True),
                Field('description', length=128),
                Field('track', 'upload', autodelete = True),
                migrate=migrate)
# upload folder needs to be visible to the download() function as well as the upload
db[table].track.uploadfolder = os.path.join(request.folder, "uploads/tracks")
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].track.requires = IS_UPLOAD_FILENAME(extension='gpx')
db[table].track.description = T('Description')
db[table].track.label = T('GPS Track File')
db[table].track.comment = DIV(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("GPS Track|A file in GPX format taken from a GPS whose timestamps can be correlated with the timestamps on the photos to locate them on the map.")))
ADD_TRACK = T('Upload Track')
title_create = ADD_TRACK
title_display = T('Track Details')
title_list = T('List Tracks')
title_update = T('Edit Track')
title_search = T('Search Tracks')
subtitle_create = T('Add New Track')
subtitle_list = T('Tracks')
label_list_button = T('List Tracks')
label_create_button = ADD_TRACK
msg_record_created = T('Track uploaded')
msg_record_modified = T('Track updated')
msg_record_deleted = T('Track deleted')
msg_list_empty = T('No Tracks currently available')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
# Reusable field for other tables to reference
track_id = SQLTable(None, 'track_id',
            Field('track_id', db.gis_track,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'gis_track.id', '%(name)s')),
                represent = lambda id: (id and [db(db.gis_track.id==id).select()[0].name] or ["None"])[0],
                label = T('Track'),
                comment = DIV(A(ADD_TRACK, _class='thickbox', _href=URL(r=request, c='gis', f='track', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_TRACK), A(SPAN("[Help]"), _class="tooltip", _title=T("GPX Track|A file downloaded from a GPS containing a series of geographic points in XML format."))),
                ondelete = 'RESTRICT'
                ))
    
# GIS Layers
#gis_layer_types = ['shapefile', 'scan', 'wfs']
gis_layer_types = ['openstreetmap', 'google', 'yahoo', 'gpx', 'georss', 'kml', 'wms', 'tms', 'xyz', 'js']
#gis_layer_openstreetmap_subtypes = ['Mapnik', 'Osmarender', 'Aerial']
gis_layer_openstreetmap_subtypes = ['Mapnik', 'Osmarender']
gis_layer_google_subtypes = ['Satellite', 'Maps', 'Hybrid', 'Terrain']
gis_layer_yahoo_subtypes = ['Satellite', 'Maps', 'Hybrid']
gis_layer_bing_subtypes = ['Satellite', 'Maps', 'Hybrid', 'Terrain']
# Base table from which the rest inherit
gis_layer = SQLTable(db, 'gis_layer', timestamp,
            #uuidstamp, # Layers like OpenStreetMap, Google, etc shouldn't sync
            Field('name', notnull=True, label=T('Name'), requires=IS_NOT_EMPTY(), comment=SPAN("*", _class="req")),
            Field('description', label=T('Description')),
            #Field('priority', 'integer', label=T('Priority')),    # System default priority is set in ol_layers_all.js. User priorities are set in WMC.
            Field('enabled', 'boolean', default=True, label=T('Enabled?')))
for layertype in gis_layer_types:
    resource = 'layer_' + layertype
    table = module + '_' + resource
    # Create Type-specific Layer tables
    if layertype == "openstreetmap":
        t = SQLTable(db, table,
            gis_layer,
            Field('subtype', label=T('Sub-type'))            )
        db.define_table(table, t, migrate=migrate)
    if layertype == "google":
        t = SQLTable(db, table,
            gis_layer,
            Field('subtype', label=T('Sub-type')))
        db.define_table(table, t, migrate=migrate)
    if layertype == "yahoo":
        t = SQLTable(db, table,
            gis_layer,
            Field('subtype', label=T('Sub-type')))
        db.define_table(table, t, migrate=migrate)
    if layertype == "bing":
        t = SQLTable(db, table,
            gis_layer,
            Field('subtype', label=T('Sub-type')))
        db.define_table(table, t, migrate=migrate)
    if layertype == "wms":
        t = SQLTable(db, table,
            gis_layer,
            Field('url', label=T('Location')),
            Field('base', 'boolean', default=True, label=T('Base Layer?')),
            Field('map', label=T('Map')),
            Field('layers', label=T('Layers')),
            Field('format', label=T('Format')),
            Field('transparent', 'boolean', default=False, label=T('Transparent?')),
            projection_id)
        db.define_table(table, t, migrate=migrate)
    if layertype == "tms":
        t = SQLTable(db, table,
            gis_layer,
            Field('url', label=T('Location')),
            Field('layers', label=T('Layers')),
            Field('format', label=T('Format')))
        db.define_table(table, t, migrate=migrate)
    if layertype == "xyz":
        t = SQLTable(db, table,
            gis_layer,
            Field('url', label=T('Location')),
            Field('base', 'boolean', default=True, label=T('Base Layer?')),
            Field('sphericalMercator', 'boolean', default=False, label=T('Spherical Mercator?')),
            Field('transitionEffect', requires=IS_NULL_OR(IS_IN_SET(['resize'])), label=T('Transition Effect')),
            Field('numZoomLevels', 'integer', label=T('num Zoom Levels')),
            Field('transparent', 'boolean', default=False, label=T('Transparent?')),
            Field('visible', 'boolean', default=True, label=T('Visible?')),
            Field('opacity', 'double', default=0.0, label=T('Transparent?'))
            )
        db.define_table(table, t, migrate=migrate)
    if layertype == "georss":
        t = SQLTable(db, table,
            gis_layer,
            Field('url', label=T('Location')),
            projection_id,
            marker_id)
        db.define_table(table, t, migrate=migrate)
    if layertype == "kml":
        t = SQLTable(db, table,
            gis_layer,
            Field('url', label=T('Location')))
        db.define_table(table, t, migrate=migrate)
    if layertype == "gpx":
        t = SQLTable(db, table,
            gis_layer,
            #Field('url', label=T('Location')),
            track_id,
            marker_id)
        db.define_table(table, t, migrate=migrate)
    if layertype == "js":
        t = SQLTable(db, table,
            gis_layer,
            Field('code', 'text', label=T('Code'), default="var myNewLayer = new OpenLayers.Layer.XYZ();\nmap.addLayer(myNewLayer);"))
        db.define_table(table, t, migrate=migrate)

# GIS Cache
# (Store downloaded KML & GeoRSS feeds)
resource = 'cache'
table = module + '_' + resource
db.define_table(table, timestamp,
                Field('name', length=128, notnull=True, unique=True),
                Field('file', 'upload', autodelete = True),
                migrate=migrate)
# upload folder needs to be visible to the download() function as well as the upload
db[table].file.uploadfolder = os.path.join(request.folder, "uploads/gis_cache")

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

