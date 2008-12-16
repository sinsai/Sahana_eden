# This scaffolding model makes your app work on Google App Engine too   #
#try:
#    from gluon.contrib.gql import *         # if running on Google App Engine
#except:
db=SQLDB('sqlite://storage.db')         # if not, use SQLite or other DB
#else:
#    db=GQLDB()                              # connect to Google BigTable
#    session.connect(request,response,db=db) # and store sessions there

# Define 'now'
import datetime; now=datetime.datetime.today()

# Use T2 plugin for AAA & CRUD
# At top of file rather than usual bottom as we refer to it within our tables
#from applications.sahana.modules.t2 import T2
#t2=T2(request,response,session,cache,T,db)

# Custom classes which extend default T2
from applications.sahana.modules.sahana import T2SAHANA
t2=T2SAHANA(request,response,session,cache,T,db)

# Custom validators
from applications.sahana.modules.validators import *

#
# Core Framework
#

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

# Home Menu Options
db.define_table('home_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db.home_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'home_menu_option.name')]
db.home_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'home_menu_option.priority')]

# Field options meta table
# Give a custom list of options for each field in this schema 
# prefixed with opt_. This is customizable then at deployment
# See the field_options.py for default customizations
# Modules: cr
db.define_table('field_option',
                SQLField('field_name'),
                SQLField('option_code',length=20),
                SQLField('option_description',length=50))
db.field_option.field_name.requires=IS_NOT_EMPTY()
db.field_option.option_code.requires=IS_NOT_EMPTY()
db.field_option.option_description.requires=IS_NOT_EMPTY()

# System Config
db.define_table('system_config',
				SQLField('setting'),
				SQLField('description',length=256),
				SQLField('value'))
# We want a THIS_NOT_IN_DB here: admin_name, admin_email, admin_tel
db.system_config.setting.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'system_config.setting')]

# Persons
# Modules: cr,dvr,mpr
db.define_table('person',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('full_name'),
                SQLField('family_name'),
                SQLField('l10_name'))
db.person.represent=lambda person: A(person.full_name,_href=t2.action('display_person',person.id))
db.person.full_name.requires=IS_NOT_EMPTY()

# Person Contacts
# Modules: cr,dvr,mpr
db.define_table('person_contact',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('person',db.person),
                SQLField('opt_contact_type'),	# mobile, home phone, email, IM, etc
                SQLField('contact_value'))
db.person_contact.person.requires=IS_IN_DB(db,'person.id','person.full_name')

# Person Identity
# Modules: dvr,mpr
db.define_table('person_identity',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('person',db.person),
                SQLField('opt_id_type'),		# ID card, Passport, Driving License, etc
                SQLField('id_value'))
db.person_identity.person.requires=IS_IN_DB(db,'person.id','person.full_name')

# Person Details
# Modules: cr,dvr,mpr
db.define_table('person_details',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('person',db.person),
                SQLField('next_kin',db.person),
                SQLField('birth_date','date'),
                SQLField('opt_age_group'),
                SQLField('relation'),
                SQLField('opt_country'),
                SQLField('opt_race'),
                SQLField('opt_religion'),
                SQLField('opt_marital_status'),
                SQLField('opt_gender'),
                SQLField('occupation'))
db.person_details.person.requires=IS_IN_DB(db,'person.id','person.full_name')
db.person_details.next_kin.requires=IS_IN_DB(db,'person.id','person.full_name')
db.person_details.birth_date.requires=IS_DATE(T("%Y-%m-%d")) # Can use Translation to provide localised formatting

# Person Status
# Modules: dvr,mpr
db.define_table('person_status',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('person',db.person),
                SQLField('isReliefWorker','boolean',default=False),
                SQLField('isVictim','boolean',default=True),
                SQLField('opt_status'),	# missing, injured, etc. customizable
                SQLField('id_value'))
db.person_status.person.requires=IS_IN_DB(db,'person.id','person.full_name')

# Person Physical
# Modules: dvr,mpr
db.define_table('person_physical',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('person',db.person),
                SQLField('height'),
                SQLField('weight'),
                SQLField('opt_blood_type'),
                SQLField('opt_eye_color'),
                SQLField('opt_skin_color'),
                SQLField('opt_hair_color'),
                SQLField('injuries'),
                SQLField('comments',length=256))
