module='gis'

# Menu Options
table='%s_menu_option' % module
db.define_table(table,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('access',db.s3_role),  # Hide menu options if users don't have the required access level
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db['%s' % table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name' % table)]
db['%s' % table].function.requires=IS_NOT_EMPTY()
db['%s' % table].access.requires=IS_NULL_OR(IS_IN_DB(db,'s3_role.id','s3_role.name'))
db['%s' % table].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.priority' % table)]
if not len(db().select(db['%s' % table].ALL)):
	db['%s' % table].insert(
        name="Home",
	function="index",
	priority=0,
	description="Home",
	enabled='True'
	)
	db['%s' % table].insert(
        name="Map Viewing Client",
	function="map_viewing_client",
	priority=1,
	enabled='True'
	)
	db['%s' % table].insert(
        name="Map Service Catalogue",
	function="map_service_catalogue",
	priority=2,
	enabled='True'
	)

# GIS Markers (Icons)
resource='marker'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('height','integer'), # In Pixels, for display purposes
                SQLField('width','integer'),
                SQLField('image','upload'))
db['%s' % table].exposes=['name','height','width','image']
db['%s' % table].displays=['name','height','width','image']
db['%s' % table].represent=lambda table:shn_list_item(table,resource='marker',action='display')
db['%s' % table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_marker.name')]
db['%s' % table].name.comment=SPAN("*",_class="req")
# Populate table with Default options
if not len(db().select(db['%s' % table].ALL)):
    # We want to start at ID 1
    db['%s' % table].truncate() 
    db['%s' % table].insert(
        name="marker",
        height=34,
        width=20,
        # Can't do sub-folders :/
        # need to script a bulk copy & rename
        image="gis_marker.image.default.png"
    )
    # We should now read in the list of default markers from the filesystem & populate the DB 1 by 1
    # - we need to get the size automatically
title_create=T('Add Marker')
title_display=T('Marker Details')
title_list=T('List Markers')
title_update=T('Edit Marker')
subtitle_create=T('Add New Marker')
subtitle_list=T('Markers')
label_list_button=T('List Markers')
label_create_button=T('Add Marker')
msg_record_created=T('Marker added')
msg_record_modified=T('Marker updated')
msg_record_deleted=T('Marker deleted')
msg_list_empty=T('No Markers currently available')
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
            
# GIS Projections
resource='projection'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('epsg','integer'),
                SQLField('maxExtent'),
                SQLField('maxResolution','double'),
                SQLField('units'))
db['%s' % table].exposes=['name','epsg','maxExtent','maxResolution','units']
db['%s' % table].displays=['name','epsg','maxExtent','maxResolution','units']
db['%s' % table].represent=lambda table:shn_list_item(table,resource='projection',action='display',extra='table.epsg')
db['%s' % table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_projection.name')]
db['%s' % table].name.comment=SPAN("*",_class="req")
db['%s' % table].epsg.requires=IS_NOT_EMPTY()
db['%s' % table].epsg.label="EPSG"
db['%s' % table].epsg.comment=SPAN("*",_class="req")
db['%s' % table].maxExtent.requires=IS_NOT_EMPTY()
db['%s' % table].maxExtent.label="maxExtent"
db['%s' % table].maxExtent.comment=SPAN("*",_class="req")
db['%s' % table].maxResolution.requires=IS_NOT_EMPTY()
db['%s' % table].maxResolution.label="maxResolution"
db['%s' % table].maxResolution.comment=SPAN("*",_class="req")
db['%s' % table].units.requires=IS_IN_SET(['m','degrees'])
# Populate table with Default options
if not len(db().select(db['%s' % table].ALL)): 
   # We want to start at ID 1
   db['%s' % table].truncate() 
   db['%s' % table].insert(
        name="Spherical Mercator",
        epsg=900913,
        maxExtent="-20037508, -20037508, 20037508, 20037508.34",
        maxResolution=156543.0339,
        units="m"
    )
   db['%s' % table].insert(
        name="WGS84",
        epsg=4326,
        maxExtent="-180,-90,180,90",
        maxResolution=1.40625,
        units="degrees"
    )
title_create=T('Add Projection')
title_display=T('Projection Details')
title_list=T('List Projections')
title_update=T('Edit Projection')
subtitle_create=T('Add New Projection')
subtitle_list=T('Projections')
label_list_button=T('List Projections')
label_create_button=T('Add Projection')
msg_record_created=T('Projection added')
msg_record_modified=T('Projection updated')
msg_record_deleted=T('Projection deleted')
msg_list_empty=T('No Projections currently defined')
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)

# GIS Config
# id=1 = Default settings
# ToDo Extend for per-user Profiles
resource='config'
table=module+'_'+resource
db.define_table(table,
				SQLField('lat'),
				SQLField('lon'),
				SQLField('zoom','integer'),
				SQLField('projection',db.gis_projection),   # NB This can then have issues with sync unless going via CSV
				SQLField('marker',db.gis_marker),           # NB This can then have issues with sync unless going via CSV
				SQLField('map_height'),
				SQLField('map_width'))
db['%s' % table].lat.requires=IS_LAT()
db['%s' % table].lon.requires=IS_LON()
db['%s' % table].zoom.requires=IS_INT_IN_RANGE(0,19)
db['%s' % table].projection.requires=IS_IN_DB(db,'gis_projection.id','gis_projection.name')
db['%s' % table].projection.display=lambda id: db(db.gis_projection.id==id).select()[0].name
db['%s' % table].marker.requires=IS_IN_DB(db,'gis_marker.id','gis_marker.name')
db['%s' % table].marker.display=lambda id: DIV(A(IMG(_src=URL(r=request,f='download',args=[db(db.gis_marker.id==id).select()[0].image]),_height=40),_class='zoom',_href='#zoom-gis_config-marker-%s' % id),DIV(IMG(_src=URL(r=request,f='download',args=[db(db.gis_marker.id==id).select()[0].image]),_width=600),_id='zoom-gis_config-marker-%s' % id,_class='hidden'))
db['%s' % table].map_height.requires=[IS_NOT_EMPTY(),IS_ALPHANUMERIC()]
db['%s' % table].map_width.requires=[IS_NOT_EMPTY(),IS_ALPHANUMERIC()]
# Populate table with Default options
if not len(db().select(db['%s' % table].ALL)): 
   # We want to start at ID 1
   db['%s' % table].truncate() 
   db['%s' % table].insert(
        lat="6",
        lon="79.4",
        zoom=7,
        projection=1,
        marker=1,
        map_height=600,
        map_width=800
    )
title_create=T('Add Config')
title_display=T('Config Details')
title_list=T('List Configs')
title_update=T('Edit Config')
subtitle_create=T('Add New Config')
subtitle_list=T('Configs')
label_list_button=T('List Configs')
label_create_button=T('Add Config')
msg_record_created=T('Config added')
msg_record_modified=T('Config updated')
msg_record_deleted=T('Config deleted')
msg_list_empty=T('No Configs currently defined')
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
            
# GIS Features
resource='feature_class'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('marker',db.gis_marker))   # NB This can then have issues with sync unless going via CSV
db['%s' % table].exposes=['name','marker']
db['%s' % table].displays=['name','marker']
db['%s' % table].represent=lambda table:shn_list_item(table,resource='feature_class',action='display')
db['%s' % table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_feature_class.name')]
db['%s' % table].name.comment=SPAN("*",_class="req")
db['%s' % table].marker.requires=IS_IN_DB(db,'gis_marker.id','gis_marker.name')
db['%s' % table].marker.display=lambda uuid: DIV(A(IMG(_src=URL(r=request,f='download',args=[db(db.gis_marker.id==id).select()[0].image]),_height=40),_class='zoom',_href='#zoom-gis_feature_class-marker-%s' % uuid),DIV(IMG(_src=URL(r=request,f='download',args=[db(db.gis_marker.id==id).select()[0].image]),_width=600),_id='zoom-gis_feature_class-marker-%s' % uuid,_class='hidden'))
title_create=T('Add Feature Class')
title_display=T('Feature Class Details')
title_list=T('List Feature Classes')
title_update=T('Edit Feature Class')
subtitle_create=T('Add New Feature Class')
subtitle_list=T('Feature Classes')
label_list_button=T('List Feature Classes')
label_create_button=T('Add Feature Class')
msg_record_created=T('Feature Class added')
msg_record_modified=T('Feature Class updated')
msg_record_deleted=T('Feature Class deleted')
msg_list_empty=T('No Feature Classes currently defined')
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)

