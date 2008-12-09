# This scaffolding model makes your app work on Google App Engine too   #
try:
    from gluon.contrib.gql import *         # if running on Google App Engine
except:
    db=SQLDB('sqlite://storage.db')         # if not, use SQLite or other DB
else:
    db=GQLDB()                              # connect to Google BigTable
    session.connect(request,response,db=db) # and store sessions there

# Define 'now'
import datetime; now=datetime.datetime.today()

# Use T2 plugin for AAA & CRUD
# At top of file rather than usual bottom as we refer to it within our tables
from applications.plugin_t2.modules.t2 import T2
t2=T2(request,response,session,cache,T,db)


# Modules
db.define_table('module',
                SQLField('name'),
                SQLField('name_nice'),
                SQLField('menu_priority','integer'),
                SQLField('description',length=256),
                SQLField('enabled','boolean',default='True'))

db.module.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'module.name')]
db.module.name_nice.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'module.name_nice')]
db.module.menu_priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'module.menu_priority')]

# GIS Menu Options
db.define_table('gis_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))

db.gis_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_menu_option.name')]
db.gis_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_menu_option.priority')]

# GIS Features
db.define_table('gis_feature',
                SQLField('name'),
                SQLField('feature_class'),
                SQLField('metadata'),
                SQLField('type'),
                SQLField('lat'),
                SQLField('lon'))

db.gis_feature.name.requires=IS_NOT_EMPTY()
db.gis_feature.feature_class.requires=IS_IN_DB(db,'gis_feature_class.name')
db.gis_feature.metadata.requires=IS_IN_DB(db,'gis_feature_metadata.id')
db.gis_feature.type.requires=IS_IN_SET(['point','line','polygon'])
db.gis_feature.lat.requires=IS_LAT()
db.gis_feature.lon.requires=IS_LON()

db.define_table('gis_feature_metadata',
                SQLField('name',db.gis_feature),
                SQLField('description',length=256),
                SQLField('author',db.t2_person),
                SQLField('timestamp_event','datetime'),
                SQLField('timestamp_added','datetime',default=now))

db.gis_feature_metadata.name.requires=[IS_NOT_EMPTY(),IS_IN_DB(db,'gis_feature.name')]
db.gis_feature_metadata.author.requires=IS_IN_DB(db,'t2_person.id')
db.gis_feature_metadata.timestamp_event.requires=IS_DATETIME()
db.gis_feature_metadata.timestamp_added.requires=IS_DATETIME()

db.define_table('gis_feature_class',
                SQLField('name'))

db.gis_feature_class.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_feature_class.name')]

# Feature Groups
# Used to select a set of Features for either Display or Export
db.define_table('gis_feature_group',
                SQLField('name'),
                SQLField('author',db.t2_person))

db.gis_feature_group.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_feature_group.name')]
db.gis_feature_group.author.requires=IS_IN_DB(db,'t2_person.id')

# Keys - needed for commercial mapping services
db.define_table('gis_key',
                SQLField('service'),
                SQLField('key'))
options=[x for x in ['google','multimap','yahoo'] if not db(db.gis_key.service==x).count()]
db.gis_key.service.requires=IS_IN_SET(options) 
db.gis_key.key.requires=IS_NOT_EMPTY()
db.gis_key.represent=lambda gis_key: A(gis_key.service,_href=t2.action('display_key',gis_key.id))

# GIS Layers
db.define_table('gis_layer',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('type'),
                SQLField('enabled','boolean',default='True'))

db.gis_layer.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_layer.name')]
db.gis_layer.type.requires=IS_IN_SET(['Base','Overlay'])
db.gis_layer.represent=lambda gis_layer: A(gis_layer.name,_href=t2.action('display_layer',gis_layer.id))

db.define_table('gis_layer_base',
                SQLField('layer_id',db.gis_layer),
                SQLField('type'))

db.gis_layer_base.layer_id.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
#db.gis_layer_base.type.requires=IS_IN_SET(['google','mapserver','openstreetmap','virtualearth','wms','yahoo'])
db.gis_layer_base.type.requires=IS_IN_SET(['google'])

db.define_table('gis_layer_overlay',
                SQLField('name',db.gis_layer),
                SQLField('type'),
                SQLField('visible','boolean',default='True'))

db.gis_layer_overlay.name.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
#db.gis_layer_overlay.type.requires=IS_IN_SET(['internal_features','georss','kml','mapserver','openstreetmap','wms'])
db.gis_layer_overlay.type.requires=IS_IN_SET(['internal_features'])

db.define_table('gis_layer_internal',
                SQLField('name',db.gis_layer),
                SQLField('feature_group',db.gis_feature_group))

db.gis_layer_internal.name.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
db.gis_layer_internal.feature_group.requires=[IS_NOT_EMPTY(),IS_IN_DB(db,'gis_feature_group.name')]

db.define_table('gis_layer_google',
                SQLField('name',db.gis_layer),
                SQLField('type'),
                SQLField('key',db.gis_key))

db.gis_layer_google.name.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
db.gis_layer_google.type.requires=IS_IN_SET(['maps','sat','hybrid','terrain'])
db.gis_layer_google.key.requires=IS_IN_DB(db,'gis_key.id','gis_key.key')

db.define_table('gis_layer_base_wms',
                SQLField('name',db.gis_layer),
                SQLField('url'))

db.gis_layer_base_wms.name.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
db.gis_layer_base_wms.url.requires=[IS_NOT_EMPTY(),IS_URL()]

db.define_table('gis_layer_overlay_wms',
                SQLField('name',db.gis_layer),
                SQLField('url'))

db.gis_layer_overlay_wms.name.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
db.gis_layer_overlay_wms.url.requires=[IS_NOT_EMPTY(),IS_URL()]

# GIS Projections
db.define_table('gis_projection',
                SQLField('name'),
                SQLField('epsg'))

db.gis_projection.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_projection.name')]
db.gis_projection.epsg.requires=[IS_NOT_EMPTY(),IS_ALPHANUMERIC()]

# GIS Markers
db.define_table('gis_marker',
                SQLField('name'),
                SQLField('image','upload'))

db.gis_marker.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_marker.name')]

# GIS Maps (UMN MapServer)
db.define_table('gis_map',
                SQLField('name'))

db.gis_map.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_map.name')]

# GIS Styles: SLD
db.define_table('gis_style',
                SQLField('name'))

db.gis_style.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_style.name')]

# Users can store a WebMapContext
db.define_table('gis_webmapcontext',
                SQLField('user',db.t2_person))

db.gis_webmapcontext.user.requires=IS_IN_DB(db,'t2_person.id')



# CR Menu Options
db.define_table('cr_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))

db.cr_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'cr_menu_option.name')]
db.cr_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'cr_menu_option.priority')]

# DVR Menu Options
db.define_table('dvr_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))

db.dvr_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'dvr_menu_option.name')]
db.dvr_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'dvr_menu_option.priority')]

# IMS Menu Options
db.define_table('ims_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))

db.ims_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'ims_menu_option.name')]
db.ims_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'ims_menu_option.priority')]

# MPR Menu Options
db.define_table('mpr_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))

db.mpr_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'mpr_menu_option.name')]
db.mpr_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'mpr_menu_option.priority')]

# OR Menu Options
db.define_table('or_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))

db.or_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'or_menu_option.name')]
db.or_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'or_menu_option.priority')]

# RMS Menu Options
db.define_table('rms_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))

db.rms_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'rms_menu_option.name')]
db.rms_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'rms_menu_option.priority')]

# VOL Menu Options
db.define_table('vol_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))

db.vol_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'vol_menu_option.name')]
db.vol_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'vol_menu_option.priority')]
