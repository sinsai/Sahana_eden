// On Creating a new feature Display a popup box to enter details.
function shn_gis_map_create_feature(feature){
    // If adding a new popup before an old one is completed, kill old popup (current feature is set to null at end of process)
    if(currentFeature != null){
        currentFeature.popup.hide();
        featuresLayer.removeFeatures([currentFeature]);
        currentFeature.popup.destroy(currentFeature.popup);
        currentFeature.destroy();
    }
    // Generate Popup + Props
    var fc_id = null;
    var fc_lonlat = feature.geometry.getBounds().getCenterLonLat();
    var fc_size = null;
    var fc_contentHTML = "<?= shn_gis_form_popupHTML_new(); ?>";
    var fc_anchor = null;
    var fc_closeBox = true; // Bad can close without create...
    var fc_closeBoxCallback = shn_gis_popup_new_cancel;
    var framedCloud = new OpenLayers.Popup.FramedCloud(fc_id, fc_lonlat, fc_size, fc_contentHTML, fc_anchor, fc_closeBox, fc_closeBoxCallback);
    framedCloud.autoSize = true;
    framedCloud.minSize = new OpenLayers.Size(460,270);
    // Add Popup
    feature.popup = framedCloud;
    map.addPopup(feature.popup);
    feature.popup.show();
    currentFeature = feature;
}
// Supports feature select control.
function onFeatureSelect_1(feature){
    // Set global for back referencing
    currentFeature = feature;
    if (feature.popup.map == null) {
        map.addPopup(feature.popup);
        feature.popup.show();
    } else {
        feature.popup.toggle();
    }
}
// Supports feature select control.
function onFeatureUnselect_1(feature) {
    feature.popup.hide();
}
// Supports feature select control.
function onPopupClose(evt) {
    onFeatureUnselect_1(currentFeature);
}