resource='feature_metadata'
table=module+'_'+resource
db.define_table(table,
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
db.gis_feature_metadata.contact.requires=IS_NULL_OR(IS_IN_DB(db,'pr_person.uuid','pr_person.full_name'))
db.gis_feature_metadata.contact.display=lambda uuid: (uuid and [db(db.pr_person.uuid==uuid).select()[0].full_name] or ["None"])[0]
db.gis_feature_metadata.url.requires=IS_URL()
title_create=T('Add Feature Metadata')
title_display=T('Feature Metadata Details')
title_list=T('List Feature Metadata')
title_update=T('Edit Feature Metadata')
subtitle_create=T('Add New Feature Metadata')
subtitle_list=T('Feature Metadata')
label_list_button=T('List Feature Metadata')
label_create_button=T('Add Feature Metadata')
msg_record_created=T('Feature Metadata added')
msg_record_modified=T('Feature Metadata updated')
msg_record_deleted=T('Feature Metadata deleted')
msg_list_empty=T('No Feature Metadata currently defined')
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
            
resource='feature'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('feature_class',length=64),
                SQLField('metadata',length=64),
                SQLField('type',default='point'),
                SQLField('lat'),
                SQLField('lon'))
db['%s' % table].exposes=['name','feature_class','metadata','type','lat','lon']
db['%s' % table].displays=['name','feature_class','metadata','type','lat','lon']
# Define in Controller as want diff functions to have diff representations & we cannot redefine later once defined at top-level
#db['%s' % table].represent=lambda table:shn_list_item(table,resource=resource,action='display')
db['%s' % table].name.requires=IS_NOT_EMPTY()
db['%s' % table].name.comment=SPAN("*",_class="req")
db['%s' % table].feature_class.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature_class.uuid','gis_feature_class.name'))
db['%s' % table].feature_class.display=lambda uuid: (uuid and [db(db.gis_feature_class.uuid==uuid).select()[0].name] or ["None"])[0]
db['%s' % table].metadata.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature_metadata.uuid'))
db['%s' % table].metadata.display=lambda uuid: (uuid and [db(db.gis_feature_metadata.uuid==uuid).select()[0].description] or ["None"])[0]
db['%s' % table].type.requires=IS_IN_SET(['point','line','polygon'])
db['%s' % table].lat.requires=IS_LAT()
db['%s' % table].lat.label=T("Latitude")
db['%s' % table].lat.comment=SPAN("*",_class="req")
db['%s' % table].lon.requires=IS_LON()
db['%s' % table].lon.label=T("Longitude")
db['%s' % table].lon.comment=SPAN("*",_class="req")
title_create=T('Add Feature')
title_display=T('Feature Details')
title_list=T('List Features')
title_update=T('Edit Feature')
subtitle_create=T('Add New Feature')
subtitle_list=T('Features')
label_list_button=T('List Features')
label_create_button=T('Add Feature')
msg_record_created=T('Feature added')
msg_record_modified=T('Feature updated')
msg_record_deleted=T('Feature deleted')
msg_list_empty=T('No Features currently defined')
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
            
