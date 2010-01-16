function addLayers(map) {
  {{if projection==900913:}}
    {{if openstreetmap:}}
        {{include 'gis/ol_layers_openstreetmap.js'}}
    {{pass}}
    {{if google:}}
        {{include 'gis/ol_layers_google.js'}}
    {{pass}}
    {{if yahoo:}}
        {{include 'gis/ol_layers_yahoo.js'}}
    {{pass}}
    {{if bing:}}
        {{include 'gis/ol_layers_bing.js'}}
    {{pass}}
  {{else:}}
    // Disable other base layers since using a non-sphericalMercator WMS projection
  {{pass}}
  {{include 'gis/ol_layers_tms.js'}}
  {{include 'gis/ol_layers_wms.js'}}
  var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
  style_marker.graphicOpacity = 1;
  var icon_img = new Image();
  var max_w = 25;
  var max_h = 35;
  var width, height;
  var iconURL;
  {{include 'gis/ol_layers_georss.js'}}
  {{include 'gis/ol_layers_gpx.js'}}
  {{include 'gis/ol_layers_kml.js'}}
  {{include 'gis/ol_layers_js.js'}}
}