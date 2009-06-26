# -*- coding: utf-8 -*-

module = 'gis'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Map Viewing Client'), False, URL(r=request, f='map_viewing_client')],
    [T('Map Service Catalogue'), False, URL(r=request, f='map_service_catalogue')],
]

# Web2Py Tools functions
def download():
    "Download a file."
    return response.download(request, db) 

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def apikey():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'apikey', deletable=False, listadd=False)
def config():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'config')
def feature():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'feature', onvalidation=lambda form: wkt_centroid(form))
def feature_class():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'feature_class')
def feature_group():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'feature_group')
def feature_metadata():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'feature_metadata')
def location():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'location')
def marker():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'marker')
def projection():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'projection', deletable=False)
def layer_openstreetmap():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'layer_openstreetmap', deletable=False)
def layer_google():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'layer_google', deletable=False)
def layer_yahoo():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'layer_yahoo', deletable=False)
def layer_bing():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'layer_bing', deletable=False)

# Module-specific functions

def shn_latlon_to_wkt(lat,lon):
    """Convert a LatLon to a WKT string
    >>> shn_latlon_to_wkt(6,80)
    'POINT(80 6)'
    """
    WKT = 'POINT(%d %d)' %(lon,lat)
    return WKT

# Features
# - experimental!
def feature_create_map():
    "Show a map to draw the feature"
    title = T("Add GIS Feature")
    form = crud.create('gis_feature', onvalidation=lambda form: wkt_centroid(form))
    _projection = db(db.gis_config.id==1).select()[0].projection
    projection = db(db.gis_projection.id==_projection).select()[0].epsg

    # Layers
    baselayers = layers()

    return dict(title=title, module_name=module_name, form=form, projection=projection, openstreetmap=baselayers.openstreetmap, google=baselayers.google, yahoo=baselayers.yahoo, bing=baselayers.bing)
    
