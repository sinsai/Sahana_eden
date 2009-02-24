module='gis'
# Current Module (for sidebar title)
module_name=db(db.s3_module.name==module).select()[0].name_nice
# List Modules (from which to build Menu of Modules)
modules=db(db.s3_module.enabled=='Yes').select(db.s3_module.ALL,orderby=db.s3_module.priority)
# List Options (from which to build Menu for this Module)
options=db(db['%s_menu_option' % module].enabled=='Yes').select(db['%s_menu_option' % module].ALL,orderby=db['%s_menu_option' % module].priority)

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name,modules=modules,options=options)
def open_option():
    "Select Option from Module Menu"
    id=request.vars.id
    options=db(db['%s_menu_option' % module].id==id).select()
    if not len(options):
        redirect(URL(r=request,f='index'))
    option=options[0].function
    redirect(URL(r=request,f=option))
def apikey():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'apikey',deletable=False,listadd=False)
def config():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'config')
def feature():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'feature',onvalidation=lambda form: wkt_centroid(form))
def feature_class():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'feature_class')
def feature_group():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'feature_group')
def feature_metadata():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'feature_metadata')
def location():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'location')
def marker():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'marker')
def projection():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'projection',deletable=False,extra='epsg')
def layer_openstreetmap():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'layer_openstreetmap',deletable=False)
def layer_google():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'layer_google',deletable=False)
def layer_yahoo():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'layer_yahoo',deletable=False)
def layer_virtualearth():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'layer_virtualearth',deletable=False)

# Module-specific functions

@auth.requires_membership(1)
def defaults():
    """Defaults are a special case of Configs - the 1st entry.
    Don't want to be able to delete these!
    """
    title=T("GIS Defaults")
    form=t2.update(db.gis_config,deletable=False) # NB deletable=False
    return dict(title=title,module_name=module_name,modules=modules,options=options,form=form)

def shn_latlon_to_wkt(lat,lon):
    """Convert a LatLon to a WKT string
    >>> shn_latlon_to_wkt(6,80)
    'POINT(80 6)'
    """
    WKT='POINT(%d %d)' %(lon,lat)
    return WKT

# Features
# - experimental!
def feature_create_map():
    "Show a map to draw the feature"
    title=T("Add GIS Feature")
    form=crud.create('gis_feature',onvalidation=lambda form: wkt_centroid(form))
    _projection=db(db.gis_config.id==1).select()[0].projection
    projection=db(db.gis_projection.id==_projection).select()[0].epsg

    #
    # Layers
    #
    
    # OpenStreetMap
    openstreetmap=Storage()
    layers_openstreetmap=db(db.gis_layer_openstreetmap.enabled==True).select(db.gis_layer_openstreetmap.ALL)
    for layer in layers_openstreetmap:
        for subtype in gis_layer_openstreetmap_subtypes:
            if layer.subtype==subtype:
                openstreetmap['%s' % subtype]=layer.name
    
    # Google
    google=Storage()
    # Check for Google Key
    try:
        google.key=db(db.gis_apikey.name=='google').select(db.gis_apikey.apikey)[0].apikey
        layers_google=db(db.gis_layer_google.enabled==True).select(db.gis_layer_google.ALL)
        for layer in layers_google:
            for subtype in gis_layer_google_subtypes:
                if layer.subtype==subtype:
                    google['%s' % subtype]=layer.name
                    google.enabled=1
    except:
        # Redirect to Key entry screen
        session.warning=T('Please enter a Google Key if you wish to use Google Layers')
        redirect(URL(r=request,f=apikey))
            
    # Yahoo
    yahoo=Storage()
    # Check for Yahoo Key
    try:
        yahoo.key=db(db.gis_apikey.name=='yahoo').select(db.gis_apikey.apikey)[0].apikey
        layers_yahoo=db(db.gis_layer_yahoo.enabled==True).select(db.gis_layer_yahoo.ALL)
        for layer in layers_yahoo:
            for subtype in gis_layer_yahoo_subtypes:
                if layer.subtype==subtype:
                    yahoo['%s' % subtype]=layer.name
                    yahoo.enabled=1
    except:
        # Redirect to Key entry screen
        session.warning=T('Please enter a Yahoo Key if you wish to use Yahoo Layers')
        redirect(URL(r=request,f=apikey))
        
    # Virtual Earth
    virtualearth=Storage()
    layers_virtualearth=db(db.gis_layer_virtualearth.enabled==True).select(db.gis_layer_virtualearth.ALL)
    for layer in layers_virtualearth:
        for subtype in gis_layer_virtualearth_subtypes:
            if layer.subtype==subtype:
                virtualearth['%s' % subtype]=layer.name

    return dict(title=title,module_name=module_name,modules=modules,options=options,form=form,projection=projection,openstreetmap=openstreetmap,google=google,yahoo=yahoo,virtualearth=virtualearth)
    
