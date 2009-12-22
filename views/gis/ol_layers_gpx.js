{{for layer in gpx_layers:}}
  {{name = layer.replace(' ', '_')}}
    iconURL = "{{=URL(r=request, c='default', f='download', args=gpx_layers[layer].marker)}}";
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
    var gpxLayer{{=name}} = new OpenLayers.Layer.GML( "gpxLayer{{=name}}", "{{=URL(r=request, c='default', f='download', args=gpx_layers[layer].url)}}", {
        style: style_marker,
        format: OpenLayers.Format.GPX, projection: proj4326});
    map.addLayer(gpxLayer{{=name}});
{{pass}}