# Feature Groups
def feature_group_contents():
    "Many to Many CRUD Controller"
    if len(request.args) == 0:
        session.error = T("Need to specify a feature group!")
        redirect(URL(r=request, f='feature_group'))
    feature_group = request.args[0]
    tables = [db.gis_feature_class_to_feature_group, db.gis_feature_to_feature_group]
    authorised = shn_has_permission('update', tables[0]) and shn_has_permission('update', tables[1])
    
    title = db.gis_feature_group[feature_group].name
    feature_group_description = db.gis_feature_group[feature_group].description
    # Start building the Return with the common items
    output = dict(module_name=module_name, title=title, description=feature_group_description)
    # Audit
    shn_audit_read(operation='list', resource='feature_group_contents', record=feature_group, representation='html')
    item_list = []
    even = True
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, 'feature_group_contents', 'html')
        # Display a List_Create page with checkboxes to remove items
        
        # Feature Classes
        query = tables[0].feature_group==feature_group
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.feature_class
            name = db.gis_feature_class[id].name
            description = db.gis_feature_class[id].description
            id_link = A(id, _href=URL(r=request, f='feature_class', args=['read', id]))
            checkbox = INPUT(_type="checkbox", _value="on", _name='feature_class_' + str(id), _class="remove_item")
            item_list.append(TR(TD(id_link), TD(name, _align='left'), TD(description, _align='left'), TD(checkbox, _align='center'), _class=theclass, _align='right'))
            
        # Features
        query = tables[1].feature_group==feature_group
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.feature
            name = db.gis_feature[id].name
            metadata = db.gis_feature[id].metadata
            if metadata:
                description = db.gis_feature_metadata[metadata].description
            else:
                description = ''
            id_link = A(id, _href=URL(r=request, f='feature', args=['read', id]))
            checkbox = INPUT(_type="checkbox", _value="on", _name='feature_' + str(id), _class="remove_item")
            item_list.append(TR(TD(id_link), TD(name, _align='left'), TD(description, _align='left'), TD(checkbox, _align='center'), _class=theclass, _align='right'))
        
        table_header = THEAD(TR(TH('ID'), TH('Name'), TH(T('Description')), TH(T('Remove'))))
        table_footer = TFOOT(TR(TD(INPUT(_id='submit_button', _type='submit', _value=T('Update')))), _colspan=3, _align='right')
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name='custom', _method='post', _enctype='multipart/form-data', _action=URL(r=request, f='feature_group_update_items', args=[feature_group])))
        subtitle = T("Contents")
        
        crud.messages.submit_button=T('Add')
        # Check for duplicates before Item is added to DB
        crud.settings.create_onvalidation = lambda form: feature_group_dupes(form)
        crud.messages.record_created = T('Feature Group Updated')
        form1 = crud.create(tables[0], next=URL(r=request, args=[feature_group]))
        form1[0][0].append(TR(TD(T('Type:')), TD(LABEL(T('Feature Class'), INPUT(_type="radio", _name="fg1", _value="FeatureClass", value="FeatureClass")), LABEL(T('Feature'), INPUT(_type="radio", _name="fg1", _value="Feature", value="FeatureClass")))))
        form2 = crud.create(tables[1], next=URL(r=request, args=[feature_group]))
        form2[0][0].append(TR(TD(T('Type:')), TD(LABEL(T('Feature Class'), INPUT(_type="radio", _name="fg2", _value="FeatureClass", value="Feature")), LABEL(T('Feature'), INPUT(_type="radio", _name="fg2", _value="Feature", value="Feature")))))
        addtitle = T("Add to feature_group")
        response.view = '%s/feature_group_contents_list_create.html' % module
        output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form1=form1, form2=form2, feature_group=feature_group))
    else:
        # Display a simple List page
        # Feature Classes
        query = tables[0].feature_group==feature_group
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.feature_class
            name = db.gis_feature_class[id].name
            description = db.gis_feature_class[id].description
            id_link = A(id, _href=URL(r=request, f='feature_class', args=['read', id]))
            item_list.append(TR(TD(id_link), TD(name, _align='left'), TD(description, _align='left'), _class=theclass, _align='right'))
            
        # Features
        query = tables[1].feature_group==feature_group
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.feature
            name = db.gis_feature[id].name
            metadata = db.gis_feature[id].metadata
            if metadata:
                description = db.gis_feature_metadata[metadata].description
            else:
                description = ''
            id_link = A(id, _href=URL(r=request, f='feature', args=['read', id]))
            item_list.append(TR(TD(id_link), TD(name, _align='left'), TD(description, _align='left'), _class=theclass, _align='right'))
        
        table_header = THEAD(TR(TH('ID'), TH('Name'), TH(T('Description'))))
        items = DIV(TABLE(table_header, TBODY(item_list), _id="table-container"))
        
        add_btn = A(T('Edit Contents'), _href=URL(r=request, c='default', f='user', args='login'), _id='add-btn')
        response.view = '%s/feature_group_contents_list.html' % module
        output.update(dict(items=items, add_btn=add_btn))
    return output
	
def feature_group_dupes(form):
    "Checks for duplicate Feature/FeatureClass before adding to DB"
    feature_group = form.vars.feature_group
    if 'feature_class' in form.vars:
        feature_class = form.vars.feature_class
        table = db.gis_feature_class_to_feature_group
        query = (table.feature_group==feature_group) & (table.feature_class==feature_class)
    elif 'feature' in form.vars:
        feature = form.vars.feature
        table = db.gis_feature_to_feature_group
        query = (table.feature_group==feature_group) & (table.feature==feature)
    else:
        # Something went wrong!
        return
    items = db(query).select()
    if items:
        session.error = T("Already in this Feature Group!")
        redirect(URL(r=request, args=feature_group))
    else:
        return
    
