module='gis'

# Menu Options
db.define_table('%s_menu_option' % module,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db['%s_menu_option' % module].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s_menu_option.name' % module)]
db['%s_menu_option' % module].name.requires=IS_NOT_EMPTY()
db['%s_menu_option' % module].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s_menu_option.priority' % module)]


# GIS Projections
db.define_table('gis_projection',
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('epsg'),
                SQLField('maxExtent',length=256),
                SQLField('maxResolution'),
                SQLField('units'))
db.gis_projection.exposes=['name','epsg','maxExtent','maxResolution','units']
db.gis_projection.displays=['name','epsg','maxExtent','maxResolution','units']
db.gis_projection.represent=lambda gis_projection: TR(TD(A(gis_projection.name,_href=t2.action('display_projection',gis_projection.id))),TD(gis_projection.epsg))
db.gis_projection.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_projection.name')]
db.gis_projection.epsg.requires=[IS_NOT_EMPTY(),IS_ALPHANUMERIC()]
db.gis_projection.epsg.label="EPSG"
db.gis_projection.maxExtent.requires=IS_NOT_EMPTY()
db.gis_projection.maxExtent.label="maxExtent"
db.gis_projection.maxResolution.requires=IS_NOT_EMPTY()
db.gis_projection.maxResolution.label="maxResolution"
db.gis_projection.units.requires=IS_IN_SET(['m','degrees'])

# GIS Config
# id=1 = Default settings
# ToDo Extend for per-user Profiles
db.define_table('gis_config',
				SQLField('lat'),
				SQLField('lon'),
				SQLField('zoom'),
				SQLField('projection',length=64),
				SQLField('marker',length=64),
				SQLField('map_height'),
				SQLField('map_width'))
db.gis_config.lat.requires=IS_LAT()
db.gis_config.lon.requires=IS_LON()
db.gis_config.zoom.requires=[IS_NOT_EMPTY(),IS_ALPHANUMERIC()]
db.gis_config.projection.requires=IS_IN_DB(db,'gis_projection.uuid','gis_projection.name')
db.gis_config.marker.requires=IS_IN_DB(db,'gis_marker.uuid','gis_marker.name')
db.gis_config.map_height.requires=[IS_NOT_EMPTY(),IS_ALPHANUMERIC()]
db.gis_config.map_width.requires=[IS_NOT_EMPTY(),IS_ALPHANUMERIC()]

# GIS Markers (Icons)
db.define_table('gis_marker',
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('height','integer'), # In Pixels, for display purposes
                SQLField('width','integer'),
                SQLField('image','upload'))
db.gis_marker.exposes=['name','height','width','image']
db.gis_marker.displays=['name','height','width','image']
db.gis_marker.represent=lambda gis_marker: A(gis_marker.name,_href=t2.action('display_marker',gis_marker.id))
db.gis_marker.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_marker.name')]

# GIS Features
db.define_table('gis_feature_class',
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('marker'))
db.gis_feature_class.exposes=['name','marker']
db.gis_feature_class.displays=['name','marker']
db.gis_feature_class.represent=lambda gis_feature_class: A(gis_feature_class.name,_href=t2.action('display_feature_class',gis_feature_class.id))
db.gis_feature_class.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_feature_class.name')]
db.gis_feature_class.marker.requires=IS_NULL_OR(IS_IN_DB(db,'gis_marker.id','gis_marker.name'))

db.define_table('gis_feature_metadata',
                SQLField('created_on','datetime',default=now), # Auto-stamped by T2
                SQLField('created_by',db.t2_person), # Auto-stamped by T2
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('modified_by',db.t2_person), # Auto-stamped by T2
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('description',length=256),
                SQLField('contact',length=64),
                SQLField('source'),
                SQLField('accuracy'),       # Drop-down on a IS_IN_SET[]?
                SQLField('sensitivity'),    # Should be turned into a drop-down by referring to AAA's sensitivity table
                SQLField('event_time','datetime'),
                SQLField('expiry_time','datetime'),
                SQLField('url'),
                SQLField('image','upload'))
db.gis_feature_metadata.exposes=['description','contact','source','accuracy','sensitivity','event_time','expiry_time','url','image']
db.gis_feature_metadata.displays=['created_on','created_by','modified_on','modified_by','description','contact','source','accuracy','sensitivity','event_time','expiry_time','url','image']
db.gis_feature_metadata.contact.requires=IS_NULL_OR(IS_IN_DB(db,'person.uuid','person.full_name'))
db.gis_feature_metadata.event_time.requires=IS_DATETIME()
db.gis_feature_metadata.expiry_time.requires=IS_DATETIME()
db.gis_feature_metadata.url.requires=IS_URL()

db.define_table('gis_feature',
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('feature_class',length=64),
                SQLField('metadata',length=64),
                SQLField('type'),
                SQLField('lat'),
                SQLField('lon'))
db.gis_feature.exposes=['name','feature_class','metadata','type','lat','lon']
db.gis_feature.displays=['name','feature_class','metadata','type','lat','lon']
db.gis_feature.represent=lambda gis_feature: A(gis_feature.name,_href=t2.action('display_feature',gis_feature.id))
db.gis_feature.name.requires=IS_NOT_EMPTY()
db.gis_feature.feature_class.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature_class.uuid','gis_feature_class.name'))
db.gis_feature.metadata.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature_metadata.uuid'))
db.gis_feature.type.requires=IS_IN_SET(['point','line','polygon'])
db.gis_feature.lat.requires=IS_LAT()
db.gis_feature.lat.label=T("Latitude")
db.gis_feature.lon.requires=IS_LON()
db.gis_feature.lon.label=T("Longitude")

# Feature Groups
# Used to select a set of Features for either Display or Export
db.define_table('gis_feature_group',
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('author',db.t2_person))
db.gis_feature_group.exposes=['name','description','author']
db.gis_feature_group.displays=['name','description','author']
db.gis_feature_group.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_feature_group.name')]
db.gis_feature_group.author.requires=IS_IN_DB(db,'t2_person.id','t2_person.name')

# GIS Keys - needed for commercial mapping services
db.define_table('gis_key',
                SQLField('modified_on','datetime',default=now),
                SQLField('service'),
                SQLField('key'),
				SQLField('description',length=256))
db.gis_key.represent=lambda gis_key: TR(TD(A(gis_key.service,_href=t2.action('display_key',gis_key.id))),TD(gis_key.key))
# We want a THIS_NOT_IN_DB here:
db.gis_key.service.requires=IS_IN_SET(['google','multimap','yahoo']) 
#db.gis_key.key.requires=THIS_NOT_IN_DB(db(db.gis_key.service==request.vars.service),'gis_key.service',request.vars.service,'service already in use')
db.gis_key.key.requires=IS_NOT_EMPTY()
db.gis_key.displays=['service','key','description']

# GIS Layers
#gis_layer_types=['internal_features','georss','kml','gpx','shapefile','scan','google','openstreetmap','virtualearth','wms','yahoo']
gis_layer_types=['openstreetmap','google','yahoo','virtualearth']
db.define_table('gis_layer',
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('type'),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default=True))
# Want: [if gis_layer.enabled: 'Enabled']
db.gis_layer.represent=lambda gis_layer: TR(TD(A(gis_layer.name,_href=t2.action('display_layer',gis_layer.id))),TD(gis_layer.enabled))
db.gis_layer.name.requires=IS_NOT_EMPTY()
db.gis_layer.type.requires=IS_IN_SET(gis_layer_types)
db.gis_layer.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_layer.priority')]

