ol_layers_features();    
ol_add_feature('Feature', $icon);

// Add marker to map
function add_Feature(layer, feature_id, geom, iconURL){
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
    // Add Feature.
    layer.addFeatures([featureVec]);
}

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
    // framedCloud = OpenLayers.Class(new OpenLayers.Popup.FramedCloud, {'autoSize': true});
    framedCloud.autoSize = true;
    framedCloud.minSize = new OpenLayers.Size(460,270);
    // Add Popup
    featureVec.popup = framedCloud;
    // Add Feature.
    layer.addFeatures([featureVec]);
}

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
var xmlHttp
function shn_gis_popup_unable()
{
    alert ("The module that created this feature does not support this action here. Navigate to the module manually to perform this action.");
}
function shn_gis_popup_print()
{
    if (xmlHttp.readyState == 4){
        var textDoc = xmlHttp.responseText;
        currentFeature.popup.setContentHTML(textDoc);
    }
}
function shn_gis_popup_refresh_print()
{
    if (xmlHttp.readyState == 4){
        var textDoc = xmlHttp.responseText;
        if(textDoc == '<delete />'){
            currentFeature.popup.hide();
            featuresLayer.removeFeatures([currentFeature]);
            currentFeature.popup.destroy(currentFeature.popup);
            currentFeature.destroy();
            //featuresLayer.redraw();
        } else{
            currentFeature.popup.setContentHTML(textDoc);
        }
    }
}
function shn_gis_popup_new_print()
{
    if (xmlHttp.readyState == 4){
        var textDoc = xmlHttp.responseText;
        
        var geom = currentFeature.geometry.clone();
              
        currentFeature.popup.hide();
        featuresLayer.removeFeatures([currentFeature]);
        currentFeature.popup.destroy(currentFeature.popup);
        currentFeature.destroy();
        currentFeature = null;
        //featuresLayer.redraw();
        if(!(textDoc == 'fail' || textDoc == '')){ 
            var uuidpos = textDoc.search('<uuid />');
            var iconURLPos = textDoc.search('<icon />');
            
            var uuid = textDoc.substring(0, uuidpos);
            var iconURL = textDoc.substring((uuidpos + 8), iconURLPos);
            var html = textDoc.substring((iconURLPos + 8));

            add_Feature_with_popup(featuresLayer, uuid, geom, html, iconURL);
        } else{
            alert("Failed to create new Feature.");   
        }
    }
}
// Called by link in popup box
function shn_gis_popup_new_ok(id){
    xmlHttp = GetXmlHttpObject();
    if (xmlHttp==null){
        alert ("Your browser does not support AJAX!");
        return;
    }
    // Clone to stop any effects on the current feature.
    var cfcopy = currentFeature.clone();
    // returns string type of a feature
    // return point if not line or poly ....danger....
    var type = featureTypeStr(cfcopy);
    // Transform for db.
    var lonlat = cfcopy.geometry.getBounds().getCenterLonLat().clone();
    var proj_current = map.getProjectionObject();
    lonlat.transform(proj_current, proj4326);
    var lat = lonlat.lat;
    var lon = lonlat.lon;
    var wkt = cfcopy.geometry.transform(proj_current, proj4326).toString();
    var name  = document.getElementById(id + '_popup_name').value;
    var desc  = document.getElementById(id + '_popup_desc').value;
    var auth  = document.getElementById(id + '_popup_auth').value;
    var furl  = document.getElementById(id + '_popup_url').value;
    var add   = document.getElementById(id + '_popup_add').value;
    var edate = document.getElementById(id + '_popup_edate').value;
    // Send to db
    var url = 'index.php?act=gis_popup_new_ok&mod=xst&stream=text';
    url = url + "&type=" + type + "&center_lat=" + lat + "&center_lon=" + lon + "&wkt=" + wkt + "&name=" + name + "&desc=" + desc + "&auth=" + auth + "&url=" + furl + "&add=" + add + "&date=" + edate;
    url = url + "&sid=" + Math.random();
    xmlHttp.onreadystatechange = shn_gis_popup_new_print;
    xmlHttp.open("GET", url, true);
    xmlHttp.send(null);
}
// Called by link in popup box
function shn_gis_popup_new_cancel(){
    currentFeature.popup.hide();
    featuresLayer.removeFeatures([currentFeature]);
    currentFeature.popup.destroy(currentFeature.popup);
    currentFeature.destroy();
    currentFeature = null;
}
// Called by link in popup box
function shn_gis_popup_refresh(id)
{
    xmlHttp = GetXmlHttpObject();
    if (xmlHttp == null){
        alert ("Your browser does not support AJAX!");
        return;
    }

    var url = 'index.php?act=gis_popup_refresh&mod=xst&stream=text&id=' + id;
    url = url +"&sid=" + Math.random();
    xmlHttp.onreadystatechange = shn_gis_popup_refresh_print;
    xmlHttp.open("GET", url, true);
    xmlHttp.send(null);
}
// Called by link in popup box
function shn_gis_popup_delete(id)
{
    xmlHttp = GetXmlHttpObject();
    if (xmlHttp == null){
        alert ();
        return;
    }
    ok = confirm("Are you sure you wish to Delete Feature from system");
    if(ok){
        var url = 'index.php?act=gis_popup_delete&mod=xst&stream=text&id=' + id;
        url = url +"&sid=" + Math.random();
        xmlHttp.onreadystatechange = shn_gis_popup_refresh_print;
        xmlHttp.open("GET", url, true);
        xmlHttp.send(null);
    }
}
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
// Called by link in popup box
function shn_gis_popup_edit_details(id)
{
    xmlHttp = GetXmlHttpObject();
    if (xmlHttp==null){
        alert ("Your browser does not support AJAX!");
        return;
    }
    var url='index.php?act=gis_popup_edit_details&mod=xst&stream=text&id=' + id;
    url = url +"&sid=" + Math.random();
    xmlHttp.onreadystatechange = shn_gis_popup_print;
    xmlHttp.open("GET", url, true);
    xmlHttp.send(null);
}
function shn_gis_popup_edit_details_ok(id)
{
    xmlHttp = GetXmlHttpObject();
    if (xmlHttp==null){
        alert ("Your browser does not support AJAX!");
        return;
    }
    var name  = document.getElementById(id + '_popup_name').value;
    var desc  = document.getElementById(id + '_popup_desc').value;
    var auth  = document.getElementById(id + '_popup_auth').value;
    var furl   = document.getElementById(id + '_popup_url').value;
    var add   = document.getElementById(id + '_popup_add').value;
    var edate  = document.getElementById(id + '_popup_edate').value;
    var url = 'index.php?act=gis_popup_edit_details_ok&mod=xst&stream=text&id=' + id;
    url = url + "&name=" + name + "&desc=" + desc + "&auth=" + auth + "&url=" + furl + "&add=" + add + "&date=" + edate;
    url = url +"&sid=" + Math.random();
    xmlHttp.onreadystatechange = shn_gis_popup_print;
    xmlHttp.open("GET", url, true);
    xmlHttp.send(null);
}
function GetXmlHttpObject(){
    var xmlHttp=null;
    try{
        // Firefox, Opera 8.0+, Safari
        xmlHttp=new XMLHttpRequest();
    }
    catch (e){
        // Internet Explorer
        try{
            xmlHttp=new ActiveXObject("Msxml2.XMLHTTP");
        }
        catch (e){
            xmlHttp=new ActiveXObject("Microsoft.XMLHTTP");
        }
    }
    return xmlHttp;
}