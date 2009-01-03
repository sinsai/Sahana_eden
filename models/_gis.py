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
resource='projection'
table=module+'_'+resource
single=resource.capitalize()
plural=single+'s'
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('epsg'),
                SQLField('maxExtent',length=256),
                SQLField('maxResolution'),
                SQLField('units'))
db['%s' % table].exposes=['name','epsg','maxExtent','maxResolution','units']
db['%s' % table].displays=['name','epsg','maxExtent','maxResolution','units']
db['%s' % table].represent=lambda table:shn_list_item(table,resource='projection',action='display',extra='table.epsg')
db['%s' % table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_projection.name')]
db['%s' % table].name.comment=SPAN("*",_class="req")
db['%s' % table].epsg.requires=[IS_NOT_EMPTY(),IS_ALPHANUMERIC()]
db['%s' % table].epsg.label="EPSG"
db['%s' % table].epsg.comment=SPAN("*",_class="req")
db['%s' % table].maxExtent.requires=IS_NOT_EMPTY()
db['%s' % table].maxExtent.label="maxExtent"
db['%s' % table].maxExtent.comment=SPAN("*",_class="req")
db['%s' % table].maxResolution.requires=IS_NOT_EMPTY()
db['%s' % table].maxResolution.label="maxResolution"
db['%s' % table].maxResolution.comment=SPAN("*",_class="req")
db['%s' % table].units.requires=IS_IN_SET(['m','degrees'])
title_create=T('Add %s' % single)
title_display=T('%s Details' % single)
title_list=T('List %s' % plural)
title_update=T('Edit %s' % single)
subtitle_create=T('Add New %s' % single)
subtitle_list=T('%s' % plural)
label_list_button=T('List %s' % plural)
label_create_button=T('Add %s' % single)
msg_record_created=T('%s added' % single)
msg_record_modified=T('%s updated' % single)
msg_record_deleted=T('%s deleted' % single)
msg_list_empty=T('No %s currently defined' % plural)
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)

# GIS Config
# id=1 = Default settings
# ToDo Extend for per-user Profiles
resource='config'
table=module+'_'+resource
single=resource.capitalize()
plural=single+'s'
db.define_table(table,
				SQLField('lat'),
				SQLField('lon'),
				SQLField('zoom'),
				SQLField('projection',length=64),
				SQLField('marker',length=64,default='e2848160-cad4-4b8e-91cf-d1b4828bf805'),
				SQLField('map_height'),
				SQLField('map_width'))
db['%s' % table].lat.requires=IS_LAT()
db['%s' % table].lon.requires=IS_LON()
db['%s' % table].zoom.requires=[IS_NOT_EMPTY(),IS_ALPHANUMERIC()]
db['%s' % table].projection.requires=IS_IN_DB(db,'gis_projection.uuid','gis_projection.name')
db['%s' % table].projection.display=lambda uuid: db(db.gis_projection.uuid==uuid).select()[0].name
db['%s' % table].marker.requires=IS_IN_DB(db,'gis_marker.uuid','gis_marker.name')
db['%s' % table].marker.display=lambda uuid: DIV(A(IMG(_src=URL(r=request,f='download',args=[db(db.gis_marker.uuid==uuid).select()[0].image]),_height=40),_class='zoom',_href='#zoom-gis_config-marker-%s' % uuid),DIV(IMG(_src=URL(r=request,f='download',args=[db(db.gis_marker.uuid==uuid).select()[0].image]),_width=600),_id='zoom-gis_config-marker-%s' % uuid,_class='hidden'))
db['%s' % table].map_height.requires=[IS_NOT_EMPTY(),IS_ALPHANUMERIC()]
db['%s' % table].map_width.requires=[IS_NOT_EMPTY(),IS_ALPHANUMERIC()]
title_create=T('Add %s' % single)
title_display=T('%s Details' % single)
title_list=T('List %s' % plural)
title_update=T('Edit %s' % single)
subtitle_create=T('Add New %s' % single)
subtitle_list=T('%s' % plural)
label_list_button=T('List %s' % plural)
label_create_button=T('Add %s' % single)
msg_record_created=T('%s added' % single)
msg_record_modified=T('%s updated' % single)
msg_record_deleted=T('%s deleted' % single)
msg_list_empty=T('No %s currently defined' % plural)
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
            
# GIS Markers (Icons)
resource='marker'
table=module+'_'+resource
single=resource.capitalize()
plural=single+'s'
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
title_create=T('Add %s' % single)
title_display=T('%s Details' % single)
title_list=T('List %s' % plural)
title_update=T('Edit %s' % single)
subtitle_create=T('Add New %s' % single)
subtitle_list=T('%s' % plural)
label_list_button=T('List %s' % plural)
label_create_button=T('Add %s' % single)
msg_record_created=T('%s added' % single)
msg_record_modified=T('%s updated' % single)
msg_record_deleted=T('%s deleted' % single)
msg_list_empty=T('No %s currently available' % plural)
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
            
