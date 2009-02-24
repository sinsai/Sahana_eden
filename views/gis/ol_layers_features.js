featuresLayer = new OpenLayers.Layer.Vector("Internal Features");
var proj_current = map.getProjectionObject();

{{for feature in features:}}
    parser = new OpenLayers.Format.WKT();
    var geom = parser.read('{{=feature.wkt}}').geometry;
    geom = geom.transform(proj4326, proj_current);
    var popupContentHTML = {{include 'gis/ol_features_popup.html'}}
    var iconURL = '{{=URL(r=request,c='default',f='download',args=[features_markers[feature.id]])}}';
    add_Feature_with_popup(featuresLayer, '{{=feature.uuid}}', geom, popupContentHTML, iconURL);
{{pass}}
    
// Add Features layer
map.addLayer(featuresLayer);

featuresLayer.events.register('featureadded', featuresLayer, function(){
       // ToDo: Support 2 Modes via if: else:
       // Add a point with popup (for use from map_viewing_client)
       shn_gis_map_create_feature;
       // Add a point without popup (for use from add_feature during module CRUD)
       //shn_gis_map_add_geometry;
});

// Show Busy cursor whilst loading Features
map.registerEvents(featuresLayer);

