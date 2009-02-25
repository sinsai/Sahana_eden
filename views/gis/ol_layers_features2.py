ol_layers_features.js old:
    {{if feature.type=='point':}}
        var geom = new OpenLayers.Geometry.Point((new OpenLayers.LonLat({{=feature.lon}}, {{=feature.lat}}).transform(proj4326, proj_current)).lon, (new OpenLayers.LonLat({{=feature.lon}}, {{=feature.lat}}).transform(proj4326, proj_current)).lat));
    //ToDo: make work for more than just points!
    {{elif feature.type=='line':}}
        coords = 
        var geom = new OpenLayers.Geometry.LineString(coords);
    {{elif feature.type=='polygon':}}
        var geom = new OpenLayers.Geometry.Polygon(new Array(new OpenLayers.Geometry.LinearRing(coords)));
    {{pass}}
    
    # Bit of a hacky way to do it. Especially the transform...
    coordinates = shn_gis_coord_decode(feature['f_coords'])
    coords = ''
    if(count(coordinates) == 1):
         coords += "var coords = new Array(new OpenLayers.Geometry.Point((new OpenLayers.LonLat({coordinates[i][0]}, {coordinates[i][1]}).transform(proj4326, proj_current)).lon, (new OpenLayers.LonLat({coordinates[i][0]}, {coordinates[i][1]}).transform(proj4326, proj_current)).lat));\n"; 
    else:
         coords += "var coords = new Array(";
         ctot = count(coordinates) - 1;
         for(i = 1; i < ctot; i++):
             coords += "new OpenLayers.Geometry.Point((new OpenLayers.LonLat({coordinates[i][0]}, {coordinates[i][1]}).transform(proj4326, proj_current)).lon, (new OpenLayers.LonLat({coordinates[i][0]}, {coordinates[i][1]}).transform(proj4326, proj_current)).lat), ";
         if(ctot > 0):
         coords += "new OpenLayers.Geometry.Point((new OpenLayers.LonLat({coordinates[i][0]}, {coordinates[i][1]}).transform(proj4326, proj_current)).lon, (new OpenLayers.LonLat({coordinates[i][0]}, {coordinates[i][1]}).transform(proj4326, proj_current)).lat)";   
         coords += ");\n"            

# Rewrite in JavaScript: http://javascript.about.com/library/bltut21.htm         
def shn_gis_coord_decode(coords):
    """ Takes the coord string stored in the db and decodes it into an array of:
    [0 => center of obj][0 => x, 1 => y, 2 => z]
    [1 => plot 1][0 => x, 1 => y, 2 => z]
    [2 => plot 2][0 => x, 1 => y, 2 => z]
    [3 => plot 3][0 => x, 1 => y, 2 => z]
    In the case of a single point (eg 33.54,64.32,0,wkt{POINT Z (33.54 64.32 0)} ) the call would result in:
    [0][0 => 33.54, 1 => 64.32, 2 => 0]
    [1][0 => 33.54, 1 => 64.32, 2 => 0]
    In a line or poly type (e.g. 2,3,0,wkt{POLYGON Z ((1 4 0,5 1 0,5 5 1))} )
    [0][0 => 2, 1 => 3, 2 => 0]
    [1][0 => 1, 1 => 4, 2 => 0]
    [2][0 => 5, 1 => 1, 2 => 0]
    [3][0 => 5, 1 => 5, 2 => 1]
    """
    output = array()
    subcoords = explode(",", coords, 4)
    #2,3,0,wkt{POLYGON Z ((1 4 0,5 1 0,5 5 1))}
    array_push(output, array(subcoords[0], subcoords[1], subcoords[2]))
    # [0][0 => 2, 1 => 3, 2 => 0]
    wkt = subcoords[3]
    # wkt{POLYGON Z ((1 4 0,5 1 0,5 5 1))}
    wkt = ereg_replace("(wkt{|})", "", wkt)
    # POLYGON Z ((1 4 0,5 1 0,5 5 1))
    wkt = explode('(' , wkt, 2)
    # 0 => POLYGON Z   1 => ((1 4 0,5 1 0,5 5 1))
    # if polygons start having inner circles this will need to change
    wkt = ereg_replace("(\(|\))", "", wkt[1])
    # 1 4 0,5 1 0,5 5 1
    wkt = explode(',' , wkt)
    # 0 => 1 4 0   1 => 5 1 0   2 => 5 5 1
    foreach(wkt as point):
        array_push(output, explode(' ' , point, 3) )
    return output
   
   
def shn_gis_form_popupHTML_view(feature):
    "Generate vars for popup HTML content"
        
    # Set Feature uuid
    if(isset(feature['f_uuid']) && feature['f_uuid'] != ''):
        feature_uuid = feature['f_uuid']
    else:
        # :(
        feature_uuid = 'popup_' . id++
    
    # Set Feature Class
    if(isset(feature['f_class']) && feature['f_class'] != ''):
        feature_class = shn_gis_get_feature_class_uuid(feature['f_class'])
    else:
        feature_class = shn_gis_get_feature_class_uuid(conf['gis_feature_type_default'])
    
    # Set name.
    if(isset(feature['f_name']) && feature['f_name'] != ''):
        name = feature['f_name']
    else:
        name = feature_class['c_name']
    
    # Set Description
    if(isset(feature['f_description']) && feature['f_description'] != ''):
        description = feature['f_description']
    else:
        description = feature_class['c_description']
    
    # Set Author
    if(isset(feature['f_author']) && feature['f_author'] != ''):
        author = feature['f_author']
    else:
        author = 'Anonymous'
    
    # Set Address
    if(isset(feature['f_address']) && feature['f_address'] != ''):
        address = feature['f_address']
    else:
        address = false
    
    # Set Event Date
    if(isset(feature['f_event_date'])):
        event_date = feature['f_event_date']
    else:
        event_date = 'Unknown'
    
    # Set View URL
    if(isset(feature['f_url']) && feature['f_url'] != ''):
        url = feature['f_url']
    else:
        url = false
    
    # Set View URL
    if(isset(feature['f_url_view']) && feature['f_url_view'] != ''):
        url_view = feature['f_url_view']
    else:
        url_view = false
    
    # Set Edit URL
    if (isset(feature['f_url_edit']) && feature['f_url_edit'] != ''):
        # if feature has an edit url
        url_edit = feature['f_url_edit']
    elif (isset(feature['f_module_item']) && feature['f_module_item'] != ''):
        # if is registered to a module but has no edit url, should not be editable.
        url_edit = false
    elif (!isset(feature['f_uuid']) || feature['f_uuid'] == ''):
        # if there is no uuid to tie feature being edited to...
        url_edit = false
    else:
        # if feature is not module related and has a uuid to tie changes to. (can edit)
        url_edit = true
    
    # Set Delete URL
    if (isset(feature['f_url_delete']) && feature['f_url_delete'] != ''):
        # if feature has a delete url
        url_del = feature['f_url_delete']
    elif (isset(feature['f_module_item']) && feature['f_module_item'] != ''):
        # if is registered to a module but has no del url, should not be deletable.
        url_del = false
    elif(!isset(feature['f_uuid']) || feature['f_uuid'] == ''):
        # if there is no uuid to tie feature being deleted to...
        url_del = false
    else:
        # if feature is not module related and has a uuid to tie changes to. (can del)
        url_del = true
 