# Feature Groups
# Used to select a set of Features for either Display or Export
resource='feature_group'
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('features','text'), # List of features (to be replaced by many-to-many table)
                SQLField('author',db.t2_person))
db['%s' % table].exposes=['name','description','features']
db['%s' % table].displays=['name','description','author','features']
db['%s' % table].represent=lambda table:shn_list_item(table,resource='feature_group',action='display')
db['%s' % table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_feature_group.name')]
db['%s' % table].name.comment=SPAN("*",_class="req")
db['%s' % table].features.comment=A(SPAN("[Help]"),_class="popupLink",_id="tooltip",_title=T("Multi-Select|Click Features to select, Click again to Remove. Dark Green is selected."))
db['%s' % table].author.requires=IS_IN_DB(db,'t2_person.id','t2_person.name')
title_create=T('Add Feature Group')
title_display=T('Feature Group Details')
title_list=T('List Feature Groups')
title_update=T('Edit Feature Group')
subtitle_create=T('Add New Feature Group')
subtitle_list=T('Feature Groups')
label_list_button=T('List Feature Groups')
label_create_button=T('Add Feature Group')
msg_record_created=T('Feature Group added')
msg_record_modified=T('Feature Group updated')
msg_record_deleted=T('Feature Group deleted')
msg_list_empty=T('No Feature Groups currently defined')
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)

            
# Many-to-Many table
# are we using this or a tag-like pseudo M2M?
db.define_table('gis_feature_group_to_feature',
                SQLField('modified_on','datetime',default=now),
                SQLField('feature_group',length=64),
                SQLField('feature',length=64))