db.person_physical.person.requires=IS_IN_DB(db,'person.id','person.full_name')

# Person Missing
# Modules: dvr,mpr
db.define_table('person_missing',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('person',db.person),
                SQLField('last_seen'),
                SQLField('last_clothing'),
                SQLField('comments',length=256))
db.person_missing.person.requires=IS_IN_DB(db,'person.id','person.full_name')

# Person Deceased
# Modules: dvr,mpr
db.define_table('person_deceased',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('person',db.person),
                SQLField('details'),
                SQLField('date_of_death','date'),
                SQLField('place_of_death'),
                SQLField('comments',length=256))
db.person_deceased.person.requires=IS_IN_DB(db,'person.id','person.full_name')

# Person Reporter
# (The person who reported about this person)
# Modules: dvr,mpr
db.define_table('person_report',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('person',db.person),
                SQLField('reporter',db.person),
                SQLField('relation'))
db.person_report.person.requires=IS_IN_DB(db,'person.id','person.full_name')
db.person_report.reporter.requires=IS_IN_DB(db,'person.id','person.full_name')

# Person Group
# Modules: dvr,mpr
db.define_table('person_group',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('opt_group_type'))

# Person Group Details
# Modules: dvr,mpr
db.define_table('person_group_details',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('person_group',db.person_group),
                SQLField('head',db.person),
                SQLField('no_of_adult_males','integer'),
                SQLField('no_of_adult_females','integer'),
                SQLField('no_of_children','integer'),
                SQLField('no_displaced','integer'),
                SQLField('no_missing','integer'),
                SQLField('no_dead','integer'),
                SQLField('no_rehabilitated','integer'),
                SQLField('checklist'),
                SQLField('description',length=256))
db.person_group_details.person_group.requires=IS_IN_DB(db,'person_group.id')
db.person_group_details.head.requires=IS_IN_DB(db,'person.id','person.full_name')

# Person to Group
# (A person can belong to multiple groups)
# Modules: dvr,mpr
db.define_table('person_to_group',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('person',db.person),
                SQLField('person_group',db.person_group))
db.person_to_group.person.requires=IS_IN_DB(db,'person.id','person.full_name')
db.person_to_group.person_group.requires=IS_IN_DB(db,'person_group.id')

 
#
# GIS
#

