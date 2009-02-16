// Add control to add new points to the map.
pointControl = new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Point);
pointControl.featureAdded = shn_gis_map_create_feature;
// We add the controls to the mf_toolbar.js
//map.addControl(pointControl);

// Add control to add new lines to the map.
lineControl = new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Path);
lineControl.featureAdded = shn_gis_map_create_feature;
//map.addControl(lineControl);

// Add control to add new polygons to the map.
polygonControl = new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Polygon);
polygonControl.featureAdded = shn_gis_map_create_feature;
//map.addControl(polygonControl);

// On Creating a new feature Display a popup box to enter details.
function shn_gis_map_create_feature(feature){
    // If adding a new popup before an old one is completed kill old popup (current feature is set to null at end of process)
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
    var fc_contentHTML = "<div class='gis_openlayers_popupbox' id='popup_0'><form method='post' action='index.php?mod=admin&amp;act=gis_database_classes_edit' id='form0' name='form0'><input name='seq' value='seq_3' type='hidden' />   <div class='gis_openlayers_popupbox_header'>     <div class='gis_openlayers_popupbox_header_r'>       <div class='gis_openlayers_popupbox_author'><label for='gis_popup_author' >Author:</label> <input type='text' name='gis_popup_author' id='popup_0_popup_auth' size='15' maxlength='60' tabindex=8 /></div>       <div class='gis_openlayers_popupbox_date'><label for='gis_popup_date' >Date:</label> <input type='text' name='gis_popup_date' id='popup_0_popup_edate' size='15' tabindex=9 /></div>     </div>     <div class='gis_openlayers_popupbox_header_l'>       <div class='gis_openlayers_popupbox_name'><label for='gis_popup_name'>Name:</label> <span><input type='text' name='gis_popup_name' id='popup_0_popup_name' size='10' maxlength='60' tabindex=6 /></span> ()</div>       <div class='gis_openlayers_popupbox_url'><label for='gis_popup_name'>Url:</label> <input type='text' name='gis_popup_url' id='popup_0_popup_url' size='40' maxlength='100' tabindex=7 /></div>     </div>      <div class='gis_openlayers_popupbox_address'><b>Address:</b> <input type='text' name='gis_popup_address' id='popup_0_popup_add' size='55' maxlength='200' tabindex=10 /></div>   </div>   <div class='gis_openlayers_popupbox_body'>     <span class='gis_openlayers_popupbox_text'><textarea rows='5' cols='70' name='gis_popup_desc' id='popup_0_popup_desc' tabindex=11 ></textarea></span>  </div>  <div class='gis_openlayers_popupbox_footer'>      <span><a onclick='shn_gis_popup_new_cancel(&#39popup_0&#39)' alt='cancel'><div class='gis_openlayers_popupbox_edit_cancel' style='width: 17px; height: 17px;'></div><span>cancel</span></a></span>      <span><a onclick='shn_gis_popup_new_ok(&#39popup_0&#39)' alt='ok'><div class='gis_openlayers_popupbox_edit_ok' style='width: 17px; height: 17px;'></div><span>ok</span></a></span>   </div>  <div style='clear: both;'></div></form></div>";
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
// unused currently (will need to be careful about icon clash with Map pan/drag!
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