var kmlLayers = new Array();
{{for layer in kml_layers:}}
    {{name = layer.replace(' ', '_')}}
    var kmlLayer{{=name}} = new OpenLayers.Layer.GML( "{{=layer}}", "{{=kml_layers[layer].url}}", {
        format: OpenLayers.Format.KML, formatOptions: { extractStyles: true, extractAttributes: true, maxDepth: 2 }, projection: proj4326});
    map.addLayer(kmlLayer{{=name}});
    kmlLayers.push(kmlLayer{{=name}});
{{pass}}
{{if kml_layers:}}
// Select Control for KML Layers
var kmlpopupControl = new OpenLayers.Control.SelectFeature(kmlLayers, { onSelect: onFeatureSelectkml, onUnselect: onFeatureUnselectkml } );
map.addControl(kmlpopupControl);
kmlpopupControl.activate();

function onPopupClosekml(evt) {
    kmlpopupControl.unselect(selectedFeaturekml);
}
function onFeatureSelectkml(feature) {
    selectedFeaturekml = feature;
    if ("undefined" === feature.attributes.description) {
        popup = new OpenLayers.Popup.FramedCloud("chicken",
            feature.geometry.getBounds().getCenterLonLat(),
            new OpenLayers.Size(100,100),
            "<h2>" + feature.attributes.name + "</h2>" + feature.attributes.description,
            null, true, onPopupClosekml);
    } else {
        popup = new OpenLayers.Popup.FramedCloud("chicken",
            feature.geometry.getBounds().getCenterLonLat(),
            new OpenLayers.Size(100,100),
            "<h2>" + feature.attributes.name + "</h2>",
            null, true, onPopupClosekml);
    }
    feature.popup = popup;
    map.addPopup(popup);
}
function onFeatureUnselectkml(feature) {
    map.removePopup(feature.popup);
    feature.popup.destroy();
    feature.popup = null;
}
{{pass}}