# GIS Menu Options
db.define_table('gis_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default=True))
db.gis_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_menu_option.name')]
db.gis_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_menu_option.priority')]

# GIS Projections
db.define_table('gis_projection',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('name'),
                SQLField('epsg'),
                SQLField('maxExtent',length=256),
                SQLField('maxResolution'),
                SQLField('units'))
db.gis_projection.represent=lambda gis_projection: TR(TD(A(gis_projection.name,_href=t2.action('display_projection',gis_projection.id))),TD(gis_projection.epsg))
db.gis_projection.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_projection.name')]
db.gis_projection.epsg.requires=[IS_NOT_EMPTY(),IS_ALPHANUMERIC()]
db.gis_projection.epsg.label="EPSG"
db.gis_projection.maxExtent.requires=IS_NOT_EMPTY()
db.gis_projection.maxExtent.label="maxExtent"
db.gis_projection.maxResolution.requires=IS_NOT_EMPTY()
db.gis_projection.maxResolution.label="maxResolution"
db.gis_projection.units.requires=IS_IN_SET(['m','degrees'])
db.gis_projection.displays=['name','epsg','maxExtent','maxResolution','units']

# GIS Config
db.define_table('gis_config',
				SQLField('setting'), # lat, lon, zoom, projection, marker, map_height, map_width
				SQLField('description',length=256),
				SQLField('value'))
db.gis_config.represent=lambda gis_config: A(gis_config.setting,_href=t2.action('display_config',gis_config.id))
# We don't want a THIS_NOT_IN_DB here as it makes it easier for Rapid Customisation in Field 
db.gis_config.setting.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_config.setting')]
# Projection should have value only from available options:
#db.gis_config.setting==projection,db.gis_config.value.requires=IS_IN_DB(db,'gis_projection.id','gis_projection.name')
# Marker should have value only from available options:
#db.gis_config.setting==marker,db.gis_config.value.requires=IS_IN_DB(db,'gis_marker.id','gis_marker.name')

# GIS Markers (Icons)
db.define_table('gis_marker',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('name'),
                SQLField('height','integer'), # In Pixels, for display purposes
                SQLField('width','integer'),
                SQLField('image','upload'))
db.gis_marker.represent=lambda gis_marker: A(gis_marker.name,_href=t2.action('display_marker',gis_marker.id))
db.gis_marker.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_marker.name')]

# GIS Features
db.define_table('gis_feature_class',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('name'),
                SQLField('marker'))
db.gis_feature_class.represent=lambda gis_feature_class: A(gis_feature_class.name,_href=t2.action('display_feature_class',gis_feature_class.id))
db.gis_feature_class.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_feature_class.name')]
db.gis_feature_class.marker.requires=IS_NULL_OR(IS_IN_DB(db,'gis_marker.id','gis_marker.name'))

db.define_table('gis_feature_metadata',
                SQLField('created_on','datetime',default=now), # Auto-stamped by T2
                SQLField('created_by',db.t2_person), # Auto-stamped by T2
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('modified_by',db.t2_person), # Auto-stamped by T2
                SQLField('description',length=256),
                SQLField('event_time','datetime'),
                SQLField('url'),
                SQLField('image','upload'))
db.gis_feature_metadata.event_time.requires=IS_DATETIME()
db.gis_feature_metadata.url.requires=IS_URL()

db.define_table('gis_feature',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('name'),
                SQLField('feature_class',db.gis_feature_class),
                SQLField('metadata',db.gis_feature_metadata),
                SQLField('type'),
                SQLField('lat'),
                SQLField('lon'))
db.gis_feature.represent=lambda gis_feature: A(gis_feature.name,_href=t2.action('display_feature',gis_feature.id))
db.gis_feature.name.requires=IS_NOT_EMPTY()
db.gis_feature.feature_class.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature_class.id','gis_feature_class.name'))
db.gis_feature.metadata.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature_metadata.id'))
db.gis_feature.type.requires=IS_IN_SET(['point','line','polygon'])
db.gis_feature.lat.requires=IS_LAT()
db.gis_feature.lat.label="Latitude"
db.gis_feature.lon.requires=IS_LON()
db.gis_feature.lon.label="Longitude"

# Feature Groups
# Used to select a set of Features for either Display or Export
db.define_table('gis_feature_group',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('name'),
                SQLField('author',db.t2_person))
db.gis_feature_group.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_feature_group.name')]
db.gis_feature_group.author.requires=IS_IN_DB(db,'t2_person.id','t2_person.name')

# GIS Keys - needed for commercial mapping services
db.define_table('gis_key',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('service'),
                SQLField('key'),
				SQLField('description',length=256))
db.gis_key.represent=lambda gis_key: TR(TD(A(gis_key.service,_href=t2.action('display_key',gis_key.id))),TD(gis_key.key))
# We want a THIS_NOT_IN_DB here:
db.gis_key.service.requires=IS_IN_SET(['google','multimap','yahoo']) 
#db.gis_key.key.requires=THIS_NOT_IN_DB(db(db.gis_key.service==request.vars.service),'gis_key.service',request.vars.service,'service already in use')
db.gis_key.key.requires=IS_NOT_EMPTY()
db.gis_key.displays=['service','key','description']

# GIS Layer Types
#IS_IN_SET(['internal_features','georss','kml','gpx','shapefile','scan','google','openstreetmap','virtualearth','wms','yahoo'])
db.define_table('gis_layer_type',
				SQLField('name'),
				SQLField('description',length=256))

db.gis_layer_type.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_layer_type.name')]

# GIS Layers
db.define_table('gis_layer',
				SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('name'),
				SQLField('description',length=256),
				SQLField('type',db.gis_layer_type),
				SQLField('priority','integer'),
                SQLField('enabled','boolean',default=True))
# Want: [if gis_layer.enabled: 'Enabled']
db.gis_layer.represent=lambda gis_layer: TR(TD(A(gis_layer.name,_href=t2.action('display_layer',gis_layer.id))),TD(gis_layer.enabled))
db.gis_layer.name.requires=IS_NOT_EMPTY()
db.gis_layer.type.requires=IS_IN_DB(db,'gis_layer_type.id','gis_layer_type.name')
db.gis_layer.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_layer.priority')]

# Layer: GeoRSS
db.define_table('gis_layer_georss',
				SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
				SQLField('layer',db.gis_layer),
				SQLField('url',default='http://host.domain.org/service'),
				SQLField('icon',db.gis_marker),
				SQLField('projection',db.gis_projection),
				SQLField('visible','boolean',default=False))
db.gis_layer_georss.layer.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
db.gis_layer_georss.url.requires=IS_URL()
db.gis_layer_georss.icon.requires=IS_IN_DB(db,'gis_marker.id','gis_marker.name')
db.gis_layer_georss.projection.requires=IS_IN_DB(db,'gis_projection.id','gis_projection.name')

# Layer: Google
db.define_table('gis_layer_google',
				SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
				SQLField('layer',db.gis_layer),
				SQLField('type'))
db.gis_layer_google.layer.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
db.gis_layer_google.type.requires=IS_IN_SET(['Satellite','Maps','Hybrid','Terrain'])

# Layer: Internal Features
db.define_table('gis_layer_features',
				SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
				SQLField('layer',db.gis_layer),
				SQLField('feature_group',db.gis_feature_group))
db.gis_layer_features.layer.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
db.gis_layer_features.feature_group.requires=IS_IN_DB(db,'gis_feature_group.id','gis_feature_group.name')

# Layer: OpenStreetMap
db.define_table('gis_layer_openstreetmap',
				SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
				SQLField('layer',db.gis_layer),
				SQLField('type'))
db.gis_layer_openstreetmap.layer.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
db.gis_layer_openstreetmap.type.requires=IS_IN_SET(['Mapnik','Osmarender','Aerial'])

# Layer: Shapefiles (via UMN MapServer)
db.define_table('gis_layer_shapefile',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
				SQLField('layer',db.gis_layer),
                SQLField('projection',db.gis_projection))
db.gis_layer_shapefile.layer.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
# We should be able to auto-detect this value (but still want to be able to over-ride)
db.gis_layer_shapefile.projection.requires=IS_IN_DB(db,'gis_projection.id','gis_projection.name')

# Layer: Virtual Earth
db.define_table('gis_layer_virtualearth',
				SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
				SQLField('layer',db.gis_layer),
				SQLField('type'))
db.gis_layer_virtualearth.layer.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
db.gis_layer_virtualearth.type.requires=IS_IN_SET(['Satellite','Maps','Hybrid'])

# Layer: Yahoo
db.define_table('gis_layer_yahoo',
				SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
				SQLField('layer',db.gis_layer),
				SQLField('type'))
db.gis_layer_yahoo.layer.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
db.gis_layer_yahoo.type.requires=IS_IN_SET(['Satellite','Maps','Hybrid'])

# Layer: WMS
db.define_table('gis_layer_wms',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('layer',db.gis_layer),
                SQLField('layers'),
                SQLField('type',default='Base'))
db.gis_layer_wms.layer.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
db.gis_layer_wms.type.requires=IS_IN_SET(['Base','Overlay'])
# Ideally pull list from GetCapabilities & use to populate IS_IN_SET
db.gis_layer_wms.layers.requires=IS_NOT_EMPTY()

# WMS - Base
db.define_table('gis_layer_wms_base',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('layer',db.gis_layer),
                SQLField('url',default='http://host.domain.org/service'),
                SQLField('projection',db.gis_projection))
db.gis_layer_wms_base.layer.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
db.gis_layer_wms_base.url.requires=[IS_NOT_EMPTY(),IS_URL()]
db.gis_layer_wms_base.projection.requires=IS_IN_DB(db,'gis_projection.id','gis_projection.name')

# WMS - Overlay
db.define_table('gis_layer_wms_overlay',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('layer',db.gis_layer),
                SQLField('url',default='http://host.domain.org/service'),
                SQLField('projection',db.gis_projection),
                SQLField('visible','boolean',default=True))
db.gis_layer_wms_overlay.layer.requires=IS_IN_DB(db,'gis_layer.id','gis_layer.name')
db.gis_layer_wms_overlay.url.requires=[IS_NOT_EMPTY(),IS_URL()]
db.gis_layer_wms_overlay.projection.requires=IS_IN_DB(db,'gis_projection.id','gis_projection.name')

# GIS Styles: SLD
db.define_table('gis_style',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('name'))
db.gis_style.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_style.name')]

# GIS WebMapContexts
# (User preferences)
db.define_table('gis_webmapcontext',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('user',db.t2_person))
db.gis_webmapcontext.user.requires=IS_IN_DB(db,'t2_person.id','t2_person.name')


#
# Shelter Registry
#

# CR Menu Options
db.define_table('cr_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db.cr_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'cr_menu_option.name')]
db.cr_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'cr_menu_option.priority')]

