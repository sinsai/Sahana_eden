<script type="text/javascript">//<![CDATA[

// make map available for easy debugging
var map, toolbar;
//var treeModel;
//var features = new Array();
var featuresLayer, currentFeature;
//var pointControl, lineControl, polygonControl;
//var selectControl, dragControl

// avoid pink tiles
OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;
OpenLayers.Util.onImageLoadErrorColor = "transparent";

// Set Proxy Host
OpenLayers.ProxyHost = '{{=URL(r=request, c='static', f='proxy.py?url=')}}';

var lat = {{=lat}};
var lon = {{=lon}};
var zoom = {{=zoom}};
var centered = false;

// See - http://crschmidt.net/~crschmidt/spherical_mercator.html#reprojecting-points
var proj4326 = new OpenLayers.Projection('EPSG:4326');
var projection_current = new OpenLayers.Projection('EPSG:{{=projection}}');
var point = new OpenLayers.LonLat(lon, lat);

// Map Options
var options = {
	displayProjection: proj4326,
	projection: projection_current,
	units: "{{=units}}",
	maxResolution: {{=maxResolution}},
	maxExtent: new OpenLayers.Bounds({{=maxExtent}})
};