# Layer: GeoRSS
db.define_table('gis_layer_georss',
				SQLField('modified_on','datetime',default=now),
				SQLField('layer',length=64),
				SQLField('url',default='http://host.domain.org/service'),
				SQLField('icon',length=64),
				SQLField('projection',length=64),
				SQLField('visible','boolean',default=False))
db.gis_layer_georss.layer.requires=IS_IN_DB(db,'gis_layer.uuid','gis_layer.name')
db.gis_layer_georss.url.requires=IS_URL()
db.gis_layer_georss.icon.requires=IS_IN_DB(db,'gis_marker.uuid','gis_marker.name')
db.gis_layer_georss.projection.requires=IS_IN_DB(db,'gis_projection.uuid','gis_projection.name')

# Layer: Google
db.define_table('gis_layer_google',
				SQLField('modified_on','datetime',default=now),
				SQLField('layer',length=64),
				SQLField('type'))
db.gis_layer_google.layer.requires=IS_IN_DB(db,'gis_layer.uuid','gis_layer.name')
db.gis_layer_google.type.requires=IS_IN_SET(['Satellite','Maps','Hybrid','Terrain'])

# Layer: Internal Features
db.define_table('gis_layer_features',
				SQLField('modified_on','datetime',default=now),
				SQLField('layer',length=64),
				SQLField('feature_group',length=64))
