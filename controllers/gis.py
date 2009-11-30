# -*- coding: utf-8 -*-

module = 'gis'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
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
    return shn_rest_controller(module, 'config', deletable=False, listadd=False)
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
    return shn_rest_controller(module, 'location', onvalidation=lambda form: wkt_centroid(form))
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
def convert_gps():
    " Provide a form which converts from GPS Coordinates to Decimal Coordinates "
    return dict()

def shn_latlon_to_wkt(lat, lon):
    """Convert a LatLon to a WKT string
    >>> shn_latlon_to_wkt(6, 80)
    'POINT(80 6)'
    """
    WKT = 'POINT(%d %d)' % (lon, lat)
    return WKT

# Features
# - experimental!
def feature_create_map():
    "Show a map to draw the feature"
    title = T("Add GIS Feature")
    form = crud.create('gis_location', onvalidation=lambda form: wkt_centroid(form))
    _projection = db(db.gis_config.id==1).select()[0].projection_id
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
    tables = [db.gis_feature_class_to_feature_group, db.gis_location_to_feature_group]
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
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, module, 'feature_group_contents', 'html')
        # Display a List_Create page with checkboxes to remove items
        
        # Feature Classes
        query = (tables[0].feature_group_id == feature_group) & (tables[0].deleted == False)
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.feature_class_id
            name = db.gis_feature_class[id].name
            description = db.gis_feature_class[id].description
            id_link = A(id, _href=URL(r=request, f='feature_class', args=['read', id]))
            checkbox = INPUT(_type="checkbox", _value="on", _name='feature_class_' + str(id), _class="remove_item")
            item_list.append(TR(TD(id_link), TD(name, _align='left'), TD(description, _align='left'), TD(checkbox, _align='center'), _class=theclass, _align='right'))
            
        # Features
        query = (tables[1].feature_group_id == feature_group) & (tables[1].deleted == False)
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.location_id
            name = db.gis_location[id].name
            # Metadata is M->1 to Features
            metadata = db(db.gis_metadata.location_id==id & db.gis_metadata.deleted==False).select()
            if metadata:
                # We just read the description of the 1st one
                description = metadata[0].description
            else:
                description = ''
            id_link = A(id, _href=URL(r=request, f='location', args=['read', id]))
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
        addtitle = T("Add to Feature Group")
        response.view = '%s/feature_group_contents_list_create.html' % module
        output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form1=form1, form2=form2, feature_group=feature_group))
    else:
        # Display a simple List page
        # Feature Classes
        query = (tables[0].feature_group_id == feature_group) & (tables[0].deleted == False)
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.feature_class_id
            name = db.gis_feature_class[id].name
            description = db.gis_feature_class[id].description
            id_link = A(id, _href=URL(r=request, f='feature_class', args=['read', id]))
            item_list.append(TR(TD(id_link), TD(name, _align='left'), TD(description, _align='left'), _class=theclass, _align='right'))
            
        # Features
        query = (tables[1].feature_group_id == feature_group) & (tables[1].deleted == False)
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.location_id
            name = db.gis_location[id].name
            # Metadata is M->1 to Features
            metadata = db(db.gis_metadata.location_id==id & db.gis_metadata.deleted==False).select()
            if metadata:
                # We just read the description of the 1st one
                description = metadata[0].description
            else:
                description = ''
            id_link = A(id, _href=URL(r=request, f='location', args=['read', id]))
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
    if 'feature_class_id' in form.vars:
        feature_class_id = form.vars.feature_class_id
        table = db.gis_feature_class_to_feature_group
        query = (table.feature_group==feature_group) & (table.feature_class_id==feature_class_id)
    elif 'location_id' in form.vars:
        location_id = form.vars.location_id
        table = db.gis_location_to_feature_group
        query = (table.feature_group==feature_group) & (table.location_id==location_id)
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
    tables = [db.gis_feature_class_to_feature_group, db.gis_location_to_feature_group]
    authorised = shn_has_permission('update', tables[0]) and shn_has_permission('update', tables[1])
    if authorised:
        for var in request.vars:
            if 'feature_class_id' in var:
                # Delete
                feature_class_id = var[14:]
                query = (tables[0].feature_group==feature_group) & (tables[0].feature_class_id==feature_class_id)
                db(query).delete()
            elif 'location_id' in var:
                # Delete
                location_id = var[8:]
                query = (tables[1].feature_group==feature_group) & (tables[1].location_id==location_id)
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
    _projection = db(db.gis_config.id==1).select()[0].projection_id
    projection = db(db.gis_projection.id==_projection).select()[0].epsg
    if 'lat' in request.vars:
        lat = request.vars.lat
    else:
        lat = db(db.gis_config.id==1).select()[0].lat
    if 'lon' in request.vars:
        lon = request.vars.lon
    else:
        lon = db(db.gis_config.id==1).select()[0].lon
    if 'zoom' in request.vars:
        zoom = request.vars.zoom
    else:
        zoom = db(db.gis_config.id==1).select()[0].zoom
    units = db(db.gis_projection.epsg==projection).select()[0].units
    maxResolution = db(db.gis_projection.epsg==projection).select()[0].maxResolution
    maxExtent = db(db.gis_projection.epsg==projection).select()[0].maxExtent
    marker_default = db(db.gis_config.id==1).select()[0].marker_id
    
    # Add the Config to the Return
    output.update(dict(width=width, height=height, projection=projection, lat=lat, lon=lon, zoom=zoom, units=units, maxResolution=maxResolution, maxExtent=maxExtent))
    
    # Layers
    baselayers = layers()
    # Add the Layers to the Return
    output.update(dict(openstreetmap=baselayers.openstreetmap, google=baselayers.google, yahoo=baselayers.yahoo, bing=baselayers.bing))

    # Internal Features
    features = Storage()
    # Features are displayed in a layer per FeatureGroup
    feature_groups = db(db.gis_feature_group.enabled == True).select()
    for feature_group in feature_groups:
        # FIXME: Use OL's Cluster Strategy to ensure no more than 200 features displayed to prevent overloading the browser!
        # - better than doing a server-side spatial query to show ones visible within viewport on every Pan/Zoom!
        groups = db.gis_feature_group
        locations = db.gis_location
        classes = db.gis_feature_class
        metadata = db.gis_metadata
        # Which Features are added to the Group directly?
        link = db.gis_location_to_feature_group
        features1 = db(link.feature_group_id == feature_group.id).select(groups.ALL, locations.ALL, classes.ALL, left=[groups.on(groups.id == link.feature_group_id), locations.on(locations.id == link.location_id), classes.on(classes.id == locations.feature_class_id)])
        # FIXME?: Extend JOIN for Metadata (sortby, want 1 only), Markers (complex logic), Resource_id (need to find from the results of prev query)
        # Which Features are added to the Group via their FeatureClass?
        link = db.gis_feature_class_to_feature_group
        features2 = db(link.feature_group_id == feature_group.id).select(groups.ALL, locations.ALL, classes.ALL, left=[groups.on(groups.id == link.feature_group_id), classes.on(classes.id == link.feature_class_id), locations.on(locations.feature_class_id == link.feature_class_id)])
        # FIXME?: Extend JOIN for Metadata (sortby, want 1 only), Markers (complex logic), Resource_id (need to find from the results of prev query)
        features[feature_group.id] = features1 | features2
        for feature in features[feature_group.id]:
            feature.module = feature.gis_feature_class.module
            feature.resource = feature.gis_feature_class.resource
            if feature.module and feature.resource:
                feature.resource_id = db(db['%s_%s' % (feature.module, feature.resource)].location_id == feature.gis_location.id).select()[0].id
            else:
                feature.resource_id = None
            # 1st choice for a Marker is the Feature's
            marker = feature.gis_location.marker_id
            if not marker:
                # 2nd choice for a Marker is the Feature Class's
                marker = feature.gis_feature_class.marker_id
            if not marker:
                # 3rd choice for a Marker is the default
                marker = marker_default
            feature.marker = db(db.gis_marker.id == marker).select()[0].image
            
            try:
                # Metadata is M->1 to Features
                # We use the most recent one
                query = (db.gis_metadata.location_id == feature.gis_location.id) & (db.gis_metadata.deleted == False)
                metadata = db(query).select(orderby=~db.gis_metadata.event_time)[0]
            except:
                metadata = None
            feature.metadata = metadata

    # Add the Features to the Return
    #output.update(dict(features=features, features_classes=feature_classes, features_markers=feature_markers, features_metadata=feature_metadata))
    output.update(dict(feature_groups=feature_groups, features=features))
    
    return output