def feature_group_update_items():
    "Update a Feature Group's items (Feature Classes & Features)"
    if len(request.args) == 0:
        session.error = T("Need to specify a feature group!")
        redirect(URL(r=request, f='feature_group'))
    feature_group = request.args[0]
    tables = [db.gis_feature_class_to_feature_group, db.gis_feature_to_feature_group]
    authorised = shn_has_permission('update', tables[0]) and shn_has_permission('update', tables[1])
    if authorised:
        for var in request.vars:
            if 'feature_class' in var:
                # Delete
                feature_class = var[14:]
                query = (tables[0].feature_group==feature_group) & (tables[0].feature_class==feature_class)
                db(query).delete()
            elif 'feature' in var:
                # Delete
                feature = var[8:]
                query = (tables[1].feature_group==feature_group) & (tables[1].feature==feature)
                db(query).delete()
        # Audit
        shn_audit_update_m2m(resource='feature_group_contents', record=feature_group, representation='html')
        session.flash = T("Feature Group updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(r=request, f='feature_group_contents', args=[feature_group]))

def map_service_catalogue():
    """Map Service Catalogue.
    Allows selection of which Layers are active."""

    title = T('Map Service Catalogue')
    subtitle = T('List Layers')
    # Start building the Return with the common items
    output = dict(module_name=module_name, title=title, subtitle=subtitle)
    
    # Hack: We control all perms from this 1 table
    table = db.gis_layer_openstreetmap
    authorised = shn_has_permission('update', table)
    item_list = []
    even = True
    if authorised:
        # List View with checkboxes to Enable/Disable layers
        for type in gis_layer_types:
            table = db['gis_layer_%s' % type]
            query = table.id > 0
            sqlrows = db(query).select()
            for row in sqlrows:
                if even:
                    theclass = "even"
                    even = False
                else:
                    theclass = "odd"
                    even = True
                if row.description:
                    description = row.description
                else:
                    description = ''
                label = type + '_' + str(row.id)
                if row.enabled:
                    enabled = INPUT(_type="checkbox", value=True, _name=label)
                else:
                    enabled = INPUT(_type="checkbox", _name=label)
                item_list.append(TR(TD(row.name), TD(description), TD(enabled), _class=theclass))
                
        table_header = THEAD(TR(TH('Layer'), TH('Description'), TH('Enabled?')))
        table_footer = TFOOT(TR(TD(INPUT(_id='submit_button', _type='submit', _value=T('Update')), _colspan=3)), _align='right')
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name='custom', _method='post', _enctype='multipart/form-data', _action=URL(r=request, f='layers_enable')))

    else:
        # Simple List View
        for type in gis_layer_types:
            table = db['gis_layer_%s' % type]
            query = table.id > 0
            sqlrows = db(query).select()
            for row in sqlrows:
                if even:
                    theclass = "even"
                    even = False
                else:
                    theclass = "odd"
                    even = True
                if row.description:
                    description = row.description
                else:
                    description = ''
                if row.enabled:
                    enabled = INPUT(_type="checkbox", value='on', _disabled="disabled")
                else:
                    enabled = INPUT(_type="checkbox", _disabled="disabled")
                item_list.append(TR(TD(row.name), TD(description), TD(enabled), _class=theclass))
                
        table_header = THEAD(TR(TH('Layer'), TH('Description'), TH('Enabled?')))
        items = DIV(TABLE(table_header, TBODY(item_list), _id="table-container"))

    output.update(dict(items=items))
    return output

def layers():
    "Provide the Enabled Layers"

    layers = Storage()

    # OpenStreetMap
    layers.openstreetmap = Storage()
    layers_openstreetmap = db(db.gis_layer_openstreetmap.enabled==True).select(db.gis_layer_openstreetmap.ALL)
    for layer in layers_openstreetmap:
        for subtype in gis_layer_openstreetmap_subtypes:
            if layer.subtype == subtype:
                layers.openstreetmap['%s' % subtype] = layer.name
    
    # Google
    layers.google = Storage()
    # Check for Google Key
    try:
        layers.google.key = db(db.gis_apikey.name=='google').select(db.gis_apikey.apikey)[0].apikey
        layers_google = db(db.gis_layer_google.enabled==True).select(db.gis_layer_google.ALL)
        for layer in layers_google:
            for subtype in gis_layer_google_subtypes:
                if layer.subtype == subtype:
                    layers.google['%s' % subtype] = layer.name
                    layers.google.enabled = 1
    except:
        # Redirect to Key entry screen
        session.warning = T('Please enter a Google Key if you wish to use Google Layers')
        redirect(URL(r=request, f=apikey))
            
    # Yahoo
    layers.yahoo = Storage()
    # Check for Yahoo Key
    try:
        layers.yahoo.key = db(db.gis_apikey.name=='yahoo').select(db.gis_apikey.apikey)[0].apikey
        layers_yahoo = db(db.gis_layer_yahoo.enabled==True).select(db.gis_layer_yahoo.ALL)
        for layer in layers_yahoo:
            for subtype in gis_layer_yahoo_subtypes:
                if layer.subtype == subtype:
                    layers.yahoo['%s' % subtype] = layer.name
                    layers.yahoo.enabled = 1
    except:
        # Redirect to Key entry screen
        session.warning = T('Please enter a Yahoo Key if you wish to use Yahoo Layers')
        redirect(URL(r=request, f=apikey))
        
    # Bing (Virtual Earth)
    layers.bing = Storage()
    layers_bing = db(db.gis_layer_bing.enabled==True).select(db.gis_layer_bing.ALL)
    for layer in layers_bing:
        for subtype in gis_layer_bing_subtypes:
            if layer.subtype == subtype:
                layers.bing['%s' % subtype] = layer.name
                
    return layers
    
