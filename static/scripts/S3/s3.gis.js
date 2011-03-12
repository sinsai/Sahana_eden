// Used by the Map (modules/s3gis.py)
// This script is in Static to allow caching
// Dynamic constants (e.g. Internationalised strings) are set in server-generated script

// Global vars
var map, mapPanel, legendPanel, toolbar, mapWin;
var pointButton, lastDraftFeature, draftLayer;
var centerPoint, currentFeature, popupControl, highlightControl;
var wmsBrowser, printProvider;
var allLayers = new Array();
OpenLayers.ImgPath = S3.Ap.concat('/static/img/gis/openlayers/');
// avoid pink tiles
OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;
OpenLayers.Util.onImageLoadErrorColor = 'transparent';
OpenLayers.ProxyHost = S3.Ap.concat('/gis/proxy?url=');
// See http://crschmidt.net/~crschmidt/spherical_mercator.html#reprojecting-points
var proj4326 = new OpenLayers.Projection('EPSG:4326');
var projection_current = new OpenLayers.Projection('EPSG:' + s3_gis_projection);
var s3_gis_options = {
        displayProjection: proj4326,
        projection: projection_current,
        // Use Manual stylesheet download (means can be done in HEAD to not delay pageload)
        theme: null,
        paddingForPopups: new OpenLayers.Bounds(50, 10, 200, 300),
        units: s3_gis_units,
        maxResolution: s3_gis_maxResolution,
        maxExtent: s3_gis_maxExtent,
        numZoomLevels: s3_gis_numZoomLevels
    };

// Functions which are called by user & hence need to be in global scope

// Replace Cluster Popup contents with selected Feature Popup
function loadClusterPopup(url, id) {
    $.get(
            url,
            function(data) {
                $('#' + id + '_contentDiv').html(data);
                map.popups[0].updateSize();
            },
            'html'
        );
}

// Zoom to Selected Feature from within Popup
function zoomToSelectedFeature(lon, lat, zoomfactor) {
    var lonlat = new OpenLayers.LonLat(lon, lat);
    // Get Current Zoom
    var currZoom = map.getZoom();
    // New Zoom
    var newZoom = currZoom + zoomfactor;
    // Center and Zoom
    map.setCenter(lonlat, newZoom);
    // Remove Popups
    for (var i=0; i < map.popups.length; ++i) {
        map.removePopup(map.popups[i]);
    }
}

// HTML5 GeoLocation: http://dev.w3.org/geo/api/spec-source.html
function getCurrentPosition(position){
    // Level to zoom into
    var zoomLevel = 15;
    var lat = position.coords.latitude;
    var lon = position.coords.longitude;
    //var elevation = position.coords.altitude;
    //var ce = position.coords.accuracy;
    //var le = position.coords.altitudeAccuracy;
    //position.coords.heading;
    //position.coords.speed;
    map.setCenter(new OpenLayers.LonLat(lon, lat).transform(proj4326, map.getProjectionObject()), zoomLevel);
};

var styleMarker = new Object();
var iconURL;
var s3_gis_image;

var scaleImage = function() {
    var scaleRatio = s3_gis_image.height / s3_gis_image.width;
    var w = Math.min(s3_gis_image.width, s3_gis_max_w);
    var h = w * scaleRatio;
    if (h > s3_gis_max_h) {
            h = s3_gis_max_h;
            scaleRatio = w / h;
            w = w * scaleRatio;
        }
    s3_gis_image.height = h;
    s3_gis_image.width = w;
}
