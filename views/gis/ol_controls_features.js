// Supports feature create controls (Point, Line & Polygon)
// On Creating a new feature, display a popup box to enter details.
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
    var fc_contentHTML = "<div class='gis_openlayers_popupbox' id='popup_0'><form method='post' action='{{=URL(r=request,c='gis',f='feature',args=['create'],vars=dict(format='json'))}}' id='form0' name='form0'> <div class='gis_openlayers_popupbox_header'> <div class='gis_openlayers_popupbox_header_r'> <div class='gis_openlayers_popupbox_author'><label for='gis_popup_author' >Author:</label> <input type='text' name='gis_popup_author' id='popup_0_popup_auth' size='15' maxlength='60' tabindex=8 /></div>       <div class='gis_openlayers_popupbox_date'><label for='gis_popup_date' >Date:</label> <input type='text' name='gis_popup_date' id='popup_0_popup_edate' size='15' tabindex=9 /></div></div><div class='gis_openlayers_popupbox_header_l'> <div class='gis_openlayers_popupbox_name'><label for='gis_popup_name'>Name:</label> <span><input type='text' name='gis_popup_name' id='popup_0_popup_name' size='10' maxlength='60' tabindex=6 /></span> ()</div>       <div class='gis_openlayers_popupbox_url'><label for='gis_popup_name'>Url:</label> <input type='text' name='gis_popup_url' id='popup_0_popup_url' size='40' maxlength='100' tabindex=7 /></div>     </div>      <div class='gis_openlayers_popupbox_address'><b>Address:</b> <input type='text' name='gis_popup_address' id='popup_0_popup_add' size='55' maxlength='200' tabindex=10 /></div>   </div>   <div class='gis_openlayers_popupbox_body'>     <span class='gis_openlayers_popupbox_text'><textarea rows='5' cols='70' name='gis_popup_desc' id='popup_0_popup_desc' tabindex=11 ></textarea></span>  </div>  <div class='gis_openlayers_popupbox_footer'>      <span><a onclick='shn_gis_popup_new_cancel(&#39popup_0&#39)' alt='cancel'><div class='gis_openlayers_popupbox_edit_cancel' style='width: 17px; height: 17px;'></div><span>cancel</span></a></span> <span><a onclick='shn_gis_popup_new_ok(&#39popup_0&#39)' alt='ok'><div class='gis_openlayers_popupbox_edit_ok' style='width: 17px; height: 17px;'></div><span>ok</span></a></span>   </div>  <div style='clear: both;'></div></form></div>";
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
// Called by closeBox in Popup
function shn_gis_popup_new_cancel(){
    currentFeature.popup.hide();
    featuresLayer.removeFeatures([currentFeature]);
    currentFeature.popup.destroy(currentFeature.popup);
    currentFeature.destroy();
    currentFeature = null;
}

// Supports feature selectControl
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
function onFeatureUnselect_1(feature) {
    feature.popup.hide();
}


// Add marker to map (called by ol_layers_features.js)
function add_Feature_with_popup(layer, feature_id, geom, popupContentHTML, iconURL) {
    // Set icon dims
    var icon_img = new Image();
    icon_img.src = iconURL;
    var max_w = 25;
    var max_h = 35;
    var width = icon_img.width;
    var height = icon_img.height;
    if(width > max_w){
        height = ((max_w / width) * height);
        width = max_w;
    }
    if(height > max_h){
        width = ((max_h / height) * width);
        height = max_h;
    }
    // http://www.nabble.com/Markers-vs-Features--td16497389.html
    var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
    //style_mark.pointRadius = 12;
    style_marker.graphicWidth = width;
    style_marker.graphicHeight = height;
    style_marker.graphicXOffset = -(width / 2);
    style_marker.graphicYOffset = -height;
    style_marker.externalGraphic = iconURL;
    style_marker.graphicOpacity = 1;
    // Create Feature Vector
    var featureVec = new OpenLayers.Feature.Vector(geom, null, style_marker);
    featureVec.fid = feature_id;
    // Create Popup
    var fc_id = null;
    var fc_lonlat = featureVec.geometry.getBounds().getCenterLonLat();
    var fc_size = null;
    var fc_contentHTML = popupContentHTML;
    var fc_anchor = null;
    var fc_closeBox = true;
    var fc_closeBoxCallback = onPopupClose;
    var framedCloud = new OpenLayers.Popup.FramedCloud(fc_id, fc_lonlat, fc_size, fc_contentHTML, fc_anchor, fc_closeBox, fc_closeBoxCallback);
    framedCloud.autoSize = true;
    framedCloud.minSize = new OpenLayers.Size(460,270);
    // Add Popup
    featureVec.popup = framedCloud;
    // Add Feature
    layer.addFeatures([featureVec]);
}
// Supports add_Feature_with_popup()
function onPopupClose(evt) {
    currentFeature.popup.hide();
}

