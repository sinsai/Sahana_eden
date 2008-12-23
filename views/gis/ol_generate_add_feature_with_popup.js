// Add marker to map
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
    // Create Feature Vector + Props
    var featureVec = new OpenLayers.Feature.Vector(geom, null, style_marker);
    featureVec.fid = feature_id;
    // Generate Popup + Props
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
    // Add Feature.
    layer.addFeatures([featureVec]);
}
