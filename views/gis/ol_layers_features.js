featuresLayer = new OpenLayers.Layer.Vector("Internal Features");
var proj_current = map.getProjectionObject();

{{for feature in features:}}
    //ToDo: make work for more than just points!
    var coords = new Array(new OpenLayers.Geometry.Point((new OpenLayers.LonLat({{=feature.lon}}, {{=feature.lat}}).transform(proj4326, proj_current)).lon, (new OpenLayers.LonLat({{=feature.lon}}, {{=feature.lat}}).transform(proj4326, proj_current)).lat));
    //var popupContentHTML = "{{#=XML(features_popup[feature.id])}}";
    var popupContentHTML = {{include 'gis/ol_features_popup.html'}}
    var geom = coordToGeom(coords, '{{=feature.type}}');
    var iconURL = '{{=URL(r=request,c='default',f='download',args=[features_markers[feature.id]])}}';
    add_Feature_with_popup(featuresLayer, '{{=feature.uuid}}', geom, popupContentHTML, iconURL);
{{pass}}
    
// Add Features layer
map.addLayer(featuresLayer);

featuresLayer.events.register('featureadded', featuresLayer, function(){
       // ToDo: Support 2 Modes via if: else:
       // Add a point with popup (for use from map_viewing_client)
       shn_gis_map_create_feature;
       // Add a point without popup (for use from add_feature during modue CRUD)
       //shn_gis_map_add_geometry;
});

// Show Busy cursor whilst loading Features
map.registerEvents(featuresLayer);

