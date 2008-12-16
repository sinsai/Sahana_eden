function ol_show_features_markers($features)
{
    global $conf;
    global $global;
    global $id;
    require_once $global['approot'] . '/inc/lib_gis/gis_fns.inc';
    require_once $global['approot'] . '/inc/lib_gis/lib_gis_forms.inc';
    // Add Features Layer
    echo 'featuresLayer = new OpenLayers.Layer.Vector("Internal Features");';
    echo "var proj_current = map.getProjectionObject();\n";
    // Set id in case any features do not have uuids...
    $id = 0;
    // Place each feature
    foreach($features as $feature){
        // Set Feature uuid
        if(isset($feature['f_uuid'])){
            $feature_uuid = 'outer_' . $feature['f_uuid'];
        } else{
            $uuid = 'outer_popup_' . $id++; // :(
        }
        // Set Feautre Type
        if(isset($feature['f_type'])){
            $type = $feature['f_type'];
        } else{
            $type = 'point';
        }
        // Generate vars for html popup HTML content
        if(isset($feature['f_class'])){
            $feature_class = shn_gis_get_feature_class_uuid($feature['f_class']);
        } else{
            $feature_class = shn_gis_get_feature_class_uuid($conf['gis_feature_type_default']);
        }
        // Set icon
        if(isset($feature['icon'])){
            $icon = $feature['icon'];
        } else {
            $icon = $feature_class['c_icon'];
        }
        if($icon == ''){
            $fc = shn_gis_get_feature_class_uuid($conf['gis_feature_type_default']);
            $icon = $fc['c_icon'];
        }
        // Bit of a hacky way to do it. Especially the transform...
        $coordinates = shn_gis_coord_decode($feature['f_coords']);
        $coords = '';
        if(count($coordinates) == 1){
             $coords = $coords . "var coords = new Array(new OpenLayers.Geometry.Point((new OpenLayers.LonLat({$coordinates[$i][0]}, {$coordinates[$i][1]}).transform(proj4326, proj_current)).lon, (new OpenLayers.LonLat({$coordinates[$i][0]}, {$coordinates[$i][1]}).transform(proj4326, proj_current)).lat));\n"; 
        } else {
             $coords = $coords . "var coords = new Array(";
             $ctot = count($coordinates) - 1;
             for($i = 1; $i < $ctot; $i++){
                 $coords = $coords . "new OpenLayers.Geometry.Point((new OpenLayers.LonLat({$coordinates[$i][0]}, {$coordinates[$i][1]}).transform(proj4326, proj_current)).lon, (new OpenLayers.LonLat({$coordinates[$i][0]}, {$coordinates[$i][1]}).transform(proj4326, proj_current)).lat), ";
             }
             if($ctot > 0){
             $coords = $coords . "new OpenLayers.Geometry.Point((new OpenLayers.LonLat({$coordinates[$i][0]}, {$coordinates[$i][1]}).transform(proj4326, proj_current)).lon, (new OpenLayers.LonLat({$coordinates[$i][0]}, {$coordinates[$i][1]}).transform(proj4326, proj_current)).lat)";   
             }
             $coords = $coords . ");\n";             
        }
        echo $coords;
        // Popup
        $html =  "var popupContentHTML = \"";
        $html = $html . shn_gis_form_popupHTML_view($feature);
        $html = $html . "\";\n";
        echo $html;
        // Create geometry of feature (point, line, polygon)
        echo "var geom = coordToGeom(coords, \"$type\");\n";
        echo "add_Feature_with_popup(featuresLayer, '$feature_uuid', geom, popupContentHTML, '$icon');\n";
    }
    // Add Feature layer
    echo "map.addLayer(featuresLayer);\n";
}