def layers_enable():
    "Enable/Disable Layers"
    
    # Hack: We control all perms from this 1 table
    table = db.gis_layer_openstreetmap
    authorised = shn_has_permission('update', table)
    if authorised:
        for type in gis_layer_types:
            resource = 'gis_layer_%s' % type
            table = db[resource]
            query = table.id > 0
            sqlrows = db(query).select()
            for row in sqlrows:
                query_inner = table.id==row.id
                var = '%s_%i' % (type, row.id)
                # Read current state
                if db(query_inner).select()[0].enabled:
                    # Old state: Enabled
                    if var in request.vars:
                        # Do nothing
                        pass
                    else:
                        # Disable
                        db(query_inner).update(enabled=False)
                        # Audit
                        shn_audit_update_m2m(resource=resource, record=row.id, representation='html')
                else:
                    # Old state: Disabled
                    if var in request.vars:
                        # Enable
                        db(query_inner).update(enabled=True)
                        # Audit
                        shn_audit_update_m2m(resource=resource, record=row.id, representation='html')
                    else:
                        # Do nothing
                        pass
        session.flash = T("Layers updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(r=request, f='map_service_catalogue'))

def map_viewing_client():
    """Map Viewing Client.
    Main user UI for viewing the Maps."""
    
    title = T('Map Viewing Client')
    response.title = title

    # Start building the Return with the Framework
    output = dict(title=title, module_name=module_name)
    
    # Config
    width = db(db.gis_config.id==1).select()[0].map_width
    height = db(db.gis_config.id==1).select()[0].map_height
    _projection = db(db.gis_config.id==1).select()[0].projection
    projection = db(db.gis_projection.id==_projection).select()[0].epsg
    lat = db(db.gis_config.id==1).select()[0].lat
    lon = db(db.gis_config.id==1).select()[0].lon
    zoom = db(db.gis_config.id==1).select()[0].zoom
    units = db(db.gis_projection.epsg==projection).select()[0].units
    maxResolution = db(db.gis_projection.epsg==projection).select()[0].maxResolution
    maxExtent = db(db.gis_projection.epsg==projection).select()[0].maxExtent
    features_marker = db(db.gis_config.id==1).select()[0].marker
    
    # Add the Config to the Return
    output.update(dict(width=width, height=height, projection=projection, lat=lat, lon=lon, zoom=zoom, units=units, maxResolution=maxResolution, maxExtent=maxExtent, features_marker=features_marker))
    
    # Layers
    baselayers = layers()
    
    # Internal Features
    # ToDo: Only include those features which are are in enabled feature groups (either independently or through a feature class)
    #feature_groups=db(db.gis_feature_group.enabled==True).select(db.gis_layer_feature_group.ALL)
    #for feature_group in feature_groups:
    # Limit to return only 200 features to prevent overloading the browser!
    features = db(db.gis_feature.id>0).select(db.gis_feature.ALL,limitby=(0,200))
    features_classes = Storage()
    features_markers = Storage()
    features_metadata = Storage()
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
    output.update(dict(openstreetmap=baselayers.openstreetmap, google=baselayers.google, yahoo=baselayers.yahoo, bing=baselayers.bing, features=features, features_classes=features_classes, features_markers=features_markers, features_metadata=features_metadata))
    
    return output
