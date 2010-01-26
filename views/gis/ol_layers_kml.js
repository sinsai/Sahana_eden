var kmlLayers = new Array();
{{for layer in kml_layers:}}
    {{name = layer.replace(' ', '_')}}
    var kmlLayer{{=name}} = new OpenLayers.Layer.GML( "{{=layer}}", "{{=kml_layers[layer].url}}", {
        strategies: [ strategy ],
        format: OpenLayers.Format.KML,
        formatOptions: { extractStyles: true, extractAttributes: true, maxDepth: 2 },
        projection: proj4326});
    map.addLayer(kmlLayer{{=name}});
    kmlLayers.push(kmlLayer{{=name}});
    kmlLayer{{=name}}.events.on({ "featureselected": onKmlFeatureSelect, "featureunselected": onFeatureUnselect });
{{pass}}
{{if kml_layers:}}
allLayers = allLayers.concat(kmlLayers);
function onKmlFeatureSelect(event) {
    var feature = event.feature;
    var selectedFeature = feature;
    if ("undefined" == feature.attributes.description) {
        var popup = new OpenLayers.Popup.FramedCloud("chicken",
        feature.geometry.getBounds().getCenterLonLat(),
        new OpenLayers.Size(200,200),
        "<h2>" + feature.attributes.name + "</h2>",
        null, true, onPopupClose);
    } else {
        var popup = new OpenLayers.Popup.FramedCloud("chicken",
        feature.geometry.getBounds().getCenterLonLat(),
        new OpenLayers.Size(200,200),
        "<h2>" + feature.attributes.name + "</h2>" + feature.attributes.description,
        null, true, onPopupClose);
    };
    feature.popup = popup;
    map.addPopup(popup);
}
{{pass}}