db.gis_layer_features.layer.requires=IS_IN_DB(db,'gis_layer.uuid','gis_layer.name')
db.gis_layer_features.feature_group.requires=IS_IN_DB(db,'gis_feature_group.uuid','gis_feature_group.name')

# Layer: OpenStreetMap
db.define_table('gis_layer_openstreetmap',
				SQLField('modified_on','datetime',default=now),
				SQLField('layer',length=64),
				SQLField('type'))
db.gis_layer_openstreetmap.layer.requires=IS_IN_DB(db,'gis_layer.uuid','gis_layer.name')
db.gis_layer_openstreetmap.type.requires=IS_IN_SET(['Mapnik','Osmarender','Aerial'])

# Layer: Shapefiles (via UMN MapServer)
db.define_table('gis_layer_shapefile',
                SQLField('modified_on','datetime',default=now),
				SQLField('layer',length=64),
                SQLField('projection',length=64))
db.gis_layer_shapefile.layer.requires=IS_IN_DB(db,'gis_layer.uuid','gis_layer.name')
# We should be able to auto-detect this value (but still want to be able to over-ride)
db.gis_layer_shapefile.projection.requires=IS_IN_DB(db,'gis_projection.uuid','gis_projection.name')

# Layer: Virtual Earth
db.define_table('gis_layer_virtualearth',
				SQLField('modified_on','datetime',default=now),
				SQLField('layer',length=64),
				SQLField('type'))
db.gis_layer_virtualearth.layer.requires=IS_IN_DB(db,'gis_layer.uuid','gis_layer.name')
db.gis_layer_virtualearth.type.requires=IS_IN_SET(['Satellite','Maps','Hybrid'])

# Layer: Yahoo
db.define_table('gis_layer_yahoo',
				SQLField('modified_on','datetime',default=now),
				SQLField('layer',length=64),
				SQLField('type'))
db.gis_layer_yahoo.layer.requires=IS_IN_DB(db,'gis_layer.uuid','gis_layer.name')
db.gis_layer_yahoo.type.requires=IS_IN_SET(['Satellite','Maps','Hybrid'])

# Layer: WMS
db.define_table('gis_layer_wms',
                SQLField('modified_on','datetime',default=now),
                SQLField('layer',length=64),
                SQLField('layers'),
                SQLField('type',default='Base'))
db.gis_layer_wms.layer.requires=IS_IN_DB(db,'gis_layer.uuid','gis_layer.name')
db.gis_layer_wms.type.requires=IS_IN_SET(['Base','Overlay'])
# Ideally pull list from GetCapabilities & use to populate IS_IN_SET
db.gis_layer_wms.layers.requires=IS_NOT_EMPTY()

# WMS - Base
db.define_table('gis_layer_wms_base',
                SQLField('modified_on','datetime',default=now),
                SQLField('layer',length=64),
                SQLField('url',default='http://host.domain.org/service'),
                SQLField('projection',length=64))
db.gis_layer_wms_base.layer.requires=IS_IN_DB(db,'gis_layer.uuid','gis_layer.name')
db.gis_layer_wms_base.url.requires=[IS_NOT_EMPTY(),IS_URL()]
db.gis_layer_wms_base.projection.requires=IS_IN_DB(db,'gis_projection.uuid','gis_projection.name')

# WMS - Overlay
db.define_table('gis_layer_wms_overlay',
                SQLField('modified_on','datetime',default=now),
                SQLField('layer',length=64),
                SQLField('url',default='http://host.domain.org/service'),
                SQLField('projection',length=64),
                SQLField('visible','boolean',default=True))
db.gis_layer_wms_overlay.layer.requires=IS_IN_DB(db,'gis_layer.uuid','gis_layer.name')
db.gis_layer_wms_overlay.url.requires=[IS_NOT_EMPTY(),IS_URL()]
db.gis_layer_wms_overlay.projection.requires=IS_IN_DB(db,'gis_projection.uuid','gis_projection.name')

# GIS Styles: SLD
db.define_table('gis_style',
                SQLField('modified_on','datetime',default=now),
                SQLField('name'))
db.gis_style.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_style.name')]

# GIS WebMapContexts
# (User preferences)
db.define_table('gis_webmapcontext',
                SQLField('modified_on','datetime',default=now),
                SQLField('user',db.t2_person))
db.gis_webmapcontext.user.requires=IS_IN_DB(db,'t2_person.id','t2_person.name')