db.gis_feature_group_to_feature.feature_group.requires=IS_IN_DB(db,'gis_feature_group.uuid','gis_feature_group.name')
db.gis_feature_group_to_feature.feature.requires=IS_IN_DB(db,'gis_feature.uuid','gis_feature.name')
                

# GIS Keys - needed for commercial mapping services
resource='apikey' # Can't use 'key' as this has other meanings for dicts!
table=module+'_'+resource
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('service'),
                SQLField('apikey'),
				SQLField('description',length=256))
db['%s' % table].displays=['service','apikey','description']
db['%s' % table].represent=lambda table:shn_list_item(table,resource='apikey',action='display',display='table.service',extra='table.apikey')
# We want a THIS_NOT_IN_DB here:
db['%s' % table].service.requires=IS_IN_SET(['google','multimap','yahoo']) 
#db['%s' % table].apikey.requires=THIS_NOT_IN_DB(db(db['%s' % table].service==request.vars.service),'gis_apikey.service',request.vars.service,'service already in use')
db['%s' % table].apikey.requires=IS_NOT_EMPTY()
db['%s' % table].apikey.label=T("Key")
# Populate table with Default options
if not len(db().select(db['%s' % table].ALL)): 
   db['%s' % table].insert(
        service="google",
        apikey="ABQIAAAAb-bE-ljr4-6Hsb4x92lWhRT2yXp_ZAY8_ufC3CFXhHIE1NvwkxQTjccCsxIjr0poUEEARUZJgolNfw",
        description="localhost"
    )
   db['%s' % table].insert(
        service="yahoo",
        apikey="euzuro-openlayers",
        description="To be replaced for Production use"
    )
   db['%s' % table].insert(
        service="multimap",
        apikey="metacarta_04",
        description="trial"
    )
title_create=T('Add Key')
title_display=T('Key Details')
title_list=T('List Keys')
title_update=T('Edit Key')
subtitle_create=T('Add New Key')
subtitle_list=T('Keys')
label_list_button=T('List Keys')
label_create_button=T('Add Key')
msg_record_created=T('Key added')
msg_record_modified=T('Key updated')
msg_record_deleted=T('Key deleted')
msg_list_empty=T('No Keys currently defined')
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
            
# GIS Layers
#gis_layer_types=['features','georss','kml','gpx','shapefile','scan','google','openstreetmap','virtualearth','wms','yahoo']
gis_layer_types=['openstreetmap','google','yahoo','virtualearth']
gis_layer_openstreetmap_subtypes=['Mapnik','Osmarender','Aerial']
gis_layer_google_subtypes=['Satellite','Maps','Hybrid','Terrain']
gis_layer_yahoo_subtypes=['Satellite','Maps','Hybrid']
gis_layer_virtualearth_subtypes=['Satellite','Maps','Hybrid']
# Base table from which the rest inherit
gis_layer=SQLTable(db,'gis_layer',
            db.Field('modified_on','datetime',default=now),
            #db.Field('uuid',length=64,default=uuid.uuid4()),   # Layers like OpenStreetMap, Google, etc shouldn't sync
            db.Field('name'),
            db.Field('description',length=256),
            #db.Field('priority','integer'),    # System default priority is set in ol_layers_all.js. User priorities are set in WMC.
            db.Field('enabled','boolean',default=True))
