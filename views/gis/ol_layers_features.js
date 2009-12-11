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

// Show Busy cursor whilst loading Draft Features
map.registerEvents(featuresLayer);

// FeatureGroup Layers
var parser = new OpenLayers.Format.WKT();
var geom, popupContentHTML, iconURL;
var featuresLayers = new Array();

{{for feature_group in feature_groups:}}
{{fgname = feature_group.name.replace(' ', '_')}}
var featuresLayer{{=fgname}} = new OpenLayers.Layer.Vector("{{=fgname}}", {displayInLayerSwitcher: true});
map.addLayer(featuresLayer{{=fgname}});
featuresLayers.push(featuresLayer{{=fgname}});
{{for feature in features[feature_group.id]:}}
  {{if feature.gis_location.id:}}
    geom = parser.read('{{=feature.gis_location.wkt}}').geometry;
    geom = geom.transform(proj4326, projection_current);
    popupContentHTML = "{{include 'gis/ol_features_popup.html'}}";
    iconURL = '{{=URL(r=request, c='default', f='download', args=[feature.marker])}}';
    add_Feature_with_popup(featuresLayer{{=fgname}}, '{{=feature.gis_location.uuid}}', geom, popupContentHTML, iconURL);
  {{else:}}
  {{pass}}
{{pass}}
{{pass}}

// Select Control for Internal FeatureGroup Layers
select = new OpenLayers.Control.SelectFeature(featuresLayers, {
        clickout: true,
        toggle: true,
        multiple: false,
        onSelect: onFeatureSelect,
        onUnselect: onFeatureUnselect
    }
);
map.addControl(select);
select.activate();