# Feature Groups
# TODO: https://trac.sahanapy.org/wiki/BluePrintMany2Many
@auth.requires_login()
def feature_groups():
    """Many to Many experiment
    currently using t2.tag_widget()
    """
    title=T("GIS Feature Groups")
    subtitle=T("Add New Feature Group")
    list=t2.itemize(db.gis_feature_group)
    if list=="No data":
        list="No Feature Groups currently defined."
    # Get all available features
    _features=db(db.gis_feature.id > 0).select()
    # Put them into a list field (should be a dict to store uuid too, but t2.tag_widget doesn't support it)
    items=[]
    #items={}
    for i in range(len(_features)):
        items.append(_features[i].name)
        #items[_features[i].name]=_features[i].uuid
    db.gis_feature_group.features.widget=lambda s,v: t2.tag_widget(s,v,items)
    #form=t2.create(db.gis_feature_group)
    form=crud.create(db.gis_feature_group)
    response.view='list_create.html'
    return dict(title=title,subtitle=subtitle,module_name=module_name,modules=modules,options=options,list=list,form=form)
	
@auth.requires_login()
def update_feature_group():
    """Many to Many experiment
    currently using t2.tag_widget()
    """
    # Get all available features
    _features=db(db.gis_feature.id > 0).select()
    items=[]
    for i in range(len(_features)):
        items.append(_features[i].name)
    db.gis_feature_group.features.widget=lambda s,v: t2.tag_widget(s,v,items)
    #form=SQLFORM(db.gis_feature_group)
    form=t2.update(db.gis_feature_group)
    db.gis_feature.represent=lambda table:shn_list_item(table,action='display')
    search=t2.search(db.gis_feature)
    return dict(module_name=module_name,modules=modules,options=options,form=form,search=search)

def map_service_catalogue():
    """Map Service Catalogue.
    Allows selection of which Layers are active."""

    # Create a manual table to aggregate all layer types
    # Could look to rewrite using Helpers: http://groups.google.com/group/web2py/browse_thread/thread/ac045f3b1d3846d9
    # We should also move to the View for better MVC!
    items='<table><tr><td></td><td><b>Enabled?</b></td></tr>'
    for type in gis_layer_types:
        resource='layer_'+type
        table=db['%s_%s' % (module,resource)]
        for layer in db(table.id>0).select():
            items+='<tr><td><a href="'
            items+=URL(r=request,f=resource)
            items+='/display/'
            items+=str(layer.id)
            items+='">'
            items+=layer.name
            items+='</a></td><td>'
            items+=str(layer.enabled)
            items+='</td></tr>'
    items+='</table>'
        
    title=T('Map Service Catalogue')
    subtitle=T('List Layers')
    return dict(module_name=module_name,modules=modules,options=options,title=title,subtitle=subtitle,item=XML(items))