# CR Shelters
db.define_table('cr_shelter',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('address',length=256),
                SQLField('capacity','integer'),
                SQLField('dwellings','integer'),
                SQLField('area'),
                SQLField('persons_per_dwelling','integer'),
                SQLField('contact',db.person),
                SQLField('location',db.gis_feature))
db.cr_shelter.represent=lambda cr_shelter: A(cr_shelter.name,_href=t2.action('display_shelter',cr_shelter.id))
db.cr_shelter.name.requires=IS_NOT_EMPTY()
# Doesn't allow db entry:
#db.cr_shelter.name.widget=lambda self,value: DIV(INPUT(_type='text'),SPAN(_class='req'))
#db.cr_shelter.name.widget=lambda self,value: DIV(INPUT(_type='text', _id=field_id,_class=field.type,_name=fieldname,value=str(default),requires=field.requires),SPAN(_class='req'))
#db.cr_shelter.name.widget=t2.input_required_widget
#db.cr_shelter.name.widget=lambda self,value: t2.input_required_widget
# Most promising, but need to fix scope for field_id:
#db.cr_shelter.name.widget=lambda self,value: t2.input_required_widget('name')
#db.cr_shelter.name.widget=lambda self,value: t2.input_required_widget(self,value)
#db.cr_shelter.name.widget=lambda self,value: t2.input_required_widget(value)
db.cr_shelter.contact.requires=IS_NULL_OR(IS_IN_DB(db,'person.id','person.full_name'))
db.cr_shelter.location.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature.id','gis_feature.name'))

