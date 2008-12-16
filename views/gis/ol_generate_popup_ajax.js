var xmlHttp
function shn_gis_popup_unable(){
    alert ("{{=T("The module that created this feature does not support this action here. Navigate to the module manually to perform this action.")}}");
}
function shn_gis_popup_print(){
    if (xmlHttp.readyState == 4){
        var textDoc = xmlHttp.responseText;
        currentFeature.popup.setContentHTML(textDoc);
    }
}
function shn_gis_popup_refresh_print(){
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
function shn_gis_popup_new_print(){
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
            alert("{{=T("Failed to create new Feature")}}.");   
        }
    }
}
// Called by link in popup box
function shn_gis_popup_new_ok(id){
    xmlHttp = GetXmlHttpObject();
    if (xmlHttp==null){
        alert ("{{=T("Your browser does not support AJAX!")}}");
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
function shn_gis_popup_refresh(id){
    xmlHttp = GetXmlHttpObject();
    if (xmlHttp == null){
        alert ("{{=T("Your browser does not support AJAX!")}}");
        return;
    }

    var url = 'index.php?act=gis_popup_refresh&mod=xst&stream=text&id=' + id;
    url = url +"&sid=" + Math.random();
    xmlHttp.onreadystatechange = shn_gis_popup_refresh_print;
    xmlHttp.open("GET", url, true);
    xmlHttp.send(null);
}
// Called by link in popup box
function shn_gis_popup_delete(id){
    xmlHttp = GetXmlHttpObject();
    if (xmlHttp == null){
        alert ("{{=T("Your browser does not support AJAX!")}}");
        return;
    }
    ok = confirm("{{=T("Are you sure you wish to Delete Feature from system?")}}");
    if(ok){
        var url = 'index.php?act=gis_popup_delete&mod=xst&stream=text&id=' + id;
        url = url +"&sid=" + Math.random();
        xmlHttp.onreadystatechange = shn_gis_popup_refresh_print;
        xmlHttp.open("GET", url, true);
        xmlHttp.send(null);
    }
}
 // Called by dragControl after editing a Features position
function shn_gis_popup_edit_position(feature, pixel){
    xmlHttp = GetXmlHttpObject();
    if (xmlHttp==null){
        alert ("{{=T("Your browser does not support AJAX!")}}");
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
function shn_gis_popup_edit_details(id){
    xmlHttp = GetXmlHttpObject();
    if (xmlHttp==null){
        alert ("{{=T("Your browser does not support AJAX!")}}");
        return;
    }
    var url='index.php?act=gis_popup_edit_details&mod=xst&stream=text&id=' + id;
    url = url +"&sid=" + Math.random();
    xmlHttp.onreadystatechange = shn_gis_popup_print;
    xmlHttp.open("GET", url, true);
    xmlHttp.send(null);
}
function shn_gis_popup_edit_details_ok(id){
    xmlHttp = GetXmlHttpObject();
    if (xmlHttp==null){
        alert ("{{=T("Your browser does not support AJAX!")}}");
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
