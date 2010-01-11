var georssLayers = new Array();
{{for layer in georss_layers:}}
  {{name = layer.replace(' ', '_')}}
    iconURL = "{{=URL(r=request, c='default', f='download', args=georss_layers[layer].marker)}}";
    icon_img.src = iconURL;
    width = icon_img.width;
    height = icon_img.height;
    if(width > max_w){
        height = ((max_w / width) * height);
        width = max_w;
    }
    if(height > max_h){
        width = ((max_h / height) * width);
        height = max_h;
    }
    style_marker.graphicWidth = width;
    style_marker.graphicHeight = height;
    style_marker.graphicXOffset = -(width / 2);
    style_marker.graphicYOffset = -height;
    style_marker.externalGraphic = iconURL;
    var georssLayer{{=name}} = new OpenLayers.Layer.GML( "{{=layer}}", "{{=georss_layers[layer].url}}", {
        format: OpenLayers.Format.GeoRSS, style: style_marker,
        formatOptions: {
            // adds the thumbnail attribute to the feature
            createFeatureFromItem: function(item) {
                var feature = OpenLayers.Format.GeoRSS.prototype.createFeatureFromItem.apply(this, arguments);
                //feature.attributes.thumbnail =
                //        this.getElementsByTagNameNS(
                //        item, "*", "thumbnail")[0].getAttribute("url");
                return feature;
            }
        },
      {{if georss_layers[layer].projection == 4326:}}
        projection: proj4326});
      {{else:}}
        projection: new OpenLayers.Projection('EPSG:{{=georss_layers[layer].projection}}')});
      {{pass}} 
    map.addLayer(georssLayer{{=name}});
    georssLayers.push(georssLayer{{=name}});
{{pass}}
{{if georss_layers:}}
// Select Control for GeoRSS Layers
var georsspopupControl = new OpenLayers.Control.SelectFeature(georssLayers, {
    onSelect: function(feature) {
        var pos = feature.geometry;
        if (popup) {
            map.removePopup(popup);
        }
        popup = new OpenLayers.Popup("popup",
            new OpenLayers.LonLat(pos.x, pos.y),
            new OpenLayers.Size(254, 320),
            "<h3>" + feature.attributes.title + "</h3>" + feature.attributes.description,
            true);
        map.addPopup(popup);
    }
}); 
map.addControl(georsspopupControl);
georsspopupControl.activate();
{{pass}}