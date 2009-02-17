// Add control to select features (showing info popup).
// unused currently
selectControl = new OpenLayers.Control.SelectFeature(featuresLayer, {
    onSelect: onFeatureSelect_1,
    onUnselect: onFeatureUnselect_1,
    multiple: false,
    clickout: true,
    toggle: true
});
//map.addControl(selectControl);

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



// Add control to drag internal features around the map.
// unused currently (will need to be careful about icon clash with Map pan/drag!)
dragControl = new OpenLayers.Control.DragFeature(featuresLayer, {
    onComplete: shn_gis_popup_edit_position
});
//map.addControl(dragControl);

// Called by dragControl after editing a Features position
function shn_gis_popup_edit_position(feature, pixel)
{
    xmlHttp = GetXmlHttpObject();
    if (xmlHttp==null){
        alert ("Your browser does not support AJAX!");
        return;
    }
    currentFeature = feature;
    // Move features popup to new location
    feature.popup.lonlat = feature.geometry.getBounds().getCenterLonLat();
    // Need id before clone
    var id  = feature.fid.substring(6)
    // Clone to stop any effects on the current feature.
    var cfcopy = feature.clone();
    // Transform for db.
    var lonlat = cfcopy.geometry.getBounds().getCenterLonLat().clone();
    var proj_current = map.getProjectionObject();
    lonlat.transform(proj_current, proj4326);
    var lat = lonlat.lat;
    var lon = lonlat.lon;
    var wkt = cfcopy.geometry.transform(proj_current, proj4326).toString();
    // Send to db
    //ToDo: =URL(r=request,c='gis',f='feature',args=['create'],vars=dict(format='json')
    var url='index.php?act=gis_popup_edit_position&mod=xst&stream=text&id=' + id;
    url = url + "&center_lat=" + lat + "&center_lon=" + lon + "&wkt=" + wkt;
    url = url +"&sid=" + Math.random();
    //xmlHttp.onreadystatechange = shn_gis_popup_print;
    xmlHttp.open("GET", url, true);
    xmlHttp.send(null);
}

// Add control to modify the shape of internal features on the map.
// WARNING this seems to cause select feature to behaviour strangely 
//(eg being able to drag a selected feature even if modify is disabled)
//modifyControl = new OpenLayers.Control.ModifyFeature(featuresLayer);
//map.addControl(modifyControl);
//modifyControl.mode = OpenLayers.Control.ModifyFeature.RESHAPE;
//modifyControl.mode &= ~OpenLayers.Control.ModifyFeature.DRAG;

// Start with select activated.
// ol_controls_activation.js
//shn_gis_map_control_select();