#
# Disaster Victim Registry
#

# DVR Menu Options
db.define_table('dvr_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db.dvr_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'dvr_menu_option.name')]
db.dvr_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'dvr_menu_option.priority')]

#
# Inventory Management System
#

# IMS Menu Options
db.define_table('ims_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db.ims_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'ims_menu_option.name')]
db.ims_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'ims_menu_option.priority')]

#
# Missing Persons Registry
#

# MPR Menu Options
db.define_table('mpr_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db.mpr_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'mpr_menu_option.name')]
db.mpr_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'mpr_menu_option.priority')]

#
# Organisation Registry
#

# OR Menu Options
db.define_table('or_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db.or_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'or_menu_option.name')]
db.or_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'or_menu_option.priority')]

# OR Organisations
db.define_table('or_organisation',
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('name'),
                #SQLField('parent',db.organisation),
                SQLField('opt_org_type'),
                SQLField('registration'),	# Registration Number
                SQLField('manpower'),
                SQLField('equipment'),
                SQLField('privacy','integer',default=0),
                SQLField('archived','boolean',default=False),
                SQLField('address',length=256),
                SQLField('contact',db.person))
db.or_organisation.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'or_organisation.name')]
#db.or_organisation.parent.requires=IS_NULL_OR(IS_IN_DB(db,'or_organisation.id','or_organisation.name'))
db.or_organisation.contact.requires=IS_NULL_OR(IS_IN_DB(db,'person.id','person.full_name'))

#
# Request Management System
#

# RMS Menu Options
db.define_table('rms_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db.rms_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'rms_menu_option.name')]
db.rms_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'rms_menu_option.priority')]

#
# Volunteer Coordination
#

# VOL Menu Options
db.define_table('vol_menu_option',
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db.vol_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'vol_menu_option.name')]
db.vol_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'vol_menu_option.priority')]
