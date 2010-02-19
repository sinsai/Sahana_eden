// General functions usable by all Layers

// Report Errors to a DIV
function ReportErrors(div,text) {
     $(div).innerHTML = text;
}
// For OSM File layers
function on_feature_hover(feature) {
        var text ="<ul>";
        var type ="way";
        if (feature.geometry.CLASS_NAME == "OpenLayers.Geometry.Point") {
            type = "node";
        }    
        text += "<li>" + feature.osm_id + ": <a href='http://www.openstreetmap.org/api/0.5/"+type + "/" + feature.osm_id + "'>API</a></li>";
        for (var key in feature.attributes) {
            text += "<li>" + key + ": " + feature.attributes[key] + "</li>";
        }
        text += "</ul>";
        $("status_osm").innerHTML = text;
}
