var proj_current = map.getProjectionObject();

// Layer to hold Draft Features
featuresLayer = new OpenLayers.Layer.Vector("Draft Features", {displayInLayerSwitcher: false});
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

// FeatureGroup Layers
{{for feature_group in feature_groups:}}
featuresLayer{{=feature_group.name}} = new OpenLayers.Layer.Vector("{{=feature_group.name}}", {displayInLayerSwitcher: true});
map.addLayer(featuresLayer{{=feature_group.name}});
{{for feature in features[feature_group.id]:}}
  {{if feature.gis_location.id:}}
    parser = new OpenLayers.Format.WKT();
    var geom = parser.read('{{=feature.gis_location.wkt}}').geometry;
    geom = geom.transform(proj4326, proj_current);
    var popupContentHTML = {{include 'gis/ol_features_popup.html'}}
    var iconURL = '{{=URL(r=request, c='default', f='download', args=[feature.marker])}}';
    add_Feature_with_popup(featuresLayer{{=feature_group.name}}, '{{=feature.gis_location.uuid}}', geom, popupContentHTML, iconURL);
  {{else:}}
  {{pass}}
{{pass}}
{{pass}}