# GIS Features
resource='feature_class'
table=module+'_'+resource
# NB Manually fixed!
single='Feature Class'
plural='Feature Classes'
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('marker',length=64,default='e2848160-cad4-4b8e-91cf-d1b4828bf805'))
db['%s' % table].exposes=['name','marker']
db['%s' % table].displays=['name','marker']
db['%s' % table].represent=lambda table:shn_list_item(table,resource='feature_class',action='display')
db['%s' % table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_feature_class.name')]
db['%s' % table].name.comment=SPAN("*",_class="req")
db['%s' % table].marker.requires=IS_IN_DB(db,'gis_marker.uuid','gis_marker.name')
db['%s' % table].marker.display=lambda uuid: DIV(A(IMG(_src=URL(r=request,f='download',args=[db(db.gis_marker.uuid==uuid).select()[0].image]),_height=40),_class='zoom',_href='#zoom-gis_feature_class-marker-%s' % uuid),DIV(IMG(_src=URL(r=request,f='download',args=[db(db.gis_marker.uuid==uuid).select()[0].image]),_width=600),_id='zoom-gis_feature_class-marker-%s' % uuid,_class='hidden'))
title_create=T('Add %s' % single)
title_display=T('%s Details' % single)
title_list=T('List %s' % plural)
title_update=T('Edit %s' % single)
subtitle_create=T('Add New %s' % single)
subtitle_list=T('%s' % plural)
label_list_button=T('List %s' % plural)
label_create_button=T('Add %s' % single)
msg_record_created=T('%s added' % single)
msg_record_modified=T('%s updated' % single)
msg_record_deleted=T('%s deleted' % single)
msg_list_empty=T('No %s currently defined' % plural)
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)

resource='feature_metadata'
table=module+'_'+resource
# NB Manually fixed!
single='Feature Metadata'
plural='Feature Metadata'
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
title_create=T('Add %s' % single)
title_display=T('%s Details' % single)
title_list=T('List %s' % plural)
title_update=T('Edit %s' % single)
subtitle_create=T('Add New %s' % single)
subtitle_list=T('%s' % plural)
label_list_button=T('List %s' % plural)
label_create_button=T('Add %s' % single)
msg_record_created=T('%s added' % single)
msg_record_modified=T('%s updated' % single)
msg_record_deleted=T('%s deleted' % single)
msg_list_empty=T('No %s currently defined' % plural)
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
            
resource='feature'
table=module+'_'+resource
single=resource.capitalize()
plural=single+'s'
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
title_create=T('Add %s' % single)
title_display=T('%s Details' % single)
title_list=T('List %s' % plural)
title_update=T('Edit %s' % single)
subtitle_create=T('Add New %s' % single)
subtitle_list=T('%s' % plural)
label_list_button=T('List %s' % plural)
label_create_button=T('Add %s' % single)
msg_record_created=T('%s added' % single)
msg_record_modified=T('%s updated' % single)
msg_record_deleted=T('%s deleted' % single)
msg_list_empty=T('No %s currently defined' % plural)
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
            
# Feature Groups
# Used to select a set of Features for either Display or Export
resource='feature_group'
table=module+'_'+resource
# NB Manually fixed!
single='Feature Group'
plural='Feature Groups'
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
title_create=T('Add %s' % single)
title_display=T('%s Details' % single)
title_list=T('List %s' % plural)
title_update=T('Edit %s' % single)
subtitle_create=T('Add New %s' % single)
subtitle_list=T('%s' % plural)
label_list_button=T('List %s' % plural)
label_create_button=T('Add %s' % single)
msg_record_created=T('%s added' % single)
msg_record_modified=T('%s updated' % single)
msg_record_deleted=T('%s deleted' % single)
msg_list_empty=T('No %s currently defined' % plural)
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)

            
# Many-to-Many table
db.define_table('gis_feature_group_to_feature',
                SQLField('modified_on','datetime',default=now),
                SQLField('feature_group',length=64),
                SQLField('feature',length=64))
db.gis_feature_group_to_feature.feature_group.requires=IS_IN_DB(db,'gis_feature_group.uuid','gis_feature_group.name')
db.gis_feature_group_to_feature.feature.requires=IS_IN_DB(db,'gis_feature.uuid','gis_feature.name')
                

# GIS Keys - needed for commercial mapping services
resource='apikey' # Can't use 'key' as this has other meanings for dicts!
table=module+'_'+resource
single='Key'
plural=single+'s'
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
title_create=T('Add %s' % single)
title_display=T('%s Details' % single)
title_list=T('List %s' % plural)
title_update=T('Edit %s' % single)
subtitle_create=T('Add New %s' % single)
subtitle_list=T('%s' % plural)
label_list_button=T('List %s' % plural)
label_create_button=T('Add %s' % single)
msg_record_created=T('%s added' % single)
msg_record_modified=T('%s updated' % single)
msg_record_deleted=T('%s deleted' % single)
msg_list_empty=T('No %s currently defined' % plural)
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)

            
# GIS Layers
resource='layer'
table=module+'_'+resource
single=resource.capitalize()
plural=single+'s'
#gis_layer_types=['features','georss','kml','gpx','shapefile','scan','google','openstreetmap','virtualearth','wms','yahoo']
gis_layer_types=['features','openstreetmap','google','yahoo','virtualearth']
db.define_table(table,
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('type'),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default=True))
#eval(extra) doesn't play nicely when extra=True/False
db['%s' % table].represent=lambda table:shn_list_item(table,resource='layer',action='display',extra=str(table.enabled))
#db['%s' % table].represent=lambda table:shn_list_item(table,resource='layer',action='display')
db['%s' % table].name.requires=IS_NOT_EMPTY()
db['%s' % table].type.requires=IS_IN_SET(gis_layer_types)
db['%s' % table].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_layer.priority')]
title_create=T('Add %s' % single)
title_display=T('%s Details' % single)
title_list=T('List %s' % plural)
title_update=T('Edit %s' % single)
subtitle_create=T('Add New %s' % single)
subtitle_list=T('%s' % plural)
label_list_button=T('List %s' % plural)
label_create_button=T('Add %s' % single)
msg_record_created=T('%s added' % single)
msg_record_modified=T('%s updated' % single)
msg_record_deleted=T('%s deleted' % single)
msg_list_empty=T('No %s currently defined' % plural)
exec('crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)
            
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

