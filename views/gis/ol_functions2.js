// General functions usable by all Layers

// Return string type of a feature
// return point if not line or poly ....danger....
function featureTypeStr(feature){
    var type = 'point';
    var geotype = feature.geometry.CLASS_NAME;
    if(geotype == 'OpenLayers.Geometry.LineString'){
        type = 'line';
    } else if(geotype == 'OpenLayers.Geometry.Polygon'){
        type = 'poly';
    }
    return type;
}
// Create geometries from point coords.
function coordToGeom(coords, type){
    var geom = coords[0]
    if(type == 'point'){
        geom = coords[0]; // =  Array(new OpenLayers.Geometry.Point(lon, lat));
    } else if(type == 'line'){
        geom = new OpenLayers.Geometry.LineString(coords);
    } else if(type == 'poly'){
        geom = new OpenLayers.Geometry.Polygon(new Array(new OpenLayers.Geometry.LinearRing(coords)));
    } 
    return geom;
}
// Report Errors to a DIV
function ReportErrors(div,text) {
     $(div).innerHTML = text;
}
// For KML layers
function onFeatureUnselect(feature) {
    map.removePopup(feature.popup);
    feature.popup.destroy();
    feature.popup = null;
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
// For OSM Base layers
function osm_getTileURL(bounds) {
    var res = this.map.getResolution();
    var x = Math.round((bounds.left - this.maxExtent.left) / (res * this.tileSize.w));
    var y = Math.round((this.maxExtent.top - bounds.top) / (res * this.tileSize.h));
    var z = this.map.getZoom();
    var limit = Math.pow(2, z);
    if (y < 0 || y >= limit) {
        return OpenLayers.Util.getImagesLocation() + "404.png";
    } else {
        x = ((x % limit) + limit) % limit;
        return this.url + z + "/" + x + "/" + y + "." + this.type;
    }
}