def map_viewing_client():
    """Map Viewing Client.
    Main user UI for viewing the Maps."""
    
    title=T('Map Viewing Client')
    response.title=title

    # Start building the Return with the Framework
    output=dict(title=title,module_name=module_name,modules=modules,options=options)
    
    # Config
    width=db(db.gis_config.id==1).select()[0].map_width
    height=db(db.gis_config.id==1).select()[0].map_height
    _projection=db(db.gis_config.id==1).select()[0].projection
    projection=db(db.gis_projection.id==_projection).select()[0].epsg
    lat=db(db.gis_config.id==1).select()[0].lat
    lon=db(db.gis_config.id==1).select()[0].lon
    zoom=db(db.gis_config.id==1).select()[0].zoom
    units=db(db.gis_projection.epsg==projection).select()[0].units
    maxResolution=db(db.gis_projection.epsg==projection).select()[0].maxResolution
    maxExtent=db(db.gis_projection.epsg==projection).select()[0].maxExtent
    features_marker = db(db.gis_config.id==1).select()[0].marker
    
    # Add the Config to the Return
    output.update(dict(width=width,height=height,projection=projection,lat=lat,lon=lon,zoom=zoom,units=units,maxResolution=maxResolution,maxExtent=maxExtent,features_marker=features_marker))
    
    #
    # Layers
    #
    
    # OpenStreetMap
    openstreetmap=Storage()
    layers_openstreetmap=db(db.gis_layer_openstreetmap.enabled==True).select(db.gis_layer_openstreetmap.ALL)
    for layer in layers_openstreetmap:
        for subtype in gis_layer_openstreetmap_subtypes:
            if layer.subtype==subtype:
                openstreetmap['%s' % subtype]=layer.name
    
    # Google
    google=Storage()
    # Check for Google Key
    try:
        google.key=db(db.gis_apikey.name=='google').select(db.gis_apikey.apikey)[0].apikey
        layers_google=db(db.gis_layer_google.enabled==True).select(db.gis_layer_google.ALL)
        for layer in layers_google:
            for subtype in gis_layer_google_subtypes:
                if layer.subtype==subtype:
                    google['%s' % subtype]=layer.name
                    google.enabled=1
    except:
        # Redirect to Key entry screen
        session.warning=T('Please enter a Google Key if you wish to use Google Layers')
        redirect(URL(r=request,f=apikey))
            
    # Yahoo
    yahoo=Storage()
    # Check for Yahoo Key
    try:
        yahoo.key=db(db.gis_apikey.name=='yahoo').select(db.gis_apikey.apikey)[0].apikey
        layers_yahoo=db(db.gis_layer_yahoo.enabled==True).select(db.gis_layer_yahoo.ALL)
        for layer in layers_yahoo:
            for subtype in gis_layer_yahoo_subtypes:
                if layer.subtype==subtype:
                    yahoo['%s' % subtype]=layer.name
                    yahoo.enabled=1
    except:
        # Redirect to Key entry screen
        session.warning=T('Please enter a Yahoo Key if you wish to use Yahoo Layers')
        redirect(URL(r=request,f=apikey))
        
    # Virtual Earth
    virtualearth=Storage()
    layers_virtualearth=db(db.gis_layer_virtualearth.enabled==True).select(db.gis_layer_virtualearth.ALL)
    for layer in layers_virtualearth:
        for subtype in gis_layer_virtualearth_subtypes:
            if layer.subtype==subtype:
                virtualearth['%s' % subtype]=layer.name
    
    # Internal Features
    # ToDo: Only include those features which are are in enabled feature groups (either independently or through a feature class)
    #feature_groups=db(db.gis_feature_group.enabled==True).select(db.gis_layer_feature_group.ALL)
    #for feature_group in feature_groups:
    # Limit to return only 200 features to prevent overloading the browser!
    features = db(db.gis_feature.id>0).select(db.gis_feature.ALL,limitby=(0,200))
    features_classes=Storage()
    features_markers=Storage()
    features_metadata=Storage()
    for feature in features:
        # 1st choice for a Marker is the Feature's
        marker = feature.marker
        try:
            feature_class = db(db.gis_feature_class.id==feature.feature_class).select()[0]
            
            if not marker:
                # 2nd choice for a Marker is the Feature Class's
                marker = feature_class.marker
        except:
            feature_class = None
        if not marker:
            # 3rd choice for a Marker is the default
            marker = features_marker
        features_classes[feature.id] = feature_class
        features_markers[feature.id] = db(db.gis_marker.id==marker).select()[0].image
                
        try:
            feature_metadata = db(db.gis_feature_metadata.id==feature.metadata).select()[0]
        except:
            feature_metadata = None
        features_metadata[feature.id] = feature_metadata

    # Add the Layers to the Return
    output.update(dict(openstreetmap=openstreetmap,google=google,yahoo=yahoo,virtualearth=virtualearth,features=features,features_classes=features_classes,features_markers=features_markers,features_metadata=features_metadata))
    
    return output