gis_layer.name.requires=IS_NOT_EMPTY()
for layertype in gis_layer_types:
    resource='layer_'+layertype
    table=module+'_'+resource
    title_create=T('Add Layer')
    title_display=T('Layer Details')
    title_list=T('List Layers')
    title_update=T('Edit Layer')
    subtitle_create=T('Add New Layer')
    subtitle_list=T('Layers')
    label_list_button=T('List Layers')
    label_create_button=T('Add Layer')
    msg_record_created=T('Layer added')
    msg_record_modified=T('Layer updated')
    msg_record_deleted=T('Layer deleted')
    msg_list_empty=T('No Layers currently defined')
    # Create Type-specific Layer tables
    if layertype=="openstreetmap":
        t=SQLTable(db,table,
            db.Field('subtype'),
            gis_layer)
        t.subtype.requires=IS_IN_SET(gis_layer_openstreetmap_subtypes)
        db.define_table(table,t)
        db['%s' % table].represent=lambda table:shn_list_item(table,resource='layer_openstreetmap',action='display',extra=str(table.enabled))
        if not len(db().select(db['%s' % table].ALL)):
            # Populate table
            for subtype in gis_layer_openstreetmap_subtypes:
                db['%s' % table].insert(
                        name='OSM '+subtype,
                        subtype=subtype
                    )
        # Customise CRUD strings if-desired
        label_list_button=T('List OpenStreetMap Layers')
        msg_list_empty=T('No OpenStreetMap Layers currently defined')
        exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
    if layertype=="google":
        t=SQLTable(db,table,
            db.Field('subtype'),
            gis_layer)
        t.subtype.requires=IS_IN_SET(gis_layer_google_subtypes)
        db.define_table(table,t)
        db['%s' % table].represent=lambda table:shn_list_item(table,resource='layer_google',action='display',extra=str(table.enabled))
        if not len(db().select(db['%s' % table].ALL)):
            # Populate table
            for subtype in gis_layer_google_subtypes:
                db['%s' % table].insert(
                        name='Google '+subtype,
                        subtype=subtype,
                        enabled=False
                    )
        # Customise CRUD strings if-desired
        label_list_button=T('List Google Layers')
        msg_list_empty=T('No Google Layers currently defined')
        exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
    if layertype=="yahoo":
        t=SQLTable(db,table,
            db.Field('subtype'),
            gis_layer)
        t.subtype.requires=IS_IN_SET(gis_layer_yahoo_subtypes)
        db.define_table(table,t)
        db['%s' % table].represent=lambda table:shn_list_item(table,resource='layer_yahoo',action='display',extra=str(table.enabled))
        if not len(db().select(db['%s' % table].ALL)):
            # Populate table
            for subtype in gis_layer_yahoo_subtypes:
                db['%s' % table].insert(
                        name='Yahoo '+subtype,
                        subtype=subtype,
                        enabled=False
                    )
        # Customise CRUD strings if-desired
        label_list_button=T('List Yahoo Layers')
        msg_list_empty=T('No Yahoo Layers currently defined')
        exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
    if layertype=="virtualearth":
        t=SQLTable(db,table,
            db.Field('subtype'),
            gis_layer)
        t.subtype.requires=IS_IN_SET(gis_layer_virtualearth_subtypes)
        db.define_table(table,t)
        db['%s' % table].represent=lambda table:shn_list_item(table,resource='layer_virtualearth',action='display',extra=str(table.enabled))
        if not len(db().select(db['%s' % table].ALL)):
            # Populate table
            for subtype in gis_layer_virtualearth_subtypes:
                db['%s' % table].insert(
                        name='VE '+subtype,
                        subtype=subtype,
                        enabled=False
                    )
        # Customise CRUD strings if-desired
        label_list_button=T('List Virtual Earth Layers')
        msg_list_empty=T('No Virtual Earth Layers currently defined')
        exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)

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

