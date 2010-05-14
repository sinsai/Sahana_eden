// make map available for easy debugging
var map;
var mapPanel, toolbar;
//var treeModel;
//var features = new Array();
var featuresLayer, currentFeature;
//var pointControl, lineControl, polygonControl;
//var selectControl, dragControl
var popupControl;
var allLayers = new Array();

OpenLayers.ImgPath = '/{{=request.application}}/static/img/gis/openlayers/';
// avoid pink tiles
OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;
OpenLayers.Util.onImageLoadErrorColor = "transparent";

// Set Proxy Host
OpenLayers.ProxyHost = '{{=URL(r=request, c='gis', f='proxy?url=')}}';

// See http://crschmidt.net/~crschmidt/spherical_mercator.html#reprojecting-points
var proj4326 = new OpenLayers.Projection('EPSG:4326');
var projection_current = new OpenLayers.Projection('EPSG:{{=projection}}');

{{if lat and lon:}}
  // Provided by URL (Bookmark) or from feature (display_feature()) or from config (map_viewing_client())
  var lat = {{=lat}};
  var lon = {{=lon}};
  var center = new OpenLayers.LonLat(lon, lat);
  center.transform(proj4326, projection_current);
{{else:}}
  // Calculate from Bounds (display_features())
  var bottom_left = new OpenLayers.LonLat({{=lon_min}}, {{=lat_min}});
  bottom_left.transform(proj4326, projection_current);
  var left = bottom_left.lon;
  var bottom = bottom_left.lat;
  top_right = new OpenLayers.LonLat({{=lon_max}}, {{=lat_max}});
  top_right.transform(proj4326, projection_current);
  var right = top_right.lon;
  var top = top_right.lat;
  var bounds = OpenLayers.Bounds.fromArray([left, bottom, right, top]);
  var center = bounds.getCenterLonLat();
{{pass}}

// Map Options
var options = {
    displayProjection: proj4326,
    projection: projection_current,
    units: "{{=units}}",
    maxResolution: {{=maxResolution}},
    maxExtent: new OpenLayers.Bounds({{=maxExtent}}),
    numZoomLevels: {{=numZoomLevels}}
};
